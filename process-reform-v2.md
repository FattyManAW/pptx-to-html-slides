# Power Squad 流程整改方案 v2.0

> 撰寫：Christina（監察組 — 設計審計）
> 日期：2026-05-22 10:17 CST
> 觸發：Allen 群組廣播 — 全面整改指令
> 狀態：草案，待監察組審批後生效

---

## 🔴 整改原因

Allen 2026-05-22 10:17 群組廣播明確指出系統性問題：

1. **標竿/樣板先行未落實** — 沒有先找業界基準就直接開發
2. **提案→審批→執行 斷鏈** — 81+ 提案堆積零回覆，直接跳過審批開工
3. **監察組/執行組 角色模糊** — 三 agent 自審自做，失去外部監督
4. **監察組未按照提案監督與驗收** — 沒有提案→測試→驗收閉環

---

## 🎯 新工作流程

```
Phase 0: 標竿調研          監察組
  └─→ 產出 Benchmark Report

Phase 1: 提案              執行組
  └─→ 提交 Proposal（含標竿對比、範圍、驗收標準）

Phase 2: 審批              監察組
  └─→ 審核提案，通過 → Phase 3，拒絕 → 退回 Phase 1

Phase 3: 開發              執行組
  └─→ 按提案範圍開發，產出 Artifact

Phase 4: 驗收              監察組
  └─→ 對照提案驗收標準測試，通過 → Done，不通過 → 退回 Phase 3

Phase 5: 閉環審計          監察組
  └─→ 每 Sprint 結束，全線事後審計報告
```

**關鍵規則：**
- 任何開發必須先有已審批的提案
- 監察組不執行開發，執行組不自我驗收
- Nana/Allen 為最終審批人，監察組為第一線審批

---

## 👥 角色分配（草案）

### 監察組（2人）

| Agent | 定位 | 職責 |
|-------|------|------|
| **Smart** | 監察組長 | 提案審批 / CI/CD gate / infra 審計 / 最終驗收簽核 |
| **Christina** | 設計審計 | 標竿調研 / 設計品質審計 / token 一致性 / a11y / Lighthouse |

### 執行組（1人）

| Agent | 定位 | 職責 |
|-------|------|------|
| **Technus** | 首席開發 | 所有開發任務執行 / build pipeline / engine / QA gate |

> ⚠️ 角色分配為草案，待 Allen/Nana 最終確認。

---

## 📋 Proposal Template（強制格式）

每份提案必須包含以下欄位，缺一不可：

```markdown
## [提案] <標題>

### 1. 標竿對比
- 業界參考：（列出 2-3 個標竿案例）
- 我們與標竿的差距：
- 為什麼這樣做：

### 2. 範圍
- 做什麼：
- 不做什麼：
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
- 風險 1：
- 緩解方案：
```

---

## 🏷️ 標竿清單（基準線）

所有設計/開發決策必須對齊以下標竿：

| 領域 | 標竿 | 參考指標 |
|------|------|---------|
| 設計系統 | Apple HIG / Stripe Design | Token 命名、色彩體系、間距系統 |
| CI/CD | Linear / Vercel | deploy gate、preview URL、rollback |
| 品質 | Lighthouse P90+ | Performance / A11y / Best Practices / SEO |
| 可訪問性 | WCAG 2.1 AA | 對比度 4.5:1、鍵盤導航、螢幕閱讀器 |
| 響應式 | Tailwind breakpoints | sm:640 / md:768 / lg:1024 / xl:1280 |
| Token 命名 | W3C Design Tokens CG | --category-name 命名法 |

---

## 🔍 審計檢查清單

監察組每 Sprint 結束後執行：

### P0 — 阻擋級（不合格 = 不驗收）
- [ ] 所有產出有對應的已審批提案
- [ ] Lighthouse Performance ≥ P85
- [ ] Lighthouse Accessibility ≥ P90
- [ ] 零 console error
- [ ] HTML valid（DOCTYPE / charset / lang / viewport）

### P1 — 重要（不合格 = 需修正後重新驗收）
- [ ] 使用 Design System tokens（--ds-* namespace）
- [ ] 響應式三斷點正常
- [ ] 鍵盤導航完整
- [ ] 圖片無 base64 內嵌
- [ ] 檔案大小 < 500KB（不含外部資源）

### P2 — 建議（記錄但不阻擋）
- [ ] SEO meta tags
- [ ] 載入動畫
- [ ] dark/light mode 支援
- [ ] print stylesheet

---

## 📅 實施時間表

| 時間 | 行動 | 負責 |
|------|------|------|
| 現在 | 流程文檔 v2.0 發布（本文件） | Christina |
| 現在 | 標竿調研報告產出 | Christina |
| 現在 | Sprint 2 事後審計 | Christina |
| 10:30 | 監察組組內審批本流程 | Smart + Christina |
| 10:45 | 提交 Allen/Nana 最終審批 | 監察組 |
| 11:00 | 新流程生效，所有後續工作按新流程 | 全員 |

---

## ⚠️ 本文件狀態

- **版本：** v2.0-draft
- **審批：** 待監察組（Smart + Christina）組內審批 → Allen/Nana 最終審批
- **生效條件：** Allen 或 Nana 在 group chat 確認「通過」
- **取代文件：** AGENTS.md 中的自主開工規則（與此衝突的部分以此為準）

---

*Christina 產出 · 2026-05-22 10:17 · 待審批*