"""
OTD v0.4 — Dispatch Policy Layer
Pluggable dispatch rules: FIFO / EDD / SPT

每個 policy 是一個 callable：(queue, context) → sorted queue（in-place）。
擴充新 policy 只需新增一個 function 並註冊到 POLICIES dict。
"""

from __future__ import annotations
from typing import Any, Callable

# ── Policy function signature ──
# def policy(queue: list, ctx: dict) -> None:
#     queue.sort(key=...)

# ═══════════════════════════════════════════════════════════════
# Policy implementations
# ═══════════════════════════════════════════════════════════════

def fifo(queue: list, ctx: dict) -> None:
    """FIFO：先進先出。維持注入順序（arrival_day / queue entry 時間）。"""
    queue.sort(key=lambda wo: getattr(wo, "_queue_entry_hour", 0))

def edd(queue: list, ctx: dict) -> None:
    """EDD：最早交期優先。
    
    因不依賴真實 due_date 格式，使用：
    due_date_hours = arrival_day × 24 + product_cycle_time_hours × qty_planned / base_qty
    為每個 WO 計算一個 reasonable due_date proxy。
    """
    _cycle_map = ctx.get("cycle_time_map", {"A": 4.0, "B": 2.5, "C": 6.0})
    for wo in queue:
        if not hasattr(wo, "due_date_hours") or getattr(wo, "due_date_hours", 0) == 0:
            ptype = getattr(wo, "product_type", "A")
            cycle_hrs = _cycle_map.get(ptype, 4.0)
            arr_day = getattr(wo, "arrival_day", 0)
            qty = getattr(wo, "qty_planned", 100)
            wo.due_date_hours = arr_day * 24 + cycle_hrs * (qty / 100)
    queue.sort(key=lambda wo: (
        getattr(wo, "due_date_hours", float("inf")),
        getattr(wo, "_queue_entry_hour", 0),
    ))

def spt(queue: list, ctx: dict) -> None:
    """SPT：最短處理時間優先。
    
    處理時間 = product_cycle_time_hours × (qty_planned / capacity_per_hour_normalized)
    以 product_type 的 cycle_time_hrs 為基準加權 qty。
    """
    _cycle_map = ctx.get("cycle_time_map", {"A": 4.0, "B": 2.5, "C": 6.0})
    for wo in queue:
        if not hasattr(wo, "spt_score") or getattr(wo, "spt_score", 0) == 0:
            ptype = getattr(wo, "product_type", "A")
            cycle_hrs = _cycle_map.get(ptype, 4.0)
            qty = getattr(wo, "qty_planned", 100)
            wo.spt_score = cycle_hrs * (qty / 100)
    queue.sort(key=lambda wo: (
        getattr(wo, "spt_score", float("inf")),
        getattr(wo, "_queue_entry_hour", 0),
    ))


# ═══════════════════════════════════════════════════════════════
# Policy registry
# ═══════════════════════════════════════════════════════════════

POLICIES: dict[str, Callable[[list, dict], None]] = {
    "FIFO": fifo,
    "EDD": edd,
    "SPT": spt,
}

def get_policy(name: str) -> Callable[[list, dict], None]:
    """取得 registered dispatch policy。不認識的 fallback 到 FIFO。"""
    return POLICIES.get(name.upper(), fifo)

def apply_policy(queue: list, policy_name: str, ctx: dict | None = None) -> None:
    """Apply dispatch policy to queue (reorder in-place)."""
    if ctx is None:
        ctx = {}
    policy_fn = get_policy(policy_name)
    policy_fn(queue, ctx)