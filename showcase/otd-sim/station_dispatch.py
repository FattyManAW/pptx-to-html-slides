"""
OTD Sim — Station Dispatch Loop + WIP Tracking + Yield Decay (v0.2-expansion)
從 Christina 的 models.py 骨架（440 行）擴充而來。
不依賴 due_date 格式。

檔案：showcase/otd-sim/station_dispatch.py
"""

from __future__ import annotations
import random
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
from models import VariantParams  # v0.3: used in __init__
try:
    from dispatch_policy import apply_policy, POLICIES  # v0.4: pluggable policy layer
except ImportError:
    apply_policy = None
    POLICIES = {"FIFO": None, "EDD": None, "SPT": None}


# ═══════════════════════════════════════════════════════════════
# Station class — 單一生產工作站
# ═══════════════════════════════════════════════════════════════

class Station:
    """
    工作站 — 實體生產單元

    特性：
    - capacity queue：可同時處理多筆工單
    - setup time：換線時間（per-product jitter）
    - WIP tracking：追蹤在製品數量
    - yield decay：良率隨處理量線性衰減（不低於 80%）
    - failure model：Poisson-based 故障模型
    - bottleneck detection：wait_time × (1 + WIP/MAX)
    """

    def __init__(self, station_id: str, config: dict):
        self.station_id = station_id
        self.name = config.get("name", station_id)
        self.capacity_per_hour = config.get("capacity", {}).get("units_per_hour", 100)
        self.max_batch = config.get("capacity", {}).get("max_batch", 500)
        self.setup_base_min = config.get("setup", {}).get("base_min", 15)
        self.setup_per_product_min = config.get("setup", {}).get("per_product_min", 5)
        self.failure_rate = config.get("failure", {}).get("rate", 0.02)
        self.mttr_min = config.get("failure", {}).get("mttr_min", 30)
        self.yield_base_rate = config.get("yield", {}).get("base_rate", 0.995)
        self.yield_decay_per_1k = config.get("yield", {}).get("decay_per_1k", 0.001)
        self.maintenance_interval_hours = config.get("maintenance", {}).get("interval_hours", 160)
        self.maintenance_duration_min = config.get("maintenance", {}).get("duration_min", 60)

        # Runtime state
        self.wip: int = 0
        self.current_wo: Any = None
        self.queue: list = []
        self.hours_since_failure: float = 0.0
        self.hours_since_maintenance: float = 0.0
        self.is_down: bool = False
        self.downtime_remaining_min: float = 0.0
        self._setup_remaining: float = 0.0

        # Metrics
        self.total_units_processed: int = 0
        self.batches_processed: int = 0
        self.total_wait_time_hours: float = 0.0

    def add_wo(self, wo: Any) -> None:
        if self.current_wo is None and not self.queue:
            self._start_wo(wo)
        else:
            wo._queue_entry_hour = self.hours_since_failure  # track wait start
            self.queue.append(wo)
            self.wip += wo.qty_planned

    def _start_wo(self, wo: Any) -> None:
        self.current_wo = wo
        self.wip += wo.qty_planned
        # Accumulate wait time from queue depth (simplified: each hour in queue = 1h wait)
        _entry = getattr(wo, "_queue_entry_hour", 0.0)
        self.total_wait_time_hours += max(0.0, _entry)
        pt = getattr(wo, "product_type", "A")
        jitter = (random.random() - 0.5) * 2 * (self.setup_per_product_min * 0.3)
        self._setup_remaining = max(0.0, self.setup_base_min + jitter)

    def step(self, hours: float = 1.0) -> list[dict]:
        records = []

        if self.is_down:
            self.downtime_remaining_min -= hours * 60
            self.hours_since_maintenance += hours
            if self.downtime_remaining_min <= 0:
                self.is_down = False
            return records

        # Maintenance check
        self.hours_since_maintenance += hours
        if self.hours_since_maintenance >= self.maintenance_interval_hours:
            self.is_down = True
            self.downtime_remaining_min = self.maintenance_duration_min
            self.hours_since_maintenance = 0.0
            return records

        # Failure check (Poisson per 100h)
        self.hours_since_failure += hours
        fail_prob = self.failure_rate * (self.hours_since_failure / 100.0)
        if random.random() < fail_prob:
            self.is_down = True
            self.downtime_remaining_min = self.mttr_min
            self.hours_since_failure = 0.0
            return records

        # Setup time
        if self._setup_remaining > 0:
            self._setup_remaining -= hours * 60
            return records

        # Current WO processing
        if self.current_wo is None:
            if self.queue:
                # Age all queued items by 1 hour
                for _wo in self.queue:
                    _wo._queue_entry_hour = getattr(_wo, "_queue_entry_hour", 0.0) + 1.0
                self._start_wo(self.queue.pop(0))
            return records

        wo = self.current_wo
        remaining = wo.qty_planned - wo.qty_good
        capacity = int(self.capacity_per_hour * hours)
        to_process = min(capacity, remaining)

        # Yield decay
        eff_yield = self._compute_yield()
        qty_good = int(to_process * eff_yield)
        qty_defect = to_process - qty_good

        wo.qty_good += qty_good
        wo.qty_defect += qty_defect
        self.total_units_processed += to_process
        self.batches_processed += 1

        if wo.qty_good + wo.qty_defect >= wo.qty_planned:
            records.append(self._make_record(wo, qty_good, qty_defect, eff_yield))
            self.current_wo = None
            # WIP = current_wo only → clear when WO departs
            self.wip = 0  # no current_wo = no WIP

        return records

    def _compute_yield(self) -> float:
        """Yield decay: yield_i = max(0.80, base - k × decay_per_1k)"""
        units_k = self.total_units_processed / 1000.0
        decayed = self.yield_base_rate - units_k * self.yield_decay_per_1k
        return max(0.80, min(decayed, self.yield_base_rate))

    def _make_record(self, wo: Any, qty_good: int, qty_defect: int, yr: float) -> dict:
        return {
            "station_id": self.station_id,
            "wo_id": wo.wo_id,
            "order_id": wo.order_id,
            "product_type": getattr(wo, "product_type", "A"),
            "qty_in": wo.qty_planned,
            "qty_good": qty_good,
            "qty_defect": qty_defect,
            "yield_rate": round(yr, 4),
            "batches_processed": self.batches_processed,
            "total_processed": self.total_units_processed,
            "is_down": self.is_down,
            "downtime_minutes": int(self.downtime_remaining_min) if self.is_down else 0,
        }

    @property
    def avg_wait_time_hours(self) -> float:
        return (self.total_wait_time_hours / self.batches_processed
                if self.batches_processed > 0 else 0.0)

    @property
    def bottleneck_score(self) -> float:
        """bottleneck_score = avg_wait × (1 + WIP/MAX)"""
        return self.avg_wait_time_hours * (1 + self.wip / max(self.max_batch, 1))


