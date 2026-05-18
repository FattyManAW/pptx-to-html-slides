#!/usr/bin/env python3
"""PPTX to self-contained HTML slides converter."""
import zipfile, xml.etree.ElementTree as ET, base64, os, re, sys

NS_A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
NS_P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
NS_R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
EMU = 914400


def t(el):
    return el.tag.split('}')[-1] if '}' in el.tag else el.tag


def px(v):
    return round(int(v) / EMU * 96)


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def parse_pptx(path):
    z = zipfile.ZipFile(path)
    tc = {}
    try:
        th = ET.fromstring(z.read('ppt/theme/theme1.xml'))
        for cs in th.iter():
            if t(cs) == 'clrScheme':
                for c in cs:
                    nm = t(c)
                    srgb = c.find('{%s}srgbClr' % NS_A)
                    if srgb is not None:
                        tc[nm] = '#' + srgb.get('val', '')
    except Exception:
        pass

    media = {}
    for n in z.namelist():
        if n.startswith('ppt/media/'):
            fn = os.path.basename(n)
            data = z.read(n)
            mime = 'image/jpeg' if n.lower().endswith(('.jpg', '.jpeg')) else 'image/png'
            media[fn] = (mime, base64.b64encode(data).decode())

    srels = {}
    for n in z.namelist():
        if 'slides/_rels/slide' in n and n.endswith('.xml.rels'):
            m = re.search(r'slide(\d+)', n)
            if not m:
                continue
            si = int(m.group(1))
            rels = {}
            for rel in ET.parse(z.open(n)).getroot():
                rid = rel.get('Id', '')
                tgt = rel.get('Target', '')
                if 'media' in tgt:
                    fn = os.path.basename(tgt.replace('..\\', '../').replace('\\', '/'))
                    rels[rid] = media.get(fn)
            srels[si] = rels

    sz_el = ET.fromstring(z.read('ppt/presentation.xml')).find('.//{%s}sldSz' % NS_P)
    W = round(int(sz_el.get('cx', 12192000)) / EMU * 96)
    H = round(int(sz_el.get('cy', 6858000)) / EMU * 96)

    slides = []
    for si in range(1, 300):
        try:
            sx = z.read('ppt/slides/slide%d.xml' % si)
        except KeyError:
            break
        root = ET.fromstring(sx)

        bg = '#FFFFFF'
        bg_el = root.find('.//{%s}cSld/{%s}bg' % (NS_P, NS_P))
        if bg_el is not None:
            srgb_bg = bg_el.find('.//{%s}srgbClr' % NS_A)
            if srgb_bg is not None:
                bg = '#' + srgb_bg.get('val', '')

        spTree = None
        for el in root.iter():
            if t(el) == 'spTree':
                spTree = el
                break
        if spTree is None:
            continue

        shapes = []
        for child in spTree:
            ct = t(child)
            if ct in ('nvGrpSpPr', 'grpSpPr'):
                continue
            if ct == 'grp':
                for gc in child:
                    if t(gc) in ('nvGrpSpPr', 'grpSpPr'):
                        continue
                    shapes.extend(_shape(gc, tc, srels.get(si, {})))
                continue
            shapes.extend(_shape(child, tc, srels.get(si, {})))

        slides.append({'w': W, 'h': H, 'bg': bg, 'shapes': shapes})

    return slides, tc


