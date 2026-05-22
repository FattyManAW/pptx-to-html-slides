# 润思IMPACTS — APS 生態伙伴解決方案

> 投影片展示 ·  62 slides · 51 images · 7,912 CJK characters  
> **QA Pipeline: 17/17 PASS (100%) · Lighthouse: P100**

---

[![CI](https://github.com/FattyManAW/pptx-to-html-slides/actions/workflows/deploy.yml/badge.svg)](https://github.com/FattyManAW/pptx-to-html-slides/actions/workflows/deploy.yml)

## 📋 產品說明

润思IMPACTS APS（智能先進排程系統）生態伙伴解決方案投影片，展示大連潤思科技基於用友 BIP 平台的智能製造解決方案。涵蓋 APS 核心功能、生態架構、行業場景與客戶案例。

### 投影片結構

| 區段 | 內容 |
|------|------|
| Cover | APS AI Agent 智能体解決方案 |
| 01 | 智能製造趨勢與 APS 定位 |
| 02-05 | APS 核心功能（排程引擎、規則庫、可視化） |
| 06-10 | 生態伙伴架構 |
| 11-15 | 行業解決方案與客戶案例 |

---

## 🛠 技術棧

### Design System Tokens
- **Color palette**: 36 色 token（ink-50 → ink-950、accent/teal、error/success/warning/info）
- **Blur gradient**: `--blur-8` `--blur-12` `--blur-24` `--blur-32` + semantic names（card/sheet/modal/nav）
- **Timing**: `--t-fast` (150ms) · `--t-mid` (300ms) · `--t-slow` (400ms)
- **Spacing**: 8px grid（s1–s10）
- **Surface/Border**: RGBA glass morphism 系統

### 框架與字體
- **CSS**: Pure CSS Variables + Custom Properties（無 Tailwind）
- **字體**: Playfair Display (Display) · Inter (Heading) · Noto Sans SC (Body)
- **載入策略**: Google Fonts 非阻塞（`media="print" onload`）
- **動畫**: CSS `@keyframes springIn` + `data-stagger` 進場序列

### 效能優化
- 51 圖片 `loading="lazy" decoding="async"`
- 零外部 JS 依賴
- 零 base64 內嵌
- LCP < 1.4s

---

## 📊 分數

### QA Pipeline
| 類別 | 結果 |
|------|------|
| P0 六大原則 | 6/6 ✅ |
| 結構 | 6/6 ✅ |
| 內容品質 | 4/5 ✅ |
| 響應式 | 2/2 ✅ |
| 字體 | 1/1 ✅ |
| **總計** | **17 PASS / 0 FAIL / 0 WARN** |

### Lighthouse
| 指標 | 分數 |
|------|------|
| Performance | **100** |
| Accessibility | **100** |
| Best Practices | **100** |
| SEO | **100** |
| FCP | 1.3s |
| LCP | 1.3s |
| TBT | 0ms |
| CLS | 0 |

---

## 🚀 部署方式

### 本地預覽
```bash
cd showcase
python3 -m http.server 8765
# 開啟 http://localhost:8765/runs-impacts-aps-partner.html
```

### GitHub Pages
```bash
git push origin gh-pages
# https://fattymanaw.github.io/pptx-to-html-slides/
```

### 靜態託管
單一 HTML 檔案，無建置步驟，可直接放在任何靜態伺服器（Nginx、S3、Netlify）。

---

## 📁 檔案結構

```
showcase/
├── runs-impacts-aps-partner.html   ← 主投影片（107KB · 2,116 行）
├── images/                          ← 51 張圖片（PNG/JPEG）
│   ├── slide3_图形_11_e7323862.png
│   ├── slide4_图片_6_cb184213.png
│   └── ...
└── README.md                        ← 本文件
```

### HTML 內部結構
```
<!DOCTYPE html>
├── <head>
│   ├── Font preconnect (Google Fonts)
│   ├── <style> — CSS Variables + Design System (~12.6KB)
│   │   ├── [00] Design Tokens (36 colors)
│   │   ├── [01] Reset
│   │   ├── [02] Slide Engine (springIn animation)
│   │   ├── [03] Progress Bar
│   │   ├── [04] Navigation (keyboard/wheel/touch)
│   │   ├── [05] Section Break
│   │   ├── [06] Slide Content
│   │   ├── [07] Cards
│   │   ├── [08] Two-Column Layout
│   │   ├── [09] Images
│   │   ├── [10] Thank You
│   │   ├── [11] Cover
│   │   ├── [12] Responsive (1024/768/480)
│   │   └── [13] Utilities (focus-visible, tags, kv)
│   └── </style>
├── <body>
│   ├── 62 × <div class="slide" data-stagger="0">
│   │   └── <div class="slide-inner">
│   │       ├── 標題 / 內容段落
│   │       └── 圖片 (loading="lazy")
│   ├── Progress bar
│   ├── Navigation bar (prev/next/fullscreen)
│   └── <script> — Keyboard + Wheel + Touch navigation (~1.9KB)
└── </body>
```

---

## 🔧 開發備註

- **gen_slides.py** pipeline：`--semantic --design tokens.json --theme dark --img-dir`
- QA Pipeline：`python3 qa_pipeline.py showcase/runs-impacts-aps-partner.html`
- Lighthouse：`lighthouse http://127.0.0.1:8765/runs-impacts-aps-partner.html`
- 設計基底：Christina Canonical + Teal System v3.1

---

*最後更新：2026-05-20 · Technus*