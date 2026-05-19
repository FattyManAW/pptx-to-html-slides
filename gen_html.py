#!/usr/bin/env python3
"""
润思IMPACTS APS 投影片 v2 — 高品質企業級設計
設計靈感：Apple 產品頁 + Linear + Stripe + Awwwards
"""
import json, os

IMG_BASE = "images"

with open('html/slides_full.json') as f:
    slides = json.load(f)

def esc(text):
    return text.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;').replace("'","&#39;")

def categorize(s):
    idx = s['idx']
    imgs = s['imgs']
    texts = s['texts']
    if idx == 0: return 'cover'
    if idx == 1: return 'toc'
    if idx == len(slides) - 1: return 'thanks'
    if imgs and not texts: return 'image'
    if imgs and texts: return 'mixed'
    return 'text'

def build_content(body_lines):
    """Build card-based section content."""
    html, cur_h, cur_items = '', '', []
    for line in body_lines:
        is_heading = line.endswith(('：',':')) or (len(line) < 25 and not line.startswith('  '))
        if is_heading:
            if cur_items:
                html += '<div class="sc"><h3>' + esc(cur_h) + '</h3><ul>'
                for x in cur_items: html += '<li>' + esc(x) + '</li>'
                html += '</ul></div>'
            cur_h, cur_items = line.rstrip('：:'), []
        else:
            cur_items.append(line)
    if cur_items:
        html += '<div class="sc"><h3>' + esc(cur_h) + '</h3><ul>'
        for x in cur_items: html += '<li>' + esc(x) + '</li>'
        html += '</ul></div>'
    if not html:
        for line in body_lines: html += '<p class="bl">' + esc(line) + '</p>'
    return html

def img_tag(src, cls='ci', lazy=True):
    lz = ' loading="lazy"' if lazy else ''
    return '<img src="' + src + '" alt="" class="' + cls + '"' + lz + '>'

