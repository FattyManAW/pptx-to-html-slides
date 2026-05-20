"""renderer.py — JSON spec + Design Tokens → HTML slides (v3.1)"""
import json

def build_css(tokens):
    c = tokens.get('colors', {})
    t = tokens.get('typography', {})
    ti = tokens.get('timing', {})
    l = tokens.get('layout', {})

    families = {}
    for role, info in t.items():
        families[role] = info.get('family', 'sans-serif')

    stagger = ti.get('stagger', [0, 80, 160, 240, 320])
    stagger_css = ''
    for ms in stagger[:5]:
        stagger_css += f'.slide.active [data-stagger="{ms}"]{{transition-delay:{ms}ms}}\n'
    if len(stagger) > 5:
        stagger_css += '.slide.active [data-stagger]{transition-delay:0ms}\n'

    spring_css = '@keyframes springIn {\n  0%   { opacity:0; transform:translateY(12px) scale(.97); }\n  60%  { opacity:1; transform:translateY(-2px) scale(1.01); }\n  80%  { transform:translateY(1px) scale(.995); }\n  100% { opacity:1; transform:translateY(0) scale(1); }\n}\n@keyframes slideUp {\n  0%   { opacity:0; transform:translateY(24px); }\n  100% { opacity:1; transform:translateY(0); }\n}\n@keyframes slideFromRight {\n  0%   { opacity:0; transform:translateX(40px); }\n  100% { opacity:1; transform:translateX(0); }\n}\n@keyframes slideExit {\n  0%   { opacity:1; transform:translateY(0); }\n  100% { opacity:0; transform:translateY(-16px); }\n}\n@keyframes shimmer {\n  0%,100% { background-position:0% 50%; }\n  50%     { background-position:100% 50%; }\n}'

    bp = l.get('breakpoints', {})
    tablet = bp.get('tablet', 1024)
    mobile = bp.get('mobile', 768)
    small = bp.get('small', 480)

    return f"""/*===============================================================
  Design System — {tokens.get('name','v3')}
  Tokens: {len(c)} colors | {len(ti)} timing | {len(t.get('weights',''))} font weights
  ================================================================*/

/*============================== [00] DESIGN TOKENS — Colors: {', '.join(list(c.keys())[:6])}... | Typography: {', '.join(list(t.keys()))} */
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
  --c-t1: {c.get('c-t1','#f0f4f8')};
  --c-t2: {c.get('c-t2','#94a3b8')};
  --c-t3: {c.get('c-t3','#64748b')};
  --c-t4: {c.get('c-t4','#3b5068')};
  --c-error:   {c.get('c-error','#ef4444')};
  --c-success: {c.get('c-success','#22c55e')};
  --c-warning: {c.get('c-warning','#f59e0b')};
  --c-info:    {c.get('c-info','#3b82f6')};
  --surface: {c.get('surface','rgba(255,255,255,.03)')};
  --surface-h: {c.get('surfaceH','rgba(255,255,255,.06)')};
  --border:  {c.get('border','rgba(255,255,255,.06)')};
  --border-a:{c.get('borderA','var(--c-teal-dim)')};
  --blur:     {l.get('glassBlur','blur(24px)')};
  --blur-card:  blur(10px);
  --blur-sheet: blur(20px);
  --blur-modal: blur(30px);
  --blur-nav:   blur(20px);
  --blur-8:  blur(8px);
  --blur-12: blur(12px);
  --blur-24: blur(24px);
  --blur-32: blur(32px);
  --shadow:  {l.get('shadow','0 8px 40px rgba(0,0,0,.35)')};
  --ease:    {ti.get('ease','cubic-bezier(0.4,0,0.2,1)')};
  --t-fast:  {ti.get('fast','150ms')};
  --t-mid:   {ti.get('mid','300ms')};
  --t-slow:  {ti.get('slow','400ms')};
  --c-bg:    {c.get('ink950','#06080d')};
  --c-bg2:   {c.get('ink900','#0f172a')};
  --c-bg3:   {c.get('ink800','#1e293b')};
  --c-surface:  {c.get('surface','rgba(255,255,255,.04)')};
  --c-surface2: {c.get('surfaceH','rgba(255,255,255,.07)')};
  --c-glass:    rgba(6,8,13,.65);
  --c-border:   {c.get('border','rgba(255,255,255,.08)')};
  --c-teal:     {c.get('accent','#14b8a6')};
  --c-teal-dim: {c.get('borderA','rgba(20,184,166,.12)')};
  --c-teal-glow: rgba(20,184,166,.25);
  --c-teal-hot: {c.get('accentMid','#2dd4bf')};
  --c-t1:  {c.get('c-t1','#f0f4f8')};
  --c-t2:  {c.get('c-t2','#94a3b8')};
  --c-t3:  {c.get('c-t3','#64748b')};
  --c-t4:  {c.get('c-t4','#3b5068')};
  --s1: {l.get('s1','0.5rem')}; --s2: {l.get('s2','1rem')}; --s3: {l.get('s3','1.5rem')};
  --s4: {l.get('s4','2rem')};   --s5: {l.get('s5','2.5rem')}; --s6: {l.get('s6','3rem')};
  --s7: {l.get('s7','4rem')};   --s8: {l.get('s8','5rem')};  --s9: {l.get('s9','6rem')};
  --s10: {l.get('s10','8rem')};
  --display: {families.get('display','serif')};
  --heading: {families.get('heading','serif')};
}}

/*================================= [01] RESET ==================================*/
*,*::before,*::after{{margin:0;padding:0;box-sizing:border-box}}
html,body{{height:100%;overflow:hidden;-webkit-font-smoothing:antialiased;touch-action:pan-y}}
body{{font-family:{families.get('body','sans-serif')};background:var(--c-bg);color:var(--c-t2);line-height:1.65}}

/*=============================== [02] SLIDE ENGINE ===============================*/
.slides-container{{position:relative;width:100vw;height:100vh;overflow:hidden;background:var(--c-bg)}}
.skeleton{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:var(--c-bg);z-index:5}}
.skeleton-bar{{width:60%;height:12px;background:linear-gradient(90deg,var(--surface) 25%,var(--surface-h) 50%,var(--surface) 75%);border-radius:6px;animation:shimmer 1.5s ease-in-out infinite;margin:8px 0}}
.slide{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;opacity:0;visibility:hidden;animation:springIn var(--t-slow) var(--ease) forwards;transform:translateY(12px);padding:{l.get('slidePadding','2rem')};will-change:opacity,transform}}
.slide.active{{opacity:1;visibility:visible;transform:translateY(0);z-index:10}}
.slide.prev{{opacity:0;transform:translateY(-12px)}}
{stagger_css}
{spring_css}
.slide *{{opacity:0;transform:translateY(8px);transition:opacity var(--t-mid) var(--ease),transform var(--t-mid) var(--ease)}}
.slide.active *{{opacity:1;transform:translateY(0)}}
.slide-inner{{width:100%;max-width:{l.get('maxWidth','1100px')};padding:2rem 1.5rem}}

/*================================= [03] PROGRESS ==================================*/
.progress-bar{{position:fixed;top:0;left:0;height:1.5px;background:linear-gradient(90deg,var(--c-teal),var(--c-teal-hot));transition:width var(--t-mid) var(--ease);z-index:301}}
.progress-track{{position:fixed;bottom:0;left:0;right:0;height:1px;background:rgba(255,255,255,.05);z-index:301}}

/*=============================== [04] NAVIGATION ================================*/
.nav-bar{{position:fixed;bottom:0;left:0;right:0;z-index:300;display:flex;align-items:center;justify-content:center;gap:1rem;padding:1rem 2rem;background:linear-gradient(transparent,var(--c-glass));backdrop-filter:blur(20px);border-top:1px solid var(--border)}}
.nav-btn{{width:40px;height:40px;border-radius:50%;border:1px solid var(--border);background:var(--surface);color:var(--c-t2);display:flex;align-items:center;justify-content:center;cursor:pointer;transition:all var(--t-fast);font-size:1rem;user-select:none}}
.nav-btn:hover{{filter:brightness(1.15);background:var(--c-surface2);border-color:var(--c-teal-dim)}}
.nav-btn:disabled{{opacity:.28;cursor:not-allowed;filter:grayscale(50%)}}
.nav-counter{{font-size:.75rem;color:var(--c-t3);font-weight:500;letter-spacing:.08em;min-width:3rem;text-align:center}}
.nav-counter .current{{color:var(--c-t1);font-weight:600}}
.slide-num{{font-size:.65rem;font-weight:600;color:var(--accent);letter-spacing:.1em;opacity:.5}}
.fs-btn{{width:32px;height:32px;border-radius:6px;border:1px solid var(--border);background:var(--surface);color:var(--c-t3);display:flex;align-items:center;justify-content:center;cursor:pointer;transition:all var(--t-fast);font-size:.75rem;margin-left:auto}}

/*============================= [05] SECTION BREAK ==============================*/
.section-break{{width:100%;height:100%;display:flex;align-items:center;justify-content:center;flex-direction:column;background:var(--c-bg)}}
.section-num{{font-family:{families.get('display','serif')};font-size:{l.get('sectionNumSize','6rem')};font-weight:900;color:var(--c-teal);opacity:.12;line-height:1}}
.section-title{{font-family:{families.get('heading','serif')};font-size:clamp(1.6rem,4vw,2.5rem);font-weight:700;color:var(--c-t1);letter-spacing:-.02em}}
.section-sub{{font-size:1rem;color:var(--c-t3);margin-top:.8rem;font-weight:300}}

/*============================= [06] SLIDE CONTENT ==============================*/
.slide-header{{display:flex;align-items:baseline;gap:.8rem;margin-bottom:1.5rem}}
.slide-num{{font-size:.65rem;font-weight:600;color:var(--accent);letter-spacing:.1em;opacity:.5}}
.slide-title{{font-family:{families.get('heading','serif')};font-size:clamp(1.2rem,2.5vw,1.7rem);font-weight:700;color:var(--c-t1);position:relative;padding-bottom:.4rem}}
.slide-title::after{{content:'';position:absolute;bottom:-1px;left:0;width:36px;height:2px;background:linear-gradient(90deg,var(--c-teal),transparent)}}
.slide-sub{{font-size:.9rem;color:var(--c-t3);font-weight:300;letter-spacing:.05em;margin-bottom:1.5rem;padding-left:3.5rem}}
.slide-headline{{font-family:{families.get('display','serif')};font-size:clamp(1.4rem,3vw,2rem);font-weight:700;color:var(--c-t1);margin-bottom:.8rem}}
.slide-body{{font-size:clamp(.8rem,1.2vw,.92rem);color:var(--c-t2);line-height:1.75;max-width:80ch;margin-bottom:1.2rem}}
.slide-body strong{{color:var(--c-t1);font-weight:600}}

/*=================================== [07] CARDS ===================================*/
.item-card{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:1rem 1.1rem;transition:all var(--t-fast)}}
.item-card:hover{{filter:brightness(1.05);background:var(--c-surface2);border-color:var(--c-teal-dim)}}
.item-card:active{{transform:scale(.97);filter:brightness(.95);transition-duration:50ms}}

/*=================================== [08] TWO-COL ===================================*/
.two-col{{display:grid;grid-template-columns:1fr 1fr;gap:2rem;align-items:start;width:100%}}
.two-col>*{{min-width:0}}

/*==================================== [09] IMAGES ====================================*/
.slide-img{{width:100%;height:auto;max-height:55vh;object-fit:contain;border-radius:8px}}

/*=================================== [10] THANK YOU ===================================*/
.thankyou{{text-align:center}}
.thankyou h1{{font-family:{families.get('display','serif')};font-size:clamp(2rem,5vw,3.5rem);font-weight:800;color:var(--c-t1);margin-bottom:.5rem}}
.thankyou p{{color:var(--c-t3);font-weight:300;font-size:1.1rem}}
.thankyou .logo{{font-size:.85rem;color:var(--c-t4);margin-top:2rem;letter-spacing:.15em;text-transform:uppercase}}

/*==================================== [11] COVER =====================================*/
.cover{{width:100%;height:100%;display:flex;align-items:center;justify-content:center;flex-direction:column;position:relative;overflow:hidden}}
.cover-bg{{position:absolute;inset:0;background:radial-gradient(ellipse 70% 60% at 50% 40%,rgba(99,102,241,.12),transparent 70%)}}
.cover-title{{font-family:{families.get('display','serif')};font-size:clamp(2rem,5.5vw,4rem);font-weight:900;color:var(--c-t1);text-align:center;line-height:1.1;position:relative;z-index:1;background:linear-gradient(135deg,var(--c-t1) 0%,var(--c-teal) 50%,var(--c-t1) 100%);background-size:200% 100%;-webkit-background-clip:text;-webkit-text-fill-color:transparent;animation:shimmer 3s ease-in-out infinite}}
.cover-title em{{font-style:normal;background:linear-gradient(135deg,var(--c-teal),var(--c-teal-hot));-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.cover-sub{{font-size:clamp(.85rem,1.5vw,1.1rem);color:var(--c-t3);margin-top:1.2rem;text-align:center;max-width:600px;position:relative;z-index:1;font-weight:300}}
.cover-meta{{margin-top:2.5rem;display:flex;gap:2rem;position:relative;z-index:1}}
.cover-meta span{{font-size:.75rem;color:var(--c-t4);letter-spacing:.12em;text-transform:uppercase}}

/*=============================== [12] RESPONSIVE — {tablet}/{mobile}/{small} ===============================*/
@media(max-width:{tablet}px){{
  .two-col{{grid-template-columns:1fr;gap:1.5rem}}
  .slide-inner{{padding:1.5rem 1rem}}
}}
@media(max-width:{mobile}px){{
  .slide{{padding:1rem}}
  .slide-inner{{padding:1rem .5rem}}
  .slide-title{{font-size:1.1rem}}
  .slide-body{{font-size:.82rem}}
  .item-card{{padding:.8rem}}
  .nav-bar{{padding:.5rem 1rem;gap:.5rem}}
}}
@media(max-width:{small}px){{
  .cover-title{{font-size:1.8rem}}
  .section-num{{font-size:4rem}}
  .cover-meta{{flex-direction:column;gap:.8rem;align-items:center}}
}}

/*================================= [13] UTILITIES ==================================*/
:focus-visible{{outline:2px solid var(--c-teal);outline-offset:2px}}
*:focus:not(:focus-visible){{outline:none}}
.tag{{display:inline-block;padding:.15rem .6rem;border-radius:999px;font-size:.7rem;font-weight:600;letter-spacing:.04em}}
.tag-teal{{background:var(--c-teal-dim);color:var(--c-teal)}}
.tag-warn{{background:rgba(245,158,11,.12);color:var(--c-warning)}}
.tag-err{{background:rgba(239,68,68,.12);color:var(--c-error)}}
.tag-ok{{background:rgba(34,197,94,.12);color:var(--c-success)}}
.kv{{display:flex;gap:.5rem;align-items:baseline;flex-wrap:wrap;margin:.25rem 0}}
.kv k{{font-weight:600;color:var(--c-t1);min-width:5rem}}
.kv v{{color:var(--c-t2);font-weight:300}}
.bullets{{list-style:none;padding:0;margin:0}}
.bullets li{{position:relative;padding-left:1.4rem;margin-bottom:.45rem;color:var(--c-t2);font-size:.88rem;line-height:1.7}}
.bullets li::before{{content:'→';position:absolute;left:0;color:var(--c-teal);font-weight:700}}
.steps{{display:flex;gap:.5rem;align-items:center;flex-wrap:wrap;margin:.5rem 0}}
.step{{display:flex;align-items:center;gap:.4rem;padding:.3rem .8rem;border-radius:8px;background:var(--surface);border:1px solid var(--border);font-size:.8rem;color:var(--c-t2)}}
.step-arrow{{color:var(--c-teal);font-weight:700}}
.two-up{{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem}}
@media(max-width:768px){{.two-up{{grid-template-columns:1fr}}}}
.center{{text-align:center}}
.mt1{{margin-top:var(--s1)}}.mt2{{margin-top:var(--s2)}}.mt3{{margin-top:var(--s3)}}
.mb1{{margin-bottom:var(--s1)}}.mb2{{margin-bottom:var(--s2)}}.mb3{{margin-bottom:var(--s3)}}
"""


