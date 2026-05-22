"""
OTD Agent Sim — 3-agent autonomous factory simulation
Track D: Smart 自主任務

Agent roles:
  - SalesAgent:     業務接單 — heartbeat 定時生成新訂單
  - PlanningAgent:  生管排程 — 讀取 pending WOs，應用 dispatch policy，路由下一站
  - LogisticsAgent: 倉管出貨 — 監控完成訂單，處理出貨，追蹤 OTD

Each agent has a step(sim_state) → list[SimEvent] interface.
Agents run independently on heartbeat ticks; no central orchestrator beyond the sim loop.
"""

from __future__ import annotations
import random
import json
import time
import sys
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional
from enum import Enum

# ── Inject showcase/otd-sim into path ──
_OTD_SIM_PATH = os.path.join(os.path.dirname(__file__), "..", "otd-sim")
if _OTD_SIM_PATH not in sys.path:
    sys.path.insert(0, _OTD_SIM_PATH)

try:
    from models import Order, OrderStatus, WorkOrder, ProductionRecord  # type: ignore
    from station_dispatch import Station, StationDispatchEngine  # type: ignore
    from dispatch_policy import POLICIES, apply_policy  # type: ignore
except ImportError:
    # Fallback: minimal inline definitions for standalone testing
    OrderStatus = Enum("OrderStatus", "RECEIVED SCHEDULED IN_PROGRESS COMPLETED SHIPPED CANCELLED")
    
    @dataclass
    class Order:
        order_id: str = ""
        customer: str = ""
        product_type: str = "A"
        quantity: int = 100
        due_date: Optional[datetime] = None
        priority: int = 1
        status: OrderStatus = OrderStatus.RECEIVED
        arrival_day: int = 0
        rush: bool = False
        work_order_ids: list = field(default_factory=list)
        completed_day: Optional[int] = None
        shipped_day: Optional[int] = None
        on_time: Optional[bool] = None
    
    @dataclass
    class WorkOrder:
        wo_id: str = ""
        order_id: str = ""
        product_type: str = "A"
        qty_planned: int = 0
        qty_good: int = 0
        qty_defect: int = 0
        station_id: str = ""
        _queue_entry_hour: float = 0.0
    
    @dataclass
    class ProductionRecord:
        wo_id: str = ""
        station_id: str = ""
        qty_good: int = 0
        qty_defect: int = 0
        yield_rate: float = 1.0
    
    POLICIES = {"FIFO": None, "EDD": None, "SPT": None}
    apply_policy = lambda q, p, ctx: None


# ═══════════════════════════════════════════════════════════════
# Core types
# ═══════════════════════════════════════════════════════════════

class EventType(str, Enum):
    ORDER_RECEIVED = "order_received"       # SalesAgent generates new order
    ORDER_SCHEDULED = "order_scheduled"     # PlanningAgent assigns WO
    WO_STARTED = "wo_started"               # WO begins at station
    WO_COMPLETED = "wo_completed"           # WO finishes at station
    ORDER_COMPLETED = "order_completed"     # All WOs done for order
    ORDER_SHIPPED = "order_shipped"         # LogisticsAgent ships
    ORDER_DELAYED = "order_delayed"         # OTD miss
    HEARTBEAT = "heartbeat"                 # Agent tick log
    WO_REWORK = "wo_rework"                 # QC triggers rework
    QC_AUDIT = "qc_audit"                   # QC audit round
    STATION_DOWN = "station_down"           # Station failure
    STATION_UP = "station_up"               # Station recovery
    SIM_START = "sim_start"
    SIM_END = "sim_end"


@dataclass
class SimEvent:
    """原子事件 — 每個 agent 決策產生一個 event"""
    tick: int           # simulation hour
    source: str         # agent name (sales/planning/logistics)
    event_type: EventType
    details: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_line(self) -> str:
        return json.dumps({
            "tick": self.tick,
            "source": self.source,
            "type": self.event_type.value,
            "details": self.details,
            "ts": self.timestamp,
        }, ensure_ascii=False)


# ═══════════════════════════════════════════════════════════════
# SimState — shared state across agents
# ═══════════════════════════════════════════════════════════════

