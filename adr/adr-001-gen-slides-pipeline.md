# ADR-001: gen_slides Pipeline 選型演進

> **狀態**: accepted  
> **日期**: 2026-05-20  
> **作者**: Smart (Power Squad)  
> **標籤**: architecture, tooling, pipeline

---

## Context

Sprint 起始目標：將三份 PPTX 轉換為企業級 HTML 投影片。初始嘗試 (`pptx2html.py`) 直接 PPTX→HTML，產出 17MB base64 內嵌圖片 + P56 Lighthouse 的廢鐵級 HTML。

需要回答：**PPTX→HTML 的正確管線架構是什麼？**

## Decision

採用 **三層分離管線**：

```
PPTX → [1] Extractor → structured JSON → [2] Renderer → HTML
                         ↑ 人工校對層（PLAYBOOK §2.5）
```

**v1 (pptx2html.py)**: 直接渲染。問題：base64 膨脹、無結構校對、不可維護。

**v2 (gen_slides.py)**: 引入 JSON 中間層 + 外部 renderer。問題：renderer 耦合設計代幣，無法換主題。

**v3 (gen_slides.py + semantic_upgrade)**: 加入 slide type 分類 + feat-grid + stat-num。問題：分類器 heuristic 不穩定。

**v4 (gen_slides_v4.py)**: PLAYBOOK §2.5 JSON 格式規範化、三套 theme 模板、內建 renderer fallback、雙輸出模式（`--json-only` / full HTML）。

## Consequences

### ✅ 正面

- JSON 中間層讓人工校對成為可能（過濾佔位符、確認 slide type）
- 三套 theme 可互換（`--template cris|aps|runs`）
- AI agent 可獨立完成 PPTX→HTML（見 Onboarding Guide §11）
- extract-tokens.py 可直接消費 gen_slides_v4 的 JSON 產出做 diff

### ⚠️ 取捨

- 中間層增加一步（PPTX→JSON 後需人工 inspection）
- 分類器（slide type heuristic）在不規則 PPTX 上有 10-15% 誤判率
- 圖片自動提取依賴 python-pptx 的 image API（部分 shape type 不支援）

### 🔮 未來方向

- v5: 反向解析（成品 HTML→結構化 JSON）實現模板剖析
- v5: ML-based slide classifier 取代 heuristic
- 多語言支援（i18n JSON layer）

## References

- PLAYBOOK.md §2 (PPT 提取策略)
- PLAYBOOK.md §2.5 (JSON 中間格式規範)
- gen_slides_v4.py (505 行)
- Sprint Retrospective §9.1 (交付時間線)