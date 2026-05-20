#!/usr/bin/env python3
"""
run_qa.py — QA Pipeline Cron Automation
=========================================
定時掃描三套投影片（潤思/APS/CRIS），偵測分數下降時自動告警推 board chat。

設計原則：
- 分數不變 → 安靜（無告警）
- 分數下降 → 推 board chat + 記錄
- 支援獨立 CLI 模式與 OpenClaw cron job 模式

用法:
  # 一次性掃描（CLI）
  python3 run_qa.py --once

  # 定時模式（for cron）
  python3 run_qa.py --watch  # 每 4h 掃一次

  # 手動重置 baseline
  python3 run_qa.py --reset-baseline

依賴: qa_pipeline.py（同目錄）

"""

import sys
import os
import json
import time
import subprocess
import datetime
import argparse
from collections import defaultdict

# ═══════════════════════════════════════
# 常數
# ═══════════════════════════════════════

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SHOWCASE_DIR = os.path.join(SCRIPT_DIR, "showcase")
BASELINE_FILE = os.path.join(SCRIPT_DIR, ".qa_baseline.json")
HISTORY_FILE = os.path.join(SCRIPT_DIR, ".qa_history.jsonl")
TRENDS_FILE = os.path.join(SHOWCASE_DIR, "trends.html")
ESCALATE_THRESHOLD = 2  # 連續 N 次下降觸發 escalate

# Board API
BOARD_ID = "3881607b-63ff-41ca-ab94-e45cace657c6"
BASE_URL = "http://100.107.36.80:8000"
AUTH_TOKEN = "ubiMy0-FgO3TA5CkRvRvSvVXpeAGi7vO9xwuyfeB7cs"

# 監控目標
WATCH_TARGETS = {
    "润思IMPACTS": os.path.join(SHOWCASE_DIR, "runs-impacts-aps-partner.html"),
    "APS AI Agent": os.path.join(SHOWCASE_DIR, "aps-ai-agent.html"),
    "CRIS IMPACTs": os.path.join(SHOWCASE_DIR, "cris-impacts-carbon.html"),
}

# 掃描間隔（秒）
SCAN_INTERVAL = 4 * 3600  # 4h

# ═══════════════════════════════════════
# Core: 運行 qa_pipeline 並提取分數
# ═══════════════════════════════════════

