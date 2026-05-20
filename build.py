#!/usr/bin/env python3
"""
build.py — gen_slides v6 跨產品統一 Build System

單一 CLI 入口，全線自動重建三套產品 + QA gate + deploy。

用法:
  python build.py --all                # 潤思+APS+CRIS 全重建
  python build.py --product aps        # 單產品重建
  python build.py --qa                 # 重建 + QA gate
  python build.py --deploy             # 重建 + QA + gh-pages deploy
  python build.py --canonical          # 重建 + canonical token 注入
  python build.py --all --qa --deploy   # 全鏈（完整 Pipeline v6）

pipeline:
  tokens.json → canonical → gen_slides_v4 → extract-tokens → run_qa → deploy

"""

import os
import sys
import json
import subprocess
import argparse
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
SHOWCASE_DIR = SCRIPT_DIR / "showcase"
TOKENS_FILE = SHOWCASE_DIR / "tokens.json"
PPTX_DIR = SCRIPT_DIR

# ─── Product Registry ────────────────────────────────────────────
# pptx 檔案 → template → output HTML
PRODUCTS = {
    "runs": {
        "name": "潤思IMPACTS",
        "pptx": "润思IMPACTS APS生态伙伴解决方案_202601V2.0.pptx",
        "template": "runs",
        "output": "runs-impacts-aps-partner.html",
    },
    "aps": {
        "name": "APS AI Agent",
        "pptx": "APS AI Agent 智能体解决方案_20260113.pptx",
        "template": "aps",
        "output": "aps-ai-agent.html",
    },
    "cris": {
        "name": "CRIS IMPACTs",
        "pptx": "CRIS IMPACTs 双碳管理系统_202601_V2.0.pptx",
        "template": "cris",
        "output": "cris-impacts-carbon.html",
    },
}


def run_cmd(cmd, label="", check=True):
    """執行 shell command，回傳 (returncode, stdout, stderr)。"""
    print(f"  🔧 {label}…", flush=True)
    result = subprocess.run(
        cmd, shell=isinstance(cmd, str), capture_output=True, text=True,
        cwd=str(SCRIPT_DIR)
    )
    if result.stdout:
        print(f"    {result.stdout[-300:]}")
    if result.returncode != 0 and check:
        print(f"    ❌ exit {result.returncode}", flush=True)
        if result.stderr:
            print(f"    stderr: {result.stderr[-200:]}", flush=True)
    return result.returncode, result.stdout, result.stderr


def build_product(product_key: str, canonical: bool = False, img_dir: str = "images") -> dict:
    """重建單一產品。回傳結果 dict。"""
    p = PRODUCTS[product_key]
    pptx_path = PPTX_DIR / p["pptx"]
    output_path = SHOWCASE_DIR / p["output"]

    if not pptx_path.exists():
        return {"product": p["name"], "ok": False, "error": f"PPTX not found: {pptx_path}"}

    print(f"\n📦 {p['name']} ({product_key})", flush=True)

    cmd = [
        sys.executable, "gen_slides_v4.py",
        "--pptx", str(pptx_path),
        "--output", str(output_path),
        "--template", p["template"],
        "--img-dir", img_dir,
    ]
    if canonical:
        cmd.append("--canonical")

    rc, stdout, stderr = run_cmd(cmd, f"gen_slides_v4 {product_key}", check=False)

    size_kb = 0
    if output_path.exists():
        size_kb = output_path.stat().st_size // 1024

        # ─── v6: auto-inject a11y post-build ───
        print(f"  🧪 a11y injection…", flush=True)
        try:
            sys.path.insert(0, str(SCRIPT_DIR / "gen_slides" / "src"))
            from a11y import enhance_html
            with open(output_path) as fh:
                html_enhanced = enhance_html(fh.read(), slides_count=0)
            with open(output_path, "w") as fh:
                fh.write(html_enhanced)
            enhanced_kb = len(html_enhanced.encode("utf-8")) // 1024
            print(f"  ✅ a11y: {size_kb}KB → {enhanced_kb}KB", flush=True)
            size_kb = enhanced_kb
        except Exception as e:
            print(f"  ⚠️  a11y injection failed: {e}", flush=True)

    return {
        "product": p["name"],
        "key": product_key,
        "ok": rc == 0 and output_path.exists(),
        "size_kb": size_kb,
        "output": str(output_path),
        "rc": rc,
    }


def run_canonical_gate() -> dict:
    """執行 extract-tokens.py --canonical gate。"""
    rc, stdout, stderr = run_cmd(
        f"{sys.executable} extract-tokens.py --canonical",
        "extract-tokens --canonical",
        check=False
    )
    missing = 0
    if "missing" in stdout.lower():
        import re
        m = re.search(r'(\d+)\s+missing', stdout)
        if m:
            missing = int(m.group(1))

    return {
        "ok": rc == 0 and missing == 0,
        "rc": rc,
        "missing_slots": missing,
        "raw": stdout[-500:],
    }


