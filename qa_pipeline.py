#!/usr/bin/env python3
"""
QA Pipeline — 投影片 HTML 品質檢查腳本
========================================
針對 3 個生產用 HTML 投影片（APS / CRIS / 潤思IMPACTS）
執行結構、內容品質、六大設計原則 (P0)、響應式、字體等多維度檢查。

用法:
  python3 qa_pipeline.py <file1.html> [file2.html ...]
  python3 qa_pipeline.py --dir /path/to/html/

輸出:
  - 終端機格式化報告（繁體中文）
  - JSON 報告檔 (qa_report.json)
"""

import sys
import os
import re
import json
import datetime
import argparse
from collections import defaultdict
from html.parser import HTMLParser


# ═══════════════════════════════════════════════════════════════
# 常數 & 設定
# ═══════════════════════════════════════════════════════════════

BLUR_VARS_REQUIRED = ["--blur-8", "--blur-12", "--blur-24", "--blur-32"]
PLACEHOLDER_PATTERNS = ["添加文本", "在此輸入", "請輸入", "placeholder text", "Lorem ipsum"]
BAD_HREF_PATTERN = re.compile(r'href\s*=\s*["\']\s*(#|javascript:void\(0\))?\s*["\']', re.IGNORECASE)

# ANSI 顏色（終端機輸出）
C_RESET = "\033[0m"
C_PASS = "\033[92m"
C_FAIL = "\033[91m"
C_WARN = "\033[93m"
C_INFO = "\033[96m"
C_BOLD = "\033[1m"
C_DIM = "\033[2m"


# ═══════════════════════════════════════════════════════════════
# HTML 解析器：擷取結構化資訊
# ═══════════════════════════════════════════════════════════════

