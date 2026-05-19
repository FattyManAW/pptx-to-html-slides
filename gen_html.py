#!/usr/bin/env python3
"""Generate high-quality HTML slides from slide data JSON."""
import json, os

IMG_BASE = "images"

with open('html/slides_full.json') as f:
    slides = json.load(f)

def esc(text):
    return text.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')

def categorize(s):
    t = s.get('_type')
    if t:
        return t
    idx = s['idx']
    imgs = s['imgs']
    texts = s['texts']
    if idx == 0:
        return 'cover'
    if idx == 1:
        return 'toc'
    if idx == len(slides) - 1:
        return 'thanks'
    if imgs and not texts:
        return 'image'
    if imgs and texts:
        return 'mixed'
    return 'text'

def render_slide(s):
    idx = s['idx']
    t = categorize(s)
    texts = s['texts']
    imgs = s['imgs']
    
    if t == 'cover':
        return f'''
<section class="slide active" data-i="{idx}">
  <div class="slide-cover">
    <div class="cover-bg"></div>
    <div class="cover-content">
      <div class="cover-badge">IMPACTS APS</div>
      <h1 class="cover-title">{esc(texts[0]) if texts else ''}</h1>
      <p class="cover-subtitle">{esc(texts[1]) if len(texts)>1 else ''}</p>
      <div class="cover-line"></div>
    </div>
  </div>
</section>'''
    
    if t == 'toc':
        items = texts[1:] if texts else []
        items_html = ''
        for item in items:
            num, *rest = item.split(' ', 1)
            label = rest[0] if rest else item
            items_html += f'''
            <div class="toc-item">
              <span class="toc-num">{num}</span>
              <span class="toc-label">{esc(label)}</span>
            </div>'''
        return f'''
<section class="slide" data-i="{idx}">
  <div class="slide-inner toc-slide">
    <div class="toc-header">
      <span class="toc-tag">CONTENTS</span>
      <h2 class="toc-title">{esc(texts[0]) if texts else ''}</h2>
    </div>
    <div class="toc-grid">{items_html}</div>
  </div>
</section>'''
    
    if t == 'thanks':
        return f'''
<section class="slide" data-i="{idx}">
  <div class="slide-inner thanks-slide">
    <div class="thanks-bg"></div>
    <h1 class="thanks-title">Thank you！</h1>
    <p class="thanks-sub">大连润思科技</p>
  </div>
</section>'''
    
    if t == 'image' and not texts:
        img_html = f'<img src="{IMG_BASE}/{imgs[0]}" alt="" class="slide-full-img" loading="lazy">' if imgs else ''
        return f'''
<section class="slide" data-i="{idx}">
  <div class="slide-inner image-only">{img_html}</div>
</section>'''
    
    title = texts[0] if texts else ''
    body = texts[1:] if len(texts) > 1 else []
    
    if t == 'mixed' and imgs:
        # Detect challenge+benefit layout
        body_str = '\n'.join(body)
        
        # Build image HTML
        if len(imgs) == 1:
            img_html = f'<img src="{IMG_BASE}/{imgs[0]}" alt="" class="content-img" loading="lazy">'
        else:
            if len(imgs) <= 2:
                grid_class = 'img-grid-2'
            elif len(imgs) <= 4:
                grid_class = 'img-grid-3'
            else:
                grid_class = 'img-grid-many'
            img_tags = ''.join(f'<img src="{IMG_BASE}/{img}" alt="" class="content-img-grid" loading="lazy">' for img in imgs)
            img_html = f'<div class="{grid_class}">{img_tags}</div>'
        
        # Check for challenge/benefit structure
        challenge_keywords = ['挑战', '痛点', '压力']
        benefit_keywords = ['效益', '提升', '优化', '降低', '促进', '助力', '增强', '减少', '支持', '缩短', '改善', '提高']
        
        is_cb = False
        has_challenge = any(any(k in line for k in challenge_keywords) for line in body[:5])
        has_benefit = any(any(k in line for k in benefit_keywords) for line in body[5:]) if len(body) > 5 else False
        if has_challenge and has_benefit:
            is_cb = True
        
        if is_cb:
            challenge_items = []
            benefit_items = []
            in_benefit = False
            for line in body:
                if any(k in line for k in challenge_keywords):
                    in_benefit = False
                    challenge_items.append(line)
                elif any(k in line for k in benefit_keywords):
                    in_benefit = True
                    benefit_items.append(line)
                elif in_benefit:
                    benefit_items.append(line)
                else:
                    if len(challenge_items) > len(benefit_items):
                        benefit_items.append(line)
                    else:
                        challenge_items.append(line)
            
            def build_col(items):
                html = ''
                cur_h = ''
                cur_items = []
                for item in items:
                    if item.endswith(('：', ':')):
                        if cur_h or cur_items:
                            html += '<div class="section-block"><h4>' + esc(cur_h.rstrip('：:')) + '</h4><ul>'
                            for ci in cur_items:
                                html += '<li>' + esc(ci) + '</li>'
                            html += '</ul></div>'
                        cur_h = item.rstrip('：:')
                        cur_items = []
                    else:
                        cur_items.append(item)
                if cur_h or cur_items:
                    html += '<div class="section-block"><h4>' + esc(cur_h) + '</h4><ul>'
                    for ci in cur_items:
                        html += '<li>' + esc(ci) + '</li>'
                    html += '</ul></div>'
                return html
            
            left_html = build_col(challenge_items)
            right_html = build_col(benefit_items)
            
            return f'''
<section class="slide" data-i="{idx}">
  <div class="slide-inner">
    <h2 class="slide-title">{esc(title)}</h2>
    <div class="two-col-layout">
      <div class="col-challenge">{left_html}</div>
      <div class="col-benefit">{right_html}</div>
    </div>
    {f'<div class="slide-image-row">{img_html}</div>' if imgs else ''}
  </div>
</section>'''
        
        # General mixed layout
        content_html = build_content_html(body)
        return f'''
<section class="slide" data-i="{idx}">
  <div class="slide-inner mixed-slide">
    <h2 class="slide-title">{esc(title)}</h2>
    <div class="content-body">{content_html}</div>
    {f'<div class="slide-image-row">{img_html}</div>' if imgs else ''}
  </div>
</section>'''
    
    # Pure text slide
    content_html = build_content_html(body)
    return f'''
<section class="slide" data-i="{idx}">
  <div class="slide-inner text-slide">
    <h2 class="slide-title">{esc(title)}</h2>
    <div class="text-content">{content_html}</div>
  </div>
</section>'''

