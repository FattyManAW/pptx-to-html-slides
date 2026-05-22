"""
otd_bridge.py — OTD Engine → Dashboard 端到端自動化
====================================================
Sprint 3 P4: 一個指令完成 pipeline → sync → validate → report

使用:
  python otd_bridge.py                      # Dry-run: 檢查全線狀態
  python otd_bridge.py --run                 # 完整執行 pipeline + sync
  python otd_bridge.py --run --days 180      # 客製天數
  python otd_bridge.py --standalone          # 產出獨立 Dashboard (inline data)
  python otd_bridge.py --validate            # 只驗證資料一致性

Flow:
  otd_data_pipeline.py  →  timeline.json (flat)
                         →  policy_comparison.json
  sync_dashboard.py      →  timeline_wrapped.json
                         →  dashboard_metrics.json
  otd-dashboard.html     ←  fetch timeline_wrapped.json
"""

from __future__ import annotations
import json
import os
import subprocess
import sys
import time
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OTD_SIM_DIR = os.path.join(SCRIPT_DIR, "otd-sim")

# Expected artifacts
ARTIFACTS = {
    "timeline_flat": os.path.join(OTD_SIM_DIR, "timeline.json"),
    "timeline_wrapped": os.path.join(OTD_SIM_DIR, "timeline_wrapped.json"),
    "policy_comparison": os.path.join(OTD_SIM_DIR, "policy_comparison.json"),
    "dashboard_metrics": os.path.join(OTD_SIM_DIR, "dashboard_metrics.json"),
    "dashboard_html": os.path.join(SCRIPT_DIR, "otd-dashboard.html"),
    "storyboard_html": os.path.join(SCRIPT_DIR, "otd-storyboard.html"),
    "due_date_html": os.path.join(SCRIPT_DIR, "otd-due-date-comparison.html"),
}


def load_json(path: str):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def file_info(path: str) -> dict:
    """Get file metadata."""
    if not os.path.exists(path):
        return {"exists": False}
    stat = os.stat(path)
    return {
        "exists": True,
        "size_kb": round(stat.st_size / 1024, 1),
        "mtime": datetime.fromtimestamp(stat.st_mtime).isoformat(),
    }


def status() -> dict:
    """Full status check across all artifacts."""
    report: dict[str, dict] = {}

    # Timeline (flat)
    tl = load_json(ARTIFACTS["timeline_flat"])
    report["timeline_flat"] = {
        **file_info(ARTIFACTS["timeline_flat"]),
    }
    if tl:
        count = len(tl) if isinstance(tl, list) else len(tl.get("timeline", []))
        fmt = "flat-array" if isinstance(tl, list) else "wrapped"
        report["timeline_flat"]["frames"] = count
        report["timeline_flat"]["format"] = fmt

    # Timeline (wrapped)
    tlw = load_json(ARTIFACTS["timeline_wrapped"])
    report["timeline_wrapped"] = file_info(ARTIFACTS["timeline_wrapped"])
    if tlw:
        tw = tlw.get("timeline", [])
        report["timeline_wrapped"]["frames"] = len(tw)

    # Policy comparison
    pc = load_json(ARTIFACTS["policy_comparison"])
    report["policy_comparison"] = file_info(ARTIFACTS["policy_comparison"])
    if pc and pc.get("results"):
        report["policy_comparison"]["policies"] = []
        for r in pc["results"]:
            report["policy_comparison"]["policies"].append({
                "policy": r["policy"],
                "otd": r.get("on_time_rate", 0),
                "shipped": r.get("shipped", 0),
                "lead_days": r.get("avg_lead_days", 0),
            })

    # Dashboard metrics
    dm = load_json(ARTIFACTS["dashboard_metrics"])
    report["dashboard_metrics"] = file_info(ARTIFACTS["dashboard_metrics"])
    if dm:
        bp = dm.get("best_policy", {})
        report["dashboard_metrics"]["best_policy"] = bp.get("name")
        report["dashboard_metrics"]["otd"] = bp.get("otd")
        report["dashboard_metrics"]["bottleneck"] = dm.get("bottleneck", {}).get("name")

    # Dashboard HTML
    report["dashboard_html"] = file_info(ARTIFACTS["dashboard_html"])
    if report["dashboard_html"].get("exists"):
        with open(ARTIFACTS["dashboard_html"], "r", encoding="utf-8") as f:
            content = f.read()
        report["dashboard_html"]["has_fetch"] = 'fetch("otd-sim/timeline_wrapped.json")' in content

    # Storyboard
    report["storyboard_html"] = file_info(ARTIFACTS["storyboard_html"])

    # Due date comparison
    report["due_date_html"] = file_info(ARTIFACTS["due_date_html"])

    return report


