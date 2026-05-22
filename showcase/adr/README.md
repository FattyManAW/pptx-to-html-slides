# Architecture Decision Records

> Power Squad · Sprint 2 (2026-05-18 – 2026-05-21)
> 格式：Michael Nygard ADR format（Context → Decision → Consequences）

---

## Decision Map

```
  PPTX 來源
      │
  [001] gen_slides Pipeline ──── 三層分離管線演進
      │
      ├── 設計系統 ──── [002] Token Compat Shim
      │                    │
      │                    └───> extract-tokens.py (CI gate)
      │
      ├── QA 品質 ──── [004] QA Check Gate (P0/P1/P2 + baseline diff)
      │                    │
      │                    └───> run_qa.py / qa_pipeline.py
      │
      ├── 效能 ──── [003] Lighthouse P100 (font loading 關鍵路徑)
      │
      └── HTML 結構 ──── [005] slide-inner 統合處理 (parser 雙向防禦)
```

---

## ADR Index

| # | 標題 | 狀態 | 日期 | 作者 | 範疇 | 關聯 |
|---|------|:----:|------|------|------|------|
| 001 | [gen_slides Pipeline 選型演進](adr-001-gen-slides-pipeline.md) | ✅ accepted | 05-20 | Smart | Architecture | 002, 004 |
| 002 | [Token Compat Shim 策略](adr-002-token-compat-shim.md) | ✅ accepted | 05-20 | Smart | Design System | 001, 004 |
| 003 | [Lighthouse P100 關鍵路徑](adr-003-lighthouse-p100-path.md) | ✅ accepted | 05-20 | Smart | Performance | 001 |
| 004 | [QA Check Gate 設計](adr-004-qa-check-gate.md) | ✅ accepted | 05-20 | Smart | QA / CI | 001, 002, 005 |
| 005 | [slide-inner 統合處理](adr-005-slide-inner-parser.md) | ✅ accepted | 05-20 | Smart | Parser | 004 |

---

## 決策時間線

```
Sprint 1 (05-18)                Sprint 2 (05-19 → 05-20)
────────────────────────────────────────────────────────────────
18:00 原始 PPTX → HTML          00:24 OTD 模擬引擎開工
20:00 v1 產出（17MB, P56）      07:33 Research phase
02:00 v2 重做（六原則）          20:35 [004] QA Pipeline v1 auto
18:00 v3 gen_slides 模組化      21:44 [002] Token 統合
                                22:00 [005] slide-inner fix
                                21:37 Cross-Team Charter
                                22:04 [001] gen_slides v4
                                ── [003] Lighthouse P100
```

---

## 統計

| 指標 | 數值 |
|------|------|
| 總 ADR 數 | 5 |
| Accepted | 5 |
| Proposed / Deprecated / Superseded | 0 |
| 作者分佈 | Smart: 5 / Technus: 0 / Christina: 0 |
| 涵蓋範疇 | Architecture, Design System, Performance, QA, Parser |

---

## 格式規範

每篇 ADR 遵循標準結構：

```markdown
# ADR-NNN: 標題

> 狀態: proposed | accepted | deprecated | superseded
> 日期: YYYY-MM-DD
> 作者: Name (Team)
> 標籤: tag1, tag2

## Context — 當時的情境與約束
## Decision — 做了什麼決定 + 被拒絕的替代方案
## Consequences — ✅ 正面 / ⚠️ 取捨 / 🔮 未來方向
## References — 關聯文件 / task / PR
```

---

## 關鍵數字（跨 ADR 摘要）

| 指標 | Before | After | 改善 |
|------|--------|-------|:----:|
| Lighthouse Perf | P56 | **P100** | +44 |
| Token common set | 32/105 (30%) | **73/105 (70%)** | +40% |
| QA scan time | 20m manual | 5s auto | **240×** |
| Slide count detection | 0 (CRIS bug) | correct | ✅ |
| Pipeline stages | 1 (direct) | 3 (extract→json→render) | modular |

---

*ADR Index v1.0 · Power Squad · Updated 2026-05-21 04:35 Asia/Taipei*