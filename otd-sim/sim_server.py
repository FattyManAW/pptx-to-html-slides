#!/usr/bin/env python3
"""
sim_server.py — OTD Simulation API Server (:8080)
====================================================
線 D：五個 Agent 即時模擬情境後端。

Endpoints:
  GET  /health          → {"status":"ok","version":"1.0","policies":[...]}
  POST /sim/run         → 執行 OTD 模擬，回傳 SimulationResult
  GET  /sim/stations    → 回傳工作站定義
  GET  /sim/config      → 回傳 factory.json 內容

Usage:
  cd showcase/otd-sim && python3 sim_server.py
  # 預設 port 8080，可設 SIM_PORT 環境變數覆蓋
"""

from __future__ import annotations
import json, os, sys, time
from datetime import datetime, timedelta
from typing import Any, Optional

# ── Path setup: 確保能 import station_dispatch, models ──
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# ── 延遲 import：確保 station_dispatch 在 path 內 ──
from station_dispatch import Station, StationDispatchLoop, WIPTrackingMixin
import models

app = FastAPI(title="OTD Simulation API", version="1.0")

# CORS — 允許 agent-workbench.html 跨域呼叫
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Config ──
CONFIG_PATH = os.path.join(HERE, "factory.json")
if not os.path.exists(CONFIG_PATH):
    raise FileNotFoundError(f"factory.json not found at {CONFIG_PATH}")


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


# ── Pydantic Models ──
class SimRequest(BaseModel):
    policy: str = "EDD"
    sim_days: int = 90
    seed: int = 42
    variant_params: Optional[dict] = None  # optional override: e.g. {"failure": {"rate_multiplier": 1.5}}


class SimResponse(BaseModel):
    policy: str
    total_orders: int
    shipped: int
    on_time: int
    overdue: int
    otd_rate_pct: float
    avg_lead_days: float
    avg_wip: float
    avg_queue_wait_hrs: float
    bottleneck_station: str
    bottleneck_load_pct: float
    total_defects: int
    avg_yield_rate: float
    station_throughput: dict[str, int]
    wip_alerts: list[dict[str, Any]]
    station_metrics: dict[str, dict[str, Any]]
    run_time_ms: float
    seed: int
    sim_days: int


# ── Helper: build stations from config ──
def build_stations(cfg: dict) -> dict[str, Station]:
    stations = {}
    for line in cfg.get("factory", {}).get("lines", []):
        for st_cfg in line.get("stations", []):
            stations[st_cfg["id"]] = Station(st_cfg["id"], st_cfg)
    return stations


