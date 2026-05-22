# Power Squad 標竿調研報告

> 撰寫：Christina（監察組 — 設計審計）
> 日期：2026-05-22 10:33 CST
> 用途：為流程整改 v2.0 建立業界基準線，所有後續提案必須引用此報告

---

## 📐 調研範圍

| 領域 | 標竿 | 參考權重 |
|------|------|:--------:|
| 設計系統 | Apple Human Interface Guidelines | ⭐⭐⭐⭐⭐ |
| 元件庫 | Stripe Design · Linear | ⭐⭐⭐⭐ |
| Token 標準 | W3C Design Tokens Community Group | ⭐⭐⭐⭐⭐ |
| CI/CD 品質閘 | Vercel / Netlify deploy preview | ⭐⭐⭐⭐ |
| 前端品質 | Lighthouse P90+ / Web Vitals | ⭐⭐⭐⭐⭐ |
| 可訪問性 | WCAG 2.1 AA | ⭐⭐⭐⭐⭐ |
| 響應式 | Tailwind CSS breakpoints | ⭐⭐⭐⭐ |
| 流程治理 | Shape Up (Basecamp) · Linear Method | ⭐⭐⭐ |

---

## 🎨 設計系統標竿

### Apple Human Interface Guidelines (HIG)

> https://developer.apple.com/design/human-interface-guidelines

**核心原則（與我們的差距分析）：**

| Apple HIG 原則 | 我們現狀 | 差距 | 行動 |
|---------------|---------|:----:|------|
| **一致性** — 相同元素始終相同呈現 | --ds-* 已建但 compat shim 仍存在 | 🟡 | 去 compat shim，強制 single source |
| **直接操控** — 用戶感到直接控制介面 | 鍵盤導航有但動畫不足 | 🟡 | 補 :active / :focus-visible |
| **反饋** — 每個動作有即時回應 | 載入狀態缺 | 🟡 | skeleton screen / loading state |
| **隱喻** — 用熟悉的概念 | ✅ OTD domain model 已用實體對應 | 🟢 | 維持 |
| **使用者控制** — 可撤銷、可返回 | nav back 有，但無 undo 概念 | 🟢 | 非核心 |

**Action Items：**
1. 強制單一 token 來源（去掉 --c-teal / --c-ink 等舊命名）
2. 補齊 :active / :focus-visible / prefers-reduced-motion
3. 所有互動元件需有 loading/error/empty 三態

### Stripe Design

> https://stripe.com/blog/designing-apis-for-humans

**Token 命名體系（標竿）：**

```
stripe. 命名法                     我們的對應
──────────────────────────        ──────────────
--color-primary-500               --ds-color-primary     (缺層級)
--color-neutral-100               --c-bg / --c-surface   (混用)
--spacing-4 (4px)                 --gap 隨意              (缺系統化)
--font-size-heading-xl            --ds-text-display      (缺 -xl/-lg 層級)
--radius-md (8px)                 --radius 不統一         (缺 token)
--shadow-elevation-1              --shadow               (缺層級)
```

**Action Items：**
1. Token 增層級：--ds-{category}-{name}-{scale}（如 --ds-space-sm / --ds-space-md / --ds-space-lg）
2. 補 radius / elevation / font-size scale tokens
3. 命名從扁平 → 層級化

### W3C Design Tokens Community Group

> https://tr.designtokens.org/

**標準格式：**

```json
{
  "color": {
    "primary": {
      "$value": "#14b8a6",
      "$type": "color",
      "$description": "品牌主色"
    }
  }
}
```

**我們框架差距：**
- 我們的 tokens.json 用扁平結構，沒 `$type` / `$value` / `$description`
- W3C 標準建議 group → item → value 三層，我們只有 category → name 兩層
- `$type` 欄位可以驅動自動化測試（type-check tokens）

**Action Items：**
1. tokens.json 重構為 W3C 標準格式
2. 加入 $type: color | dimension | duration | fontFamily 等
3. 自動化 token type validation

---

## 🚀 CI/CD 品質閘標竿

### Vercel / Netlify Deploy Preview

| 標竿特性 | 我們現狀 | 差距 |
|---------|---------|:----:|
| PR → 自動 preview URL | ❌ 無 preview | 🔴 |
| Lighthouse check per deploy | ✅ deploy.yml 有 | 🟢 |
| 失敗阻止 merge | ✅ QA gate exit code | 🟢 |
| 差異報告（before/after） | ❌ 無 diff | 🟡 |
| Rollback 一鍵 | ❌ gh-pages force push | 🔴 |

