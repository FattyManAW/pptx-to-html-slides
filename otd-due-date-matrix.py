"""
otd-due-date-matrix.py — Sprint 2 T2 五格式 × 三政策 15 組合矩陣
DueDateAdapter 五格式 × dispatch_policy 三政策 = 15 組合全跑
產出 due_date_matrix.json + otd-due-date-comparison.html
"""
import json, sys, os, copy
from datetime import datetime

sys.path.insert(0, '/Users/henry/Documents/任務檔案/投影片轉換/showcase/otd-sim')
sys.path.insert(0, '/Users/henry/Documents/任務檔案/投影片轉換')

from station_dispatch import Station, StationDispatchLoop, WIPTrackingMixin
import models as sim_models

FACTORY = '/Users/henry/Documents/任務檔案/投影片轉換/showcase/otd-sim/factory.json'
OUT_JSON = '/Users/henry/Documents/任務檔案/投影片轉換/showcase/otd-sim/due_date_matrix.json'
OUT_HTML = '/Users/henry/Documents/任務檔案/投影片轉換/showcase/otd-due-date-comparison.html'

FORMATS = ["default", "iso8601", "epoch", "arrival_plus_N", "product_lead"]
POLICIES_LIST = ["FIFO", "SPT", "EDD"]

def load_config():
    with open(FACTORY) as f:
        return json.load(f)

def build_stations(cfg):
    stations = {}
    for line in cfg.get("factory", {}).get("lines", []):
        for st_cfg in line.get("stations", []):
            stations[st_cfg["id"]] = Station(st_cfg["id"], st_cfg)
    return stations

def patch_format(cfg, fmt):
    """對 config 做 due_date format 修改（deep copy 後使用）"""
    cfg['order_template']['due_date']['format'] = fmt
    if fmt == 'arrival_plus_N':
        cfg['order_template']['due_date']['arrival_plus_days'] = 7
    elif fmt == 'product_lead':
        for p in cfg['order_template']['products']:
            if 'lead_time_days' not in p:
                p['lead_time_days'] = max(1, int(p.get('cycle_time_hrs', 4) / 8))

def compute_metrics(cfg, loop, orders):
    """計算 OTD / avg_lead / bottleneck / WIP alerts"""
    tracker = WIPTrackingMixin()
    bn_report = tracker.get_bottleneck_report(loop)
    alerts = tracker.check_wip_alert(loop)

    shipped = len(loop._warehouse_shipments)
    on_time = sum(1 for s in loop._warehouse_shipments if s.get("otd", True))

    lead_times = []
    for sh in loop._warehouse_shipments:
        oid = sh.get("order_id", "")
        arr = next((o.arrival_day for o in orders if o.order_id == oid), 0)
        dd_str = sh.get("delivery_date", "")
        if dd_str:
            try:
                dd = datetime.fromisoformat(dd_str)
                delivery_day = (dd - datetime(2025, 1, 1)).days
            except:
                delivery_day = sh.get("completed_day", 0) + sh.get("transit_days", 0)
        else:
            delivery_day = sh.get("completed_day", 0) + sh.get("transit_days", 0)
        lt = delivery_day - arr
        if lt > 0:
            lead_times.append(lt)
    avg_lead = round(sum(lead_times) / len(lead_times), 1) if lead_times else 0.0

    all_wait = [s.avg_wait_time_hours for s in loop.stations.values() if s.batches_processed > 0]
    avg_wait = round(sum(all_wait) / len(all_wait), 1) if all_wait else 0.0

    return {
        'otd': round(on_time / shipped * 100, 1) if shipped else 0.0,
        'on_time_rate': round(on_time / shipped, 4) if shipped else 0.0,
        'avg_lead_days': avg_lead,
        'avg_queue_wait_hrs': avg_wait,
        'bottleneck': bn_report.get("bottleneck_station", ""),
        'bottleneck_score': bn_report.get("score", 0),
        'wip_alerts': alerts,
        'shipped': shipped,
        'total_orders': len(orders),
        'overdue': shipped - on_time,
        'defects': loop.total_defects,
        'avg_wip': round(loop.avg_wip, 2),
    }

def main():
    base_cfg = load_config()
    all_results = []
    total_combos = len(FORMATS) * len(POLICIES_LIST)
    done = 0

    print(f"{'='*60}")
    print(f"  OTD Due Date Matrix — 5 formats × 3 policies = {total_combos} combos")
    print(f"{'='*60}")

    for fmt in FORMATS:
        cfg = copy.deepcopy(base_cfg)
        patch_format(cfg, fmt)
        stations = build_stations(cfg)

        for pol in POLICIES_LIST:
            done += 1
            try:
                sim = sim_models.SimulationEngine(cfg, seed=42)
                sim.scheduler.rule = pol
                orders = sim._generate_orders()
                wos = sim._schedule_orders(orders)

                loop = StationDispatchLoop(stations, dispatch_policy=pol)
                loop.run(wos, cfg.get('sim_days', 90))

                m = compute_metrics(cfg, loop, orders)
                rec = {
                    'format': fmt,
                    'policy': pol,
                    **m
                }
                all_results.append(rec)
                print(f"  [{done:02d}/{total_combos}] {fmt:18s} × {pol:5s} → "
                      f"OTD={m['otd']:.1f}% lead={m['avg_lead_days']:.1f}d "
                      f"WIP={m['avg_wip']:.2f} BN={m['bottleneck']}")
            except Exception as e:
                print(f"  [{done:02d}/{total_combos}] {fmt:18s} × {pol:5s} → ERR: {e}")
                all_results.append({'format': fmt, 'policy': pol, 'error': str(e)})

    # Save JSON
    with open(OUT_JSON, 'w') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\n📁 JSON → {OUT_JSON}")

    # Print summary table
    print(f"\n{'='*75}")
    print(f"  Matrix Summary")
    print(f"{'='*75}")
    print(f"  {'Format':<18} {'Policy':<6} {'OTD%':>7} {'Lead':>7} {'WIP':>6} {'Bottleneck':<14} {'Alerts':>7}")
    print(f"  {'-'*18} {'-'*6} {'-'*7} {'-'*7} {'-'*6} {'-'*14} {'-'*7}")
    for r in sorted(all_results, key=lambda x: x.get('otd', 0), reverse=True):
        if 'error' in r:
            print(f"  {r['format']:<18} {r['policy']:<6} ERR: {r['error'][:40]}")
            continue
        alert_str = '⚠️' + str(r['wip_alerts'][:20]) if r['wip_alerts'] else '✅'
        print(f"  {r['format']:<18} {r['policy']:<6} {r['otd']:>6.1f}% {r['avg_lead_days']:>6.1f}d "
              f"{r['avg_wip']:>5.2f}  {r['bottleneck']:<14} {alert_str:>7}")

    # Best combo
    valid = [r for r in all_results if 'error' not in r]
    if valid:
        best = max(valid, key=lambda x: x['otd'])
        print(f"\n  🏆 Best Combo: {best['format']} × {best['policy']} (OTD={best['otd']}%)")

    print(f"\n  Total: {len(all_results)}/{total_combos} combos completed")

if __name__ == "__main__":
    main()
