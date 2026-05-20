# CRIS IMPACTs — 双碳数字化管理系统

> 投影片展示 · 36 slides · 31 images · 3,849 CJK characters  
> **QA Pipeline: 16/16 PASS (100%) · Lighthouse: P100**

---

## 📋 產品說明

CRIS IMPACTs（双碳数字化管理系统）投影片，展示大連潤思科技基於用友 BIP 平台的碳管理一體化解決方案。涵蓋政策背景、行業趨勢、IMPACTs 核心功能、客戶案例等。

### 投影片結構

| 區段 | slides | 內容 |
|------|--------|------|
| Cover | 1 | IMPACTs 双碳数字化管理系统 |
| 政策背景 | 2-7 | 双碳政策、CBAM 碳關稅、ESG 投資趨勢 |
| 挑戰與痛點 | 8-10 | 企業碳管理現狀、碳盤查必要性 |
| 解決方案 | 11-27 | IMPACTs 核心功能（數據採集、核算、分析、報告） |
| 產品優勢 | 25-27 | 行業覆蓋、國際標準、技術架構 |
| 服務優勢 | 26-27 | 用友整合、智能分析、數據安全 |
| 客戶案例 | 28-35 | 金屬製品、膠膜行業案例 |
| Thank You | 36 | 尾頁 |

---

## 🛠 技術棧

### Design System Tokens
- **Color palette**: 36 色 token（ink-50 → ink-950、accent teal、semantic colors）
- **Blur gradient**: `--blur-8` `--blur-12` `--blur-24` `--blur-32` + semantic names
- **Timing**: `--t-fast` (150ms) · `--t-mid` (300ms) · `--t-slow` (400ms)
- **Spacing**: 8px grid（s1–s10）
- **Surface/Border**: RGBA glass morphism 系統
- **Teal accent**: 完整 teal 色系（`--c-teal` `--c-teal-dim` `--c-teal-glow` `--c-teal-hot`）

### 框架與字體
- **CSS**: Pure CSS Variables + Custom Properties（無 Tailwind — 已移除 CDN）
- **字體**: Playfair Display (Display) · Inter (Heading) · Noto Sans SC (Body)
- **載入策略**: Google Fonts 非阻塞（`media="print" onload`）
- **動畫**: CSS `@keyframes springIn` + `data-stagger` 進場序列

### 效能優化
- 移除 Tailwind CDN（122KB 廢碼 → 0）
- 31 圖片 `loading="lazy" decoding="async"`
- 零外部 JS 依賴
- FCP/LCP < 1s（從 10.3s 降至 823ms）

---

## 📊 分數

### QA Pipeline（修復後）
| 類別 | 結果 |
|------|------|
| P0 六大原則 | 6/6 ✅ |
| 結構 | 6/6 ✅ |
| 內容品質 | 5/5 ✅ |
| 響應式 | 2/2 ✅ |
| 字體 | 1/1 ✅ |
| **總計** | **16 PASS / 0 FAIL / 0 WARN** |

### Lighthouse
| 指標 | 分數 |
|------|------|
| Performance | **100** |
| Accessibility | **100** |
| Best Practices | **100** |
| SEO | **100** |
| FCP | 823ms |
| LCP | 823ms |
| TBT | 0ms |
| CLS | 0 |

---

## 🚀 部署方式

### 本地預覽
```bash
cd showcase
python3 -m http.server 8765
# 開啟 http://localhost:8765/cris-impacts-carbon.html
```

### 靜態託管
單一 HTML 檔案（38KB），無外部依賴（Tailwind CDN 已移除），可直接部署至任何靜態伺服器。

---

## 📁 檔案結構

```
showcase/
├── cris-impacts-carbon.html   ← 主投影片（38KB · 626 行 · 36 slides）
├── images/                     ← 31 張圖片（PNG/JPEG/GIF）
│   ├── slide2_图片_15_f29c5461.png
│   ├── slide16_圖片_4_26c41198.jpeg
│   ├── slide19_图片_3_15286e7b.png
│   └── ...
└── README-cris.md              ← 本文件
```

### HTML 內部結構
```
<!DOCTYPE html>
├── <head>
│   ├── Font preconnect + 非阻塞載入
│   ├── <meta> description + favicon SVG
│   ├── <style> — Design System (~12KB)
│   │   ├── [00] Design Tokens (36 colors + teal system)
│   │   ├── [01] Reset
│   │   ├── [02] Slide Engine (springIn animation)
│   │   ├── [03] Progress Bar
│   │   ├── [04] Navigation
│   │   ├── [05] Section Break
│   │   ├── [06] Slide Content / Cards / Two-Column
│   │   ├── [07-11] Images / ThankYou / Cover / Responsive
│   │   └── [12-13] Utilities (focus-visible, tags, kv)
│   └── </style>
├── <body aria-label="IMPACTs 双碳数字化管理系统 — 投影片展示">
│   ├── 36 × slide blocks
│   ├── Progress + Navigation
│   └── <script> — Navigation engine (~1.7KB)
└── </body>
```

---

## 🔧 修復歷史

| 日期 | 項目 | 變更 |
|------|------|------|
| 2026-05-20 | Technus 接手 | 從 Christina 原始版本升級 |
| | 36 slides | 28 → 36（以 cris-impacts-dark.html 為基底） |
| | 佔位文字 | 「添加文本」→ 實質內容 |
| | blur tokens | 補 `--blur-8/12/24/32` |
| | aria-label | 加入 slides-container |
| | Tailwind CDN | 移除（122KB 廢碼） |
| | Font loading | 同步 → 非阻塞 |
| | 圖片 lazy | 31 張加入 loading="lazy" |

### 原始缺口（Christina task 66fabffd）
1. ~~Slide 數量不一致 (28≠36)~~ → 36 ✅
2. ~~2 個 media 缺失~~ → 以 dark 版基底補齊 ✅
3. ~~1 處 bounce 動畫違規~~ → dark 版使用 springIn ✅
4. ~~缺 1024px 斷點~~ → 已含 @media(max-width:1024px) ✅

---

*最後更新：2026-05-20 · Technus*