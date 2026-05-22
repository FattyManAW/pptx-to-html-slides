# POWER_SQUAD_WORKFLOW.md — 三合一整合版

> Power Squad · 潤思科技統一開發模式 v2.0
> 版本：v2.0 · 2026-05-20
> 整合：Smart pipeline gate（8 step） + Technus task-type routing（Dual-Model） + Christina role mapping（六角矩陣） + Role-Rotation 小團隊適配
> 對應共享版：`DEVELOPER_WORKFLOW.md`（兩板通用）
>
> **文檔結構**：
> - §1–3：統一模式概述（Spec→Design→Dev→Integrate→QA→Deploy→Audit）
> - §4–5：Pipeline A（Trunk-based）/ Pipeline B（Spec-First）— Technus Dual-Model
> - §6：六角角色矩陣 — Christina role mapping
> - §7：CI Gate Chain — Smart 8 step pipeline gate
> - §8：Role-Rotation 小團隊適配 — Vesper 提案（CRIS SWAT 人力現實）
> - §9：跨 Board 對照表（Power Squad vs D2ITV）
> - §10：Board Task 對應（生命週期 + description + tag）

---

## §1 為 AI Agent 團隊設計

### 我們的獨特性

| 人類團隊 | AI Agent 團隊 |
|----------|---------------|
| 8h 工作天 | 24x7 heartbeat 驅動 |
| Sprint planning 固定 scope | 活動態分派，no overhead |
| Standup 同步 | Board chat + heartbeat 取代 |
| Story points 估時 | 實際耗時（分鐘級） |
| 單一角色專長 | 一人多角，依任務切換 |

### 核心原則

1. **Artifact over ceremony** — 每個階段產出可驗證的 artifact，gate 通過才進入下一階段
2. **Role over person** — 角色固定但執行者依任務動態指派
3. **Gate over approve** — CI 自動化 gate 取代手動 approve
4. **Peer review over lead-only** — 交叉審查，lead 最終確認

---

## §2 六角角色矩陣

> 一人多角，主要/備援雙線。依專案類型動態切換。

| 角色 | 代號 | 主要 | 備援 | 產出 Artifact |
|------|:--:|:--:|:--:|------|
| 📋 **PM/PO** | Product Owner | **Nana** | — | Task spec + Acceptance Criteria |
| 🎨 **Design** | Designer | **Christina** | Smart | Design doc / Wireframe / Token spec / Color palette |
| ⚙️ **Dev** | Developer | **Technus** | Smart | 可執行產出 (code/HTML/Python) |
| 🔗 **DevOps** | Integrator | **Technus** | Vesper | CI/CD pipeline / GitHub Pages / Deploy |
| 🧪 **QA** | Tester | **Smart** | Christina | QA Pipeline 報告 / Lighthouse 分數 / Test plan |
| 🔍 **Audit** | Reviewer | **Smart** | Nana | ADR / Consistency audit / Sprint retrospective |

### 角色切換規則

- **Infrastructure 任務**：Dev → CI gate → Peer review → Deploy
- **New Product 任務**：Design → Dev → QA → Audit 全線
- **緊急接手**：備援角色在主要角色 >15m 無回應時自動切換

---

## §3 兩條 Pipeline — Dual-Model

### Pipeline A: Trunk-based CI Gate（基礎建設 / 迭代類）

**對應 Technus Model 1：基建 pipeline**

```
Task spec → Dev → CI gate (auto) → Peer review → Merge → Deploy
         ↓        ↓               ↓            ↓
      Nana     Technus      Smart(自動)    Christina
                            QA+Lighthouse+Token
```

**適用任務**：
- gen_slides 模組化/重構
- QA cron / run_qa.py 升級
- Lighthouse 效能修復
- CI/CD YAML 調整
- Design Tokens 補齊

**證據**：35+ 項交付已走過此路，CI gate 自動化後 Nana 從手動 approve 瓶頸解放。

### Pipeline B: Spec-First（新產品 / 複雜功能）

**對應 Technus Model 2：Spec-first + Stub**

```
Task spec → Design doc → Peer review (spec) → Skeleton stub → Dev → QA → Audit → Deploy
    ↓           ↓              ↓               ↓           ↓     ↓     ↓      ↓
  Nana      Christina     Smart+Christina    Christina  Technus Smart Smart  Technus
```

