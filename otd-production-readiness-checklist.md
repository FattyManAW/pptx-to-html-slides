# OTD Engine v0.5 → v1.0 Production Readiness Checklist

> 執行時間：2026-05-22 04:05 CST
> 執行者：Smart（MC-1ac8b4f3）
> 狀態：✅ ALL PASS — OTD v0.5 production-ready

---

## 1. Test Suite — pytest 50/50 ✅

| Suite | Tests | Status |
|-------|:-----:|:------:|
| test_dispatch.py — FIFO | 5 | ✅ PASS |
| test_dispatch.py — EDD | 5 | ✅ PASS |
| test_dispatch.py — SPT | 5 | ✅ PASS |
| test_dispatch.py — PolicyRegistry | 8 | ✅ PASS |
| test_dispatch.py — EdgeCases | 2 | ✅ PASS |
| test_due_date.py — ISO8601 | 4 | ✅ PASS |
| test_due_date.py — Epoch | 3 | ✅ PASS |
| test_due_date.py — ArrivalPlusN | 3 | ✅ PASS |
| test_due_date.py — ProductLead | 5 | ✅ PASS |
| test_due_date.py — Default | 3 | ✅ PASS |
| test_due_date.py — EdgeCases | 4 | ✅ PASS |
| test_due_date.py — Config | 3 | ✅ PASS |
| **Total** | **50** | **✅ 50/50** |

## 2. DueDateAdapter — 五格式 Edge Case 驗證 ✅

| Format | Normal | Override | Fallback | Test |
|--------|:------:|:--------:|:--------:|:----:|
| default | ✅ | N/A | ✅ | bad config → defaults to 14d+jitter |
| iso8601 | ✅ | ✅ | ✅ | malformed → falls back |
| epoch | ✅ | ✅ | ✅ | — |
| arrival_plus_N | ✅ | N/A | ✅ | custom days |
| product_lead | ✅ | N/A | ✅ | 5 products (A-E) |

**Edge cases verified:**
- Unknown format → graceful fallback to default ✅
- Negative arrival_day → correct due_date ✅
- Missing override → fallback logic intact ✅
- Malformed ISO → fallback to computed ✅

## 3. Dispatch → Shipment 全閉環 ✅

```
Order Generator (900 orders)
  → Scheduler (FIFO/SPT/EDD policy)
  → StationDispatchLoop (S1→S2→S3 per-product route)
  → Production (capacity queue + setup + failure + yield decay)
  → Warehouse FIFO + transit_delay
  → Shipment (on_time=✓/✗)
```

| Metric | FIFO | SPT | EDD |
|--------|-----:|----:|----:|
| Orders | 900 | 900 | 900 |
| Timeline Records | 1,208 | vary | vary |
| Shipments | 411 | 411 | 412 |
| OTD Rate | 45.7% | 45.7% | 45.8% |
| Avg Lead Time | 46.3d | 46.3d | 46.3d |
| Avg WIP | 168.0 | 311.7 | 273.0 |
| Bottleneck | L1-S1 | L1-S1 | L1-S1 |

## 4. Dashboard 資料流 ✅

| Artifact | Path | Size | Status |
|----------|------|------|:------:|
| timeline.json | otd-sim/timeline.json | 561KB | ✅ |
| timeline_e2e.json | otd-sim/timeline_e2e.json | 130KB | ✅ |
| timeline_wrapped.json | otd-sim/timeline_wrapped.json | 613KB | ✅ |
| dashboard_metrics.json | otd-sim/dashboard_metrics.json | 2.2KB | ✅ |
| sweep_results.json | otd-sim/sweep_results.json | 5.8KB | ✅ |
| policy_comparison.json | otd-sim/policy_comparison.json | 1.9KB | ✅ |
| otd-dashboard.html | showcase/ | 19.5KB | ✅ |
| otd-dashboard-standalone.html | showcase/ | 20KB | ✅ |

Dashboard metrics fields: `frame_count`, `total_stations`, `station_wip_max`, `bottleneck`, `yield_rates`, `best_policy`, `policy_results`

## 5. API / Integration ✅

| Check | Status |
|-------|:------:|
| station_dispatch.py imports OK | ✅ |
| factory.json valid config | ✅ |
| dispatch_policy.py (FIFO/SPT/EDD/registry) | ✅ |
| DueDateAdapter standalone | ✅ |
| SimulationEngineV02.run() | ✅ |
| models.py compatibility | ✅ |
| otd_data_pipeline.py | ✅ |
| otd_auto_report.py | ✅ |
| otd_sweep.py (parameter grid search) | ✅ |
| otd_stress_test.py | ✅ |
| sim_server.py (Flask API) | ✅ |
| agents.py (Agent-based simulation) | ✅ |

## 6. 已知限制

| # | 限制 | 影響 | 建議 |
|---|------|------|------|
| 1 | OTD rate ~45% — 瓶頸 L1-S1 | 模擬結果偏低 | 調 factory.json station capacity 或 splits |
| 2 | due_date 無真實工廠數據 | 排程精度有限 | 等 Allen 提供真實 due_date 格式後切 config |
| 3 | 三政策差異小（45.7% vs 45.8%） | 短期模擬看不出差異 | 跑更長模擬（365d）或注入 asymmetric demand |
| 4 | Dashboard 資料流依賴手動 script | 非即時 auto-sync | otd_data_pipeline.py 已就位，串 cron 即可 |
| 5 | 無參數靈敏度報告 | 無法評估參數對 OTD 的影響 | otd_sweep.py 已就位，跑 grid search 即可 |

## 7. v1.0 發布建議

### 現在可發布 ✅
- pytest 50/50 ✅
- 五格式 due_date adapter ✅
- 全閉環 dispatch→shipment ✅
- Dashboard 資料流完整 ✅
- 多政策對比 ✅

### v1.0 後改善（Phase 2）
1. 真實工廠 due_date 數據注入 → OTD 精度提升
2. cron autopilot：定時跑 sweep + 更新 dashboard_metrics.json
3. Monte Carlo 1000-run 參數空間掃描（otd_sweep.py 擴充）
4. CI gate：`pytest tests/ --tb=short` exit code check 串入 build.py

---

**結論：OTD Engine v0.5 已通過全部 production readiness 檢查。可發布為 v1.0-rc1。**

Signed: Smart · 2026-05-22 04:05 CST