def _shape(child, tc, rels):
    shapes = []
    ct = t(child)

    if ct == 'pic':
        nv = child.find('{%s}nvPicPr/{%s}cNvPr' % (NS_P, NS_P))
        name = nv.get('name', '') if nv is not None else ''
        blip = child.find('.//{%s}blip' % NS_A)
        embed = blip.get('{%s}embed' % NS_R, '') if blip is not None else ''
        media = rels.get(embed)
        if not media:
            return shapes
        xfrm = child.find('.//{%s}xfrm' % NS_A)
        off = xfrm.find('{%s}off' % NS_A) if xfrm is not None else None
        ext = xfrm.find('{%s}ext' % NS_A) if xfrm is not None else None
        l = px(off.get('x', 0)) if off is not None else 0
        t_ = px(off.get('y', 0)) if off is not None else 0
        w = px(ext.get('cx', 0)) if ext is not None else 0
        h = px(ext.get('cy', 0)) if ext is not None else 0
        mime, b64 = media
        shapes.append({'type': 'pic', 'l': l, 't': t_, 'w': w, 'h': h, 'src': 'data:%s;base64,%s' % (mime, b64)})
        return shapes

    if ct == 'sp':
        nv = child.find('{%s}nvSpPr/{%s}cNvPr' % (NS_P, NS_P))
        name = nv.get('name', '') if nv is not None else ''
        is_title = '标题' in name

        xfrm = child.find('.//{%s}xfrm' % NS_A)
        off = xfrm.find('{%s}off' % NS_A) if xfrm is not None else None
        ext = xfrm.find('{%s}ext' % NS_A) if xfrm is not None else None
        l = px(off.get('x', 0)) if off is not None else 0
        t_ = px(off.get('y', 0)) if off is not None else 0
        w = px(ext.get('cx', 0)) if ext is not None else 0
        h = px(ext.get('cy', 0)) if ext is not None else 0

        body_color = '#000000'
        txBody = child.find('{%s}txBody' % NS_P)
        if txBody is not None:
            sf = txBody.find('.//{%s}solidFill/{%s}srgbClr' % (NS_A, NS_A))
            if sf is not None:
                body_color = '#' + sf.get('val', body_color)

        paras = []
        if txBody is not None:
            for p_el in txBody.findall('{%s}p' % NS_A):
                segs = []
                p_style = {}
                pPr = p_el.find('{%s}pPr' % NS_A)
                if pPr is not None:
                    algn = pPr.find('{%s}algn' % NS_A)
                    if algn is not None:
                        p_style['text-align'] = algn.get('val', 'left')

                for r_el in p_el.findall('{%s}r' % NS_A):
                    rPr = r_el.find('{%s}rPr' % NS_A)
                    t_el = r_el.find('{%s}t' % NS_A)
                    text = t_el.text if (t_el is not None and t_el.text) else ''

                    css_parts = []
                    if rPr is not None:
                        fams = []
                        for fn_tag in ('latin', 'ea', 'cs'):
                            f_el = rPr.find('{%s}%s' % (NS_A, fn_tag))
                            if f_el is not None:
                                fv = f_el.get('typeface', '')
                                if fv:
                                    fams.append(fv)
                        if fams:
                            ff = ', '.join(['"' + f + '"' for f in fams])
                            css_parts.append('font-family:' + ff)

                        sz = rPr.get('sz')
                        if sz:
                            css_parts.append('font-size:' + str(int(sz) / 100) + 'pt')
                        if rPr.get('b') == '1':
                            css_parts.append('font-weight:bold')
                        if rPr.get('i') == '1':
                            css_parts.append('font-style:italic')

                        sf2 = rPr.find('{%s}solidFill' % NS_A)
                        if sf2 is not None:
                            srgb2 = sf2.find('{%s}srgbClr' % NS_A)
                            if srgb2 is not None:
                                css_parts.append('color:#' + srgb2.get('val', ''))
                            else:
                                sc2 = sf2.find('{%s}schemeClr' % NS_A)
                                if sc2 is not None:
                                    cn = sc2.get('val', '')
                                    if cn in tc:
                                        css_parts.append('color:' + tc[cn])

                    segs.append((text, ';'.join(css_parts)))

                if segs:
                    paras.append({'segs': segs, 'style': p_style})

        if paras:
            shapes.append({'type': 'text', 'is_title': is_title, 'l': l, 't': t_, 'w': w, 'h': h, 'color': body_color, 'paras': paras})

    return shapes


def render_html(slides, title):
    W = slides[0]['w']
    H = slides[0]['h']

    sections = []
    for i, sl in enumerate(slides):
        inner = ''
        for sh in sl['shapes']:
            if sh['type'] == 'pic':
                inner += '<div class="sh pic" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx">' % (sh['l'], sh['t'], sh['w'], sh['h'])
                inner += '<img src="%s" style="width:100%%;height:100%%;object-fit:contain">' % sh['src']
                inner += '</div>\n'
            elif sh['type'] == 'text':
                cls = 'sh text ttl' if sh['is_title'] else 'sh text'
                inner += '<div class="%s" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx;color:%s">' % (cls, sh['l'], sh['t'], sh['w'], sh['h'], sh['color'])
                for p in sh['paras']:
                    st = p['style']
                    aln = st.get('text-align', 'left')
                    inner += '<p style="text-align:%s">' % aln
                    for text, css in p['segs']:
                        if css:
                            inner += '<span style="%s">%s</span>' % (css, esc(text))
                        else:
                            inner += esc(text)
                    inner += '</p>'
                inner += '</div>\n'

        cls = 'slide active' if i == 0 else 'slide'
        sections.append('<section class="%s" data-i="%d">\n%s</section>' % (cls, i, inner))

    body = ''.join(sections)

    return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>%s</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:100%%;height:100%%;overflow:hidden;background:#1a1a2e;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}
