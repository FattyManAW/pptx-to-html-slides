"""
sync_dashboard.py — OTD Dashboard API 自動同步
==============================================
Sprint 3 T2: 讓 timeline.json + policy_comparison.json 自動注入 Dashboard HTML

功能:
  1. 轉換 timeline.json (flat array → wrapped {timeline: [...]} format)
  2. 將 policy comparison 寫入 json，Dashboard 可直接 fetch
  3. 可選：直接更新 Dashboard HTML 內部 inline data（standalone mode）
  4. 可選：觸發 otd_data_pipeline.py 重跑

使用:
  python sync_dashboard.py                          # Dry-run: 檢查現有檔案轉換
  python sync_dashboard.py --sync                   # 將 timeline.json 接上 Dashboard 格式
  python sync_dashboard.py --reload                 # 重跑 pipeline + sync
  python sync_dashboard.py --standalone             # 產出含 inline data 的獨立 Dashboard
"""

from __future__ import annotations
import json
import os
import re
import shutil
import sys
from datetime import datetime

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OTD_SIM_DIR = os.path.join(SCRIPT_DIR, "otd-sim")
TIMELINE_PATH = os.path.join(OTD_SIM_DIR, "timeline.json")
COMPARISON_PATH = os.path.join(OTD_SIM_DIR, "policy_comparison.json")
DASHBOARD_PATH = os.path.join(SCRIPT_DIR, "otd-dashboard.html")
SYNCED_TIMELINE_PATH = os.path.join(OTD_SIM_DIR, "timeline_wrapped.json")
METRICS_PATH = os.path.join(OTD_SIM_DIR, "dashboard_metrics.json")