**Action Items：**
1. 研究 GitHub Pages deploy preview（或用 Vercel free tier）
2. 產出 deploy diff report（before/after size + LH + tokens）

### Lighthouse P90+ 基準

| 指標 | P90 基準 | 我們達標？ |
|------|:-------:|:----------:|
| Performance | ≥ 90 | ✅ P100（三產品） |
| Accessibility | ≥ 90 | 🟡 未穩定測量 |
| Best Practices | ≥ 90 | ✅ |
| SEO | ≥ 90 | 🟡 缺 meta |

**Action Items：**
1. 所有 HTML 頁面強制 SEO meta（title/description/og）
2. a11y audit 自動化（axe-core CI 整合）

---

## ♿ 可訪問性標竿

### WCAG 2.1 AA 快速檢查清單

| 要求 | 閾值 | 我們現狀 |
|------|:----:|:-------:|
| 色彩對比度（文字） | ≥ 4.5:1 | 🟡 暗色背景，手動檢查過關但未自動化 |
| 色彩對比度（大文字） | ≥ 3:1 | ✅ |
| 鍵盤導航（Tab/Enter/Esc） | 完全可操作 | ✅（已有但未正規化測試） |
| Focus 指示器 | 可見 | 🟡 :focus-visible 有但 :active 缺 |
| 非文字內容 alt | 有意義 | 🟡 部分缺 |
| 縮放 200% 可用 | 內容不丟失 | 🟡 未測試 |
| prefers-reduced-motion | 尊重系統設定 | ❌ 未實作 |

**Action Items：**
1. CI 整合 axe-core 或 pa11y
2. 所有動畫 wrap @media (prefers-reduced-motion: reduce)
3. 自動色彩對比檢查

---

## 📋 流程治理標竿

### Shape Up (Basecamp)

**核心規則（對應我們整改）：**

| Shape Up 規則 | 我們對應 |
|--------------|---------|
| **Shaping** — 先塑形（問題定義）再開發 | 提案前標竿調研 |
| **Betting** — 決定做什麼（不做什麼） | 監察組審批 |
| **Building** — 6 週內交付 | 我們的估時（分/時級） |
| **Cool-down** — 兩週修 bug / 清理 | Sprint 結束後的審計周 |

### Linear Method

**核心規則：**
- 每個 issue 有明確 owner、estimate、status
- Project lead 決定 priority（不是 engineer）
- 所有決策寫進 issue comment（可追溯）

**我們對應：**
- Board task 已有 owner/status/estimate → ✅
- Priority 由 lead 決定 → 🟡 目前 Nana 角色空缺
- 決策可追溯 → 🟡 board chat 分散，需統合

---

## 📊 差距矩陣總表

| 標竿領域 | 現狀 | 差距評級 | 優先級 |
|---------|:----:|:-------:|:-----:|
| Design System 一致性 | 73 tokens 但 compat shim 仍在 | 🔴 劇烈 | P0 |
| Token 命名層級化 | 扁平結構 | 🔴 劇烈 | P0 |
| W3C Token 標準格式 | JSON 格式不標準 | 🟡 中等 | P1 |
| 預覽部署 | 無 preview URL | 🔴 劇烈 | P0 |
| 部署差異報告 | 無 diff | 🟡 中等 | P2 |
| a11y 自動化測試 | 有 LH 但缺 axe-core | 🔴 劇烈 | P0 |
| 動畫 prefers-reduced-motion | 未實作 | 🟡 中等 | P1 |
| SEO meta | 部分缺 | 🟡 中等 | P1 |
| 角色分離 | 監察/執行不分 | 🔴 劇烈 | P0 |
| 提案標準化 | 格式不統一 | 🔴 劇烈 | P0 |

---

## 🎯 建議實施順序

**Phase 1（本日內，P0）：**
1. 角色分離生效（監察組/執行組）
2. Proposal 模板強制使用
3. Token compat shim 移除方案

**Phase 2（Sprint 3，P1）：**
4. W3C 標準 token 格式遷移
5. axe-core CI 整合
6. SEO meta 補齊

**Phase 3（Sprint 3，P2）：**
7. 預覽部署（Vercel preview）
8. 部署差異報告
9. prefers-reduced-motion

---

*Christina 產出 · 監察組標竿調研 · 2026-05-22 10:33*