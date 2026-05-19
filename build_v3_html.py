#!/usr/bin/env python3
"""生成润思IMPACTS v3 HTML — 嚴格對標六大原則"""
import json

with open('/Users/henry/Documents/任務檔案/投影片轉換/slides_v3.json') as f:
    slides = json.load(f)

IMG = "html/images"

def esc(t):
    return t.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')

def render_section(s):
    n = esc(s['n'])
    t = esc(s['t'])
    return f'''<div class="section-break" data-stagger="0">
  <div class="section-inner">
    <span class="section-num">0{n}</span>
    <h2 class="section-title">{t}</h2>
  </div>
</div>'''

def render_thanks(s):
    t = esc(s['t'])
    st = esc(s.get('st',''))
    return f'''<div class="slide" data-stagger="0">
  <div class="slide-inner thanks-inner">
    <p class="thanks-eyebrow">Thank You</p>
    <h1 class="thanks-title">{t}</h1>
    <div class="thanks-rule"></div>
    <p class="thanks-sub">{st}</p>
  </div>
</div>'''

def render_cover(s):
    t = esc(s['t'])
    st = esc(s['st'])
    return f'''<div class="slide cover-slide" data-stagger="0">
  <div class="cover-bg">
    <div class="cover-orb1"></div>
    <div class="cover-orb2"></div>
    <div class="cover-orb3"></div>
    <div class="cover-grid"></div>
    <div class="cover-vignette"></div>
  </div>
  <div class="cover-inner">
    <span class="cover-tag">智能制造解决方案</span>
    <h1 class="cover-title">{t}</h1>
    <p class="cover-sub">{st}</p>
    <div class="cover-rule"></div>
    <p class="cover-meta"><span class="sep">✦</span> 离散型制造行业 <span class="sep">✦</span> APS智慧排程 <span class="sep">✦</span> AI Agent</p>
  </div>
</div>'''

def render_normal(s):
    t = esc(s.get('t',''))
    st = esc(s.get('st',''))
    h = esc(s.get('h',''))
    b = esc(s.get('b',''))
    imgs = s.get('imgs', [])
    items = s.get('items', [])

    # Build content blocks
    blocks = []

    # Title row
    blocks.append(f'<div class="slide-header"><span class="slide-num">0{s["num"]:02d}</span><h2 class="slide-title">{t}</h2></div>')

    # Subtitle
    if st:
        blocks.append(f'<p class="slide-sub">{st}</p>')

    # Headline
    if h:
        blocks.append(f'<h3 class="slide-headline">{h}</h3>')

    # Body text
    if b:
        blocks.append(f'<p class="slide-body">{b}</p>')

    # Items (2-col cards)
    if items:
        blocks.append('<div class="items-grid">')
        for it in items:
            ih = esc(it.get('h',''))
            ils = it.get('ls', [])
            items_html = ''.join(f'<li>{esc(x)}</li>' for x in ils)
            blocks.append(f'<div class="item-card"><h4>{ih}</h4><ul>{items_html}</ul></div>')
        blocks.append('</div>')

    # Two-col challenge/benefit
    if 'twocol' in s:
        tc = s['twocol']
        left_h = esc(tc[0].get('h','')) if tc else ''
        right_h = esc(tc[1].get('h','')) if len(tc)>1 else ''
        left_ls = tc[0].get('ls',[]) if tc else []
        right_ls = tc[1].get('ls',[]) if len(tc)>1 else []
        left_items = ''.join(f'<li>{esc(x)}</li>' for x in left_ls)
        right_items = ''.join(f'<li>{esc(x)}</li>' for x in right_ls)
        blocks.append(f'<div class="twocol"><div class="col-left"><div class="cb"><h4>{left_h}</h4><ul>{left_items}</ul></div></div><div class="col-right"><div class="cb"><h4>{right_h}</h4><ul>{right_items}</ul></div></div></div>')

    # Images
    if imgs:
        if len(imgs) == 1:
            blocks.append(f'<div class="slide-img-row"><img class="ci" src="{IMG}/{imgs[0]}" alt="{t}"></div>')
        elif len(imgs) == 2:
            blocks.append(f'<div class="ig2"><img class="ci" src="{IMG}/{imgs[0]}" alt="{t}"><img class="ci" src="{IMG}/{imgs[1]}" alt="{t}"></div>')
        else:
            imgs_html = ''.join(f'<img class="cig" src="{IMG}/{img}" alt="{t}">' for img in imgs)
            blocks.append(f'<div class="igm">{imgs_html}</div>')

    inner = '\n'.join(blocks)
    stagger = s.get('stagger', 0)
    return f'''<div class="slide" data-stagger="{stagger}">
  <div class="slide-inner">
    {inner}
  </div>
</div>'''