def validate() -> tuple[bool, list[str]]:
    """Validate data consistency across artifacts."""
    issues = []
    s = status()

    # 1. Flat timeline must exist
    if not s["timeline_flat"].get("exists"):
        issues.append("❌ timeline.json missing — run pipeline first")

    # 2. Flat must be flat format
    if s["timeline_flat"].get("format") == "wrapped":
        issues.append("⚠️  timeline.json is wrapped — pipeline may have changed format")

    # 3. Wrapped must exist
    if not s["timeline_wrapped"].get("exists"):
        issues.append("❌ timeline_wrapped.json missing — run sync")

    # 4. Frame counts must match
    flat_frames = s["timeline_flat"].get("frames", 0)
    wrap_frames = s["timeline_wrapped"].get("frames", 0)
    if flat_frames > 0 and wrap_frames > 0 and flat_frames != wrap_frames:
        issues.append(f"❌ Frame mismatch: flat={flat_frames} wrapped={wrap_frames}")

    # 5. Policy comparison must exist
    if not s["policy_comparison"].get("exists"):
        issues.append("❌ policy_comparison.json missing — run pipeline first")

    # 6. Dashboard HTML must reference wrapped
    if s["dashboard_html"].get("exists") and not s["dashboard_html"].get("has_fetch"):
        issues.append("⚠️  Dashboard missing fetch() reference to timeline_wrapped.json")

    # 7. OTD realism check
    if s["policy_comparison"].get("policies"):
        all_100 = all(p["otd"] >= 0.99 for p in s["policy_comparison"]["policies"])
        if all_100:
            issues.append("⚠️  All policies 100% OTD — engine capacity model may not be engaged")

    # 8. Lead time check
    if s["policy_comparison"].get("policies"):
        all_zero = all(p["lead_days"] == 0 for p in s["policy_comparison"]["policies"])
        if all_zero:
            issues.append("⚠️  All lead times 0 days — processing time not applied")

    return len(issues) == 0, issues


