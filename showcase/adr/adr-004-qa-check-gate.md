# ADR-004: QA Check Gate 設計

> **狀態**: accepted  
> **日期**: 2026-05-20  
> **作者**: Smart (Power Squad)  
> **標籤**: qa, ci, testing

---

## Context

Sprint 初期，品質檢查靠「目視」。Christina CRIS v3 卡 8h 沒發現 slide count mismatch（28≠36），直到 QA Pipeline 掃描才揭露。

需要回答：**自動化 QA 檢查的分層策略是什麼？如何確保分數不退化？**

## Decision

採用 **P0/P1/P2 三層 gate + baseline diff**：

### 分層設計

| 層級 | 覆蓋範圍 | 檢查項 | 致命？ |
|------|----------|--------|:------:|
| **P0** | 結構完整性 | DOCTYPE, charset, viewport, slide count, base64, fonts | ✅ |
| **P1** | CSS 架構 | tokens 數量, 模組化註解, backdrop-filter, radial-gradient, @media 斷點 | ❌ |
| **P2** | 互動功能 | keyboard, wheel, touch, fullscreen, progress bar | ❌ |

### Baseline Diff 機制

```
首次掃描 → 寫入 .qa_baseline.json
後續掃描 → 比對 baseline → pass/fail/warn counts
分數不變 → 安靜
分數下降 → per-product escalate（連續 2 次下降才告警）
```

### 為什麼不只用 pass/fail？

- 初始版 HTML 一定有缺漏（74-86% QA）
- 用 baseline 追蹤**退步**而非絕對分數
- 避免「永遠紅色」的 alarm fatigue

## Consequences

### ✅ 正面

- QA Pipeline 從手動 20min/次 → 自動 5s/次
- 驅動閉環迭代：掃描 → 修復清單 → 修 → 再掃
- Baseline diff 避免 noise（分數不變不告警）
- CI/CD Stage 1 整合為 gate（qa_pipeline.py exit code）

### ⚠️ 取捨

- 首次掃描分數低不告警（需人工判斷是否接受 baseline）
- slide count detection 對 `.slide-inner` wrapper 有 bug（見 ADR-005）
- P0 檢查項需要隨著 PLAYBOOK 演進同步更新

### 數據驗證

```
APS:  第一輪 19/19 QA → 第二輪 100%（+5 check）
CRIS: 第一輪 74% → 第二輪 100%（+9 check）
潤思: 第一輪 86% → 第二輪 100%（+3 check）
```

### 🔮 未來方向

- P3 layer: 設計品質（色彩 harmony, typography scale, whitespace ratio）
- 與 Lighthouse CI 整合為統一一鍵檢查
- QA gate 掛 PR hook（非 merge if fail）

## References

- qa_pipeline.py (35 項檢查)
- run_qa.py (647 行, cron automation)
- .qa_baseline.json（當前 baseline）
- PLAYBOOK.md §6 (QA 檢查清單)
- Sprint Retrospective §9.1（CRIS 8h→30min）