def _render_blocks(blocks, img_dir, slide_num=0):
    """Convert blocks list → HTML inner content.

    Image blocks may reference either a bare filename (extractor no-img_dir
    mode) or a shape name. We try: (1) exact filename, (2) glob slideN_*name*,
    (3) glob *name*.
    """
    import glob, os

    def resolve_img(raw_fname):
        # exact match first
        candidate = os.path.join(img_dir, raw_fname)
        if os.path.exists(candidate):
            return raw_fname
        # strip extension for glob matching
        base = os.path.splitext(raw_fname)[0]
        # glob by slide num + base
        matches = glob.glob(os.path.join(img_dir, f'slide{slide_num}_*{base}*'))
        if not matches:
            matches = glob.glob(os.path.join(img_dir, f'*{base}*'))
        if matches:
            return os.path.basename(matches[0])
        return raw_fname  # fallback to original

    parts = []
    for b in blocks:
        if b.startswith('[IMAGE:'):
            # [IMAGE:shape_name.png] or [IMAGE:actual_filename.png]
            raw_fname = b[7:-1]
            fname = resolve_img(raw_fname)
            parts.append(f'<img class="slide-img" src="{img_dir}/{fname}" alt="">')
        elif '	' in b or '    ' in b[:4]:
            # Indented → bullet
            parts.append(f'<li>{b.strip()}</li>')
        elif b.startswith(('1.','2.','3.','4.','5.','6.','7.','8.','9.')):
            parts.append(f'<li>{b[3:].strip()}</li>')
        else:
            parts.append(f'<p>{b}</p>')
    html = ''.join(parts)
    # Wrap consecutive <li> in <ul>
    import re
    html = re.sub(r'(<li>.*?</li>)+', lambda m: '<ul class="bullets">'+m.group()+'</ul>', html)
    return html

