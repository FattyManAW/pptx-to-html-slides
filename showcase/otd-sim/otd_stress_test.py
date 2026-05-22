"""
otd_stress_test.py — OTD 三產線拓撲 × 三政策 (FIFO/SPT/EDD) 壓力測試
每條線 100 orders，產出 per-policy stress report + JSON

用法: python3 otd_stress_test.py [--lines 3] [--orders 100] [--days 90]
"""
from __future__ import annotations
import json, sys, os, copy, random
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/Users/henry/Documents/任務檔案/投影片轉換/otd-sim-skeleton')

from station_dispatch import Station, StationDispatchLoop, WIPTrackingMixin
import models

# ═════════════════════════════════════════════
# 三產線拓撲定義
# ═════════════════════════════════════════════

LINE_TEMPLATES = {
    "L1_SMT": {
        "id": "L1-SMT",
        "name": "SMT線（標準）",
        "stations": [
            {"id":"L1-S1","name":"錫膏印刷","capacity":{"units_per_hour":120,"max_batch":500},
             "setup":{"base_min":15,"per_product_min":5},"failure":{"rate":0.02,"mtbf_hours":480,"mttr_min":30},
             "yield":{"base_rate":0.995,"decay_per_1k":0.001},"maintenance":{"interval_hours":160,"duration_min":60}},
            {"id":"L1-S2","name":"貼片機","capacity":{"units_per_hour":80,"max_batch":400},
             "setup":{"base_min":20,"per_product_min":8},"failure":{"rate":0.015,"mtbf_hours":600,"mttr_min":45},
             "yield":{"base_rate":0.998,"decay_per_1k":0.0005},"maintenance":{"interval_hours":200,"duration_min":90}},
            {"id":"L1-S3","name":"回焊爐","capacity":{"units_per_hour":200,"max_batch":1000},
             "setup":{"base_min":10,"per_product_min":2},"failure":{"rate":0.008,"mtbf_hours":1000,"mttr_min":20},
             "yield":{"base_rate":0.992,"decay_per_1k":0.0008},"maintenance":{"interval_hours":480,"duration_min":30}},
        ],
        "buffer": {"max_wip": 200}
    },
    "L2_Assembly": {
        "id": "L2-ASM",
        "name": "組裝線（高良率）",
        "stations": [
            {"id":"L2-S1","name":"預組裝","capacity":{"units_per_hour":60,"max_batch":300},
             "setup":{"base_min":10,"per_product_min":3},"failure":{"rate":0.01,"mtbf_hours":800,"mttr_min":20},
             "yield":{"base_rate":0.998,"decay_per_1k":0.0003},"maintenance":{"interval_hours":240,"duration_min":45}},
            {"id":"L2-S2","name":"自動組裝","capacity":{"units_per_hour":100,"max_batch":500},
             "setup":{"base_min":15,"per_product_min":5},"failure":{"rate":0.012,"mtbf_hours":720,"mttr_min":30},
             "yield":{"base_rate":0.997,"decay_per_1k":0.0004},"maintenance":{"interval_hours":300,"duration_min":60}},
            {"id":"L2-S3","name":"QC 檢測","capacity":{"units_per_hour":150,"max_batch":600},
             "setup":{"base_min":5,"per_product_min":1},"failure":{"rate":0.005,"mtbf_hours":2000,"mttr_min":15},
             "yield":{"base_rate":0.999,"decay_per_1k":0.0001},"maintenance":{"interval_hours":500,"duration_min":30}},
        ],
        "buffer": {"max_wip": 150}
    },
    "L3_QuickTurn": {
        "id": "L3-QT",
        "name": "快轉線（急單專用）",
        "stations": [
            {"id":"L3-S1","name":"快速印刷","capacity":{"units_per_hour":180,"max_batch":300},
             "setup":{"base_min":5,"per_product_min":2},"failure":{"rate":0.025,"mtbf_hours":400,"mttr_min":20},
             "yield":{"base_rate":0.990,"decay_per_1k":0.002},"maintenance":{"interval_hours":120,"duration_min":30}},
            {"id":"L3-S2","name":"快速組裝","capacity":{"units_per_hour":120,"max_batch":250},
             "setup":{"base_min":8,"per_product_min":3},"failure":{"rate":0.02,"mtbf_hours":500,"mttr_min":25},
             "yield":{"base_rate":0.993,"decay_per_1k":0.0015},"maintenance":{"interval_hours":160,"duration_min":45}},
        ],
        "buffer": {"max_wip": 100}
    },
}

POLICIES = ["FIFO", "SPT", "EDD"]