def build_content_html(body):
    html = ''
    current_section = None
    for line in body:
        if line.endswith(('：', ':')) or (len(line) < 25 and not line.startswith('  ')):
            if current_section:
                html += close_section(current_section)
            current_section = {'heading': line.rstrip('：:'), 'items': []}
        else:
            if current_section is None:
                current_section = {'heading': '', 'items': []}
            current_section['items'].append(line)
    if current_section:
        html += close_section(current_section)
    return html

def close_section(sec):
    h = ''
    if sec['heading']:
        h += '<h3 class="section-heading">' + esc(sec['heading']) + '</h3>'
    if sec['items']:
        if len(sec['items']) == 1:
            h += '<p class="section-text">' + esc(sec['items'][0]) + '</p>'
        else:
            h += '<ul class="section-list">'
            for item in sec['items']:
                h += '<li>' + esc(item) + '</li>'
            h += '</ul>'
    return h

# Generate all slides
slides_html = ''
for s in slides:
    slides_html += render_slide(s)

# Full HTML
html = f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>润思 IMPACTS APS 生态伙伴解决方案</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;600;700;900&family=Noto+Serif+SC:wght@600;700;900&display=swap" rel="stylesheet">
<script src="https://cdn.tailwindcss.com"></script>
<script>
tailwind.config={{"theme":{{"extend":{{"fontFamily":{{"sans":['"Noto Sans SC"',"sans-serif"],"serif":['"Noto Serif SC"","serif"]}},"colors":{{"primary":{{"50":"#eff6ff","100":"#dbeafe","200":"#bfdbfe","300":"#93c5fd","400":"#60a5fa","500":"#3b82f6","600":"#2563eb","700":"#1d4ed8","800":"#1e40af","900":"#1e3a8a"}},"dark":{{"900":"#0f172a","800":"#1e293b","700":"#334155"}},"accent":{{"DEFAULT":"#f59e0b","light":"#fbbf24"}}}}}}}}
</script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{height:100%;overflow:hidden}}
body{{font-family:'Noto Sans SC',sans-serif;background:#0a0a0f;color:#e2e8f0}}
.slides-container{{position:relative;width:100vw;height:100vh;overflow:hidden}}
.slide{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;opacity:0;visibility:hidden;transition:opacity 0.5s ease,transform 0.5s ease;transform:translateX(40px);padding:2rem}}
.slide.active{{opacity:1;visibility:visible;transform:translateX(0);z-index:10}}
.slide.prev{{transform:translateX(-40px)}}
/* Cover */
.slide-cover{{position:relative;width:100%;height:100%;display:flex;align-items:center;justify-content:center;overflow:hidden}}
.cover-bg{{position:absolute;inset:0;background:radial-gradient(ellipse at 20% 50%,rgba(59,130,246,0.15) 0%,transparent 50%),radial-gradient(ellipse at 80% 20%,rgba(245,158,11,0.1) 0%,transparent 50%),linear-gradient(135deg,#0f172a 0%,#1e293b 50%,#0f172a 100%)}}
.cover-bg::before{{content:'';position:absolute;inset:0;background:url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%233b82f6' fill-opacity='0.03'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")}}
.cover-content{{position:relative;text-align:center;max-width:900px;padding:3rem}}
.cover-badge{{display:inline-block;padding:0.4rem 1.5rem;background:linear-gradient(135deg,#3b82f6,#1d4ed8);color:white;font-size:0.85rem;font-weight:600;letter-spacing:0.15em;border-radius:9999px;margin-bottom:2rem;box-shadow:0 4px 20px rgba(59,130,246,0.4)}}
.cover-title{{font-family:'Noto Serif SC',serif;font-size:clamp(2rem,5vw,3.5rem);font-weight:900;line-height:1.2;margin-bottom:1.5rem;background:linear-gradient(135deg,#f8fafc,#94a3b8);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}}
.cover-subtitle{{font-size:clamp(1rem,2vw,1.35rem);color:#94a3b8;font-weight:300;letter-spacing:0.05em}}
.cover-line{{width:80px;height:3px;background:linear-gradient(90deg,#3b82f6,#f59e0b);margin:2rem auto 0;border-radius:2px}}
/* TOC */
.toc-slide{{width:100%;max-width:1100px}}
.toc-header{{margin-bottom:3rem}}
.toc-tag{{font-size:0.75rem;font-weight:700;letter-spacing:0.2em;color:#3b82f6;text-transform:uppercase}}
.toc-title{{font-family:'Noto Serif SC',serif;font-size:clamp(1.8rem,4vw,2.5rem);font-weight:700;margin-top:0.5rem;color:#f1f5f9}}
.toc-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem}}
.toc-item{{display:flex;align-items:center;gap:1rem;padding:1rem 1.5rem;background:rgba(30,41,59,0.5);border:1px solid rgba(59,130,246,0.15);border-radius:12px;transition:all 0.2s}}
.toc-item:hover{{background:rgba(59,130,246,0.1);border-color:rgba(59,130,246,0.4);transform:translateY(-2px)}}
.toc-num{{font-size:1.5rem;font-weight:900;color:#3b82f6;min-width:2rem}}
.toc-label{{font-size:1rem;font-weight:500;color:#cbd5e1}}
/* Slide inner */
.slide-inner{{width:100%;max-width:1200px;padding:2rem}}
.text-slide .slide-title,.mixed-slide .slide-title,.slide-inner:not(.toc-slide):not(.thanks-slide) h2.slide-title{{font-family:'Noto Serif SC',serif;font-size:clamp(1.3rem,3vw,2rem);font-weight:700;color:#f1f5f9;margin-bottom:1.5rem;padding-bottom:0.75rem;border-bottom:2px solid rgba(59,130,246,0.3)}}
.section-heading{{font-size:clamp(0.95rem,1.6vw,1.15rem);font-weight:700;color:#60a5fa;margin:1rem 0 0.4rem}}
.section-list{{list-style:none;padding:0;margin:0}}
.section-list li{{position:relative;padding:0.35rem 0 0.35rem 1.5rem;font-size:clamp(0.78rem,1.3vw,0.92rem);color:#cbd5e1;line-height:1.6}}
.section-list li::before{{content:'';position:absolute;left:0;top:0.85rem;width:6px;height:6px;background:#3b82f6;border-radius:50%;opacity:0.6}}
.section-list li+li{{border-top:1px solid rgba(255,255,255,0.04)}}
.section-text{{font-size:clamp(0.8rem,1.3vw,0.95rem);color:#cbd5e1;line-height:1.7;padding:0.3rem 0}}
/* Content images */
.content-img{{width:100%;max-height:40vh;object-fit:contain;border-radius:8px;border:1px solid rgba(255,255,255,0.08)}}
.img-grid-2,.img-grid-3,.img-grid-many{{display:grid;gap:0.5rem}}
.img-grid-2{{grid-template-columns:1fr 1fr}}.img-grid-3{{grid-template-columns:1fr 1fr 1fr}}.img-grid-many{{grid-template-columns:repeat(auto-fit,minmax(200px,1fr))}}
.content-img-grid{{width:100%;max-height:22vh;object-fit:contain;border-radius:6px;border:1px solid rgba(255,255,255,0.06)}}
/* Two col layout */
.two-col-layout{{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;margin-top:1rem}}
.col-challenge .section-block{{background:rgba(239,68,68,0.04);border:1px solid rgba(239,68,68,0.12);border-radius:10px;padding:0.8rem;margin-bottom:0.6rem}}
.col-challenge .section-block h4{{color:#f87171;font-size:0.85rem;font-weight:700;margin-bottom:0.4rem}}
.col-benefit .section-block{{background:rgba(34,197,94,0.04);border:1px solid rgba(34,197,94,0.12);border-radius:10px;padding:0.8rem;margin-bottom:0.6rem}}
.col-benefit .section-block h4{{color:#4ade80;font-size:0.85rem;font-weight:700;margin-bottom:0.4rem}}
.col-challenge .section-block ul,.col-benefit .section-block ul{{list-style:none;padding:0;margin:0}}
.col-challenge .section-block li,.col-benefit .section-block li{{font-size:clamp(0.68rem,1.1vw,0.82rem);color:#cbd5e1;padding:0.15rem 0 0.15rem 1rem;position:relative;line-height:1.45}}
.col-challenge .section-block li::before{{content:'▸';position:absolute;left:0;color:#f87171;font-size:0.65rem;top:0.2rem}}
.col-benefit .section-block li::before{{content:'✓';position:absolute;left:0;color:#4ade80;font-size:0.65rem;top:0.1rem}}
.slide-image-row{{margin-top:1rem}}
/* Image only */
.image-only{{width:100%;height:100%;display:flex;align-items:center;justify-content:center;padding:1rem}}
.slide-full-img{{max-width:100%;max-height:100%;object-fit:contain;border-radius:8px}}
/* Thanks */
.thanks-slide{{position:relative;width:100%;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center}}
.thanks-bg{{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 50%,rgba(59,130,246,0.1) 0%,transparent 60%),linear-gradient(135deg,#0f172a 0%,#1e293b 100%)}}
.thanks-title{{position:relative;font-family:'Noto Serif SC',serif;font-size:clamp(2.5rem,6vw,4rem);font-weight:900;background:linear-gradient(135deg,#3b82f6,#60a5fa,#f59e0b);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:1rem}}
.thanks-sub{{position:relative;font-size:1.2rem;color:#64748b;letter-spacing:0.1em}}
/* Nav */
.nav-bar{{position:fixed;bottom:0;left:0;right:0;z-index:100;display:flex;align-items:center;justify-content:center;gap:1.5rem;padding:1rem 2rem;background:linear-gradient(transparent,rgba(15,23,42,0.95));backdrop-filter:blur(10px)}}
.nav-btn{{width:44px;height:44px;border-radius:50%;border:1px solid rgba(255,255,255,0.15);background:rgba(30,41,59,0.6);color:#94a3b8;display:flex;align-items:center;justify-content:center;cursor:pointer;transition:all 0.2s;font-size:1.2rem}}
.nav-btn:hover{{background:rgba(59,130,246,0.2);border-color:#3b82f6;color:#60a5fa}}
.nav-btn:disabled{{opacity:0.3;cursor:not-allowed}}
.nav-counter{{font-size:0.85rem;color:#64748b;font-variant-numeric:tabular-nums;min-width:80px;text-align:center}}
.nav-counter .current{{color:#f1f5f9;font-weight:600}}
.progress-bar{{position:fixed;top:0;left:0;height:3px;background:linear-gradient(90deg,#3b82f6,#f59e0b);transition:width 0.3s ease;z-index:100}}
.keyboard-hint{{position:fixed;bottom:5rem;right:1.5rem;font-size:0.7rem;color:rgba(100,116,139,0.5);z-index:50}}
/* Responsive */
@media(max-width:768px){{.slide{{padding:1rem}}.slide-inner{{padding:1rem}}.two-col-layout{{grid-template-columns:1fr;gap:1rem}}.toc-grid{{grid-template-columns:1fr 1fr}}.nav-bar{{gap:0.75rem;padding:0.75rem 1rem}}}}
@media(max-width:480px){{.toc-grid{{grid-template-columns:1fr}}.img-grid-2,.img-grid-3{{grid-template-columns:1fr}}}}
::-webkit-scrollbar{{width:4px}}::-webkit-scrollbar-track{{background:transparent}}::-webkit-scrollbar-thumb{{background:rgba(59,130,246,0.3);border-radius:2px}}
</style>
</head>
<body>
<div class="progress-bar" id="progressBar"></div>
<div class="slides-container" id="slidesContainer">
{slides_html}
</div>
<nav class="nav-bar">
  <button class="nav-btn" id="prevBtn" onclick="goPrev()">&#8249;</button>
  <div class="nav-counter"><span class="current" id="currentPage">1</span> / <span id="totalPages">{len(slides)}</span></div>
  <button class="nav-btn" id="nextBtn" onclick="goNext()">&#8250;</button>
</nav>
<div class="keyboard-hint">&#8592; &#8594; 鍵盤翻頁</div>
<script>
const totalSlides={len(slides)};let current=0;
function goToSlide(n){{if(n<0||n>=totalSlides)return;const slides=document.querySelectorAll('.slide');slides[current].classList.remove('active');slides[current].classList.add('prev');current=n;slides.forEach((s,i)={{s.classList.remove('active','prev');if(i===current)s.classList.add('active');else if(i<current)s.classList.add('prev')}});document.getElementById('currentPage').textContent=current+1;document.getElementById('progressBar').style.width=((current+1)/totalSlides*100)+'%';document.getElementById('prevBtn').disabled=current===0;document.getElementById('nextBtn').disabled=current===totalSlides-1}}
function goNext(){{goToSlide(current+1)}}function goPrev(){{goToSlide(current-1)}}
document.addEventListener('keydown',(e) =>{{if(e.key==='ArrowRight'||e.key===' '||e.key==='PageDown')goNext();if(e.key==='ArrowLeft'||e.key==='PageUp')goPrev();if(e.key==='Home')goToSlide(0);if(e.key==='End')goToSlide(totalSlides-1)}});
let touchStartX=0;document.getElementById('slidesContainer').addEventListener('touchstart',(e) => {{touchStartX=e.changedTouches[0].screenX}});document.getElementById('slidesContainer').addEventListener('touchend',(e) => {{const diff=touchStartX-e.changedTouches[0].screenX;if(Math.abs(diff)>50){{if(diff>0)goNext();else goPrev()}}}});
document.getElementById('prevBtn').disabled=true;document.getElementById('progressBar').style.width=(1/totalSlides*100)+'%';
</script>
</body>
</html>'''

out_path = 'html/runs-impacts-aps-partner-v2.html'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)

size_kb = os.path.getsize(out_path) // 1024
print(f"Generated: {out_path} ({size_kb} KB)")
print(f"Total slides: {len(slides)}")