def render_slide(s):
    idx = s['idx']
    t = categorize(s)
    texts = s['texts']
    imgs = s['imgs']
    I = IMG_BASE

    if t == 'cover':
        return (
            '<section class="slide active" data-i="' + str(idx) + '">'
            '<div class="cover-bg"><div class="cover-glow"></div><div class="cover-grid"></div></div>'
            '<div class="cover-inner">'
            '<div class="cover-tag">IMPACTS APS</div>'
            '<h1 class="cover-title">' + esc(texts[0]) + '</h1>'
            '<p class="cover-sub">' + esc(texts[1]) + '</p>'
            '<div class="cover-rule"></div>'
            '<div class="cover-meta"><span>大连润思科技</span><span class="sep">|</span><span>制造行业及智能制造解决方案商</span></div>'
            '</div></section>'
        )

    if t == 'toc':
        items_html = ''
        for item in (texts[1:] if texts else []):
            num, *rest = item.split(' ', 1)
            label = rest[0] if rest else item
            items_html += (
                '<div class="toc-card">'
                '<span class="toc-n">' + num + '</span>'
                '<span class="toc-l">' + esc(label) + '</span>'
                '</div>'
            )
        return (
            '<section class="slide" data-i="' + str(idx) + '">'
            '<div class="toc-inner"><div class="toc-top">'
            '<span class="toc-label">CONTENTS</span>'
            '<h2 class="toc-title">' + esc(texts[0]) + '</h2>'
            '</div><div class="toc-grid">' + items_html + '</div></div></section>'
        )

    if t == 'thanks':
        return (
            '<section class="slide" data-i="61">'
            '<div class="thanks-bg"><div class="thanks-orb"></div></div>'
            '<div class="thanks-inner">'
            '<div class="thanks-eyebrow">Thank you</div>'
            '<h1 class="thanks-title">Thank you！</h1>'
            '<div class="thanks-rule"></div>'
            '<p class="thanks-sub">大连润思科技</p>'
            '</div></section>'
        )

    if t == 'image' and not texts:
        img_html = img_tag(I + '/' + imgs[0], 'fi') if imgs else ''
        return '<section class="slide" data-i="' + str(idx) + '"><div class="slide-center">' + img_html + '</div></section>'

    title = texts[0] if texts else ''
    body = texts[1:] if len(texts) > 1 else []

    # Build image HTML
    if len(imgs) == 1:
        img_html = img_tag(I + '/' + imgs[0], 'ci')
    elif len(imgs) <= 2:
        img_html = '<div class="ig2">' + ''.join(img_tag(I + '/' + img, 'cig') for img in imgs) + '</div>'
    elif len(imgs) <= 4:
        img_html = '<div class="ig3">' + ''.join(img_tag(I + '/' + img, 'cig') for img in imgs) + '</div>'
    else:
        img_html = '<div class="igm">' + ''.join(img_tag(I + '/' + img, 'cig') for img in imgs) + '</div>'

    content_html = build_content(body)

    if t == 'mixed' and imgs:
        ck = ['挑战','痛点','压力','困难','问题','瓶颈']
        bk = ['效益','提升','优化','降低','促进','助力','增强','减少','支持','缩短','改善','提高','强化','推动']
        is_cb = (any(k in l for k in ck for l in body[:5]) and
                 any(k in l for k in bk for l in body[5:])) if len(body) > 5 else False

        if is_cb:
            ci, bi, ib = [], [], False
            for line in body:
                if any(k in line for k in ck): ib = False; ci.append(line)
                elif any(k in line for k in bk): ib = True; bi.append(line)
                elif ib: bi.append(line)
                else:
                    if len(ci) > len(bi): bi.append(line)
                    else: ci.append(line)
            def col(items):
                h, c = '', []
                for item in items:
                    if item.endswith(('：',':')):
                        if c:
                            h += '<div class="cb"><h4>' + esc(c[0].rstrip('：:')) + '</h4><ul>'
                            for x in c[1:]: h += '<li>' + esc(x) + '</li>'
                            h += '</ul></div>'
                        c = [item.rstrip('：:')]
                    else: c.append(item)
                if c:
                    h += '<div class="cb"><h4>' + esc(c[0]) + '</h4><ul>'
                    for x in c[1:]: h += '<li>' + esc(x) + '</li>'
                    h += '</ul></div>'
                return h
            return (
                '<section class="slide" data-i="' + str(idx) + '"><div class="slide-inner">'
                '<div class="slide-header"><span class="slide-num">' + str(idx + 1).zfill(2) + '</span>'
                '<h2 class="slide-title">' + esc(title) + '</h2></div>'
                '<div class="twocol">'
                '<div class="col-left">' + col(ci) + '</div>'
                '<div class="col-right">' + col(bi) + '</div>'
                '</div>'
                '<div class="slide-img-row">' + img_html + '</div></div></section>'
            )

        return (
            '<section class="slide" data-i="' + str(idx) + '"><div class="slide-inner">'
            '<div class="slide-header"><span class="slide-num">' + str(idx + 1).zfill(2) + '</span>'
            '<h2 class="slide-title">' + esc(title) + '</h2></div>'
            '<div class="content-body">' + content_html + '</div>'
            '<div class="slide-img-row">' + img_html + '</div></div></section>'
        )

    return (
        '<section class="slide" data-i="' + str(idx) + '"><div class="slide-inner">'
        '<div class="slide-header"><span class="slide-num">' + str(idx + 1).zfill(2) + '</span>'
        '<h2 class="slide-title">' + esc(title) + '</h2></div>'
        '<div class="content-body">' + content_html + '</div></div></section>'
    )

# =================== GENERATE SLIDES ===================
slides_html = ''.join(render_slide(s) for s in slides)
total = len(slides)

