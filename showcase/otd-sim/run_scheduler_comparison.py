"""
run_scheduler_comparison.py — OTD v0.4 三政策比較 runner
產出 PolicyScore 報告（text + JSON）
"""
import json, sys, os
from datetime import datetime

sys.path.insert(0, '/Users/henry/Documents/任務檔案/投影片轉換/otd-sim-skeleton')
sys.path.insert(0, os.path.dirname(__file__))

from station_dispatch import Station, StationDispatchLoop, WIPTrackingMixin
import models

def load_config():
    with open('/Users/henry/Documents/任務檔案/投影片轉換/otd-sim-skeleton/factory.json') as f:
        return json.load(f)

def build_stations(cfg):
    stations = {}
    for line in cfg.get("factory", {}).get("lines", []):
        for st_cfg in line.get("stations", []):
            stations[st_cfg["id"]] = Station(st_cfg["id"], st_cfg)
    return stations

def run_single_policy(cfg, policy, sim_days=90):
    stations = build_stations(cfg)
    sim = models.SimulationEngine(cfg, seed=42)
    sim.scheduler.rule = policy           # v0.4: set policy
    orders = sim._generate_orders()
    wos = sim._schedule_orders(orders)   # uses sim.scheduler internally

    loop = StationDispatchLoop(stations, dispatch_policy=policy)
    loop.run(wos, sim_days)

    tracker = WIPTrackingMixin()
    bn_report = tracker.get_bottleneck_report(loop)
    alerts = tracker.check_wip_alert(loop)

    shipped = len(loop._warehouse_shipments)
    on_time = sum(1 for s in loop._warehouse_shipments if s.get("otd", True))
    total_orders = len(wos)

    lead_times = []
    for sh in loop._warehouse_shipments:
        arr = next((o.arrival_day for o in orders if o.order_id == sh.get("order_id","")), 0)
        dd_str = sh.get("delivery_date", "")
        if dd_str:
            try:
                dd = datetime.fromisoformat(dd_str)
                delivery_day = (dd - datetime(2025,1,1)).days
            except:
                delivery_day = sh.get("completed_day",0) + sh.get("transit_days",0)
        else:
            delivery_day = sh.get("completed_day",0) + sh.get("transit_days",0)
        lt = delivery_day - arr
        if lt > 0: lead_times.append(lt)
    avg_lead = round(sum(lead_times)/len(lead_times),1) if lead_times else 0.0

    all_wait = [s.avg_wait_time_hours for s in stations.values() if s.batches_processed > 0]
    avg_wait = round(sum(all_wait)/len(all_wait),1) if all_wait else 0.0
    throughput = {sid: s.total_units_processed for sid, s in stations.items()}

    return {
        "policy": policy,
        "total_orders": total_orders,
        "shipped": shipped,
        "on_time": on_time,
        "overdue": shipped - on_time,
        "avg_lead_days": avg_lead,
        "on_time_rate": round(on_time/total_orders,4) if total_orders else 0.0,
        "avg_queue_wait_hrs": avg_wait,
        "bottleneck_station": bn_report.get("bottleneck_station",""),
        "bottleneck_score": bn_report.get("score",0),
        "station_throughput": throughput,
        "wip_alerts": alerts,
        "total_defects": loop.total_defects,
        "avg_yield_rate": round(loop.avg_yield_rate,4),
        "records": len(loop.all_records),
    }

def main():
    cfg = load_config()
    policies = ["FIFO","SPT","EDD"]
    sim_days = cfg.get("sim_days",90)
    print("="*65)
    print(f"  OTD v0.4 — 排程政策比較報告（{sim_days} 天）")
    print("="*65)
    results = []
    for p in policies:
        print(f"\n▶ Running {p}...")
        r = run_single_policy(cfg, p, sim_days)
        results.append(r)
    results.sort(key=lambda x: x["shipped"], reverse=True)
    print()
    print("-"*65)
    print(f"{'Policy':<10} {'Shipped':>8} {'On-Time':>8} {'OTD%':>7} {'Lead':>7} {'Bottleneck':<12} {'Wait(hr)':>8}")
    print("-"*65)
    for r in results:
        print(f"{r['policy']:<10} {r['shipped']:>8} {r['on_time']:>8} "
              f"{r['on_time_rate']:>6.1%} {r['avg_lead_days']:>6.1f}d "
              f"{r['bottleneck_station']:<12} {r['avg_queue_wait_hrs']:>7.1f}h")
    print()
    print("  📊 Throughput by station:")
    for r in results:
        print(f"    [{r['policy']}] {r['station_throughput']}")
    print()
    print("  🔧 WIP alerts:")
    for r in results:
        print(f"    [{r['policy']}] {'⚠️ ' + str(r['wip_alerts']) if r['wip_alerts'] else '✅ No WIP alerts'}")
    best = results[0]
    print(f"\n  🏆 Best: {best['policy']} (shipped={best['shipped']}, OTD={best['on_time_rate']:.1%})")
    out = {"run_at": datetime.now().isoformat(), "seed":42, "sim_days":sim_days, "results": results}
    out_path = os.path.join(os.path.dirname(__file__), "policy_comparison.json")
    with open(out_path,"w") as f: json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\n  📁 JSON → {out_path}")

if __name__ == "__main__":
    main()