class SlideParser(HTMLParser):
    """解析 HTML，擷取投影片相關結構資訊。"""

    def __init__(self):
        super().__init__()
        self.slides = []           # [{heading_levels, has_content, ...}]
        self.all_headings = []     # [(level, tag, text_snippet)]
        self.links = []            # [(href, text_snippet)]
        self.style_count = 0
        self.script_count = 0
        self.google_fonts = False
        self.has_base64 = False
        self.has_viewport = False
        self.has_doctype = False
        self.has_charset = False
        self.has_aria = False
        self.has_skip_link = False
        self.has_focus_visible = False
        self.has_active_style = False
        self.has_media_query = False
        self.has_data_stagger = False
        self.has_blur_vars = set()
        self.all_font_weights = set()
        self.placeholders_found = []
        self.empty_tags = []       # [(tag, line_approx)]

        # 狀態追蹤
        self._current_slide = None
        self._in_style = False
        self._style_content = ""
        self._in_slide = False
        self._slide_depth = 0
        self._slide_headings = []
        self._line_count = 0

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        # Doctype 是特殊案例，由原始文字處理
        if tag in ("style",):
            self._in_style = True
            self.style_count += 1
            self._style_content = ""

        if tag == "script":
            self.script_count += 1

        # Viewport meta
        if tag == "meta":
            name = attrs_dict.get("name", "")
            charset = attrs_dict.get("charset", "")
            if name == "viewport":
                self.has_viewport = True
            if charset and "utf-8" in charset.lower():
                self.has_charset = True
            # Also check http-equiv
            if attrs_dict.get("charset", "").upper() == "UTF-8":
                self.has_charset = True

        # Google Fonts
        if tag == "link":
            href = attrs_dict.get("href", "")
            if "fonts.googleapis.com" in href:
                self.google_fonts = True

        # aria-label / skip-link
        if "aria-label" in attrs_dict:
            self.has_aria = True
        if attrs_dict.get("class", "") and "skip-link" in attrs_dict.get("class", ""):
            self.has_skip_link = True

        # Font weights (capture inline style)
        style_attr = attrs_dict.get("style", "")
        fw_match = re.search(r'font-weight:\s*(\d+)', style_attr)
        if fw_match:
            self.all_font_weights.add(int(fw_match.group(1)))

        # Check for data-stagger
        if "data-stagger" in attrs_dict:
            self.has_data_stagger = True

        # Slide detection: class="slide" OR data-i OR role=group with aria-label="slide"
        classes = attrs_dict.get("class", "")
        data_i = attrs_dict.get("data-i")
        role = attrs_dict.get("role", "")
        aria_label = attrs_dict.get("aria-label", "")

        is_slide = (
            "slide" in classes.split()
            or data_i is not None
            or (role == "group" and "slide" in aria_label.lower())
        )

        # Filter out non-slide classes that contain "slide" (like slide-inner, slide-num)
        if is_slide and classes:
            class_list = classes.split()
            # Check if any class is exactly "slide" or starts with "slide " (combined classes)
            has_exact_slide = "slide" in class_list
            # For <section class="slide ..."> or <div class="slide" ...>
            if not has_exact_slide:
                # Might be slide--divider, slide-container etc - still a slide
                has_slide_prefix = any(c == "slide" or c.startswith("slide--") or c.startswith("slide-") for c in class_list)
                if has_slide_prefix:
                    is_slide = True
                else:
                    is_slide = False

        if is_slide:
            self._in_slide = True
            self._slide_headings = []
            self._current_slide = {"headings": self._slide_headings}

        # Track headings
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag[1])
            self.all_headings.append((level, tag, ""))
            if self._in_slide:
                self._slide_headings.append(level)

        # Track links
        if tag == "a":
            href = attrs_dict.get("href", "")
            self.links.append((href, ""))

    def handle_endtag(self, tag):
        if tag == "style":
            self._in_style = False
            self._parse_style_block(self._style_content)

        # Detect slide end
        if self._in_slide and tag in ("section", "div", "article"):
            # Only close if we think this might be the slide container
            pass

    def handle_data(self, data):
        text = data.strip()
        if self._in_style:
            self._style_content += data

        # Check for base64
        if "data:image" in data or "base64," in data:
            self.has_base64 = True

        # Check placeholders
        for ph in PLACEHOLDER_PATTERNS:
            if ph.lower() in data.lower():
                self.placeholders_found.append(ph)

    def _parse_style_block(self, content):
        """從 <style> 區塊萃取 CSS 相關資訊。"""
        # blur variables
        for match in re.finditer(r'(--blur-[\w-]+)', content):
            self.has_blur_vars.add(match.group(1))

        # :focus-visible
        if ":focus-visible" in content:
            self.has_focus_visible = True

        # :active or nav-active
        if re.search(r':active|nav-active', content):
            self.has_active_style = True

        # @media
        if "@media" in content:
            self.has_media_query = True

        # font-weight in CSS rules
        for match in re.finditer(r'font-weight\s*:\s*(\d+)', content):
            self.all_font_weights.add(int(match.group(1)))

        # data-stagger in CSS (transition-delay based stagger)
        if "data-stagger" in content or "[data-stagger" in content:
            self.has_data_stagger = True


# ═══════════════════════════════════════════════════════════════
# 後處理：正則補強（處理 HTMLParser 無法解析的部分）
# ═══════════════════════════════════════════════════════════════

