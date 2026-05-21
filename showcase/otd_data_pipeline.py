"""
otd_data_pipeline.py — OTD Engine 真實數據接入層
================================================
Sprint 3 T1: 從 CSV/API 匯入真實訂單 → OTD engine → Dashboard 自動化

支援格式:
  - CSV (ERP export, 多種 column mapping)
  - JSON API (REST endpoint)
  - 直接 dict list

產出:
  - 標準化 Order objects → SimulationEngine
  - 自動跑三 policy (FIFO/SPT/EDD)
  - 輸出 timeline.json + policy_comparison.json

使用:
  python otd_data_pipeline.py --csv orders.csv
  python otd_data_pipeline.py --api http://erp/api/orders
  python otd_data_pipeline.py --json orders.json
"""

from __future__ import annotations
import csv
import json
import os
import sys
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Any

# Path setup for OTD engine imports
OTD_SIM_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "otd-sim") if "__file__" in dir() else "showcase/otd-sim"
sys.path.insert(0, OTD_SIM_DIR)

import models
from station_dispatch import Station, StationDispatchLoop, WIPTrackingMixin


# ═══════════════════════════════════════════════════════════════
# Column Mapping — 多種 ERP 格式支援
# ═══════════════════════════════════════════════════════════════

# Canonical column names → internal fields
CANONICAL_COLUMNS = {
    # Order ID
    "order_id": "order_id",
    "order_no": "order_id",
    "訂單編號": "order_id",
    "PO Number": "order_id",
    "工單號碼": "order_id",

    # Customer
    "customer": "customer",
    "客戶": "customer",
    "customer_name": "customer",
    "客戶名稱": "customer",
    "Client": "customer",

    # Product type
    "product_type": "product_type",
    "產品類型": "product_type",
    "product_code": "product_type",
    "item_type": "product_type",
    "產品代碼": "product_type",

    # Quantity
    "quantity": "quantity",
    "qty": "quantity",
    "數量": "quantity",
    "order_qty": "quantity",
    "訂單數量": "quantity",

    # Due date (multiple formats)
    "due_date": "due_date",
    "due": "due_date",
    "交期": "due_date",
    "delivery_date": "due_date",
    "required_date": "due_date",
    "出貨日": "due_date",

    # Priority
    "priority": "priority",
    "優先級": "priority",
    "order_priority": "priority",
    "rush": "priority",

    # Arrival / order date
    "arrival_date": "arrival_date",
    "order_date": "arrival_date",
    "下單日": "arrival_date",
    "created_date": "arrival_date",
    "接單日期": "arrival_date",

    # Route (optional)
    "route": "route",
    "產線": "route",
    "production_line": "route",
}


# ═══════════════════════════════════════════════════════════════
# Due Date Parser — 多格式支援
# ═══════════════════════════════════════════════════════════════