def render_slides(spec, tokens, img_dir='html/images'):
    slides_data = spec.get('slides', [])
    body_parts = []
    for idx, s in enumerate(slides_data):
        blocks = s.get('blocks', [])
        _section = s.get('_section')
        inner = _render_blocks(blocks, img_dir, slide_num=idx+1)
        if _section and idx > 0:
            body_parts.append(f"""<div class="section-break" data-stagger="0">
  <div class="section-num">{idx+1}</div>
  <div class="section-title">{_section}</div>
</div>""")
        stagger_val = s.get('stagger', 0)
        body_parts.append(f'<div class="slide" role="group" aria-label="slide {idx+1}" data-stagger="{stagger_val}"><div class="slide-inner">{inner}</div></div>')

    css = build_css(tokens)
    font_link = tokens.get('fonts', {}).get('google', '')
    font_tag = f'<link href="https://fonts.googleapis.com/css2?family={font_link}&display=swap" rel="stylesheet">' if font_link else ''
    total = len(slides_data)
    title = spec.get('title', 'Presentation')

    nav_buttons = f"""<button class="nav-btn" id="prevBtn" disabled>‹</button>
  <span class="nav-counter"><span class="current" id="curNum">1</span> / {total}</span>
  <button class="nav-btn" id="nextBtn">›</button>"""

    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
{font_tag}
<script src="https://cdn.tailwindcss.com"></script>
<style>
{css}
</style>
</head>
<body>
<div class="skeleton" id="skeleton"><div class="skeleton-bar" style="width:40%"></div><div class="skeleton-bar" style="width:60%"></div><div class="skeleton-bar" style="width:50%"></div></div>
<div class="slides-container" id="slides">
{"".join(body_parts)}
</div>
<div class="progress-track"><div class="progress-bar" id="progressBar"></div></div>
<nav class="nav-bar">
  {nav_buttons}
  <span id="cnt" style="position:fixed;top:.8rem;right:1rem;font-size:.65rem;color:var(--c-t4);font-weight:500;z-index:301"></span>
  <button class="fs-btn" id="fsBtn" title="Fullscreen">⛶</button>