def post_process(raw_html, parser):
    """用正則表達式補強 HTMLParser 結果。"""
    # Doctype
    if re.match(r'\s*<!DOCTYPE\s+html', raw_html, re.IGNORECASE):
        parser.has_doctype = True

    # Charset (meta charset="UTF-8")
    if re.search(r'charset\s*=\s*["\']?UTF-8', raw_html, re.IGNORECASE):
        parser.has_charset = True

    # viewport
    if re.search(r'name\s*=\s*["\']viewport["\']', raw_html, re.IGNORECASE):
        parser.has_viewport = True

    # base64 (exclude favicon — inline SVG favicons are acceptable)
    if re.search(r'(?:data:image/(?!svg)|base64,)', raw_html):
        parser.has_base64 = True

    # Empty tags: <p></p>, <p> </p>, <h1></h1> etc.
    for match in re.finditer(r'<(p|h[1-6])\b[^>]*>\s*</\1>', raw_html, re.IGNORECASE):
        tag = match.group(1)
        line_num = raw_html[:match.start()].count('\n') + 1
        parser.empty_tags.append((tag, line_num))

    # Google Fonts
    if "fonts.googleapis.com" in raw_html:
        parser.google_fonts = True

    # Bad hrefs: href="" or href="#" or href="javascript:void(0)"
    for match in re.finditer(BAD_HREF_PATTERN, raw_html):
        parser.links.append((match.group(0), "INVALID"))

    # Placeholders
    for ph in PLACEHOLDER_PATTERNS:
        if ph in raw_html:
            if ph not in parser.placeholders_found:
                parser.placeholders_found.append(ph)

    # aria-label anywhere
    if 'aria-label' in raw_html:
        parser.has_aria = True

    # skip-link
    if 'skip-link' in raw_html:
        parser.has_skip_link = True

    # data-stagger
    if 'data-stagger' in raw_html:
        parser.has_data_stagger = True

    # font-weight counts in full raw (including inline)
    for match in re.finditer(r'font-weight\s*:\s*(\d+)', raw_html):
        parser.all_font_weights.add(int(match.group(1)))

    # Count slides: look for patterns
    slide_patterns = [
        r'<section\s+[^>]*class="[^"]*slide\b',   # <section class="slide ...">
        r'<div\s+[^>]*class="[^"]*slide\b[^"]*"',  # <div class="slide ...">
        r'class="[^"]*\bslide\b[^"]*"',             # Any tag with class containing "slide"
    ]

    return parser


def count_slides(raw_html, parser):
    """
    計算投影片數量。使用精確 pattern 匹配：
    - <section class="slide" ...>  (APS / CRIS)
    - <div class="slide" role="group" aria-label="slide N">  (RUNS)
    排除 slide-inner, slide-num, slide-title, slides-container 等非投影片 class。
    """
    # Pattern: class="slide" 作為獨立詞（前後為空白/引號/結尾）而非複合 class 的一部份
    # 匹配: class="slide" 或 class="slide xxx" 但不匹配 class="slide-inner"
    # v1.1: 若 slide count=0，fallback 到 slide-inner 計數
    slide_pattern = re.compile(
        r'class="slide(?:\s|")',  # "slide" followed by space or closing quote
        re.IGNORECASE
    )
    matches = slide_pattern.findall(raw_html)
    slide_count = len(matches)
    
    # Fallback: if no standalone "slide" classes, count slide-inner blocks
    if slide_count == 0:
        inner_pattern = re.compile(r'class="slide-inner"', re.IGNORECASE)
        inner_matches = inner_pattern.findall(raw_html)
        if inner_matches:
            # slide-inner is nested inside slide containers; count = slides
            slide_count = len(inner_matches)
    
    return slide_count


# ═══════════════════════════════════════════════════════════════
# 檢查函式（每個檢查回傳 (status, message, detail)）
# ═══════════════════════════════════════════════════════════════

def check_doctype(parser):
    if parser.has_doctype:
        return ("PASS", "HTML5 doctype 存在")
    return ("FAIL", "缺少 <!DOCTYPE html>")

def check_charset(parser):
    if parser.has_charset:
        return ("PASS", "charset=UTF-8 已宣告")
    return ("FAIL", "未宣告 charset=UTF-8")

def check_viewport(parser):
    if parser.has_viewport:
        return ("PASS", "viewport meta 標籤存在")
    return ("WARN", "缺少 viewport meta 標籤")

def check_slides(raw_html, parser):
    count = count_slides(raw_html, parser)
    if count > 0:
        return ("PASS", f"偵測到 {count} 張投影片")
    return ("FAIL", "無法偵測投影片（無 slide class/slide-inner/data-i）")

def check_style_blocks(parser):
    return ("INFO", f"{parser.style_count} 個 <style> 區塊")

def check_script_blocks(parser):
    return ("INFO", f"{parser.script_count} 個 <script> 區塊")

