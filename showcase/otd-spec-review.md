# OTD 模擬引擎 Spec Review

> Reviewer: Christina · 2026-05-20 · 讀 spec v0.1-draft
> 結論：**架構完整，可以直接進入實作階段。**

---

## ✅ 架構完整性（10/10）

| 檢查項目 | 狀態 | 說明 |
|----------|:--:|------|
| 四階段 Domain Model | ✅ | Order → Schedule → Production → Shipment |
| JSON Schema 定義 | ✅ | Factory / Order Template / Parameters / Scheduling 四塊 |
| API 介面 | ✅ | `run(config_path, seed) → SimulationResult` |
| 工廠拓撲 | ✅ | Lines → Stations → Warehouse 三層 |
| 變異參數表 | ✅ | 8 個隨機變數，觸發位置明確 |
| 排程規則 | ✅ | FIFO / EDD / SPT / CR / Hybrid |
| Output Schema | ✅ | sim_days / warmup_days / seed 等 |
| 版本標記 | ✅ | v0.1-draft |
| Code blocks | ✅ | ≥5 個 JSON/Python 區塊 |
| 表格結構 | ✅ | 實體定義 / 變異參數 / 工廠拓撲 表格化 |

---

## 💡 架構建議（語意層面）

### S1. SimulationResult 輸出 Schema 未展開

**現況**：只定義了 `run()` 函數簽名，回傳 `dict`，但沒有列出實際的 JSON 輸出結構。

**建議**：補上 Output Schema 表格：

```json
{
  "simulation_result": {
    "config": { "version": "...", "seed": 42 },
    "metrics": {
      "otd_rate": 0.92,
      "avg_lead_time_days": 12.3,
      "avg_wip": 145,
      "bottleneck_station": "L1-S2",
      "total_defects": 23,
      "on_time_orders": 184,
      "late_orders": 16
    },
    "timeline": [
      { "event": "order_received", "order_id": "O001", "day": 1 },
      { "event": "production_start", "work_order_id": "W001", "day": 2, "station": "L1-S1" },
      ...
    ],
    "daily_snapshot": [
      { "day": 1, "wip": 45, "orders_pending": 12, "orders_shipped": 0 },
      ...
    ]
  }
}
```

---

### S2. 變異參數沒有預設值範圍標記

**現況**：表格列出類型/範圍，但 JSON Schema 的 `parameters` block 只定義了 multiplier，沒有預設值。

**建議**：補上 `default` 欄位：

```json
{
  "parameters": {
    "failure": { "rate_multiplier": 1.0, "default": 1.0, "min": 0.5, "max": 3.0 },
    "yield": { "decay_multiplier": 1.0, "default": 1.0, "min": 0.8, "max": 2.0 },
    ...
  }
}
```

---

### S3. Work Order 與 Order 的關係未明確定義

**現況**：Order → Schedule（工單），但一個 Order 是否可以拆成多個 Work Order？Work Order 的狀態機（pending → scheduled → in_progress → completed → shipped）是否定義？

**建議**：補 Work Order 狀態機定義：

| 狀態 | 觸發條件 |
|------|----------|
| `pending` | Order 收到，未排程 |
| `scheduled` | 排程完成，等待生產 |
| `in_progress` | 工作站開始加工 |
| `completed` | 工作站完工 |
| `shipped` | Shipment 出貨完成 |

---

### S4. Station 良率衰減計算公式未標註

**現況**：`yield_decay` 列出 `per 1000 units`，但計算公式未寫明。

**建議**：補公式：

```
yield_rate_n = base_rate - (units_processed / 1000) * decay_per_1k
clamp(yield_rate_n, min=0.80, max=base_rate)
```

---

### S5. Schedule → Production 的觸發條件未定義

**現況**：四階段流程圖清楚，但什麼時候從 Schedule 階段進入 Production 階段？是排程完成自動觸發，還是需要手動確認？

**建議**：定義觸發條件（建議：`planned_start <= now` 且 Station 空閒 → 自動觸發）

---

## 🐛 潛在問題（邊角案例）

### B1. `due_date` 在 JSON Schema 中是絕對日期還是相對天數？

**現況**：Domain Model 說 `due_date`，Order Template Schema 說 `due_date: { base_days: 14, jitter_days: 3 }`。

**問題**：`due_date` 是絕對日期（2026-01-15）還是相對天數（from order arrival + 14 days）？兩種解讀會導致完全不同的排程結果。

**建議**：明確定義，建議用相對天數（from Day 0）+ `arrival_day` 屬性。

---

### B2. `warmup_days` 的數據是否排除在 metrics 之外？

**現況**：`warmup_days: 7` 定義在頂層，但沒有說明 warmup 期間的訂單和產出是否計入最終 OTD 計算。

**建議**：明確定義是否排除，並在 `SimulationResult` 中分開報告 `warmup_metrics` 和 `steady_state_metrics`。

---

### B3. `seed` 的可重現性邊界

**現況**：`seed: 42` 在頂層，但變異參數注入點多達 8 個。

**問題**：同一 seed 下，執行順序不同是否保證相同結果？如果 Order 到達順序有隨機性，seed 的意義會縮減。

**建議**：明確定義 seed 控制範圍（建議：所有隨機決策都從 seed 啟動的 PRNG 取樣），並在 Output 中報告實際使用的 seed 值。

---

### B4. `rush_order` 的 `due_days` 與一般訂單的 `due_date` 格式不一致

**現況**：
- 一般訂單：`due_date: { base_days: 14, jitter_days: 3 }`
- 急單：`rush_order: { due_days: 3 }`

**問題**：急單是相對天數，一般訂單也是相對，但欄位名不同（`due_days` vs `due_date.base_days`），容易造成實作混淆。

**建議**：統一命名為 `lead_time_days` 或保留 `due_days` 作為通用欄位。

---

## 📊 Domain Model 流程圖

> 見 `otd-domain-model.html` — 互動式單頁視覺化，涵蓋四階段 + 變異參數節點。

---

## 總結

| 維度 | 評分 | 說明 |
|------|:--:|------|
| 架構完整性 | ✅ | 四階段 + 拓撲 + Schema 全有 |
| JSON Schema | ✅ | 四塊 Schema 定義清楚 |
| API 設計 | ✅ | `run()` 單一入口，seed 可覆蓋 |
| 變異參數 | ✅ | 8 個隨機變數，觸發位置明確 |
| 邊角案例 | ⚠️ | 4 個建議（due_date 格式、warmup 排除、seed 邊界、due_days 一致性）|
| 可實作性 | ✅ | Spec 粒度足夠，可直接進入 coding |

**建議下一步**：先解決 B1（due_date 格式）和 S1（Output Schema），其餘可在實作時迭代。
