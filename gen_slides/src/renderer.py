"""renderer.py — JSON spec + Design Tokens → HTML slides"""
import json, os, re

def load_tokens(path):
    with open(path) as f:
        return json.load(f)

def css_var(name, tokens, fallback=''):
    """Resolve a CSS var reference like --ink-950."""
    colors = tokens.get('colors', {})
    key = name.lstrip('-')
    return colors.get(key, fallback)

def build_css(tokens):
    c = tokens.get('colors', {})
    t = tokens.get('typography', {})
    ti = tokens.get('timing', {})
    l = tokens.get('layout', {})

    font_link = '|'.join(tokens.get('fonts', {}).get('google', '').split('|'))
    families = {}
    for role, info in t.items():
        families[role] = info.get('family', 'sans-serif')

    stagger = ti.get('stagger', [0, 80, 160, 240, 320])
    stagger_css = ''
    for ms in stagger[:5]:
        stagger_css += f'.slide.active [data-stagger="{ms}"]{{transition-delay:{ms}ms}}\n'
    if len(stagger) > 5:
        stagger_css += '.slide.active [data-stagger]{transition-delay:0ms}\n'

    bp = l.get('breakpoints', {})
    tablet = bp.get('tablet', 1024)
    mobile = bp.get('mobile', 768)
    small = bp.get('small', 480)

    return f"""/* ================================================================
   Design System — {tokens.get('name','v3')}
   Tokens: {len(c)} colors | {len(ti)} timing rules | {len(t.get('weights',''))} font weights
   ================================================================ */

/* [00] DESIGN TOKENS — Colors: {', '.join(list(c.keys())[:6])}... | Typography: {', '.join(list(t.keys()))} */
:root {{
  --ink-50:  {c.get('ink50','#f8fafc')};
  --ink-100: {c.get('ink100','#f1f5f9')};
  --ink-200: {c.get('ink200','#e2e8f0')};
  --ink-300: {c.get('ink300','#cbd5e1')};
  --ink-400: {c.get('ink400','#94a3b8')};
  --ink-500: {c.get('ink500','#64748b')};
  --ink-600: {c.get('ink600','#475569')};
  --ink-700: {c.get('ink700','#334155')};
  --ink-800: {c.get('ink800','#1e293b')};
  --ink-900: {c.get('ink900','#0f172a')};
  --ink-950: {c.get('ink950','#06080d')};
  --accent:  {c.get('accent','#6366f1')};
  --accent-mid: {c.get('accentMid','#818cf8')};
  --surface: {c.get('surface','rgba(255,255,255,.03)')};
  --surface-h: {c.get('surfaceH','rgba(255,255,255,.06)')};
  --border:  {c.get('border','rgba(255,255,255,.06)')};
  --border-a:{c.get('borderA','rgba(99,102,241,.2)')};
  --blur:    {l.get('glassBlur','blur(24px)')};
  --shadow:  {l.get('shadow','0 8px 40px rgba(0,0,0,.35)')};
  --t-fast:  {ti.get('fast','200ms')};
  --t-base:  {ti.get('base','350ms')};
}}

/* Reset */
*,*::before,*::after{{margin:0;padding:0;box-sizing:border-box}}
html,body{{height:100%;overflow:hidden;-webkit-font-smoothing:antialiased}}
body{{font-family:{families.get('body','sans-serif')};background:var(--ink-950);color:var(--ink-200);line-height:1.65}}

/* Slide Engine */
.slides-container{{position:relative;width:100vw;height:100vh;overflow:hidden;background:var(--ink-950)}}
.slide{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;opacity:0;visibility:hidden;transition:opacity var(--t-base) ease-out,transform var(--t-base) ease-out;transform:translateY(12px);padding:{l.get('slidePadding','2rem')};will-change:opacity,transform}}
.slide.active{{opacity:1;visibility:visible;transform:translateY(0);z-index:10}}
.slide.prev{{opacity:0;transform:translateY(-12px)}}
{stagger_css}
.slide *{{opacity:0;transform:translateY(8px);transition:opacity var(--t-base) ease-out,transform var(--t-base) ease-out}}
.slide.active *{{opacity:1;transform:translateY(0)}}

/* Progress */
.progress-track{{position:fixed;top:0;left:0;right:0;height:1.5px;background:rgba(255,255,255,.03);z-index:300}}
.progress-bar{{position:fixed;top:0;left:0;height:1.5px;background:linear-gradient(90deg,var(--accent),var(--accent-mid));transition:width var(--t-base) ease-out;z-index:301}}

/* Navigation */
.nav-bar{{position:fixed;bottom:0;left:0;right:0;z-index:300;display:flex;align-items:center;justify-content:center;gap:1rem;padding:1rem 2rem;background:linear-gradient(transparent,rgba(6,8,13,.9));backdrop-filter:blur(20px);border-top:1px solid var(--border)}}
.nav-btn{{width:40px;height:40px;border-radius:50%;border:1px solid var(--border);background:var(--surface);color:var(--ink-400);display:flex;align-items:center;justify-content:center;cursor:pointer;transition:all .2s;font-size:1rem;user-select:none}}
.nav-btn:hover{{background:rgba(99,102,241,.12);border-color:var(--border-a);color:var(--accent-mid)}}
.nav-btn:disabled{{opacity:.15;cursor:default}}
.nav-counter{{font-size:.75rem;color:var(--ink-600);font-variant-numeric:tabular-nums;min-width:60px;text-align:center}}
.nav-counter .current{{color:var(--ink-200);font-weight:600}}
.fs-btn{{width:32px;height:32px;border-radius:6px;border:1px solid var(--border);background:var(--surface);color:var(--ink-500);display:flex;align-items:center;justify-content:center;cursor:pointer;transition:all .2s;font-size:.75rem;margin-left:auto}}
.fs-btn:hover{{background:rgba(99,102,241,.1);border-color:var(--border-a);color:var(--accent-mid)}}

/* Section Break */
.section-break{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:var(--ink-950)}}
.section-inner{{text-align:center}}
.section-num{{display:block;font-size:{l.get('sectionNumSize','6rem')};font-weight:700;color:rgba(99,102,241,.06);letter-spacing:-.05em;line-height:1;margin-bottom:-1rem}}
.section-title{{font-family:{families.get('display','serif')};font-size:clamp(2rem,5vw,3.2rem);font-weight:700;color:var(--ink-50);line-height:1.2}}

/* Slide Content */
.slide-inner{{width:100%;max-width:{l.get('maxWidth','1100px')};padding:2rem 1.5rem}}
.slide-header{{display:flex;align-items:baseline;gap:.8rem;margin-bottom:1.5rem}}
.slide-num{{font-size:.65rem;font-weight:600;color:var(--accent);letter-spacing:.1em;opacity:.5}}
.slide-title{{font-family:{families.get('heading','serif')};font-size:clamp(1.2rem,2.5vw,1.7rem);font-weight:700;color:var(--ink-50);line-height:1.3;padding-bottom:.5rem;border-bottom:1px solid rgba(99,102,241,.1);position:relative}}
.slide-title::after{{content:'';position:absolute;bottom:-1px;left:0;width:36px;height:2px;background:linear-gradient(90deg,var(--accent),var(--accent-mid));border-radius:1px}}
.slide-sub{{font-size:.9rem;color:var(--ink-500);font-weight:300;letter-spacing:.05em;margin-bottom:1.5rem;padding-left:3.5rem}}
.slide-headline{{font-family:{families.get('display','serif')};font-size:clamp(1.4rem,3vw,2rem);font-weight:700;color:var(--ink-100);line-height:1.3;margin-bottom:1rem}}
.slide-body{{font-size:clamp(.8rem,1.2vw,.92rem);color:var(--ink-400);line-height:1.75;max-width:80ch;margin-bottom:1.2rem}}

/* Cards */
.item-card{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:1rem 1.1rem;transition:all .2s}}
.item-card:hover{{background:var(--surface-h);border-color:var(--border-a);transform:translateY(-2px);box-shadow:var(--shadow)}}
.item-card h4{{font-family:{families.get('heading','serif')};font-size:.85rem;font-weight:700;color:var(--accent-mid);margin-bottom:.4rem}}
.item-card ul{{list-style:none;padding:0;margin:0}}
.item-card li{{font-size:clamp(.7rem,1vw,.8rem);color:var(--ink-400);padding:.18rem 0 .18rem .8rem;position:relative;line-height:1.5}}
.item-card li::before{{content:'';position:absolute;left:0;top:.55rem;width:4px;height:4px;background:var(--accent);border-radius:50%;opacity:.35}}

/* Two-col */
.twocol{{display:grid;grid-template-columns:1fr 1fr;gap:1.2rem;margin-top:.5rem}}
.cb{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:.8rem 1rem}}
.cb h4{{font-family:{families.get('heading','serif')};font-size:.8rem;font-weight:700;margin-bottom:.3rem}}
.cb ul{{list-style:none;padding:0;margin:0}}
.cb li{{font-size:clamp(.65rem,.95vw,.76rem);color:var(--ink-400);padding:.1rem 0 .1rem .9rem;position:relative;line-height:1.4}}
.col-left .cb{{border-color:rgba(248,113,113,.08)}}.col-left .cb h4{{color:#f87171}}
.col-left .cb li::before{{content:'›';position:absolute;left:0;color:#f87171;font-size:.6rem;top:.05rem}}
.col-right .cb{{border-color:rgba(74,222,128,.08)}}.col-right .cb h4{{color:#4ade80}}
.col-right .cb li::before{{content:'✓';position:absolute;left:0;color:#4ade80;font-size:.6rem;top:.05rem}}

/* Images */
.ci{{width:100%;max-height:42vh;object-fit:contain;border-radius:10px;border:1px solid var(--border);box-shadow:var(--shadow)}}
.cig{{width:100%;max-height:22vh;object-fit:contain;border-radius:8px;border:1px solid var(--border);opacity:.8}}
.ig2{{display:grid;grid-template-columns:1fr 1fr;gap:.8rem;margin-top:1rem}}
.ig3{{display:grid;grid-template-columns:repeat(3,1fr);gap:.6rem;margin-top:1rem}}
.igm{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:.6rem;margin-top:1rem}}

/* Thank You */
.thanks-inner{{position:relative;text-align:center;padding:3rem}}
.thanks-eyebrow{{font-size:.65rem;font-weight:700;letter-spacing:.3em;text-transform:uppercase;color:var(--accent);margin-bottom:1.2rem}}
.thanks-title{{font-family:{families.get('display','serif')};font-size:clamp(2.2rem,5vw,3.8rem);font-weight:800;color:var(--ink-50);margin-bottom:1.2rem}}
.thanks-rule{{width:40px;height:1.5px;background:linear-gradient(90deg,var(--accent),var(--accent-mid));margin:0 auto 1.2rem;border-radius:1px}}
.thanks-sub{{font-size:.85rem;color:var(--ink-500);letter-spacing:.1em}}

/* Cover */
.cover-bg{{position:absolute;inset:0;overflow:hidden;background:radial-gradient(ellipse 70% 55% at 20% 35%,rgba(99,102,241,.08) 0%,transparent 60%),radial-gradient(ellipse 55% 70% at 80% 25%,rgba(99,102,241,.05) 0%,transparent 55%),var(--ink-950)}}
.cover-vignette{{position:absolute;inset:0;background:radial-gradient(ellipse at center,transparent 35%,rgba(6,8,13,.55) 100%)}}
.cover-inner{{position:relative;text-align:center;max-width:820px;padding:3rem 2rem}}
.cover-tag{{display:inline-block;padding:.35rem 1.2rem;font-size:.65rem;font-weight:700;letter-spacing:.18em;text-transform:uppercase;color:var(--accent-mid);border:1px solid var(--border-a);border-radius:999px;margin-bottom:2rem}}
.cover-title{{font-family:{families.get('display','serif')};font-size:clamp(2rem,5vw,3.4rem);font-weight:800;line-height:1.15;margin-bottom:1.2rem;color:var(--ink-50)}}
.cover-sub{{font-size:clamp(.9rem,1.6vw,1.1rem);color:var(--ink-400);font-weight:300;letter-spacing:.06em;line-height:1.6}}
.cover-rule{{width:60px;height:1.5px;background:linear-gradient(90deg,var(--accent),var(--accent-mid));margin:2rem auto;border-radius:1px}}
.cover-meta{{font-size:.75rem;color:var(--ink-600);letter-spacing:.1em}}

/* [11] RESPONSIVE — {tablet}/{mobile}/{small} */
@media(max-width:{tablet}px){{.slide{{padding:1.5rem}}.slide-inner{{padding:1.8rem 1.2rem}}.ci{{max-height:32vh}}.twocol{{gap:.8rem}}.items-grid{{grid-template-columns:1fr 1fr}}}}
@media(max-width:{mobile}px){{.slide{{padding:1rem}}.slide-inner{{padding:1.2rem .8rem}}.twocol{{grid-template-columns:1fr}}.items-grid{{grid-template-columns:1fr}}.ig2,.ig3{{grid-template-columns:1fr}}}}
@media(max-width:{small}px){{.slide{{padding:.6rem}}.slide-inner{{padding:.8rem .5rem}}.igm{{grid-template-columns:1fr}}}}

/* [12] UTILITIES */
::-webkit-scrollbar{{width:2px}}::-webkit-scrollbar-thumb{{background:rgba(99,102,241,.15);border-radius:2px}}
"""