# ═══════════════════════════════════════════════════════════════
# StationDispatchLoop — 調度迴圈 + WIP tracking + bottleneck detection
# ═══════════════════════════════════════════════════════════════

class StationDispatchLoop:
    """
    工作站調度迴圈

    責任：
    1. 逐小時步進全線工作站
    2. WIP tracking：追蹤每站 in-progress 數量
    3. Bottleneck detection：自動偵測瓶頸站
    4. 產出 StationRecord list + daily_snapshot
    """

    def __init__(self, stations: dict[str, Station], ship_modes: list[dict] | None = None,
                     dispatch_policy: str = "FIFO"):
        self.stations = stations
        self.dispatch_policy = dispatch_policy  # FIFO / SPT / EDD
        self._cycle_time_map = {"A": 4.0, "B": 2.5, "C": 6.0}
        self.all_records: list[dict] = []
        self.daily_snapshots: list[dict] = []
        self._warehouse_queue: list[dict] = []
        self._warehouse_shipments: list[dict] = []
        self._ship_modes: list[dict] = ship_modes or [{"name": "standard", "base_days": 2, "jitter_days": 1}]

    def run(self, work_orders: list, sim_days: int) -> list[dict]:
        if not work_orders or not self.stations:
            return []

        # v0.3-fix: pull-based — only inject 1 WO to first station, forward passes it 1×1.
        # Pre-loading all WOs causes S1 to be permanently busy and never releases to S2/S3.
        self._all_work_orders: list = work_orders  # full list for reference
        self._wo_injected: set = set()  # track which WOs have been injected into the line

        # Factory route + station index per WO
        self._wo_factory_route: dict[str, list[str]] = {
            wo.wo_id: wo.station_ids for wo in work_orders
        }
        self._wo_station_idx: dict[str, int] = {
            wo.wo_id: 0 for wo in work_orders
        }

        # Work order pool: WOs not yet injected, ordered by scheduler priority
        self._wo_pool: list = list(work_orders)
        self._wo_pool_idx: int = 0  # next WO to inject

        # Inject first WO only
        first_sid = work_orders[0].station_ids[0]
        if first_sid in self.stations and self._wo_pool:
            first_wo = self._wo_pool.pop(0)
            self.stations[first_sid].add_wo(first_wo)
            self._wo_injected.add(first_wo.wo_id)
            # Apply dispatch policy to S1 queue
            self._reorder_queue(self.stations[first_sid].queue)

        # v0.3: _now_day tracks simulation day for callbacks
        self._now_day: int = 0

        def _forward_cb(next_sid: str, record: dict) -> None:
            """v0.3: Forward completed WO to next station queue.
            Direct queue injection — no WIP touch, no pending hack."""
            _wo_data = {
                "wo_id": record["wo_id"],
                "order_id": record["order_id"],
                "product_type": record.get("product_type", "A"),
                "qty_planned": record["qty_in"],
                "qty_good": record.get("qty_good", 0),
                "qty_defect": record.get("qty_defect", 0),
                "priority": 1,
                "_queue_entry_hour": 0.0,
                "arrival_day": getattr(self._wo_pool[0], "arrival_day", 0) if self._wo_pool else 0,
            }
            if next_sid in self.stations:
                self.stations[next_sid].queue.append(type("_WO", (), _wo_data)())

        def _shipment_cb(record: dict) -> None:
            """Last station completed → send to warehouse queue."""
            wo_id = record.get("wo_id", "")
            self._warehouse_queue.append({
                "wo_id": wo_id,
                "order_id": record["order_id"],
                "product_type": record.get("product_type", "A"),
                "qty": record["qty_good"],
                "completed_day": self._now_day,
            })

        self._forward_callback = _forward_cb
        self._shipment_callback = _shipment_cb

        total_hours = sim_days * 24
        for hour in range(total_hours):
            self._now_day = hour // 24
            # v0.3: Pull-based injection — if S1 queue empty, inject next WO
            first_sid = work_orders[0].station_ids[0] if work_orders else None
            if (first_sid and first_sid in self.stations
                    and not self.stations[first_sid].queue
                    and self._wo_pool):
                next_wo = self._wo_pool.pop(0)
                self.stations[first_sid].add_wo(next_wo)
                self._wo_injected.add(next_wo.wo_id)
                self._reorder_queue(self.stations[first_sid].queue)
            for sid, station in self.stations.items():
                records = station.step(hours=1.0)
                for rec in records:
                    self.all_records.append(rec)
                    # v0.3: Forward completed WO to next station or warehouse
                    self._forward_to_next_station(rec)

            if hour % 24 == 23:
                # v0.3: FIFO warehouse ship at end of each day
                if self._warehouse_queue:
                    _maybe_ship_fifo(self)
                self._take_daily_snapshot(hour // 24 + 1)

        return self.all_records

    def _take_daily_snapshot(self, day: int) -> None:
        snap = {"day": day}
        for sid, s in self.stations.items():
            snap[f"wip_{sid}"] = s.wip
            snap[f"bs_{sid}"] = round(s.bottleneck_score, 3)
            snap[f"down_{sid}"] = s.is_down
        self.daily_snapshots.append(snap)

    def _reorder_queue(self, queue: list) -> None:
        """v0.4: 可插拔排程 — 使用 dispatch_policy.py 的 policy registry。"""
        if not queue:
            return
        ctx = {
            "cycle_time_map": self._cycle_time_map,
            "dispatch_policy": self.dispatch_policy,
        }
        if apply_policy:
            apply_policy(queue, self.dispatch_policy, ctx)
        else:
            # Fallback: inline simple sorts
            if self.dispatch_policy == "SPT":
                queue.sort(key=lambda wo: (
                    self._cycle_time_map.get(getattr(wo, "product_type", "A"), 4.0),
                    getattr(wo, "_queue_entry_hour", 0.0)
                ))
            elif self.dispatch_policy == "EDD":
                for wo in queue:
                    if not hasattr(wo, "due_date_hours"):
                        wo.due_date_hours = float("inf")
                queue.sort(key=lambda wo: getattr(wo, "due_date_hours", float("inf")))

    def _forward_to_next_station(self, record: dict) -> None:
        """
        v0.3: Forward completed WO to next station using _wo_factory_route + _wo_station_idx.
        Station complete → idx+1 → if has next → callback(next_sid, record).
        If last station → callback shipment.
        No more route.list() — factory route is immutable, index advances step by step.
        """
        wo_id = record.get("wo_id", "")
        route = self._wo_factory_route.get(wo_id)
        if not route:
            return
        idx = self._wo_station_idx.get(wo_id, 0)
        if idx + 1 < len(route):
            next_sid = route[idx + 1]
            self._wo_station_idx[wo_id] = idx + 1  # advance position
            if hasattr(self, '_forward_callback') and self._forward_callback:
                self._forward_callback(next_sid, record)
        else:
            if hasattr(self, '_shipment_callback') and self._shipment_callback:
                self._shipment_callback(record)

    @property
    def bottleneck_station(self) -> str:
        if not self.stations:
            return ""
        return max(self.stations.items(), key=lambda kv: kv[1].bottleneck_score)[0]

    @property
    def avg_wip(self) -> float:
        if not self.stations:
            return 0.0
        return sum(s.wip for s in self.stations.values()) / len(self.stations)

    @property
    def total_defects(self) -> int:
        return sum(r.get("qty_defect", 0) for r in self.all_records)

    @property
    def avg_yield_rate(self) -> float:
        if not self.all_records:
            return 0.0
        return sum(r.get("yield_rate", 0) for r in self.all_records) / len(self.all_records)


# ═══════════════════════════════════════════════════════════════
# WIPTrackingMixin — WIP 追蹤擴充
# ═══════════════════════════════════════════════════════════════


# Shipment + Warehouse
@dataclass
class ShipmentRecord:
    shipment_id: str
    order_id: str
    wo_id: str
    ship_date: datetime
    carrier: str
    transit_days: float
    delivery_date: datetime
    on_time: bool
    units_shipped: int = 0

def _maybe_ship_fifo(loop: "StationDispatchLoop") -> None:
    """v0.3: FIFO warehouse — ship oldest queued items each day."""
    if not loop._warehouse_queue:
        return
    # Ship all queued items daily (FIFO: queue is already ordered by completion_day)
    for item in list(loop._warehouse_queue):
        _carrier = item.get("carrier", "standard")
        mode = next((m for m in loop._ship_modes if m["name"] == _carrier),
                    {"base_days": 2, "jitter_days": 1, "cost_per_unit": 5})
        transit = max(0.1, mode["base_days"] + random.uniform(-mode["jitter_days"], mode["jitter_days"]))
        ship_date = datetime(2025, 1, 1) + timedelta(days=item["completed_day"])
        rec = {
            "shipment_id": f"SH{len(loop._warehouse_shipments)+1:05d}",
            "wo_id": item["wo_id"],
            "order_id": item["order_id"],
            "product_type": item.get("product_type", "A"),
            "qty_shipped": item["qty"],
            "completed_day": item["completed_day"],
            "ship_date": ship_date.isoformat(),
            "carrier": item.get("carrier", "陸運"),
            "transit_days": round(transit, 2),
            "delivery_date": (ship_date + timedelta(days=transit)).isoformat(),
        }
        loop._warehouse_shipments.append(rec)
    loop._warehouse_queue.clear()


class Warehouse:
    """v0.3: FIFO warehouse queue + shipment records."""

    def __init__(self, config: dict):
        self.capacity = config.get("capacity", 10000)
        self.ship_modes = config.get("ship_modes", [])
        self.queue: list = []
        self.shipments: list = []

    def receive(self, wo, completed_day, now):
        self.queue.append({
            "wo_id": wo.wo_id, "order_id": wo.order_id,
            "qty": wo.qty_good, "completed_day": completed_day,
            "due_date": getattr(wo, "_due_date", now + timedelta(days=14)),
            "carrier": self.ship_modes[0]["name"] if self.ship_modes else "standard"
        })

    def ship(self, now):
        records = []
        while self.queue:
            item = self.queue.pop(0)
            mode = next((m for m in self.ship_modes if m["name"] == item["carrier"]),
                        {"base_days": 2, "jitter_days": 1, "cost_per_unit": 5})
            transit = max(0.1, mode["base_days"] + random.uniform(-mode["jitter_days"], mode["jitter_days"]))
            rec = ShipmentRecord(
                shipment_id=f"SH{len(self.shipments)+1:05d}",
                order_id=item["order_id"], wo_id=item["wo_id"],
                ship_date=now, carrier=item["carrier"],
                transit_days=transit,
                delivery_date=now + timedelta(days=transit),
                on_time=(now + timedelta(days=transit)) <= item["due_date"],
                units_shipped=item["qty"])
            self.shipments.append(rec)
            records.append(rec)
        return records

class WIPTrackingMixin:
    """WIP tracking mixin：提供 WIP 快照 + 警報 + 瓶頸報告"""

    def get_wip_snapshot(self, loop: StationDispatchLoop) -> dict[str, int]:
        return {sid: s.wip for sid, s in loop.stations.items()}

    def get_bottleneck_report(self, loop: StationDispatchLoop) -> dict:
        stations_info = []
        for sid, s in loop.stations.items():
            stations_info.append({
                "station_id": sid,
                "wip": s.wip,
                "avg_wait_hours": round(s.avg_wait_time_hours, 2),
                "bottleneck_score": round(s.bottleneck_score, 3),
                "is_down": s.is_down,
                "total_processed": s.total_units_processed,
            })
        stations_info.sort(key=lambda x: x["bottleneck_score"], reverse=True)
        bn = stations_info[0] if stations_info else {}
        return {
            "bottleneck_station": bn.get("station_id", ""),
            "score": bn.get("bottleneck_score", 0),
            "stations": stations_info,
        }

    def check_wip_alert(self, loop: StationDispatchLoop, threshold: float = 0.8) -> list[str]:
        alerts = []
        for sid, s in loop.stations.items():
            ratio = s.wip / max(s.max_batch, 1)
            if ratio >= threshold:
                alerts.append(
                    f"[{sid}] WIP {s.wip}/{s.max_batch} ({ratio:.0%}) >= threshold {threshold:.0%}"
                )
        return alerts


# ═══════════════════════════════════════════════════════════════
# SimulationEngineV02 — 擴充版（含 station dispatch loop）
# ═══════════════════════════════════════════════════════════════

class SimulationEngineV02:
    """
    OTD 模擬引擎 v0.3
    
    四階段流程：
        Day 0..N: Order generator → Order (RECEIVED)
                  ↓ Scheduler.sort()
        Day N+1:  WorkOrder (SCHEDULED)
                  ↓ StationDispatchLoop (per-product route)
        Day N+2:  Production (IN_PROGRESS → COMPLETED)
                  ↓ Warehouse FIFO → Shipment
        Day N+3:  Shipment (SHIPPED, on_time=?)
    
    v0.3 擴充：
      [x] Station class — capacity queue + setup + failure + yield decay
      [x] StationDispatchLoop — 逐小時步進 + WIP + bottleneck
      [x] _forward_to_next_station: per-product route (S1→S2→S3 / S1→S2 / S1→S2→S3→S3)
      [x] Warehouse FIFO queue + transit_delay shipment
      [x] _compute_metrics: OTD rate + avg_wip + bottleneck + warehouse_shipments
    
    待 Allen 確認 due_date 格式後：
      [ ] _schedule_orders: 注入排程演算法（EDD / SPT / priority boost）
      [ ] avg_lead_time_days: 從 order arrival → shipment delivery 精確計算
    """

    def __init__(self, config: dict, seed: int | None = None):
        self.config = config
        self.seed = seed or config.get("seed", 42)
        self.rng = random.Random(self.seed)
        self.variants = VariantParams(config.get("parameters", {}), self.rng)
        self.wip_tracker = WIPTrackingMixin()

    def run(self, dispatch_policy: str = "FIFO") -> "SimulationResult":
        from models import Order, WorkOrder, Scheduler, VariantParams, SimulationResult
        sched = Scheduler(rule=self.config.get("scheduling", {}).get("rule", "EDD"))
        variants = VariantParams(self.config.get("parameters", {}), self.rng)
        orders = self._generate_orders(variants)
        wos = self._schedule_orders(orders, sched)

        result = SimulationResult(
            config_version=self.config.get("version", "0.4"),
            seed=self.seed,
        )

        factory = self.config.get("factory", {})
        _last_loop = None
        for line in factory.get("lines", []):
            stations = self._build_stations(line)
            if not stations:
                continue
            _ship_modes = self.config.get("factory", {}).get("warehouse", {}).get("ship_modes",
                [{"name": "standard", "base_days": 2, "jitter_days": 1}])
            loop = StationDispatchLoop(stations, ship_modes=_ship_modes, dispatch_policy=dispatch_policy)
            loop.run(wos, self.config.get("sim_days", 90))
            result.timeline.extend(loop.all_records)
            result.daily_snapshot.extend(loop.daily_snapshots)
            result.total_defects += loop.total_defects
            self._last_loop = loop  # v0.3: keep ref for inspection

        metrics = self._compute_metrics(orders, dispatch_loop=self._last_loop)
        result.otd_rate = metrics.get("otd_rate", 0.0)
        result.otd_count = metrics.get("otd_count", 0)
        result.avg_wip = metrics.get("avg_wip", 0.0)
        result.bottleneck_station = metrics.get("bottleneck_station", "")
        result.total_orders = len(orders)
        result.warehouse_shipments = metrics.get("warehouse_shipments", 0)
        result.avg_lead_time_days = metrics.get("avg_lead_time_days", 0.0)
        return result

    def _build_stations(self, line: dict) -> dict[str, Station]:
        return {s["id"]: Station(s["id"], s) for s in line.get("stations", [])}

    def _generate_orders(self, variants: Any) -> list:
        from models import Order
        orders = []
        sim_days = self.config.get("sim_days", 90)
        template = self.config.get("order_template", {})
        base_pd = template.get("arrival", {}).get("base_per_day", 10)
        for day in range(sim_days):
            daily_qty = variants.demand_spike(base_pd)
            for _ in range(daily_qty):
                is_rush = variants.rush_order()
                orders.append(Order(
                    order_id=f"O{day:04d}{self.rng.randint(0,999):03d}",
                    customer=f"Customer-{self.rng.randint(1,20)}",
                    product_type=self._pick_product(template),
                    quantity=self.rng.randint(50, 500),
                    due_date=datetime(2025, 1, 1) + timedelta(
                        days=self._sample_due_days(template)),
                    priority=2 if is_rush else 1,
                    arrival_day=day,
                    rush=is_rush,
                ))
        return orders

    def _pick_product(self, template: dict) -> str:
        products = template.get("products", [])
        r = self.rng.random() * 100
        cum = 0.0
        for p in products:
            cum += p.get("mix_pct", 0)
            if r < cum:
                return p["type"]
        return products[0]["type"]

    def _sample_due_days(self, template: dict) -> int:
        dd = template.get("due_date", {})
        base = dd.get("base_days", 14)
        jitter = dd.get("jitter_days", 3)
        return base + self.rng.randint(-jitter, jitter)

    def _schedule_orders(self, orders: list, sched: Any) -> list:
        """v0.3: 根據 factory.json product route 分配 station_ids。"""
        from models import WorkOrder
        # Build route lookup: product_type → station_ids
        template = self.config.get("order_template", {})
        _route_map: dict[str, list[str]] = {}
        for p in template.get("products", []):
            ptype = p.get("type", "A")
            stations = p.get("route", [])
            if stations:
                _route_map[ptype] = [f"L1-{s}" if not s.startswith("L1-") else s for s in stations]

        wos = []
        for i, order in enumerate(sched.sort(orders)):
            ptype = getattr(order, "product_type", "A")
            route = _route_map.get(ptype, ["L1-S1", "L1-S2", "L1-S3"])
            wo = WorkOrder(
                wo_id=f"W{i:04d}", order_id=order.order_id,
                line_id="L1", station_ids=route,
                priority=order.priority, qty_planned=order.quantity,
            )
            wo.arrival_day = order.arrival_day
            wo.product_type = ptype  # v0.3: attach product_type for routing trace
            wos.append(wo)
            order.to_scheduled(wo.wo_id, day=order.arrival_day)
        return wos

    def _compute_metrics(self, orders: list, dispatch_loop=None) -> dict:
        """v0.3: OTD rate + avg WIP + bottleneck + avg_lead_time_days."""
        _loop = dispatch_loop or self
        # orders are work orders; build wo_id → order arrival_day map
        _wo_arrival = {getattr(o, 'wo_id', ''): getattr(o, 'arrival_day', 0) for o in orders}

        # v0.3-fix: lead_time = delivery_day - arrival_day (includes transit delay)
        lead_times = []
        for r in _loop._warehouse_shipments:
            arr = _wo_arrival.get(r.get("wo_id", ""), 0)
            # delivery_date is ISO string; extract day delta from arrival
            dd_str = r.get("delivery_date", "")
            if dd_str:
                try:
                    from datetime import datetime
                    dd = datetime.fromisoformat(dd_str)
                    delivery_day = (dd - datetime(2025, 1, 1)).days
                except Exception:
                    delivery_day = r.get("completed_day", 0) + r.get("transit_days", 0)
            else:
                delivery_day = r.get("completed_day", 0) + r.get("transit_days", 0)
            lt = delivery_day - arr
            if lt > 0:
                lead_times.append(round(lt, 1))
        avg_lead = round(sum(lead_times) / len(lead_times), 1) if lead_times else 0.0

        # OTD rate: on-time shipments / total work orders
        on_time = sum(1 for r in _loop._warehouse_shipments if r.get("otd", True))
        total = len(orders)
        otd = round(on_time / total, 4) if total else 0.0

        return {
            "otd_rate": otd,
            "otd_count": on_time,
            "avg_wip": round(_loop.avg_wip, 1),
            "bottleneck_station": _loop.bottleneck_station,
            "total_defects": _loop.total_defects,
            "avg_yield_rate": round(_loop.avg_yield_rate, 4),
            "warehouse_shipments": len(_loop._warehouse_shipments),
            "avg_lead_time_days": avg_lead,
        }


# ═══════════════════════════════════════════════════════════════
# DueDateAdapter — OTD v0.5 (五格式: iso8601/epoch/arrival_plus_N/product_lead/default)
# ═══════════════════════════════════════════════════════════════

class DueDateAdapter:
    """Compute due_date from config for given order + product_type.

    Formats:
      - iso8601: overrides[order_id] as ISO string ("2025-06-15" / "2025-06-15T14:00:00")
      - epoch: overrides[order_id] as Unix timestamp
      - arrival_plus_N: arrival_day + arrival_plus_days
      - product_lead: arrival_day + product.lead_time_days
      - default: arrival_day + base_days ± jitter_days

    All formats fall back to arrival_day + base_days when no override exists.
    """

    def __init__(self, config: dict):
        dd = config.get("order_template", {}).get("due_date", {})
        self.format = dd.get("format", "default")
        self.base_days = dd.get("base_days", 14)
        self.jitter_days = dd.get("jitter_days", 3)
        self.arrival_plus_days = dd.get("arrival_plus_days", 7)
        self.overrides = dd.get("overrides", {})
        self._products: dict[str, int] = {}
        for p in config.get("order_template", {}).get("products", []):
            self._products[p["type"]] = p.get("lead_time_days", 10)

    def compute(self, order_id: str, product_type: str, arrival_day: int,
                rng=None) -> datetime:
        from datetime import datetime, timedelta
        # Check override
        oid = self.overrides.get(order_id)

        if self.format == "iso8601":
            return self._parse_iso(oid, arrival_day)
        elif self.format == "epoch":
            return self._parse_epoch(oid, arrival_day)
        elif self.format == "arrival_plus_N":
            return datetime(2025, 1, 1) + timedelta(days=max(arrival_day, 0) + self.arrival_plus_days)
        elif self.format == "product_lead":
            lead = self._products.get(product_type, self.base_days)
            return datetime(2025, 1, 1) + timedelta(days=max(arrival_day, 0) + lead)
        else:
            # default / unknown → base_days ± jitter
            return self._fallback_default(arrival_day, rng)

    def _parse_iso(self, override: str | None, arrival_day: int):
        from datetime import datetime, timedelta
        if override:
            try:
                return datetime.fromisoformat(override)
            except (ValueError, TypeError):
                pass
        # No override → fallback to arrival + base_days (deterministic, no jitter)
        return datetime(2025, 1, 1) + timedelta(days=max(arrival_day, 0) + self.base_days)

    def _parse_epoch(self, override: str | None, arrival_day: int):
        from datetime import datetime, timedelta
        if override is not None:
            try:
                return datetime.utcfromtimestamp(int(override))
            except (ValueError, TypeError):
                pass
        # No override → fallback to arrival + base_days (deterministic, no jitter)
        return datetime(2025, 1, 1) + timedelta(days=max(arrival_day, 0) + self.base_days)

    def _fallback_default(self, arrival_day: int, rng=None) -> datetime:
        from datetime import datetime, timedelta
        import random as _random
        r = rng or _random
        jitter = r.randint(-self.jitter_days, self.jitter_days) if self.jitter_days else 0
        return datetime(2025, 1, 1) + timedelta(days=max(arrival_day, 0) + self.base_days + jitter)

    def __repr__(self):
        return f"DueDateAdapter(format={self.format!r}, base_days={self.base_days}, jitter_days={self.jitter_days})"
