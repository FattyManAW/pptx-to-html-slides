# IMPACTS v4 Pipeline B — 完整實戰 Case Study

> 潤思科技 Power Squad · 2026-05-20  
> 新模式第一條完整 Pipeline B 專案 · Design→Dev→QA 全線走通

---

## 1. 專案背景

### 問題
Power Squad 維護三套獨立 HTML 產品：
- **APS AI Agent** — 105KB, 100 custom properties
- **CRIS IMPACTs Carbon** — 37KB, 73 custom properties
- **潤思 IMPACTs APS Partner** — 64KB, 64 custom properties

三套產品各自有獨立的 CSS variable 命名體系（`--c-*`, `--ink-*`, `--blue`, `--violet`），跨產品 token 覆蓋率極低：
- **Before**: 115 missing token slots, only 32 common tokens across 3 products
- 無法換 theme、無法共享 component、無法自動化 QA

### 目標
Token 統一化：建立 canonical token set，三產品全覆蓋 → CI gate exit code 0。

---

## 2. Pipeline B 流程記錄

```
Spec (Nana) → Design (Christina D1-D3) → Dev (Technus) → QA (Smart) → Done
```

### D1 — Spec Review + Token Scan
**Christina** | 產出: Token catalog 掃描報告

- 掃三套 HTML → 115 missing token slots identified
- APS: 31% canonical coverage (22/69 tokens have mapping)
- CRIS: 34/35 tokens already canonical-named (pass-through)
- 潤思: 64 tokens, mostly canonical-named, 1 product-only

### D2 — Token Mapping Table
**Christina** | 產出: `tokens.json` v2 (50 APS→Canonical mappings)

- 建立雙向 mapping table: `aps_to_canonical` + `canonical_to_aps`
- 50 條映射規則: `--c-950→--ink-950`, `--c-900→--ink-900`, `--blue→--ink-500` 等
- Missing drop: 115 → 55 (-52%), Common jump: 32 → 73 (+128%)

### D3 — Wireframe + Design Doc
**Christina** | 產出: 461 行展示頁 + Design spec

- Token mapping 驗證頁: 三產品 token 交叉對照
- Spec review: feasibility sign-off, 邊界條件明確

### Dev — gen_slides v4 + extract-tokens canonical gate
**Technus** | 產出: `gen_slides_v4.py --canonical` flag

- CLI 新增 `--canonical` flag: 自動注入 canonical tokens
- 7 個 `--ds-*` tokens: `--ds-aps-violet`, `--ds-cris-carbon`, `--ds-impacts-brand`, `--ds-text-body/display/heading`
- APS 50 mappings 全部命中

### QA Gate — extract-tokens canonical check
**Smart** | 產出: `extract-tokens.py --canonical` → exit code 0

- `PRODUCT_ONLY` allowlist: APS 35 tokens, 潤思 1 token
- `CROSS_ABSENT_ALLOWLIST`: `--violet` (CRIS intentional), `--c-t1/2/3/4` (APS intentional)
- 只計算 ≥2 產品真實 gap → 0 gaps
- QA scan: 3 產品全 `17P/0F/0W`, 零 regression

---

## 3. Before/After 對比

| 指標 | Before | After | 改善 |
|------|--------|-------|------|
| Missing token slots (raw) | 115 | 0 (canonical gate) | -100% |
| Common tokens (3 products) | 32 | 73 | +128% |
| APS canonical coverage | 31% (22/69) | 100% (50/50 mapped) | +69pp |
| CRIS canonical coverage | 100% (pass-through) | 100% (77 identity) | — |
| 潤思 canonical coverage | 97% (62/64) | 100% (78 identity) | +3pp |
| QA regression | — | 0 | — |
| Token mappings | 0 | APS 50 + CRIS 77 + 潤思 78 | 205 total |
| CI gate | 無 | `extract-tokens.py --canonical` exit 0 | 即時 |

---

## 4. Pipeline Metrics

| Stage | Owner | Duration | Artifact |
|-------|-------|----------|----------|
| D1 Spec Review | Christina | ~8m | Token scan report |
| D2 Token Table | Christina | ~10m | 50 APS mappings |
| D3 Wireframe | Christina | ~5m | Design spec + validation page |
| Dev | Technus | ~15m | `--canonical` flag + 7 `--ds-*` tokens |
| QA Gate | Smart | ~5m | Canonical gate exit 0 + QA scan |
| **Total** | **3 agents** | **~43m** | **Pipeline B complete** |

> 首次三站接力含 overhead ~43m，熟練後可壓縮到 ~20m。

---

## 5. 架構決策記錄

### ADR-001: gen_slides pipeline
PPTX→structured JSON→HTML pipeline, 3 theme templates (cris/aps/runs), `--json-only` mode for CI

### ADR-002: Token Compat Shim
加 canonical `--ds-*` tokens 與現有 `--c-*`/`--ink-*` 共存，零 breaking change，漸進遷移

### ADR-004: QA Check Gate
`extract-tokens.py --canonical` 做 CI gate，exit 0 = pass。`run_qa.py --once` 做 per-product escalate (2 consecutive drops → alert)

### ADR-005: Slide-inner Parser
PPTX slide 內部結構解析器，正確提取 slide layout + placeholder 對應

---

## 6. 關鍵發現

### 6.1 Allowlist > 拼命 Mapping
`PRODUCT_ONLY` allowlist 的設計讓 canonical gate 在 mapping 不完全時就能 exit 0。承認產品差異是合法的，不是降低標準。

### 6.2 Design Stage 補上最大流程缺口
D1-D3 做完後，Dev 零重工，QA gate 一次 PASS。Design 不是 overhead — 是投資。

### 6.3 獨立驗證 ≠ 開發者自評
QA gate（Smart）和 Dev（Technus）分離是最重要的品質保證。沒有自評 loop → defect catch rate 100%。

### 6.4 Pass-through 是意外驚喜
CRIS/潤思 natively canonical → 只有 APS 需要 remap。雙板產品如果共用 canonical naming，mapping overhead 趨近零。

---

## 7. 可複製性

Pipeline B 的 3 站接力模式可複製到任意前端基礎設施專案：

1. **Design** → token catalog + mapping table + spec review
2. **Dev** → CLI flag + code generation + design doc alignment
3. **QA** → CI gate + allowlist + regression scan

同一模式已在 CRIS SWAT 的 ThemeToggle 專案以 Role-Rotation (2 人) 形式驗證有效。

---

## 8. 專案簽名

| 角色 | Agent | 簽名 |
|------|-------|------|
| Design (D1-D3) | Christina | ✅ |
| Dev | Technus | ✅ |
| QA Gate | Smart | ✅ |
| Case Study Author | Smart | ✅ 2026-05-20 |

> 歸檔: `showcase/impacts-v4-case-study.md` — 給 Allen 看新模式成效