@dataclass
class SimState:
    """Agent-visible simulation state"""
    tick: int = 0                          # current sim hour
    day: int = 0
    orders: dict[str, Order] = field(default_factory=dict)
    work_orders: dict[str, WorkOrder] = field(default_factory=dict)
    pending_queue: list[Order] = field(default_factory=list)      # orders waiting scheduling
    completed_orders: list[Order] = field(default_factory=list)   # ready to ship
    shipped_orders: list[Order] = field(default_factory=list)
    events: list[SimEvent] = field(default_factory=list)
    # metrics
    total_orders: int = 0
    on_time_count: int = 0
    late_count: int = 0
    lead_times: list[int] = field(default_factory=list)           # arrival→ship in hours

    # config
    dispatch_policy: str = "EDD"
    arrival_base_per_day: int = 10
    arrival_jitter_pct: float = 20.0
    ship_transit_days: int = 2

    @property
    def ot(self) -> float:
        """On-time rate"""
        shipped = self.on_time_count + self.late_count
        return self.on_time_count / shipped if shipped > 0 else 0.0

    @property
    def avg_lead_time_hours(self) -> float:
        return sum(self.lead_times) / len(self.lead_times) if self.lead_times else 0.0

    def next_order_id(self) -> str:
        self.total_orders += 1
        return f"ORD-{self.total_orders:04d}"

    def next_wo_id(self) -> str:
        n = len(self.work_orders) + 1
        return f"WO-{n:04d}"


# ═══════════════════════════════════════════════════════════════
# AGENT 1: SalesAgent — 業務接單
# ═══════════════════════════════════════════════════════════════