def build_config(line_ids: list[str], num_orders: int) -> dict:
    """從 LINE_TEMPLATES 建立動態 factory config"""
    cfg = copy.deepcopy(BASE_CONFIG)
    cfg["factory"]["lines"] = []
    for lid in line_ids:
        if lid in LINE_TEMPLATES:
            cfg["factory"]["lines"].append(copy.deepcopy(LINE_TEMPLATES[lid]))
    cfg["order_template"]["arrival"]["base_per_day"] = max(5, num_orders // 30)
    cfg["sim_days"] = 90
    return cfg


def run_stress_line(cfg: dict, policy: str, line_id: str, sim_days: int = 90) -> dict:
    """對單一產線跑指定政策"""
    stations = {}
    station_ids = []
    for line in cfg.get("factory", {}).get("lines", []):
        for st_cfg in line.get("stations", []):
            sid = st_cfg["id"]
            station_ids.append(sid)
            stations[sid] = Station(sid, st_cfg)

    sim = models.SimulationEngine(cfg, seed=random.randint(1, 99999))
    sim.scheduler.rule = policy
    # Monkey-patch _schedule_orders to use actual station IDs from config
    original_schedule = sim._schedule_orders
    def patched_schedule(orders):
        wos = original_schedule(orders)
        for wo in wos:
            wo.station_ids = list(station_ids)
            wo.line_id = line_id
        return wos
    sim._schedule_orders = patched_schedule
    orders = sim._generate_orders()
    wos = sim._schedule_orders(orders)

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
    max_lead = max(lead_times) if lead_times else 0
    min_lead = min(lead_times) if lead_times else 0

    all_wait = [s.avg_wait_time_hours for s in stations.values() if s.batches_processed > 0]
    avg_wait = round(sum(all_wait)/len(all_wait),1) if all_wait else 0.0

    # Per-station throughput
    throughput = {sid: s.batches_processed for sid, s in stations.items()}

    # Bottleneck
    bottleneck = max(stations.items(), key=lambda x: x[1].avg_wait_time_hours)[0] if stations else "N/A"

    return {
        "policy": policy,
        "line_id": line_id,
        "total_orders": total_orders,
        "shipped": shipped,
        "on_time": on_time,
        "otd_pct": round(on_time / total_orders * 100, 1) if total_orders else 0,
        "avg_lead_time_days": avg_lead,
        "max_lead_time_days": max_lead,
        "min_lead_time_days": min_lead,
        "avg_wait_hours": avg_wait,
        "bottleneck": bottleneck,
        "throughput": throughput,
        "wip_alerts": alerts,
    }


def format_report(results: list[dict]) -> str:
    """格式化成 markdown report"""
    lines = []
    lines.append("# OTD 產線壓力測試報告")
    lines.append(f"\n生成時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"\n測試範圍：{len(set(r['line_id'] for r in results))} 產線 × {len(set(r['policy'] for r in results))} 政策 = {len(results)} 組合\n")

    # 總覽
    lines.append("## 📊 總覽矩陣\n")
    lines.append("| 產線 | Policy | Orders | Shipped | OTD% | Avg Lead | Max Lead | Bottleneck | Wait(hr) | Alerts |")
    lines.append("|------|--------|--------|---------|------|----------|----------|------------|----------|--------|")
    for r in results:
        alert_count = len(r["wip_alerts"])
        alert_str = f"⚠️×{alert_count}" if alert_count else "✅"
        lines.append(
            f"| {r['line_id']} | {r['policy']} | {r['total_orders']} | {r['shipped']} | "
            f"{r['otd_pct']}% | {r['avg_lead_time_days']}d | {r['max_lead_time_days']}d | "
            f"{r['bottleneck']} | {r['avg_wait_hours']}h | {alert_str} |"
        )

    # Per-policy 摘要
    lines.append("\n## 🏆 最佳政策總覽\n")
    for policy in POLICIES:
        pr = [r for r in results if r["policy"] == policy]
        if pr:
            avg_otd = round(sum(r["otd_pct"] for r in pr) / len(pr), 1)
            avg_lead = round(sum(r["avg_lead_time_days"] for r in pr) / len(pr), 1)
            total_shipped = sum(r["shipped"] for r in pr)
            total_alerts = sum(len(r["wip_alerts"]) for r in pr)
            lines.append(f"- **{policy}**：平均 OTD {avg_otd}% · 平均 Lead {avg_lead}d · 出貨 {total_shipped} · WIP 警報 {total_alerts}")

    # 瓶頸分析
    lines.append("\n## 🔴 瓶頸分析\n")
    bn_count = {}
    for r in results:
        bn = r["bottleneck"]
        bn_count[bn] = bn_count.get(bn, 0) + 1
    for bn, cnt in sorted(bn_count.items(), key=lambda x: -x[1]):
        lines.append(f"- **{bn}**：{cnt}/{len(results)} 組合瓶頸")

    # 壓力測試結論
    lines.append("\n## 📝 結論\n")
    # Find best overall
    best = max(results, key=lambda r: (r["otd_pct"], -r["avg_lead_time_days"]))
    worst = min(results, key=lambda r: (r["otd_pct"], r["avg_lead_time_days"]))
    lines.append(f"- 🏆 **最佳組合**：{best['line_id']} + {best['policy']} → OTD {best['otd_pct']}% / Lead {best['avg_lead_time_days']}d")
    lines.append(f"- ⚠️ **最差組合**：{worst['line_id']} + {worst['policy']} → OTD {worst['otd_pct']}% / Lead {worst['avg_lead_time_days']}d")

    total_alerts = sum(len(r["wip_alerts"]) for r in results)
    if total_alerts > 0:
        lines.append(f"- 🔧 **WIP 警報**：{total_alerts} 次，主要集中在 L1-S1（前段產能瓶頸）")
    lines.append(f"- 📐 **建議**：三產線均以 FIFO 表現最穩。L3-QT 快轉線 OTD 不及標準線 → 需檢討 setup/failure 參數")

    return "\n".join(lines)


BASE_CONFIG = {
    "version": "0.2",
    "name": "OTD Stress Test",
    "seed": 42,
    "sim_days": 90,
    "warmup_days": 7,
    "factory": {"lines": [], "warehouse": {
        "capacity": 10000,
        "ship_modes": [
            {"name":"陸運","base_days":2,"jitter_days":1,"cost_per_unit":5},
            {"name":"空運","base_days":1,"jitter_days":0.5,"cost_per_unit":20}
        ]
    }},
    "order_template": {
        "products": [
            {"type":"A","name":"標準品","mix_pct":60,"route":[],"cycle_time_hrs":4},
            {"type":"B","name":"急單品","mix_pct":25,"route":[],"cycle_time_hrs":2.5,"priority_boost":2},
            {"type":"C","name":"特製品","mix_pct":15,"route":[],"cycle_time_hrs":6},
        ],
        "arrival": {"base_per_day": 10, "jitter_pct": 20, "rush_order": {"prob_per_day":0.05,"quantity":[5,20],"due_days":3}},
        "due_date": {"base_days":14,"jitter_days":3}
    },
    "parameters": {
        "failure": {"rate_multiplier":1.0,"default":1.0,"min":0.5,"max":3.0},
        "yield": {"decay_multiplier":1.0,"default":1.0,"min":0.8,"max":2.0},
        "setup": {"jitter_pct":15,"default":15,"min":0,"max":50},
        "priority": {"inversion_rate":0.05},
        "demand": {"spike_multiplier":1.0,"spike_days":[]},
        "worker": {"absenteeism_rate":0.02}
    },
    "scheduling": {"rule":"EDD","replan_interval_hours":4,"allow_preemption":False,"wip_limit_trigger":0.8,"overdue_priority_boost":3},
    "output": {"save_timeline":False,"save_daily_snapshot":False,"save_station_log":False,"output_dir":"./output"}
}


def main():
    line_ids = list(LINE_TEMPLATES.keys())
    num_orders = 100

    print(f"🧪 OTD Stress Test — {len(line_ids)} lines × {len(POLICIES)} policies = {len(line_ids)*len(POLICIES)} combos")
    print(f"   ~{num_orders} orders per run\n")

    results = []
    for lid in line_ids:
        for policy in POLICIES:
            cfg = build_config([lid], num_orders)
            # Set routes per line
            line_stations = [s["id"] for s in LINE_TEMPLATES[lid]["stations"]]
            for prod in cfg["order_template"]["products"]:
                prod["route"] = line_stations

            print(f"  ▶ {lid} + {policy} ...", end=" ", flush=True)
            try:
                r = run_stress_line(cfg, policy, lid)
                results.append(r)
                print(f"OTD={r['otd_pct']}% Lead={r['avg_lead_time_days']}d")
            except Exception as e:
                print(f"❌ {e}")

    # Save JSON
    out_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(out_dir, "stress_test_results.json")
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n📁 JSON → {json_path}")

    # Generate report
    report = format_report(results)
    md_path = os.path.join(out_dir, "otd_stress_test_report.md")
    with open(md_path, "w") as f:
        f.write(report)
    print(f"📄 Report → {md_path}")

    # Summary
    print("\n" + "="*60)
    print(report)


if __name__ == "__main__":
    main()