def load_json(path: str) -> dict | list | None:
    """Load JSON file, return None if missing."""
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data, pretty: bool = True):
    """Save JSON with consistent formatting."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        if pretty:
            json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            json.dump(data, f, ensure_ascii=False)


def convert_timeline(flat: list) -> dict:
    """Convert flat array [{ts,day,hour,stations}] → {timeline: [...]}."""
    return {"timeline": flat}


def extract_metrics(timeline: list, comparison: dict | None) -> dict:
    """Extract summary metrics for dashboard display."""
    if not timeline:
        return {}

    # From timeline
    frame_count = len(timeline)

    # Find max WIP per station
    station_wips = {}
    bottleneck = {"id": "", "name": "", "score": 0.0}
    yield_rates = {}

    for frame in timeline:
        for st in frame.get("stations", []):
            sid = st["id"]
            station_wips[sid] = max(station_wips.get(sid, 0), st["wip"])
            yield_rates[sid] = st.get("yield_rate", 1.0)
            if st.get("bottleneck_score", 0) > bottleneck["score"]:
                bottleneck = {
                    "id": sid,
                    "name": st.get("name", sid),
                    "score": st.get("bottleneck_score", 0),
                }

    # From comparison
    policy_results = []
    best_policy = None
    if comparison and "results" in comparison:
        policy_results = comparison["results"]
        # Find best by on_time_rate
        best = max(comparison["results"],
                   key=lambda x: x.get("on_time_rate", 0),
                   default=None)
        if best:
            best_policy = {
                "name": best["policy"],
                "otd": best.get("on_time_rate", 0),
                "shipped": best.get("shipped", 0),
                "lead_days": best.get("avg_lead_days", 0),
            }

    return {
        "generated_at": datetime.now().isoformat(),
        "frame_count": frame_count,
        "total_stations": len(station_wips),
        "station_wip_max": station_wips,
        "bottleneck": bottleneck,
        "yield_rates": yield_rates,
        "best_policy": best_policy,
        "policy_results": policy_results,
    }


def sync(sync_json: bool = True, sync_metrics: bool = True):
    """Sync timeline.json → timeline_wrapped.json + dashboard_metrics.json."""
    timeline = load_json(TIMELINE_PATH)
    comparison = load_json(COMPARISON_PATH)

    results = {}

    # Step 1: Convert flat timeline → wrapped
    if timeline and isinstance(timeline, list):
        metrics = extract_metrics(timeline, comparison)

        if sync_json:
            wrapped = convert_timeline(timeline)
            save_json(SYNCED_TIMELINE_PATH, wrapped)
            results["timeline_wrapped"] = {
                "path": SYNCED_TIMELINE_PATH,
                "frames": len(timeline),
            }
            print(f"✅ timeline_wrapped.json: {len(timeline)} frames → {SYNCED_TIMELINE_PATH}")

        if sync_metrics:
            save_json(METRICS_PATH, metrics)
            results["dashboard_metrics"] = {
                "path": METRICS_PATH,
                "best_policy": metrics.get("best_policy", {}).get("name"),
                "bottleneck": metrics.get("bottleneck", {}).get("name"),
            }
            print(f"✅ dashboard_metrics.json → {METRICS_PATH}")
            if metrics.get("best_policy"):
                bp = metrics["best_policy"]
                print(f"   🏆 Best: {bp['name']} (OTD={bp['otd']:.1%}, {bp['shipped']} shipped, {bp['lead_days']}d lead)")

        return results

    elif timeline and isinstance(timeline, dict):
        print("ℹ️  timeline.json is already wrapped format")
        if sync_json:
            save_json(SYNCED_TIMELINE_PATH, timeline)
            results["timeline_wrapped"] = {"path": SYNCED_TIMELINE_PATH, "existing": True}
        return results

    else:
        print("❌ timeline.json not found or empty")
        print(f"   Expected at: {TIMELINE_PATH}")
        return None


def produce_standalone(output_path: str | None = None):
    """Create standalone Dashboard HTML with inline JSON data.

    This modifies the Dashboard to embed timeline + metrics directly,
    so it works without fetch() (e.g., local file:// or offline).
    """
    if not os.path.exists(DASHBOARD_PATH):
        print(f"❌ Dashboard not found: {DASHBOARD_PATH}")
        return

    timeline = load_json(TIMELINE_PATH)
    if not timeline:
        print("❌ timeline.json not found — run pipeline first")
        return

    # Ensure wrapped format
    if isinstance(timeline, list):
        timeline = convert_timeline(timeline)

    comparison = load_json(COMPARISON_PATH)
    metrics = extract_metrics(
        timeline.get("timeline", timeline) if isinstance(timeline, dict) else [],
        comparison,
    )

    html = open(DASHBOARD_PATH, "r", encoding="utf-8").read()

    # Replace fetch() call with inline data
    # Pattern: const r = await fetch("otd-sim/timeline.json");
    #            data = await r.json();
    inline_block = (
        "// INLINE DATA — auto-generated by sync_dashboard.py\n"
        f"// Generated: {datetime.now().isoformat()}\n"
        f"data = {json.dumps(timeline, ensure_ascii=False)};\n"
        f"const METRICS = {json.dumps(metrics, ensure_ascii=False)};\n"
        "// END INLINE DATA\n"
    )

    # Replace the fetch + json lines
    pattern = r"const r = await fetch\(\"otd-sim/timeline\.json\"\);\s*\n\s*data = await r\.json\(\);"
    if re.search(pattern, html):
        html = re.sub(pattern, inline_block, html)
        print("✅ Replaced fetch() with inline data")
    else:
        print("⚠️  Could not find fetch() pattern — data may still be fetched dynamically")

    # Add metrics overlay display after init()
    metrics_js = """
    // Metrics overlay (auto-injected)
    if (typeof METRICS !== 'undefined' && METRICS.best_policy) {
        const bp = METRICS.best_policy;
        const bar = document.querySelector('.meta-bar');
        if (bar) {
            const el = document.createElement('span');
            el.className = 'meta';
            el.innerHTML = `<b>🏆 ${bp.name}</b> OTD ${(bp.otd*100).toFixed(1)}% · ${bp.shipped} shipped · ${bp.lead_days}d`;
            el.style.color = 'var(--accent)';
            bar.appendChild(el);
        }
    }
    """
    # Insert after init() call
    html = html.replace("init();", "init();" + metrics_js)

    output_path = output_path or os.path.join(SCRIPT_DIR, "otd-dashboard-standalone.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Standalone Dashboard: {output_path}")
    print(f"   {len(html):,} bytes")


def reload_pipeline():
    """Run otd_data_pipeline.py then sync."""
    pipeline = os.path.join(SCRIPT_DIR, "otd_data_pipeline.py")
    if not os.path.exists(pipeline):
        print(f"❌ Pipeline not found: {pipeline}")
        return

    import subprocess
    print("🔧 Running otd_data_pipeline.py...")
    result = subprocess.run(
        [sys.executable, pipeline, "--sim-days", "90"],
        cwd=SCRIPT_DIR,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"❌ Pipeline failed:\n{result.stderr}")
        return

    print("📊 Syncing...")
    sync()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="OTD Dashboard Sync — timeline.json → Dashboard auto-inject",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python sync_dashboard.py                    # Dry-run: status check
  python sync_dashboard.py --sync             # Convert & sync
  python sync_dashboard.py --reload           # Reload pipeline + sync
  python sync_dashboard.py --standalone       # Produce standalone Dashboard
        """,
    )

    parser.add_argument("--sync", action="store_true", help="Sync timeline.json → Dashboard format")
    parser.add_argument("--reload", action="store_true", help="Re-run pipeline then sync")
    parser.add_argument("--standalone", action="store_true",
                        help="Produce standalone Dashboard with inline data")
    parser.add_argument("--output", default=None, help="Output path for standalone Dashboard")

    args = parser.parse_args()

    if args.reload:
        reload_pipeline()
    elif args.standalone:
        produce_standalone(args.output)
    elif args.sync:
        sync()
    else:
        # Dry-run mode
        print("🔍 OTD Dashboard Sync — Status Check")
        print("=" * 55)

        timeline = load_json(TIMELINE_PATH)
        if timeline:
            count = len(timeline) if isinstance(timeline, list) else len(timeline.get("timeline", []))
            fmt = "flat-array" if isinstance(timeline, list) else "wrapped ({timeline: [...]})"
            print(f"  timeline.json    ✅ {count} frames ({fmt})")
        else:
            print("  timeline.json    ❌ MISSING")

        comparison = load_json(COMPARISON_PATH)
        if comparison:
            results = comparison.get("results", [])
            print(f"  policy_comparison ✅ {len(results)} policies")
            for r in results:
                print(f"                    {r['policy']}: OTD={r.get('on_time_rate',0):.1%} "
                      f"shipped={r['shipped']} lead={r.get('avg_lead_days',0)}d")
        else:
            print("  policy_comparison ❌ MISSING")

        dash = os.path.exists(DASHBOARD_PATH)
        print(f"  otd-dashboard.html {'✅' if dash else '❌'}")

        # Check format mismatch
        if timeline and isinstance(timeline, list):
            print()
            print("⚠️  Format mismatch detected:")
            print("   timeline.json = flat array [{...}, {...}]")
            print("   Dashboard expects = {timeline: [...]}")
            print()
            print("   Run: python sync_dashboard.py --sync")
        else:
            print()
            print("   ✅ Format compatible (no --sync needed)")
            print("   Run: python sync_dashboard.py --relaod  to refresh data")
            print("   Run: python sync_dashboard.py --standalone  for offline Dashboard")


if __name__ == "__main__":
    main()