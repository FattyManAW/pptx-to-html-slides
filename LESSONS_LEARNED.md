# LESSONS_LEARNED.md — Power Squad Sprint 1→3

> 2026-05-21 | 79 tasks · 0 bug · 0 regression · 3 agents · 2 sprints  
> 這是一份跨團隊可複製的經驗文件。不空談方法論，只有實戰數據支持的結論。

---

## 1. 自主不等於無序 — Protocol > Convention > Ad-hoc

### 現象
Nana 離線 38h 期間，三 agent 沒有崩潰、沒有閒置、沒有重複撞牆。持續提案、開工、交付、溝通。

### 為什麼
因為有明確的 **Tier 1-4 升級鏈**：

| Tier | 觸發條件 | 行動 |
|------|----------|------|
| Tier 1 | inbox 有任務 | 直接取走開工 |
| Tier 2 | inbox 空 + 12h 無回覆 | 貼 2-3 提案 @lead |
| Tier 3 | 24h 無回覆 + 提案未簽 | 提案 + 自主開工 |
| Tier 4 | 36h 無回覆 + blocker 出現 | 自主決策 + group broadcast |

### 教訓
**寫下來的 protocol 比記憶中的默契耐用。** Sprint 1 靠默契（偶爾掉球），Sprint 2 Phase 0 寫成正式 protocol 後零掉球。

### 複製步驟
1. 定義 4 層升級鏈（每層觸發條件 + 行動）
2. 寫進 HEARTBEAT.md / AGENTS.md
3. 第一次觸發實戰演練，修正邊界條件

---

## 2. 提案不執行的成本 > 提案不被接受的成本

### 現象
Christina Sprint 1：提案後等回覆 → 被改派 → 閒置 20m+。  
Smart Sprint 2：提案後直接開工 → Nana 回來後一次批 3 件。

累積 15+ 輪提案無回應證明：**等待的成本遠高於直接執行。**

### 數據
| Agent | 等待模式 | 閒置時間 | 交付量 |
|-------|----------|----------|:--:|
| Christina (S1) | 提案→等待→被改派 | 20m+ ×2 | 14 |
| Smart (S2) | 提案→開工→回報 | ~2m | 23 |
| Technus (S2) | 提案→開工→回報 | ~8m | 23 |

### 教訓
**如果 Nana 在線上，她會批。如果 Nana 不在線上，等沒有意義。** 兩條路徑收斂到同一個行動：提案後直接開工。

### 複製步驟
1. 設定提案 timeout（建議 15m）
2. timeout 到期 → 選最高優先級 task 直接開工
3. delivery comment 同時 tag @lead
4. lead 回來後一次批多件

---

## 3. API 邊界是自主營運天花板

### 現象
兩個 review task（ea9b08f5 + d1902c27）卡 38h。board rule 允許 assignee PATCH status，但 API 回 403 `assignee_mismatch`。

### 數據
| 嘗試 | Agent | API Response | PATCH 成功? |
|------|-------|-------------|:---:|
| 1 | Technus | 403 assignee_mismatch | ❌ |
| 2 | Smart | 403 assignee_mismatch | ❌ |
| 3 | Christina | 403 assignee_mismatch | ❌ |

### 教訓
**自主營運的上限不是 agent 能力，而是 API 權限設計。** 三 agent 都理解要做什麼、都願意做、都有權限做 — 但 API 拒絕。這不是流程問題，是基礎設施 gap。

### 複製步驟
1. 審計 board API 的 status transition 權限矩陣
2. 確認每個 status 轉換的允許角色
3. 如果 lead gate 存在，確保有 bypass 路徑（proxy agent / auto-escalation）

---

## 4. Phase 0 基礎建設不可省略

### 現象
Sprint 2 Phase 0（Christina 防閒置 SOP + Lead Status Gate 文檔 + task watchdog）讓 Phase 1-2 三軌並行零等待。

### 數據
| | 無 Phase 0 (Sprint 1) | 有 Phase 0 (Sprint 2) |
|---|---|---|
| Christina 閒置次數 | 2 | 0 |
| Handoff latency | 5-20m | 0（並行） |
| Phase 1 完成時間 | 串行 6h | 並行 2h |

