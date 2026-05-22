# OTD v0.4 排程政策比較報告

> 模擬：90 天 × 900 orders × factory.json line-1（S1/S2/S3）
> 引擎：station_dispatch.py + dispatch_policy.py pluggable layer

## 政策對照

| Metric | FIFO | SPT | EDD |
|--------|------|-----|-----|
| Ships | 410 | 410 | **411** |
| OTD% | 45.6% | 45.6% | **45.7%** |
| Avg Lead (d) | **26.5** | 52.9 | 32.8 |
| Avg Wait (h) | 8.5 | **7.6** | 7.8 |
| Bottleneck | L1-S1 | L1-S1 | L1-S1 |
| WIP Alerts | ⚠️ S1 143%, S2 121% | ✅ 無 | ⚠️ S1 116%, S2 94% |

## 分析

### EDD（最早交期優先）🏆 總 winner
- **OTD 最高** 45.7%，shipment 最多
- Lead time 適中（32.8d），比 FIFO 多 6d 但 OTD 略好
- WIP 警告中等，S1 116% / S2 94%

### FIFO（先進先出）
- **Lead time 最短** 26.5d — 唯一低於 30d 的政策
- OTD 接近 EDD（45.6%）
- **WIP 溢位最嚴重** — S1 143%（714 units vs 500 cap），S2 121%
- → 適合以速度為目標的場景，但需擴產能

### SPT（最短處理時間優先）
- **WIP 最乾淨** — 零告警！唯一不觸發 WIP threshold 的政策
- 但 lead time 最長（52.9d）— type C(6h) 大單被推遲
- → 適合瓶頸站產能緊張的場景

## 結論

| 場景 | 推薦 |
|------|------|
| 追求 OTD 最大化 | **EDD** |
| 追求最短交期 | **FIFO**（但需解 WIP 溢位）|
| 產能受限/防瓶頸 | **SPT** |
| 混合策略 | EDD 為主 + SPT 分流 type A/B |

## 下一步建議
1. 擴充 factory.json → 3 條產線並行測試（模擬真實工廠）
2. Hybrid policy: EDD 排程 + SPT 分流小單
3. 參數敏感度分析：調整 setup time / yield decay / failure rate 後重跑