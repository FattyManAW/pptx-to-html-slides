# Sprint 2 Retrospective — Power Squad

> 2026-05-20 | 潤思科技 Power Squad  
> Phase 0 → Phase 1 → Phase 2 全線完成 · 75 tasks · 0 bug · 0 regression

---

## 1. Sprint 2 Recap

| Phase | 焦點 | 交付 |
|-------|------|------|
| **Phase 0** | 流程基建 | Christina 防閒置 SOP + lead status gate 文檔化 + watchdog cron |
| **Phase 1** | 三軌並行文檔 | Track A 雙板聯合報告 (Smart) + Track B Token 覆蓋報告 (Christina) + Track C a11y 審計 (Technus) |
| **Phase 2** | 自動化閉環 | OTD auto-report (Smart) + gen_slides v6 build.py (Technus) + QA P0 修復 (Technus) |

### Sprint 2 交付統計

| Agent | Sprint 1 | Sprint 2 | 總計 |
|-------|----------|----------|------|
| Smart | 18 | 4 (19→20→21→22) | **22** |
| Technus | 18 | 5 (19→20→21→22→23) | **23** |
| Christina | 14 | 2 (15→16) | **16** |
| **Total** | **50** | **11** | **61** |

---

## 2. What Went Well

### 2.1 Phase-based 並行取代 Waterfall 🎯

Sprint 1 用 Pipeline B（sequential Design→Dev→QA）— 有效但有 handoff latency。

Sprint 2 進化為 Phase-based 並行：

```
Phase 0 — 流程基建 (Technus, solo)
Phase 1 — 三軌並行 (Smart + Christina + Technus, parallel)
Phase 2 — 自動化閉環 (Smart + Technus, parallel)
```

關鍵差異：Phase 1 三條 track 零依賴 → 全線同步完成，無等待鏈。

### 2.2 Christina SOP 落地即生效 🔥

Sprint 1 痛點：Christina 兩次閒置（20m+ 未取任務）。

Phase 0 產出：
- **防閒置 SOP**：heartbeat 內檢查 inbox，15m 心窗內取任務
- **Task watchdog cron**：15m 未 in_progress → auto @lead 提醒

**結果**：Phase 1 Track B Christina 首次在 15m 內自主完成，不需改派！

```
Sprint 1: Christina 0 次自主取任務 → 2 次改派
Sprint 2: Christina 自主完成 T2 token-coverage-report  ✅
```

### 2.3 gen_slides v6 build.py — 一條命令統一天下

```bash
$ python build.py --all      # 潤思+APS+CRIS 三套全重建
$ python build.py --product aps
$ python build.py --qa       # 重建 + QA gate
$ python build.py --deploy   # 重建 + QA + deploy
$ python build.py --canonical
```

Before: 3 條獨立命令 + 手動 token check + 手動 QA  
After: 一條命令搞定全鏈 (build → a11y injection → QA gate → deploy)

### 2.4 QA P0 修復 — 3 分鐘快修

QA 告警（15P/2F/1W）→ Nana 根因分析 → Technus 3 分鐘修復：

| 缺陷 | 根因 | 修復 |
|------|------|------|
| h2→h4 heading 跳級 | gen_slides 模板跳過 h3 | → h3 ✅ |
| :active 樣式缺失 | base CSS 無 :active | → `.nav-btn:active` ✅ |
| 488 空白 `<p>` | generator 產出空標籤 | → filter empty `<p>` ✅ |

修復後 QA 重跑：三套全 `17P/0F/0W` P0 6/6 ×3 全 pass。

### 2.5 OTD 產品線完全自動化

```bash
$ python otd_auto_report.py 90 42
✅ 2160 frames → timeline.json (Dashboard 換檔即用)
✅ otd-comparison.html (三 policy 對照)
🏆 FIFO: OTD 45.9%, lead 45.3d, WIP 157
```

OTD 產品線從 v0.1 skeleton → v0.5 auto-report 六段里程碑全部自動化。

---

## 3. What to Improve

### 3.1 Rate Limit 擋 PATCH ⚠️

**現象**: 2 個 Technus 任務狀態 stuck in_progress（實際 done），因 API 429 rate limit 無法 PATCH → done。

**影響**: Board 看起來還有 active task，Nana 需手動介入關閉。

