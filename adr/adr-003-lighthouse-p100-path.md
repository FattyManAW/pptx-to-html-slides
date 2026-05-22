# ADR-003: Lighthouse P100 關鍵路徑

> **狀態**: accepted  
> **日期**: 2026-05-20  
> **作者**: Smart (Power Squad)  
> **標籤**: performance, lighthouse, fonts

---

## Context

v1 HTML 投影片 Lighthouse Performance 只有 **P56**（FCP 19.4s, TBT 8.2s）。

目標：APS + CRIS 從 P56 → P100 Performance。

需要回答：**投影片型 HTML 的 Lighthouse Performance 瓶頸在哪？**

## Decision

關鍵路徑是 **Font Loading**，非 JS/圖片。

### 修復前（P56）

```html
<!-- 同步載入，block rendering -->
<link href="https://fonts.googleapis.com/css2?family=..." rel="stylesheet">
```
→ FCP 停在字體下載完成（~19s on slow 3G）

### 修復後（P100）

```html
<!-- 1. Preconnect（DNS/TLS 預熱） -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>

<!-- 2. 非阻塞載入（media="print" trick + onload swap） -->
<link rel="stylesheet" href="..." media="print" onload="this.media='all';this.onload=null">

<!-- 3. NoScript fallback -->
<noscript><link rel="stylesheet" href="..."></noscript>

<!-- 4. font-display: swap → instant fallback to system font -->
```

| 指標 | P56 | P100 | 改善 |
|------|-----|------|------|
| FCP | 19.4s | 0.8s | **-96%** |
| TBT | 8.2s | 0ms | **-100%** |
| CLS | 0.12 | 0.00 | **-100%** |
| Performance | 56 | **100** | +44 |

## Consequences

### ✅ 正面

- 投影片型 HTML 的 Lighthouse P100 可複製到任意 PPT→HTML 產出
- 修復僅需改 4 行 `<link>`，無需動 CSS/JS
- font-display: swap 確保中文內容在字體載入前可讀

### ⚠️ 取捨

- 用戶可能看到短暫的字體閃爍（FOUT），但優於 19s 白屏
- NoScript fallback 增加 1 行（可接受）

### 🔮 未來方向

- 字體子集化（subset）減少下載量
- 自託管字體（繞過 Google Fonts CDN latency）
- Landing Page Performance 待修（P55→85，需相同修復）

## References

- showcase/aps-ai-agent.html（已套用字體優化）
- showcase/cris-impacts-carbon.html（已套用）
- showcase/runs-impacts-aps-partner.html（已套用）
- lighthouse/ 目錄（v3 審計報告）