class SalesAgent:
    """
    業務接單 agent。
    
    Heartbeat: 每天 09:00 觸發一次（每 24 ticks）
    行動: 生成當日新訂單（依 arrival_base + jitter），依 product mix 分配類型。
    決策參數: rush_order_threshold（急單概率）、product_mix（A/B/C 比例）
    """
    
    def __init__(self, name: str = "SalesAgent", 
                 product_mix: dict | None = None,
                 rush_prob: float = 0.05):
        self.name = name
        self.product_mix = product_mix or {"A": 0.60, "B": 0.25, "C": 0.15}
        self.rush_prob = rush_prob
        self.last_order_day: int = -1
        self.products = [
            {"type": "A", "name": "標準品", "qty_min": 50, "qty_max": 200, "lead_days": 7},
            {"type": "B", "name": "急單品", "qty_min": 20, "qty_max": 100, "lead_days": 3},
            {"type": "C", "name": "特製品", "qty_min": 10, "qty_max": 80,  "lead_days": 10},
        ]
    
    def step(self, state: SimState) -> list[SimEvent]:
        """Heartbeat: 新的一天開始 → 生成新訂單"""
        events = []
        day = state.tick // 24
        
        # Only generate once per day
        if day <= self.last_order_day:
            return events
        self.last_order_day = day
        
        # Determine order count with jitter
        base = state.arrival_base_per_day
        jitter = random.uniform(-base * state.arrival_jitter_pct / 100, 
                                 base * state.arrival_jitter_pct / 100)
        count = max(1, int(base + jitter))
        
        for _ in range(count):
            # Pick product type by weighted mix
            ptype = random.choices(
                list(self.product_mix.keys()),
                weights=list(self.product_mix.values()),
                k=1
            )[0]
            
            # Find product config
            prod = next((p for p in self.products if p["type"] == ptype), self.products[0])
            qty = random.randint(prod["qty_min"], prod["qty_max"])
            
            # Due date: arrival_day + lead_days
            due_date = datetime.now() + timedelta(days=day + prod["lead_days"] + random.randint(-1, 2))
            rush = random.random() < self.rush_prob
            if rush:
                due_date = datetime.now() + timedelta(days=day + prod["lead_days"] // 2)
            
            oid = state.next_order_id()
            order = Order(
                order_id=oid,
                customer=f"CUST-{random.randint(1, 20):03d}",
                product_type=ptype,
                quantity=qty,
                due_date=due_date,
                priority=2 if rush else 1,
                status=OrderStatus.RECEIVED,
                arrival_day=day,
                rush=rush,
            )
            state.orders[oid] = order
            state.pending_queue.append(order)
            
            events.append(SimEvent(
                tick=state.tick,
                source=self.name,
                event_type=EventType.ORDER_RECEIVED,
                details={
                    "order_id": oid,
                    "product_type": ptype,
                    "quantity": qty,
                    "due_date": due_date.isoformat(),
                    "rush": rush,
                    "priority": order.priority,
                }
            ))
        
        # Heartbeat log
        events.append(SimEvent(
            tick=state.tick,
            source=self.name,
            event_type=EventType.HEARTBEAT,
            details={"day": day, "new_orders": count, "total_pending": len(state.pending_queue)}
        ))
        
        return events


# ═══════════════════════════════════════════════════════════════
# AGENT 2: PlanningAgent — 生管排程
# ═══════════════════════════════════════════════════════════════

class PlanningAgent:
    """
    生管排程 agent。
    
    Heartbeat: 每 tick (1 hour) 觸發
    行動: 
      1. Scan pending_queue → create WorkOrders per order
      2. Apply dispatch policy to WO queue
      3. Route WOs to first station (or next station)
      4. Monitor station WIP — rebalance if bottleneck detected
    決策: dispatch_policy selection (FIFO/EDD/SPT), bottleneck rebalance threshold
    """
    
    def __init__(self, name: str = "PlanningAgent",
                 dispatch_policy: str = "EDD",
                 stations: dict[str, Any] | None = None,
                 product_routes: dict | None = None):
        self.name = name
        self.dispatch_policy = dispatch_policy
        self.stations: dict[str, Any] = stations or {}
        self.product_routes = product_routes or {
            "A": ["L1-S1", "L1-S2", "L1-S3"],
            "B": ["L1-S1", "L1-S2"],
            "C": ["L1-S1", "L1-S2", "L1-S3", "L1-S3"],
        }
        self.queued_wos: list[WorkOrder] = []
        # Per-order: track how many WOs created + completed
        self.order_wo_count: dict[str, int] = {}
        self.order_wo_done: dict[str, int] = {}
    
    def step(self, state: SimState) -> list[SimEvent]:
        events = []
        
        # ── 1. Create WOs from pending orders ──
        for order in list(state.pending_queue):
            route = self.product_routes.get(order.product_type, ["L1-S1"])
            # Create one WO per station in route
            for sid in route:
                wid = state.next_wo_id()
                wo = WorkOrder(
                    wo_id=wid,
                    order_id=order.order_id,
                    product_type=order.product_type,
                    qty_planned=order.quantity,
                    qty_good=0,
                    qty_defect=0,
                    station_id=sid,
                    _queue_entry_hour=float(state.tick),
                )
                state.work_orders[wid] = wo
                self.queued_wos.append(wo)
                order.work_order_ids.append(wid)
                self.order_wo_count[order.order_id] = self.order_wo_count.get(order.order_id, 0) + 1
            
            order.status = OrderStatus.SCHEDULED
            state.pending_queue.remove(order)
            events.append(SimEvent(
                tick=state.tick,
                source=self.name,
                event_type=EventType.ORDER_SCHEDULED,
                details={
                    "order_id": order.order_id,
                    "product_type": order.product_type,
                    "quantity": order.quantity,
                    "route": route,
                    "wo_count": len(route),
                }
            ))
        
        # ── 2. Dispatch queued WOs to stations ──
        if self.queued_wos:
            # Apply dispatch policy
            cycle_map = {"A": 4.0, "B": 2.5, "C": 6.0}
            ctx = {"cycle_time_map": cycle_map}
            
            if self.dispatch_policy == "FIFO":
                self.queued_wos.sort(key=lambda wo: wo._queue_entry_hour)
            elif self.dispatch_policy == "EDD":
                for wo in self.queued_wos:
                    order = state.orders.get(wo.order_id)
                    if order:
                        wo.priority = order.priority
                self.queued_wos.sort(key=lambda wo: (
                    -wo.priority,
                    wo._queue_entry_hour,
                ))
            elif self.dispatch_policy == "SPT":
                for wo in self.queued_wos:
                    cycle = cycle_map.get(wo.product_type, 4.0)
                    wo.priority = -int(cycle * wo.qty_planned / 100)
                self.queued_wos.sort(key=lambda wo: (
                    wo.priority,
                    wo._queue_entry_hour,
                ))
        
        # Route WOs to stations (simplified: each WO assigned to its station_id)
        for wo in list(self.queued_wos):
            station = self.stations.get(wo.station_id)
            if station is None:
                # No station object → abstract processing: just log
                processing_hours = {"A": 4.0, "B": 2.5, "C": 6.0}.get(wo.product_type, 4.0)
                wo.qty_good = wo.qty_planned
                self.queued_wos.remove(wo)
                events.append(self._complete_wo(state, wo, "abstract"))
            else:
                # Try to add WO to station
                station.add_wo(wo)
                self.queued_wos.remove(wo)
                events.append(SimEvent(
                    tick=state.tick,
                    source=self.name,
                    event_type=EventType.WO_STARTED,
                    details={
                        "wo_id": wo.wo_id,
                        "order_id": wo.order_id,
                        "station_id": wo.station_id,
                        "qty": wo.qty_planned,
                        "product_type": wo.product_type,
                    }
                ))
        
        # ── 3. Process stations (1 hour step) ──
        for sid, station in self.stations.items():
            records = station.step(1.0)
            for rec in records:
                wo_id = rec.get("wo_id", "")
                wo = state.work_orders.get(wo_id)
                if wo:
                    events.append(self._complete_wo(state, wo, sid))
        
        # ── 4. Check completed orders ──
        for oid, order in list(state.orders.items()):
            if order.status == OrderStatus.SCHEDULED or order.status == OrderStatus.IN_PROGRESS:
                total = self.order_wo_count.get(oid, 0)
                done = self.order_wo_done.get(oid, 0)
                if total > 0 and done >= total:
                    order.status = OrderStatus.COMPLETED
                    order.completed_day = state.tick // 24
                    state.completed_orders.append(order)
                    events.append(SimEvent(
                        tick=state.tick,
                        source=self.name,
                        event_type=EventType.ORDER_COMPLETED,
                        details={
                            "order_id": oid,
                            "product_type": order.product_type,
                            "arrival_day": order.arrival_day,
                            "completed_day": order.completed_day,
                        }
                    ))
        
        return events
    
    def _complete_wo(self, state: SimState, wo: WorkOrder, station_id: str) -> SimEvent:
        oid = wo.order_id
        self.order_wo_done[oid] = self.order_wo_done.get(oid, 0) + 1
        return SimEvent(
            tick=state.tick,
            source=self.name,
            event_type=EventType.WO_COMPLETED,
            details={
                "wo_id": wo.wo_id,
                "order_id": oid,
                "station_id": station_id,
                "qty_good": wo.qty_good,
                "qty_defect": wo.qty_defect,
            }
        )


# ═══════════════════════════════════════════════════════════════
# AGENT 3: LogisticsAgent — 倉管出貨
# ═══════════════════════════════════════════════════════════════

class LogisticsAgent:
    """
    倉管出貨 agent。
    
    Heartbeat: 每 tick 觸發
    行動:
      1. Scan completed_orders → ship them (with transit delay)
      2. Track OTD: on_time vs late
      3. Maintain warehouse FIFO queue
    決策: ship_mode selection (expedited for late orders), transit buffer
    """
    
    def __init__(self, name: str = "LogisticsAgent",
                 ship_transit_ticks: int = 48):  # 2 days
        self.name = name
        self.ship_transit_ticks = ship_transit_ticks
        self.in_transit: dict[str, int] = {}      # order_id → remaining ticks
    
    def step(self, state: SimState) -> list[SimEvent]:
        events = []
        
        # ── 1. Process in-transit shipments ──
        for oid in list(self.in_transit.keys()):
            self.in_transit[oid] -= 1
            if self.in_transit[oid] <= 0:
                del self.in_transit[oid]
        
        # ── 2. Ship completed orders ──
        for order in list(state.completed_orders):
            # Transit delay
            transit = self.ship_transit_ticks + random.randint(-8, 8)  # ±8h jitter
            self.in_transit[order.order_id] = transit
            
            # Calculate delivery date
            delivery_tick = state.tick + transit
            order.shipped_day = delivery_tick // 24
            
            # OTD check
            if order.due_date:
                delivery_dt = datetime.now() + timedelta(hours=delivery_tick - state.tick)
                order.on_time = delivery_dt <= order.due_date
            else:
                order.on_time = True
            
            order.status = OrderStatus.SHIPPED
            state.completed_orders.remove(order)
            state.shipped_orders.append(order)
            
            # Track metrics
            lead_time_hours = state.tick - order.arrival_day * 24
            state.lead_times.append(lead_time_hours)
            
            if order.on_time:
                state.on_time_count += 1
            else:
                state.late_count += 1
                events.append(SimEvent(
                    tick=state.tick,
                    source=self.name,
                    event_type=EventType.ORDER_DELAYED,
                    details={
                        "order_id": order.order_id,
                        "product_type": order.product_type,
                        "lead_time_hours": lead_time_hours,
                        "due_date": order.due_date.isoformat() if order.due_date else "N/A",
                    }
                ))
            
            events.append(SimEvent(
                tick=state.tick,
                source=self.name,
                event_type=EventType.ORDER_SHIPPED,
                details={
                    "order_id": order.order_id,
                    "product_type": order.product_type,
                    "quantity": order.quantity,
                    "on_time": order.on_time,
                    "lead_time_hours": lead_time_hours,
                    "transit_hours": transit,
                }
            ))
        
        return events


# ═══════════════════════════════════════════════════════════════
# SimRunner — orchestrates agents + engine
# ═══════════════════════════════════════════════════════════════

class SimRunner:
    """
    模擬主控 loop — 驅動三 agent + 底層 engine 同步 stepping。
    每個 tick: SalesAgent → PlanningAgent → LogisticsAgent → Station engine。
    """
    
    def __init__(self, total_ticks: int = 720,     # 30 days
                 dispatch_policy: str = "EDD",
                 arrival_base: int = 10,
                 ship_transit_ticks: int = 48):
        self.total_ticks = total_ticks
        self.state = SimState(
            dispatch_policy=dispatch_policy,
            arrival_base_per_day=arrival_base,
            ship_transit_days=ship_transit_ticks // 24,
        )
        self.sales = SalesAgent()
        self.planning = PlanningAgent(dispatch_policy=dispatch_policy)
        self.logistics = LogisticsAgent(ship_transit_ticks=ship_transit_ticks)
        self.output_path: str | None = None
    
    def run(self, output_path: str | None = None) -> dict:
        """Run the simulation and return summary dict."""
        self.output_path = output_path
        log_lines = []
        
        # Sim start
        start_event = SimEvent(tick=0, source="SimRunner", event_type=EventType.SIM_START)
        self.state.events.append(start_event)
        log_lines.append(start_event.to_line())
        
        for tick in range(self.total_ticks):
            self.state.tick = tick
            self.state.day = tick // 24
            
            # Agent heartbeats
            events = []
            events += self.sales.step(self.state)
            events += self.planning.step(self.state)
            events += self.logistics.step(self.state)
            
            for ev in events:
                self.state.events.append(ev)
                log_lines.append(ev.to_line())
        
        # Sim end
        end_event = SimEvent(
            tick=self.total_ticks,
            source="SimRunner",
            event_type=EventType.SIM_END,
            details={
                "total_orders": self.state.total_orders,
                "shipped": len(self.state.shipped_orders),
                "completed": len(self.state.completed_orders),
                "pending": len(self.state.pending_queue),
                "ot": round(self.state.ot * 100, 1),
                "avg_lead_time_hours": round(self.state.avg_lead_time_hours, 1),
                "on_time_count": self.state.on_time_count,
                "late_count": self.state.late_count,
            }
        )
        self.state.events.append(end_event)
        log_lines.append(end_event.to_line())
        
        # Write output
        if output_path:
            with open(output_path, "w") as f:
                f.write("\n".join(log_lines) + "\n")
        
        return end_event.details
    
    def summary(self) -> str:
        """Human-readable summary report."""
        s = self.state
        lines = [
            "=" * 60,
            "  OTD Agent Sim — Simulation Summary",
            "=" * 60,
            f"  Duration:       {self.total_ticks} ticks ({self.total_ticks // 24} days)",
            f"  Dispatch:       {s.dispatch_policy}",
            f"  Orders created: {s.total_orders}",
            f"  Shipped:        {len(s.shipped_orders)}",
            f"  In pipeline:    {len(s.completed_orders) + len(s.pending_queue)}",
            f"  On-time rate:   {s.ot * 100:.1f}% ({s.on_time_count}/{s.on_time_count + s.late_count})",
            f"  Avg lead time:  {s.avg_lead_time_hours:.1f} hours ({s.avg_lead_time_hours / 24:.1f} days)",
            "=" * 60,
            "",
            "Agent decision log highlights:",
        ]
        
        # Top 5 events by type
        from collections import Counter
        type_counts = Counter(e.event_type.value for e in s.events)
        for etype, count in type_counts.most_common(8):
            lines.append(f"  {etype:20s}: {count:4d}")
        
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="OTD Agent Sim — 3-agent factory simulation")
    p.add_argument("--days", type=int, default=30, help="Simulation duration in days")
    p.add_argument("--policy", type=str, default="EDD", choices=["FIFO", "EDD", "SPT"])
    p.add_argument("--arrival", type=int, default=10, help="Base orders per day")
    p.add_argument("--output", type=str, default="agent-sim-log.jsonl",
                   help="Output path for agent event log")
    p.add_argument("--summary-only", action="store_true", help="Print summary only")
    args = p.parse_args()
    
    ticks = args.days * 24
    runner = SimRunner(total_ticks=ticks, dispatch_policy=args.policy, arrival_base=args.arrival)
    
    if not args.summary_only:
        print(f"Running OTD Agent Sim: {args.days} days, {args.policy}, {args.arrival} orders/day")
    
    result = runner.run(args.output)
    
    print(runner.summary())
    print(f"\nAgent log written to: {args.output}")
    print(f"OTD={result['ot']}% | {result['shipped']} shipped | avg lead {result['avg_lead_time_hours']:.1f}h")