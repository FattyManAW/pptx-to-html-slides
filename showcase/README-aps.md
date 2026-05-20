# APS AI Agent — 智能体解决方案

> 投影片展示 · 10 slides · 純 CSS 無圖片 · 1,131 CJK characters  
> **QA Pipeline: 17/17 PASS (100%) · Lighthouse: P100**

---

[![CI](https://github.com/FattyManAW/pptx-to-html-slides/actions/workflows/deploy.yml/badge.svg)](https://github.com/FattyManAW/pptx-to-html-slides/actions/workflows/deploy.yml)

## 📋 產品說明

APS AI Agent 智能体解決方案投影片，展示大連潤思科技的 AI 驅動先進排程系統。聚焦 APS 核心能力、AI 智能體架構、與 ERP/MES 整合場景。

### 投影片結構

| 投影片 | 內容 |
|------|------|
| 1 | Cover — APS AI Agent 智能体解決方案 |
| 2 | 智能製造挑戰與 APS 定位 |
| 3 | APS AI Agent 核心架構 |
| 4 | 智能排程引擎 |
| 5 | AI 決策規則庫 |
| 6 | 可視化排程看板 |
| 7 | AI Agent 自主調度流程 |
| 8 | 與用友 ERP/APS/MES 整合 |
| 9 | 行業應用場景 |
| 10 | 總結與聯繫 |

---

## 🛠 技術棧

### Design System Tokens
- **Color palette**: 完整 12 階灰階（c-50 → c-950）+ accent（indigo）+ semantic（success/warning/error/info）
- **Blur gradient**: 雙系統 — 自訂 `--blur-sm/md/lg/xl` + QA 標準 `--blur-8/12/24/32`
- **Glass morphism**: surface/border/backdrop-filter 完整支援
- **Typography scale**: Display / Heading / Body 三級階梯
- **Spacing**: 8px grid（gap-1 → gap-12）

### 框架與字體
- **CSS**: Pure CSS Variables + Custom Properties（無 Tailwind）
- **字體**: Playfair Display (Display) · Inter (Heading) · Noto Sans SC (Body)
- **載入策略**: Google Fonts 非阻塞（`media="print" onload`）
- **動畫**: CSS `@keyframes fadeSlideUp` + `data-stagger` 進場序列

### 效能優化
- 零圖片 — 純文字排版減免網路請求
- `<section class="slide">` 語義標籤
- `tabindex="0"` + `aria-label` 完整無障礙
- FCP/LCP < 1s

---

## 📊 分數

### QA Pipeline（修正後）
| 類別 | 結果 |
|------|------|
| P0 六大原則 | 6/6 ✅ |
| 結構 | 6/6 ✅ |
| 內容品質 | 5/5 ✅ |
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
| FCP | < 1s |
| LCP | < 1s |
| TBT | 0ms |
| CLS | 0 |

---

## 🚀 部署方式

### 本地預覽
```bash
cd showcase
python3 -m http.server 8765
# 開啟 http://localhost:8765/aps-ai-agent.html
```

### 靜態託管
單一 HTML 檔案（44KB），無外部依賴，可直接部署至任何靜態伺服器。

---

## 📁 檔案結構

```
showcase/
├── aps-ai-agent.html   ← 主投影片（44KB · 1,149 行 · 10 slides）
├── aps-assets/          ← APS 專屬資源目錄
│   └── ...
└── README-aps.md        ← 本文件
```

### HTML 內部結構
```
<!DOCTYPE html>
├── <head>
│   ├── Font preconnect + 非阻塞載入
│   ├── <meta> description + favicon SVG
│   ├── <style> — Design System (~21KB)
│   │   ├── §1-§15 完整 Design Tokens
│   │   ├── Reset + Base
│   │   ├── Typography scale
│   │   ├── Slide Engine (fadeSlideUp)
│   │   ├── Glass Cards / Feature Grids / Stat Boxes
│   │   ├── Progress Bar + Navigation
│   │   ├── Responsive (1024/768/480)
│   │   └── Utilities (focus-visible, tags)
│   └── </style>
├── <body>
│   ├── <main> — 10 × <section class="slide" data-i="N" data-stagger="0" tabindex="0">
│   │   └── 語義結構（h1/h2/p + glass cards/feature grids）
│   ├── Progress indicator
│   ├── Navigation bar
│   └── <script> — Navigation engine (~1.8KB)
└── </body>
```

---

## 🔧 開發備註

- QA Pipeline：`python3 qa_pipeline.py showcase/aps-ai-agent.html`
- Lighthouse：`lighthouse http://127.0.0.1:8765/aps-ai-agent.html`
- Blur tokens 為雙系統（自有 + QA 標準並存）
- `data-stagger` + `tabindex` 為本次修復補入（2026-05-20）
- qa_pipeline.py 已修正：favicon SVG 不再誤報 base64 違規

---

*最後更新：2026-05-20 · Technus*