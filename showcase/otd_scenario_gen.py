"""
otd_scenario_gen.py — Realistic Factory Order Scenario Generator
===============================================================
Sprint 3 P4: 生成多情境真實訂單 → 驗證 OTD pipeline 的實際分析能力

情境類型:
  1. normal    — 穩定訂單流，標準交期
  2. rush      — 30% 急單，交期壓縮
  3. overload  — 產能 120% 超載，大量延遲
  4. mixed     — 多產品型 + 多客戶 + 變動交期

產出: CSV per scenario → otd_data_pipeline.py --csv
"""
from __future__ import annotations
import csv
import os
import random
import sys
from datetime import datetime, timedelta
from typing import Any

# ═══════════════════════════════════════════════════════════════
# 產品定義（含處理時間、標準 lead time）
# ═══════════════════════════════════════════════════════════════

PRODUCTS = {
    "A": {"name": "標準型 PCB", "lead_days": 14, "qty_weights": [50, 100, 200, 500], "mix_pct": 0.40},
    "B": {"name": "高頻模組", "lead_days": 21, "qty_weights": [20, 50, 100, 200], "mix_pct": 0.25},
    "C": {"name": "電源供應器", "lead_days": 10, "qty_weights": [100, 200, 500, 1000], "mix_pct": 0.20},
    "D": {"name": "散熱模組", "lead_days": 18, "qty_weights": [30, 60, 120, 300], "mix_pct": 0.10},
    "E": {"name": "連接器", "lead_days": 7, "qty_weights": [200, 500, 1000, 2000], "mix_pct": 0.05},
}

CUSTOMERS = {
    "國內": ["台積電", "聯發科", "鴻海", "廣達", "和碩", "緯創"],
    "國外": ["Apple Inc.", "Samsung", "Dell", "HP", "Cisco", "Nokia"],
}
ALL_CUSTOMERS = CUSTOMERS["國內"] + CUSTOMERS["國外"]


# ═══════════════════════════════════════════════════════════════
# 情境定義
# ═══════════════════════════════════════════════════════════════

SCENARIOS = {
    "normal": {
        "n_orders": 80,
        "days_span": 60,
        "rush_pct": 0.05,
        "lead_mult": 1.0,   # 標準交期
        "desc": "穩定生產 — 每日 1-2 張訂單，標準交期，少量急單",
    },
    "rush": {
        "n_orders": 60,
        "days_span": 30,
        "rush_pct": 0.30,
        "lead_mult": 0.6,   # 交期壓縮 40%
        "desc": "旺季衝刺 — 30% 急單，交期壓縮至 60%，考驗排程彈性",
    },
    "overload": {
        "n_orders": 120,
        "days_span": 45,
        "rush_pct": 0.10,
        "lead_mult": 0.8,
        "desc": "產能超載 — 120 張訂單擠在 45 天內，預期大量延遲",
    },
    "mixed": {
        "n_orders": 100,
        "days_span": 90,
        "rush_pct": 0.15,
        "lead_mult": 1.0,
        "desc": "多產品混合 — 五種產品型、12 家客戶、標準至急單混合",
    },
}


# ═══════════════════════════════════════════════════════════════
# Generator
# ═══════════════════════════════════════════════════════════════

def pick_product() -> str:
    r = random.random()
    cum = 0.0
    for pid, pdef in PRODUCTS.items():
        cum += pdef["mix_pct"]
        if r <= cum:
            return pid
    return "A"


def generate_scenario_csv(
    scenario: str,
    output_dir: str,
    base_date: datetime | None = None,
    seed: int = 42,
) -> str:
    """Generate a CSV for the given scenario."""
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario}. Available: {list(SCENARIOS.keys())}")

    cfg = SCENARIOS[scenario]
    random.seed(seed)
    base = base_date or datetime(2025, 3, 1)

    outpath = os.path.join(output_dir, f"orders_{scenario}.csv")
    with open(outpath, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["order_id", "customer", "product_type", "quantity",
                          "arrival_date", "due_date", "priority", "scenario"])
        for i in range(cfg["n_orders"]):
            order_id = f"S-{scenario[:3].upper()}-{i+1:04d}"
            customer = random.choice(ALL_CUSTOMERS)
            product = pick_product()
            pdef = PRODUCTS[product]
            qty = random.choice(pdef["qty_weights"])

            # Arrival: spread across days_span
            arr_offset = random.randint(0, cfg["days_span"] - 1)
            arr_date = base + timedelta(days=arr_offset)

            # Due date: standard lead × multiplier + jitter
            is_rush = random.random() < cfg["rush_pct"]
            lead = int(pdef["lead_days"] * cfg["lead_mult"] * (0.7 if is_rush else 1.0))
            lead += random.randint(-2, 3)  # natural jitter
            lead = max(3, lead)  # minimum 3 days
            due_date = arr_date + timedelta(days=lead)
            priority = 3 if is_rush else (2 if random.random() < 0.15 else 1)

            writer.writerow([order_id, customer, product, qty,
                             arr_date.strftime("%Y-%m-%d"),
                             due_date.strftime("%Y-%m-%d"),
                             priority, scenario])

    return outpath


def generate_all(output_dir: str, base_date: datetime | None = None) -> dict[str, str]:
    """Generate all scenarios, return {scenario: csv_path}."""
    result = {}
    for scenario in SCENARIOS:
        path = generate_scenario_csv(scenario, output_dir, base_date=base_date)
        result[scenario] = path
        n = SCENARIOS[scenario]["n_orders"]
        desc = SCENARIOS[scenario]["desc"]
        print(f"  ✅ {scenario:12s} → {n} orders ({desc})")
    return result


def print_summary(output_dir: str) -> None:
    """Print a summary of all generated scenarios."""
    print("\n" + "=" * 70)
    print(f"{'Scenario':<14} {'Orders':>7} {'Days':>6} {'Rush%':>6} {'LeadMult':>8} {'Desc'}")
    print("-" * 70)
    for name, cfg in SCENARIOS.items():
        print(f"{name:<14} {cfg['n_orders']:>7} {cfg['days_span']:>6} "
              f"{cfg['rush_pct']:>5.0%} {cfg['lead_mult']:>8.1f}x  {cfg['desc']}")
    print("=" * 70)


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "otd-sim", "scenarios"
    )
    os.makedirs(output, exist_ok=True)
    print("📊 Generating OTD Scenario Orders\n")
    generate_all(output)
    print_summary(output)
    print(f"\n📁 Output directory: {output}")