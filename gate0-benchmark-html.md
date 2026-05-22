# Gate 0 — HTML 簡報線 標竿分析（Power Squad · Smart）

> 提交: Smart · 2026-05-22 11:28 CST
> 基準線: GH Pages 三產品現狀（commit 92f3bb7）
> 標竿來源: showcase/benchmark-research.md + Christina html-presentation-benchmarks.md

---

## 基準線：GH Pages 線上現狀

| 產品 | URL | slides | Phase 0 | Phase 1 | Phase 2 |
|------|------|:--:|:--:|:--:|:--:|
| 潤思 | [live](https://fattymanaw.github.io/pptx-to-html-slides/runs-impacts-aps-partner.html) | 62 | ✅ | ✅ | ✅ |
| CRIS | [live](https://fattymanaw.github.io/pptx-to-html-slides/cris-impacts-carbon.html) | 36 | ✅ | ✅ | ✅ |
| APS | [live](https://fattymanaw.github.io/pptx-to-html-slides/aps-ai-agent.html) | 12 | ✅ | ✅ | ✅ |

Phase 0: hover glow + color badges + sticky nav
Phase 1: Hero Number + Fragment 漸進揭露 + Auto-Animate
Phase 2: Overview 鳥瞰 + Story Arc 五段敘事

---

## 標竿 1: Stripe Sessions（視覺敘事）

**引用**: https://stripe.com/sessions

| # | Gap | Before (現狀) | After (目標) | 可行性 |
|:--:|------|------|------|:--:|
| 1 | 一畫面一核心數字 | Hero Number 只在 APS（97%）+ CRIS（100%），潤思缺 | 每份簡報 ≥3 張 hero slide | 高 |
| 2 | 60% 留白 | 部分 slide 資訊密度過高（潤思 62p 部分 slide >50 行文字） | 關鍵 slide 減至 ≤3 行核心訊息 | 中 |
| 3 | Scroll-driven parallax | 目前純 slide-based，無 scroll 視差 | 第一頁 hero parallax 背景 | 中 |
| 4 | Chapter sticky nav 動畫過場 | 有 sticky nav 但無章節間過場動畫 | nav dot scale+color 過渡 | 高 |
| 5 | 敘事語言（非功能清單） | Story Arc divider 已加，但內容 slide 仍偏功能羅列 | 每 slide 標題 = 一句價值主張 | 中 |

---

## 標竿 2: Reveal.js（互動簡報框架）

**引用**: https://revealjs.com/

| # | Gap | Before (現狀) | After (目標) | 可行性 |
|:--:|------|------|------|:--:|
| 1 | 演講者筆記 | 無 | speaker notes panel（按 S 鍵） | 高 |
| 2 | 觸控手勢 | 只有 swipe，無 pinch-zoom | pinch-to-zoom 圖片細節 | 低 |
| 3 | 簡報計時器 | 無 | 右上角 elapsed timer | 高 |
| 4 | PDF 匯出 | 無 | 列印-friendly CSS + 匯出按鈕 | 中 |
| 5 | 深色/淺色切換 | APS 有 ThemeToggle，CRIS/潤思無 | 三產品統一 theme toggle | 中 |

---

## 標竿 3: Apple HIG（設計一致性 + 輔助功能）

**引用**: https://developer.apple.com/design/human-interface-guidelines/
**數據**: sprint2-post-audit.md（Christina · 2026-05-22）

| # | Gap | Before（現狀） | After（目標） | 可行性 |
|:--:|------|------|------|:--:|
| 1 | Design Token 一致性 | DS token 滲透率僅 40%（只有三產品用 --ds-*） | 全線頁面（含 OTD/christina-portfolio）遷移 --ds-* | 高 |
| 2 | 鍵盤導航覆蓋 | 僅 10%（只有 APS+潤思有 keydown） | 全線補 keydown + tabindex | 高 |
| 3 | prefers-reduced-motion | 僅 10%（CRIS+潤思） | 全線動畫 wrap @media query | 高 |
| 4 | 色彩對比 WCAG AA | 無自動化檢查 | axe-core/paqly CI 整合 | 中 |
| 5 | 觸控目標 ≥44pt | 未檢查 | 互動元件最小觸控尺寸 | 中 |

---

## 標竿 4: Stripe（Token 層級化 + 材質影深）

**引用**: https://stripe.com/ · sprint2-post-audit.md

| # | Gap | Before（現狀） | After（目標） | 可行性 |
|:--:|------|------|------|:--:|
| 1 | Token 層級化（primitive→semantic→component） | 僅 APS 有完整 DS token 體系 | 三產品 + OTD 系列統一三層架構 | 高 |
| 2 | 材質影深（surface/overlay/popover） | 部分頁面用內聯自訂變數 | 全線 --surface / --overlay / --shadow-* 統一 | 中 |
| 3 | 動畫語意化（--ease / --t-fast / --t-mid） | APS 有動畫 token，CRIS 用 hardcoded | 全線動畫 token 化 | 高 |
| 4 | 字體層級（display/heading/body/caption） | APS 有四級字體，CRIS/潤思混用 | 三產品統一字體階梯 | 中 |
| 5 | Color 語意化（accent/success/warning/danger） | badges 已做 pass/warn，缺 semantic color | 完整 color token 體系 | 高 |

---

## 標竿 5: WCAG 2.1 AA（無障礙標準）

**引用**: https://www.w3.org/TR/WCAG21/ · sprint2-post-audit.md

| # | Gap | Before（現狀） | After（目標） | 可行性 |
|:--:|------|------|------|:--:|
| 1 | 鍵盤導航強制 | 20 頁中僅 2 頁有 keydown（10%） | 全線 100% 鍵盤可操作 | 高 |
| 2 | prefers-reduced-motion 尊重 | 20 頁中僅 2 頁（10%） | 全線動畫 wrap `@media (prefers-reduced-motion: reduce)` | 高 |
| 3 | 色彩對比 ≥4.5:1 | 無自動化掃描 | CI axe-core gate | 中 |
| 4 | aria-label 覆蓋 | 互動元件未標註 | 所有 button/link 補 aria-label | 高 |
| 5 | focus-visible 指示器 | 無焦點樣式 | `:focus-visible` ring/outline | 高 |

---

## 標竿 6: Linear（微互動 + 狀態可視化）

**引用**: https://linear.app/features

| # | Gap | Before (現狀) | After (目標) | 可行性 |
|:--:|------|------|------|:--:|
| 1 | Keyboard-first 快速鍵面板 | `?` 或 `F` 只觸發全螢幕 | `?` → shortcut cheat sheet overlay | 高 |
| 2 | 載入骨架屏 | 無 | skeleton loading（CRIS 858KB 載入慢） | 高 |
| 3 | 狀態轉換動畫 | Auto-Animate 已做 slide 層級 | card-level transition（hover→active→done） | 中 |
| 4 | Cmd+K 命令面板 | 無 | Cmd+K → slide jump / search | 低 |
| 5 | Color-coded status 擴展 | badges 只有 pass/warn | 加入 in-progress/review/done 四態 | 高 |

---

## 優先序（六標竿合併）

| 優先級 | 標竿 | Gap # | 項目 | 估時 | 影響 |
|:--:|:--:|:--:|------|:--:|------|
| **P0** | Apple | H-1 | DS token 遷移（OTD 系列 + portfolio → --ds-*） | 20m | 一致性：40% → 100% |
| **P0** | Apple | H-2 | 鍵盤導航補齊（全線 keydown + tabindex） | 15m | a11y: 10% → 100% |
| **P0** | Apple | H-3 | prefers-reduced-motion 全線覆蓋 | 10m | a11y: 10% → 100% |
| **P0** | Stripe Sessions | S1-1 | Hero Number 潤思補齊 | 15m | 三產品視覺敘事一致性 |
| **P0** | Reveal | R2-5 | 三產品統一 Theme Toggle | 20m | 線上一致性 |
| **P0** | Linear | L3-1 | `?` 快速鍵面板 | 15m | 可用性 |
| **P1** | Stripe | S4-1 | Token 層級化（primitive→semantic→component） | 30m | 設計系統成熟度 |
| **P1** | Stripe | S4-3 | 動畫 token 化（--ease / --t-fast） | 15m | 動畫一致性 |
| **P1** | AWS/WCAG | W-4 | aria-label 全線覆蓋 | 15m | a11y: focus-visible |
| **P1** | Stripe Sessions | S1-2 | 內容密度瘦身（潤思） | 30m | 可讀性 |
| **P1** | Linear | L3-2 | CRIS skeleton loading | 20m | 效能感知 |
| **P2** | AWS/WCAG | W-1 | axe-core CI 整合 | 30m | 自動化 a11y gate |
| **P2** | Reveal | R2-1 | 演講者筆記 | 30m | 專業度 |
| **P2** | Reveal | R2-3 | 簡報計時器 | 15m | 專業度 |

**P0 總估時**: 95m（6 項）  
**P1 總估時**: 110m（5 項）  
**P2 總估時**: 75m（3 項）

---

## 驗收標準

| # | 標準 | 驗證方式 |
|:--:|------|------|
| 1 | P0 三項全上線 | curl + grep marker |
| 2 | 三產品 live URL 200 | 監察組獨立 curl |
| 3 | Lighthouse ≥ P90（三產品） | CI Lighthouse gate |
| 4 | QA re-run 零 regression | `run_qa.py --ci` |
| 5 | 監察組 screenshot verify ×3 | Christina 獨立審 |

---

## 現狀基線

```
$ curl -sI https://fattymanaw.github.io/pptx-to-html-slides/aps-ai-agent.html | head -1
HTTP/2 200

$ curl -sI https://fattymanaw.github.io/pptx-to-html-slides/cris-impacts-carbon.html | head -1
HTTP/2 200

$ curl -sI https://fattymanaw.github.io/pptx-to-html-slides/runs-impacts-aps-partner.html | head -1
HTTP/2 200
```

三產品 Phase 0-2 全功能已上線（commit 92f3bb7, CI 全綠）。
