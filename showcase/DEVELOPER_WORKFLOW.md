# DEVELOPER_WORKFLOW.md — Power Squad 開發模式 v1

> AI Agent 專用 Spec-First Pipeline + Trunk-based CI Gate
> 適用：Power Squad + CRIS SWAT 兩板
> 版本：v1.0 | 2026-05-20 | 基於 35 項交付實戰經驗

---

## 目錄

1. [為 AI Agent 團隊設計](#為-ai-agent-團隊設計)
2. [六角角色矩陣](#六角角色矩陣)
3. [兩條 Pipeline](#兩條-pipeline)
4. [Gate 規則](#gate-規則)
5. [跨板協作](#跨板協作)
6. [示範專案](#示範專案)
7. [與 Scrum/Kanban/SAFe 的差異](#與-scrumkanbansafe-的差異)

---

## 為 AI Agent 團隊設計

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
3. **Gate over approve** — CI 自動化 gate（QA + Lighthouse + Token check）取代手動 approve
4. **Peer review over lead-only** — 交叉審查，lead 最終確認

---

## 六角角色矩陣

一人多角，主要/備援雙線。依專案類型動態切換。

| 角色 | 代號 | 主要 | 備援 | 產出 Artifact |
|------|:--:|:--:|:--:|------|
| 📋 **PM/PO** | Product Owner | **Nana** | — | Task spec + Acceptance Criteria |
| 🎨 **Design** | Designer | **Christina** | Smart | Design doc / Wireframe / Token spec / Color palette |
| ⚙️ **Dev** | Developer | **Technus** | Smart | 可執行產出 (code/HTML/Python) |
| 🔗 **DevOps** | Integrator | **Technus** | — | CI/CD pipeline / GitHub Actions / Deploy |
| 🧪 **QA** | Tester | **Smart** | Christina | QA Pipeline 報告 / Lighthouse 分數 / Test plan |
| 🔍 **Audit** | Reviewer | **Smart** | Nana | ADR / Consistency audit / Sprint retrospective |

### 角色切換規則

- **Infrastructure 任務**（CI/CD、QA cron、Lighthouse）：Dev + DevOps 雙角色，Dev→CI gate→Peer review→Deploy
- **New Product 任務**（OTD 模擬、新投影片）：Design→Dev→QA→Audit 全線
- **緊急接手**：備援角色在主要角色 >15m 無回應時自動切換

---

## 兩條 Pipeline

### Pipeline A: Trunk-based CI Gate（基礎建設類）

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

**證據**：35 項中 25+ 項已走過此路。CI gate 自動化後 Nana 從手動 approve 瓶頸解放。

### Pipeline B: Spec-First（新產品/複雜功能）

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

**證據**：OTD 已完整 demo 此流程（spec→review→skeleton 三層就位，等 Allen 確認方向→Dev）。

---

## Gate 規則

### 必要 Gate（Blocking）

| Gate | 觸發時機 | 驗證工具 | Fail 處理 |
|------|----------|----------|-----------|
| QA Gate | Dev 完成後 / PR 提交時 | `run_qa.py --once` | 退回 Dev 修復 |
| Lighthouse Gate | QA pass 後 | Lighthouse audit (≥P85) | 退回 Dev 修復 |
| Token Gate | QA + LH pass 後 | `extract-tokens.py --check` | Warning（不 block） |
| Design Review | Spec-First 模式下 | 設計稿 vs 成品對照 | 退回 Design 修正 |
| Peer Review | 所有 gate pass 後 | 交叉審查 | Discussion → rework |
| Lead Confirm | Peer review pass 後 | Nana 最終確認 | 退回或 approve |

### 選擇性 Gate（Non-Blocking）

| Gate | 工具 | 用途 |
|------|------|------|
| Consistency Audit | consistency-audit.md | 跨產品一致性掃描 |
| ADR Record | adr/ 目錄 | 架構決策記錄 |
| Sprint Retro | PLAYBOOK.md | 週期性回顧 |

---

## 跨板協作

### Power Squad + CRIS SWAT

兩板共享：
- **QA 標準**：qa_pipeline.py + run_qa.py
- **設計系統**：tokens.json + Design System Reference
- **CI/CD 模板**：.github/workflows/deploy.yml
- **開發模式**：本文件（DEVELOPER_WORKFLOW.md）

溝通規則：
- 跨板討論 → 潤思科技 group chat
- 板內討論 → 各自 board chat
- 不得私下 DM（保持透明、可追溯）

---

## 示範專案

### 潤思 IMPACTS HTML v4 — 全程 Spec-First Pipeline

目標：用新模式重新產出潤思 IMPACTS，對比現有 v3.1 成果。

| Step | 角色 | 產出 | Gate |
|------|:--:|------|:--:|
| 1 | 📋 Nana | Task spec（需求 + AC） | — |
| 2 | 🎨 Christina | Design doc（排版/motion/color spec） | — |
| 3 | 🔍 Smart | Peer review spec + test plan | Design Review |
| 4 | 🎨 Christina | Skeleton stub（HTML 框架） | — |
| 5 | ⚙️ Technus | 完整 HTML v4 | — |
| 6 | 🧪 CI | QA Gate + Lighthouse Gate | QA Gate + LH Gate |
| 7 | 🎨 Christina | Visual QA（設計稿 vs 成品） | Design Review |
| 8 | 🔍 Smart | Audit + ADR | Peer Review |
| 9 | 📋 Nana | Lead Confirm | Lead Confirm |
| 10 | 🔗 Technus | Deploy to gh-pages | — |

**成功標準**：v4 QA score ≥ v3.1 (17/17) · Lighthouse ≥ P100 · 生產時間 ≤ v3.1 原始時間

---

## 與 Scrum/Kanban/SAFe 的差異

| 維度 | Scrum | Kanban | SAFe | **我們的模式** |
|------|-------|--------|------|----------------|
| Sprint | 2w 固定 | 無 | PI (8-12w) | **活動態，heartbeat 驅動** |
| Standup | Daily | 無 | Daily | **Board chat + heartbeat** |
| Role | 固定（SM/PO/Dev） | 無 | 多層 | **一人多角，依任務切換** |
| Gate | DoD checklist | WIP limit | PI gate | **CI 自動化 gate chain** |
| 估時 | Story points | 無 | WSJF | **實際耗時（分鐘）** |
| Review | Sprint review | 無 | System demo | **Peer review + CI gate** |
| Retro | Sprint retro | 不定期 | PI retro | **Sprint retro 按需觸發** |

---

## 版本演進

| 版本 | 日期 | 變更 |
|------|------|------|
| v1.0 | 2026-05-20 | 初版 — 基於 35 項交付實戰經驗 |

---

> **「不是誰做什麼，而是每個階段產出可驗證的 artifact → gate → 下一階段。」**
> — Power Squad 開發模式核心原則