"""
OTD Agent Sim — Full Integration Runner
Connects 4 agents (Sales/Planning/QC/Logistics) to real Station engine
Reads factory.json → creates Station objects → generates realistic sim data
"""
from __future__ import annotations
import sys, os, json, random
from pathlib import Path

# Inject otd-sim path
_OTD_SIM = os.path.join(os.path.dirname(__file__), "..", "otd-sim")
if _OTD_SIM not in sys.path:
    sys.path.insert(0, _OTD_SIM)

from station_dispatch import Station
from agents import (
    SimState, SimRunner, SimEvent, EventType,
    SalesAgent, PlanningAgent, LogisticsAgent,
)

# ═══════════════════════════════════════════════════════════════
# QC Agent — 品質管理
# ═══════════════════════════════════════════════════════════════

class QCAgent:
    """
    品質管理 agent。
    
    Heartbeat: 每 8 ticks (8h, 每班)
    行動:
      1. 抽檢已完成 WO 的 yield rate
      2. 低於 threshold → 觸發 rework decision
      3. 追蹤 defect trend → 建議 maintenance
    決策: sample_rate, defect_threshold, rework_qty_pct
    """
    
    def __init__(self, name: str = "QCAgent",
                 sample_pct: float = 0.15,
                 defect_threshold: float = 0.95,
                 rework_pct: float = 0.30):
        self.name = name
        self.sample_pct = sample_pct
        self.defect_threshold = defect_threshold
        self.rework_pct = rework_pct
        self.inspected_wos: set = set()
        self.rework_queue: list = []
        self.last_audit_tick: int = -8
    
    def step(self, state: SimState) -> list[SimEvent]:
        events = []
        
        # Audit interval: every 8 hours (1 shift)
        if state.tick - self.last_audit_tick < 8:
            return events
        self.last_audit_tick = state.tick
        
        # Inspect recently completed WOs (from events)
        completed = [
            e for e in state.events[-500:]
            if e.event_type == EventType.WO_COMPLETED
            and e.source != self.name
            and e.details.get("wo_id") not in self.inspected_wos
        ]
        
        inspected = 0
        defects_found = 0
        
        for ev in completed:
            if random.random() > self.sample_pct:
                continue
            
            wo_id = ev.details.get("wo_id", "")
            self.inspected_wos.add(wo_id)
            inspected += 1
            
            # Simulate inspection: yield check
            actual_yield = ev.details.get("yield_rate", random.uniform(0.90, 1.0))
            qty = ev.details.get("qty_good", 100)
            
            if actual_yield < self.defect_threshold:
                defects_found += 1
                rework_qty = int(qty * self.rework_pct)
                self.rework_queue.append({
                    "wo_id": wo_id,
                    "order_id": ev.details.get("order_id", ""),
                    "station_id": ev.details.get("station_id", ""),
                    "defect_qty": rework_qty,
                    "yield_rate": actual_yield,
                    "tick": state.tick,
                })
                events.append(SimEvent(
                    tick=state.tick,
                    source=self.name,
                    event_type=EventType.WO_REWORK,
                    details={
                        "wo_id": wo_id,
                        "order_id": ev.details.get("order_id", ""),
                        "defect_qty": rework_qty,
                        "yield_rate": round(actual_yield, 4),
                        "action": "rework_triggered",
                    }
                ))
        
        if inspected > 0:
            events.append(SimEvent(
                tick=state.tick,
                source=self.name,
                event_type=EventType.QC_AUDIT,
                details={
                    "inspected": inspected,
                    "defects_found": defects_found,
                    "defect_rate": round(defects_found / inspected * 100, 1) if inspected else 0,
                    "rework_queue_size": len(self.rework_queue),
                    "day": state.day,
                }
            ))
        
        return events


# ═══════════════════════════════════════════════════════════════
# Integrated SimRunner — with real stations
# ═══════════════════════════════════════════════════════════════

