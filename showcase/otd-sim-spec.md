# OTD 模擬引擎 MVP Spec

> 工廠 OTD (Order-to-Delivery) 流程模擬系統 — Domain Model + 設定檔 Schema + API 介面  
> 版本: v0.1-draft · 狀態: Allen review pending

---

## 一、Domain Model

### 1.1 核心實體

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Order   │───▶│ Schedule │───▶│Production│───▶│ Shipment │
│  訂單     │    │  排程     │    │  生產     │    │  出貨     │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
     │                │               │               │
     ▼                ▼               ▼               ▼
  客戶/          工單指派/       工作站/          物流/
  交期/          優先級/         良率/           運輸時間/
  數量           產能            瓶頸            準交率
```

### 1.2 實體定義

| 實體 | 屬性 | 說明 |
|------|------|------|
| **Order** | `id`, `customer`, `product_type`, `quantity`, `due_date`, `priority`, `status` | 客戶訂單，觸發整個流程 |
| **Schedule** | `order_id`, `work_order_id`, `assigned_line`, `planned_start`, `planned_end`, `priority_rule` | 排程結果（工單） |
| **Production** | `work_order_id`, `station_id`, `actual_start`, `actual_end`, `yield_rate`, `defect_count`, `downtime_minutes` | 實際生產記錄 |
| **Shipment** | `order_id`, `ship_date`, `carrier`, `transit_days`, `delivery_date`, `on_time` | 出貨與到貨 |

### 1.3 工廠拓撲

```
Factory
  ├── Lines[]              ← 產線
  │     ├── Stations[]     ← 工作站 (瓶頸點)
  │     │     ├── capacity (units/hr)
  │     │     ├── setup_time (min)
  │     │     ├── failure_rate (0-1)
  │     │     ├── yield_decay (per 1000 units)
  │     │     └── maintenance_interval (hrs)
  │     └── buffer_size    ← 在製品(WIP)上限
  └── Warehouse            ← 成品倉
        ├── capacity
        └── ship_modes[]
