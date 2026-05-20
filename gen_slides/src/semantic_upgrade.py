#!/usr/bin/env python3
"""
Generator 語義層升級 Phase 1
Input: gen 產出的 flat HTML (all <p>)
Output: 語義化 HTML (dividers, heading levels, feat-grid, stat-num)
"""

import re, sys

DIVIDER_KEYWORDS = ['政策','趋势','挑战','解决方案','案例','实施步骤','现状','痛点分析','合作伙伴']

def classify_slide(texts):
    """R1: Slide type classification"""
    clean = [t for t in texts if t.strip() and t.strip() != '添加文本']
    if not clean:
        return "empty"
    if len(clean) == 1:
        t = clean[0]
        for kw in DIVIDER_KEYWORDS:
            if kw in t and len(t) <= 20:
                return "divider"
        if any(kw in t for kw in ['Thank you','谢谢']):
            return "thanks"
        return "divider"  # single-line = divider by default
    return "content"

def tag_line(text):
    """R2: Determine if a line is a heading, and what level"""
    t = text.strip()
    if not t:
        return None
    
    # Skip pure numbers/ordering
    if re.match(r'^\d{1,2}$', t):
        return ('tag', t)
    
    # : 結尾 ≤12 字 → h3
    if t.endswith('：') or t.endswith(':'):
        if len(t) <= 15:
            return ('h3', t.rstrip('：:'))
        return ('h4', t)
    
    # —— 分隔 ≤20 字 → h3  
    if '——' in t and len(t) <= 25:
        return ('h3', t)
    
    # - 結尾的 sub-header → h4
    if t.endswith('-') and len(t) <= 25:
        return ('h4', t.rstrip('-'))
    
    # Long text → body
    if len(t) >= 60:
        return ('p', t)
    
    # Medium → sub-label
    if len(t) <= 30:
        # Check if it looks like a heading (short, no punctuation)
        if not any(c in t for c in '，。、；') and len(t) <= 18:
            return ('h4', t)
        return ('p-sub', t)
    
    return ('p', t)

def inject_feat_grid(items):
    """R3: Wrap 4+ heading+text pairs into feat-grid"""
    if len(items) < 4:
        return None
    
    # Check pattern: h4 followed by p-sub or p
    pairs = []
    i = 0
    while i < len(items):
        if items[i][0] in ('h3', 'h4'):
            heading = items[i]
            body = items[i+1] if i+1 < len(items) and items[i+1][0] in ('p', 'p-sub') else None
            pairs.append((heading, body))
            i += 2 if body else 1
        else:
            i += 1
    
    if len(pairs) < 4:
        return None
    
    return pairs

def extract_stat(text):
    """R4: Detect and wrap stat numbers"""
    # 8986吨, 2.5年, 40%, 500万元, 100万元
    patterns = [
        (r'(\d[\d,.]*)\s*(吨|噸|年|天|万|萬|家|项|項|亿|億|pp)', r'<span class="stat-num">\1</span>\2'),
        (r'(\d[\d,.]*%)', r'<span class="stat-highlight">\1</span>'),
    ]
    for pat, repl in patterns:
        if re.search(pat, text):
            text = re.sub(pat, repl, text)
    return text