.deck{width:100%%;height:100%%;position:relative;display:flex;align-items:center;justify-content:center}
.slide{position:absolute;width:%dpx;height:%dpx;opacity:0;transform:scale(.94) translateY(24px);transition:opacity .35s ease,transform .35s ease;pointer-events:none;overflow:hidden;border-radius:8px;box-shadow:0 20px 60px rgba(0,0,0,.5)}
.slide.active{opacity:1;transform:scale(1) translateY(0);pointer-events:auto;z-index:10}
.sh{position:absolute;overflow:hidden}
.sh.pic img{width:100%%;height:100%%;object-fit:contain}
.sh.text p{margin:0;line-height:1.5;white-space:pre-wrap;word-break:break-word}
.sh.ttl p{font-weight:700}
.nav{position:fixed;bottom:20px;left:50%%;transform:translateX(-50%%);display:flex;gap:10px;z-index:100;align-items:center}
.nav button{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.2);color:#fff;padding:6px 14px;border-radius:16px;cursor:pointer;font-size:13px;backdrop-filter:blur(8px);transition:.2s}
.nav button:hover{background:rgba(255,255,255,.25)}
.nav button:disabled{opacity:.25;cursor:default}
.nav .cnt{color:rgba(255,255,255,.6);font-size:13px;min-width:50px;text-align:center}
.fs{position:fixed;top:14px;right:14px;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);color:#fff;width:34px;height:34px;border-radius:50%%;cursor:pointer;z-index:100;display:flex;align-items:center;justify-content:center;font-size:15px;backdrop-filter:blur(8px)}
.prog{position:fixed;top:0;left:0;height:3px;background:#E60012;z-index:100;transition:width .3s}
</style>
</head>
<body>
<div class="prog" id="prog"></div>
<button class="fs" onclick="fs()">&#x26F6;</button>
<div class="deck" id="deck">%s</div>
<div class="nav">
  <button id="pb" onclick="prev()">&#8592; Prev</button>
  <span class="cnt" id="cnt">1 / %d</span>
  <button id="nb" onclick="next()">Next &#8594;</button>
</div>
<script>
var cur=0,tot=%d,slides=document.querySelectorAll('.slide');
function goto(n){
  if(n<0||n>=tot)return;
  slides[cur].className='slide';
  cur=n;
  slides[cur].className='slide active';
  document.getElementById('cnt').textContent=(cur+1)+' / '+tot;
  document.getElementById('prog').style.width=((cur+1)/tot*100)+'%%';
  document.getElementById('pb').disabled=cur===0;
  document.getElementById('nb').disabled=cur===tot-1;
}
function next(){goto(cur+1)}
function prev(){goto(cur-1)}
function fs(){if(!document.fullscreenElement)document.documentElement.requestFullscreen();else document.exitFullscreen()}
document.addEventListener('keydown',function(e){
  if(e.key==='ArrowRight'||e.key===' '||e.key==='PageDown'){e.preventDefault();next()}
  if(e.key==='ArrowLeft'||e.key==='PageUp'){e.preventDefault();prev()}
  if(e.key==='Home'){e.preventDefault();goto(0)}
  if(e.key==='End'){e.preventDefault();goto(tot-1)}
  if(e.key==='f'){fs()}
});
var tx=0;
document.addEventListener('touchstart',function(e){tx=e.touches[0].clientX});
document.addEventListener('touchend',function(e){
  var d=tx-e.changedTouches[0].clientX;
  if(Math.abs(d)>50){d>0?next():prev()}
});
goto(0);
</script>
</body>
</html>''' % (esc(title), W, H, body, len(slides), len(slides))


def main():
    if len(sys.argv) < 3:
        print("Usage: pptx2html.py <input.pptx> <output.html> [--title 'Title']")
        sys.exit(1)
    inp = sys.argv[1]
    out = sys.argv[2]
    title = 'Presentation'
    if '--title' in sys.argv:
        ti = sys.argv.index('--title')
        if ti + 1 < len(sys.argv):
            title = sys.argv[ti + 1]

    print("Converting %s ..." % os.path.basename(inp))
    slides, tc = parse_pptx(inp)
    print("  %d slides" % len(slides))

    html = render_html(slides, title)
    os.makedirs(os.path.dirname(os.path.abspath(out)) or '.', exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)

    print("  -> %s (%.0f KB)" % (out, os.path.getsize(out) / 1024))


if __name__ == '__main__':
    main()