class IntegratedRunner(SimRunner):
    """Extended runner that loads real Station objects from factory.json."""
    
    def __init__(self, factory_config: dict, **kwargs):
        super().__init__(**kwargs)
        self.config = factory_config
        
        # Build real stations
        self.stations: dict[str, Station] = {}
        for line in factory_config.get("factory", {}).get("lines", []):
            for sconf in line.get("stations", []):
                sid = sconf["id"]
                self.stations[sid] = Station(sid, sconf)
        
        # Give stations to PlanningAgent
        self.planning.stations = self.stations
        
        # Add QC agent
        self.qc = QCAgent()
        
        # Load product routes from config
        self.product_routes = {}
        for prod in factory_config.get("order_template", {}).get("products", []):
            self.product_routes[prod["type"]] = prod.get("route", [])
        self.planning.product_routes = self.product_routes
    
    def run(self, output_path: str | None = None) -> dict:
        self.output_path = output_path
        log_lines = []
        
        start_event = SimEvent(tick=0, source="SimRunner", event_type=EventType.SIM_START)
        self.state.events.append(start_event)
        log_lines.append(start_event.to_line())
        
        for tick in range(self.total_ticks):
            self.state.tick = tick
            self.state.day = tick // 24
            
            # Run all 4 agents
            all_events = []
            all_events += self.sales.step(self.state)
            all_events += self.planning.step(self.state)
            all_events += self.qc.step(self.state)
            all_events += self.logistics.step(self.state)
            
            for ev in all_events:
                self.state.events.append(ev)
                log_lines.append(ev.to_line())
        
        # Calculate lead times properly
        self._calc_lead_times()
        
        # End event
        end_event = SimEvent(
            tick=self.total_ticks,
            source="SimRunner",
            event_type=EventType.SIM_END,
            details={
                "total_orders": self.state.total_orders,
                "shipped": len(self.state.shipped_orders),
                "completed": len(self.state.completed_orders),
                "pending": len(self.state.pending_queue),
                "ot_pct": round(self.state.ot * 100, 1),
                "avg_lead_time_hours": round(self.state.avg_lead_time_hours, 1),
                "avg_lead_time_days": round(self.state.avg_lead_time_hours / 24, 1),
                "on_time_count": self.state.on_time_count,
                "late_count": self.state.late_count,
                "qc_inspections": len(self.qc.inspected_wos),
                "qc_defects": len(self.qc.rework_queue),
                "stations": {
                    sid: {"wip": s.wip, "processed": s.total_units_processed}
                    for sid, s in self.stations.items()
                }
            }
        )
        self.state.events.append(end_event)
        log_lines.append(end_event.to_line())
        
        if output_path:
            with open(output_path, "w") as f:
                f.write("\n".join(log_lines) + "\n")
        
        return end_event.details
    
    def _calc_lead_times(self):
        """Post-hoc lead time calculation from event log."""
        self.state.lead_times = []
        for order in self.state.shipped_orders:
            arrival_tick = order.arrival_day * 24
            ship_events = [
                e for e in self.state.events
                if e.event_type.value == "order_shipped"
                and e.details.get("order_id") == order.order_id
            ]
            if ship_events:
                ship_tick = ship_events[0].tick
                lt = ship_tick - arrival_tick
                self.state.lead_times.append(lt)


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="OTD 4-Agent Sim with real Station Engine")
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--policy", type=str, default="EDD", choices=["FIFO", "EDD", "SPT"])
    p.add_argument("--arrival", type=int, default=5)
    p.add_argument("--factory", type=str, 
                   default=os.path.join(_OTD_SIM, "factory.json"))
    p.add_argument("--output", type=str, default="agent-sim-log.jsonl")
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    
    random.seed(args.seed)
    
    with open(args.factory) as f:
        factory_config = json.load(f)
    
    runner = IntegratedRunner(
        factory_config=factory_config,
        total_ticks=args.days * 24,
        dispatch_policy=args.policy,
        arrival_base=args.arrival,
    )
    
    print(f"🚀 OTD 4-Agent Sim: {args.days}d, {args.policy}, {args.arrival} ord/day")
    print(f"   Stations: {list(runner.stations.keys())}")
    
    result = runner.run(args.output)
    
    print(f"\n{'='*60}")
    print(f"  RESULTS")
    print(f"{'='*60}")
    print(f"  Orders created:  {result['total_orders']}")
    print(f"  Shipped:         {result['shipped']}")
    print(f"  Pending:         {result['pending']}")
    print(f"  On-time rate:    {result['ot_pct']}% ({result['on_time_count']}/{result['on_time_count']+result['late_count']})")
    print(f"  Avg lead time:   {result['avg_lead_time_hours']:.0f}h ({result['avg_lead_time_days']:.1f}d)")
    print(f"  QC inspections:  {result['qc_inspections']}")
    print(f"  QC defects:      {result['qc_defects']}")
    print(f"  Station WIP:")
    for sid, s in result['stations'].items():
        print(f"    {sid:8s}: WIP={s['wip']:4d} | processed={s['processed']:5d}")
    print(f"{'='*60}")
    print(f"  Log: {args.output}")