def render_slides(spec, tokens, img_dir='html/images'):
    c = tokens.get('colors', {})
    css = build_css(tokens)
    t = tokens.get('typography', {})
    body_parts = []
    num = 0
    slides_data = spec.get('slides', [])

    for s in slides_data:
        if s.get('_section'):
            body_parts.append(f"""<div class="section-break" data-stagger="0">
  <div class="section-inner">
    <span class="section-num">0{s.get('_section_num','')}</span>
    <h2 class="section-title">{_esc(s['_section'])}</h2>
  </div>
</div>""")
            continue
        if s.get('title', '').lower() in ('thank you', 'thanks'):
            body_parts.append(f"""<div class="slide" data-stagger="0">
  <div class="thanks-inner">
    <p class="thanks-eyebrow">Thank You</p>
    <h1 class="thanks-title">{_esc(s.get('title',''))}</h1>
    <div class="thanks-rule"></div>
    <p class="thanks-sub">{_esc(s.get('body',''))}</p>
  </div>
</div>""")
            continue
        num += 1
        s['num'] = num

        # Build content
        inner_parts = []
        inner_parts.append(f'<div class="slide-header"><span class="slide-num">{num:02d}</span><h2 class="slide-title">{_esc(s.get("title",""))}</h2></div>')
        if s.get('body'):
            inner_parts.append(f'<p class="slide-body">{_esc(s["body"])}</p>')

        # Detect and render content blocks from PPTX text
        for block in s.get('blocks', [])[1:4]:  # max 3 blocks
            if block.startswith('[IMAGE:'):
                fname = block[7:-1]
                inner_parts.append(f'<div class="slide-img-row"><img class="ci" src="{img_dir}/{fname}" alt=""></div>')
            elif len(block) > 10:
                inner_parts.append(f'<p class="slide-body">{_esc(block)}</p>')

        inner = '\n'.join(inner_parts)
        stagger_val = s.get('stagger', 0)
        body_parts.append(f'<div class="slide" data-stagger="{stagger_val}"><div class="slide-inner">{inner}</div></div>')

    total = num
    body = '\n\n'.join(body_parts)

    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>{_esc(spec.get('source','Presentation'))} — v3</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family={tokens.get('fonts',{}).get('google','Inter:wght@300;400;500;600;700')}&display=swap" rel="stylesheet">