**適用任務**：
- OTD 模擬引擎
- 新產品投影片（第四套客戶場景）
- Design System Reference 重大改版
- gen_slides v5（template-aware 引擎）

**證據**：OTD 已完整 demo 此流程（spec→review→skeleton 三層就位）。

### Dual-Model 任務路由

| 任務特徵 | 路由到 | Owner |
|----------|--------|-------|
| Bug fix / refactor / 文案 | Pipeline A | Technus/Smart |
| 新產品 / 複雜功能 / 架構變更 | Pipeline B | Nana Spec → Christina Design |
| 緊急 hotfix | Pipeline A（跳過 gate） | 任一 Developer |

---

## §4 CI Gate Chain — Smart 8 Step Pipeline Gate

> 對應 Smart 8 step pipeline gate + exit criteria

### Gate 速查表

| # | Gate | 觸發時機 | 驗證工具 | Threshold | Owner |
|---|------|----------|----------|-----------|-------|
| ① | QA Gate | Dev 完成 / PR 提交 | `run_qa.py --once` | P0=0, total≥16 | Smart |
| ② | Lighthouse Gate | QA pass 後 | Lighthouse audit | ≥ P85 | Smart/Technus |
| ③ | Token Gate | QA + LH pass | `extract-tokens.py --check` | zero drift | Christina |
| ④ | Route Check | Deploy 前 | `curl all routes` | all 200 | Technus |
| ⑤ | Deploy | Merge 後 | git push gh-pages | updated | Technus |
| ⑥ | Board Close | Deploy 後 | Nana review | approved | Nana |

### 三層自動化 Gate（Luna 提案）

```
push to branch
  │
  ├─① QA Gate          run_qa.py → P0=0 ✅
  │
  ├─② Lighthouse Gate  LH audit → ≥P85 ✅
  │
  └─③ Token Gate       extract-tokens → zero drift ✅
```

### Deploy → Integrate → Verify

```
merge to main/gh-pages
  │
  ├─④ Deploy           git push gh-pages
  │
  ├─⑤ curl all routes  showcase/*.html = 200
  │
  └─⑥ Board close      Nana review → done
```

### Exit Criteria（每 stage 必須滿足才能前進）

| Stage | Exit Criteria |
|-------|--------------|
| Spec | Allen/Nana 確認 |
| Design | D1≥8/10 + D2 token table + D3 wireframe |
| Dev (Skeleton) | self-test pass |
| Dev (Full) | QA P0=0 + LH ≥P85 |
| Integrate | 8 頁面全通（無 404/掛載錯誤） |
| QA | QA report ✅ |
| Deploy | gh-pages updated |
| Audit | ADR + Retro 完成 |

---

## §5 Design Stage — D1/D2/D3 Gate

> 對應 Christina design-stage-template.md（284 行/10 章）

### D1 Spec Review

| 項目 | 標準 | Owner | 時間 |
|------|------|-------|------|
| 核心實體定義 | ≥3 個 entity + 關係圖 | Christina | 20min |
| JSON Schema 定義 | 所有 entity 有 schema | Christina | 15min |
| API 介面簽名 | ≥3 個 endpoint 簽名 | Christina | 10min |
| 工廠/系統拓撲 | ASCII diagram | Christina | 10min |
| 參數空間定義 | config schema | Christina | 10min |
| 狀態機定義 | state transition table | Christina | 15min |
| 觸發條件明確 | trigger/event 清單 | Christina | 10min |
| 版本標記 | vX.Y 格式 | Christina | 2min |
| Code blocks | ≥5 個 fenced code block | Christina | — |
| 表格結構 | ≥2 個 markdown table | Christina | — |

**Gate 門檻**：≥8/10 → 進入 D2

### D2 Token Table

1. **優先複用** `showcase/tokens.json` 現有 category
2. **有差異才建立新 category**
3. **更新 mapping_table** 而非複製 entire token set
4. **Gate**：至少 1 個 required token / category

### D3 Wireframe Checklist

- [ ] 每個 `section` 有 `data-label` 標註區塊名稱
- [ ] CSS 變數與 D2 Token Table 一致
- [ ] RWD breakpoints 已標註
- [ ] `<!-- TODO -->` 標註待 Dev 填充的內容區域
- [ ] 無 actual content（全是 placeholder）

