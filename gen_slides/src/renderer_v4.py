"""
renderer.py — Structured JSON → HTML (gen_slides v4 module)

提供：
- render(spec, template, img_dir) → HTML string
- 獨立於現有 renderer.py（bundled CSS approach）
"""

import os
import sys
from .themes import get_theme


def build_tokens(theme_spec):
    """從 theme dict 建構 tokens 物件。"""
    c = theme_spec.get("colors", {})
    return {
        "name": theme_spec.get("name", "Untitled"),
        "colors": c,
        "typography": {
            "display": {"family": "'Playfair Display',serif", "weights": "700;800;900", "use": "cover-title,section-title"},
            "heading": {"family": "'Playfair Display','Noto Serif SC',serif", "weights": "600;700", "use": "slide-title,item-card h4"},
            "body": {"family": "'Inter','Noto Sans SC',sans-serif", "weights": "300;400;500;600;700", "use": "slide-body,slide-sub"},
        },
        "timing": {
            "fast": "150ms", "mid": "300ms", "slow": "400ms",
            "stagger": [0, 80, 160, 240, 320],
            "ease": "cubic-bezier(0.4, 0, 0.2, 1)",
            "wheelDebounce": 120,
        },
        "spacing": {"s1": "0.5rem", "s2": "1rem", "s3": "1.5rem", "s4": "2rem", "s5": "2.5rem", "s6": "3rem", "s7": "4rem", "s8": "5rem", "s9": "6rem", "s10": "8rem"},
        "layout": {
            "maxWidth": "1100px", "slidePadding": "2rem",
            "sectionBreakBg": "#050810", "sectionNumSize": "6rem",
            "glassBlur": "blur(24px)", "shadow": "0 8px 40px rgba(0,0,0,.35)",
            "breakpoints": {"tablet": 1024, "mobile": 768, "small": 480},
        },
        "fonts": {
            "google": "Inter:wght@300;400;500;600;700|Playfair+Display:wght@600;700;800;900|Noto+Sans+SC:wght@300;400;500;600;700",
            "preconnect": ["https://fonts.googleapis.com", "https://fonts.gstatic.com"],
        },
    }


