# ADR-005: slide-inner 統合處理

> **狀態**: accepted  
> **日期**: 2026-05-20  
> **作者**: Smart (Power Squad)  
> **標籤**: html, parser, regression

---

## Context

CRIS IMPACTs HTML 採用 `.slide-inner` wrapper 結構：

```html
<div class="slide" data-stagger="0">
  <div class="slide-inner">
    <h2 class="slide-title">...</h2>
    <!-- 內容 -->
  </div>
</div>
```

而 APS 和潤思直接將內容放在 `.slide` 內：

```html
<div class="slide" data-stagger="0">
  <h2 class="slide-title">...</h2>
</div>
```

QA Pipeline 的 `count_slides()` 函數只認 `<div class="slide"` 元素數量，CRIS 造成 `slide_count=0`，觸發假警報。

需要回答：**parser 應該如何處理兩種 slide 結構？**

## Decision

採用 **雙向防禦**：Parser 寬鬆匹配 + HTML 結構對齊。

### Parser 端（run_qa.py / qa_pipeline.py）

```python
def count_slides(html):
    # 寬鬆匹配：同時支援兩種結構
    direct = len(re.findall(r'<div class="slide"', html))
    inner = len(re.findall(r'<div class="slide-inner"', html))
    return max(direct, inner)
```

### HTML 端（結構規範）

gen_slides_v4 產出統一使用 `.slide-inner` wrapper：

```html
<div class="slide" data-stagger="0">
  <div class="slide-inner">
    <!-- 所有內容放這裡 -->
  </div>
</div>
```

現有 APS 和潤思 HTML 不做 retroactive 修改（避免 regression），僅新產出對齊。

## Consequences

### ✅ 正面

- Parser 不再因 wrapper 差異產生 0 slide count
- gen_slides_v4 新產出統一結構（見 output/*.html）
- 未來新 agent 只需一種結構就能通過 QA

### ⚠️ 取捨

- APS (44KB) 和潤思 (105KB) 暫不 retrofix（手動改風險 > 收益）
- `max(direct, inner)` 可能高估 slide 數（如果兩者並存）
- CRIS 37KB 唯一回歸受害（slide-inner 觸發 repair task b343f2bf）

### Timeline

| 時間 | 事件 |
|------|------|
| 05-19 21:15 | QA Cron 告警：CRIS slide_count=0 |
| 05-19 21:30 | Technus 定位根因：count_slides() 只認 `.slide` |
| 05-19 22:00 | qa_pipeline.py 修正 → re-baseline |
| 05-19 22:15 | CRIS QA 恢復正常 85% |

### 🔮 未來方向

- gen_slides_v5 統一輸出結構（單一 `.slide` pattern）
- Parser 改為 DOM-based（非 regex），一勞永逸解決結構差異

## References

- showcase/cris-impacts-carbon.html (`.slide-inner` wrapper)
- qa_pipeline.py `count_slides()` function
- Technus repair task b343f2bf (CRIS regression fix)
- PLAYBOOK.md §12.2 (Lessons Learned — slide-inner Regression)