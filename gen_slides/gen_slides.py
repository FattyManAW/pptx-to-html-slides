#!/usr/bin/env python3
"""gen_slides.py — PPTX → v3 HTML Slides (one command)"""
import json, sys, os, argparse

def main():
    ap = argparse.ArgumentParser(description='PPTX → v3 HTML Slides generator')
    ap.add_argument('--pptx', required=True, help='Input PPTX path')
    ap.add_argument('--design', default='design_tokens/v3_tokens.json', help='Design tokens JSON path')
    ap.add_argument('--output', required=True, help='Output HTML path')
    ap.add_argument('--img-dir', default='html/images', help='Image directory (relative to output)')
    ap.add_argument('--section-names', help='Comma-separated section names')
    ap.add_argument('--extract-only', action='store_true', help='Only extract PPTX to JSON spec')
    args = ap.parse_args()

    # Load design tokens
    tokens_path = args.design
    if not os.path.isabs(tokens_path):
        tokens_path = os.path.join(os.path.dirname(__file__), tokens_path)
    with open(tokens_path) as f:
        tokens = json.load(f)

    # Extract PPTX
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    from pptx_extractor import extract

    secs = args.section_names.split(',') if args.section_names else None
    spec = extract(args.pptx, secs)

    if args.extract_only:
        print(json.dumps(spec, ensure_ascii=False, indent=2))
        return

    # Render HTML
    from renderer import render_slides
    html = render_slides(spec, tokens, img_dir=args.img_dir)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, 'w') as f:
        f.write(html)

    size_kb = len(html) // 1024
    print(f"✅ {spec['source']} → {args.output}")
    print(f"   {spec['total']} slides | {size_kb}KB")

if __name__ == '__main__':
    main()