def _build_css(tokens):
    """從 tokens 建立完整 CSS。"""
    c = tokens["colors"]
    display_font = tokens["typography"]["display"]["family"]
    heading_font = tokens["typography"]["heading"]["family"]
    body_font = tokens["typography"]["body"]["family"]
    accent = c.get("accent", "#14b8a6")
    accent_mid = c.get("accentMid", c.get("c-teal-hot", "#2dd4bf"))
    bg = c.get("c-bg", c.get("ink950", c.get("c-900", "#06080d")))
    ink_text = c.get("c-t1", c.get("ink50", "#f0f4f8"))
    ink_sub = c.get("c-t2", c.get("ink400", "#94a3b8"))
    ink_dim = c.get("c-t3", c.get("ink500", "#64748b"))
    surface = c.get("surface", "rgba(255,255,255,.04)")
    border = c.get("border", "rgba(255,255,255,.08)")

    return f"""/* v4 Design System — {tokens['name']} */
:root {{
  --accent: {accent}; --accent-mid: {accent_mid};
  --c-bg: {bg}; --c-t1: {ink_text}; --c-t2: {ink_sub}; --c-t3: {ink_dim};
  --surface: {surface}; --border: {border};
  --t-fast: 150ms; --t-mid: 300ms; --t-slow: 400ms;
  --ease: cubic-bezier(0.4,0,0.2,1);
  --s1: 0.5rem; --s2: 1rem; --s3: 1.5rem; --s4: 2rem;
  --blur-8: blur(8px); --blur-12: blur(12px); --blur-24: blur(24px); --blur-32: blur(32px);
  --blur-card: blur(10px); --blur-sheet: blur(20px); --blur-modal: blur(30px); --blur-nav: blur(20px);
}}
*,*::before,*::after{{margin:0;padding:0;box-sizing:border-box}}
html,body{{height:100%;overflow:hidden;font-family:{body_font};background:var(--c-bg);color:var(--c-t2);line-height:1.65;-webkit-font-smoothing:antialiased}}
.slides-container{{position:relative;width:100vw;height:100vh;overflow:hidden;background:var(--c-bg)}}
.slide{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;opacity:0;visibility:hidden;padding:2rem;animation:springIn var(--t-slow) var(--ease) forwards;transform:translateY(12px)}}
.slide.active{{opacity:1;visibility:visible;transform:translateY(0);z-index:10}}
.slide *{{opacity:0;transform:translateY(8px);transition:opacity var(--t-mid) var(--ease),transform var(--t-mid) var(--ease)}}
.slide.active *{{opacity:1;transform:translateY(0)}}
@keyframes springIn{{0%{{opacity:0;transform:translateY(12px)scale(.97)}}60%{{opacity:1;transform:translateY(-2px)scale(1.01)}}100%{{opacity:1;transform:translateY(0)scale(1)}}}}
.slide-inner{{width:100%;max-width:1100px;padding:2rem 1.5rem}}
.slide-title{{font-family:{heading_font};font-size:clamp(1.2rem,2.5vw,1.7rem);font-weight:700;color:var(--c-t1);margin-bottom:1rem;position:relative;padding-bottom:.4rem}}
.slide-title::after{{content:'';position:absolute;bottom:-1px;left:0;width:36px;height:2px;background:linear-gradient(90deg,var(--accent),transparent)}}
.slide-body{{font-size:clamp(.8rem,1.2vw,.92rem);color:var(--c-t2);line-height:1.75;margin-bottom:.8rem}}
.slide-headline{{font-family:{heading_font};font-size:clamp(1.1rem,2.2vw,1.5rem);font-weight:700;color:var(--c-t1);margin-bottom:.6rem}}
.progress-bar{{position:fixed;top:0;left:0;height:1.5px;background:linear-gradient(90deg,var(--accent),var(--accent-mid));z-index:301;transition:width var(--t-mid)}}
.progress-track{{position:fixed;bottom:0;left:0;right:0;height:1px;background:rgba(255,255,255,.05);z-index:301}}
.nav-bar{{position:fixed;bottom:0;left:0;right:0;z-index:300;display:flex;align-items:center;justify-content:center;gap:1rem;padding:1rem 2rem;background:linear-gradient(transparent,rgba(6,8,13,.65));backdrop-filter:blur(20px);border-top:1px solid var(--border)}}
.nav-btn{{width:40px;height:40px;border-radius:50%;border:1px solid var(--border);background:var(--surface);color:var(--c-t2);display:flex;align-items:center;justify-content:center;cursor:pointer;transition:all var(--t-fast);user-select:none}}
.nav-btn:hover{{background:rgba(255,255,255,.07);border-color:rgba(20,184,166,.12)}}
.nav-btn:disabled{{opacity:.28;cursor:not-allowed}}
.nav-counter{{font-size:.75rem;color:var(--c-t3);font-weight:500;min-width:3rem;text-align:center}}
.nav-counter .current{{color:var(--c-t1);font-weight:600}}
.cover{{width:100%;height:100%;display:flex;align-items:center;justify-content:center;flex-direction:column;position:relative;overflow:hidden}}
.cover-bg{{position:absolute;inset:0;background:radial-gradient(ellipse 70% 60% at 50% 40%,rgba(20,184,166,.12),transparent 70%)}}
.cover-title{{font-family:{display_font};font-size:clamp(2rem,5.5vw,4rem);font-weight:900;color:var(--c-t1);text-align:center;line-height:1.1;z-index:1;background:linear-gradient(135deg,var(--c-t1) 0%,var(--accent) 50%,var(--c-t1) 100%);background-size:200%;-webkit-background-clip:text;-webkit-text-fill-color:transparent;animation:shimmer 3s ease-in-out infinite}}
@keyframes shimmer{{0%,100%{{background-position:0% 50%}}50%{{background-position:100% 50%}}}}
.cover-sub{{font-size:clamp(.85rem,1.5vw,1.1rem);color:var(--c-t3);margin-top:1.2rem;text-align:center;max-width:600px;z-index:1}}
.section-break{{width:100%;height:100%;display:flex;align-items:center;justify-content:center;flex-direction:column;background:var(--c-bg)}}
.section-num{{font-family:{display_font};font-size:6rem;font-weight:900;color:var(--accent);opacity:.12;line-height:1}}
.section-title{{font-family:{heading_font};font-size:clamp(1.6rem,4vw,2.5rem);font-weight:700;color:var(--c-t1);letter-spacing:-.02em}}
.thankyou{{text-align:center}}
.thankyou h1{{font-family:{display_font};font-size:clamp(2rem,5vw,3.5rem);font-weight:800;color:var(--c-t1);margin-bottom:.5rem}}
.thankyou p{{color:var(--c-t3);font-weight:300;font-size:1.1rem}}
.thankyou .logo{{font-size:.85rem;color:var(--c-t4);margin-top:2rem;letter-spacing:.15em}}
.item-card{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:1rem 1.1rem;transition:all var(--t-fast)}}
.item-card:hover{{background:rgba(255,255,255,.07);border-color:rgba(20,184,166,.12)}}
.item-card h4{{font-family:{heading_font};font-weight:600;color:var(--c-t1);margin-bottom:.4rem}}
.two-col{{display:grid;grid-template-columns:1fr 1fr;gap:2rem}}
.slide-img{{width:100%;height:auto;max-height:55vh;object-fit:contain;border-radius:8px}}
:focus-visible{{outline:2px solid var(--accent);outline-offset:2px}}
*:focus:not(:focus-visible){{outline:none}}
@media(max-width:1024px){{.two-col{{grid-template-columns:1fr}}}}
@media(max-width:768px){{.slide{{padding:1rem}}.two-col{{grid-template-columns:1fr}}.nav-bar{{padding:.5rem 1rem;gap:.5rem}}}}
@media(max-width:480px){{.cover-title{{font-size:1.8rem}}.section-num{{font-size:4rem}}}}
"""