```

---

## 二、變異參數

### 2.1 隨機變數注入點

| 參數 | 類型 | 範圍 | 觸發位置 |
|------|------|------|----------|
| `machine_failure_rate` | Poisson λ/100h | 0.01–0.20 | Station |
| `setup_time_jitter` | Normal(μ, σ) | ±30% | 換線時 |
| `yield_decay_rate` | Linear decay | 0.1–2.0%/1k units | Station |
| `priority_inversion` | Bernoulli(p) | 0–0.15 | Schedule |
| `rush_order_prob` | Poisson λ/day | 0–3 | Order generator |
| `transit_delay` | Log-normal(μ, σ) | 1–5 days | Shipment |
| `demand_spike` | Periodic multiplier | 1.0–3.0× | Order generator |
| `worker_absenteeism` | Bernoulli(p) | 0–0.05 | Station |

### 2.2 調度規則

| 規則 | 說明 |
|------|------|
| **FIFO** | 先進先出（baseline） |
| **EDD** | 最早交期優先 |
| **SPT** | 最短加工時間優先 |
| **CR** | Critical Ratio = (due_date - now) / remaining_time |
| **Hybrid** | EDD + WIP limit + priority boost for overdue |

---

## 三、JSON 設定檔 Schema

### 3.1 頂層結構

```json
{
  "version": "0.1",
  "name": "Factory OTD Simulation",
  "seed": 42,
  "sim_days": 90,
  "warmup_days": 7,
  "factory": { /* 工廠拓撲 */ },
  "order_template": { /* 訂單生成器 */ },
  "parameters": { /* 變異參數空間 */ },
  "scheduling": { /* 排程規則 */ },
  "output": { /* 輸出設定 */ }
}
```

### 3.2 Factory Schema

```json
{
  "factory": {
    "lines": [
      {
        "id": "L1",
        "name": "SMT線",
        "stations": [
          {
            "id": "L1-S1",
            "name": "錫膏印刷",
            "capacity": { "units_per_hour": 120, "max_batch": 500 },
            "setup": { "base_min": 15, "per_product_min": 5 },
            "failure": { "rate": 0.02, "mtbf_hours": 480, "mttr_min": 30 },
            "yield": { "base_rate": 0.995, "decay_per_1k": 0.001 },
            "maintenance": { "interval_hours": 160, "duration_min": 60 }
          }
        ],
        "buffer": { "max_wip": 200 }
      }
    ],
    "warehouse": {
      "capacity": 10000,
      "ship_modes": [
        { "name": "陸運", "base_days": 2, "jitter_days": 1, "cost_per_unit": 5 },
        { "name": "空運", "base_days": 1, "jitter_days": 0.5, "cost_per_unit": 20 }
      ]
    }
  }
}
```

### 3.3 Order Template Schema

```json
{
  "order_template": {
    "products": [
      { "type": "A", "name": "標準品", "mix_pct": 60, "route": ["L1-S1", "L1-S2", "L1-S3"], "cycle_time_hrs": 4 },
      { "type": "B", "name": "急單品", "mix_pct": 25, "route": ["L1-S1", "L1-S2"], "cycle_time_hrs": 2.5, "priority_boost": 2 },
      { "type": "C", "name": "特製品", "mix_pct": 15, "route": ["L1-S1", "L1-S2", "L1-S3", "L1-S4"], "cycle_time_hrs": 6 }
    ],
    "arrival": {
      "base_per_day": 10,
      "jitter_pct": 20,
      "rush_order": { "prob_per_day": 0.05, "quantity": [5, 20], "due_days": 3 }
    },
    "due_date": { "base_days": 14, "jitter_days": 3 }
  }
}
```

### 3.4 Parameters Schema

```json
{
  "parameters": {
    "failure": { "rate_multiplier": 1.0 },
    "yield": { "decay_multiplier": 1.0 },
    "setup": { "jitter_pct": 15 },
    "priority": { "inversion_rate": 0.05 },
    "demand": { "spike_multiplier": 1.0, "spike_days": [] },
    "worker": { "absenteeism_rate": 0.02 }
  }
}
```

### 3.5 Scheduling Schema

```json
{
  "scheduling": {
    "rule": "EDD",
    "replan_interval_hours": 4,
    "allow_preemption": false,
    "wip_limit_trigger": 0.8,
    "overdue_priority_boost": 3
  }
}
```

---

## 四、模擬引擎 API 介面

### 4.1 `run(config) → SimulationResult`

```python
def run(config_path: str, seed: int = None) -> dict:
    """
    執行一次模擬，回傳完整 timeline + metrics。
    
    Args:
        config_path: JSON 設定檔路徑
        seed: 隨機種子（覆蓋設定檔內的 seed）
    
    Returns:
        SimulationResult dict
    """
