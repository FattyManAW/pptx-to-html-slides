#!/usr/bin/env python3
"""
gen_slides_v4.py — PPTX → Structured JSON → HTML 自動化管線

v4 模組化重構（2026-05-20）：
- gen_slides/src/extractor.py — PPTX → JSON
- gen_slides/src/renderer_v4.py — JSON → HTML
- gen_slides/src/upgrader.py — semantic injection
- gen_slides/src/themes.py — 設計主題

用法：
  python3 gen_slides_v4.py --pptx input.pptx --output output.html
  python3 gen_slides_v4.py --pptx input.pptx --json-only
  python3 gen_slides_v4.py --pptx input.pptx --template cris
"""

import sys
import os
import json
import argparse

# 從模組導入
sys.path.insert(0, os.path.dirname(__file__))
from gen_slides.src.extractor import extract, classify_slide, is_placeholder, extract_pptx
from gen_slides.src.renderer_v4 import render, render_html
from gen_slides.src.upgrader import upgrade, semantic_upgrade
from gen_slides.src.themes import THEMES, get_theme, list_themes, PLACEHOLDER_PATTERNS, SECTION_KEYWORDS, COMPARISON_KEYWORDS
from gen_slides.src.canonical_map import remap_html_file

# ───── 向後相容 export ─────
# 所有核心函式已遷移至 gen_slides/src/ 模組
# 保留 gen_slides_v4.py 作為 CLI entry point + import * 橋接
PLACEHOLDER_PATTERNS = list(PLACEHOLDER_PATTERNS)  # from themes
SECTION_KEYWORDS = list(SECTION_KEYWORDS)
COMPARISON_KEYWORDS = list(COMPARISON_KEYWORDS)


# ───── CLI ────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="gen_slides_v4 — PPTX → JSON → HTML (modular)")
    ap.add_argument("--pptx", required=True, help="輸入 PPTX 路徑")
    ap.add_argument("--output", "-o", help="輸出 HTML 路徑")
    ap.add_argument("--json-only", action="store_true", help="只輸出 JSON")
    ap.add_argument("--json-out", help="JSON 輸出到檔案")
    ap.add_argument("--template", "-t", choices=["cris", "aps", "runs"], default="cris", help="設計模板")
    ap.add_argument("--img-dir", default="images", help="圖片輸出目錄")
    ap.add_argument("--section-names", help="逗號分隔章節名稱")
    ap.add_argument("--canonical", action="store_true", help="注入 Christina Canonical token shim（50 APS→Canonical mappings + --ds-* tokens）")
    args = ap.parse_args()

    if not os.path.exists(args.pptx):
        print(f"❌ 找不到 PPTX: {args.pptx}", file=sys.stderr)
        sys.exit(1)

    print(f"📦 提取中... {args.pptx}", file=sys.stderr)
    spec = extract(args.pptx, img_dir=args.img_dir)

    if args.section_names:
        names = [n.strip() for n in args.section_names.split(",")]
        n_slides = len(spec["slides"])
        per = max(1, n_slides // len(names))
        for idx, name in enumerate(names):
            pos = min(idx * per, n_slides - 1)
            spec["slides"][pos]["_section"] = name

    # 語義注入
    spec = upgrade(spec)

    if args.json_only:
        print(json.dumps(spec, ensure_ascii=False, indent=2))
        print(f"\n✅ {spec['total']} slides extracted", file=sys.stderr)
        return

    if args.json_out:
        with open(args.json_out, "w") as f:
            json.dump(spec, f, ensure_ascii=False, indent=2)
        print(f"📋 JSON: {args.json_out}", file=sys.stderr)

    output_path = args.output or os.path.splitext(args.pptx)[0] + ".html"
    print(f"🎨 渲染中... template={args.template}", file=sys.stderr)
    html = render(spec, template=args.template, img_dir=args.img_dir)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)

    # Canonical shim injection
    if args.canonical:
        from gen_slides.src.canonical_map import apply_shim, load_mappings
        mappings = load_mappings()
        html = apply_shim(html, mappings)
        aps_count = len(mappings.get("aps_to_canonical", {}))
        ds_count = len(mappings.get("ds_tokens", {}))
        print(f"   canonical: {aps_count} token mappings + {ds_count} --ds-* tokens injected", file=sys.stderr)

    with open(output_path, "w") as f:
        f.write(html)

    size_kb = len(html.encode("utf-8")) // 1024
    print(f"✅ {spec['source']} → {output_path}", file=sys.stderr)
    print(f"   {spec['total']} slides | {size_kb}KB | template={args.template}", file=sys.stderr)

    types = {}
    for s in spec["slides"]:
        t = s.get("type", "content")
        types[t] = types.get(t, 0) + 1
    print(f"   類型: {', '.join(f'{k}×{v}' for k,v in sorted(types.items()))}", file=sys.stderr)


if __name__ == "__main__":
    main()