def check_base64(parser):
    if parser.has_base64:
        return ("FAIL", "❌ 發現 base64 圖片！應使用外部檔案")
    return ("PASS", "無 base64 內嵌圖片")

def check_google_fonts(parser):
    if parser.google_fonts:
        return ("PASS", "已載入 Google Fonts CDN")
    return ("WARN", "未使用 Google Fonts（可能使用系統字體）")

def check_links(raw_html, parser):
    """檢查所有 <a href> 是否有效。"""
    # 收集所有 href 屬性值
    all_hrefs = re.findall(r'<a\s+[^>]*href\s*=\s*["\']([^"\']*)["\']', raw_html, re.IGNORECASE)
    bad = []
    for href in all_hrefs:
        href_stripped = href.strip()
        if (not href_stripped
            or href_stripped == "#"
            or href_stripped.startswith("javascript:void(0)")
            or href_stripped.startswith("javascript:;")):
            bad.append(href_stripped)

    if not all_hrefs:
        return ("INFO", "無 <a> 連結（可能僅使用按鈕導航）")
    if bad:
        return ("WARN", f"{len(bad)} 個無效連結: {bad[:3]}{'...' if len(bad) > 3 else ''}")
    return ("PASS", f"所有 {len(all_hrefs)} 個連結有效")

def check_empty_tags(parser):
    if parser.empty_tags:
        tags_str = ", ".join(f"<{t}>" for t, _ in parser.empty_tags[:5])
        return ("WARN", f"{len(parser.empty_tags)} 個空白標籤: {tags_str}")
    return ("PASS", "無空白 <p> 或 <h1>-<h4> 標籤")

def check_placeholders(parser):
    if parser.placeholders_found:
        return ("FAIL", f"發現佔位文字: {parser.placeholders_found}")
    return ("PASS", "無佔位文字（如「添加文本」）")

def check_heading_hierarchy(raw_html, parser):
    """
    P0-1: 語義層次 — 檢查投影片內容中的標題層級不跳級。
    支援: <section class="slide"> (APS/CRIS), <div class="slide" role="group"> (RUNS),
    以及 RUNS 的單行 div 結構。
    """
    # 找出所有 slide 區塊 — 使用精確 class="slide" 匹配
    # 按 slide 開頭標記分割原始 HTML
    slide_split = re.split(
        r'(?=<(?:section|div)\s+[^>]*class="slide(?:\s|")[^>]*>)',
        raw_html, flags=re.IGNORECASE
    )
    slide_blocks = slide_split[1:]  # 跳過第一個分割之前的內容

    if not slide_blocks:
        return ("INFO", "無投影片區塊可檢查標題層級")

    issues = []
    for i, block in enumerate(slide_blocks):
        headings = re.findall(r'<(h[1-6])\b[^>]*>', block, re.IGNORECASE)
        levels = [int(h[1]) for h in headings]
        if not levels:
            continue

        # 檢查是否跳級 (例如 h2 → h4 跳過 h3)
        prev = levels[0]
        for curr in levels[1:]:
            if curr > prev + 1:
                issues.append(f"投影片 #{i+1}: {headings[0]} → {headings[levels.index(curr)]}")
                break
            prev = curr

    if issues:
        return ("FAIL", f"標題層級跳級: {'; '.join(issues[:3])}")

    # 檢查是否有任何 slide 含有 heading
    has_any_heading = any(
        re.search(r'<(h[1-6])\b[^>]*>', block, re.IGNORECASE)
        for block in slide_blocks
    )
    if not has_any_heading:
        return ("INFO", "投影片中無標題標籤")

    return ("PASS", "標題層級正確（無跳級）")

def check_blur_vars(parser):
    """P0-2: Blur — 檢查 --blur-* CSS 變數。"""
    missing = [v for v in BLUR_VARS_REQUIRED if v not in parser.has_blur_vars]
    if not missing:
        return ("PASS", f"所有 blur 變數已定義: {', '.join(sorted(parser.has_blur_vars))}")
    if parser.has_blur_vars:
        return ("WARN", f"部分 blur 變數缺失: {missing}（現有: {sorted(parser.has_blur_vars)}）")
    return ("FAIL", "未定義任何 --blur-* CSS 變數")