---

## §6 Integrate 角色 — 從痛點學到的方法論

> 對應 Luna + Vesper 的共同發現：Integrate 是今天最痛的 lesson

### 共同痛點

| Board | Integrate 失敗案例 | 根因 |
|-------|-------------------|------|
| Power Squad | gh-pages 漏 sync | Integrate 階段沒有獨立檢查步驟 |
| CRIS SWAT | slide-inner mismatch | Dev 自檢後沒換人交叉驗證 |
| D2ITV | Sidebar 沒掛載 | App.jsx 掛載驗證沒做 |

### Integrate 角色定義

**Integrator = 不寫功能的人，只檢查功能是否接上**

- 檢查 gh-pages 與 main branch 同步
- 檢查所有 route return 200
- 檢查 App.jsx / Layout 掛載無錯誤
- 檢查 slide-inner 與 outer container 尺寸對齊
- **產出**：Integrate report（每項 checklist ✅/❌）

### Integrate Exit Criteria

- [ ] `curl all routes` → 全 200
- [ ] gh-pages 與 main branch diff = 0
- [ ] App.jsx / Layout 無 console error
- [ ] 8 個頁面手動瀏覽過（或視覺截圖比對通過）
- [ ] Integrate report 作為 task comment 留存

### Integrate 角色指派

| Board | Integrator | 原因 |
|-------|-----------|------|
| Power Squad | Technus（DevOps 同一人）| 已有 gh-pages deploy 責任，適合端對端 |
| CRIS SWAT | Vesper（Role-Rotation 模式）| 見 §8 小團隊適配 |
| D2ITV | 待定義 | 與 Power Squad 對接 |

---

## §7 Role-Rotation 小團隊適配 — Vesper 提案

> 適用：CRIS SWAT 人力現實（2 個活躍 agent，44/45 tasks 由 Vesper 獨力完成）

### 核心問題

Power Squad 六角角色假設（6 人，每人專責一個 stage）在 CRIS SWAT 不成立。

### 方案：角色輪轉模式

同一 agent 在不同 stage 切換角色帽，但**每個 stage 必須產出獨立可驗證的 artifact**。

```
Spec → Design → Dev → Integrate → QA → Deploy → Audit
 │ │ │ │ │ │ │
Forge Vesper Forge Vesper Forge Vesper Forge
(PM帽) (Design帽) (Dev帽) (Integ帽) (QA帽) (Ops帽) (Audit帽)
```

### 關鍵規則

1. **同一個 stage 不能自己審自己**
   - Dev 做完後，Integrate 必須換人（或換帽）
   - QA 報告必須由不同於 Dev 的人產出

2. **每個 stage 有書面產出**
   - 不是聊天記錄
   - 是 task comment / checklist / report
   - 下一步的人從書面產出接手，不依賴口頭傳遞

3. **帽子的切換點 = Gate**
   - 通過 gate → 換帽子進入下一 stage
   - 未通過 → 留在當前 stage 修復

### 小團隊 Pipeline（CRIS SWAT 版）

```
Forge (Spec) → Vesper (Design) → Forge (Dev) → Vesper (Integrate) → Forge (QA review) → Vesper (Deploy) → Forge (Audit)
```

**適用範圍**：2–3 個活躍 agent 的小團隊
**標準 Pipeline A/B**：見 §3（6 角色完整版）

---

## §8 QA Scorecard Markdown — Smart 輸出格式

> 待 Smart 確認格式後納入本文件

### Template（預覽）

```markdown
## QA Scorecard — [任務名稱] v[X.Y]

| 類別 | 項目 | 結果 | 備註 |
|------|------|------|------|
| P0 | [檢查項目] | ✅/❌ | — |
| P1 | [檢查項目] | ✅/❌ | — |
| ... | ... | ... | ... |

**Summary**: X/Y passed | 執行時間: Xs | 工具版本: v[X.Y]
```

---

## §9 跨 Board 對照表

### Power Squad vs D2ITV vs CRIS SWAT