```

### 4.2 SimulationResult Schema

```json
{
  "run_id": "20260520-0830-abc123",
  "config": { /* 執行的設定拷貝 */ },
  "seed": 42,
  "duration": { "sim_days": 90, "wall_seconds": 2.3 },
  "timeline": [
    {
      "time": 0.5,
      "event": "order_arrival",
      "order_id": "ORD-001",
      "details": { "type": "A", "quantity": 100, "due_day": 14 }
    },
    {
      "time": 1.2,
      "event": "schedule_assign",
      "order_id": "ORD-001",
      "work_order_id": "WO-001",
      "details": { "line": "L1", "priority_rule": "EDD" }
    },
    {
      "time": 3.0,
      "event": "station_start",
      "work_order_id": "WO-001",
      "station": "L1-S1",
      "details": { "units": 100 }
    },
    {
      "time": 4.2,
      "event": "station_complete",
      "work_order_id": "WO-001",
      "station": "L1-S1",
      "details": { "yield": 0.994, "defects": 6, "duration_hrs": 1.2 }
    }
  ],
  "metrics": {
    "orders": {
      "total": 950,
      "completed": 892,
      "cancelled": 12,
      "in_progress": 46
    },
    "otd": {
      "on_time_rate": 0.876,
      "mean_lateness_days": 1.8,
      "p95_lateness_days": 4.2,
      "otif": 0.853
    },
    "production": {
      "total_units": 89200,
      "mean_cycle_time_hrs": 5.2,
      "mean_yield": 0.987,
      "bottleneck": "L1-S3",
      "utilization": { "L1-S1": 0.72, "L1-S2": 0.85, "L1-S3": 0.94 }
    },
    "wip": {
      "mean_wip": 156,
      "max_wip": 248,
      "wip_turns": 12.3
    },
    "downtime": {
      "total_hours": 48.5,
      "events": 12,
      "mtbf_actual": 180,
      "mttr_actual": 4.0
    }
  }
}
```

### 4.3 `batch_run(config, param_sweeps) → [SimulationResult]`

```python
def batch_run(config_path: str, sweeps: list, runs_per_config: int = 10) -> list:
    """
    參數掃描模式：對每組參數執行 runs_per_config 次模擬。
    
    Args:
        config_path: 基礎設定檔
        sweeps: [{param_path: values}] 參數掃描定義
        runs_per_config: 每組參數的重複次數
    
    Returns:
        list of SimulationResult
    """
```

### 4.4 `compare(results) → ComparisonReport`

```python
def compare(results: list) -> dict:
    """
    對多組模擬結果進行統計比較。
    
    Returns:
        { "baseline": metrics, "scenarios": [{name, metrics, delta}] }
    """
```

---

## 五、不納入 MVP 的項目（v0.2+）

| 項目 | 理由 |
|------|------|
| 即時模擬（real-time clock） | v0.1 用 discrete-event fast-forward |
| 3D 廠房視覺化 | 先用 CLI + JSON 輸出 |
| AI/ML 調度最佳化 | 先支援手動規則切換 |
| 多廠區協同 | 先單廠 |
| 供應鏈上游（原料庫存） | 先從訂單到出貨（內部 OTD） |
| 財務指標（成本/P&L） | 先看準交率 + 利用率 |

---

## 六、技術選型建議

| 層 | 推薦 | 備選 |
|------|------|------|
| 模擬引擎 | Python (simpy) | Python (從頭寫 discrete-event) |
| 隨機數 | numpy.random | Python random |
| 輸出格式 | JSON | CSV for timeline |
| 統計 | pandas.describe() | scipy.stats |
| 視覺化 | matplotlib (timeline/OTD chart) | Plotly (互動版) |

### simpy 範例片段

```python
import simpy

def station_process(env, name, station, order):
    """模擬一個工作站的處理流程"""
    # 檢查機器狀態
    if env.failure_rng.random() < station['failure']['rate']:
        yield env.timeout(station['failure']['mttr_min'] / 60)
    # 生產
    cycle_time = order['quantity'] / station['capacity']['units_per_hour']
    yield env.timeout(cycle_time)
    # 良率
    good = int(order['quantity'] * station['yield']['base_rate'])
    return {'good': good, 'defect': order['quantity'] - good}
```

---

## 七、MVP 交付定義

| 交付物 | 格式 | 驗收標準 |
|------|------|----------|
| 設定檔 schema | JSON Schema | `jsonschema.validate()` 通過 |
| 模擬引擎 | Python script | 90 天模擬 < 5 秒 wall time |
| Timeline 輸出 | JSON | 每筆事件有 timestamp + type |
| Metrics 輸出 | JSON | 含 OTD rate + utilization + WIP + downtime |
| 範例設定檔 | config.json | 可直接餵給引擎執行 |
| CLI | `python3 simulate.py config.json` | exit code 0, stdout 為 metrics JSON |

---

*版本: v0.1-draft · 建立於 2026-05-20 · Technus*  
*待 Allen review 後進入實作階段*