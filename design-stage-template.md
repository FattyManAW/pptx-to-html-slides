# Design Stage — Deliverables 模板

> Power Squad 開發模式 v1 · Pipeline B（Spec-First）· D1-D3 Gate
> Owner: Christina / Design · 2026-05-20

---

## 概述

Spec Review 通過後、Dev 開始前，Design Stage 固定產出三件：

```
Spec ──[D1]─→ Spec Review Comment ──[D2]─→ Token Table ──[D3]─→ Wireframe Checklist ──→ Dev Ready
```

**Gate 條件**：D1 + D2 + D3 全完成 → Nana approve → 開 Dev task

---

## D1 — Spec Review Comment

**Purpose**：在 Dev 看見 Spec 之前，先由 Design Lead 掃一遍架構完整性。

**Template**：

```markdown
## [任務名稱] Spec Review

> Reviewer: Christina · YYYY-MM-DD
> 結論：✅ 架構完整，可以直接進入實作 / ⚠️ 有 N 個建議 / ❌ 需要重寫

### 架構完整性 QA（10 項）

| 檢查項目 | 狀態 | 說明 |
|----------|:--:|------|
| 核心實體定義 | ✅/❌ | |
| JSON Schema 定義 | ✅/❌ | |
| API 介面簽名 | ✅/❌ | |
| 工廠/系統拓撲 | ✅/❌ | |
| 參數空間定義 | ✅/❌ | |
| 狀態機定義 | ✅/❌ | |
| 觸發條件明確 | ✅/❌ | |
| 版本標記 | ✅/❌ | |
| Code blocks ≥ 5 | ✅/❌ | |
| 表格結構 | ✅/❌ | |

### 架構建議（S1-S5）

#### S1. [標題]
**現況**：
**建議**：
**優先度**：高/中/低

### 邊角案例（B1-B5）

#### B1. [標題]
**問題**：
**建議**：

### 總結

| 維度 | 評分 | 說明 |
|------|:--:|------|
| 架構完整性 | ✅ | |
| 可實作性 | ✅ | |
| 邊角案例 | ⚠️ | N 個建議 |

**建議下一步**：...
```

**當 D1 不通過時**：退回 Spec Owner 修正，不進入 D2。

---

## D2 — Token Table

**Purpose**：Design Token 單一事實來源，Dev 和 Integrate 共用同一份。

**Template**（對應 `showcase/tokens.json` 格式）：

```json
{
  "version": "0.1",
  "categories": {
    "color_palette": {
      "description": "灰度階梯",
      "tokens": [
        { "name": "--ink-50", "value": "#f8fafc", "required": true },
        { "name": "--ink-100", "value": "#f1f5f9", "required": true }
        // ... 到 --ink-950
      ]
    },
    "semantic_color": {
      "description": "語意顏色（文字/狀態/品牌）",
      "tokens": [
        { "name": "--c-t1", "value": "#f0f4f8", "required": true },
        { "name": "--c-error", "value": "#ef4444", "required": true }
        // ...
      ]
    },
    // spacing / blur / timing / easing / border / shadow / typography ...
  },
  "mapping_table": {
    "description": "跨產品 token 映射（當存在多套 HTML 時）",
    "mappings": [
      { "from": "--c-950", "to": "--ink-950", "scope": "aps-compat" }
    ]
  },
  "validation_rules": {
    "description": "QA pipeline 驗證規則",
    "rules": [
      { "id": "C01", "check": "color_contrast", "min_ratio": 4.5 }
    ]
  }
}
```

**Gate 條件**：
- ✅ 每個 category 有至少 1 個 required token
- ✅ mapping_table 在多產品場景下不為空
- ✅ validation_rules 數量 ≥ 3

---

## D3 — Wireframe / Component Map

**Purpose**：用骨架 HTML 定義每個區塊的結構和 class 命名，Dev 只需填空內容。

**Template**：

```html
<!-- Wireframe: [頁面名稱] -->
<!-- Design Stage D3 — Christina YYYY-MM-DD -->
<!-- Status: skeleton only, content TBD -->

<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>[頁面名稱] Wireframe</title>
<style>
/* D3: 只寫骨架樣式，不寫內容 */
:root {
  --bg: #06080d;
  --t1: #f0f4f8;
  --t2: #a0a8b8;
  --accent: #14b8a6;
  --surface: rgba(255,255,255,.035);
  --border: rgba(255,255,255,.07);
  --s2: 1rem; --s4: 2rem; --s6: 3rem; --s8: 4rem;
}
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
body{font-family:var(--body);background:var(--bg);color:var(--t2);line-height:1.7}
/* ── Component skeleton ── */
.section { border: 1px dashed var(--border); padding: var(--s4); margin: var(--s2); }
.section::before { content: attr(data-label); display: block; font-size: .7rem; color: var(--accent); margin-bottom: .5rem; }
/* Hero / Grid / Table / Card 等骨架 ... */
</style>
</head>
<body>
  <!-- Wireframe block: Hero -->
  <section class="section hero" data-label="HERO">
    <h1>[標題 placeholder]</h1>
    <p>[副標 placeholder]</p>
  </section>

  <!-- Wireframe block: Content Grid -->
  <section class="section" data-label="CONTENT GRID">
    <div class="grid">
      <div class="card" data-label="card-1">[card]</div>
      <div class="card" data-label="card-2">[card]</div>
      <div class="card" data-label="card-3">[card]</div>
    </div>
  </section>

  <!-- Wireframe block: Table -->
  <section class="section" data-label="DATA TABLE">
    <table class="table">
      <thead><tr><th>[col-1]</th><th>[col-2]</th></tr></thead>
      <tbody><tr><td>[data]</td><td>[data]</td></tr></tbody>
    </table>
  </section>
</body>
</html>
```