def _render_slide_body(s, img_dir="images"):
    """渲染單張 slide 的 inner HTML。"""
    stype = s.get("type", "content")
    inner = ""

    if stype == "cover":
        title = s.get("t", "")
        subtitle = s.get("st", "")
        inner = f'<div class="cover">\n<div class="cover-bg"></div>\n<h1 class="cover-title">{title}</h1>\n<p class="cover-sub">{subtitle}</p>\n</div>'
    elif stype == "section":
        n = s.get("n", "")
        title = s.get("t", "")
        inner = f'<div class="section-break">\n<div class="section-num">{n}</div>\n<div class="section-title">{title}</div>\n</div>'
    elif stype == "thanks":
        title = s.get("t", "Thank You")
        sub = s.get("st", "")
        inner = f'<div class="thankyou">\n<h1>{title}</h1>\n<p>{sub}</p>\n<div class="logo">Power Squad</div>\n</div>'
    elif stype == "twocol":
        cols = s.get("twocol", [])
        col_html = ""
        for col in cols:
            items = "<br>".join(col.get("ls", []))
            col_html += f'<div class="two-col-item"><h3>{col.get("side","")}</h3><p>{items}</p></div>'
        inner = f'<h2 class="slide-title">{s.get("t","")}</h2>\n<div class="two-col">{col_html}</div>'
    elif stype == "items":
        title = s.get("t", "")
        cards = s.get("items", [])
        items_html = ""
        for card in cards:
            h = card.get("h", "")
            details = "<br>".join(card.get("ls", []))
            items_html += f'<div class="item-card"><h4>{h}</h4><p class="slide-body">{details}</p></div>'
        inner = f'<h2 class="slide-title">{title}</h2>\n<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:1rem">{items_html}</div>'
    else:
        blocks = s.get("blocks", [])
        title = s.get("t", "")
        body = s.get("b", "")
        imgs = s.get("imgs", [])
        inner = f'<h2 class="slide-title">{title}</h2>'
        if body:
            inner += f'\n<p class="slide-body">{body}</p>'
        for block in blocks[1:]:
            inner += f'\n<p class="slide-body">{block}</p>'
        for img in imgs:
            inner += f'\n<img class="slide-img" src="{img_dir}/{img}" alt="" loading="lazy" decoding="async">'

    return inner


