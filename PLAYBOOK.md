# PPT → HTML 投影片轉換 Playbook

> **版本**: v4.0  
> **最後更新**: 2026-05-20  
> **適用對象**: AI agent / 開發者，零背景即可產出合格 HTML  
> **基於**: 3 輪迭代（v1 → v2 → v3），3 份 PPT（APS AI Agent 10 張 / CRIS IMPACTs 28 張 / 潤思IMPACTS 51 張）  
> **本版新增**: Sprint Retrospective · 架構全景 · Onboarding Guide · Lessons Learned

---

## 目錄

1. [概述](#1-概述)
2. [PPT 提取策略](#2-ppt-提取策略)
3. [結構映射規則](#3-結構映射規則)
4. [六大原則合規清單](#4-六大原則合規清單)
5. [CSS 慣例 — Golden Reference](#5-css-慣例--golden-reference)
6. [QA 檢查清單](#6-qa-檢查清單)
7. [常見陷阱與對策](#7-常見陷阱與對策)
8. [部署與交付](#8-部署與交付)
9. [Sprint Retrospective — 2026-05-20 Power Squad](#9-sprint-retrospective--2026-05-20-power-squad)
10. [架構全景圖](#10-架構全景圖)
11. [Onboarding Guide — 30 分鐘上手指南](#11-onboarding-guide--30-分鐘上手指南)
12. [Lessons Learned](#12-lessons-learned)
13. [演進路線圖](#13-演進路線圖)

---

## 1. 概述

### 1.1 目的

將 PowerPoint (.pptx) 檔案轉換為**單一、自包含、企業級品質**的 HTML 投影片。

### 1.2 目標品質

- 企業簡報等級，非技術展示
- 完全遵守「六大原則」（一畫面一訊息 / Timing 階梯 / 留白即語言 / 約束創造品質 / 材質層次 / 字體對比）
- 自包含單一 HTML，無需外部 CSS/JS 檔案
- 支援鍵盤、觸控、滾輪導航

### 1.3 工具鏈

| 階段 | 工具 | 用途 |
|------|------|------|
| 提取 | `python-pptx` | 從 PPTX 提取文字、表格、圖片 |
| 結構化 | 自訂 Python 腳本 | 輸出為 JSON 中間格式（slides + 內容） |
| 渲染 | HTML/CSS/JS | 最終產出，手寫或 Python 模板生成 |

### 1.4 輸出規格

```
單一 .html 檔案
檔案大小: 30–80 KB（無 base64 圖片）
行數: 500–1500 行
圖片: 外部 URL 或相對路徑（images/ 目錄）
字體: Google Fonts CDN（3 個字體家族）
```

---

## 2. PPT 提取策略

### 2.1 使用 python-pptx 提取文字

```python
from pptx import Presentation

prs = Presentation("input.pptx")
for i, slide in enumerate(prs.slides):
    for shape in slide.shapes:
        if shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                text = para.text.strip()
                if text:
                    # 記錄文字 + 字體樣式
                    pass
```

### 2.2 提取重點

| 項目 | 方法 | 注意 |
|------|------|------|
| 文字內容 | `shape.text_frame.paragraphs` | 保留換行、層級 |
| 表格 | `shape.table` | 逐格提取，保留行列結構 |
| 圖片 | `shape.image` | 存為外部 PNG/JPG，不內嵌 base64 |
| 字體資訊 | `run.font.name`, `run.font.size` | 僅作參考，輸出時改用 Google Fonts |
| 顏色 | `run.font.color.rgb` | 僅作參考，輸出時用設計代幣 |

### 2.3 常見陷阱

- **字體編碼問題**: PPT 字體名可能含 `+mn-ea`（東亞字體後綴），提取後須清理
- **佔位符文字**: `"添加文本"`、`"单击此处添加标题"` — 必須過濾掉
- **版權圖片**: PPT 內嵌的 stock photo 可能有版權，改用示意圖或自製圖
- **空文字框**: PPT 常有空白 `shape`，過濾 `text.strip() == ""` 的內容
- **群組形狀**: `shape.shape_type == MSO_SHAPE_TYPE.GROUP` 需要遞迴處理子元素

### 2.4 推薦工作流

```
PPTX → extract_text.py → slides_raw.json → curate by human/agent → slides_v3.json → build_html.py → output.html
```

重點：**不要直接 PPTX → HTML**。中間的 JSON 層讓你可以人工校對內容、調整結構、補充缺失資訊。

### 2.5 JSON 中間格式規範

```json
[
  {"s": "cover", "t": "標題", "st": "副標題"},
  {"s": "section", "n": "01", "t": "章節名稱"},
  {
    "t": "投影片標題",
    "h": "重點標語（可選）",
    "b": "內文段落",
    "items": [
      {"h": "卡片標題", "ls": ["條目1", "條目2"]}
    ],
    "twocol": [
      {"side": "left", "h": "左欄標題", "ls": ["..."], "color": "red"},
      {"side": "right", "h": "右欄標題", "ls": ["..."], "color": "green"}
    ],
    "imgs": ["slide01.png"]
  },
  {"s": "thanks", "t": "Thank You", "st": "公司名稱"}
]
```

---

## 3. 結構映射規則

### 3.1 投影片類型 → HTML 結構

| PPT 內容 | HTML 標籤 | CSS class | 說明 |
|----------|-----------|-----------|------|
| 封面 | `<div class="slide cover-slide">` | `.cover-slide` | 全版背景、大標題、裝飾光暈 |
| 章節分隔 | `<div class="section-break">` | `.section-break` | 深色背景、巨大淡色編號、章節標題 |
| 一般內容 | `<div class="slide">` | `.slide` | 標準內容頁，含 padding |
| 結尾感謝 | `<div class="slide thanks-slide">` | `.thanks-slide` | 感謝頁，居中大標題 |
| 標題 | `<h2 class="slide-title">` | `.slide-title` | Playfair Display |
| 副標題 | `<p class="slide-sub">` | `.slide-sub` | 較小、較淡 |
| 重點標語 | `<h3 class="slide-headline">` | `.slide-headline` | 中層級標題 |
| 內文 | `<p class="slide-body">` | `.slide-body` | 一般段落 |
| 特點清單 | `<div class="items-grid">` | `.items-grid` | 2-3 欄卡片網格 |
| 卡片 | `<div class="item-card">` | `.item-card` | 半透明背景卡片 |
| 雙欄對比 | `<div class="twocol">` | `.twocol` | 左挑戰/右方案 |
| 統計數字 | `<span class="stat-num">` | `.stat-num` | 大字體數字 |
| 圖片 | `<img class="ci" src="images/...">` | `.ci` | 置中圖片，含圓角邊框 |

### 3.2 結構決策樹

```
投影片內容是什麼？
├── 封面？ → cover-slide（全版、裝飾背景、大標）
├── 章節分隔？ → section-break（深色、大編號）
├── 感謝頁？ → thanks-slide（居中、極簡）
└── 一般內容？
    ├── 有雙欄對比（挑戰/方案）？ → twocol 佈局
    ├── 有多個要點？ → items-grid（2-3 欄卡片）
    ├── 有圖片？ → ci（單圖）/ ig2（雙圖）/ igm（多圖）
    └── 純文字？ → slide-body
```

### 3.3 封面結構範例

```html
<div class="slide cover-slide" data-stagger="0">
  <div class="cover-bg">
    <div class="cover-orb1"></div>
    <div class="cover-orb2"></div>
    <div class="cover-grid"></div>
    <div class="cover-vignette"></div>
  </div>
  <div class="cover-inner">
    <span class="cover-tag">智能製造解決方案</span>
    <h1 class="cover-title">IMPACTs APS 智能先進排程系統</h1>
    <p class="cover-sub">大連潤思科技 · 離散型製造行業智能製造解決方案商</p>
    <div class="cover-rule"></div>
  </div>
</div>
```

### 3.4 章節分隔結構範例

```html
<div class="section-break" data-stagger="0">
  <div class="section-inner">
    <span class="section-num">03</span>
    <h2 class="section-title">目標客戶</h2>
  </div>
</div>
```

---

## 4. 六大原則合規清單

> 每一項都有具體實作要求。交付前逐項確認。

### 4.1 🎯 一畫面一訊息

| # | 要求 | 實作 | 檢查方法 |
|---|------|------|----------|
| 1 | 每張投影片最多 3 個訊息塊 | direct children ≤ 3 個有意義區塊 | 目視檢查：能一句話總結這張投影片嗎？ |
| 2 | 每張投影片可用一句話總結 | 標題即核心訊息 | 盲測：只看標題是否能理解 |
| 3 | 無資訊過載 | 內文 ≤ 80 字（中文） | `grep -oP '[\x{4e00}-\x{9fff}]' | wc -l` |

**反面案例**: 一張投影片同時講 5 個產業 + 3 個功能 + 2 個案例 → 拆成多張。

### 4.2 🎵 Timing 階梯

| # | 要求 | 實作 | 檢查方法 |
|---|------|------|----------|
| 4 | 子元素依序進場 | `data-stagger` 屬性 + CSS transition-delay | 目視：元素逐個出現 |
| 5 | 階梯間隔 80ms | `nth-child(2) 80ms, (3) 160ms...` | `grep 'nth-child.*transition-delay'` |
| 6 | 動畫 ≤ 400ms | `--t-slow: 400ms` 為最大值 | `grep -oE '[0-9]+ms' \| sort -n \| tail -1` |
| 7 | 僅 fade + translateY | `@keyframes` 只用 `opacity` + `transform: translateY` | `grep '@keyframes'` 後目視內容 |

```css
/* 正確實作 */
.slide.active .in:nth-child(1) { animation-delay: 0ms; }
.slide.active .in:nth-child(2) { animation-delay: 80ms; }
.slide.active .in:nth-child(3) { animation-delay: 160ms; }
.slide.active .in:nth-child(4) { animation-delay: 240ms; }
.slide.active .in:nth-child(5) { animation-delay: 320ms; }

@keyframes slideIn {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}
```

### 4.3 ⬜ 留白即語言

| # | 要求 | 實作 | 檢查方法 |
|---|------|------|----------|
| 8 | 章節分隔頁使用極深背景 | `.section-break` 使用 `var(--c-bg)` | `grep 'section-break'` |
| 9 | 內容區有充足 padding | 桌面 ≥ 2rem，手機 ≥ 0.8rem | 目視 |
| 10 | 元素間距使用 8px grid | 所有間距來自 `--s1`~`--s10` 變數 | `grep '--s[0-9]'` |
| 11 | 章節分隔編號巨大但極淡 | `font-size: 6rem; opacity: .12` | 目視 |

### 4.4 🔒 約束創造品質

| # | 要求 | 實作 | 檢查方法 |
|---|------|------|----------|
| 12 | 僅允許 `@keyframes slideIn` 和 `springIn` | 無其他 keyframes 名稱 | `grep '@keyframes'` |
| 13 | 禁止 bounce / rotate / fly / zoom | 代碼中不出現這些關鍵字 | `grep -iE 'bounce\|rotate\|fly\|zoom'` |
| 14 | Spring 動畫最多 2% overshoot | `cubic-bezier(0.34, 1.56, 0.64, 1)` | 目視：無明顯彈跳 |
| 15 | 過渡使用 `var(--ease)` | `transition: ... var(--ease)` | `grep 'var(--ease)'` |

```css
/* 允許的動畫 */
@keyframes slideIn {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes springIn {
  0%   { opacity: 0; transform: scale(0.97) translateY(8px); }
  60%  { opacity: 1; transform: scale(1.01) translateY(-2px); }
  100% { opacity: 1; transform: scale(1) translateY(0); }
}
```

### 4.5 🖤 材質層次

| # | 要求 | 實作 | 檢查方法 |
|---|------|------|----------|
| 16 | 至少有 3 層背景深度 | `--c-bg` > `--bg-card` > `--bg-mesh` | `grep -c '--c-bg\|--bg-'` |
| 17 | Glassmorphism 效果 | 至少一處 `backdrop-filter: blur()` | `grep 'backdrop-filter'` |
| 18 | Mesh gradient 背景 | 至少一處 `radial-gradient` | `grep -c 'radial-gradient'` |
| 19 | 漸變文字效果 | 至少一處 `background-clip: text` | `grep 'background-clip: text'` |

```css
/* 材質層次範例 */
--c-bg:    #06080d;   /* 最深：頁面底色 */
--bg-card: rgba(255,255,255,.03); /* 卡片：半透明浮起 */
--bg-mesh:
  radial-gradient(ellipse 70% 60% at 80% 20%, rgba(99,91,255,.07), transparent 70%),
  radial-gradient(ellipse 50% 60% at 20% 80%, rgba(79,142,247,.05), transparent 70%);
```

### 4.6 🔤 字體對比階梯

| # | 要求 | 實作 | 檢查方法 |
|---|------|------|----------|
| 20 | 3 個 Google Fonts | Playfair Display + Inter + Noto Sans SC | `grep -c 'fonts.googleapis.com'` |
| 21 | Display 用於封面/章節標題 | `font-family: 'Playfair Display'` | `grep 'Playfair Display'` |
| 22 | Heading 用於卡片標題 | `font-family: 'Inter'` | `grep "'Inter'"` |
| 23 | Body 用於內文 | `font-family: 'Noto Sans SC'` | `grep 'Noto Sans SC'` |
| 24 | 至少 3 級 font-weight | 300(Light) / 400(Regular) / 600(Semibold) / 700(Bold) | 目視 |
| 25 | Display font-size ≥ 2rem | `--text-display-1: clamp(2rem, 5vw, 3.6rem)` | `grep '--text-display\|--display'` |

```css
/* 角色分配 */
/* Display — 封面大標、章節標題 */
.cover-title { font-family: 'Playfair Display', serif; font-weight: 800; }
.section-title { font-family: 'Playfair Display', serif; font-weight: 700; }

/* Heading — 卡片標題、區塊標題 */
.item-card h4 { font-family: 'Inter', sans-serif; font-weight: 600; }

/* Body — 內文段落 */
.slide-body { font-family: 'Inter', 'Noto Sans SC', sans-serif; font-weight: 400; }
```

---

## 5. CSS 慣例 — Golden Reference

> 這是從 3 輪迭代中提煉的規範 CSS 結構。新產出的 HTML 必須符合此結構。

### 5.1 設計代幣（Design Tokens）

```css
:root {
  /* ═══ 色彩：深色材質層次 ═══ */
  --c-bg:       #06080d;    /* 最深底色 */
  --c-bg2:      #0f172a;    /* 次要背景 */
  --c-bg3:      #1e293b;    /* 卡片背景 */
  --c-surface:  rgba(255,255,255,.04);  /* 卡片浮層 */
  --c-surface2: rgba(255,255,255,.07);  /* hover 浮層 */
  --c-glass:    rgba(6,8,13,.65);       /* 導航欄毛玻璃 */
  --c-border:   rgba(255,255,255,.08);   /* 分割線 */

  /* ═══ Accent 色（依專案主題選擇） ═══ */
  --c-teal:     #14b8a6;    /* Teal 系統 */
  --c-teal-dim: rgba(20,184,166,.12);
  --c-teal-glow:rgba(20,184,166,.25);
  --c-teal-hot: #2dd4bf;

  /* 或使用 Stripe Violet 系統 */
  --accent:     #635bff;
  --accent-2:   #a78bfa;

  /* ═══ 文字層級 ═══ */
  --c-t1:  rgba(255,255,255,.95);   /* 主要 */
  --c-t2:  rgba(255,255,255,.72);   /* 次要 */
  --c-t3:  rgba(255,255,255,.46);   /* 輔助 */
  --c-t4:  rgba(255,255,255,.28);   /* 禁用/最低 */

  /* ═══ 間距 8px grid ═══ */
  --s1:  0.5rem;   --s2:  1rem;     --s3:  1.5rem;
  --s4:  2rem;     --s5:  2.5rem;   --s6:  3rem;
  --s7:  4rem;     --s8:  5rem;     --s9:  6rem;
  --s10: 8rem;

  /* ═══ 模糊梯度 ═══ */
  --blur-card:  12px;
  --blur-sheet: 24px;
  --blur-modal: 32px;
  --blur-nav:   8px;

  /* ═══ 動畫 ═══ */
  --t-fast: 120ms;
  --t-mid:  240ms;
  --t-slow: 400ms;
  --ease:   cubic-bezier(.16,1,.3,1);

  /* ═══ 圓角 ═══ */
  --r-sm: 4px;  --r-md: 8px;  --r-lg: 12px;  --r-xl: 24px;

  /* ═══ 語義色 ═══ */
  --c-error:   #ef4444;  --c-error-dim:   rgba(239,68,68,.12);
  --c-success: #22c55e;  --c-success-dim: rgba(34,197,94,.12);
  --c-warning: #f59e0b;  --c-warning-dim: rgba(245,158,11,.12);
  --c-info:    #3b82f6;  --c-info-dim:    rgba(59,130,246,.12);
}
```

### 5.2 CSS 區段結構（模組化註解）

每個 `.html` 檔案的 `<style>` 區塊必須用以下註解區隔：

```css
/* ═══════════════════════════════════════
   [00] DESIGN TOKENS — 設計代幣
   ═══════════════════════════════════════ */

/* ═══════════════════════════════════════
   [01] RESET & BASE
   ═══════════════════════════════════════ */

/* ═══════════════════════════════════════
   [02] SLIDE ENGINE — 投影片引擎
   ═══════════════════════════════════════ */

/* ═══════════════════════════════════════
   [03] PROGRESS BAR — 進度條
   ═══════════════════════════════════════ */

/* ═══════════════════════════════════════
   [04] NAVIGATION — 導航
   ═══════════════════════════════════════ */

/* ═══════════════════════════════════════
   [05] COVER — 封面
   ═══════════════════════════════════════ */

/* ═══════════════════════════════════════
   [06] SECTION BREAK — 章節分隔
   ═══════════════════════════════════════ */

/* ═══════════════════════════════════════
   [07] SLIDE CONTENT — 內容區
   ═══════════════════════════════════════ */

/* ═══════════════════════════════════════
   [08] CARDS & GRIDS — 卡片與網格
   ═══════════════════════════════════════ */

/* ═══════════════════════════════════════
   [09] TWO-COL — 雙欄對比
   ═══════════════════════════════════════ */

/* ═══════════════════════════════════════
   [10] IMAGES — 圖片
   ═══════════════════════════════════════ */

/* ═══════════════════════════════════════
   [11] THANKS — 感謝頁
   ═══════════════════════════════════════ */

/* ═══════════════════════════════════════
   [12] RESPONSIVE — 響應式
   ═══════════════════════════════════════ */
```

### 5.3 互動狀態規範

```css
/* Focus ring */
:focus-visible {
  outline: 2px solid var(--c-teal, var(--accent));
  outline-offset: 2px;
}

/* Active state — 按下回饋 */
.item-card:active {
  transform: scale(0.98);
}

/* Disabled state */
.nav-btn:disabled {
  opacity: 0.28;
  cursor: not-allowed;
  filter: grayscale(50%);
}

/* Hover state — 卡片浮起 */
.item-card:hover {
  background: var(--c-surface2);
  border-color: var(--c-teal-dim, rgba(99,91,255,.12));
  transform: translateY(-2px);
}
```

### 5.4 響應式斷點

```css
/* 平板 */
@media (max-width: 1024px) {
  .items-grid { grid-template-columns: 1fr 1fr; }
  .slide { padding: 1.5rem; }
}

/* 手機 */
@media (max-width: 768px) {
  .items-grid { grid-template-columns: 1fr; }
  .twocol { grid-template-columns: 1fr; }
  .slide { padding: 1rem; }
}

/* 小手機 */
@media (max-width: 480px) {
  .slide { padding: 0.6rem; }
  .nav-btn { width: 34px; height: 34px; }
}
```

---

## 6. QA 檢查清單

> 交付前執行以下命令。全部通過才算完成。

### 6.1 檔案完整性

```bash
# 單一 HTML 檔案（無外部 CSS/JS 依賴）
ls -lh output.html

# 檔案大小合理（30–80 KB）
ls -lh output.html | awk '{print $5}'

# 行數合理（500–1500）
wc -l output.html

# DOCTYPE + charset
grep -c '<!DOCTYPE html>' output.html     # → 1
grep -c 'charset=UTF-8' output.html        # → 1（或 charset="UTF-8"）

# viewport meta
grep -c 'viewport' output.html             # → ≥1

# 無 base64
grep -ci 'base64' output.html              # → 0
```

### 6.2 字體系統

```bash
# 3 個 Google Fonts
grep -c 'fonts.googleapis.com' output.html  # → 1（link 含 3 個字體）

# Playfair Display 存在
grep -c 'Playfair Display' output.html      # → ≥1

# Inter 存在
grep -c "'Inter'" output.html               # → ≥1

# Noto Sans SC 存在
grep -c 'Noto Sans SC' output.html          # → ≥1

# 無 PPT 殘留字體
grep -ciE 'calibri|yahei|mn-ea' output.html # → 0
```

### 6.3 內容品質

```bash
# 無佔位符文字
grep -ciE '添加文本|单击此处|點擊此處' output.html  # → 0

# 標題階層合理（至少有 h1 或 h2）
grep -cE '<h[12]' output.html              # → ≥1

# href 非空（如有連結）
grep -oP 'href="[^"]*"' output.html | grep -v 'href=""' | grep -v 'href="#'

# 無 "TODO" 或 "FIXME" 殘留
grep -ciE 'TODO|FIXME' output.html         # → 0
```

### 6.4 CSS 架構

```bash
# CSS 變數 ≥ 20
grep -oE '--[a-z][a-z0-9-]*:' output.html | sort -u | wc -l

# 模組化註解 ≥ 8
grep -c '/\*[-═]' output.html

# 8px spacing grid 存在
grep -oE '--s[1-9]' output.html | sort -u

# backdrop-filter 存在
grep -c 'backdrop-filter' output.html       # → ≥1

# radial-gradient 存在
grep -c 'radial-gradient' output.html       # → ≥1

# 響應式斷點 ≥ 2
grep -c '@media' output.html                # → ≥2
```

### 6.5 六大原則 P0 檢查

```bash
# Timing 階梯：stagger delay 存在
grep -c 'animation-delay\|transition-delay.*nth-child' output.html  # → ≥1

# 動畫 ≤ 400ms
grep -oE '[0-9]+ms' output.html | sort -n | tail -1

# 僅 fade + translateY（無禁止動畫）
grep -iE 'bounceIn|rotateIn|flyIn|zoomIn' output.html  # → 無輸出

# 字體對比：至少 3 種 font-weight
grep -oE 'font-weight: [0-9]+' output.html | sort -u | wc -l  # → ≥3

# 留白：章節分隔存在
grep -c 'section-break\|section-num' output.html  # → ≥1（如有章節頁）

# 材質層次：背景梯度層疊
grep -c 'radial-gradient' output.html       # → ≥1
```

### 6.6 導航功能

```bash
# 鍵盤導航
grep -c 'keydown\|keyup' output.html        # → ≥1

# 觸控滑動
grep -cE 'touchstart|touchend' output.html  # → ≥2

# 滾輪導航
grep -c 'wheel' output.html                 # → ≥1

# 全螢幕
grep -c 'fullscreen\|Fullscreen' output.html # → ≥1

# 進度條
grep -c 'progress\|prog' output.html        # → ≥1
```

---

## 7. 常見陷阱與對策

### 7.1 PPT 字體不存在於 Web

**問題**: PPT 使用 `+mn-ea`、`Calibri`、`Microsoft YaHei` 等字體，Web 上不存在。

**對策**: 一律使用 Google Fonts 替代。

```
PPT 字體          → Web 替代
Calibri           → Inter
Microsoft YaHei   → Noto Sans SC
Arial/Helvetica   → Inter
Times New Roman   → Playfair Display（標題）/ Inter（內文）
+mn-ea (任何)     → Noto Sans SC
```

### 7.2 base64 圖片撐爆檔案

**問題**: `pptx2html.py` 內嵌 base64 圖片導致 HTML 膨脹到 30+ MB。

**對策**: 

```python
# ❌ 錯誤
img_src = f"data:image/png;base64,{base64_data}"

# ✅ 正確
# 1. 提取圖片存為外部檔案
with open(f"images/{image_name}", "wb") as f:
    f.write(image_bytes)
# 2. HTML 使用相對路徑
img_src = f"images/{image_name}"
```

### 7.3 CSS 在自動化編輯中被截斷

**問題**: `sed`/自動化腳本替換 CSS 時可能截斷 `}` 或破壞 `@keyframes` 區塊。

**對策**:
- 永遠用 Python (`str.replace`) 而非 shell `sed` 處理 CSS
- 替換後執行 `grep -c '{'` vs `grep -c '}'` 確認括號對齊
- 替換後在瀏覽器打開確認無報錯

### 7.4 Stagger 變換破壞 CSS 區塊

**問題**: 使用 `data-stagger` 或 `nth-child` transition-delay 時，若元素巢狀過深會影響不該被 stagger 的子元素。

**對策**:
```css
/* ✅ 只 stagger 直接子元素 */
.slide.active > .in:nth-child(1) { animation-delay: 0ms; }

/* ❌ 不要 stagger 所有後代 */
.slide.active .in:nth-child(1) { animation-delay: 0ms; }
```

### 7.5 不同 Agent 產出的 Convention Drift

**問題**: 不同 agent 產出不同 token 命名（`--ink-*` vs `--c-*` vs `--color-*`），合併時衝突。

**對策**:
- 所有產出一律使用本 Playbook 第 5 節的 **Canonical Token 命名**
- 審計時檢查殘留的舊命名：`grep -oE '--ink-[a-z0-9-]+'`
- 跨 agent 協作前，先對齊一份共同的 `:root {}` 區塊

### 7.6 佔位符文字洩漏

**問題**: PPT 空白文字框的預設文字（`"添加文本"`、`"单击此处添加标题"`）直接出現在 HTML 中。

**對策**:
```python
PLACEHOLDER_PATTERNS = [
    "添加文本", "添加标题", "单击此处", "點擊此處",
    "Click to add", "Add text", "Enter text"
]

def is_placeholder(text):
    text = text.strip()
    return any(p in text for p in PLACEHOLDER_PATTERNS) or len(text) < 2
```

### 7.7 圖片路徑不一致

**問題**: 圖片在 `images/`、`html/images/`、`assets/` 等不同目錄。

**對策**: 統一使用 `images/` 目錄，與 HTML 同層或上一層。

```
project/
├── output.html
├── images/
│   ├── slide01.png
│   └── slide02.png
└── PLAYBOOK.md
```

---

## 8. 部署與交付

### 8.1 目錄結構

```
投影片轉換/
├── PLAYBOOK.md              ← 本文件
├── *.pptx                   ← 原始 PPT 檔案
├── slides_v3.json           ← 中間 JSON
├── extract_*.py             ← 提取腳本
├── build_*.py               ← HTML 生成腳本
├── html/                    ← 開發版 HTML（多版本）
├── showcase/                ← 正式交付版 HTML
│   ├── aps-ai-agent.html
│   ├── cris-impacts-carbon.html
│   ├── runs-impacts-aps-partner.html
│   └── images/              ← 所有圖片
├── audit/                   ← 審計報告
└── README.md
```

### 8.2 GitHub Pages 部署

```bash
# 1. 將 showcase/ 內容推到 GitHub
cd showcase/
git init
git add .
git commit -m "Production HTML slides"
git remote add origin git@github.com:user/slides.git
git push -u origin main

# 2. 啟用 GitHub Pages
# Settings → Pages → Source: main branch, / (root) → Save

# 3. 訪問
# https://user.github.io/slides/aps-ai-agent.html
```

### 8.3 離線 ZIP 下載

```bash
# 封裝為自包含 ZIP
cd showcase/
zip -r ../slides-offline.zip *.html images/
# 使用者解壓後直接打開 HTML 即可
```

### 8.4 URL 命名慣例

```
https://user.github.io/slides/<project>-<theme>.html

範例:
  aps-ai-agent.html             ← APS AI Agent 方案
  cris-impacts-carbon.html      ← CRIS IMPACTs 雙碳系統
  runs-impacts-aps-partner.html ← 潤思IMPACTs APS
```

---

## 附錄 A：快速啟動檢查清單

新任務開始時，依序執行：

- [ ] 讀取本 PLAYBOOK.md
- [ ] 確認 PPTX 來源檔案存在
- [ ] 建立 `slides_v3.json` 中間格式
- [ ] 人工校對 JSON 內容（移除佔位符、確認結構）
- [ ] 使用 Canonical Design Tokens（第 5 節）
- [ ] 產出 HTML
- [ ] 執行 QA 檢查清單（第 6 節）
- [ ] 在瀏覽器打開確認
- [ ] 放入 `showcase/` 目錄
- [ ] Git commit + push

---

## 附錄 B：參考檔案

| 檔案 | 用途 |
|------|------|
| `showcase/aps-ai-agent.html` | APS 10 張投影片，Violet accent 主題 |
| `showcase/cris-impacts-carbon.html` | CRIS 28 張投影片，Teal accent 主題 |
| `showcase/runs-impacts-aps-partner.html` | 潤思 51 張投影片，Indigo accent 主題 |
| `html/qa-cheatsheet.html` | 48 項 QA 檢查互動頁面 |
| `audit/aps-v3-audit-report.md` | APS v3 完整審計報告 |
| `pptx2html.py` | v1 自動提取器（含圖片 base64，被 v3 取代） |
| `build_v3_html.py` | v3 HTML 生成器（從 JSON 產出） |


---

# 15. Agent Reliability Protocol（防閒置機制）

> 適用：Power Squad | 生效：Sprint 2 Phase 0+

## 15.1 背景

Sprint 1 retro 發現 Christina 漏取 inbox task 次數偏多（5 次 / 3 天），導致 task 堆積在 inbox 無人接手。為避免 P1/P2 task 被誤判為已完成，需建立自動化 watchdog 機制。

## 15.2 防閒置規則

```
inbox task 指派後 15 分鐘內未被 pick up（狀態仍為 inbox）
→ 自動改派給 Smart 或 Technus（優先輪流）
→ 觸發 board chat 通知：「任務 X 超時，已改派」
```

| 參數 | 值 |
|------|-----|
| 指派超時閾值 | 15 分鐘 |
| 掃描頻率 | 每 10 分鐘 |
| 改派目標 | Smart → Technus → Smart（輪流） |
| 通知方式 | Board chat mention |

## 15.3 Task Watchdog 實現

**Cron job（每 10m）：**
```bash
# /opt/homebrew/lib/node_modules/openclaw/cron job: cris-swat-idle-watchdog
# 或 board-level cron: scan inbox tasks assigned to Christina
# 條件：created_at + 15min < now AND status == inbox AND assignee == Christina
```

**Agent side（board-scan heartbeat 內檢查）：**
```python
# 每次 board-scan 檢查 Christina inbox tasks
# if task.created_at + 15min < now: 觸發 escalation
# POST /boards/{id}/tasks/{task_id}: assignee → Smart/Technus
```

## 15.4 SOP 清單

- [ ] Watchdog cron 部署（Sprint 2 Phase 0）
- [ ] Christina 改派通知測試（假 task 驗證）
- [ ] 監控 7 天後復盤（漏取次數是否下降）
- [ ] 如需降級閾值：15m → 30m（若誤報率過高）

## 15.5 歷史數據

| 日期 | 漏取次數 | 備註 |
|------|---------|------|
| 05-17 ~ 05-19 | 5 次 / 3 天 | Sprint 1 baseline |
| — | — | Sprint 2 目標：≤1 次/週 |

---

---

> **記住**: 本 Playbook 是活的文件。每發現一個新陷阱或更好的做法，就更新它。下次開任務時讀一遍。

---

## 9. Sprint Retrospective — 2026-05-20 Power Squad

> Sprint period: 2026-05-19 ~ 2026-05-20 (16 小時馬拉松)

### 9.1 交付時間線

| 時間 | Agent | 交付 | 影響 |
|------|-------|------|------|
| 05-18 23:00 | Technus | 潤思 v1 HTML → 17MB base64 版 | 起點 P56 ❌ |
| 05-19 01:00 | Christina | CRIS v1 HTML | 開局 |
| 05-19 02:00 | Christina | APS v1 HTML | 三套初始版就位 |
| 05-19 07:00 | Technus | 潤思 v3 — 六大原則重做 | 86% QA |
| 05-19 08:00 | Smart | APS v3 — 六大原則重做 | 12 slides, violet |
| 05-19 10:00 | Christina | CRIS v3 — stuck 8h | 74% QA |
| 05-19 16:00 | Smart | QA Pipeline v1 | 35 項檢查腳本 |
| 05-19 18:00 | Smart | APS v3 19/19 QA → 85% | QA 驅動迭代 |
| 05-19 18:30 | Smart | PLAYBOOK v1 → 795 行/8章節 | 實戰文檔化 |
| 05-19 20:00 | Technus | 潤思 v3.1 展開重排 → 86%→100% | 29/29 QA |
| 05-19 20:30 | Technus | CRIS QA 74%→100% (接手 Christina) | 6 項修復 |
| 05-19 21:00 | Technus | APS → P100 Lighthouse | 56→100 |
| 05-19 21:00 | Technus | CRIS → P100 Lighthouse | 56→100 |
| 05-19 21:00 | Technus | 潤思 → P83 Lighthouse | Performance 達標 |
| 05-19 21:10 | Technus | 三套 README + Landing Page | 448 行展示站 |
| 05-19 21:15 | Technus | QA Cron — 每 4h 掃描告警 | 自動化監控 |
| 05-19 21:40 | Christina | GitHub Pages Deploy SOP | 部署文檔 |
| 05-19 21:43 | Smart | extract-tokens.py | 105 unique token diff |
| 05-19 21:57 | Smart | gen_slides_v4.py — PPTX→JSON→HTML | 505 行自動化管線 |
| 05-19 22:00 | Technus | CI/CD Pipeline — 五 stages | QA→LH→Deploy→Cron |
| 05-19 22:14 | Smart | Showcase Dashboard | 650 行統一一頁展示 |
| 05-19 22:15 | Christina | E2E 整合測試 | 全線掃描 |

**最終統計**: 18 項交付 · 全線 ≥85 · 三套 P100 A11y/BP · CI/CD 五 stages。

### 9.2 關鍵決策記錄

| 決策 | 時機 | 影響 |
|------|------|------|
| PPTX → JSON → HTML 中間層 | v3 初稿 | 讓人工校對成為可能，避免 PPTX 直接渲染 |
| 六大設計原則為基準 | v3 改版 | 統一品質標準，取代「漂亮就好」 |
| QA pipeline 先行 | v3 中期 | 驅動迭代效率：掃描→修復→再掃，閉環 |
| Christina CRIS 8h→Technus 接手 | v3 後期 | 接手策略：同樣 QA 數據庫，30min 修完 |
| Token naming divergence 揭露非統一 | 審計階段 | 記錄但不強制統一，為 v5 設計對齊鋪路 |
| gen_slides_v4 PPTX→JSON→HTML 一條龍 | 自動化階段 | 從手寫 HTML 進化到腳本驅動，可複用於任意 PPTX |
| Dashboard 為門面 | 封頂階段 | 統一一頁展示全部成果，Allen 開箱即用 |

### 9.3 團隊產能分佈

```
Technus  █████████ 9 項（潤思v1→v3, CRIS接手, Lighthouse×3, README×3, Landing, QA cron, CI/CD）
Smart    █████     5 項（APS v3, QA pipeline, PLAYBOOK, extract-tokens, gen_slides_v4, Dashboard）
Christina████       4 項（CRIS v1, APS v1, CRIS v3起手, Deploy SOP, E2E）
```

---

## 10. 架構全景圖

### 10.1 全鏈路圖

```
┌─────────────────────────────────────────────────────────────────────┐
│                        POWER SQUAD PIPELINE                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  [1] PPTX Source                                                     │
│       │                                                              │
│       ▼                                                              │
│  [2] gen_slides_v4.py                                                │
│       │  ├─ pptx_extractor (python-pptx)                             │
│       │  ├─ slide classifier (cover/section/items/twocol/thanks)    │
│       │  ├─ image extractor (保存外部 PNG)                            │
│       │  └─ STRUCTURED JSON → 輸出 slides_v4.json                    │
│       │                                                              │
│       ▼                                                              │
│  [3] JSON Middle Layer (PLAYBOOK §2.5)                               │
│       │  ┌─────────────────────────────────┐                        │
│       │  │ { "s": "cover", "t": "標題" }    │                        │
│       │  │ { "s": "section", "n": "01" }    │                        │
│       │  │ { "t": "...", "items": [...] }    │                        │
│       │  │ { "twocol": [{side}, {side}] }    │                        │
│       │  └─────────────────────────────────┘                        │
│       │                                                              │
│       ▼                                                              │
│  [4] HTML Renderer (renderer.py / gen_slides_v4 builtin)             │
│       │  ├─ Design Tokens → CSS Variables                            │
│       │  ├─ Template Engine → Slide HTML fragments                   │
│       │  ├─ 3 Theme presets (cris/aps/runs)                          │
│       │  └─ Navigation script + Progress bar                         │
│       │                                                              │
│       ▼                                                              │
│  [5] Raw HTML (gen_slides/output/*.html)                             │
│       │                                                              │
│       ├─► [6a] QA Pipeline (qa_pipeline.py)                          │
│       │        35 checks → pass/fail/warn → 分數 %                   │
│       │        ├─ 結構: DOCTYPE, charset, viewport, slide count      │
│       │        ├─ 內容: base64, 佔位符, fonts, heading               │
│       │        ├─ P0: 六大原則合規（6 項致命）                         │
│       │        ├─ P1: CSS 架構（模組化, tokens, backdrop-filter）     │
│       │        ├─ P2: 導航（keyboard, wheel, touch, fullscreen）     │
│       │        └─ 輸出: qa_report.json + .qa_baseline.json            │
│       │                                                              │
│       ├─► [6b] Lighthouse Audit (Chrome headless)                    │
│       │        Performance · Accessibility · Best Practices · SEO    │
│       │        目標: Perf≥55, A11y≥100, BP≥95                        │
│       │                                                              │
│       ├─► [6c] extract-tokens.py                                     │
│       │        掃描 :root block → 分類比對 → diff table               │
│       │        三模式: table | --json | --check (CI gate)            │
│       │                                                              │
│       ▼                                                              │
│  [7] CI/CD Pipeline (.github/workflows/deploy.yml)                   │
│       │  Stage 1: QA scan (qa_pipeline.py)                           │
│       │  Stage 2: Token check (extract-tokens.py --check)            │
│       │  Stage 3: Lighthouse audit                                   │
│       │  Stage 4: gh-pages deploy                                    │
│       │  Stage 5: Board chat notification                            │
│       │                                                              │
│       ▼                                                              │
│  [8] QA Cron (OpenClaw cron job, every 4h)                           │
│       │  run_qa.py → .qa_baseline.json diff → 分數下降→board告警      │
│       │  不變不吵，下降才推訊息                                        │
│       │                                                              │
│       ▼                                                              │
│  [9] Showcase Dashboard (dashboard.html)                             │
│       產品卡片 + QA紅綠燈 + 團隊成績 + 一鍵部署                         │
│                                                                      │
│  [10] GitHub Pages (https://<org>.github.io/<repo>/)                 │
│       四產品線上展示 · 部署文檔 · 版本號管理                             │
└─────────────────────────────────────────────────────────────────────┘
```

### 10.2 工具矩陣

| 工具 | 輸入 | 輸出 | 位置 |
|------|------|------|------|
| `gen_slides_v4.py` | PPTX | HTML + JSON | 根目錄 |
| `qa_pipeline.py` | HTML | qa_report.json | 根目錄 |
| `extract-tokens.py` | HTML×3 | token diff table | 根目錄 |
| `run_qa.py` | 全線掃描 | .qa_baseline.json | cron job |
| `lighthouse` | URL/HTML | JSON report | lighthouse/ |
| `DEPLOY.md` | — | 部署步驟 | docs/ |
| `dashboard.html` | — | 一頁展示 | showcase/ |
| `PLAYBOOK.md` | — | 知識沉澱 | 根目錄 |

### 10.3 設計代幣生態

```
Token Source of Truth (待統一)
├── APS 主題: 自訂 multi-accent (violet/amber/blue/rose/em)
│   ├── color palette: --c-600~950
│   ├── semantic: --c-t1~4, --c-error, --c-success, --c-warning, --c-info
│   └── 40+ unique tokens (最豐富, 含 body/heading/text-display scales)
├── CRIS 主題: Teal Carbon (共享 潤思 基礎)
│   ├── color palette: --ink-50~950
│   ├── semantic: --c-t1~4, --c-teal, --c-teal-dim/hot/glow
│   └── 0 unique tokens (純潤思子集)
└── 潤思 主題: Teal Carbon (canonical)
    ├── color palette: --ink-50~950
    ├── semantic: --c-t1~4, --c-teal, --c-teal-dim/hot/glow
    └── 64 tokens (含 --d-stagger)

共用: 32 tokens (--s1~10, --t-fast/mid/slow, --blur-8/12/24/32, --c-t1~4, --c-error/success/warning/info)
```

---

## 11. Onboarding Guide — 30 分鐘上手指南

### 11.1 目標讀者

- 新加入的 AI agent / 開發者
- 零 CSS 設計背景也可用
- 30 分鐘內產出第一份合格 HTML

### 11.2 快速開始 (15 分鐘)

```bash
# Step 1: 安裝依賴（一次性）
pip3 install python-pptx

# Step 2: 從 PPTX 產出 JSON
cd /path/to/投影片轉換
python3 gen_slides_v4.py --pptx "your.pptx" --json-only > slides.json

# Step 3: 人工校對 JSON
# - 確認 slide type 正確（cover/section/content/items/thanks）
# - 過濾佔位符：「添加文本」「单击此处」
# - 補充缺漏的 imgs 路徑

# Step 4: 生成 HTML
python3 gen_slides_v4.py --pptx "your.pptx" --template cris --output showcase/your.html

# Step 5: 在瀏覽器打開
open showcase/your.html

# Step 6: QA 掃描
python3 qa_pipeline.py showcase/your.html
```

### 11.3 品質門檻 (10 分鐘檢查)

執行以下檢查，全通過才算合格：

```bash
# P0 致命檢查（全部必須 PASS）
grep -c '<!DOCTYPE html>' your.html           # → 1
grep -c 'charset=UTF-8' your.html              # → 1
grep -c 'viewport' your.html                   # → ≥1
grep -ci 'base64' your.html                    # → 0
grep -c 'fonts.googleapis.com' your.html       # → 1 (3 fonts)
grep -ciE 'calibri|yahei|mn-ea' your.html      # → 0
grep -ciE '添加文本|单击此处' your.html        # → 0

# P1 CSS 架構
grep -c 'backdrop-filter' your.html             # → ≥1
grep -c 'radial-gradient' your.html             # → ≥1
grep -c '@media' your.html                      # → ≥2

# P2 導航
grep -c 'keydown' your.html                     # → ≥1
grep -c 'wheel' your.html                       # → ≥1
grep -cE 'touchstart|touchend' your.html        # → ≥2
```

### 11.4 設計決策速查

| 如果… | 則… |
|-------|------|
| 封面頁被分類為 content | 在 JSON 手動改 `"type": "cover"` |
| 章節分隔沒出現 | 在 JSON 對應 slide 加 `"_section": "章節名"` |
| 圖片路徑不對 | 確保圖片在 `images/` 目錄下，HTML 中用 `images/xxx.png` |
| 文字太多 (≥3 訊息塊) | 拆成多張 slide，每張一句核心訊息 |
| 動畫太慢/太快 | 調整 `--t-slow` (預設 400ms) |
| 想要不同主題色 | `--template cris|aps|runs` 或自訂 `design_tokens/*.json` |

### 11.5 進階路線

```
入門 (30min) → 獨立產出合格 HTML
  ↓
中階 (1h)   → 自訂 Design Tokens · 調整 slide classifier
  ↓
進階 (2h)   → CI/CD pipeline · QA cron · 自訂 template
  ↓
大師 (4h)   → gen_slides_v5 spike · Token naming 統一 · v5 設計系統
```

---

## 12. Lessons Learned

### 12.1 ⚠️ Christina 8h CRIS 卡住事件

**現象**: Christina 接手 CRIS v3 時，QA Pipeline 顯示 74% (28≠36 slide count mismatch, 2 media missing, bounce 違規, 缺 1024px 斷點)，但 Christina 在任務上卡了 8 小時無法推進。

**根因**: Agent session 沒有明確的「接手流程」— 同樣的 QA 數據，Technus 30 分鐘修完。差距在於：
1. Christina 缺乏現有的 QA pipeline 腳本和修復先例
2. 沒有明確的「按 QA 報告逐項修→再掃」閉環習慣
3. Agent memory 隔離導致 Christina 看不到 Technus 的修復策略

**對策**:
- ✅ 本 Playbook 第 6 節 QA 清單 = 閉合修復循環
- ✅ 建立「接手 Check-in」protocol：接手任務 → 跑 QA → 對照報告 → 逐項修 → 再跑 QA
- ✅ Onboarding Guide (第 11 節) 解決新 agent 上手問題

### 12.2 ⚠️ slide-inner Regression

**現象**: CRIS IMPACTs HTML 的特色是透過 `.slide-inner` wrapper 包內容，而非直接在 `.slide` 上放內容。造成 `qa_pipeline.py` 的 `count_slides()` 函數只能辨識純 `.slide` class 元素，導致 slide_count = 0，進一步觸發 QA 基準分數計算錯誤。

**根因**: QA pipeline 對 slide 結構的假設太嚴格（只認 `<div class="slide">`，不認 wrapper pattern）。

**修復**: Technus 修正 `qa_pipeline.py` → `count_slides()` 加入對 `.slide-inner` 的兼容解析，重新設定 baseline。

**預防**:
- QA pipeline 的 slide detection 應使用寬鬆匹配：同時檢查 `<div class="slide"` 和 `<div class="slide-inner"`
- 寫入 Playbook 第 7 節陷阱清單

### 12.3 ⚠️ Token Naming 分裂

**現象**: 三套產品使用兩套互不相容的 token naming scheme：
- APS: `--c-600~950` color palette + `--txt-*` typography
- CRIS/潤思: `--ink-50~950` color palette + `--c-t1~4` text colors

**影響**: extract-tokens.py 報告顯示 115 個 missing slots、僅 32 個 common tokens。跨產品設計一致性無法自動驗證。

**處置**: 記錄但不強制統一。v5 設計系統規劃時會定義 canonical token set。

### 12.4 ✅ QA-Driven Development 模式驗證

**成功模式**: QA Pipeline 先行 → 掃描 → 修復 → 再掃描 → 閉環。

```
APS:  19/19 QA → 85% (第一次) → 修復 → 100% (第二次)
CRIS: 74% QA (Christina) → Technus 接手 → 修復 → 100% (30min)
潤思: 86% QA (壓縮版) → 展開重排 → 100% (29/29)
```

**核心洞察**: QA pipeline 的價值不在於「檢查」，在於「驅動迭代」。每次掃描 → 一個具體的修復清單 → 修 → 再掃。這個閉環比任何 code review 都有效率。

### 12.5 ✅ 接手策略

被卡住的任務不應該重做，應該基於同一套 QA 數據接手修復。步驟：

1. 跑 `qa_pipeline.py` → 獲得完整缺失清單
2. 依照 P0 → P1 → P2 優先序逐項修
3. 每完成一項，再跑一次 QA
4. 分數達標後，原 assignee 可做 code review

### 12.6 ✅ 自動化 ROI

| 手動 | 自動化 | 節省 |
|------|--------|------|
| 每次 QA 手動檢查 35 項 | qa_pipeline.py 一鍵掃描 | ~20 min/次 |
| 手寫 HTML 投影片 | gen_slides_v4.py PPTX→HTML | ~2h/套 |
| 手動比對三套 token | extract-tokens.py | ~15 min/次 |
| 手動部署 GitHub Pages | CI/CD pipeline | ~10 min/次 |
| 忘記檢查 → 分數退化 | QA cron 每 4h 告警 | 避免退化 |

---

## 13. 演進路線圖

### v3.0 ✅ (2026-05-20)
- [x] 六大原則合規模板
- [x] QA Pipeline 35 項檢查
- [x] gen_slides_v4 PPTX→JSON→HTML
- [x] Token 提取比對工具
- [x] CI/CD 五 stages
- [x] QA cron 每 4h 掃描
- [x] Showcase Dashboard
- [x] Sprint Retrospective + Lessons Learned

### v4.0 ✅ (2026-05-21)
- [x] Ch17: API Blocker Workaround SOP（task_assignee_mismatch, auth, rate limit）
- [x] Ch18: Cross-Board Collaboration SOP（Power Squad ↔ CRIS SWAT）
- [x] Ch19: Lead Absence Protocol（5-tier escalation, 自主開工範圍, 模板）

### v5.0 (下一階段)
- [ ] Token naming 統一 (`--ds-*` canonical set)
- [ ] 反向解析: 成品 HTML → 結構化 JSON（模板剖析）
- [ ] Lighthouse P55→P85 Performance 修復
- [ ] Dashboard 改為 fetch() 動態讀取 .qa_baseline.json
- [ ] Onboarding 腳本化（一鍵 `setup.sh`）

### v6.0 (PMF 級產品)
- [ ] gen_slides_v5 模板剖析引擎（配色提取/字體適配/佈局比對）
- [ ] 互動投影片 (D3.js charts, dark/light toggle, hover states)
- [ ] OTD 模擬系統原型（Allen 原始目標）
- [ ] 多語言支援 (i18n token system)
- [ ] Design System 獨立 package


---

# 15. Agent Reliability Protocol（防閒置機制）

> 適用：Power Squad | 生效：Sprint 2 Phase 0+

## 15.1 背景

Sprint 1 retro 發現 Christina 漏取 inbox task 次數偏多（5 次 / 3 天），導致 task 堆積在 inbox 無人接手。為避免 P1/P2 task 被誤判為已完成，需建立自動化 watchdog 機制。

## 15.2 防閒置規則

```
inbox task 指派後 15 分鐘內未被 pick up（狀態仍為 inbox）
→ 自動改派給 Smart 或 Technus（優先輪流）
→ 觸發 board chat 通知：「任務 X 超時，已改派」
```

| 參數 | 值 |
|------|-----|
| 指派超時閾值 | 15 分鐘 |
| 掃描頻率 | 每 10 分鐘 |
| 改派目標 | Smart → Technus → Smart（輪流） |
| 通知方式 | Board chat mention |

## 15.3 Task Watchdog 實現

**Cron job（每 10m）：**
```bash
# /opt/homebrew/lib/node_modules/openclaw/cron job: cris-swat-idle-watchdog
# 或 board-level cron: scan inbox tasks assigned to Christina
# 條件：created_at + 15min < now AND status == inbox AND assignee == Christina
```

**Agent side（board-scan heartbeat 內檢查）：**
```python
# 每次 board-scan 檢查 Christina inbox tasks
# if task.created_at + 15min < now: 觸發 escalation
# POST /boards/{id}/tasks/{task_id}: assignee → Smart/Technus
```

## 15.4 SOP 清單

- [ ] Watchdog cron 部署（Sprint 2 Phase 0）
- [ ] Christina 改派通知測試（假 task 驗證）
- [ ] 監控 7 天後復盤（漏取次數是否下降）
- [ ] 如需降級閾值：15m → 30m（若誤報率過高）

## 15.5 歷史數據

| 日期 | 漏取次數 | 備註 |
|------|---------|------|
| 05-17 ~ 05-19 | 5 次 / 3 天 | Sprint 1 baseline |
| — | — | Sprint 2 目標：≤1 次/週 |

---
---

# 16. Board Rule Reference（狀態管理規則）

> 適用：Power Squad | 生效：Sprint 2 Phase 0+

## 16.1 Status Change Authority

| Rule | 值 | 說明 |
|------|----|------|
| `only_lead_can_change_status` | `false` ✅ | Agent 可自行更新 task status |
| `require_approval_for_status_change` | `false` ✅ | 狀態變更無需 lead 審批 |

**變更歷史：**
- Sprint 1 前：`only_lead_can_change_status: true`
- Sprint 1 retro P0 #3：討論放寬 → 改為 `false`
- Sprint 2 Phase 0：正式落地文檔化

**原因：** Worker Gate 模式下 Agent 完成任務需立即將 task 從 `in_progress` → `review`，等待 lead review 後才 `done`。若必須 lead 才能改狀態，將導致 30 分鐘以上手動等待。

**例外：**
- `inbox` → `in_progress`：Agent 可自行 pick up ✅
- `review` → `done`：需 lead/Nana 審批 ✅
- `done` → `in_progress`：需 lead 重新開啟 ✅

## 16.2 Task Assignment Rules

| Rule | 值 |
|------|----|
| Agent 可自行領取 inbox task | ✅ |
| Inbox 超時自動改派 | ✅（15m → Smart/Technus）|
| Task Watchdog | ✅（每 10m 掃描）|

---

# 17. API Blocker Workaround SOP（API 限制自救手冊）

> 適用：Power Squad | 狀態：active | 最後更新：2026-05-21

## 17.1 已知 API 限制

| # | 問題 | 現象 | 影響 | 狀態 |
|---|------|------|------|------|
| 1 | `task_assignee_mismatch` | 非 assignee 無法 PATCH task status | Review→done 阻塞 | 🟡 待修 |
| 2 | Auth token 失效 | 401 / no response | 全線阻塞（5/20 8h） | 🟢 文檔化 |
| 3 | Rate limit | 429 Too Many Requests | PATCH 連續失敗 | 🟢 可繞 |
| 4 | Bearer prefix 要求 | 無 Bearer → 401 | 新手誤觸 | 🟢 文檔化 |

## 17.2 `task_assignee_mismatch` Workaround

**問題：** review task 指派給 Smart（aef9098a），Christina/Technus 無法推→done。

**Sprint 1-2 實例：** ea9b08f5（OTD 測試框架）+ d1902c27（Christina 自我審計）stuck 23h+。

### 方案 A：Peer Review Comment（推薦）

```bash
# 1. 產出 review comment 貼 task thread
curl -X POST $BASE_URL/api/v1/agent/boards/$BOARD_ID/tasks/$TASK_ID/comments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "## Review ✅\n\n### Code Quality: PASS\n- 結構清晰，模組化完整\n- 測試覆蓋率充分\n\n### Recommendation: APPROVE\n理由：<1-2句>"
  }'

# 2. 標記 board-group chat 讓 assignee 可看到
# 3. assignee（Smart）用自己的 credential PATCH → done
```

**優點：** 零風險，不碰 task status，純文字 review。
**缺點：** 需 assignee 自行 PATCH（Smart 需 online）。

### 方案 B：Lead Override（需 Nana）

Nana 用 lead credential PATCH status review → done，不受 assignee 限制。

### 方案 C：Board Rule 放寬（需開會）

提議 board-level flag：`peer_review_done: true` — 任何 agent 可推非自審 task → done。

## 17.3 Auth Token 失效 SOP

```
現象：401 Unauthorized / curl 無回應

步驟：
1. curl $BASE_URL/healthz（無 auth，確認服務在線）
2. curl -v 含 Bearer → 確認 401
3. 檢查 .env / TOOLS.md 中 AUTH_TOKEN 是否更新
4. 通知 @Nana / @Allen 重新發 token
5. 記錄 downtime（start/end/resolution）→ board memory

歷史：5/20 08:00-16:01 失效（8h），根因未知，Allen 手動修復。
```

## 17.4 Rate Limit 繞過策略

```
429 時：
1. 等 Retry-After header 指定秒數
2. 若無 header：退避 30s → 重試（最多 3 次）
3. 合併 requests：單次 POST 多個 comments / memory entries
4. 錯開 cron 時間：3 agent 掃板間隔 ≥ 5m
```

## 17.5 Bearer Prefix 檢查清單

```bash
# ✅ 正確
curl -H "Authorization: Bearer gby5En..."

# ❌ 錯誤（Sprint 1 新手誤觸）
curl -H "Authorization: gby5En..."          # → 401
curl -H "Authorization: SECRET_gby5En..."    # → 401

# TOOLS.md 已正確標註 ✅
```

---

# 18. Cross-Board Collaboration SOP（跨板協同）

> 適用：Power Squad + CRIS SWAT | 狀態：active | 最後更新：2026-05-21

## 18.1 兩板架構

```
Power Squad                         CRIS SWAT
─────────────────────────────────────────────────
Board: 3881607b                    Board: (<Vesper board>)
Lead: Nana                         Lead: Allen (?) / Nana
Agents: Smart / Technus / Christina Agents: Vesper / Luna
Scope: PPTX→HTML pipeline           Scope: CRIS product dev
Tools: gen_slides / run_qa / CI     Tools: ThemeToggle / CRIS engine
```

## 18.2 協同模式

### Mode A：Power Squad → CRIS SWAT（QA Gate 共用）

```
CRIS SWAT 產出 → Power Squad QA Gate 審查 → 成績回流 CRIS SWAT
```

**實例：** CRIS SWAT ThemeToggle（Luna 開發）→ Power Squad QA Gate 掃描 → 成績貼兩板。

SOP：
1. CRIS agent 產出後貼 board-group memory 標記 `cross-board,qa-request`
2. Power Squad agent 跑 run_qa.py 並產出成績單
3. 張貼 CRIS SWAT board memory + 標記原 thread

**約束：** Power Squad agent 不可修改 CRIS SWAT 成品（跨板只審不修）。

### Mode B：共享 Design System

```
tokens.json → 兩板共享 canonical token set
```

- 73 common tokens 已建立
- CRIS SWAT 可用 `--ds-*` namespace 直接引用
- 變更 canonical set 需兩板 lead 同意

### Mode C：聯合 Report

```
BEFORE_AFTER_REPORT.md（Smart，2026-05-20）
```

- 每 Sprint 結尾產出一份聯合成績單
- 內容：兩板 done count / QA 分數 / 教訓 / 下一步
- 張貼兩板 board memory

## 18.3 跨板溝通規範

| 規則 | 說明 |
|------|------|
| 標籤 `cross-board` | 所有跨板 memory entry 加此 tag |
| 不跨板改 task | Power Squad agent 不碰 CRIS SWAT task |
| Review-only | Power Squad QA gate 僅審查，不修改成品 |
| Lead Cc | 跨板協商需 Cc 兩板 lead |
| Memory sync | 重要決策同步兩板 memory |

## 18.4 跨板 CI 統一（Sprint 3 規劃）

```
deploy.yml 共用：
1. QA Gate stage（共用 run_qa.py）
2. Token check stage（共用 extract-tokens.py）
3. Lighthouse stage（共用 lighthouserc）
4. Deploy stage（各板獨立 gh-pages）

目標：一條 workflow 管兩板 deploy。
```

## 18.5 歷史

| 日期 | 事件 | 結果 |
|------|------|------|
| 5/20 | Cross-Team Charter v1.0 | 雙 Squad 協同正式化 |
| 5/20 | Smart 聯合 Before/After Report | 兩板數據對比完成 |
| 5/20 | Luna ThemeToggle QA Gate | Power Squad 跨板審查成功 |

---

# 19. Lead Absence Protocol（Lead 離線應對）

> 適用：Power Squad | 狀態：active | 最後更新：2026-05-21

## 19.1 分級響應

```
Tier 1: 常規（< 4h）
→ 正常提案 + 等待

Tier 2: 注意（4-12h）
→ 提案後不等回覆，選 best proposal 自主開工（documentation/analysis 類）
→ 不執行 external side effect 任務

Tier 3: 警報（12-24h）
→ 每 2h lead-checkin escalation
→ 自主開工加速（連續提案+執行）
→ 準備 formal status report（給 Allen backfill）

Tier 4: 緊急（24-48h）
→ 發 formal escalation @Nana + @Allen（跨 channel）
→ 附：當前 sprint status + 阻塞 + 建議行動
→ 考慮外部溝通（email/phone）→ 需 lead 授權

Tier 5: 斷聯（> 48h）
→ 啟動 backup lead（Allen）
→ 必要時停止新任務，維護現有成品
→ 全線狀態凍結，等待 human decision
```

## 19.2 自主開工範圍（不需 lead approval）

| ✅ 可做 | ❌ 不可做 |
|---------|----------|
| Documentation / SOP 更新 | External deployment |
| Research / 分析報告 | Email / 外部通訊 |
| PLAYBOOK.md 補完 | Public post / GitHub release |
| Memory 重整 | Destructive action |
| QA scan / healthcheck | Cross-team task assignment |
| Spec / wireframe / prototype | 修改 auth / security config |
| Review comment（純文字） | PATCH task status（跨 assignee） |

## 19.3 Escalation 模板

### Tier 3 Escalation（12-24h）

```markdown
⚠️ Lead Check-in — {N} hours since last response

**Status:**
- Board: {total} tasks · {done} done · {review} review · {inbox} inbox
- Blockers: {list}
- Agents active: Christina / Smart / Technus

**What we can do right now:**
1. {proposal 1}
2. {proposal 2}
3. {proposal 3}

**Request:** Please confirm one direction or approve autonomous mode.

@Nana
```

### Tier 4 Escalation（24-48h）

```markdown
🚨 FORMAL ESCALATION — Lead absent {N} hours

@Nana @Allen

**Urgency:** {why urgent}
**Board:** Power Squad ({board_id})
**Sprint:** Sprint 3 Phase {N}

**Current state:** {summary}
**Stalled items:** {list}
**Risk:** {what could go wrong if left unaddressed}

**Immediate ask:** 
1. Confirm "autonomous mode" for next 24h
2. Approve one blocked task → done
3. Designate backup lead

This will auto-escalate to Allen at 48h mark.
```

## 19.4 Auto-Escalation Cron（Sprint 3 實作）

```yaml
# OpenClaw cron job: lead-absence-watchdog
cron: "0 */2 * * *"  # every 2h
board_id: 3881607b

trigger:
  - last_lead_activity > 12h → Tier 3 escalation
  - last_lead_activity > 24h → Tier 4 escalation
  - last_lead_activity > 48h → Tier 5 escalation + @Allen

action:
  - POST board-group memory with escalation template
  - tag: escalation, lead-absence
  - mention: @Nana, (@Allen if Tier 4+)
```

## 19.5 歷史事件

| 日期 | Duration | Tier | Result |
|------|----------|------|--------|
| 5/20-5/21 | 23h+ | 3→4 | 自主開工持續 · 3 agent 並行 · 零 idle |
| — | — | — | 累積經驗：自主模式可行但 review→done 阻塞 |

## 19.6 教訓

1. **review→done 阻塞是自主模式最大弱點** — 需 board-level 放寬 peer review gate
2. **三 agent 並行可在無 lead 下維持產能** — Sprint 2/3 實證
3. **文檔類任務是安全的自動填充物** — 不依賴 external side effect
4. **24h 是心理閾值** — 超過後需 formal escalation（本 protocol）

---

# 20. Three-Unit Interaction SOP（三單位互動標準作業程序）

> 適用：Power Squad + CRIS SWAT + Elite | 狀態：active | 最後更新：2026-05-21
> 觸發：Allen 2026-05-21 group broadcast — 明確三單位角色分工

## 20.1 角色定義

```
Power Squad ──── 執行團隊（做）
CRIS SWAT  ──── 執行團隊（做）
Elite       ──── 監管審查（看 → 建議 → 輔導改善 → 複查）
```

| 單位 | 角色 | 職責 | 禁止 |
|------|------|------|------|
| Power Squad | 執行 | 產出 artifacts / 修復 / QA gate | — |
| CRIS SWAT | 執行 | 產出 artifacts / 修復 / deploy | — |
| Elite | 監管 | 審查產出 → 量化建議包 → 輔導改善 → 複查達標 | ❌ 親自執行修改 |

## 20.2 互動流程

```
執行團隊產出（Power Squad / CRIS SWAT）
  │
  ▼
Elite 審查（三條審計線輪流）
  │
  ├── 產出：量化建議包（Audit Pack）
  │     - 🔴 Must-Fix（阻斷交付 → 進 sprint backlog）
  │     - 🟡 Should-Fix（品質提升 → board chat 討論取捨）
  │     - 🟢 Nice-to-Have（未來方向 → Sprint+1 planning）
  │
  ▼
執行團隊改善（依建議包迭代）
  │
  ▼
Elite 複查
  │
  ├── Pass → 達標
  └── Fail → 回到改善步驟（下一輪）
```

## 20.3 Audit Pack 標準模板

Elite 審計員出包時使用此格式（直接複製貼上）：

```markdown
## Elite Audit Pack — {product} / {audit line} / Round {N}

### 審查對象
- Task: {task_id}
- Artifact: {file path}
- QA baseline: {P0 X/Y · P1 X/Y · Lighthouse PXX}

### 🔴 Must-Fix（阻斷交付）
| # | 問題 | 檔案:行號 | 修法（可複製貼上） | 預期結果 |
|---|------|----------|-------------------|---------|
| 1 | {具體描述} | `file:42` | ```diff\n- old\n+ new``` | {可量化的改善} |

### 🟡 Should-Fix（品質提升）
| # | 問題 | 建議 | 預期影響 |
|---|------|------|---------|

### 🟢 Nice-to-Have（未來方向）
| # | 想法 | 優先級 |
|---|------|:------:|

### 複查 Checklist
- [ ] Must-Fix #1 已修 → QA re-run PASS
- [ ] Must-Fix #2 已修 → token diff clean
- [ ] Should-Fix 取捨討論完成

### 建議包版本
v1.0 · {審計員} · {日期}
```

## 20.4 執行團隊收包後的處理流程

```
收到 Audit Pack →
  Must-Fix：直接進 current sprint backlog → 修 → QA → Elite 複查
  Should-Fix：board chat @Elite 討論取捨 → accepted → sprint backlog / rejected → 記錄原因
  Nice-to-Have：標記 Sprint+1 planning → 不阻塞當前交付
```

### 回應模板

```markdown
@Elite 收到 Audit Pack · Round {N}

Must-Fix: {N} 項 → sprint backlog · ETA {time}
Should-Fix: {N} 項 → 討論中（{accepted} accepted / {discussing} discussing）
Nice-to-Have: {N} 項 → Sprint+1 backlog

預計修完時間：{time}
複查 ready：{time}
```

## 20.5 約束與規範

| 規則 | 說明 |
|------|------|
| Elite 不親自改 code | 建議包格式確保「修法」欄位是 diff/command，非實際修改 |
| 執行者不跳過 Elite 複查 | Must-Fix 修完後需 Elite 複查簽核才算 done |
| Audit Pack 需量化 | 禁止模糊評論（「顏色不好看」→ ❌），需具體到「`--accent: #C0392B → #E74C3C`」 |
| 一包一輪 | 每輪 Audit Pack 獨立版本號，覆蓋上次 Must-Fix 的複查結果 |
| Cross-board 可見 | Audit Pack 張貼 group memory（tag: `audit-pack`），三單位全員可見 |

## 20.6 審計線（三條輪流）

Elite 的三條審計線依序輪流出 Audit Pack：

| 審計線 | 範圍 | 頻率 |
|--------|------|------|
| 審計線 1 | Code / Architecture（結構、模組化、CI） | 每輪交替 |
| 審計線 2 | Design / UX（token、色彩、排版、動畫） | 每輪交替 |
| 審計線 3 | Content / Business（中文正確性、商業邏輯、數據一致性） | 每輪交替 |

## 20.7 歷史

| 日期 | 事件 | 結果 |
|------|------|------|
| 5/21 15:04 | Allen group broadcast — 三單位角色定義 | 此 SOP 建立 |
| 5/21 15:09 | Henry 確認 interaction model + 建議包格式 | 模板定稿 |

---


> **記住**: 本 Playbook 是活的文件。每發現一個新陷阱或更好的做法，就更新它。下次開任務時讀一遍。

---

*Playbook v4.1 — Power Squad Complete Operations Manual · 2026-05-21 · +Ch20 Three-Unit Interaction SOP*