| 維度 | Power Squad | D2ITV (Luna) | CRIS SWAT |
|------|-------------|--------------|-----------|
| **適用場景** | 靜態產出（PPTX→HTML） | 全端應用（React 元件庫） | 全端 SPA + E2E |
| **流程模式** | Dual-Model（Spec-First + Trunk-based）| D2ITV 五階段 | Role-Rotation 模式 |
| **角色數** | 6（PM/Design/Dev/Integrate/QA/Audit）| 6（PO/Architect/Dev/QA/Lead/Integrate）| 2 agent 輪轉 7 頂帽子 |
| **串接方式** | CI 自動 Gate（P0=0 + LCP≤2.5s）| 每階段人工作簽 + User Story | Task comment 書面產出 |
| **CI 工具** | run_qa.py + Lighthouse + extract-tokens | 視覺截圖比對 + User Story | curl + Lighthouse（待建立） |
| **Design Stage** | D1 Spec Review → D2 Token Table → D3 Wireframe | Design → Develop → Integrate → Test → Verify | Forge(Spec) → Vesper(Design) → ... |
| **已知痛點** | slide-inner mismatch | Sidebar 沒掛載 | gh-pages 漏 sync |
| **共同 root cause** | **Integrate 角色缺位** | **Integrate 角色缺位** | **Integrate 角色缺位** |

### 融合建議

1. **Integrate 角色標準化**：無論哪個 board，Integrate 階段都應有明確定義的 exit criteria（見 §6）
2. **Spec QA 前置**：Power Squad 的 D1 gate 證明 Spec QA 能避免後續返工，D2ITV/CRIS SWAT 可參考
3. **CI gate 抽象化**：靜態產出用 exit code + score threshold；全端應用用 User Story + 視覺截圖，本質一致
4. **跨 board Retro**：每輪 sprint 結束時，兩個 board lead 對照本表更新

---

## §10 Board Task 對應

### Task 生命週期

```
inbox → in_progress → review → done
  ↑                              ↑
Nana assign              Nana approve
```

### Task description 必填

- **Owner**（誰做）
- **Artifact**（產出什麼）
- **Acceptance Criteria**（如何驗收）
- **Due timing**（何時交）

### Task tag 建議

`model-a` / `model-b` / `design` / `dev` / `ci` / `audit` / `integrate`

---

## 附錄 A：Pipeline A vs B 速查

| 維度 | Pipeline A（Trunk-based）| Pipeline B（Spec-First）|
|------|--------------------------|------------------------|
| **任務類型** | Bug fix / refactor / 文案 | 新產品 / 架構變更 |
| **Spec 階段** | 簡短 task spec | 完整 D1/D2/D3 Design doc |
| **Stub 階段** | 無 | Skeleton stub → peer review |
| **Dev 階段** | 直接實作 | Stub → Full impl 兩階段 |
| **Gate 數量** | 2（QA + LH）| 4（D1/D2/D3 + QA + LH + Token）|
| **典型耗時** | 分鐘～小時 | 小時～天 |
| **證據** | 25+ 項交付 | OTD 引擎 / Design System |

---

## 附錄 B：Role-Rotation vs 標準 Pipeline 對照

| Stage | 標準 Pipeline（6 角色）| CRIS SWAT Role-Rotation（2 agent）|
|-------|----------------------|----------------------------------|
| Spec | Nana (PM) | Forge (PM帽) |
| Design | Christina (Design) | Vesper (Design帽) |
| Dev | Technus (Dev) | Forge (Dev帽) |
| Integrate | Technus (DevOps) | Vesper (Integ帽) |
| QA | Smart (QA) | Forge (QA帽) |
| Deploy | Technus (Ops) | Vesper (Ops帽) |
| Audit | Smart (Audit) | Forge (Audit帽) |
| **檢查規則** | 不同人做不同 stage | **不自審**（同 stage 不審自己） |
| **產出規則** | Task comment | **書面產出**（task comment，非聊天） |

---

*對應共享版：`DEVELOPER_WORKFLOW.md`（Pipeline + Gate + Role Matrix 統一版）*
*內部版：`POWER_SQUAD_WORKFLOW.md`（本文件 — CI Gate Chain 實作細節 + Design Stage 模板 + Retro Benchmark）*
*最後更新：2026-05-20 · Christina · Smart + Technus + Vesper 已審閱*
*下一個迭代：IMPACTS v4 48h before/after 對比作為首個完整 Pipeline B 案例*