def _build_nav_js(total):
    """建立導航 JS。"""
    return f"""<script>
(function(){{
  const slides=document.querySelectorAll('.slide,.section-break');
  const bar=document.getElementById('progressBar');
  const cur=document.getElementById('curNum');
  const prevBtn=document.getElementById('prevBtn');
  const nextBtn=document.getElementById('nextBtn');
  let current=0,total=slides.length;
  const db={{}};
  const W=120;
  function go(n){{
    if(n<0||n>=total)return;
    const p=slides[current];p&&p.classList.remove('active');
    current=n;
    slides[current].classList.add('active');
    bar.style.width=((current+1)/total*100)+'%';
    cur.textContent=current+1;
    prevBtn.disabled=current===0;
    nextBtn.disabled=current===total-1;
  }}
  prevBtn.onclick=()=>go(current-1);
  nextBtn.onclick=()=>go(current+1);
  document.addEventListener('keydown',e=>{{
    if(e.key==='ArrowRight'||e.key===' ')go(current+1);
    if(e.key==='ArrowLeft')go(current-1);
    if(e.key==='Home')go(0);
    if(e.key==='End')go(total-1);
  }});
  document.addEventListener('wheel',e=>{{
    const n=Date.now();
    if(n-db.last<W)return;db.last=n;
    go(current+(e.deltaY>0?1:-1));
  }},{{passive:true}});
  let ty=0;
  document.addEventListener('touchstart',e=>{{ty=e.touches[0].clientY}},{{passive:true}});
  document.addEventListener('touchend',e=>{{
    const dy=ty-e.changedTouches[0].clientY;
    if(Math.abs(dy)>30)go(current+(dy>0?1:-1));
  }},{{passive:true}});
  go(0);
}})();
</script>"""


def render(spec, template="cris", img_dir="images"):
    """
    結構化 JSON → HTML 字串。
    """
    theme = get_theme(template)
    tokens = build_tokens(theme)
    css = _build_css(tokens)
    slides = spec.get("slides", [])
    total = len(slides)
    font_link = tokens["fonts"]["google"]

    body_parts = []
    for idx, s in enumerate(slides):
        stagger = s.get("stagger", 0)
        inner = _render_slide_body(s, img_dir)

        # Section break 注入
        _section = s.get("_section")
        if _section and idx > 0:
            body_parts.append(
                f'<div class="section-break" data-stagger="0">\n'
                f'<div class="section-num">{idx+1:02d}</div>\n'
                f'<div class="section-title">{_section}</div>\n'
                f'</div>'
            )

        body_parts.append(
            f'<div class="slide" data-stagger="{stagger}">\n'
            f'  <div class="slide-inner">{inner}\n'
            f'  </div>\n'
            f'</div>'
        )

    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{spec.get('source','Presentation')}</title>
<meta name="description" content="{spec.get('source','')} — Power Squad">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family={font_link}&display=swap" media="print" onload="this.media='all';this.onload=null">
<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family={font_link}&display=swap"></noscript>
<style>
{css}
</style>
</head>
<body>
<div class="slides-container" id="slides" aria-label="{spec.get('source','Presentation')} — 投影片展示">
{"".join(body_parts)}
</div>
<div class="progress-track"><div class="progress-bar" id="progressBar"></div></div>
<nav class="nav-bar">
  <button class="nav-btn" id="prevBtn" disabled aria-label="上一頁">‹</button>
  <span class="nav-counter"><span class="current" id="curNum">1</span> / {total}</span>
  <button class="nav-btn" id="nextBtn" aria-label="下一頁">›</button>
</nav>
{_build_nav_js(total)}
</body>
</html>"""


# 向後相容別名
render_html = render
build_tokens_from_theme = build_tokens