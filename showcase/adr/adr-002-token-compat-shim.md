# ADR-002: Token Compat Shim 策略

> **狀態**: accepted  
> **日期**: 2026-05-20  
> **作者**: Smart (Power Squad)  
> **標籤**: design-system, tokens, compatibility

---

## Context

一致性審計報告（`consistency-audit.md`）揭露：三套產品使用兩套互不相容的 token naming scheme：

- **APS**: `--c-600~950` color palette + `--txt-*` typography
- **CRIS/潤思**: `--ink-50~950` color palette + `--c-t1~4` text colors

結果：105 unique tokens，僅 32 common（30%共用），115 missing slots。

需要回答：**如何在不破壞線上產品的前提下統一名稱空間？**

## Decision

採用 **Compat Shim 策略**：追加新 token 不刪舊 token。

```css
/* Step 1: 定義 canonical token（追加, 不替換） */
:root {
  --ds-ink-950: #06080d;      /* canonical */
  --ds-accent: var(--c-teal); /* alias to existing */
}

/* Step 2: 內部元件改用 canonical */
.slide { background: var(--ds-ink-950, var(--c-bg)); }

/* Step 3: Phase-out: 等所有 consumer 都遷移完再移除舊 token */
```

### 被拒絕的方案

| 方案 | 拒絕原因 |
|------|----------|
| 全量重寫 APS CSS | 44KB CSS 重寫風險高，可能引入 regression |
| 統一為 `--ink-*` | APS 用 `--c-*`，需全部 grep-replace |
| 不做統一 | 無法做跨產品 token CI check |

## Consequences

### ✅ 正面

- 零破壞：現有 HTML 完全不受影響
- 漸進遷移：新功能用 canonical，舊功能保留兼容
- CI gate 可行性：extract-tokens.py `--check` 可同時檢查新舊 token

### ⚠️ 取捨

- 過渡期 token 數量膨脹（105 → ~140）
- 雙重維護成本（直到 phase-out）
- Landing Page 不受 token 體系約束（獨立暗色主題）

### 🔮 未來方向

- v5 設計系統：定義 `--ds-*` 為單一事實來源
- `tokens.json` 雙向映射 → Christina token 對齊任務（33d732f9）
- extract-tokens.py 加入 `--canonical` 模式（僅檢查 canonical set）

## References

- consistency-audit.md §1（Token 缺口矩陣）
- extract-tokens.py (258 行)
- Christina task 33d732f9（Token 對齊）