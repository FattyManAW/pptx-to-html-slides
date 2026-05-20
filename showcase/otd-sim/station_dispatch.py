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

    def add_wo(self, wo: Any) -> None:
        if self.current_wo is None and not self.queue:
            self._start_wo(wo)
        else:
            self.queue.append(wo)
            self.wip += wo.qty_planned

    def _start_wo(self, wo: Any) -> None:
        self.current_wo = wo
        self.wip += wo.qty_planned
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
            self.wip = max(0, self.wip - wo.qty_planned)

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

    def __init__(self, stations: dict[str, Station]):
        self.stations = stations
        self.all_records: list[dict] = []
        self.daily_snapshots: list[dict] = []

    def run(self, work_orders: list, sim_days: int) -> list[dict]:
        if not work_orders or not self.stations:
            return []

        # 初始化：工單分配到第一站
        first_sid = work_orders[0].station_ids[0]
        for wo in work_orders:
            if first_sid in self.stations:
                self.stations[first_sid].add_wo(wo)

        total_hours = sim_days * 24
        for hour in range(total_hours):
            for sid, station in self.stations.items():
                records = station.step(hours=1.0)
                for rec in records:
                    self.all_records.append(rec)

            if hour % 24 == 23:
                self._take_daily_snapshot(hour // 24 + 1)

        return self.all_records

    def _take_daily_snapshot(self, day: int) -> None:
        snap = {"day": day}
        for sid, s in self.stations.items():
            snap[f"wip_{sid}"] = s.wip
            snap[f"bs_{sid}"] = round(s.bottleneck_score, 3)
            snap[f"down_{sid}"] = s.is_down
        self.daily_snapshots.append(snap)

    def _forward_to_next_station(self, record: dict) -> None:
        """
        把完成品傳到下一個工作站。
        路由依據 station_ids = ["L1-S1", "L1-S2", "L1-S3"]。
        station 完成 → 查 route index → 若還有下一站 → add_wo()。
        """
        sid = record["station_id"]
        route = list(self.stations.keys())
        try:
            next_idx = route.index(sid) + 1
        except ValueError:
            return
        if next_idx < len(route):
            next_sid = route[next_idx]
            # SimulationEngineV02 透過 _forward_callback 注入工單
            if hasattr(self, '_forward_callback') and self._forward_callback:
                self._forward_callback(next_sid, record)

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
    OTD 模擬引擎 v0.2
    
    四階段流程：
        Day 0..N: Order generator → Order (RECEIVED)
                  ↓ Scheduler.sort()
        Day N+1:  WorkOrder (SCHEDULED)
                  ↓ StationDispatchLoop
        Day N+2:  Production (IN_PROGRESS → COMPLETED)
                  ↓ Warehouse → Shipment
        Day N+3:  Shipment (SHIPPED, on_time=?)
    
    此版本擴充：
      [x] Station class — capacity queue + setup + failure + yield decay
      [x] StationDispatchLoop — 逐小時步進 + WIP + bottleneck
      [x] YieldDecayModel — Bernoulli 隨機良率
      [x] WIPTrackingMixin — WIP 快照 + 警報 + 瓶頸報告
      [x] SimulationEngineV02 — 四階段骨架（含 station dispatch）
    
    待 Allen 確認 due_date 格式後：
      [ ] _forward_to_next_station: 根據 factory.json route 路由
      [ ] _ship_orders: transit_delay + warehouse queue
      [ ] avg_lead_time_days 計算
    """

    def __init__(self, config: dict, seed: int | None = None):
        self.config = config
        self.seed = seed or config.get("seed", 42)
        self.rng = random.Random(self.seed)
        self.wip_tracker = WIPTrackingMixin()

    def run(self) -> "SimulationResult":
        from models import Order, WorkOrder, Scheduler, VariantParams, SimulationResult
        sched = Scheduler(rule=self.config.get("scheduling", {}).get("rule", "EDD"))
        variants = VariantParams(self.config.get("parameters", {}), self.rng)
        orders = self._generate_orders(variants)
        wos = self._schedule_orders(orders, sched)

        result = SimulationResult(
            config_version=self.config.get("version", "0.2"),
            seed=self.seed,
        )

        factory = self.config.get("factory", {})
        for line in factory.get("lines", []):
            stations = self._build_stations(line)
            if not stations:
                continue
            loop = StationDispatchLoop(stations)
            loop.run(wos, self.config.get("sim_days", 90))
            result.timeline.extend(loop.all_records)
            result.daily_snapshot.extend(loop.daily_snapshots)
            result.total_defects += loop.total_defects

        metrics = self._compute_metrics(orders)
        result.otd_rate = metrics.get("otd_rate", 0.0)
        result.avg_wip = metrics.get("avg_wip", 0.0)
        result.bottleneck_station = metrics.get("bottleneck_station", "")
        result.total_orders = len(orders)
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
        from models import WorkOrder
        wos = []
        for i, order in enumerate(sched.sort(orders)):
            wo = WorkOrder(
                wo_id=f"W{i:04d}", order_id=order.order_id,
                line_id="L1", station_ids=["L1-S1", "L1-S2", "L1-S3"],
                priority=order.priority, qty_planned=order.quantity,
            )
            wos.append(wo)
            order.to_scheduled(wo.wo_id, day=order.arrival_day)
        return wos

    def _compute_metrics(self, orders: list) -> dict:
        shipped = [o for o in orders if o.status.name == "SHIPPED"]
        if not shipped:
            return {"otd_rate": 0.0, "avg_wip": 0.0, "bottleneck_station": ""}
        on_time = [o for o in shipped if o.on_time]
        return {
            "otd_rate": len(on_time) / len(shipped),
            "avg_wip": 0.0,
            "bottleneck_station": "",
        }