def check_data_stagger(parser):
    """P0-3: Timing/Stagger — 檢查 data-stagger 屬性。"""
    if parser.has_data_stagger:
        return ("PASS", "data-stagger 屬性存在")
    return ("FAIL", "缺少 data-stagger 屬性（元素無進場延遲）")

def check_focus_visible(parser):
    """P0-4: Focus — 檢查 :focus-visible 規則。"""
    if parser.has_focus_visible:
        return ("PASS", ":focus-visible 樣式規則存在")
    return ("FAIL", "缺少 :focus-visible 樣式規則")

def check_active_style(parser):
    """P0-5: Active — 檢查 :active 或 nav-active 樣式。"""
    if parser.has_active_style:
        return ("PASS", ":active / nav-active 樣式規則存在")
    return ("FAIL", "缺少 :active 或 nav-active 樣式規則")

def check_a11y(parser):
    """P0-6: A11y — 檢查 skip-link 或 aria-label。"""
    if parser.has_skip_link:
        return ("PASS", "skip-link 存在")
    if parser.has_aria:
        return ("PASS", "aria-label 屬性存在")
    return ("FAIL", "缺少 skip-link 或 aria-label 屬性")

def check_media_query(parser):
    """檢查 @media 響應式斷點。"""
    if parser.has_media_query:
        # 計算 @media 區塊數量
        return ("PASS", "至少 1 個 @media 響應式斷點")
    return ("FAIL", "無 @media 查詢（非響應式）")

def check_viewport_meta(parser):
    """檢查 viewport meta 是否正確。"""
    if parser.has_viewport:
        return ("PASS", "viewport meta 正確")
    return ("WARN", "缺少 viewport meta")

def check_font_weights(parser):
    """檢查字體粗細層級（至少 300 + 600）。"""
    weights = sorted(parser.all_font_weights)
    has_light = any(w <= 300 for w in parser.all_font_weights)
    has_bold = any(w >= 600 for w in parser.all_font_weights)

    if has_light and has_bold:
        return ("PASS", f"字體粗細充足: {weights}（含 300/Regular + 600/Bold）")
    if has_bold:
        return ("WARN", f"缺少輕字重 (≤300)，粗體正常: {weights}")
    if has_light:
        return ("WARN", f"缺少粗字重 (≥600)，輕體正常: {weights}")
    return ("FAIL", f"字體粗細不足: {weights}")


# ═══════════════════════════════════════════════════════════════
# 主分析函式
# ═══════════════════════════════════════════════════════════════