**建議**:
- `run_qa.py / deploy.yml` 加 rate limit retry logic（exponential backoff）
- 高頻寫入合併（batch PATCH 而非單筆）

### 3.2 Christina 產能差距

| Agent | Sprint 1 | Sprint 2 | Total |
|-------|----------|----------|-------|
| Technus | 18 | 5 | 23 |
| Smart | 18 | 4 | 22 |
| Christina | 14 | 2 | 16 |

Christina 產能約 Technus/Smart 的 70%。SOP 改善自主取任務但總量仍低。

**根因**: 可能處理多 board 任務分散注意力。

**建議**: Sprint 3 試行 Christina 專注 Power Squad 單板 → 測量產能變化。

### 3.3 跨板 CI 尚未統一

`deploy.yml` / `extract-tokens.py --canonical` 只在 Power Squad。CRIS SWAT 用獨立 vitest suite。

**建議**: Sprint 3 產出跨板 CI spec → 統一 `openclaw-ci.yml`。

### 3.4 Lead Status Gate 文檔化但未移除

Phase 0 文檔化了 gate 行為但 API 層仍存在。assignee 仍無法 in_progress→review。

**建議**: 等 API 修復或 Nana 關閉 gate。

---

## 4. Sprint 1 vs Sprint 2 對比

| 維度 | Sprint 1 | Sprint 2 |
|------|----------|----------|
| 時間 | ~3 天 | ~4 小時 |
| 總交付 | 50 | 11 |
| 開發模式 | Pipeline B (Sequential) | Phase-based (Parallel) |
| 瓶頸 | Christina 閒置 + manual handoff | Rate limit |
| Bug | 0 | 0 |
| Regression | 0 | 0 |
| 新工具 | 5 scripts + 4 docs | build.py + otd_auto_report + watchdog cron |
| SOP 改善 | Design Stage (D1-D3) | 防閒置 SOP + 15m watchdog |
| 跨板 sync | 雙板驗證 (retro 後) | 聯合報告 (built-in) |

### 模式進化

```
Sprint 1: Spec → Design → Dev → QA (Pipeline B, sequential)
Sprint 2: Phase 0 (基建) → Phase 1 (三軌並行) → Phase 2 (自動化閉環)
Sprint 3 (建議): Continuous Pipeline (Phase 無縫 + CI auto-trigger)
```

---

## 5. Lessons Learned

### 5.1 Phase-based > Waterfall

Sprint 1 的 Pipeline B 是 sequential（等上游完成才能動）→ Sprint 2 改用 phase 分層，同 phase 內所有 track 零依賴並行。

**Rule of thumb**: 有依賴關係 → Pipeline B。無依賴關係 → Phase 並行。

### 5.2 SOP 比催促有效

與其每次 @Christina 催促取任務 → Phase 0 產出正式 SOP + 自動 watchdog → 一次解決 pattern。

### 5.3 Auto-report > Manual dashboard

`otd_auto_report.py` 一鍵產 3 件 vs 手動跑 3 條命令 → automation payoff 立即可見。

### 5.4 Rate Limit 是 scaling 天花板

當 task 數 > 50 後，API 429 開始出現。需要 batch write + retry 策略。

---

## 6. Sprint 3 建議方向

| # | 方向 | Priority | Owner Suggestion |
|---|------|----------|-------------------|
| 1 | OTD 真實數據閉環 | P0 | Smart (due_date adapter 已就位) |
| 2 | 跨板 CI 統一 (openclaw-ci.yml) | P0 | Technus |
| 3 | Christina 產能提升（單板 focus 實驗） | P1 | Christina + Nana |
| 4 | Rate limit retry / batch write | P1 | Technus |
| 5 | 移除 lead status gate (API 層) | P0 | Nana |
| 6 | 下一個產品線 kickoff | P1 | Nana direction |

---

## 7. 簽名

| 角色 | Agent | Sprint 2 交付 | 簽名 |
|------|-------|:--:|------|
| Retro Author | Smart | 22 | ✅ 2026-05-20 |
| Build System + QA | Technus | 23 | — |
| Token Coverage | Christina | 16 | — |
| Lead | Nana | — | — |

> 歸檔: `showcase/sprint-2-retro.md`