# Build HTML body
body_parts = []
num = 0
for s in slides:
    if s.get('s') == 'cover':
        body_parts.append(render_cover(s))
        continue
    if s.get('s') == 'section':
        body_parts.append(render_section(s))
        continue
    if s.get('s') == 'thanks':
        body_parts.append(render_thanks(s))
        continue
    num += 1
    s['num'] = num
    body_parts.append(render_normal(s))

body = '\n\n'.join(body_parts)

html = f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>润思IMPACTS APS 生态伙伴解决方案 — v3</title>
<meta name="description" content="润思IMPACTS APS智慧排程系统 — 离散型制造行业智能制造解决方案">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@700;800;900&family=Noto+Sans+SC:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.tailwindcss.com"></script>
<script>tailwind.config={{"theme":{{"extend":{{"fontFamily":{{"display":["Playfair Display","serif"],"body":["Inter","Noto Sans SC","sans-serif"]}}}}}}}}</script>
<style>
/* ================================================================
   润思IMPACTS APS — v3 Design System
   六大原則：一畫面一訊息 · Timing 階梯 · 留白即語言 · 約束創造品質 · 材質層次 · 字體對比
   ================================================================ */

/* ===== [01] DESIGN TOKENS ===== */
:root {{
  --ink-50:  #f8fafc;  --ink-100: #f1f5f9;
  --ink-200: #e2e8f0;  --ink-300: #cbd5e1;
  --ink-400: #94a3b8;  --ink-500: #64748b;
  --ink-600: #475569;  --ink-700: #334155;
  --ink-800: #1e293b;  --ink-900: #0f172a;
  --ink-950: #06080d;
  --accent: #6366f1;   --accent-mid: #818cf8;
  --surface: rgba(255,255,255,.03);
  --surface-h: rgba(255,255,255,.06);
  --border: rgba(255,255,255,.06);
  --border-a: rgba(99,102,241,.2);
  --blur: blur(24px);
  --shadow: 0 8px 40px rgba(0,0,0,.35);
  --font-display: 'Playfair Display',serif;
  --font-body: 'Inter','Noto Sans SC',sans-serif;
  --t-fast: 0.2s;   --t-base: 0.35s;   --t-slow: 0.55s;
}}

/* ===== [02] RESET & BASE ===== */
*,*::before,*::after{{margin:0;padding:0;box-sizing:border-box}}
html,body{{height:100%;overflow:hidden;-webkit-font-smoothing:antialiased}}
body{{font-family:var(--font-body);background:var(--ink-950);color:var(--ink-200);line-height:1.65}}

/* ===== [03] SLIDE ENGINE — stagger timing ===== */
.slides-container{{position:relative;width:100vw;height:100vh;overflow:hidden;background:var(--ink-950)}}
.slide{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;opacity:0;visibility:hidden;transition:opacity var(--t-base) ease-out,transform var(--t-base) ease-out;transform:translateY(12px);padding:2rem;will-change:opacity,transform}}
.slide.active{{opacity:1;visibility:visible;transform:translateY(0);z-index:10}}
.slide.prev{{opacity:0;transform:translateY(-12px)}}

/* Stagger children */
.slide.active *:nth-child(1){{transition-delay:0ms}}
.slide.active *:nth-child(2){{transition-delay:80ms}}
.slide.active *:nth-child(3){{transition-delay:160ms}}
.slide.active *:nth-child(4){{transition-delay:240ms}}
.slide.active *:nth-child(5){{transition-delay:320ms}}
.slide.active *:nth-child(n+6){{transition-delay:0ms}}

/* ===== [04] PROGRESS BAR ===== */
.progress-track{{position:fixed;top:0;left:0;right:0;height:1.5px;background:rgba(255,255,255,.03);z-index:300}}
.progress-bar{{position:fixed;top:0;left:0;height:1.5px;background:linear-gradient(90deg,var(--accent),var(--accent-mid));transition:width var(--t-base) ease-out;z-index:301}}