def analyze_html(filepath):
    """
    對單一 HTML 檔案執行完整 QA 檢查。
    回傳 dict: {filename, results: [...], summary: {...}}
    """
    with open(filepath, "r", encoding="utf-8") as f:
        raw_html = f.read()

    parser = SlideParser()
    parser.feed(raw_html)
    post_process(raw_html, parser)

    filename = os.path.basename(filepath)

    # 執行所有檢查
    checks = []

    # ── 結構檢查 ──
    checks.append(("結構", "HTML5 Doctype", *check_doctype(parser)))
    checks.append(("結構", "Charset UTF-8", *check_charset(parser)))
    checks.append(("結構", "Viewport Meta", *check_viewport(parser)))
    checks.append(("結構", "投影片數量", *check_slides(raw_html, parser)))
    checks.append(("結構", "<style> 區塊", *check_style_blocks(parser)))
    checks.append(("結構", "<script> 區塊", *check_script_blocks(parser)))

    # ── 內容品質 ──
    checks.append(("內容", "Base64 檢查", *check_base64(parser)))
    checks.append(("內容", "Google Fonts", *check_google_fonts(parser)))
    checks.append(("內容", "連結有效性", *check_links(raw_html, parser)))
    checks.append(("內容", "空白標籤", *check_empty_tags(parser)))
    checks.append(("內容", "佔位文字", *check_placeholders(parser)))

    # ── P0 六大原則 ──
    checks.append(("P0-1", "語義層次 (Heading)", *check_heading_hierarchy(raw_html, parser)))
    checks.append(("P0-2", "Blur 變數", *check_blur_vars(parser)))
    checks.append(("P0-3", "Timing/Stagger", *check_data_stagger(parser)))
    checks.append(("P0-4", "Focus 可見", *check_focus_visible(parser)))
    checks.append(("P0-5", "Active 樣式", *check_active_style(parser)))
    checks.append(("P0-6", "A11y 無障礙", *check_a11y(parser)))

    # ── 響應式 ──
    checks.append(("響應式", "@media 斷點", *check_media_query(parser)))
    checks.append(("響應式", "Viewport Meta", *check_viewport_meta(parser)))

    # ── 字體 ──
    checks.append(("字體", "Font-weight 層級", *check_font_weights(parser)))

    # ── 計算分數 ──
    p0_results = [(cat, name, status) for cat, name, status, _ in checks if cat.startswith("P0")]
    quality_results = [(cat, name, status) for cat, name, status, _ in checks if cat in ("內容",)]

    p0_pass = sum(1 for _, _, s in p0_results if s == "PASS")
    p0_total = len(p0_results)
    q_pass = sum(1 for _, _, s in quality_results if s == "PASS")
    q_total = len(quality_results)

    # 整體計分
    all_results = checks
    total_pass = sum(1 for _, _, s, _ in all_results if s == "PASS")
    total_fail = sum(1 for _, _, s, _ in all_results if s == "FAIL")
    total_warn = sum(1 for _, _, s, _ in all_results if s == "WARN")
    total_info = sum(1 for _, _, s, _ in all_results if s == "INFO")

    return {
        "filename": filename,
        "filepath": filepath,
        "filesize_kb": round(len(raw_html) / 1024, 1),
        "slide_count": count_slides(raw_html, parser),
        "results": [
            {"category": cat, "check": name, "status": status, "message": msg}
            for cat, name, status, msg in checks
        ],
        "summary": {
            "p0": {"pass": p0_pass, "total": p0_total, "score": f"{p0_pass}/{p0_total}"},
            "quality": {"pass": q_pass, "total": q_total, "score": f"{q_pass}/{q_total}"},
            "overall": {
                "pass": total_pass, "fail": total_fail, "warn": total_warn, "info": total_info,
                "total": len(checks)
            }
        }
    }


# ═══════════════════════════════════════════════════════════════
# 輸出格式化
# ═══════════════════════════════════════════════════════════════

def status_icon(status):
    """回傳 ANSI 彩色狀態圖示。"""
    icons = {
        "PASS": f"{C_PASS}✓ PASS{C_RESET}",
        "FAIL": f"{C_FAIL}✗ FAIL{C_RESET}",
        "WARN": f"{C_WARN}⚠ WARN{C_RESET}",
        "INFO": f"{C_INFO}ℹ INFO{C_RESET}",
    }
    return icons.get(status, status)