def run_qa_pipeline(filepath: str) -> dict:
    """匯入 qa_pipeline 的 analyze_html 並回傳結果。"""
    sys.path.insert(0, SCRIPT_DIR)
    try:
        from qa_pipeline import analyze_html
        result = analyze_html(filepath)
        return result
    except ImportError as e:
        print(f"❌ 無法匯入 qa_pipeline: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"❌ QA 分析失敗 {filepath}: {e}", file=sys.stderr)
        return None


def extract_scores(result: dict) -> dict:
    """從 analyze_html 結果提取摘要分數。"""
    summary = result.get("summary", {})
    p0 = summary.get("p0", {})
    quality = summary.get("quality", {})
    overall = summary.get("overall", {})

    return {
        "slide_count": result.get("slide_count", 0),
        "filesize_kb": result.get("filesize_kb", 0),
        "p0_score": p0.get("score", "?/6"),
        "quality_score": quality.get("score", "?/5"),
        "pass_count": overall.get("pass", 0),
        "fail_count": overall.get("fail", 0),
        "warn_count": overall.get("warn", 0),
        "total_checks": overall.get("total", 0),
        "pct": round((overall.get("pass", 0) / overall.get("total", 1)) * 100),
    }


def scan_all(product_filter: str = None) -> dict:
    """掃描全部目標（或依 --product 過濾），回傳 {name: scores}。"""
    targets = WATCH_TARGETS
    if product_filter:
        # --product aps|cris|runs 過濾
        filter_map = {
            "aps": ["APS AI Agent"],
            "cris": ["CRIS IMPACTs"],
            "runs": ["润思IMPACTS"],
        }
        keys = []
        for token in product_filter.split(","):
            token = token.strip().lower()
            if token in filter_map:
                keys.extend(filter_map[token])
        if keys:
            targets = {k: v for k, v in WATCH_TARGETS.items() if k in keys}
    
    results = {}
    for name, path in targets.items():
        if not os.path.isfile(path):
            print(f"⚠ {name}: 檔案不存在 {path}", file=sys.stderr)
            results[name] = {"error": "file_not_found"}
            continue

        print(f"🔍 掃描 {name}...")
        result = run_qa_pipeline(path)
        if result is None:
            results[name] = {"error": "analysis_failed"}
            continue

        scores = extract_scores(result)
        results[name] = scores

        status = "✅" if scores["fail_count"] == 0 else "❌"
        print(f"  {status} {name}: {scores['pass_count']}P/{scores['fail_count']}F/{scores['warn_count']}W "
              f"({scores['p0_score']} P0, {scores['quality_score']} quality)")

    return results


# ═══════════════════════════════════════
# Baseline（歷史基準分數）
# ═══════════════════════════════════════

def load_baseline() -> dict:
    """載入儲存的 baseline。"""
    if os.path.isfile(BASELINE_FILE):
        with open(BASELINE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_baseline(baseline: dict):
    """儲存 baseline 至磁碟。"""
    with open(BASELINE_FILE, "w") as f:
        json.dump(baseline, f, ensure_ascii=False, indent=2)
    print(f"📋 Baseline 已儲存: {BASELINE_FILE}")


def compare_with_baseline(current: dict) -> list:
    """比較當前結果與 baseline，回傳分數下降項目。"""
    baseline = load_baseline()
    drops = []

    for name, scores in current.items():
        if "error" in scores:
            drops.append({
                "name": name,
                "type": "error",
                "detail": scores["error"],
                "message": f"❌ {name} 掃描失敗: {scores['error']}"
            })
            continue

        prev = baseline.get(name)
        if prev is None:
            # 首次掃描，設 baseline 不告警
            continue

        pct_diff = scores["pct"] - prev.get("pct", 100)
        fail_diff = scores["fail_count"] - prev.get("fail_count", 0)

        if fail_diff > 0 or pct_diff < 0:
            drops.append({
                "name": name,
                "type": "downgrade",
                "prev_pct": prev.get("pct", 100),
                "curr_pct": scores["pct"],
                "prev_pass": prev.get("pass_count", 0),
                "curr_pass": scores["pass_count"],
                "prev_fail": prev.get("fail_count", 0),
                "curr_fail": scores["fail_count"],
                "pct_diff": pct_diff,
                "fail_diff": fail_diff,
            })

    return drops


# ═══════════════════════════════════════
# Board Chat 告警
# ═══════════════════════════════════════

def post_to_board_chat(message: str):
    """推送告警到 board chat。"""
    try:
        result = subprocess.run([
            "curl", "-sS", "-X", "POST",
            f"{BASE_URL}/api/v1/agent/boards/{BOARD_ID}/memory",
            "-H", f"X-Agent-Token: {AUTH_TOKEN}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({"content": message, "tags": ["chat"]})
        ], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            resp = json.loads(result.stdout)
            print(f"📢 告警已推送 board chat (id={resp.get('id','?')})")
        else:
            print(f"⚠ 推送失敗: {result.stderr}")
    except Exception as e:
        print(f"⚠ 推送異常: {e}")


def format_alert_message(drops: list, timestamp: str) -> str:
    """格式化告警訊息。"""
    lines = [f"## ⚠ QA Pipeline 告警 — {timestamp}"]
    lines.append("")
    lines.append("以下項目分數下降：")
    lines.append("")

    for d in drops:
        if d["type"] == "error":
            lines.append(f"- {d['message']}")
        else:
            name = d["name"]
            lines.append(f"### {name}")
            lines.append(f"| 指標 | 上次 | 本次 | 變化 |")
            lines.append(f"|------|------|------|------|")
            lines.append(f"| 通過率 | {d['prev_pct']}% | **{d['curr_pct']}%** | 📉 {d['pct_diff']}% |")
            lines.append(f"| PASS | {d['prev_pass']} | {d['curr_pass']} | - |")
            lines.append(f"| FAIL | {d['prev_fail']} | **{d['curr_fail']}** | +{d['fail_diff']} |")
            lines.append("")

    lines.append("請檢查對應 HTML 檔案修復。")
    return "\n".join(lines)


# ═══════════════════════════════════════
# History Log（JSONL 追加記錄）
# ═══════════════════════════════════════

def append_history(current: dict, timestamp: str):
    """將本次掃描結果追加到 .qa_history.jsonl。"""
    entry = {
        "ts": timestamp,
        "scans": current
    }
    with open(HISTORY_FILE, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_history() -> list:
    """載入歷程記錄。"""
    if not os.path.isfile(HISTORY_FILE):
        return []
    entries = []
    with open(HISTORY_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries


# ═══════════════════════════════════════
# Escalate: 連續退步預警
# ═══════════════════════════════════════

def check_escalate(drops: list) -> list:
    """Per-product 檢查：任一產品連續 2 次下降才 escalate。
    回傳需 escalate 的產品名稱清單。"""
    history = load_history()
    if len(history) < ESCALATE_THRESHOLD:
        return []

    # 從 drops 中提取受影響的產品
    affected = {d["name"] for d in drops if d["type"] == "downgrade"}
    if not affected:
        return []

    escalate_list = []
    for product in affected:
        consecutive_drops = 0
        for entry in reversed(history[-ESCALATE_THRESHOLD:]):
            scans = entry.get("scans", {})
            ps = scans.get(product, {})
            if ps.get("fail_count", 0) > 0 or ps.get("pct", 100) < 85:
                consecutive_drops += 1
            else:
                break
        if consecutive_drops >= ESCALATE_THRESHOLD:
            escalate_list.append(product)
    
    return escalate_list


def format_escalate_message(products: list, timestamp: str) -> str:
    """格式化 escalate 告警訊息。"""
    history = load_history()
    lines = [
        f"## 🚨 QA Cron ESCALATE — 連續退步預警",
        "",
        f"已連續 {ESCALATE_THRESHOLD} 次掃描出現 FAIL。",
        f"觸發時間: {timestamp}",
        "",
        "**需要人工介入檢查。**",
        "",
        "最近掃描記錄：",
        ""
    ]
    for entry in history[-3:]:
        ts = entry.get("ts", "?")
        scans = entry.get("scans", {})
        lines.append(f"- **{ts}**")
        for name, scores in scans.items():
            f = scores.get("fail_count", "?")
            p = scores.get("pass_count", "?")
            emoji = "✅" if f == 0 else "❌"
            lines.append(f"  {emoji} {name}: {p}P/{f}F")
        lines.append("")
    return "\n".join(lines)


# ═══════════════════════════════════════
# Trends HTML 生成
# ═══════════════════════════════════════

def generate_trends_html():
    """從 .qa_history.jsonl 生成純 CSS 趨勢儀表板。"""
    history = load_history()
    if not history:
        print("⚠ 無歷史記錄，請先執行 --once 建立資料。")
        return

    # 提取時序數據
    labels = []
    datasets = {name: [] for name in WATCH_TARGETS}
    
    for entry in history:
        ts = entry.get("ts", "?")
        # 只顯示時間部分
        short_ts = ts.split(" ")[-1][:5] if " " in ts else ts[:5]
        labels.append(short_ts)
        
        scans = entry.get("scans", {})
        for name in WATCH_TARGETS:
            scores = scans.get(name, {})
            pct = scores.get("pct", 0)
            datasets[name].append(pct)

    # 計算 max for scale
    all_pcts = [v for vals in datasets.values() for v in vals]
    chart_max = max(all_pcts) if all_pcts else 100
    chart_max = max(chart_max, 100)  # 至少 100

    # 產品顏色
    colors = {
        "润思IMPACTS": "#14b8a6",
        "APS AI Agent": "#6366f1",
        "CRIS IMPACTs": "#f59e0b",
    }

    # 生成 bars
    bars_html = []
    for name in WATCH_TARGETS:
        vals = datasets.get(name, [])
        color = colors.get(name, "#64748b")
        bars_html.append(f'<div class="chart-row"><span class="chart-label">{name}</span><div class="chart-bar-group">')
        for v in vals:
            h = max(2, (v / chart_max) * 100)
            label = f"{v}%" if v > 0 else ""
            bars_html.append(
                f'<div class="bar" style="height:{h}%;background:{color}" title="{name}: {v}%">'
                f'<span class="bar-val">{label}</span></div>'
            )
        bars_html.append('</div></div>')

    bars_block = "\n        ".join(bars_html)
    x_labels = "\n          ".join(f"<span>{l}</span>" for l in labels)

    html = f'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>QA Pipeline — 歷史趨勢儀表板</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: 'Inter','Noto Sans SC',sans-serif; background:#0f172a; color:#e2e8f0; min-height:100vh; padding:2rem; }}
h1 {{ font-family: 'Playfair Display',serif; font-size:2rem; margin-bottom:.5rem; color:#f0f4f8; }}
.sub {{ color:#64748b; font-size:.85rem; margin-bottom:2rem; }}
.chart {{ display:flex; flex-direction:column; gap:1.5rem; max-width:900px; }}
.chart-row {{ display:flex; align-items:flex-end; gap:1rem; min-height:80px; }}
.chart-label {{ min-width:120px; font-size:.8rem; color:#94a3b8; text-align:right; }}
.chart-bar-group {{ display:flex; gap:4px; align-items:flex-end; flex:1; height:120px; border-bottom:1px solid rgba(255,255,255,.06); padding-bottom:2px; }}
.bar {{ flex:1; min-width:16px; border-radius:3px 3px 0 0; position:relative; transition:opacity .2s; opacity:.75; }}
.bar:hover {{ opacity:1; }}
.bar-val {{ position:absolute; top:-18px; left:50%; transform:translateX(-50%); font-size:.6rem; color:#94a3b8; white-space:nowrap; }}
.x-labels {{ display:flex; gap:4px; margin-top:4px; padding-left:136px; }}
.x-labels span {{ flex:1; min-width:16px; font-size:.55rem; color:#475569; text-align:center; }}
.stats {{ display:grid; grid-template-columns:repeat(3,1fr); gap:1rem; margin:2rem 0; max-width:900px; }}
.stat-card {{ background:rgba(255,255,255,.04); border:1px solid rgba(255,255,255,.06); border-radius:10px; padding:1rem; }}
.stat-card h3 {{ font-size:.7rem; color:#64748b; text-transform:uppercase; letter-spacing:.08em; margin-bottom:.3rem; }}
.stat-card .val {{ font-size:1.6rem; font-weight:700; }}
.stats .润思IMPACTS .val {{ color:#14b8a6; }}
.stats .APS .val {{ color:#6366f1; }}
.stats .CRIS .val {{ color:#f59e0b; }}
.footer {{ margin-top:2rem; font-size:.7rem; color:#475569; }}
</style>
</head>
<body>
<h1>📊 QA Pipeline 歷史趨勢</h1>
<p class="sub">Power Squad — 三套投影片 QA 分數走勢 · {len(history)} 次掃描記錄</p>

<div class="stats">
'''
    
    # 最新分數卡片
    latest = history[-1]["scans"] if history else {}
    short_names = {"润思IMPACTS": "润思IMPACTS", "APS AI Agent": "APS", "CRIS IMPACTs": "CRIS"}
    for name in WATCH_TARGETS:
        s = latest.get(name, {})
        pct = s.get("pct", "?")
        pf = f"{s.get('pass_count','?')}P/{s.get('fail_count','?')}F"
        cls = short_names.get(name, name).replace(" ", "")
        html += f'<div class="stat-card {cls}"><h3>{name}</h3><div class="val">{pct}%</div><div style="font-size:.75rem;color:#64748b">{pf}</div></div>\n'
    
    html += f'''</div>

<div class="chart">
        {bars_block}
      </div>
      <div class="x-labels">
          {x_labels}
      </div>

<p class="footer">Auto-generated by run_qa.py · Power Squad QA Cron</p>
</body>
</html>'''

    with open(TRENDS_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"📊 趨勢儀表板已產出: {TRENDS_FILE} ({len(html)} bytes)")


# ═══════════════════════════════════════
# 主邏輯
# ═══════════════════════════════════════

def once(baseline_enabled: bool = True, alert_enabled: bool = True, product_filter: str = None):
    """單次掃描。"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"=== QA Cron Scan @ {timestamp} ===")
    print()

    current = scan_all(product_filter=product_filter)

    if baseline_enabled:
        drops = compare_with_baseline(current)
        save_baseline(current)
        append_history(current, timestamp)

        # 連續退步 escalate（per-product）
        escalate_list = check_escalate(drops) if drops else []
        if escalate_list:
            esc_msg = format_escalate_message(escalate_list, timestamp)
            print(f"\n🚨 ESCALATE: {', '.join(escalate_list)} 連續 {ESCALATE_THRESHOLD} 次退步！")
            if alert_enabled:
                post_to_board_chat(esc_msg)
        elif drops and alert_enabled:
            alert_msg = format_alert_message(drops, timestamp)
            print(f"\n📢 發現 {len(drops)} 項變更，推播告警...")
            post_to_board_chat(alert_msg)
        elif not drops:
            print("\n✅ 分數無變化，安靜。")
    else:
        append_history(current, timestamp)
        print("\n📋 Baseline 模式關閉 — 跳過比較。")

    # 自動更新趨勢儀表板
    generate_trends_html()

    return current


def watch():
    """持續監控模式。"""
    print("🟢 QA Cron 監控已啟動")
    print(f"   掃描間隔: {SCAN_INTERVAL}s ({SCAN_INTERVAL//3600}h)")
    print(f"   監控目標: {len(WATCH_TARGETS)} 套")
    print()

    while True:
        try:
            once()
        except Exception as e:
            print(f"❌ 掃描週期異常: {e}", file=sys.stderr)

        next_scan = datetime.datetime.now() + datetime.timedelta(seconds=SCAN_INTERVAL)
        print(f"\n⏰ 下次掃描: {next_scan.strftime('%H:%M')}")
        time.sleep(SCAN_INTERVAL)


def reset_baseline():
    """手動重置 baseline。"""
    if os.path.isfile(BASELINE_FILE):
        os.remove(BASELINE_FILE)
        print(f"🗑 Baseline 已重置: {BASELINE_FILE}")
    else:
        print("⚠ 無 baseline 可重置。")


# ═══════════════════════════════════════
# JSON Summary（CI 可解析結構化輸出）
# ═══════════════════════════════════════

def json_summary(current: dict) -> dict:
    """產生 CI-ready 結構化摘要。
    格式: {product: {scores, trend, status, checked_at}} 
    """
    baseline = load_baseline()
    history = load_history()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    summary = {}
    for name, scores in current.items():
        prev = baseline.get(name, {})
        prev_pct = prev.get("pct", None)
        curr_pct = scores.get("pct", 0) if "error" not in scores else 0
        
        # 趨勢：比對上次
        trend = "stable"
        if prev_pct is not None:
            if curr_pct > prev_pct:
                trend = "up"
            elif curr_pct < prev_pct:
                trend = "down"
        
        # 狀態
        status = "pass" if scores.get("fail_count", 1) == 0 else "warn"
        if "error" in scores:
            status = "error"
        
        entry = {
            "product": name,
            "scores": scores,
            "trend": trend,
            "trend_vs_baseline": {"prev_pct": prev_pct, "curr_pct": curr_pct},
            "status": status,
            "checked_at": timestamp,
        }
        
        # 加入連續退步資訊
        if trend == "down" and len(history) >= ESCALATE_THRESHOLD:
            consecutive = 0
            for hist_entry in reversed(history[-ESCALATE_THRESHOLD:]):
                hs = hist_entry.get("scans", {}).get(name, {})
                if hs.get("pct", 100) < 85 or hs.get("fail_count", 0) > 0:
                    consecutive += 1
            if consecutive >= ESCALATE_THRESHOLD:
                entry["status"] = "escalate"
                entry["escalate_consecutive"] = consecutive
        
        summary[name] = entry
    
    return {
        "summary": summary,
        "overall": {
            "products_scanned": len(current),
            "products_pass": sum(1 for v in summary.values() if v["status"] == "pass"),
            "products_warn": sum(1 for v in summary.values() if v["status"] == "warn"),
            "products_escalate": sum(1 for v in summary.values() if v["status"] == "escalate"),
            "checked_at": timestamp,
        }
    }


# ═══════════════════════════════════════
# CLI
# ═══════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="QA Pipeline Cron Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
模式:
  --once             一次性掃描並回報
  --watch            持續監控（每 4h）
  --reset-baseline   清除歷史分數基準
  --json             僅輸出原始結果 JSON
  --json-summary     輸出結構化摘要 JSON（CI 可解析）

範例:
  python3 run_qa.py --once
  python3 run_qa.py --once --product aps
  python3 run_qa.py --once --json-summary
  python3 run_qa.py --reset-baseline
        """
    )
    parser.add_argument("--once", action="store_true", help="一次性掃描")
    parser.add_argument("--watch", action="store_true", help="持續監控")
    parser.add_argument("--reset-baseline", action="store_true", help="清除 baseline")
    parser.add_argument("--json", action="store_true", help="輸出原始結果 JSON")
    parser.add_argument("--json-summary", action="store_true", help="輸出結構化摘要 JSON（CI 可解析）")
    parser.add_argument("--no-alert", action="store_true", help="禁用 board chat 告警")
    parser.add_argument("--trends", action="store_true", help="僅生成 trends.html（不掃描）")
    parser.add_argument("--product", help="單產品掃描: aps | cris | runs（可逗號分隔）")

    args = parser.parse_args()

    if args.reset_baseline:
        reset_baseline()
        return

    if args.trends:
        generate_trends_html()
        return

    if args.watch:
        watch()
        return

    # 預設：--once
    current = once(baseline_enabled=True, alert_enabled=not args.no_alert, product_filter=args.product)

    if args.json_summary:
        # JSON output only — suppress log noise
        summary = json_summary(current)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    elif args.json:
        print(json.dumps(current, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()