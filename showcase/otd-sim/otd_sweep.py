"""
OTD v1.1 — Parameter Sweep Runner (P23)
對 OTD Engine 做參數空間掃描：故障率 × 換線時間 × 良率衰減 × 三 policy

產出：sweep_results.json → otd-sensitivity.html 熱力圖

用法：
    cd showcase/otd-sim
    python otd_sweep.py              # 完整 sweep（~2 min）
    python otd_sweep.py --quick      # 快速 sweep（5 場景 × 3 policy）
"""

from __future__ import annotations
import json
import copy
import sys
import time
from datetime import datetime
from pathlib import Path

# Add parent dir for imports
sys.path.insert(0, str(Path(__file__).parent))

from station_dispatch import SimulationEngineV02

# ═══════════════════════════════════════════════════════════════
# Parameter grid definition
# ═══════════════════════════════════════════════════════════════

PARAM_PROFILES = [
    {"name": "Baseline",      "failure": 1.0, "setup": 15, "yield": 1.0},
    {"name": "High Failure",  "failure": 3.0, "setup": 15, "yield": 1.0},
    {"name": "High Setup",    "failure": 1.0, "setup": 50, "yield": 1.0},
    {"name": "Low Yield",     "failure": 1.0, "setup": 15, "yield": 0.8},
    {"name": "Extreme",       "failure": 3.0, "setup": 50, "yield": 0.8},
]

POLICIES = ["FIFO", "SPT", "EDD"]

# Quick mode: only baseline + extreme
QUICK_PROFILES = [
    {"name": "Baseline",      "failure": 1.0, "setup": 15, "yield": 1.0},
    {"name": "Extreme",       "failure": 3.0, "setup": 50, "yield": 0.8},
]

# ═══════════════════════════════════════════════════════════════
# Sweep runner
# ═══════════════════════════════════════════════════════════════

def load_config() -> dict:
    with open(Path(__file__).parent / "factory.json") as f:
        return json.load(f)

def patch_config(base: dict, profile: dict) -> dict:
    """Deep-copy config and apply parameter profile."""
    config = copy.deepcopy(base)
    config["sim_days"] = 30  # reduced for sweep speed
    config["warmup_days"] = 3
    params = config["parameters"]
    params["failure"]["rate_multiplier"] = profile["failure"]
    params["setup"]["jitter_pct"] = profile["setup"]
    params["yield"]["decay_multiplier"] = profile["yield"]
    return config

def run_sweep(quick: bool = False) -> list[dict]:
    base = load_config()
    profiles = QUICK_PROFILES if quick else PARAM_PROFILES
    results = []

    total = len(profiles) * len(POLICIES)
    i = 0
    t0 = time.time()

    for prof in profiles:
        for policy in POLICIES:
            i += 1
            config = patch_config(base, prof)
            try:
                engine = SimulationEngineV02(config, seed=42)
                result = engine.run(dispatch_policy=policy)

                results.append({
                    "profile": prof["name"],
                    "failure_rate": prof["failure"],
                    "setup_jitter": prof["setup"],
                    "yield_decay": prof["yield"],
                    "policy": policy,
                    "otd_rate": round(result.otd_rate, 4),
                    "otd_count": result.otd_count,
                    "total_orders": result.total_orders,
                    "avg_lead_time_days": result.avg_lead_time_days,
                    "avg_wip": result.avg_wip,
                    "bottleneck_station": result.bottleneck_station,
                    "warehouse_shipments": result.warehouse_shipments,
                    "total_defects": result.total_defects,
                })
                elapsed = time.time() - t0
                eta = (elapsed / i) * (total - i) if i > 0 else 0
                print(f"[{i}/{total}] {prof['name']:15s} × {policy:4s}  "
                      f"OTD={result.otd_rate:.2%}  lead={result.avg_lead_time_days:.1f}d  "
                      f"bn={result.bottleneck_station}  ({elapsed:.0f}s elapsed, ETA {eta:.0f}s)")
            except Exception as e:
                results.append({
                    "profile": prof["name"],
                    "failure_rate": prof["failure"],
                    "setup_jitter": prof["setup"],
                    "yield_decay": prof["yield"],
                    "policy": policy,
                    "error": str(e),
                })
                print(f"[{i}/{total}] {prof['name']} × {policy}  ERROR: {e}")

    return results


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

def main():
    quick = "--quick" in sys.argv
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    results = run_sweep(quick=quick)

    out_path = Path(__file__).parent / "sweep_results.json"
    payload = {
        "generated_at": ts,
        "mode": "quick" if quick else "full",
        "policies": POLICIES,
        "sim_days": 30,
        "total_scenarios": len(results),
        "results": results,
    }
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Sweep complete: {len(results)} scenarios → {out_path}")

    # Summary table
    print("\n── Policy Comparison (Best per metric) ──")
    for policy in POLICIES:
        policy_results = [r for r in results if r.get("policy") == policy]
        if not policy_results:
            continue
        avg_otd = sum(r.get("otd_rate", 0) for r in policy_results) / len(policy_results)
        avg_lead = sum(r.get("avg_lead_time_days", 0) for r in policy_results) / len(policy_results)
        avg_wip = sum(r.get("avg_wip", 0) for r in policy_results) / len(policy_results)
        print(f"  {policy:5s}: OTD={avg_otd:.1%}  lead={avg_lead:.1f}d  WIP={avg_wip:.1f}")

    best = max((r for r in results if "otd_rate" in r), key=lambda r: r["otd_rate"])
    print(f"\n🏆 Best OTD: {best['profile']} × {best['policy']} = {best['otd_rate']:.1%} (lead {best.get('avg_lead_time_days',0)}d)")

if __name__ == "__main__":
    main()