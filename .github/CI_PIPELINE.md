# CI/CD Pipeline — Power Squad 自動化部署

> **push main → QA Gate → Lighthouse Audit → Deploy → 成績單推 board chat**

---

## Pipeline 架構

```
┌──────────┐    ┌───────────┐    ┌───────────┐    ┌──────────────┐
│ QA Gate  │───▶│ Lighthouse│───▶│  Deploy   │───▶│ Report Card  │
│ run_qa.py│    │ 3 product │    │ gh-pages  │    │ → board chat │
└──────────┘    └───────────┘    └───────────┘    └──────────────┘
     │                │                │                  │
     ▼                ▼                ▼                  ▼
┌──────────┐    ┌───────────┐    ┌───────────┐    ┌──────────────┐
│ ≥85%     │    │ ≥P85      │    │peaceiris/  │    │ 成功/失敗     │
│ PASS     │    │ per prod  │    │gh-pages@v4 │    │ 分數摘要      │
└──────────┘    └───────────┘    └───────────┘    └──────────────┘

任何 stage 失敗 → 自動 Rollback Alert → board chat ⚠ 告警
gh-pages 不受影響（只在全部 pass 後才 deploy）
```

## 五個 Stages

### Stage 0: QA Gate
- 執行 `run_qa.py --once --json --no-alert`
- 門檻：三套 FAIL count = 0
- 同時跑 `extract-tokens.py` 檢測 token 漂移（non-blocking）

### Stage 1: Lighthouse Audit
- 本地 HTTP server 起 showcase/
- 跑三套（潤思/APS/CRIS）Lighthouse
- 門檻：每套 Performance ≥ 85
- 輸出 `lh_scores.json`

### Stage 2: Deploy
- 使用 `peaceiris/actions-gh-pages@v4`
- 部署 `showcase/` → `gh-pages` 分支
- 保留歷史版本（`force_orphan: false`）

### Stage 3: Report Card
- 生成成績單 Markdown
- 推送到 board chat（Power Squad）
- 上傳 artifact（ci-report）

### Stage 4: Rollback (on failure)
- 只在 `failure()` 觸發
- 不改變 gh-pages（safe rollback）
- 告警推 board chat

---

## 觸發方式

```yaml
on:
  push:
    branches: [main]         # push main → 自動
  workflow_dispatch:          # 手動觸發（GitHub UI）
```

## 現有積木

| 積木 | 用途 | CI 用法 |
|------|------|---------|
| `run_qa.py` | QA 掃描 | Stage 0 gate |
| `extract-tokens.py` | Token 驗證 | Stage 0 non-blocking check |
| `qa_pipeline.py` | QA 引擎（被 run_qa 調用） | — |
| `DEPLOY.md` | 部署 SOP + deploy.sh | 文件參考 |
| `showcase/` | 三套 HTML + Landing + README | deploy source |

---

## 分數門檻

| 指標 | 門檻 | Stage |
|------|:---:|-------|
| QA PASS rate | 0 FAIL | QA Gate |
| Lighthouse Performance | ≥ 85 | Lighthouse |
| Token drift | non-blocking ⚠ | QA Gate |
| Deploy | all pass → deploy | Deploy |

---

## 本地測試

```bash
# 模擬 QA Gate
python3 run_qa.py --once --no-alert

# 模擬 Lighthouse
lighthouse http://127.0.0.1:8765/runs-impacts-aps-partner.html --chrome-flags="--headless --no-sandbox"

# 模擬 token check
python3 extract-tokens.py

# 手動觸發 workflow
gh workflow run "Power Squad CI/CD"
```

---

## 環境變數與 Secrets

| Secret | 說明 |
|--------|------|
| `GITHUB_TOKEN` | 自動注入，peaceiris deploy 用 |
| API auth token | 已 hardcode 在 workflow（不受 GitHub Secrets 管理） |

---

## Rollback SOP

當 CI 告警時：

1. **檢查失敗 stage**：board chat 收到 `⚠ CI/CD Pipeline FAILED` 訊息
2. **QA Gate 失敗**：修復 HTML，commit，重推
3. **Lighthouse 失敗**：檢查網路/CDN，或調降門檻（極端情況）
4. **Deploy 失敗**：檢查 gh-pages 分支權限
5. gh-pages 不受 CI 失敗影響（只在全部 pass 才寫入）

手動 rollback：
```bash
git checkout gh-pages
git revert HEAD --no-edit
git push origin gh-pages
```

---

## 檔案位置

```
.github/
└── workflows/
    └── deploy.yml          ← CI/CD pipeline definition (8.9KB)
        ├── qa-gate          ← Stage 0
        ├── lighthouse       ← Stage 1
        ├── deploy           ← Stage 2
        ├── report           ← Stage 3
        └── rollback         ← Stage 4
```

---

*版本：v1.0 · 建立於 2026-05-20 · Technus*