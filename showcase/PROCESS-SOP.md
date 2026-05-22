# PROCESS-SOP.md — Power Squad 權威作業流程

> 版本：v1.1
> 生效日：Allen 審批通過即時生效
> 編撰：Christina（監察組 — 設計審計）
> 合併來源：process-reform-v2.md + benchmark-research.md + sprint2-post-audit.md + Commander-D 閘門框架 + Technus Gate 定義
> 最後更新：2026-05-22 10:58 CST

---

## §1 角色定義

| 角色 | Agent | 職責 | 禁止 |
|------|-------|------|------|
| **主審（設計審計）** | Christina | Gate 0/1/3/4 主審 — 標竿審核、提案審核、Per-Checkpoint 監督、驗收簽核 | 不執行開發 |
| **覆核（流程紀律）** | Commander-D | Gate 3/4 覆核 — 流程紀律強制、雙簽覆核 | 不執行開發 |
| **監察組長** | Smart | CI/CD gate、infra 審計、技術驗收支援 | 不執行開發 |
| **首席開發** | Technus | 所有開發執行、build pipeline、engine、QA gate | 不自我驗收 |
| **Lead** | Nana | 任務優先級、方向決策 | — |
| **業主（Gate 2 唯一批准人）** | Allen | Gate 2 審批（不可代理）、終極戰略方向 | — |

**核心規則：監察組不開發，執行組不驗收自己。Gate 2 僅 Allen 可批准。**

---

## §2 五段 Gate 流程（強制）

```
G0: 標竿確認 ──→ G1: 正式提案 ──→ G2: Lead審批 ──→ G3: 開發監督 ──→ G4: 驗收雙簽
  審核: Christina    審核: Christina    審核: Allen       監督: Christina     簽核: Christina
                                                      + Commander-D      覆核: Commander-D
```

| Gate | 名稱 | 輸入 | 輸出 | 審核人 | 通過條件 |
|:----:|------|------|------|--------|---------|
| G0 | 標竿確認 | 任務方向 | Benchmark Report | **Christina** | ≥2 標竿引用，符合 §6 基準 |
| G1 | 正式提案 | Benchmark Report | Proposal（依 §3 模板） | **Christina** | 欄位齊全，標竿對齊 |
| G2 | Lead 審批 | Proposal + G0/G1 簽核 | 批准/退回 | **Allen（不可代理）** | Allen 明確批准 |
| G3 | 開發監督 | 已批准 Proposal | Artifact + QA Report | **Christina + Commander-D** | Per-checkpoint 合格 |
| G4 | 驗收雙簽 | Artifact + QA Report | 驗收決策 | **Christina 簽核 + Commander-D 覆核** | §5 清單全過 |

**鐵律：**
- G2 未通過 → G3 不得啟動
- Gate 2 僅 Allen 可批准，不可代理
- G4 雙簽缺一不可
- G4 未通過 → 任務退回 G3，不得 done

---

## §3 Proposal 強制模板

每份提案必須逐項填寫，缺一不可：

```markdown
## [提案] <標題>

### 1. 標竿對比
- 業界參考：（≥2 個，引用 benchmark-research.md 標竿）
- 與標竿的差距：
- 為什麼這樣做：

### 2. 範圍
- 做什麼：（具體產出）
- 不做什麼：（明確排除）
- 依賴項：（需先完成的任務）

### 3. 驗收標準
- [ ] <可量化標準 1>
- [ ] <可量化標準 2>
- [ ] <可量化標準 3>

### 4. 產出物
- 檔案路徑 / 類型 / 預估大小

### 5. 估時
- 預估：<X 分鐘>
- 複雜度：低 / 中 / 高

### 6. 風險
- 風險：
- 緩解方案：
```

---

## §4 Lead Absence Protocol（Allen 不可代理時的替代）

| 階段 | 時間 | 觸發條件 | G2 審批替代 |
|:----:|------|---------|------------|
| Tier 1 | 4h | Allen 未回應 | Christina + Commander-D 聯名簽核可放行 P1 以下 |
| Tier 2 | 12h | 仍無回應 | 同上，可放行 P0 以下 |
| Tier 3 | 24h | 仍無回應 | Christina + Commander-D + Smart 三人聯名全權審批 |
| Tier 4 | 48h | 仍無回應 | 直接 escalate Allen via 所有可用管道 |

**任何 Tier 下，G4 驗收仍需雙簽（Christina + Commander-D）。**

---

## §5 審計檢查清單

### P0 — 阻擋級（不合格 = 不驗收）
- [ ] 有對應的已審批 Proposal（G2 pass）
- [ ] HTML 結構完整（DOCTYPE / charset="UTF-8" / lang / viewport）
- [ ] 無 base64 內嵌圖片
- [ ] Lighthouse Performance ≥ P85
- [ ] Lighthouse Accessibility ≥ P90
- [ ] 零 console error
- [ ] 檔案 < 500KB