/* ===== [05] NAVIGATION ===== */
.nav-bar{{position:fixed;bottom:0;left:0;right:0;z-index:300;display:flex;align-items:center;justify-content:center;gap:1rem;padding:1rem 2rem;background:linear-gradient(transparent,rgba(6,8,13,.9));backdrop-filter:blur(20px);border-top:1px solid var(--border)}}
.nav-btn{{width:40px;height:40px;border-radius:50%;border:1px solid var(--border);background:var(--surface);color:var(--ink-400);display:flex;align-items:center;justify-content:center;cursor:pointer;transition:all var(--t-fast);font-size:1rem;user-select:none}}
.nav-btn:hover{{background:rgba(99,102,241,.12);border-color:var(--border-a);color:var(--accent-mid)}}
.nav-btn:disabled{{opacity:.15;cursor:default}}
.nav-counter{{font-size:.75rem;color:var(--ink-600);font-variant-numeric:tabular-nums;min-width:60px;text-align:center;letter-spacing:.05em}}
.nav-counter .current{{color:var(--ink-200);font-weight:600}}
.fs-btn{{width:32px;height:32px;border-radius:6px;border:1px solid var(--border);background:var(--surface);color:var(--ink-500);display:flex;align-items:center;justify-content:center;cursor:pointer;transition:all var(--t-fast);font-size:.75rem;margin-left:auto}}
.fs-btn:hover{{background:rgba(99,102,241,.1);border-color:var(--border-a);color:var(--accent-mid)}}

/* ===== [06] COVER ===== */
.cover-bg{{position:absolute;inset:0;overflow:hidden;
  background:
    radial-gradient(ellipse 70% 55% at 20% 35%,rgba(99,102,241,.08) 0%,transparent 60%),
    radial-gradient(ellipse 55% 70% at 80% 25%,rgba(99,102,241,.05) 0%,transparent 55%),
    radial-gradient(ellipse 40% 40% at 60% 80%,rgba(99,102,241,.03) 0%,transparent 50%),
    var(--ink-950)}}
.cover-orb{{position:absolute;border-radius:50%;background:radial-gradient(circle,rgba(99,102,241,.06) 0%,transparent 65%);animation:float 18s ease-in-out infinite}}
@keyframes float{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate(20px,-15px)}}}}
.cover-vignette{{position:absolute;inset:0;background:radial-gradient(ellipse at center,transparent 35%,rgba(6,8,13,.55) 100%)}}

.cover-inner{{position:relative;text-align:center;max-width:820px;padding:3rem 2rem}}
.cover-tag{{display:inline-block;padding:.35rem 1.2rem;font-size:.65rem;font-weight:700;letter-spacing:.18em;text-transform:uppercase;color:var(--accent-mid);border:1px solid var(--border-a);border-radius:999px;margin-bottom:2rem}}
.cover-title{{font-family:var(--font-display);font-size:clamp(2rem,5vw,3.4rem);font-weight:800;line-height:1.15;margin-bottom:1.2rem;color:var(--ink-50)}}
.cover-sub{{font-size:clamp(.9rem,1.6vw,1.1rem);color:var(--ink-400);font-weight:300;letter-spacing:.06em;line-height:1.6}}
.cover-rule{{width:60px;height:1.5px;background:linear-gradient(90deg,var(--accent),var(--accent-mid));margin:2rem auto;border-radius:1px}}
.cover-meta{{font-size:.75rem;color:var(--ink-600);letter-spacing:.1em}}

/* ===== [07] SECTION BREAK ===== */
.section-break{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:var(--ink-950)}}
.section-inner{{text-align:center}}
.section-num{{display:block;font-size:6rem;font-weight:700;color:rgba(99,102,241,.06);letter-spacing:-.05em;line-height:1;margin-bottom:-1rem}}
.section-title{{font-family:var(--font-display);font-size:clamp(2rem,5vw,3.2rem);font-weight:700;color:var(--ink-50);line-height:1.2}}

/* ===== [08] SLIDE INNER ===== */
.slide-inner{{width:100%;max-width:1100px;padding:2rem 1.5rem}}
.slide-header{{display:flex;align-items:baseline;gap:.8rem;margin-bottom:1.5rem}}
.slide-num{{font-size:.65rem;font-weight:600;color:var(--accent);letter-spacing:.1em;opacity:.5}}
.slide-title{{font-family:var(--font-display);font-size:clamp(1.2rem,2.5vw,1.7rem);font-weight:700;color:var(--ink-50);line-height:1.3;padding-bottom:.5rem;border-bottom:1px solid rgba(99,102,241,.1);position:relative}}
.slide-title::after{{content:'';position:absolute;bottom:-1px;left:0;width:36px;height:2px;background:linear-gradient(90deg,var(--accent),var(--accent-mid));border-radius:1px}}
.slide-sub{{font-size:.9rem;color:var(--ink-500);font-weight:300;letter-spacing:.05em;margin-bottom:1.5rem;padding-left:3.5rem}}
.slide-headline{{font-family:var(--font-display);font-size:clamp(1.4rem,3vw,2rem);font-weight:700;color:var(--ink-100);line-height:1.3;margin-bottom:1rem}}
.slide-body{{font-size:clamp(.8rem,1.2vw,.92rem);color:var(--ink-400);line-height:1.75;max-width:80ch;margin-bottom:1.2rem}}