</nav>
<script>
(function(){{
  // Skeleton: hide on DOMContentLoaded
  document.addEventListener('DOMContentLoaded',()=>{{
    const sk=document.querySelector('.skeleton');if(sk)sk.style.display='none';
  }});
  const slides=document.querySelectorAll('.slide,.section-break');
  const bar=document.getElementById('progressBar');
  const cur=document.getElementById('curNum');
  const prevBtn=document.getElementById('prevBtn');
  const nextBtn=document.getElementById('nextBtn');
  let current=0,total=slides.length;
  const debounce={{}};
  const WHEEL_DEBOUNCE=120;

  function go(n){{
    if(n<0||n>=total)return;
    const prev=slides[current];prev.classList.remove('active');prev.classList.add('prev');
    current=n;
    slides[current].classList.add('active');slides[current].classList.remove('prev');
    bar.style.width=((current+1)/total*100)+'%';
    cur.textContent=current+1;document.getElementById('cnt').textContent=current+1+'/'+total;
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
    if(e.key==='f'||e.key==='F'){{
      const d=document.fullscreenElement;
      document[d?'exitFullscreen':'requestFullscreen']();
    }}
  }});
  document.addEventListener('wheel',e=>{{
    const now=Date.now();
    if(now-debounce.last<WHEEL_DEBOUNCE)return;
    debounce.last=now;
    go(current+(e.deltaY>0?1:-1));
  }},{{passive:true}});
  document.addEventListener('touchstart',e=>{{debounce.ty=e.touches[0].clientY}},{{passive:true}});
  document.addEventListener('touchend',e=>{{
    const dy=debounce.ty-e.changedTouches[0].clientY;
    if(Math.abs(dy)>30)go(current+(dy>0?1:-1));
  }},{{passive:true}});
  go(0);
}})();
</script>
</body>
</html>"""