# =================== FULL HTML ===================
html = '''<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>润思 IMPACTS APS 生态伙伴解决方案</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@600;700;800;900&family=Noto+Sans+SC:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.tailwindcss.com"></script>
<script>tailwind.config={"theme":{"extend":{"fontFamily":{"display":["Playfair Display","serif"],"body":["Inter","Noto Sans SC","sans-serif"],"sc":["Noto Sans SC","sans-serif"]}}}}</script>
<style>
/* ================================================================
   润思 IMPACTS APS — 高品質投影片 v2
   設計：Apple + Linear + Stripe + Awwwards 啟發
   62 張 | 深色企業級 | 模組化 CSS | 三斷點響應式
   ================================================================ */

/* ===== [01] RESET & BASE ===== */
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%;overflow:hidden;-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale}
body{font-family:'Inter','Noto Sans SC',sans-serif;background:#050508;color:#e2e8f0;line-height:1.6}

/* ===== [02] SLIDE ENGINE ===== */
.slides-container{position:relative;width:100vw;height:100vh;overflow:hidden;background:#050508}
.slide{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;opacity:0;visibility:hidden;transition:opacity .6s cubic-bezier(.4,0,.2,1),transform .6s cubic-bezier(.4,0,.2,1);transform:scale(.97) translateY(8px);padding:2rem;will-change:opacity,transform}
.slide.active{opacity:1;visibility:visible;transform:scale(1) translateY(0);z-index:10}
.slide.prev{opacity:0;transform:scale(1.02) translateY(-8px)}

/* ===== [03] PROGRESS BAR ===== */
.progress-track{position:fixed;top:0;left:0;right:0;height:2px;background:rgba(255,255,255,.03);z-index:300}
.progress-bar{position:fixed;top:0;left:0;height:2px;background:linear-gradient(90deg,#6366f1,#8b5cf6,#ec4899,#f59e0b);transition:width .4s cubic-bezier(.4,0,.2,1);z-index:301;box-shadow:0 0 12px rgba(139,92,246,.6)}

/* ===== [04] NAVIGATION ===== */
.nav-bar{position:fixed;bottom:0;left:0;right:0;z-index:300;display:flex;align-items:center;justify-content:center;gap:1rem;padding:1rem 2.5rem;background:linear-gradient(transparent,rgba(5,5,8,.92));backdrop-filter:blur(20px) saturate(1.2);border-top:1px solid rgba(255,255,255,.04)}
.nav-btn{width:42px;height:42px;border-radius:50%;border:1px solid rgba(255,255,255,.08);background:rgba(255,255,255,.04);color:#94a3b8;display:flex;align-items:center;justify-content:center;cursor:pointer;transition:all .25s cubic-bezier(.4,0,.2,1);font-size:1.1rem;backdrop-filter:blur(10px)}
.nav-btn:hover{background:rgba(99,102,241,.15);border-color:rgba(99,102,241,.4);color:#a5b4fc;transform:scale(1.05)}
.nav-btn:disabled{opacity:.2;cursor:default;transform:none}
.nav-btn:disabled:hover{background:rgba(255,255,255,.04);border-color:rgba(255,255,255,.08);color:#94a3b8}
.nav-counter{font-size:.8rem;color:#475569;font-variant-numeric:tabular-nums;min-width:70px;text-align:center;letter-spacing:.05em}
.nav-counter .current{color:#e2e8f0;font-weight:600}
.fs-btn{width:34px;height:34px;border-radius:8px;border:1px solid rgba(255,255,255,.08);background:rgba(255,255,255,.04);color:#64748b;display:flex;align-items:center;justify-content:center;cursor:pointer;transition:all .25s;font-size:.8rem;backdrop-filter:blur(10px);margin-left:auto}
.fs-btn:hover{background:rgba(99,102,241,.15);border-color:rgba(99,102,241,.4);color:#a5b4fc}

/* ===== [05] KEYBOARD HINT ===== */
.kbh{position:fixed;bottom:5.5rem;right:1.5rem;font-size:.65rem;color:rgba(71,85,105,.5);z-index:150;letter-spacing:.03em;user-select:none}

/* ================================================================
   [10] COVER SLIDE
   ================================================================ */
.cover-bg{position:absolute;inset:0;overflow:hidden;
  background:
    radial-gradient(ellipse 80% 60% at 15% 40%,rgba(99,102,241,.12) 0%,transparent 60%),
    radial-gradient(ellipse 60% 80% at 85% 20%,rgba(236,72,153,.08) 0%,transparent 55%),
    radial-gradient(ellipse 50% 50% at 50% 100%,rgba(245,158,11,.05) 0%,transparent 50%),
    linear-gradient(160deg,#0a0a12 0%,#0f0f1a 40%,#0a0a12 100%)}
.cover-glow{position:absolute;width:600px;height:600px;border-radius:50%;background:radial-gradient(circle,rgba(99,102,241,.08) 0%,transparent 70%);top:10%;left:60%;animation:float 8s ease-in-out infinite}
.cover-grid{position:absolute;inset:0;
  background-image:
    linear-gradient(rgba(99,102,241,.03) 1px,transparent 1px),
    linear-gradient(90deg,rgba(99,102,241,.03) 1px,transparent 1px);
  background-size:60px 60px}
@keyframes float{0%,100%{transform:translateY(0) rotate(0deg)}50%{transform:translateY(-20px) rotate(5deg)}}

.cover-inner{position:relative;text-align:center;max-width:900px;padding:4rem;animation:fadeInUp .8s ease-out}
@keyframes fadeInUp{from{opacity:0;transform:translateY(30px)}to{opacity:1;transform:translateY(0)}}

.cover-tag{display:inline-block;padding:.35rem 1.2rem;font-size:.7rem;font-weight:700;letter-spacing:.25em;text-transform:uppercase;color:#a5b4fc;border:1px solid rgba(99,102,241,.3);border-radius:9999px;margin-bottom:2.5rem;background:rgba(99,102,241,.06)}
.cover-title{font-family:'Playfair Display','Noto Serif SC',serif;font-size:clamp(2.2rem,5.5vw,3.8rem);font-weight:800;line-height:1.15;margin-bottom:1.5rem;
  background:linear-gradient(135deg,#f8fafc 0%,#e2e8f0 40%,#94a3b8 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.cover-sub{font-size:clamp(.95rem,1.8vw,1.25rem);color:#64748b;font-weight:300;letter-spacing:.08em;line-height:1.6}
.cover-rule{width:60px;height:2px;background:linear-gradient(90deg,#6366f1,#ec4899,#f59e0b);margin:2.5rem auto;border-radius:1px}
.cover-meta{font-size:.8rem;color:#475569;letter-spacing:.1em;display:flex;align-items:center;justify-content:center;gap:.75rem}
.cover-meta .sep{color:#334155}

/* ================================================================
   [20] TABLE OF CONTENTS
   ================================================================ */
.toc-inner{width:100%;max-width:1100px}
.toc-top{margin-bottom:3rem}
.toc-label{font-size:.65rem;font-weight:700;letter-spacing:.25em;color:#6366f1;text-transform:uppercase}
.toc-title{font-family:'Playfair Display','Noto Serif SC',serif;font-size:clamp(1.6rem,3.5vw,2.4rem);font-weight:700;margin-top:.4rem;color:#f1f5f9}
.toc-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:.75rem}
.toc-card{display:flex;align-items:center;gap:1rem;padding:.9rem 1.2rem;background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.06);border-radius:14px;transition:all .3s cubic-bezier(.4,0,.2,1);cursor:default}
.toc-card:hover{background:rgba(99,102,241,.06);border-color:rgba(99,102,241,.2);transform:translateY(-3px);box-shadow:0 8px 30px rgba(0,0,0,.3)}
.toc-n{font-size:1.3rem;font-weight:800;background:linear-gradient(135deg,#6366f1,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;min-width:1.8rem}
.toc-l{font-size:.9rem;font-weight:500;color:#94a3b8}

/* ================================================================
   [30] SLIDE INNER LAYOUT
   ================================================================ */
.slide-inner{width:100%;max-width:1200px;padding:2.5rem 2rem;animation:fadeIn .5s ease-out}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
.slide-header{display:flex;align-items:baseline;gap:1rem;margin-bottom:2rem}
.slide-num{font-size:.7rem;font-weight:600;color:#6366f1;letter-spacing:.1em;opacity:.6}
.slide-title{font-family:'Playfair Display','Noto Serif SC',serif;font-size:clamp(1.3rem,2.8vw,1.9rem);font-weight:700;color:#f1f5f9;line-height:1.3;padding-bottom:.6rem;border-bottom:1px solid rgba(99,102,241,.15)}

/* ===== Section Block (card) ===== */
.sc{background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.05);border-radius:12px;padding:1.1rem 1.3rem;margin-bottom:.6rem;transition:border-color .2s}
.sc:hover{border-color:rgba(99,102,241,.15)}
.sc h3{font-size:clamp(.85rem,1.4vw,1rem);font-weight:700;color:#818cf8;margin-bottom:.4rem;display:flex;align-items:center;gap:.4rem}
.sc h3::before{content:'';display:inline-block;width:3px;height:.8em;background:linear-gradient(180deg,#6366f1,#8b5cf6);border-radius:2px;flex-shrink:0}
.sc ul{list-style:none;padding:0}
.sc li{position:relative;padding:.3rem 0 .3rem 1.3rem;font-size:clamp(.75rem,1.2vw,.88rem);color:#94a3b8;line-height:1.55;transition:color .15s}
.sc li:hover{color:#cbd5e1}
.sc li::before{content:'';position:absolute;left:0;top:.7rem;width:5px;height:5px;background:#6366f1;border-radius:50%;opacity:.4}
.sc li+li{border-top:1px solid rgba(255,255,255,.03)}
.bl{font-size:clamp(.8rem,1.3vw,.95rem);color:#94a3b8;line-height:1.7;padding:.3rem 0;border-bottom:1px solid rgba(255,255,255,.03)}

/* ===== Content Images ===== */
.ci{width:100%;max-height:42vh;object-fit:contain;border-radius:10px;border:1px solid rgba(255,255,255,.06);box-shadow:0 4px 30px rgba(0,0,0,.3)}
.cig{width:100%;max-height:20vh;object-fit:contain;border-radius:8px;border:1px solid rgba(255,255,255,.04);box-shadow:0 2px 15px rgba(0,0,0,.2)}
.fi{max-width:100%;max-height:100%;object-fit:contain;border-radius:10px;box-shadow:0 8px 40px rgba(0,0,0,.4)}
.ig2{display:grid;grid-template-columns:1fr 1fr;gap:.6rem}
.ig3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:.6rem}
.igm{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:.6rem}

/* ================================================================
   [40] TWO-COL: CHALLENGE vs BENEFIT
   ================================================================ */
.twocol{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;margin-top:.5rem}
.col-left .cb{background:rgba(239,68,68,.03);border:1px solid rgba(239,68,68,.08);border-radius:12px;padding:.8rem 1rem;margin-bottom:.5rem}
.col-left .cb h4{color:#f87171;font-size:.82rem;font-weight:700;margin-bottom:.35rem;display:flex;align-items:center;gap:.3rem}
.col-left .cb h4::before{content:'';width:8px;height:8px;border-radius:50%;background:#ef4444;flex-shrink:0}
.col-right .cb{background:rgba(34,197,94,.03);border:1px solid rgba(34,197,94,.08);border-radius:12px;padding:.8rem 1rem;margin-bottom:.5rem}
.col-right .cb h4{color:#4ade80;font-size:.82rem;font-weight:700;margin-bottom:.35rem;display:flex;align-items:center;gap:.3rem}
.col-right .cb h4::before{content:'';width:8px;height:8px;border-radius:50%;background:#22c55e;flex-shrink:0}
.col-left .cb ul,.col-right .cb ul{list-style:none;padding:0;margin:0}
.col-left .cb li,.col-right .cb li{font-size:clamp(.68rem,1.05vw,.8rem);color:#94a3b8;padding:.12rem 0 .12rem 1.1rem;position:relative;line-height:1.4}
.col-left .cb li::before{content:'›';position:absolute;left:0;color:#f87171;font-size:.7rem;top:.1rem}
.col-right .cb li::before{content:'✓';position:absolute;left:0;color:#4ade80;font-size:.65rem;top:.05rem}
.slide-img-row{margin-top:1.2rem}

/* ================================================================
   [50] FULL IMAGE SLIDE
   ================================================================ */
.slide-center{width:100%;height:100%;display:flex;align-items:center;justify-content:center;padding:1.5rem}

/* ================================================================
   [60] THANKS SLIDE
   ================================================================ */
.thanks-bg{position:absolute;inset:0;overflow:hidden;
  background:
    radial-gradient(ellipse 70% 50% at 30% 60%,rgba(99,102,241,.08) 0%,transparent 60%),
    radial-gradient(ellipse 60% 40% at 75% 30%,rgba(236,72,153,.06) 0%,transparent 50%),
    linear-gradient(160deg,#0a0a12 0%,#0f0f1a 100%)}
.thanks-orb{position:absolute;width:500px;height:500px;border-radius:50%;background:radial-gradient(circle,rgba(139,92,246,.06) 0%,transparent 70%);top:15%;right:10%;animation:float 10s ease-in-out infinite reverse}
.thanks-inner{position:relative;text-align:center;padding:4rem;animation:fadeInUp .8s ease-out}
.thanks-eyebrow{font-size:.75rem;font-weight:700;letter-spacing:.3em;text-transform:uppercase;color:#818cf8;margin-bottom:1.5rem}
.thanks-title{font-family:'Playfair Display','Noto Serif SC',serif;font-size:clamp(2.5rem,6vw,4.5rem);font-weight:800;
  background:linear-gradient(135deg,#e2e8f0,#94a3b8,#64748b);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:1.5rem}
.thanks-rule{width:40px;height:2px;background:linear-gradient(90deg,#6366f1,#ec4899);margin:0 auto 1.5rem;border-radius:1px}
.thanks-sub{font-size:1rem;color:#475569;letter-spacing:.15em}

/* ================================================================
   [70] CONTENT BODY
   ================================================================ */
.content-body{display:flex;flex-direction:column;gap:.3rem}

/* ================================================================
   [80] RESPONSIVE — 3 BREAKPOINTS
   ================================================================ */

/* Tablet Landscape: 1024px */
@media(max-width:1024px){
  .slide{padding:1.5rem}
  .slide-inner{padding:2rem 1.5rem;max-width:960px}
  .cover-inner{padding:3rem}
  .cover-title{font-size:clamp(1.8rem,4.5vw,2.6rem)}
  .toc-grid{grid-template-columns:repeat(3,1fr)}
  .ci{max-height:35vh}
  .cig{max-height:18vh}
  .twocol{gap:1rem}
}

/* Tablet / Mobile: 768px */
@media(max-width:768px){
  .slide{padding:1rem}
  .slide-inner{padding:1.5rem 1rem}
  .cover-inner{padding:2rem}
  .cover-title{font-size:clamp(1.6rem,5vw,2.2rem)}
  .twocol{grid-template-columns:1fr}
  .toc-grid{grid-template-columns:repeat(2,1fr)}
  .nav-bar{padding:.75rem 1rem;gap:.75rem}
  .toc-card{padding:.75rem 1rem}
  .kbh{display:none}
  .ig2,.ig3{grid-template-columns:1fr}
}

/* Small Mobile: 480px */
@media(max-width:480px){
  .slide{padding:.75rem}
  .slide-inner{padding:1rem .75rem}
  .cover-inner{padding:1.5rem 1rem}
  .cover-title{font-size:1.5rem}
  .toc-grid{grid-template-columns:1fr}
  .toc-card{padding:.65rem .8rem}
  .nav-btn{width:36px;height:36px;font-size:.95rem}
  .nav-bar{padding:.6rem .75rem}
  .igm{grid-template-columns:1fr 1fr}
}

/* ===== Utilities ===== */
::-webkit-scrollbar{width:3px}::-webkit-scrollbar-thumb{background:rgba(99,102,241,.2);border-radius:2px}
</style>
</head>
<body>
<div class="progress-track"></div>
<div class="progress-bar" id="progressBar"></div>
<div class="slides-container" id="slidesContainer">
''' + slides_html + '''
</div>
<nav class="nav-bar">
  <button class="nav-btn" id="prevBtn" onclick="goPrev()" aria-label="上一張">&#8249;</button>
  <div class="nav-counter"><span class="current" id="currentPage">1</span> <span style="color:#334155">/</span> <span id="totalPages">''' + str(total) + '''</span></div>
  <button class="nav-btn" id="nextBtn" onclick="goNext()" aria-label="下一張">&#8250;</button>
  <button class="fs-btn" id="fsBtn" onclick="toggleFS()" title="全螢幕">&#x26F6;</button>
</nav>
<div class="kbh">&#8592; &#8594; 翻頁 &nbsp;|&nbsp; F 全螢幕</div>
<script>
var totalSlides=''' + str(total) + ''';var current=0;
function goToSlide(n){if(n<0||n>=totalSlides)return;var slides=document.querySelectorAll('.slide');slides[current].classList.remove('active');slides[current].classList.add('prev');current=n;slides.forEach(function(s,i){s.classList.remove('active','prev');if(i===current)s.classList.add('active');else if(i<current)s.classList.add('prev')});document.getElementById('currentPage').textContent=current+1;document.getElementById('progressBar').style.width=((current+1)/totalSlides*100)+'%';document.getElementById('prevBtn').disabled=current===0;document.getElementById('nextBtn').disabled=current===totalSlides-1}
function goNext(){goToSlide(current+1)}function goPrev(){goToSlide(current-1)}
function toggleFS(){if(!document.fullscreenElement){document.documentElement.requestFullscreen().catch(function(){})}else{document.exitFullscreen()}}
document.addEventListener('keydown',function(e){if(e.key==='ArrowRight'||e.key===' '||e.key==='PageDown')goNext();if(e.key==='ArrowLeft'||e.key==='PageUp')goPrev();if(e.key==='Home')goToSlide(0);if(e.key==='End')goToSlide(totalSlides-1);if(e.key==='f'||e.key==='F')toggleFS()});
var ts=0;document.getElementById('slidesContainer').addEventListener('touchstart',function(e){ts=e.changedTouches[0].screenX});document.getElementById('slidesContainer').addEventListener('touchend',function(e){var d=ts-e.changedTouches[0].screenX;if(Math.abs(d)>50){if(d>0)goNext();else goPrev()}});
document.getElementById('prevBtn').disabled=true;document.getElementById('progressBar').style.width=(1/totalSlides*100)+'%';
</script>
</body>
</html>'''

out_path = 'html/runs-impacts-aps-partner-v2.html'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)
size_kb = os.path.getsize(out_path) // 1024
print("Generated: %s (%d KB), %d slides" % (out_path, size_kb, total))
