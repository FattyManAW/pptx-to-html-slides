"""
OTD Sim — 四模組骨架 (v0.1-skeleton)
Domain Model stub: Order → Schedule → Production → Shipment

產出後由實作者擴充為完整模擬引擎。
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


# ═══════════════════════════════════════════════════════════════
# MODULE 1 — models.py
# 核心實體定義（Order / Schedule / Production / Shipment）
# ═══════════════════════════════════════════════════════════════


class OrderStatus(str, Enum):
    """訂單狀態機"""
    RECEIVED = "received"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"


@dataclass
class Order:
    """客戶訂單 — 觸發整個 OTD 流程"""

    order_id: str
    customer: str
    product_type: str
    quantity: int
    due_date: datetime
    priority: int = 1
    status: OrderStatus = OrderStatus.RECEIVED
    arrival_day: int = 0
    rush: bool = False

    # 追蹤欄位（實作時自動填充）
    work_order_ids: list[str] = field(default_factory=list)
    scheduled_day: int | None = None
    completed_day: int | None = None
    shipped_day: int | None = None
    on_time: bool | None = None

    # --- 狀態機方法 ---

    def to_scheduled(self, work_order_id: str, day: int) -> None:
        """Transition: RECEIVED → SCHEDULED"""
        assert self.status == OrderStatus.RECEIVED
        self.status = OrderStatus.SCHEDULED
        self.work_order_ids.append(work_order_id)
        self.scheduled_day = day

    def to_in_progress(self, day: int) -> None:
        """Transition: SCHEDULED → IN_PROGRESS"""
        assert self.status == OrderStatus.SCHEDULED
        self.status = OrderStatus.IN_PROGRESS

    def to_completed(self, day: int) -> None:
        """Transition: IN_PROGRESS → COMPLETED"""
        assert self.status == OrderStatus.IN_PROGRESS
        self.status = OrderStatus.COMPLETED
        self.completed_day = day

    def to_shipped(self, delivery_date: datetime, day: int) -> None:
        """Transition: COMPLETED → SHIPPED"""
        assert self.status == OrderStatus.COMPLETED
        self.status = OrderStatus.SHIPPED
        self.shipped_day = day
        self.on_time = delivery_date <= self.due_date


@dataclass
class WorkOrder:
    """工單 — 由 Order 拆分而來"""

    wo_id: str
    order_id: str
    line_id: str
    station_ids: list[str]
    priority: int = 1
    planned_start: datetime | None = None
    planned_end: datetime | None = None
    actual_start: datetime | None = None
    actual_end: datetime | None = None
    qty_planned: int = 0
    qty_good: int = 0
    qty_defect: int = 0

    # 執行記錄（每站完成後疊加）
    station_logs: list[dict[str, Any]] = field(default_factory=list)

    def record_station(self, station_id: str, start: datetime, end: datetime,
                       qty_in: int, qty_out: int, qty_defect: int) -> None:
        """記錄單站加工結果"""
        self.station_logs.append({
            "station_id": station_id,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "qty_in": qty_in,
            "qty_out": qty_out,
            "qty_defect": qty_defect,
        })
        self.qty_good += qty_out
        self.qty_defect += qty_defect


@dataclass
class StationRecord:
    """工作站生產記錄"""

    station_id: str
    wo_id: str
    day: int
    actual_start: datetime
    actual_end: datetime
    units_processed: int
    yield_rate: float
    defect_count: int
    downtime_minutes: int = 0
    failure_event: bool = False


@dataclass
class Shipment:
    """出貨記錄"""

    shipment_id: str
    order_id: str
    ship_date: datetime
    carrier: str
    transit_days: float
    delivery_date: datetime
    on_time: bool


# ═══════════════════════════════════════════════════════════════
# MODULE 2 — scheduler.py
# 排程規則：FIFO / EDD / SPT / CR / Hybrid
# ═══════════════════════════════════════════════════════════════


class Scheduler:
    """排程引擎 — 根據規則對 WorkOrder 排序"""

    def __init__(self, rule: str = "EDD", now_fn=None):
        """
        Args:
            rule: 排程規則名稱 (FIFO / EDD / SPT / CR / Hybrid)
            now_fn:  可注入的時間函數（測試用），預設 datetime.now
        """
        self.rule = rule
        self._now_fn = now_fn or (lambda: datetime.now())

    def sort(self, orders: list[Order], now: datetime | None = None) -> list[Order]:
        """對訂單列表排序，回傳優先順序（高優先級在前）"""
        if now is None:
            now = self._now_fn()

        if self.rule == "FIFO":
            return sorted(orders, key=lambda o: o.arrival_day)
        elif self.rule == "EDD":
            return sorted(orders, key=lambda o: (o.due_date, o.priority))
        elif self.rule == "SPT":
            # TODO: 需要 product_type → cycle_time_hrs 查表
            return sorted(orders, key=lambda o: o.arrival_day)
        elif self.rule == "CR":
            return sorted(orders, key=self._cr_key)
        elif self.rule == "Hybrid":
            return sorted(orders, key=self._hybrid_key)
        else:
            raise ValueError(f"Unknown scheduling rule: {self.rule}")

    def _cr_key(self, order: Order):
        """Critical Ratio = (due - now) / remaining_time"""
        now = self._now_fn()
        remaining = max((order.due_date - now).total_seconds() / 3600, 0.001)
        cr = remaining / 3600  # placeholder: 應代入 remaining_work_hrs
        return (1.0 / (cr + 0.001), order.priority)

    def _hybrid_key(self, order: Order):
        """EDD + WIP limit + overdue boost"""
        overdue = order.due_date < self._now_fn()
        boost = 100 if overdue else (3 if order.priority > 1 else 0)
        return (order.due_date, -boost)


# ═══════════════════════════════════════════════════════════════
# MODULE 3 — variants.py
# 8 個隨機變數注入點
# ═══════════════════════════════════════════════════════════════

import random
import math


class VariantParams:
    """
    工廠模擬中的隨機變異參數。
    所有隨機決策皆由外部傳入的 random.Random(seed) 驅動，
    確保同一 seed 可重現。
    """

    def __init__(self, params: dict, rng: random.Random):
        """
        Args:
            params: 從 config["parameters"] 讀取
            rng:    已設定 seed 的 Random 實例
        """
        self.p = params
        self.rng = rng

    # --- Station-level ---

    def machine_failure(self, station_id: str, hours_operated: float) -> bool:
        """
        Poisson λ/100h 觸發機器故障。
        rate_multiplier 由 config 控制。
        """
        base_rate = self.p.get("failure", {}).get("rate_multiplier", 1.0)
        # TODO: 替換為實際 Poisson 抽樣
        return self.rng.random() < base_rate * hours_operated / 100

    def yield_decay(self, base_rate: float, units_processed: int) -> float:
        """
        良率衰減：linear decay per 1k units
        decay_multiplier 由 config 控制
        """
        decay_mult = self.p.get("yield", {}).get("decay_multiplier", 1.0)
        decay_per_1k = 0.001 * decay_mult
        decayed = base_rate - (units_processed / 1000) * decay_per_1k
        return max(0.80, min(decayed, base_rate))

    def setup_jitter(self, base_min: float) -> float:
        """Normal(μ=base, σ=±30%) 抖動"""
        jitter_pct = self.p.get("setup", {}).get("jitter_pct", 15) / 100
        mu, sigma = base_min, base_min * jitter_pct
        return max(0.0, self.rng.gauss(mu, sigma))

    def worker_absent(self) -> bool:
        """工人缺勤 Bernoulli(p)"""
        p = self.p.get("worker", {}).get("absenteeism_rate", 0.02)
        return self.rng.random() < p

    # --- Schedule-level ---

    def priority_inversion(self) -> bool:
        """優先級翻轉 Bernoulli(p)"""
        p = self.p.get("priority", {}).get("inversion_rate", 0.05)
        return self.rng.random() < p

    # --- Order-level ---

    def rush_order(self) -> bool:
        """急單 Poisson λ/day 觸發"""
        prob = self.p.get("demand", {}).get("rush_order_prob_per_day", 0.05)
        return self.rng.random() < prob

    def demand_spike(self, base_per_day: int) -> int:
        """需求尖峰 multiplier (1.0–3.0×)"""
        spike = self.p.get("demand", {}).get("spike_multiplier", 1.0)
        return int(base_per_day * spike)

    # --- Shipment-level ---

    def transit_delay(self, base_days: float) -> float:
        """
        Log-normal(μ, σ) 運輸延遲。
        均值 = base_days，σ ≈ 0.3 × base_days
        """
        sigma = base_days * 0.3
        mu = math.log(base_days ** 2 / math.sqrt(base_days ** 2 + sigma ** 2))
        result = self.rng.lognormvariate(mu, sigma)
        return max(0.0, result)


# ═══════════════════════════════════════════════════════════════
# MODULE 4 — engine.py
# 模擬引擎骨架：run(config_path, seed) → SimulationResult
# ═══════════════════════════════════════════════════════════════


@dataclass
class SimulationResult:
    """模擬結果容器（骨架）"""

    config_version: str
    seed: int
    otd_rate: float = 0.0
    avg_lead_time_days: float = 0.0
    avg_wip: float = 0.0
    bottleneck_station: str = ""
    total_defects: int = 0
    on_time_orders: int = 0
    late_orders: int = 0
    total_orders: int = 0
    timeline: list[dict[str, Any]] = field(default_factory=list)
    daily_snapshot: list[dict[str, Any]] = field(default_factory=list)

    # TODO: 補 station_log, yield_curve 等


class SimulationEngine:
    """
    工廠 OTD 模擬引擎骨架。

    四階段流程：
        Day 0..N: Order generator → Order (status=RECEIVED)
                  ↓ Scheduler.sort()
        Day N+1:  WorkOrder (status=SCHEDULED)
                  ↓ Station execution
        Day N+2:  Production (status=IN_PROGRESS → COMPLETED)
                  ↓ Warehouse → Shipment
        Day N+3:  Shipment (status=SHIPPED, on_time=?)

    TODO（實作時補充）：
    - [ ] _generate_orders(): Poisson process + rush order
    - [ ] _schedule_orders(): Scheduler.sort() → WorkOrder
    - [ ] _run_production(): Station execution loop with VariantParams
    - [ ] _ship_orders(): Warehouse → Shipment with transit_delay
    - [ ] _compute_metrics(): OTD rate, avg lead time, bottleneck
    """

    def __init__(self, config: dict, seed: int | None = None):
        self.config = config
        self.seed = seed or config.get("seed", 42)
        self.rng = random.Random(self.seed)
        self.scheduler = Scheduler(
            rule=config.get("scheduling", {}).get("rule", "EDD"),
            now_fn=lambda: self.now,
        )
        self.variants = VariantParams(config.get("parameters", {}), self.rng)
        self.now: datetime = datetime.now()  # 模擬時會被覆蓋

    # ── 主入口 ──

    def run(self) -> SimulationResult:
        """執行一次完整模擬，回傳 SimulationResult。"""
        # TODO: 實作四階段
        # 1. generate orders
        # 2. schedule → work orders
        # 3. run production loop
        # 4. ship & compute metrics
        result = SimulationResult(
            config_version=self.config.get("version", "0.1"),
            seed=self.seed,
        )
        return result

    # ── 子階段骨架（待擴充） ──

    def _generate_orders(self) -> list[Order]:
        """TODO: Poisson process order arrival + rush order inject"""
        orders: list[Order] = []
        sim_days = self.config.get("sim_days", 90)
        template = self.config.get("order_template", {})
        arrival = template.get("arrival", {})
        base_per_day = arrival.get("base_per_day", 10)
        rush_cfg = arrival.get("rush_order", {})
        rush_prob = rush_cfg.get("prob_per_day", 0.05)

        for day in range(sim_days):
            daily_qty = self.variants.demand_spike(base_per_day)
            for _ in range(daily_qty):
                is_rush = self.variants.rush_order()
                orders.append(Order(
                    order_id=f"O{day:04d}{self.rng.randint(0,999):03d}",
                    customer=f"Customer-{self.rng.randint(1,20)}",
                    product_type=self._pick_product(template),
                    quantity=self.rng.randint(50, 500),
                    due_date=self.now + timedelta(days=self._sample_due_days(template)),
                    priority=2 if is_rush else 1,
                    arrival_day=day,
                    rush=is_rush,
                ))
        return orders

    def _pick_product(self, template: dict) -> str:
        """根據 mix_pct 隨機選擇產品類型"""
        products = template.get("products", [])
        r = self.rng.random() * 100
        cum = 0.0
        for p in products:
            cum += p.get("mix_pct", 0)
            if r < cum:
                return p["type"]
        return products[0]["type"]

    def _sample_due_days(self, template: dict) -> int:
        """due_date = base_days ± jitter_days"""
        dd = template.get("due_date", {})
        base = dd.get("base_days", 14)
        jitter = dd.get("jitter_days", 3)
        return base + self.rng.randint(-jitter, jitter)

    def _schedule_orders(self, orders: list[Order]) -> list[WorkOrder]:
        """TODO: 將 Order 拆分為 WorkOrder，指派產線/工作站"""
        work_orders: list[WorkOrder] = []
        for i, order in enumerate(self.scheduler.sort(orders)):
            wo = WorkOrder(
                wo_id=f"W{i:04d}",
                order_id=order.order_id,
                line_id="L1",
                station_ids=["L1-S1", "L1-S2", "L1-S3"],
                priority=order.priority,
                qty_planned=order.quantity,
            )
            work_orders.append(wo)
            order.to_scheduled(wo.wo_id, day=order.arrival_day)
        return work_orders

    def _run_production(self, work_orders: list[WorkOrder]) -> list[StationRecord]:
        """v0.2: station dispatch 已移至 StationDispatchLoop。見 showcase/otd-sim/station_dispatch.py"""
        records: list[StationRecord] = []
        return records  # stub — StationDispatchLoop 填充

    def _ship_orders(self) -> list[Shipment]:
        """v0.2: shipment 骨架保留，待 Allen 確認 due_date 格式後注入 transit_delay"""
        return []  # stub — VariantParams.transit_delay() 就緒

    def _compute_metrics(self, orders: list[Order],
                         shipments: list[Shipment]) -> dict[str, float]:
        """計算 OTD rate, avg lead time, bottleneck 等"""
        shipped = [o for o in orders if o.status == OrderStatus.SHIPPED]
        if not shipped:
            return {"otd_rate": 0.0, "avg_lead_time_days": 0.0,
                    "avg_wip": 0.0, "total_defects": 0, "bottleneck_station": ""}
        on_time = [o for o in shipped if o.on_time]
        return {
            "otd_rate": len(on_time) / len(shipped),
            "avg_lead_time_days": 0.0,  # TODO: 從 daily_snapshot 計算
            "avg_wip": 0.0,             # TODO: 從 StationDispatchLoop 取
            "total_defects": 0,         # TODO: 從 StationDispatchLoop 取
            "bottleneck_station": "",   # TODO: 從 StationDispatchLoop 取
        }


# ═══════════════════════════════════════════════════════════════
# EXPANSION v0.2 說明
# ═══════════════════════════════════════════════════════════════
#
# 本次擴充（不依賴 due_date 格式）：
#   [x] Station class — capacity queue + setup time + failure + yield decay
#   [x] StationDispatchLoop — 逐小時步進 + WIP tracking + bottleneck detection
#   [x] YieldDecayModel — Bernoulli 隨機良率（隨處理量遞減）
#   [x] WIPTrackingMixin — WIP 快照 + 警報 + 瓶頸報告
#   [x] SimulationEngineV02 — 四階段骨架（含 station dispatch）
#   [x] models.py _run_production/_compute_metrics 骨架更新
#
# 待 Allen 確認 due_date 格式後注入：
#   [ ] _schedule_orders: 根據 factory.json route 分配工單到各站
#   [ ] _ship_orders: transit_delay + warehouse queue
#   [ ] _forward_to_next_station: 跨站路由邏輯
#   [ ] avg_lead_time_days 計算
#
# 檔案：showcase/otd-sim/models.py (440 行) + station_dispatch.py (588 行)
