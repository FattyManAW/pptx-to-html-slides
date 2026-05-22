#!/usr/bin/env python3
"""
generate_timeline.py — Run OTD engine + capture hourly station snapshots → Dashboard timeline.json
"""

import sys, json
from datetime import datetime, timedelta

sys.path.insert(0, ".")
from station_dispatch import SimulationEngineV02, StationDispatchLoop, Station, _maybe_ship_fifo


def main(sim_days=30, seed=42, out_path="timeline.json"):
    with open("factory.json") as f:
        config = json.load(f)
    config["sim_days"] = sim_days
    config["seed"] = seed

    engine = SimulationEngineV02(config, seed=seed)

    # Station names
    names = {}
    for line in config["factory"]["lines"]:
        for s in line["stations"]:
            names[s["id"]] = s["name"]

    # Generate orders + schedule (deterministic: same seed)
    variants = engine.variants
    orders = engine._generate_orders(variants)
    from models import Scheduler
    sched = Scheduler(rule=config.get("scheduling", {}).get("rule", "EDD"))
    wos = engine._schedule_orders(orders, sched)

    # Build fresh stations
    stations = engine._build_stations(config["factory"]["lines"][0])
    ship_modes = config.get("warehouse", {}).get(
        "ship_modes",
        [{"name": "standard", "base_days": 2, "jitter_days": 1}],
    )

    loop = StationDispatchLoop(stations, ship_modes=ship_modes)
    loop._all_work_orders = wos
    loop._wo_injected = set()
    loop._wo_factory_route = {wo.wo_id: wo.station_ids for wo in wos}
    loop._wo_station_idx = {wo.wo_id: 0 for wo in wos}
    loop._wo_pool = list(wos)
    loop._now_day = 0

    # Inject first WO
    first_wo = wos[0]
    if first_wo.station_ids[0] in stations:
        loop._wo_pool.pop(0)
        stations[first_wo.station_ids[0]].add_wo(first_wo)
        loop._wo_injected.add(first_wo.wo_id)

    # Forward callbacks (same as dispatch loop internals)
    def _fwd(next_sid, rec):
        d = {
            "wo_id": rec["wo_id"], "order_id": rec["order_id"],
            "product_type": rec.get("product_type", "A"),
            "qty_planned": rec["qty_in"],
            "qty_good": rec.get("qty_good", 0),
            "qty_defect": rec.get("qty_defect", 0),
            "priority": 1, "_queue_entry_hour": 0.0,
        }
        if next_sid in stations:
            stations[next_sid].queue.append(type("_WO", (), d)())

    def _ship(rec):
        loop._warehouse_queue.append({
            "wo_id": rec.get("wo_id", ""),
            "order_id": rec["order_id"],
            "product_type": rec.get("product_type", "A"),
            "qty": rec["qty_good"],
            "completed_day": loop._now_day,
        })

    loop._forward_callback = _fwd
    loop._shipment_callback = _ship

    frames = []
    base_ts = datetime(2025, 1, 1, 8, 0, 0)
    total_hours = sim_days * 24

    for hour in range(total_hours):
        loop._now_day = hour // 24

        # Pull-based injection: if S1 queue empty, inject next WO
        first_sid = wos[0].station_ids[0] if wos else None
        if (first_sid and first_sid in stations
                and not stations[first_sid].queue and loop._wo_pool):
            nw = loop._wo_pool.pop(0)
            stations[first_sid].add_wo(nw)
            loop._wo_injected.add(nw.wo_id)

        # Step all stations
        for sid, s in stations.items():
            records = s.step(hours=1.0)
            for rec in records:
                loop.all_records.append(rec)
                loop._forward_to_next_station(rec)

        # Warehouse: FIFO ship at end of day
        if loop._warehouse_queue:
            _maybe_ship_fifo(loop)

        # Capture snapshot
        snap_stations = []
        for sid, s in stations.items():
            yr = s._compute_yield()
            snap_stations.append({
                "id": sid,
                "name": names.get(sid, sid),
                "wip": s.wip,
                "processed": s.total_units_processed,
                "yield_rate": round(yr, 4),
                "bottleneck_score": round(s.bottleneck_score, 3),
                "is_down": s.is_down,
                "downtime_min": int(s.downtime_remaining_min) if s.is_down else 0,
            })
        frames.append({
            "ts": (base_ts + timedelta(hours=hour)).isoformat(),
            "day": hour // 24,
            "hour": hour % 24,
            "stations": snap_stations,
        })

    # Write
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(frames, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(frames)} hourly frames → {out_path}")
    print(f"   Format: {{ts, day, hour, stations: [{{id, name, wip, yield_rate, bottleneck_score, is_down}}]}}")
    print(f"   Shipments: {len(loop._warehouse_shipments)}")
    print(f"   Defects: {loop.total_defects}")
    print(f"   First frame:  {frames[0]['ts']}")
    print(f"   Last frame:   {frames[-1]['ts']}")


if __name__ == "__main__":
    d = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    s = int(sys.argv[2]) if len(sys.argv) > 2 else 42
    o = sys.argv[3] if len(sys.argv) > 3 else "timeline.json"
    main(d, s, o)