def upgrade_html(input_path, output_path):
    """Main upgrade pipeline"""
    html = open(input_path).read()
    
    # Match any slide div (may have aria/role attrs)
    slide_pattern = re.compile(r'(<div class="slide"[^>]*><div class="slide-inner">)(.*?)(</div></div>)', re.DOTALL)
    
    def upgrade_slide(match):
        prefix = match.group(1)
        content = match.group(2)
        suffix = match.group(3)
        
        # Extract <p> texts and <img> tags
        texts = re.findall(r'<p>(.*?)</p>', content)
        imgs = re.findall(r'<img[^>]*>', content)
        
        if not texts:
            # Image-only slide — keep imgs
            return prefix + '\n'.join(imgs) + suffix
        
        slide_type = classify_slide(texts)
        
        # Filter placeholders
        texts = [t for t in texts if t.strip() != '添加文本']
        
        if slide_type == 'divider':
            t = texts[0] if texts else ''
            return f'{prefix}<div class="divider"><h2>{t}</h2></div>{suffix}'
        
        if slide_type == 'thanks':
            return f'{prefix}<h1 class="thanks-text">{texts[0]}</h1>{suffix}'
        
        # Content slide: tag each line
        tagged = [tag_line(t) for t in texts]
        tagged = [x for x in tagged if x is not None]
        
        # Try feat-grid
        grid_pairs = inject_feat_grid(tagged)
        
        # Phase 2: trim long text before rendering
        html_parts = []
        if grid_pairs:
            html_parts.append('<div class="feat-grid">')
            for h, b in grid_pairs:
                h_text = extract_stat(trim_text(h[1], max_chars=48))
                html_parts.append(f'<div class="feat-item data-stagger" style="animation-delay:var(--d-stagger)">')
                html_parts.append(f'<{h[0]}>{h_text}</{h[0]}>')
                if b:
                    b_text = extract_stat(trim_text(b[1], max_chars=56))
                    html_parts.append(f'<p class="txt-body-2">{b_text}</p>')
                html_parts.append('</div>')
            html_parts.append('</div>')
            
            handled_count = len(grid_pairs) * 2
            for tag, text in tagged[handled_count:]:
                text = trim_text(text, max_chars=72) if tag in ('p', 'p-sub') else text
                text = extract_stat(text)
                if tag == 'p':
                    html_parts.append(f'<p class="txt-body">{text}</p>')
                elif tag == 'p-sub':
                    html_parts.append(f'<p class="txt-body-2">{text}</p>')
                elif tag in ('h3', 'h4'):
                    html_parts.append(f'<{tag}>{text}</{tag}>')
                elif tag == 'tag':
                    html_parts.append(f'<span class="tag tag--violet">{text}</span>')
        else:
            html_parts.append('<div class="content-block">')
            for tag, text in tagged:
                text = trim_text(text, max_chars=72) if tag in ('p', 'p-sub') else text
                text = extract_stat(text)
                if tag == 'p':
                    html_parts.append(f'<p class="txt-body">{text}</p>')
                elif tag == 'p-sub':
                    html_parts.append(f'<p class="txt-body-2">{text}</p>')
                elif tag in ('h3', 'h4'):
                    html_parts.append(f'<{tag}>{text}</{tag}>')
                elif tag == 'tag':
                    html_parts.append(f'<span class="tag tag--violet">{text}</span>')
            html_parts.append('</div>')
        
        # Add images after content
        if imgs:
            html_parts.append('\n'.join(imgs))
        
        new_content = '\n'.join(html_parts)
        return f'{prefix}\n{new_content}\n{suffix}'
    
    upgraded = slide_pattern.sub(upgrade_slide, html)
    open(output_path, 'w').write(upgraded)
    
    # Stats
    orig = open(input_path).read()
    print(f"Input:  {len(orig.splitlines())} lines | {len(orig)//1024}KB | {len(re.findall('<section', orig))} slides")
    print(f"Output: {len(upgraded.splitlines())} lines | {len(upgraded)//1024}KB")
    
    # Count semantic elements
    for elem in ['divider', 'feat-grid', 'feat-item', 'stat-num', 'stat-highlight', 
                 'content-block', '<h3>', '<h4>', 'tag--violet', '数据-stagger']:
        count = upgraded.count(elem)
        if count > 0:
            print(f"  {elem:25s}: {count}")
    
    # Check remaining flatness
    flat_p = upgraded.count('<p>') - upgraded.count('<p class="txt')
    print(f"  {'<p> (flat)':25s}: {flat_p}")

# ── Phase 2: Content Trimming Engine ──

def trim_text(text, max_chars=80):
    """
    Smart trim: first sentence, max_chars ceiling, preserve data.
    Priority order: first 。→ max_chars → first ，→ hard cut
    """
    t = text.strip()
    if not t or len(t) <= max_chars:
        return t
    
    # Strategy 1: first complete sentence (。)
    dot = t.find('。')
    if dot > 0 and dot <= max_chars:
        return t[:dot+1]
    
    # Strategy 2: max_chars at sentence boundary (；)
    semi = t.find('；')
    if semi > 0 and semi <= max_chars:
        return t[:semi+1]
    
    # Strategy 3: max_chars at clause boundary (，)
    comma = t.rfind('，', 0, max_chars)
    if comma > max_chars * 0.6:
        return t[:comma] + '…'
    
    # Strategy 4: hard cut at max_chars
    return t[:max_chars-1] + '…'


def trim_duplicate_slides(slides):
    """
    Remove consecutive duplicate slides (same title).
    Common in PPT: title slide repeated before content.
    """
    seen_titles = {}
    trimmed = []
    for i, slide in enumerate(slides):
        # Extract first non-empty text as title
        texts = slide.get("texts", [])
        title = texts[0].strip() if texts else ""
        if not title:
            trimmed.append(slide)
            continue
        
        clean_title = title.rstrip('：:')
        if clean_title in seen_titles:
            # Duplicate: keep only if it has significantly more content
            prev_idx = seen_titles[clean_title]
            prev_len = len(slides[prev_idx].get("texts", []))
            curr_len = len(texts)
            if curr_len <= prev_len:
                continue  # skip this duplicate
        
        seen_titles[clean_title] = i
        trimmed.append(slide)
    
    return trimmed


# Phase 1 + Phase 2 combined pipeline
if __name__ == '__main__':
    import sys
    inp = sys.argv[1] if len(sys.argv) > 1 else "/Users/henry/Documents/任務檔案/投影片轉換/html/cris-impacts-gen.html"
    out = sys.argv[2] if len(sys.argv) > 2 else inp.replace('.html', '-v4.html')
    upgrade_html(inp, out)