def parse_due_date(raw: str, arrival_date: datetime | None = None) -> datetime:
    """Parse due_date from multiple formats.

    Supports:
      - ISO8601: "2026-06-15" / "2026-06-15T18:00:00"
      - Epoch: "1715702400"
      - YYMMDD: "260615" → 2026-06-15
      - Simple: "15" (day of month) → arrival_date.month + 15th
      - "14d" / "+14" → arrival_date + N days
      - "2w" → arrival_date + 14 days
    """
    raw = str(raw).strip()

    if not raw:
        return _default_due(arrival_date)

    # ISO8601
    try:
        return datetime.fromisoformat(raw)
    except (ValueError, TypeError):
        pass

    # Epoch (10-digit unix timestamp)
    if raw.isdigit() and len(raw) >= 10:
        try:
            return datetime.fromtimestamp(int(raw))
        except (OSError, ValueError):
            pass

    # YYMMDD (6-digit)
    if raw.isdigit() and len(raw) == 6:
        try:
            return datetime.strptime(raw, "%y%m%d")
        except ValueError:
            pass

    # Relative: "+N" or "Nd" or "N days"
    if raw.startswith("+") or raw.lower().endswith("d"):
        try:
            n = int(raw.lstrip("+").rstrip("d").rstrip(" days").strip())
            base = arrival_date or datetime.now()
            return base + timedelta(days=n)
        except ValueError:
            pass

    # "Nw" → N weeks
    if raw.lower().endswith("w"):
        try:
            n = int(raw.rstrip("w").rstrip("W").strip())
            base = arrival_date or datetime.now()
            return base + timedelta(weeks=n)
        except ValueError:
            pass

    # Try common date formats
    for fmt in ["%Y/%m/%d", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y%m%d"]:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue

    # Day-of-month: "15" (pad to arrival month)
    if raw.isdigit() and 1 <= int(raw) <= 31 and arrival_date:
        try:
            d = int(raw)
            y, m = arrival_date.year, arrival_date.month
            if d < arrival_date.day:  # next month
                m += 1
                if m > 12:
                    m = 1
                    y += 1
            return datetime(y, m, d)
        except ValueError:
            pass

    # Fallback: default lead time
    return _default_due(arrival_date)


def _default_due(arrival_date: datetime | None = None) -> datetime:
    base = arrival_date or datetime.now()
    return base + timedelta(days=14)


# ═══════════════════════════════════════════════════════════════
# CSV Parser
# ═══════════════════════════════════════════════════════════════

def map_columns(headers: list[str]) -> dict[str, str]:
    """Map CSV column names to canonical field names."""
    mapping = {}
    for h in headers:
        h_clean = h.strip().strip('"').strip("'")
        if h_clean in CANONICAL_COLUMNS:
            mapping[CANONICAL_COLUMNS[h_clean]] = h
    return mapping


def parse_csv(filepath: str, sim_start_date: datetime | None = None) -> list[models.Order]:
    """Parse a CSV file into Order objects.

    The CSV can have any column names — the parser auto-maps them via CANONICAL_COLUMNS.
    Missing fields get sensible defaults.
    """
    orders = []
    sim_start = sim_start_date or datetime(2025, 1, 1)

    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError(f"CSV has no headers: {filepath}")

        col_map = map_columns(reader.fieldnames)

        for i, row in enumerate(reader):
            try:
                # Required: order_id (auto-generate if missing)
                order_id = _get_field(row, col_map, "order_id", f"CSV-{i:04d}")

                # Customer
                customer = _get_field(row, col_map, "customer", "Unknown")

                # Product type (default "A")
                product_type = _get_field(row, col_map, "product_type", "A")

                # Quantity
                qty_str = _get_field(row, col_map, "quantity", "100")
                quantity = int(qty_str) if qty_str.isdigit() else 100

                # Arrival date
                arr_str = _get_field(row, col_map, "arrival_date", None)
                arrival_date = None
                arrival_day_offset = 0
                if arr_str:
                    arrival_date = parse_due_date(arr_str, sim_start)
                    arrival_day_offset = (arrival_date - sim_start).days

                # Due date
                due_str = _get_field(row, col_map, "due_date", None)
                if due_str:
                    due_date = parse_due_date(due_str, arrival_date or sim_start)
                else:
                    due_date = arrival_date + timedelta(days=14) if arrival_date else sim_start + timedelta(days=14)

                # Priority
                pri_str = _get_field(row, col_map, "priority", "1")
                try:
                    priority = int(pri_str)
                except ValueError:
                    priority = 1

                # Route
                route_str = _get_field(row, col_map, "route", None)

                order = models.Order(
                    order_id=order_id,
                    customer=customer,
                    product_type=product_type,
                    quantity=quantity,
                    due_date=due_date,
                    priority=priority,
                    arrival_day=arrival_day_offset,
                )

                # Attach route info for downstream
                if route_str:
                    order._route_hint = route_str

                orders.append(order)

            except Exception as e:
                print(f"  ⚠️ Skipping row {i}: {e}", file=sys.stderr)
                continue

    return orders


def _get_field(row: dict, col_map: dict, field: str, default: Any = None) -> Any:
    """Get a field value from CSV row using column mapping."""
    csv_col = col_map.get(field)
    if csv_col and csv_col in row and row[csv_col]:
        return row[csv_col].strip()
    return default


# ═══════════════════════════════════════════════════════════════
# JSON / Dict Parser
# ═══════════════════════════════════════════════════════════════

def parse_json(filepath: str, sim_start_date: datetime | None = None) -> list[models.Order]:
    """Parse a JSON file into Order objects.

    Expected format:
      [{"order_id": "ORD-001", "customer": "A", "product_type": "A", "quantity": 100, ...}]
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        # Support {"orders": [...]} wrapper
        items = data.get("orders", data.get("data", [data]))
    else:
        items = data

    return parse_dict_list(items, sim_start_date)


def parse_dict_list(items: list[dict], sim_start_date: datetime | None = None) -> list[models.Order]:
    """Parse a list of dicts into Order objects."""
    orders = []
    sim_start = sim_start_date or datetime(2025, 1, 1)

    for i, item in enumerate(items):
        order_id = item.get("order_id") or item.get("order_no") or f"DICT-{i:04d}"
        customer = item.get("customer", "Unknown")
        product_type = item.get("product_type", "A")
        quantity = int(item.get("quantity", item.get("qty", 100)))

        # Arrival
        arr_str = item.get("arrival_date") or item.get("order_date")
        arrival_date = None
        arrival_day_offset = 0
        if arr_str:
            arrival_date = parse_due_date(str(arr_str), sim_start)
            arrival_day_offset = (arrival_date - sim_start).days

        # Due date
        due_str = item.get("due_date") or item.get("due")
        if due_str:
            due_date = parse_due_date(str(due_str), arrival_date or sim_start)
        else:
            due_date = (arrival_date or sim_start) + timedelta(days=14)

        priority = int(item.get("priority", 1))

        order = models.Order(
            order_id=order_id,
            customer=customer,
            product_type=product_type,
            quantity=quantity,
            due_date=due_date,
            priority=priority,
            arrival_day=arrival_day_offset,
        )
        orders.append(order)

    return orders


# ═══════════════════════════════════════════════════════════════
# API Fetcher
# ═══════════════════════════════════════════════════════════════

def fetch_api(url: str, api_token: str | None = None) -> list[models.Order]:
    """Fetch orders from a REST API endpoint.

    Expected API response: JSON list or {"orders": [...]} wrapper.
    """
    import urllib.request
    import urllib.error

    headers = {"Accept": "application/json"}
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.URLError as e:
        raise RuntimeError(f"API fetch failed: {e}") from e

    if isinstance(data, dict):
        items = data.get("orders", data.get("data", [data]))
    else:
        items = data

    return parse_dict_list(items)


# ═══════════════════════════════════════════════════════════════
# Pipeline Runner — CSV/API → OTD Engine → Dashboard
# ═══════════════════════════════════════════════════════════════

def run_pipeline(
    orders: list[models.Order],
    factory_config_path: str | None = None,
    policies: list[str] | None = None,
    sim_days: int = 90,
    output_dir: str | None = None,
    seed: int = 42,
) -> dict:
    """Run the full OTD pipeline: orders → engine → results.

    Args:
        orders: Parsed Order objects
        factory_config_path: Path to factory.json (default: otd-sim/factory.json)
        policies: Policies to compare (default: ["FIFO", "SPT", "EDD"])
        sim_days: Simulation days
        output_dir: Output directory (default: otd-sim/)
        seed: Random seed

    Returns:
        dict with results + output paths
    """
    if not orders:
        return {"error": "No orders to process", "results": []}

    if factory_config_path is None:
        factory_config_path = os.path.join(OTD_SIM_DIR, "factory.json")
    if policies is None:
        policies = ["FIFO", "SPT", "EDD"]
    if output_dir is None:
        output_dir = OTD_SIM_DIR

    # Load factory config
    with open(factory_config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    # Build stations
    stations = {}
    for line in cfg.get("factory", {}).get("lines", []):
        for st_cfg in line.get("stations", []):
            stations[st_cfg["id"]] = Station(st_cfg["id"], st_cfg)

    results = []
    for policy in policies:
        print(f"  ▶ Running {policy} with {len(orders)} real orders...")

        # Fresh engine per policy
        sim = models.SimulationEngine(cfg, seed=seed)
        sim.orders = orders  # Inject real orders
        sim.scheduler.rule = policy

        # Generate work orders from real orders
        wos = sim._schedule_orders(orders)

        # Run dispatch loop
        loop = StationDispatchLoop(stations, dispatch_policy=policy)
        loop.run(wos, sim_days)

        # Metrics
        tracker = WIPTrackingMixin()
        bn_report = tracker.get_bottleneck_report(loop)
        alerts = tracker.check_wip_alert(loop)

        shipped = len(loop._warehouse_shipments)
        on_time = sum(1 for s in loop._warehouse_shipments if s.get("otd", True))

        lead_times = []
        for sh in loop._warehouse_shipments:
            arr_day = next(
                (o.arrival_day for o in orders if o.order_id == sh.get("order_id", "")),
                0,
            )
            dd_str = sh.get("delivery_date", "")
            if dd_str:
                try:
                    dd = datetime.fromisoformat(dd_str)
                    delivery_day = (dd - datetime(2025, 1, 1)).days
                except (ValueError, TypeError):
                    delivery_day = sh.get("completed_day", 0) + sh.get("transit_days", 0)
            else:
                delivery_day = sh.get("completed_day", 0) + sh.get("transit_days", 0)
            lt = delivery_day - arr_day
            if lt > 0:
                lead_times.append(lt)

        avg_lead = round(sum(lead_times) / len(lead_times), 1) if lead_times else 0.0

        all_wait = [s.avg_wait_time_hours for s in stations.values() if s.batches_processed > 0]
        avg_wait = round(sum(all_wait) / len(all_wait), 1) if all_wait else 0.0

        throughput = {sid: s.total_units_processed for sid, s in stations.items()}

        results.append({
            "policy": policy,
            "total_orders": len(orders),
            "shipped": shipped,
            "on_time": on_time,
            "overdue": shipped - on_time,
            "avg_lead_days": avg_lead,
            "on_time_rate": round(on_time / len(orders), 4) if orders else 0.0,
            "avg_queue_wait_hrs": avg_wait,
            "avg_yield_rate": round(loop.avg_yield_rate, 4),
            "bottleneck_station": bn_report.get("bottleneck_station", ""),
            "bottleneck_score": bn_report.get("score", 0),
            "station_throughput": throughput,
            "wip_alerts": alerts,
            "total_defects": loop.total_defects,
            "records": len(loop.all_records),
        })

    # Rank by shipped
    results.sort(key=lambda x: x["shipped"], reverse=True)
    best = results[0] if results else None

    # Write outputs
    os.makedirs(output_dir, exist_ok=True)

    # Policy comparison
    comparison_path = os.path.join(output_dir, "policy_comparison.json")
    with open(comparison_path, "w", encoding="utf-8") as f:
        json.dump({
            "run_at": datetime.now().isoformat(),
            "source": "real_data",
            "order_count": len(orders),
            "seed": seed,
            "sim_days": sim_days,
            "results": results,
        }, f, indent=2, ensure_ascii=False)

    # Generate sample CSV for demo
    sample_csv_path = os.path.join(output_dir, "sample_orders.csv")
    _write_sample_csv(sample_csv_path)

    return {
        "source": "real_data",
        "order_count": len(orders),
        "results": results,
        "best_policy": best["policy"] if best else None,
        "best_otd": best["on_time_rate"] if best else 0.0,
        "output_files": {
            "policy_comparison": comparison_path,
            "sample_csv": sample_csv_path,
        },
    }


# ═══════════════════════════════════════════════════════════════
# Sample CSV Generator (for demo/testing)
# ═══════════════════════════════════════════════════════════════

def _write_sample_csv(path: str, n_orders: int = 50) -> None:
    """Generate a sample CSV for testing."""
    import random
    random.seed(42)

    products = ["A", "A", "A", "B", "B", "C"]  # weighted by mix_pct
    customers = ["客戶甲", "客戶乙", "客戶丙", "Customer-X", "Customer-Y"]
    base_date = datetime(2025, 1, 1)

    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["order_id", "customer", "product_type", "quantity",
                          "arrival_date", "due_date", "priority"])
        for i in range(n_orders):
            order_id = f"REAL-{i+1:04d}"
            customer = random.choice(customers)
            product = random.choice(products)
            qty = random.choice([50, 100, 200, 500, 1000])
            arr_date = base_date + timedelta(days=random.randint(0, 30))
            lead_days = 14 + random.randint(-3, 7)
            due_date = arr_date + timedelta(days=lead_days)
            priority = 2 if random.random() < 0.1 else 1  # 10% rush
            writer.writerow([order_id, customer, product, qty,
                             arr_date.strftime("%Y-%m-%d"),
                             due_date.strftime("%Y-%m-%d"),
                             priority])


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="OTD Data Pipeline — CSV/API → OTD Engine → Dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python otd_data_pipeline.py --csv orders.csv
  python otd_data_pipeline.py --json orders.json
  python otd_data_pipeline.py --api http://erp/api/orders
  python otd_data_pipeline.py --csv orders.csv --policies FIFO,EDD --sim-days 60
  python otd_data_pipeline.py --sample  # Generate sample CSV only
        """,
    )

    parser.add_argument("--csv", help="Path to CSV order file")
    parser.add_argument("--json", help="Path to JSON order file")
    parser.add_argument("--api", help="API endpoint URL for orders")
    parser.add_argument("--api-token", help="Bearer token for API auth")
    parser.add_argument("--policies", default="FIFO,SPT,EDD",
                        help="Comma-separated policies (default: FIFO,SPT,EDD)")
    parser.add_argument("--sim-days", type=int, default=90,
                        help="Simulation days (default: 90)")
    parser.add_argument("--factory-config", help="Path to factory.json")
    parser.add_argument("--output-dir", default=None, help="Output directory")
    parser.add_argument("--sample", action="store_true",
                        help="Generate sample CSV only, don't run simulation")
    parser.add_argument("--start-date", default="2025-01-01",
                        help="Simulation start date (default: 2025-01-01)")

    args = parser.parse_args()

    # Resolve paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    otd_dir = os.path.join(script_dir, "otd-sim")
    factory_config = args.factory_config or os.path.join(otd_dir, "factory.json")
    output_dir = args.output_dir or otd_dir

    # Sample-only mode
    if args.sample:
        sample_path = os.path.join(output_dir, "sample_orders.csv")
        _write_sample_csv(sample_path)
        print(f"✅ Sample CSV written: {sample_path}")
        print(f"   Run with: python {__file__} --csv {sample_path}")
        return

    # Parse orders
    sim_start = datetime.fromisoformat(args.start_date)
    orders = []

    if args.csv:
        print(f"📥 Loading CSV: {args.csv}")
        orders = parse_csv(args.csv, sim_start)
    elif args.json:
        print(f"📥 Loading JSON: {args.json}")
        orders = parse_json(args.json, sim_start)
    elif args.api:
        print(f"📥 Fetching API: {args.api}")
        orders = fetch_api(args.api, args.api_token)
    else:
        # Demo mode: generate sample data
        print("📥 No input specified — generating sample data (50 orders)")
        sample_path = os.path.join(output_dir, "sample_orders.csv")
        _write_sample_csv(sample_path)
        orders = parse_csv(sample_path, sim_start)

    if not orders:
        print("❌ No orders loaded. Exiting.", file=sys.stderr)
        sys.exit(1)

    print(f"   Loaded {len(orders)} orders")

    # Run pipeline
    policies = [p.strip() for p in args.policies.split(",")]
    print(f"\n🔧 Running OTD pipeline ({args.sim_days}d, {len(policies)} policies)")
    print("=" * 65)

    result = run_pipeline(
        orders=orders,
        factory_config_path=factory_config,
        policies=policies,
        sim_days=args.sim_days,
        output_dir=output_dir,
    )

    # Print report
    print()
    print("-" * 65)
    print(f"{'Policy':<10} {'Shipped':>8} {'On-Time':>8} {'OTD%':>7} {'Lead':>7} {'Bottleneck':<12}")
    print("-" * 65)
    for r in result["results"]:
        print(f"{r['policy']:<10} {r['shipped']:>8} {r['on_time']:>8} "
              f"{r['on_time_rate']:>6.1%} {r['avg_lead_days']:>6.1f}d "
              f"{r['bottleneck_station']:<12}")

    print()
    print(f"  📁 Policy comparison: {result['output_files']['policy_comparison']}")
    print(f"  🏆 Best policy: {result['best_policy']} (OTD={result['best_otd']:.1%})")
    print(f"  ✅ Pipeline complete — {len(orders)} real orders processed")


if __name__ == "__main__":
    main()