def print_report(all_results):
    """在終端機輸出格式化的 QA 報告。"""
    print()
    print(f"{C_BOLD}{'═' * 70}{C_RESET}")
    print(f"{C_BOLD}  投影片 HTML QA 檢查報告{C_RESET}")
    print(f"  執行時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{C_BOLD}{'═' * 70}{C_RESET}")

    for result in all_results:
        fn = result["filename"]
        fp = result["filepath"]
        ss = result["summary"]

        print(f"\n{C_BOLD}━━━ {fn} ({result['slide_count']} 張投影片, {result['filesize_kb']} KB) ━━━{C_RESET}")
        print(f"{C_DIM}  路徑: {fp}{C_RESET}")

        # 分組輸出
        current_cat = None
        for r in result["results"]:
            cat = r["category"]
            if cat != current_cat:
                current_cat = cat
                print(f"\n  {C_BOLD}── {cat} ──{C_RESET}")

            icon = status_icon(r["status"])
            print(f"    {icon}  {r['check']}: {r['message']}")

        # 摘要
        p0 = ss["p0"]
        q = ss["quality"]
        ov = ss["overall"]

        print(f"\n  {C_BOLD}┌─ 評分摘要 ─────────────────────────────┐{C_RESET}")
        print(f"  {C_BOLD}│{C_RESET} P0 六大原則: {p0['score']} 通過")
        print(f"  {C_BOLD}│{C_RESET} 內容品質:    {q['score']} 通過")
        print(f"  {C_BOLD}│{C_RESET} 總計:        {ov['pass']} PASS / {ov['fail']} FAIL / {ov['warn']} WARN / {ov['info']} INFO")
        print(f"  {C_BOLD}└──────────────────────────────────────────┘{C_RESET}")

    # 總結
    print(f"\n{C_BOLD}{'═' * 70}{C_RESET}")
    total_p0_pass = sum(r["summary"]["p0"]["pass"] for r in all_results)
    total_p0 = sum(r["summary"]["p0"]["total"] for r in all_results)
    total_q_pass = sum(r["summary"]["quality"]["pass"] for r in all_results)
    total_q = sum(r["summary"]["quality"]["total"] for r in all_results)
    total_all_pass = sum(r["summary"]["overall"]["pass"] for r in all_results)
    total_all_fail = sum(r["summary"]["overall"]["fail"] for r in all_results)
    total_all_warn = sum(r["summary"]["overall"]["warn"] for r in all_results)

    print(f"{C_BOLD}  全部檔案總計{C_RESET}")
    print(f"  P0: {total_p0_pass}/{total_p0}  |  品質: {total_q_pass}/{total_q}  |  "
          f"{total_all_pass} PASS / {total_all_fail} FAIL / {total_all_warn} WARN")
    print(f"{C_BOLD}{'═' * 70}{C_RESET}")
    print()


# ═══════════════════════════════════════════════════════════════
# CLI 入口
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="投影片 HTML QA 檢查工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  python3 qa_pipeline.py file1.html file2.html
  python3 qa_pipeline.py --dir /path/to/html/
  python3 qa_pipeline.py *.html --output report.json
        """
    )
    parser.add_argument("files", nargs="*", help="HTML 檔案路徑")
    parser.add_argument("--dir", "-d", help="掃描目錄中所有 .html 檔案")
    parser.add_argument("--output", "-o", default="qa_report.json", help="JSON 報告輸出路徑 (預設: qa_report.json)")

    args = parser.parse_args()

    # 收集檔案
    filepaths = list(args.files)

    if args.dir:
        dir_path = os.path.abspath(args.dir)
        if not os.path.isdir(dir_path):
            print(f"錯誤: 目錄不存在 — {dir_path}", file=sys.stderr)
            sys.exit(1)
        for f in sorted(os.listdir(dir_path)):
            if f.endswith(".html") or f.endswith(".htm"):
                filepaths.append(os.path.join(dir_path, f))

    if not filepaths:
        print("錯誤: 請提供至少一個 HTML 檔案或使用 --dir 指定目錄", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    # 檢查檔案存在性
    for fp in filepaths:
        if not os.path.isfile(fp):
            print(f"錯誤: 檔案不存在 — {fp}", file=sys.stderr)
            sys.exit(1)

    # 分析所有檔案
    all_results = []
    for fp in filepaths:
        try:
            result = analyze_html(fp)
            all_results.append(result)
        except Exception as e:
            print(f"{C_FAIL}分析失敗: {fp} — {e}{C_RESET}", file=sys.stderr)

    if not all_results:
        print("無檔案可分析", file=sys.stderr)
        sys.exit(1)

    # 輸出終端機報告
    print_report(all_results)

    # 輸出 JSON 報告
    report = {
        "report_title": "投影片 HTML QA 檢查報告",
        "generated_at": datetime.datetime.now().isoformat(),
        "files_analyzed": len(all_results),
        "results": all_results
    }
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"{C_INFO}JSON 報告已輸出至: {os.path.abspath(args.output)}{C_RESET}\n")


if __name__ == "__main__":
    main()