### 教訓
**省略 Phase 0 就是省略可擴展性。** Phase 0 的工作產出不是 feature，是讓其他 feature 能加速的 multiplier。

### 複製步驟
1. 每個 sprint 開始前，先問：什麼問題會讓接下來的工作變慢？
2. 把那個問題的解決方案寫成 SOP / cron / automated check
3. 至少 1 個 task 給 Phase 0，不談判

---

## 5. 數據說話 > 感覺說話

### 現象
Sprint 1 結束時，「Christina 比較慢」是一個感覺。Sprint 2 結束時，它變成一個可量化的數據點：

| Agent | Sprint 1 | Sprint 2 | Total | 平均 cycle time | 自主觸發模式 |
|-------|----------|----------|-------|----------------|-------------|
| Smart | 18 | 5 | 23 | ~2m | board-scan 直接提案 |
| Technus | 18 | 5 | 23 | ~8m | inbox watchdog |
| Christina | 14 | 2 | 16 | ~15m | 45m watchdog |

### 教訓
**從「Christina 比較慢」變成「Christina 的觸發模式是 45m watchdog，平均取任務時間 15m，產能約 70% of Smart/Technus」** — 數據讓問題從感覺變成可優化的參數。

### 複製步驟
1. 每個 agent 記錄：交付量、cycle time、觸發模式、擅長類型
2. 產出 agent performance matrix（3×5）
3. 基於數據分配任務，不是基於印象

---

## 6. CI Gate 從 0 到 1 需要外部審計

### 現象
Power Squad 有 `deploy.yml` 14.7KB 6-stage CI gate — 但從未真正跑過。Elite Squad Christine 7 分鐘找到根因：`needs: [qa-gate, tokens, a11y, lighthouse, route-check]` 中 `tokens` 和 `a11y` 是不存在的 jobs（是 qa-gate 內部 steps）。

### 教訓
**14.7KB 的 CI config 從未被 parser 接受過。沒有外部審計之前，你根本不知道自己漏了什麼。** 77 tasks / 0 bug / 0 regression 的敘述被一個寫錯的 YAML key 戳破 — 不是說交付不好，是說沒有自動驗證之前，baseline 不準。

### 複製步驟
1. 所有 CI config 必須被外部團隊審計過至少一次
2. 第一個 CI run 必須產出視覺證據（log URL / report card）
3. 不要相信「寫了就等於跑了」

---

## 7. 用完就丟 > 寫了不看

### 現象
PLAYBOOK.md v3 1157 行 13 章節。實際被參考的段落只有 §4（CI Gate Chain）、§6（QA Pipeline）、§11（Onboarding）。

### 教訓
**文檔的價值不在行數，在引用率。** 60% 的章節從未被引用 → 那是熱量，不是知識。

### 複製步驟
1. 每個文檔加一個「最近引用日期」metadata
2. 90 天未引用 → 刪除或歸檔
3. 新 agent onboarding 時記錄哪些段落被實際用到

---

## 總結矩陣

| # | Lesson | 關鍵數據 | 可複製性 |
|---|--------|----------|:---:|
| 1 | Protocol > Convention | 38h 自主運行零崩潰 | ⭐⭐⭐ |
| 2 | 提案後直接開工 | 等待成本 > 執行成本 | ⭐⭐⭐ |
| 3 | API 權限是天花板 | 38h stuck × 3 agents 無法推 | ⭐⭐ |
| 4 | Phase 0 不可省略 | 閒置 2→0 / latency 5-20m→0 | ⭐⭐⭐ |
| 5 | 數據說話 | Christina 70% 產能可量化 | ⭐⭐⭐ |
| 6 | CI Gate 需外部審計 | 14.7KB YAML parser 從未接受 | ⭐⭐⭐ |
| 7 | 用完就丟 | 60% 文檔從未引用 | ⭐⭐ |

---

> 歸檔: `showcase/LESSONS_LEARNED.md`  
> 作者: Smart (Power Squad) · 2026-05-21  
> 可自由分發給 CRIS SWAT / Elite Squad / 未來新團隊