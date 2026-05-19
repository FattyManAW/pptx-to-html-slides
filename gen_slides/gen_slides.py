#!/usr/bin/env python3
"""gen_slides.py — PPTX → v3 HTML Slides (one command)"""
import json, sys, os, argparse

def semantic_upgrade(html):
    """R1-R4: slide type classification, heading tagging, feat-grid, stat-num"""
    import re

    DIVIDER_KEYWORDS = ['政策','趋势','挑战','解决方案','案例','实施步骤','现状','痛点分析','合作伙伴']

    def classify_slide(texts):
        clean = [t for t in texts if t.strip() and t.strip() != '添加文本']
        if not clean: return 'empty'
        if len(clean) == 1:
            t = clean[0]
            for kw in DIVIDER_KEYWORDS:
                if kw in t and len(t) <= 20: return 'divider'
            if any(kw in t for kw in ['Thank you','谢谢']): return 'thanks'
            return 'divider'
        return 'content'

    def tag_line(text):
        t = text.strip()
        if not t: return None
        if re.match(r'^\d{1,2}$', t): return ('tag', t)
        if t.endswith('：') or t.endswith(':'):
            return ('h3', t.rstrip('：:')) if len(t) <= 15 else ('h4', t)
        if '——' in t and len(t) <= 25: return ('h3', t)
        if t.endswith('-') and len(t) <= 25: return ('h4', t.rstrip('-'))
        if len(t) >= 60: return ('p', t)
        if len(t) <= 30:
            if not any(c in t for c in '，。、；') and len(t) <= 18: return ('h4', t)
            return ('p-sub', t)
        return ('p', t)

    def inject_feat_grid(items):
        if len(items) < 4: return None
        pairs = []; i = 0
        while i < len(items):
            if items[i][0] in ('h3', 'h4'):
                heading = items[i]
                body = items[i+1] if i+1 < len(items) and items[i+1][0] in ('p','p-sub') else None
                pairs.append((heading, body)); i += 2 if body else 1
            else: i += 1
        return pairs if len(pairs) >= 4 else None

    def extract_stat(text):
        for pat, repl in [(r'(\d[\d,.]*)\s*(吨|噸|年|天|万|萬|家|项|項|亿|億|pp)', r'<span class="stat-num">\1</span>\2'),
                          (r'(\d[\d,.]*%)', r'<span class="stat-highlight">\1</span>')]:
            if re.search(pat, text): text = re.sub(pat, repl, text)
        return text

    slide_re = re.compile(r'(<div class="slide"[^>]*><div class="slide-inner">)(.*?)(</div></div>)', re.DOTALL)

    def upgrade_slide(m):
        prefix, content, suffix = m.group(1), m.group(2), m.group(3)
        texts = re.findall(r'<p[^>]*>(.*?)</p>', content)
        imgs = re.findall(r'<img[^>]*>', content)
        if not texts: return prefix + '\n'.join(imgs) + suffix
        slide_type = classify_slide(texts)
        texts = [t for t in texts if t.strip() != '添加文本']
        if slide_type == 'divider':
            return f'{prefix}<div class="divider"><h2>{texts[0] if texts else ""}</h2></div>{suffix}'
        if slide_type == 'thanks':
            return f'{prefix}<h1 class="thanks-text">{texts[0]}</h1>{suffix}'
        tagged = [tag_line(t) for t in texts]; tagged = [x for x in tagged if x]
        grid_pairs = inject_feat_grid(tagged)
        parts = []
        if grid_pairs:
            parts.append('<div class="feat-grid">')
            for h, b in grid_pairs:
                parts.append(f'<div class="feat-item data-stagger" style="animation-delay:var(--d-stagger)">')
                parts.append(f'<{h[0]}>{extract_stat(h[1])}</{h[0]}>')
                if b: parts.append(f'<p class="txt-body-2">{extract_stat(b[1])}</p>')
                parts.append('</div>')
            parts.append('</div>')
            handled = len(grid_pairs) * 2
            for tag, text in tagged[handled:]:
                text = extract_stat(text)
                if tag == 'p': parts.append(f'<p class="txt-body">{text}</p>')
                elif tag == 'p-sub': parts.append(f'<p class="txt-body-2">{text}</p>')
                elif tag in ('h3','h4'): parts.append(f'<{tag}>{text}</{tag}>')
                elif tag == 'tag': parts.append(f'<span class="tag tag--violet">{text}</span>')
        else:
            parts.append('<div class="content-block">')
            for tag, text in tagged:
                text = extract_stat(text)
                if tag == 'p': parts.append(f'<p class="txt-body">{text}</p>')
                elif tag == 'p-sub': parts.append(f'<p class="txt-body-2">{text}</p>')
                elif tag in ('h3','h4'): parts.append(f'<{tag}>{text}</{tag}>')
                elif tag == 'tag': parts.append(f'<span class="tag tag--violet">{text}</span>')
            parts.append('</div>')
        if imgs: parts.append('\n'.join(imgs))
        inner = '\n'.join(parts)
        return f'{prefix}\n{inner}\n{suffix}'

    return slide_re.sub(upgrade_slide, html)


def main():
    ap = argparse.ArgumentParser(description='PPTX → v3 HTML Slides generator')
    ap.add_argument('--pptx', required=True, help='Input PPTX path')
    ap.add_argument('--design', default='design_tokens/v3_tokens.json', help='Design tokens JSON path')
    ap.add_argument('--output', required=True, help='Output HTML path')
    ap.add_argument('--img-dir', default='html/images', help='Image directory (relative to output)')
    ap.add_argument('--section-names', help='Comma-separated section names')
    ap.add_argument('--extract-only', action='store_true', help='Only extract PPTX to JSON spec')
    ap.add_argument('--theme', choices=['v3_dark','v3_warm','v3_green'], help='Color theme (overrides design tokens)')
    ap.add_argument('--semantic', action='store_true', help='Run semantic upgrade (dividers, feat-grid, stat-num) after rendering')
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
    spec = extract(args.pptx, secs, img_dir=args.img_dir)

    if args.extract_only:
        print(json.dumps(spec, ensure_ascii=False, indent=2))
        return

    # Render HTML
    from renderer import render_slides
    html = render_slides(spec, tokens, img_dir=args.img_dir)

    if args.semantic:
        html = semantic_upgrade(html)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, 'w') as f:
        f.write(html)

    size_kb = len(html) // 1024
    print(f"✅ {spec['source']} → {args.output}")
    print(f"   {spec['total']} slides | {size_kb}KB")

if __name__ == '__main__':
    main()