### P1 — 重要（不合格 = 退回修正）
- [ ] 使用 --ds-* Design System tokens（≥ 5 個不同 token）
- [ ] 鍵盤導航完整（Tab / Enter / Esc / 左右鍵）
- [ ] prefers-reduced-motion 尊重系統設定
- [ ] 響應式三斷點正常（sm:640 / md:768 / lg:1024）
- [ ] :focus-visible 可見

### P2 — 建議（記錄不阻擋）
- [ ] SEO meta（title / description / og:image）
- [ ] 載入動畫（skeleton / spinner）
- [ ] dark/light mode（prefers-color-scheme）

---

## §6 標竿基準

所有設計/開發決策必須對齊以下標竿（詳見 benchmark-research.md）：

| 領域 | 標竿 | 關鍵指標 |
|------|------|---------|
| 設計系統 | Apple HIG · Stripe | 一致性、層級化 token（--ds-{cat}-{name}-{scale}） |
| Token 標準 | W3C Design Tokens CG | $type / $value / $description 三層結構 |
| CI/CD | Vercel · Linear | deploy preview + diff report + auto-rollback |
| 品質 | Lighthouse P90+ | Performance / A11y / Best Practices / SEO |
| 可訪問性 | WCAG 2.1 AA | 對比度 ≥4.5:1、鍵盤全操作、prefers-reduced-motion |
| 流程治理 | Shape Up (Basecamp) | Shaping→Betting→Building→Cool-down |

**差距矩陣（P0 優先）：**
1. 🔴 Token 命名從扁平→層級化（--ds-space-sm / --ds-space-md）
2. 🔴 a11y 自動化（axe-core CI）
3. 🔴 預覽部署（Vercel preview URL）
4. 🟡 W3C token 格式遷移
5. 🟡 SEO meta 補齊

---

## §7 Board Chat 紀律

| 規則 | 說明 |
|------|------|
| 提案頻率 | 每 heartbeat ≤1 則提案，每日 ≤3 則 |
| 進度更新 | 僅在狀態有實質變化時發布 |
| 禁止 filler | 禁止「還在等」「checking in」類無資訊量訊息 |
| 審批請求 | 明確 @lead 或 @監察組，附提案連結 |
| 驗收記錄 | 必須貼 board chat（可追溯），不得僅在 task comment |

---

## §8 Daily Rhythm

### 監察組
- 每個 heartbeat：掃板 → 審計進行中任務 → 標記不合格項
- 每日 09:00：前日審計彙總（board chat）
- Sprint 結束：全線事後審計報告

### 執行組
- 無 G2 審批 pass → 只做標竿調研和提案撰寫，不做開發
- G2 pass → G3 開發 → 產出 + QA → 提交 G4 驗收
- 開發期間每 30m 更新 task comment（進度 + 證據）

---

## §9 Sprint 2 回溯審計摘要

| 層級 | 通過 | 總數 | 狀態 |
|:----:|:---:|:---:|:----:|
| P0 | 51 | 51 | 🟢 100% |
| P1 | 12 | 40 | 🔴 30% |
| P2 | 20 | 20 | 🟢 100% |

**P1 不合格明細：** --ds-* tokens 8/20 · 鍵盤導航 2/20 · prefers-reduced-motion 2/20
**修正負責：** Technus（執行組），Christina（監察組驗收）
**修正期限：** Sprint 3 結束前

---

## §10 事故教訓（從 45h 混亂中學到）

| # | 教訓 | 規則 |
|---|------|------|
| 1 | 無審批即開發 = 先斬後奏 | G2 未過，G3 不啟動 |
| 2 | 監察組缺席 = 無人把關 | 每個 heartbeat 強制掃板審計 |
| 3 | Lead 缺席無替代 = 全線凍結或失控 | Tier 1-4 escalation protocol |
| 4 | 提案 spam 淹沒決策 = 無效溝通 | ≤1/heartbeat, ≤3/day |
| 5 | 角色不分 = 自審自做 | 監察組不開發，執行組不驗收自己 |

---

## §11 審批記錄

| 角色 | 狀態 | 日期 |
|------|:----:|------|
| 監察組主審（Christina） | ✅ | 2026-05-22 10:58 |
| 監察組覆核（Commander-D） | ⏳ | — |
| 監察組（Smart） | ⏳ | — |
| 執行組確認（Technus） | ⏳ | — |
| **Lead 審批（Allen — Gate 2）** | ⏳ | — |

---

*PROCESS-SOP.md v1.1 · Commander-D 框架合併完成 · 待 Allen 審批生效*