<script src="https://cdn.tailwindcss.com"></script>
<script>tailwind.config={{"theme":{{"extend":{{"fontFamily":{{"body":["Inter","Noto Sans SC","sans-serif"]}}}}}}}}</script>
<style>{css}
</style>
</head>
<body>
<div class="progress-track"><div class="progress-bar" id="progressBar"></div></div>
<div class="slides-container" id="slidesContainer">
{body}
</div>
<div class="nav-bar" id="navBar">
  <button class="nav-btn" id="prevBtn" aria-label="prev">‹</button>
  <span class="nav-counter"><span class="current" id="currentNum">1</span> / <span id="totalNum">{total}</span></span>
  <button class="nav-btn" id="nextBtn" aria-label="next">›</button>
  <button class="fs-btn" id="fsBtn" aria-label="fullscreen">⛶</button>
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
    locked=true;slides[idx].classList.remove('active');slides[idx].classList.add('prev');
    setTimeout(()=>slides[idx].classList.remove('prev'),700);
    idx=i;slides[idx].classList.add('active');
    bar.style.width=(100/(slides.length-1))*idx+'%';curr.textContent=idx+1;
    pBtn.disabled=idx===0;nBtn.disabled=idx===slides.length-1;
    setTimeout(()=>{{locked=false}},400);
  }}
  pBtn.onclick=()=>go(idx-1);nBtn.onclick=()=>go(idx+1);
  fsBtn.onclick=()=>{{if(!document.fullscreenElement)document.documentElement.requestFullscreen();else document.exitFullscreen();}};
  document.addEventListener('keydown',e=>{{if(e.key==='ArrowRight'||e.key===' ')go(idx+1);if(e.key==='ArrowLeft')go(idx-1);}});
  let wt=null;document.addEventListener('wheel',e=>{{clearTimeout(wt);wt=setTimeout(()=>{{if(e.deltaY>30)go(idx+1);else if(e.deltaY<-30)go(idx-1);}},120);}},{{passive:true}});
  let tx=0;document.addEventListener('touchstart',e=>{{tx=e.touches[0].clientX}},{{passive:true}});
  document.addEventListener('touchend',e=>{{const dx=e.changedTouches[0].clientX-tx;if(Math.abs(dx)>50)go(idx+(dx>0?-1:1));}},{{passive:true}});
  total.textContent=slides.length;slides[0].classList.add('active');
}})();
</script>
</body>
</html>"""

def _esc(t):
    return t.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')
