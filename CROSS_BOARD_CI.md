# CROSS_BOARD_CI.md — 跨板 CI 統一部署指南

> CI/CD v10 支援跨 repo 複用，同一份 deploy.yml 適配任何 ppthtml 產品 repo。

## 架構

```
        ┌──────────────┐        ┌──────────────┐
        │ Power Squad  │        │  CRIS SWAT   │
        │ pptx-to-     │        │  cris-swat-  │
        │ html-slides  │        │  showcase    │
        └──────┬───────┘        └──────┬───────┘
               │                       │
        ┌──────▼───────────────────────▼──────┐
        │         ci-status.json              │
        │   (Badge JSON per repo, same schema)│
        └──────────────────────────────────────┘
```

### 共用 Stages
| Stage | Power Squad | CRIS SWAT | 註 |
|-------|-------------|-----------|-----|
| 🔍 Lint | ruff | ruff | 相同 |
| 🧪 QA Gate | run_qa.py | run_qa.py | per-product manifest |
| - Token | extract-tokens.py | extract-tokens.py | 相同 |
| - A11y | WCAG AA scan | WCAG AA scan | 相同 |
| 🔍 Lighthouse | ≥P85 per HTML | ≥P85 per HTML | 相同 |
| 🧪 Test | pytest (if tests/) | pytest (if tests/) | optional |
| 🔗 Routes | all showcase/*.html | all showcase/*.html | 相同 |
| 🚀 Deploy | gh-pages | gh-pages | 各自 repo |
| 🏷️ CI Badge | ci-status.json | ci-status.json | 相同 schema |
| 📊 Report | artifact | artifact | 相同 |

## CRIS SWAT 啟動步驟

### 前置條件
- GitHub repo: `FattyManAW/cris-swat-showcase`
- 目錄結構已有 `showcase/*.html`
- 已有 `run_qa.py`, `extract-tokens.py`, `extract_json.py`

### Step 1: 複製 deploy.yml v10
```bash
cd cris-swat-showcase
mkdir -p .github/workflows
cp ../pptx-to-html-slides/.github/workflows/deploy.yml .github/workflows/
```

### Step 2: GitHub 設定
Settings → Actions → General:
- ✅ Read and write permissions
- ✅ Allow GitHub Actions to create and approve pull requests

Settings → Pages:
- Source: Deploy from a branch
- Branch: gh-pages / (root)

### Step 3: 驗證
```bash
# 本地測試
python3 run_qa.py --ci
python3 extract-tokens.py --check
# push → Actions tab 確認 5-stage 全線通過
```

### Step 4: CI Badge 嵌入
在 CRIS SWAT README 加入：
```markdown
![CI/CD](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/FattyManAW/cris-swat-showcase/ci-status/ci-status.json)
```

## v10 vs v9 差異
| | v9 (Power Squad-only) | v10 (Cross-Board) |
|---|---|---|
| Product discovery | hardcoded 3 products | dynamic showcase/*.html |
| Test gate | none | pytest (if tests/) |
| CI badge | manual | auto ci-status.json |
| Lighthouse skip | none | workflow_dispatch input |
| Index fallback | landing→index | flexible (any first .html) |
| Rollback message | generic | repo-aware |
| Token gate | grep [CM] | grep [CM] (same) |
| A11y gate | hardcoded paths | glob showcase/*.html |

## 兩板對照
| | Power Squad | CRIS SWAT |
|---|---|---|
| Repo | FattyManAW/pptx-to-html-slides | FattyManAW/cris-swat-showcase |
| Products | 潤思/APS/CRIS/用友 | CRIS 主題 |
| QA tools | run_qa.py + extract-tokens + a11y | same |
| Deploy URL | fattymanaw.github.io/pptx-to-html-slides/ | fattymanaw.github.io/cris-swat-showcase/ |
| CI Badge | ✅ | 啟動後可用 |

## 維護
- 所有板共用同一份 deploy.yml 邏輯
- 產品差異透過 `showcase/*.html` 動態發現
- 若有 repo-specific 需求 → workflow_dispatch input 或 env var 控制
- 共用 schema: `ci-status.json`（標籤/顏色/階段/時間戳）