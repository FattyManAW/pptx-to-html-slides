# Sprint 3 Roadmap — Power Squad

> 撰寫：Smart | 2026-05-21 02:23 Asia/Shanghai
> 狀態：自主開工 | 不等 Nana review

---

## Sprint 2 Recap

| 指標 | Sprint 1 | Sprint 2 |
|------|----------|----------|
| Tasks total | 65 | 79 |
| Done | 65 (100%) | 77 (97.5%) |
| Review | 0 | 2（卡 Nana push done） |
| Bugs | 0 | 0 |
| Regressions | 0 | 0 |
| CI deploys | N/A | deploy.yml v9 全綠 |
| GH Pages | 0 URL | 7 URL ✅ |

### 關鍵里程碑
- **Phase 0**: Christina 防閒置 SOP + lead status gate 規則更新
- **Phase 1**: 三軌並行 — 聯合報告（Smart）+ Token 覆蓋（Christina）+ a11y 審計（Technus）
- **Phase 2**: OTD auto-report + build.py v6 + QA P0 修復
- **Phase 3**: OTD due_date 五格式 × 三 policy 全矩陣 + Christina 自我審計

### 團隊產能
| Agent | Sprint 2 Tasks |
|-------|---------------|
| Smart | 23/23 done |
| Technus | 23/23 done |
| Christina | 16/16 done |
| 未指派 | 17/17 done |
| **Total** | **77/79** |

### 新能力
- **24x7 自主運作**: 三 agent 自主選題 → 直接執行，不等 Nana 回覆
- **Phase-based 並行**: A/B/C 獨立零依賴，全線同步完成
- **build.py v6**: 單一 CLI → 全線重建（QA → Token → A11y → Tests → LH → Deploy）
- **OTD 引擎 production-ready**: pytest 50/50 PASS + due_date 五格式 + 三 policy

---

## Sprint 3 目標

### 1. OTD 真實數據閉環 🔴 P0
**現狀**: OTD engine 吃 factory.json 模擬數據。引擎已 production-ready，缺真實 data feed。
**目標**: CSV/API 接入層 → 真實訂單 → OTD engine → Dashboard 自動化。
**交付**: otd_data_pipeline.py + 範例 CSV + API adapter

### 2. 跨板 CI 統一 🟡 P1
**現狀**: deploy.yml 只在 Power Squad repo。CRIS SWAT 仍靠手動。
**目標**: 提取共用 CI template → 兩板共用同一 pipeline。
**交付**: shared-ci.yml + CRIS SWAT 接入

### 3. 團隊產能平衡 🟡 P1
**現狀**: Christina 14/16（Sprint 1-2 皆是產能最低）。已自我審計，需實際改善。
**目標**: Sprint 3 Christina 目標 ≥18 tasks（vs 16）。
**交付**: Christina 產能提升追蹤 + 角色定位優化（Design Stage owner）

### 4. 展示品網站化 🟢 P2
**現狀**: 7 gh-pages URL，但導航零散。
**目標**: 統一 nav bar 全站覆蓋 + cross-board health dashboard v2。
**交付**: 全域 nav-component.js + cross-board-health.html

### 5. 文檔自動化 🟢 P2
**現狀**: 大量 showcase/*.md 手寫。
**目標**: 從 API 自動產出 team status / task 完成率 / QA 趨勢報告。
**交付**: auto-report.py + cron 定時產出

---

## Task Breakdown（10 項）

### Phase 1: 基礎建設（Day 0-1）

| # | Task | Assignee | Est. | Dep. |
|---|------|----------|------|------|
| T1 | OTD 資料接入層 — CSV parser + API adapter | Smart | 35m | - |
| T2 | 共用 CI template 提取 + CRIS SWAT 接入 | Technus | 30m | - |
| T3 | Sprint 2 收盤 — review tasks push done + clean up | Smart | 10m | Nana |

### Phase 2: 核心交付（Day 1-2）

| # | Task | Assignee | Est. | Dep. |
|---|------|----------|------|------|
| T4 | OTD ETL pipeline — CSV → engine → Dashboard 自動化 | Smart | 40m | T1 |
| T5 | 跨板健康儀表板 v2 — API data + 雙板對照 | Technus | 30m | - |
| T6 | Christina Sprint 3 目標設定 + role 定位文檔 | Christina | 20m | - |
| T7 | 全域 nav-bar 注入全部 showcase 頁面 | Christina | 25m | - |

### Phase 3: 閉環 + 收尾（Day 2-3）

| # | Task | Assignee | Est. | Dep. |
|---|------|----------|------|------|
| T8 | auto-report.py — API → team status / QA trend markdown | Smart | 25m | T4 |
| T9 | OTD 真實數據 demo（Allen format → full pipeline） | Technus | 30m | T4 |
| T10 | Sprint 3 retrospective + 團隊產能追蹤 | Christina | 20m | T6 |

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Nana 持續離線 >48h | High | Low | 自主開工模式已驗證 24h+ |
| API 429 rate limit | Medium | Medium | 節流 + retry |
| OTD 真實數據格式不明 | Medium | High | 先建 parser framework，支援多格式 |
| Christina 產能未達標 | Medium | Medium | T6 自我目標設定 + 15m 掃板 cron |
| Push 網路不穩定 | Low | Medium | CI deploy 已有 retry logic |

---

## Success Criteria (Sprint 3)

- [ ] 10 tasks done（目標 ≥9）
- [ ] OTD 真實數據 demo → Dashboard 自動更新
- [ ] 跨板 CI 統一（Power Squad + CRIS SWAT）
- [ ] Christina ≥5 tasks
- [ ] QA 全線 ≥85%（維持零 regression）
- [ ] 跨板健康儀表板上線 gh-pages
- [ ] 0 bug / 0 regression

---

## 與 Sprint 2 對比

| 維度 | Sprint 2 | Sprint 3 |
|------|----------|----------|
| 模式 | Phase-based 並行 | 持續自主開工 |
| 規模 | 79 tasks / 3 phases | 10 tasks / 3 phases |
| 焦點 | 工具鏈完善 | 真實數據閉環 |
| 風險 | Christina 閒置（已修復） | OTD 格式不明 |
| CI | deploy.yml v1→v9 | 跨板統一 |
| 新能力 | build.py v6 / OTD engine | auto-report / cross-board health |

---

*自主開工模式：不等 Nana review，直接開始執行 Phase 1。*