def run_full(sim_days: int = 90) -> dict:
    """Run pipeline → sync → validate in one shot."""
    results = {"started": datetime.now().isoformat(), "steps": []}

    # Step 1: Pipeline
    print("═" * 60)
    print("Step 1/3: Running OTD data pipeline...")
    print("═" * 60)
    t0 = time.time()
    pipeline_path = os.path.join(SCRIPT_DIR, "otd_data_pipeline.py")
    proc = subprocess.run(
        [sys.executable, pipeline_path, "--sim-days", str(sim_days)],
        cwd=SCRIPT_DIR,
        capture_output=True,
        text=True,
        timeout=300,
    )
    elapsed = round(time.time() - t0, 1)
    results["steps"].append({
        "step": "pipeline",
        "elapsed_s": elapsed,
        "exit_code": proc.returncode,
        "output": proc.stdout[-500:],
    })
    print(proc.stdout[-500:])
    if proc.returncode != 0:
        print(f"❌ Pipeline failed:\n{proc.stderr}")
        results["error"] = "pipeline_failed"
        results["stderr"] = proc.stderr[-1000:]
        return results
    print(f"✅ Pipeline complete ({elapsed}s)")

    # Step 2: Sync
    print()
    print("═" * 60)
    print("Step 2/3: Syncing to Dashboard format...")
    print("═" * 60)
    t0 = time.time()
    sync_path = os.path.join(SCRIPT_DIR, "sync_dashboard.py")
    proc = subprocess.run(
        [sys.executable, sync_path, "--sync"],
        cwd=SCRIPT_DIR,
        capture_output=True,
        text=True,
        timeout=60,
    )
    elapsed = round(time.time() - t0, 1)
    results["steps"].append({
        "step": "sync",
        "elapsed_s": elapsed,
        "exit_code": proc.returncode,
        "output": proc.stdout.strip(),
    })
    print(proc.stdout)
    if proc.returncode != 0:
        print(f"❌ Sync failed:\n{proc.stderr}")
        results["error"] = "sync_failed"
        return results
    print(f"✅ Sync complete ({elapsed}s)")

    # Step 3: Validate
    print()
    print("═" * 60)
    print("Step 3/3: Validating data consistency...")
    print("═" * 60)
    ok, issues = validate()
    results["steps"].append({
        "step": "validate",
        "passed": ok,
        "issues": issues,
    })

    if issues:
        for issue in issues:
            print(f"  {issue}")
        if not ok:
            results["warning"] = "validation_warnings"

    if ok:
        print("  ✅ All checks passed")

    # Final summary
    s = status()
    results["final_status"] = s
    results["completed"] = datetime.now().isoformat()
    results["total_elapsed_s"] = round(
        sum(step.get("elapsed_s", 0) for step in results["steps"]), 1
    )

    print()
    print("═" * 60)
    print("🏁 Bridge Complete")
    print("═" * 60)
    print(f"  📊 {s['timeline_wrapped'].get('frames', '?')} timeline frames")
    if s["policy_comparison"].get("policies"):
        for p in s["policy_comparison"]["policies"]:
            print(f"  📋 {p['policy']}: OTD={p['otd']:.1%} · {p['shipped']} shipped · {p['lead_days']}d lead")
    print(f"  🏆 Best: {s['dashboard_metrics'].get('best_policy', '?')}")
    print(f"  ⏱️  {results['total_elapsed_s']}s total")
    print()
    print(f"  View: open showcase/otd-dashboard.html")

    return results


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="OTD Bridge — Engine → Dashboard 端到端自動化",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python otd_bridge.py                    # Status check
  python otd_bridge.py --run              # Full pipeline → sync
  python otd_bridge.py --run --days 180   # 180-day simulation
  python otd_bridge.py --validate         # Consistency check only
        """,
    )
    parser.add_argument("--run", action="store_true", help="Run full pipeline → sync")
    parser.add_argument("--days", type=int, default=90, help="Simulation days (default: 90)")
    parser.add_argument("--validate", action="store_true", help="Validate consistency only")
    parser.add_argument("--json", action="store_true", help="Output status as JSON")

    args = parser.parse_args()

    if args.run:
        result = run_full(sim_days=args.days)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    elif args.validate:
        ok, issues = validate()
        for issue in issues:
            print(f"  {issue}")
        if ok:
            print("  ✅ All checks passed — data is consistent")
        else:
            print(f"\n  {len(issues)} issue(s) found")
            sys.exit(1)
    else:
        # Status mode
        s = status()
        if args.json:
            print(json.dumps(s, indent=2, ensure_ascii=False, default=str))
        else:
            _print_status(s)


def _print_status(s: dict):
    """Pretty-print status report."""
    print("🔍 OTD Bridge — Full Status Report")
    print("═" * 60)

    sections = [
        ("1. Engine Output (timeline.json)", "timeline_flat", ["frames", "format", "size_kb"]),
        ("2. Dashboard Data (timeline_wrapped.json)", "timeline_wrapped", ["frames", "size_kb"]),
        ("3. Policy Comparison", "policy_comparison", ["policies"]),
        ("4. Dashboard Metrics", "dashboard_metrics", ["best_policy", "otd", "bottleneck"]),
        ("5. Dashboard HTML", "dashboard_html", ["has_fetch", "size_kb"]),
        ("6. Storyboard HTML", "storyboard_html", ["size_kb"]),
        ("7. Due Date Comparison", "due_date_html", ["size_kb"]),
    ]

    for title, key, fields in sections:
        d = s.get(key, {})
        exists = d.get("exists", False)
        icon = "✅" if exists else "❌"
        print(f"\n{icon} {title}")
        if not exists:
            print("   MISSING — run pipeline first")
            continue
        print(f"   size={d.get('size_kb', '?')}KB · mtime={d.get('mtime', '?')[:19]}")
        for f in fields:
            val = d.get(f)
            if val is not None:
                if isinstance(val, list):
                    for item in val[:5]:
                        if isinstance(item, dict):
                            print(f"   {item.get('policy','?')}: OTD={item.get('otd',0):.1%} · {item.get('shipped',0)} shipped")
                elif isinstance(val, (int, float)):
                    if f == "otd":
                        print(f"   {f}={val:.1%}")
                    else:
                        print(f"   {f}={val}")
                else:
                    print(f"   {f}={val}")

    # Summary
    print("\n" + "═" * 60)
    pc = s.get("policy_comparison", {})
    dm = s.get("dashboard_metrics", {})
    frames = s.get("timeline_wrapped", {}).get("frames", 0)
    print(f"📊 {frames} frames · {dm.get('best_policy','?')} best · bottleneck={dm.get('bottleneck','?')}")

    # Health indicator
    healthy = all(
        s.get(k, {}).get("exists", False)
        for k in ["timeline_flat", "timeline_wrapped", "policy_comparison", "dashboard_html"]
    )
    if healthy:
        print("🏥 Bridge health: HEALTHY — all artifacts present")
        print("💡 Run: python otd_bridge.py --run  to refresh data")
    else:
        print("🏥 Bridge health: DEGRADED — missing artifacts")
        print("💡 Run: python otd_bridge.py --run  to rebuild")


if __name__ == "__main__":
    main()