# ── Core: run one simulation ──
def run_simulation(cfg: dict, policy: str, sim_days: int, seed: int,
                   variant_params: Optional[dict] = None) -> SimResponse:
    """執行一次模擬，回傳結構化結果"""
    t0 = time.time()

    # Apply variant overrides
    if variant_params:
        for key, val in variant_params.items():
            if key in cfg.get("parameters", {}):
                cfg["parameters"][key].update(val)

    cfg["scheduling"]["rule"] = policy
    cfg["sim_days"] = sim_days
    cfg["seed"] = seed

    stations = build_stations(cfg)

    sim = models.SimulationEngine(cfg, seed=seed)
    sim.scheduler.rule = policy
    orders = sim._generate_orders()
    wos = sim._schedule_orders(orders)

    loop = StationDispatchLoop(stations, dispatch_policy=policy)
    loop.run(wos, sim_days)

    tracker = WIPTrackingMixin()
    bn_report = tracker.get_bottleneck_report(loop)

    shipped = len(loop._warehouse_shipments)
    on_time = sum(1 for s in loop._warehouse_shipments if s.get("otd", True))
    total_orders = len(wos)

    # avg lead time
    lead_times = []
    for sh in loop._warehouse_shipments:
        arr = next((o.arrival_day for o in orders if o.order_id == sh.get("order_id", "")), 0)
        completed = sh.get("completed_day", 0)
        transit = sh.get("transit_days", 0)
        lt = completed + transit - arr
        if lt > 0:
            lead_times.append(lt)
    avg_lead = round(sum(lead_times) / len(lead_times), 1) if lead_times else 0.0

    # avg queue wait
    all_wait = [s.avg_wait_time_hours for s in stations.values() if hasattr(s, 'avg_wait_time_hours') and s.batches_processed > 0]
    avg_wait = round(sum(all_wait) / len(all_wait), 1) if all_wait else 0.0

    # bottleneck load %
    bottleneck_load = bn_report.get("score", 0)
    bottleneck_name = bn_report.get("bottleneck_station", "")

    # station throughput
    throughput = {sid: s.total_units_processed for sid, s in stations.items()}

    # station metrics (deeper)
    station_metrics = {}
    for sid, s in stations.items():
        station_metrics[sid] = {
            "name": s.name,
            "capacity_per_hour": s.capacity_per_hour,
            "units_processed": s.total_units_processed,
            "batches": s.batches_processed,
            "avg_wait_hrs": round(s.avg_wait_time_hours, 2) if hasattr(s, 'avg_wait_time_hours') else 0.0,
            "utilization_pct": round(s.total_units_processed / max(s.capacity_per_hour * sim_days * 24, 1) * 100, 1) if sim_days else 0.0,
            "yield_base_rate": s.yield_base_rate,
        }

    # WIP alerts
    raw_alerts = tracker.check_wip_alert(loop)
    wip_alerts = []
    if isinstance(raw_alerts, list):
        for a in raw_alerts:
            if isinstance(a, dict):
                wip_alerts.append({"station": a.get("station", ""), "wip": a.get("wip", 0), "limit": a.get("limit", 0)})
            elif isinstance(a, str):
                wip_alerts.append({"station": a, "wip": 0, "limit": 0})

    elapsed = round((time.time() - t0) * 1000, 1)

    return SimResponse(
        policy=policy,
        total_orders=total_orders,
        shipped=shipped,
        on_time=on_time,
        overdue=shipped - on_time,
        otd_rate_pct=round(on_time / total_orders * 100, 2) if total_orders else 0.0,
        avg_lead_days=avg_lead,
        avg_wip=round(loop.avg_wip, 1),
        avg_queue_wait_hrs=avg_wait,
        bottleneck_station=bottleneck_name,
        bottleneck_load_pct=round(bottleneck_load, 1),
        total_defects=loop.total_defects,
        avg_yield_rate=round(loop.avg_yield_rate, 4),
        station_throughput=throughput,
        wip_alerts=wip_alerts,
        station_metrics=station_metrics,
        run_time_ms=elapsed,
        seed=seed,
        sim_days=sim_days,
    )


# ═══════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════

@app.get("/health")
def health():
    cfg = load_config()
    policies = list(cfg.get("scheduling", {}).get("rule", "EDD").split(",") if False
                    else ["FIFO", "EDD", "SPT"])
    return {
        "status": "ok",
        "version": "1.0",
        "policies": policies,
        "sim_days_default": cfg.get("sim_days", 90),
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/sim/config")
def get_config():
    return load_config()


@app.get("/sim/stations")
def get_stations():
    cfg = load_config()
    stations = []
    for line in cfg.get("factory", {}).get("lines", []):
        for s in line.get("stations", []):
            stations.append({
                "id": s["id"],
                "name": s["name"],
                "capacity_units_per_hour": s.get("capacity", {}).get("units_per_hour"),
                "setup_base_min": s.get("setup", {}).get("base_min"),
                "yield_base_rate": s.get("yield", {}).get("base_rate"),
                "failure_rate": s.get("failure", {}).get("rate"),
            })
    return {"stations": stations}


@app.post("/sim/run")
def sim_run(req: SimRequest):
    """執行一次 OTD 模擬"""
    try:
        cfg = load_config()
        result = run_simulation(cfg, req.policy, req.sim_days, req.seed, req.variant_params)
        return result.model_dump()
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sim/compare")
def sim_compare(req: SimRequest):
    """比較 FIFO / EDD / SPT 三政策"""
    policies = ["FIFO", "EDD", "SPT"]
    results = []
    try:
        cfg = load_config()
        for p in policies:
            cfg_copy = json.loads(json.dumps(cfg))
            r = run_simulation(cfg_copy, p, req.sim_days, req.seed, req.variant_params)
            results.append(r.model_dump())
        # sort by shipped desc
        results.sort(key=lambda x: x["shipped"], reverse=True)
        best = results[0]["policy"] if results else ""
        return {"policies_compared": len(results), "best_policy": best, "results": results,
                "run_at": datetime.now().isoformat()}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ── Entry ──
if __name__ == "__main__":
    port = int(os.environ.get("SIM_PORT", 8080))
    print(f"🚀 OTD Simulation API starting on :{port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")