**Checklist**：

- [ ] 每個 `section` 有 `data-label` 標註區塊名稱
- [ ] CSS 變數與 D2 Token Table 一致
- [ ] RWD breakpoints 已標註
- [ ] `<!-- TODO -->` 標註待 Dev 填充的內容區域
- [ ] 無 actual content（全是 placeholder）

---

## 使用範例：OTD Domain Model 回顧

| 任務 | D1 Spec Review | D2 Token Table | D3 Wireframe |
|------|:--------------:|:--------------:|:------------:|
| OTD Domain Model | ✅ 10/10 QA（spec 已存在） | ⚠️ 未建立（接現有 tokens.json） | ✅ otd-domain-model.html 視覺化 |

**教訓**：D2 可複用現有 tokens.json，不需要每次都從頭建立。但 D1（Spec Review）應該是強制 gate——OTD spec 如果有 D1 前置，就不會出現 B1-B4 四個邊角案例。

---

## Design Stage 執行節奏

| Step | Owner | 預計時間 | Gate |
|------|-------|----------|------|
| D1 Spec Review Comment | Christina | 20-40min | ≥ 8/10 QA |
| D2 Token Table | Christina | 10-20min | 所有 category 有 required tokens |
| D3 Wireframe | Christina | 30-60min | 所有 section 有 data-label |
| → Nana approve | Nana | 5min | D1+D2+D3 全通過 |
| → Dev Ready | Dev | — | Nana approve 後開工 |

**總預計**：60-120 分鐘（依任務大小伸縮）

---

## 附錄 A — Retro Benchmark 模板

> Allen 指令：用已完成任務做 before/after 比對。
> 每項 retro 選一個已完成任務，對照開發模式文檔中的流程檢查點。

### 範例 1：CRIS IMPACTs v1 → v2 → v3

| 維度 | v1 | v2 | v3 |
|------|-----|-----|-----|
| QA P0 | 3/6 | 5/6 | 6/6 |
| QA total | 12/22 | 18/22 | 22/22 |
| Lighthouse | P72 | P85 | P100 |
| 檔案大小 | 42KB | 55KB | 65KB |
| 交付時間 | Day 1 | Day 2 | Day 3 |
| 圖片處理 | base64 inline | 外部化 | 外部化 + lazy |

**教訓**：迭代重構 > 一次性改寫。v1→v2 的 QA 分數跳升最大（3→5 P0），不是改最多的一輪，而是先 fix P0 再改架構。

### 範例 2：gen_slides v3 → v4 重構

| 維度 | v3 (monolith) | v4 (modules) |
|------|--------------|--------------|
| 檔案行數 | 605 | 97 (CLI) + 4 modules |
| QA P0 | 3/6 (v3.2 baseline) | 6/6 |
| QA total | 15P/1F | 17P/0F/0W |
| Zero regression | — | ✅ 17P/0F/0W ×3 |
| 可維護性 | 難以單元測試 | extractor/renderer/upgrader/orchestrator 可獨立測試 |

**教訓**：模組化不是花時間重寫，是省未來的 debug 時間。Zero regression 認證證明拆解不破壞行為。

### 範例 3：OTD Spec → Review → Skeleton

| 階段 | 狀態 | 產出 |
|------|:--:|------|
| Spec v0.1-draft | ⚠️ 架構完整但缺 4 個邊角 | 360 行 spec |
| + Spec Review | ✅ 發現 4 建議 + 4 邊角 | 5.8KB review |
| + Domain Model | ✅ 視覺化四階段 | 18KB HTML |
| + Skeleton | ✅ 四模組 stub | 440 行 models.py + factory.json |

**教訓**：Spec QA 前置避免 Dev 階段回頭改 spec。如果 D1 gate 存在，Spec Owner 在 review 時就會修正 B1-B4，不需要等到 Skeleton 寫完才發現。

---

## 附錄 B — D2 Token Table 快速複用規則

當任務與現有產品（潤思 / APS / CRIS）共享視覺風格時：

1. **優先複用** `showcase/tokens.json` 中的 category
2. **有差異才建立新 category**，不要複製貼上
3. 新 token 必須滿足 D2 Gate：至少 1 個 required token
4. 更新 `mapping_table` 而非複製 entire token set

---

## 附錄 C — 常見 Dev 反饋與 Design 回應

| Dev 反饋 | Design 回應 |
|---------|------------|
| 「這個顏色太淺/太深」 | 調整 token value，不改 inline style |
| 「字體大小不對齊」 | 補 typography scale entry |
| 「這個元件沒有響應式」 | 補 RWD section in D3 wireframe |
| 「這個動畫太卡」 | 調整 --t-fast/--t-mid/--t-slow 或 easing |
| 「這個 gap/spacing 不對」 | 調 --s1~s10 grid，不改 margin inline |
