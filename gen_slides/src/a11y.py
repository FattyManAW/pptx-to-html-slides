"""
a11y.py — WCAG 2.1 AA Accessibility Injection (gen_slides v5)

功能：
1. inject_aria_labels()     — nav button + slide aria-label 增強
2. inject_skip_nav()        — skip-nav link
3. inject_reduced_motion()  — prefers-reduced-motion CSS
4. inject_focus_trap()      — focus-visible + tab order
5. inject_aria_current()    — aria-current="page" on active slide
6. inject_aria_live()       — aria-live region for screen readers
7. check_contrast()         — text/background contrast ratio checker

用法：
  from gen_slides.src.a11y import enhance_html
  html = enhance_html(html, slides_count)
"""

import re
from typing import Tuple


# ═══════════════════════════════════════════════════════════════════
# Color contrast (WCAG AA ≥ 4.5:1 normal, ≥ 3:1 large)
# ═══════════════════════════════════════════════════════════════════

def _hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return None
    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (r, g, b)
    except ValueError:
        return None


def _relative_luminance(r: int, g: int, b: int) -> float:
    """Compute WCAG relative luminance."""
    def _channel(c: int) -> float:
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def contrast_ratio(hex1: str, hex2: str) -> float:
    """Return contrast ratio between two hex colors, or None if unparseable."""
    rgb1 = _hex_to_rgb(hex1)
    rgb2 = _hex_to_rgb(hex2)
    if rgb1 is None or rgb2 is None:
        return None
    l1 = _relative_luminance(*rgb1)
    l2 = _relative_luminance(*rgb2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def check_contrast(html: str) -> dict:
    """
    Scan inline styles + style blocks for color declarations and check contrast.
    Returns: { "pass": [...], "fail": [...], "total": N }
    """
    results = {"pass": [], "fail": [], "total": 0}

    # Extract CSS blocks
    style_blocks = re.findall(r'<style[^>]*>(.*?)</style>', html, re.DOTALL | re.IGNORECASE)

    # Color property patterns
    color_pattern = re.compile(
        r'(?:color|background(?:-color)?|fill|stroke)\s*:\s*'
        r'(#[0-9a-fA-F]{3,6}|rgba?\([^)]+\)|var\(--[^)]+\))',
        re.IGNORECASE
    )

    for block in style_blocks:
        props = color_pattern.findall(block)
        if len(props) < 2:
            continue
        for i in range(0, len(props) - 1, 2):
            fg = props[i]
            bg = props[i + 1]
            # Skip var() references
            if 'var(' in fg or 'var(' in bg:
                continue
            ratio = contrast_ratio(fg, bg)
            if ratio is None:
                continue
            results["total"] += 1
            if ratio >= 4.5:
                results["pass"].append({"fg": fg, "bg": bg, "ratio": round(ratio, 2)})
            else:
                results["fail"].append({"fg": fg, "bg": bg, "ratio": round(ratio, 2)})

    return results


# ═══════════════════════════════════════════════════════════════════
# ARIA + Keyboard Navigation Injection
# ═══════════════════════════════════════════════════════════════════

SKIP_NAV_CSS = """
.skip-nav{position:absolute;top:-100%;left:0;background:var(--accent,#14b8a6);color:#000;padding:.4rem .8rem;z-index:9999;font-size:.75rem;font-weight:600;border-radius:0 0 6px 0}
.skip-nav:focus{top:0}
"""

REDUCED_MOTION_CSS = """
@media(prefers-reduced-motion:reduce){
  *,*::before,*::after{animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important;scroll-behavior:auto!important}
}
"""

FOCUS_TRAP_CSS = """
.slides-container *:focus-visible{outline:2px solid var(--accent,#14b8a6);outline-offset:3px;border-radius:3px}
.slides-container *:focus:not(:focus-visible){outline:none}
.skip-link:focus{position:static;clip:auto;width:auto;height:auto;overflow:visible;white-space:normal}
"""


def inject_skip_nav(html: str) -> str:
    """Insert skip-nav link as first child of <body>."""
    skip_link = (
        '<a href="#slides" class="skip-nav" tabindex="0">'
        '<span style="position:absolute;width:1px;height:1px;overflow:hidden">跳至主要內容</span>'
        '跳至主要內容</a>'
    )
    return re.sub(r'(<body[^>]*>)', r'\1\n  ' + skip_link, html, count=1, flags=re.IGNORECASE)


def inject_aria_labels(html: str) -> str:
    """
    增強導航按鈕的 aria-label：
    - prevBtn → "上一張投影片"
    - nextBtn → "下一張投影片"
    - fsBtn   → "全螢幕切換"
    """
    html = re.sub(
        r'<button[^>]*id=["\']prevBtn["\'][^>]*>',
        '<button id="prevBtn" aria-label="上一張投影片"',
        html, flags=re.IGNORECASE
    )
    html = re.sub(
        r'<button[^>]*id=["\']nextBtn["\'][^>]*>',
        '<button id="nextBtn" aria-label="下一張投影片"',
        html, flags=re.IGNORECASE
    )
    html = re.sub(
        r'<button[^>]*id=["\']fsBtn["\'][^>]*>',
        '<button id="fsBtn" aria-label="全螢幕切換"',
        html, flags=re.IGNORECASE
    )
    return html


def inject_aria_current(html: str, slides_count: int = 0) -> str:
    """在 active slide 的 role="group" 加上 aria-current="page"。"""
    html = re.sub(
        r'<div class="slide active" role="group"(.*?)>',
        r'<div class="slide active" role="group" aria-current="page"\1>',
        html, flags=re.IGNORECASE
    )
    return html


def inject_aria_live(html: str, slides_count: int = 0) -> str:
    """在 nav counter 區域加入 aria-live="polite" 供螢幕閱讀器即時讀出進度。"""
    # Match: <div class="nav-counter", <span class="nav-counter", or <span class="current"
    patterns = [
        (r'(<(?:div|span) class="nav-counter")', r'\1 aria-live="polite" aria-atomic="true"'),
        (r'(<span class="current")', r'\1 aria-live="polite" aria-atomic="true"'),
    ]
    for pat, repl in patterns:
        if re.search(pat, html, re.IGNORECASE):
            html = re.sub(pat, repl, html, flags=re.IGNORECASE)
            break
    return html


def inject_reduced_motion(html: str) -> str:
    """注入 prefers-reduced-motion CSS media query。"""
    # Find last </style> and inject before it
    if '<style' in html and '</style>' in html:
        css_block = REDUCED_MOTION_CSS.strip()
        return html.replace(
            '</style>',
            '\n/* a11y v5: prefers-reduced-motion */\n' + css_block + '\n</style>',
            1
        )
    # No style block — inject one before </head>
    return html.replace(
        '</head>',
        '<style>\n/* a11y v5: prefers-reduced-motion */\n' + REDUCED_MOTION_CSS + '\n</style>\n</head>',
        1
    )


def inject_focus_trap(html: str) -> str:
    """注入 focus-visible + skip-link CSS。"""
    css_block = FOCUS_TRAP_CSS.strip()
    if '<style' in html and '</style>' in html:
        html = html.replace(
            '</style>',
            '\n/* a11y v5: focus trap */\n' + css_block + '\n</style>',
            1
        )
    else:
        html = html.replace(
            '</head>',
            '<style>\n/* a11y v5: focus trap */\n' + css_block + '\n</style>\n</head>',
            1
        )
    return html


def inject_skip_nav_css(html: str) -> str:
    """注入 skip-nav CSS（如果尚未存在）。"""
    if 'skip-nav' not in html:
        css_block = SKIP_NAV_CSS.strip()
        if '<style' in html and '</style>' in html:
            html = html.replace(
                '</style>',
                '\n/* a11y v5: skip nav */\n' + css_block + '\n</style>',
                1
            )
        else:
            html = html.replace(
                '</head>',
                '<style>\n/* a11y v5: skip nav */\n' + css_block + '\n</style>\n</head>',
                1
            )
    return html


def inject_slide_roles(html: str) -> str:
    """為沒有 role="group" 的 slide 注入 role="group"。"""
    # Only inject on slides that don't already have role="group"
    def _add_role(m):
        attrs = m.group(1)
        if 'role=' in attrs:
            return m.group(0)  # already has role, skip
        return f'<div class="slide"{attrs} role="group">'
    html = re.sub(
        r'<div class="slide([^>]*)>',
        _add_role,
        html, flags=re.IGNORECASE
    )
    return html


def enhance_html(html: str, slides_count: int = 0) -> str:
    """
    一站式 a11y 增強入口。
    依序執行：
      1. skip-nav link + CSS
      2. nav button aria-label
      3. aria-current on active slide
      4. aria-live on nav counter
      5. prefers-reduced-motion CSS
      6. focus-visible CSS
    """
    html = inject_skip_nav(html)
    html = inject_aria_labels(html)
    html = inject_aria_current(html, slides_count)
    html = inject_aria_live(html, slides_count)
    html = inject_reduced_motion(html)
    html = inject_focus_trap(html)
    html = inject_slide_roles(html)
    return html


def a11y_report(html: str) -> dict:
    """
    產出 a11y QA report。
    回傳: { score: int, max: int, checks: [...], contrast: {...} }
    """
    checks = []
    score = 0
    max_score = 0

    # Check 1: skip-nav
    max_score += 1
    has_skip = bool(re.search(r'class=["\']skip-nav["\']', html, re.IGNORECASE))
    checks.append({"name": "skip-nav link", "pass": has_skip, "detail": "Skip to main content link"})
    if has_skip: score += 1

    # Check 2: aria-label on nav buttons
    max_score += 1
    prev_aria = bool(re.search(r'prevBtn[^>]*aria-label', html, re.IGNORECASE))
    next_aria = bool(re.search(r'nextBtn[^>]*aria-label', html, re.IGNORECASE))
    nav_aria_ok = prev_aria and next_aria
    checks.append({"name": "nav-btn aria-label", "pass": nav_aria_ok, "detail": f"prevBtn={prev_aria}, nextBtn={next_aria}"})
    if nav_aria_ok: score += 1

    # Check 3: aria-current on active slide
    has_aria_current = 'aria-current' in html
    has_aria_current = 'aria-current' in html
    checks.append({"name": "aria-current on active slide", "pass": has_aria_current, "detail": "Active slide marked with aria-current=page"})
    if has_aria_current: score += 1

    # Check 4: aria-live region
    max_score += 1
    has_live = 'aria-live' in html
    checks.append({"name": "aria-live region", "pass": has_live, "detail": "Screen reader live region for nav counter"})
    if has_live: score += 1

    # Check 5: prefers-reduced-motion
    max_score += 1
    has_reduced = bool(re.search(r'prefers-reduced-motion', html, re.IGNORECASE))
    checks.append({"name": "prefers-reduced-motion", "pass": has_reduced, "detail": "Animation reduction for motion-sensitive users"})
    if has_reduced: score += 1

    # Check 6: focus-visible
    max_score += 1
    has_focus = bool(re.search(r'focus-visible', html, re.IGNORECASE))
    checks.append({"name": "focus-visible styles", "pass": has_focus, "detail": "Keyboard navigation visible focus indicator"})
    if has_focus: score += 1

    # Check 7: slide role="group" (matches <div class="slide" ... role="group">)
    max_score += 1
    slide_groups = len(re.findall(r'class="slide[^"]*"[^>]*role="group"', html, re.IGNORECASE))
    has_groups = slide_groups > 0
    checks.append({"name": "slide role=group", "pass": has_groups, "detail": f"{slide_groups} slides with role=group"})
    if has_groups: score += 1

    # Check 8: contrast (pass/fail from checker)
    max_score += 1
    contrast = check_contrast(html)
    contrast_pass = len(contrast["fail"]) == 0
    checks.append({"name": "color contrast AA", "pass": contrast_pass, "detail": f"{len(contrast['pass'])} pass, {len(contrast['fail'])} fail"})
    if contrast_pass: score += 1

    return {
        "score": score,
        "max": max_score,
        "pct": round(score / max_score * 100) if max_score > 0 else 0,
        "checks": checks,
        "contrast": contrast,
    }