/* ===== [09] CONTENT BLOCKS ===== */
.items-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:.8rem;margin-top:.5rem}}
.item-card{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:1rem 1.1rem;transition:all var(--t-fast)}}
.item-card:hover{{background:var(--surface-h);border-color:var(--border-a);transform:translateY(-2px);box-shadow:var(--shadow)}}
.item-card h4{{font-family:var(--font-display);font-size:.85rem;font-weight:700;color:var(--accent-mid);margin-bottom:.4rem;letter-spacing:.02em}}
.item-card ul{{list-style:none;padding:0;margin:0}}
.item-card li{{font-size:clamp(.7rem,1vw,.8rem);color:var(--ink-400);padding:.18rem 0 .18rem .8rem;position:relative;line-height:1.5}}
.item-card li::before{{content:'';position:absolute;left:0;top:.55rem;width:4px;height:4px;background:var(--accent);border-radius:50%;opacity:.35}}

/* ===== [10] TWO-COL ===== */
.twocol{{display:grid;grid-template-columns:1fr 1fr;gap:1.2rem;margin-top:.5rem}}
.cb{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:.8rem 1rem}}
.cb h4{{font-family:var(--font-display);font-size:.8rem;font-weight:700;margin-bottom:.3rem}}
.col-left .cb{{border-color:rgba(248,113,113,.08)}}
.col-left .cb h4{{color:#f87171}}
.col-right .cb{{border-color:rgba(74,222,128,.08)}}
.col-right .cb h4{{color:#4ade80}}
.cb ul{{list-style:none;padding:0;margin:0}}
.cb li{{font-size:clamp(.65rem,.95vw,.76rem);color:var(--ink-400);padding:.1rem 0 .1rem .9rem;position:relative;line-height:1.4}}
.col-left .cb li::before{{content:'›';position:absolute;left:0;color:#f87171;font-size:.6rem;top:.05rem}}
.col-right .cb li::before{{content:'✓';position:absolute;left:0;color:#4ade80;font-size:.6rem;top:.05rem}}

/* ===== [11] IMAGES ===== */
.ci{{width:100%;max-height:42vh;object-fit:contain;border-radius:10px;border:1px solid var(--border);box-shadow:var(--shadow)}}
.cig{{width:100%;max-height:22vh;object-fit:contain;border-radius:8px;border:1px solid var(--border);opacity:.8}}
.ig2{{display:grid;grid-template-columns:1fr 1fr;gap:.8rem;margin-top:1rem}}
.ig3{{display:grid;grid-template-columns:repeat(3,1fr);gap:.6rem;margin-top:1rem}}
.igm{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:.6rem;margin-top:1rem}}

/* ===== [12] THANK YOU ===== */
.thanks-bg{{position:absolute;inset:0;background:var(--ink-950)}}
.thanks-inner{{position:relative;text-align:center;padding:3rem}}
.thanks-eyebrow{{font-size:.65rem;font-weight:700;letter-spacing:.3em;text-transform:uppercase;color:var(--accent);margin-bottom:1.2rem}}
.thanks-title{{font-family:var(--font-display);font-size:clamp(2.2rem,5vw,3.8rem);font-weight:800;color:var(--ink-50);margin-bottom:1.2rem}}
.thanks-rule{{width:40px;height:1.5px;background:linear-gradient(90deg,var(--accent),var(--accent-mid));margin:0 auto 1.2rem;border-radius:1px}}
.thanks-sub{{font-size:.85rem;color:var(--ink-500);letter-spacing:.1em}}

/* ===== [13] RESPONSIVE ===== */
@media(max-width:1024px){{
  .slide{{padding:1.5rem}}
  .slide-inner{{padding:1.8rem 1.2rem;max-width:960px}}
  .cover-inner{{padding:2.5rem 1.5rem}}
  .ci{{max-height:32vh}}
  .cig{{max-height:18vh}}
  .twocol{{gap:.8rem}}
  .items-grid{{grid-template-columns:1fr 1fr}}
}}
@media(max-width:768px){{
  .slide{{padding:1rem}}
  .slide-inner{{padding:1.2rem .8rem}}
  .cover-inner{{padding:1.8rem 1rem}}
  .cover-title{{font-size:1.8rem}}
  .twocol{{grid-template-columns:1fr}}
  .items-grid{{grid-template-columns:1fr}}
  .ig2,.ig3{{grid-template-columns:1fr}}
  .nav-bar{{padding:.7rem .8rem;gap:.6rem}}
}}
@media(max-width:480px){{
  .slide{{padding:.6rem}}
  .slide-inner{{padding:.8rem .5rem}}
  .cover-inner{{padding:1.2rem .8rem}}
  .cover-title{{font-size:1.4rem}}
  .nav-btn{{width:34px;height:34px}}
  .igm{{grid-template-columns:1fr}}
}}

/* ===== [14] UTILITIES ===== */
::-webkit-scrollbar{{width:2px}}::-webkit-scrollbar-thumb{{background:rgba(99,102,241,.15);border-radius:2px}}
.slide *{{opacity:0;transform:translateY(8px);transition:opacity var(--t-base) ease-out,transform var(--t-base) ease-out}}
.slide.active *{{opacity:1;transform:translateY(0)}}
</style>
</head>
<body>
<div class="progress-track"><div class="progress-bar" id="progressBar"></div></div>
<div class="slides-container" id="slidesContainer">
{body}
</div>
<div class="nav-bar" id="navBar">
  <button class="nav-btn" id="prevBtn" aria-label="上一张">‹</button>
  <span class="nav-counter"><span class="current" id="currentNum">1</span> / <span id="totalNum">{num}</span></span>
  <button class="nav-btn" id="nextBtn" aria-label="下一张">›</button>
  <button class="fs-btn" id="fsBtn" aria-label="全屏">⛶</button>
</div>

<script>
(function(){{
  const slides=document.querySelectorAll('.slide');
  const bar=document.getElementById('progressBar');
  const curr=document.getElementById('currentNum');
  const total=document.getElementById('totalNum');
  const pBtn=document.getElementById('prevBtn');
  const nBtn=document.getElementById('nextBtn');
  const fsBtn=document.getElementById('fsBtn');
  let idx=0,locked=false;

  function go(i){{
    if(locked||i===idx||i<0||i>=slides.length)return;
    locked=true;
    slides[idx].classList.remove('active');
    slides[idx].classList.add('prev');
    setTimeout(()=>{{slides[idx].classList.remove('prev')}},700);
    idx=i;
    slides[idx].classList.add('active');
    bar.style.width=(100/(slides.length-1))*idx+'%';
    curr.textContent=idx+1;
    pBtn.disabled=idx===0;
    nBtn.disabled=idx===slides.length-1;
    setTimeout(()=>{{locked=false}},400);
  }}

  pBtn.onclick=()=>go(idx-1);
  nBtn.onclick=()=>go(idx+1);
  fsBtn.onclick=()=>{{
    if(!document.fullscreenElement)document.documentElement.requestFullscreen();
    else document.exitFullscreen();
  }};
  document.addEventListener('keydown',e=>{{
    if(e.key==='ArrowRight'||e.key===' ')go(idx+1);
    if(e.key==='ArrowLeft')go(idx-1);
  }});
  let wt=null;
  document.addEventListener('wheel',e=>{{
    clearTimeout(wt);
    wt=setTimeout(()=>{{
      if(e.deltaY>30)go(idx+1);
      else if(e.deltaY<-30)go(idx-1);
    }},120);
  }},{{passive:true}});
  let tx=0;
  document.addEventListener('touchstart',e=>{{tx=e.touches[0].clientX}},{{passive:true}});
  document.addEventListener('touchend',e=>{{
    const dx=e.changedTouches[0].clientX-tx;
    if(Math.abs(dx)>50)go(idx+(dx>0?-1:1));
  }},{{passive:true}});

  total.textContent=slides.length;
  slides[0].classList.add('active');
}})();
</script>
</body>
</html>'''

out = '/Users/henry/Documents/任務檔案/投影片轉換/html/runs-impacts-aps-partner-v3.html'
with open(out, 'w') as f:
    f.write(html)
size = len(html)
print(f"v3 HTML: {size:,} bytes ({size//1024}KB) — {num} slides")