def run_qa_gate() -> dict:
    """執行 run_qa.py --ci。"""
    rc, stdout, stderr = run_cmd(
        f"{sys.executable} run_qa.py --ci",
        "run_qa --ci",
        check=False
    )
    # Parse JSON result
    try:
        # Find JSON in output
        json_start = stdout.find('{')
        if json_start >= 0:
            data = json.loads(stdout[json_start:])
            overall = data.get("overall", {})
            return {
                "ok": rc == 0,
                "rc": rc,
                "products_pass": overall.get("products_pass", 0),
                "products_fail": overall.get("products_fail", 0),
                "products_warn": overall.get("products_warn", 0),
                "raw": data,
            }
    except (json.JSONDecodeError, IndexError):
        pass
    return {"ok": rc == 0, "rc": rc, "raw": stdout[-500:]}


def run_deploy() -> dict:
    """執行 git push gh-pages (deploy)。"""
    print("  🚀 Deploy → gh-pages…", flush=True)
    # Check if gh-pages branch exists
    result = subprocess.run(
        ["git", "push", "origin", "main"],
        capture_output=True, text=True, cwd=str(SCRIPT_DIR)
    )
    return {
        "ok": result.returncode == 0,
        "rc": result.returncode,
        "raw": (result.stdout + result.stderr)[-500:],
    }


def build_all(canonical: bool = False, qa: bool = False, deploy: bool = False) -> dict:
    """全產品重建 pipeline。"""
    start = time.time()
    print("=" * 60, flush=True)
    print("🏗️  gen_slides v6 — Build System", flush=True)
    print(f"   Products: {list(PRODUCTS.keys())}", flush=True)
    print(f"   Canonical: {canonical} | QA: {qa} | Deploy: {deploy}", flush=True)
    print("=" * 60, flush=True)

    results = {"builds": [], "canonical": None, "qa": None, "deploy": None}

    # Step 1: Build
    print("\n📌 Step 1: Build all products", flush=True)
    for key in PRODUCTS:
        r = build_product(key, canonical=canonical)
        results["builds"].append(r)
        icon = "✅" if r["ok"] else "❌"
        print(f"  {icon} {r['product']}: {r.get('size_kb', 0)}KB rc={r.get('rc', '?')}", flush=True)

    # Step 2: Canonical Gate
    if canonical:
        print("\n📌 Step 2: Canonical Gate", flush=True)
        cg = run_canonical_gate()
        results["canonical"] = cg
        icon = "✅" if cg["ok"] else "❌"
        print(f"  {icon} missing_slots={cg.get('missing_slots', '?')} rc={cg.get('rc', '?')}", flush=True)

    # Step 3: QA Gate
    if qa:
        print("\n📌 Step 3: QA Gate", flush=True)
        qr = run_qa_gate()
        results["qa"] = qr
        icon = "✅" if qr["ok"] else "❌"
        print(f"  {icon} pass={qr.get('products_pass', '?')} fail={qr.get('products_fail', '?')} rc={qr.get('rc', '?')}", flush=True)

    # Step 4: Deploy
    if deploy:
        print("\n📌 Step 4: Deploy", flush=True)
        dr = run_deploy()
        results["deploy"] = dr
        icon = "✅" if dr["ok"] else "❌"
        print(f"  {icon} rc={dr.get('rc', '?')}", flush=True)

    elapsed = time.time() - start
    results["elapsed"] = f"{elapsed:.1f}s"
    results["ok"] = all(r["ok"] for r in results["builds"]) and \
                    (not canonical or results["canonical"]["ok"]) and \
                    (not qa or results["qa"]["ok"]) and \
                    (not deploy or results["deploy"]["ok"])

    print(f"\n{'=' * 60}", flush=True)
    icon = "✅" if results["ok"] else "❌"
    print(f"{icon} Pipeline {'PASSED' if results['ok'] else 'FAILED'} in {elapsed:.1f}s", flush=True)
    print("=" * 60, flush=True)
    return results


def main():
    ap = argparse.ArgumentParser(
        description="build.py — gen_slides v6 跨產品統一 Build System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  python build.py --all                  # 三套全重建
  python build.py --product aps          # 單產品（APS）
  python build.py --all --qa             # 重建 + QA gate
  python build.py --all --qa --deploy    # 全鏈（build → QA → deploy）
  python build.py --all --canonical --qa # 全鏈含 canonical gate
        """
    )
    ap.add_argument("--all", action="store_true", help="重建三套產品（潤思+APS+CRIS）")
    ap.add_argument("--product", choices=list(PRODUCTS.keys()), help="單產品重建（runs|aps|cris）")
    ap.add_argument("--qa", action="store_true", help="重建後執行 QA gate (run_qa --ci)")
    ap.add_argument("--canonical", action="store_true", help="注入 canonical token shim")
    ap.add_argument("--deploy", action="store_true", help="重建後 git push deploy")
    ap.add_argument("--json", action="store_true", help="輸出 JSON summary")
    args = ap.parse_args()

    if not args.all and not args.product:
        ap.print_help()
        print("\n❌ 請指定 --all 或 --product", file=sys.stderr)
        sys.exit(1)

    # Build
    if args.all:
        results = build_all(canonical=args.canonical, qa=args.qa, deploy=args.deploy)
    else:
        r = build_product(args.product, canonical=args.canonical)
        results = {"builds": [r], "ok": r["ok"]}

    # Output
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))

    sys.exit(0 if results.get("ok") else 1)


if __name__ == "__main__":
    main()
