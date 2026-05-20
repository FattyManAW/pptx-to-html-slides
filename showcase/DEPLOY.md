# DEPLOY.md — Power Squad GitHub Pages 部署標準化 SOP

> **目標**：任何人（Smart / Technus / Christina / 新人）拿到這份文檔都能獨立部署。

---

## 目錄

1. [gh-pages 分支結構標準](#1-gh-pages-分支結構標準)
2. [版本號命名規則](#2-版本號命名規則)
3. [showcase 目錄結構規範](#3-showcase-目錄結構規範)
4. [自動部署腳本](#4-自動部署腳本)
5. [CI/CD GitHub Actions（可選）](#5-cicd-github-actions可選)
6. [團隊成員部署 Checklist](#6-團隊成員部署-checklist)
7. [常見問題](#7-常見問題)

---

## 1. gh-pages 分支結構標準

### 原則

- **gh-pages 是生產分支**，只有要部署到 GitHub Pages 的檔案
- **PPTX 原始檔不該在 gh-pages 上**（目前 3 份 PPTX 共 63MB，浪費部署空間）
- **主分支（main/master）放原始碼與建構工具**
- **gh-pages 只放靜態網站產出**

### 標準目錄結構

```
gh-pages/
├── index.html                  ← 入口：Landing Page（團隊展示站）
├── showcase/                   ← 正式交付品
│   ├── runs-impacts-aps-partner.html     # 润思 IMPACTS（62 slides）
│   ├── aps-ai-agent.html                 # APS AI Agent（12 slides）
│   ├── cris-impacts-carbon.html          # CRIS IMPACTs（36 slides）
│   ├── landing.html                      # Power Squad 作品集（備份）
│   ├── README-runs-impacts.md
│   ├── README-aps.md
│   ├── README-cris.md
│   ├── DEPLOY.md                         # 本文件
│   └── images/                           # 共享圖片資源
│       ├── slide10_图形_11_*.png
│       ├── ...
│       └── img_map.json
├── html/                        ← 舊版/開發中版本（保留但不為入口）
│   ├── aps-ai-agent.html
│   ├── cris-impacts-carbon.html
│   ├── cris-impacts-carbon.v3.html
│   ├── runs-impacts-aps-partner-v3.1.html
│   ├── runs-impacts-aps-partner.html
│   ├── ...（歷史版本）
│   ├── images/                  ← 舊版圖片
│   └── aps-assets/              ← APS 舊版 assets
├── gen_slides/                  ← 生成工具（供參考）
│   ├── gen_slides.py
│   ├── design_tokens/
│   └── src/
└── gen_v3.py                    ← 潤思投影片定義
```

### ❌ 不該出現在 gh-pages 的檔案

| 檔案 | 大小 | 原因 |
|------|------|------|
| `*.pptx` | ~63MB 合計 | 原始素材，應只在 main 分支 |
| `html/*-backup.html` | 不定 | 備份不應部署 |
| `gen_slides/output_test.html` | 不定 | 測試輸出 |
| `slides_v3.json` | 14KB | 中間產物 |

---

## 2. 版本號命名規則

### 格式

```
{product}-v{major}.{minor}.{patch}.html
```

### 範例

| 檔案名 | 版本 | 意義 |
|--------|------|------|
| `runs-impacts-aps-partner-v3.0.html` | v3.0 | 六大原則初版 |
| `runs-impacts-aps-partner-v3.1.html` | v3.1 | 潤思 CSS 系統級修復 |
| `runs-impacts-aps-partner-v3.2.html` | v3.2 | 內容層 QA 全過 |

### 版本遞增規則

| 層級 | 觸發條件 | 範例 |
|------|----------|------|
| **Major（X.0）** | 全面重做、設計系統更換 | v2→v3（六大原則重寫） |
| **Minor（X.Y）** | CSS 修復、內容補齊、QA 分數躍升 | v3.0→v3.1（潤思 CSS token） |
| **Patch（X.Y.Z）** | Bug fix、小範圍文字修復 | v3.1→v3.1.1（修錯字） |

### 穩定版連結

`showcase/` 下的主檔名（無版本號）永遠指向**最新穩定版**：

```
showcase/runs-impacts-aps-partner.html    ← 最新穩定版（目前 v3.1）
showcase/aps-ai-agent.html                ← 最新穩定版（目前 v3）
showcase/cris-impacts-carbon.html         ← 最新穩定版（目前 v3）
```

---

## 3. showcase 目錄結構規範

### 每個交付品必須包含

```
showcase/
├── {product-slug}.html          ← 主 HTML（最新穩定版）
├── {product-slug}-v{x}.{y}.html ← 歷史版本（可選，保留在 html/）
├── README-{product-slug}.md     ← 技術文件
├── images/                      ← 共享圖片（所有產品共用）
│   ├── slide{N}_{描述}_{hash}.{ext}
│   └── img_map.json
└── {product}-assets/            ← 產品專用 assets（如果有）
```

### 圖片命名規範

```
slide{N}_{type}_{hash}.{ext}

範例：
slide19_圖片_4_cc620d64.jpeg
slide10_图形_11_7a305f0c.png
```

- `{N}` = 原始 PPTX slide 編號
- `{type}` = 圖片/图形/表格（來自 PPTX 內部名稱）
- `{hash}` = 8 位 hex（防止同名衝突）
- `{ext}` = png / jpeg / gif

### 不該做的事

- ❌ 不要把 PPTX 放進 showcase
- ❌ 不要把 base64 圖片內嵌進 HTML
- ❌ 不要用中文檔名（GitHub Pages 路徑相容性）
- ❌ 不要用空格或特殊字元在檔名

---

## 4. 自動部署腳本

### 本地部署（推薦方式）

```bash
#!/bin/bash
# deploy.sh — Power Squad GitHub Pages 一鍵部署
# 用法: ./deploy.sh "v3.2 — 全員 QA 100% + P100"

set -e

REPO_DIR="/Users/henry/Documents/任務檔案/投影片轉換"
SHOWCASE_DIR="$REPO_DIR/showcase"
HTML_DIR="$REPO_DIR/html"
COMMIT_MSG="${1:-deploy: update showcase}"

echo "🚀 Power Squad Deploy"
echo "===================="

# 1. 切換到 gh-pages
cd "$REPO_DIR"
git checkout gh-pages 2>/dev/null || {
  echo "❌ 找不到 gh-pages 分支，請先建立"
  exit 1
}

# 2. 同步 showcase/ → gh-pages
echo "📦 同步 showcase/ ..."
rm -rf showcase/ 2>/dev/null
cp -r "$SHOWCASE_DIR" showcase/

# 3. 同步 html/（保留歷史版本）
echo "📦 同步 html/ ..."
rm -rf html/ 2>/dev/null
cp -r "$HTML_DIR" html/

# 4. 移除不該部署的檔案
echo "🧹 清理不該部署的檔案 ..."
find . -name "*.pptx" -delete
find . -name "*-backup.html" -delete
find . -name "output_test.html" -delete

# 5. Git 操作
echo "📝 Git add + commit ..."
git add -A
git status

echo ""
read -p "確認提交？[y/N] " confirm
if [[ "$confirm" != "y" ]]; then
  echo "已取消。"
  exit 0
fi

git commit -m "$COMMIT_MSG"
git push origin gh-pages

echo ""
echo "✅ 部署完成！"
echo "🔗 https://fattymanaw.github.io/pptx-to-html-slides/"
echo "⏱  GitHub Pages 通常 1-2 分鐘 rebuild"
```

### 快速部署（單一檔案更新）

```bash
#!/bin/bash
# quick-deploy.sh — 只更新一個 HTML 檔案到 gh-pages
# 用法: ./quick-deploy.sh showcase/landing.html "fix: landing page lighthouse P100"

set -e

FILE="$1"
MSG="${2:-quick deploy: update $FILE}"

git checkout gh-pages
cp "$FILE" .
git add "$(basename "$FILE")"
git commit -m "$MSG"
git push origin gh-pages

echo "✅ $FILE deployed"
```

---

## 5. CI/CD GitHub Actions（可選）

適合 Technus 的 cron 自動化技能 — 在 main 分支 push 時自動部署到 gh-pages。

```yaml
# .github/workflows/deploy.yml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:  # 允許手動觸發

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to gh-pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./showcase
          publish_branch: gh-pages
          force_orphan: true  # 只保留最新版本
          commit_message: "deploy: ${{ github.event.head_commit.message }}"
```

> ⚠️ `force_orphan: true` 會清除 gh-pages 歷史（只留最新）。如果需保留歷史版本，設為 `false`。

---

## 6. 團隊成員部署 Checklist

### 部署前

- [ ] QA Pipeline 掃描通過（QA ≥ 85%）
- [ ] Lighthouse ≥ P85（Performance）
- [ ] 所有圖片路徑使用相對路徑（`images/...` 或 `assets/...`）
- [ ] 無 base64 圖片
- [ ] 無 PPTX 專用字體（僅用 Google Fonts）
- [ ] `<meta name="description">` 已填入
- [ ] `<title>` 有意義（非 "Presentation"）
- [ ] RWD 三斷點已測試（桌面/平板/手機）
- [ ] 檔案放在正確目錄（`showcase/` 或 `html/`）
- [ ] README 已更新版本號

### 部署中

- [ ] `git checkout gh-pages`
- [ ] 複製新檔案到正確位置
- [ ] 移除 PPTX / backup / test 檔案
- [ ] `git diff --stat` 確認變更範圍
- [ ] Commit message 包含版本號與摘要

### 部署後

- [ ] 等 1-2 分鐘 GitHub Pages rebuild
- [ ] 瀏覽器開啟 `https://fattymanaw.github.io/pptx-to-html-slides/`
- [ ] 點擊三張卡片確認所有連結有效（無 404）
- [ ] 跑一次 Lighthouse 確認線上分數不低於本地
- [ ] Board chat 公告部署完成 + 分數

### 緊急 Rollback

```bash
# 回退到上一個 commit
git checkout gh-pages
git revert HEAD --no-edit
git push origin gh-pages
```

---

## 7. 常見問題

### Q: showcase/ 和 html/ 的差別？

| 目錄 | 用途 | 受眾 |
|------|------|------|
| `showcase/` | 正式交付品、Landing Page 連結目標 | 客戶 / Nana |
| `html/` | 開發中版本、歷史版本、實驗 | 團隊內部 |

部署到 Landing Page 的卡片連結應指向 `showcase/`。

### Q: 為什麼 gh-pages 上有 PPTX 檔案？

歷史遺留問題。目前已 63MB，應移到 main 分支。用 `git rm *.pptx` 清理。

### Q: 圖片路徑怎麼處理？

所有圖片統一放在 `showcase/images/`，HTML 內用相對路徑：

```html
<!-- ✅ 正確 -->
<img src="images/slide19_圖片_4_cc620d64.jpeg">

<!-- ❌ 錯誤 — 絕對路徑 -->
<img src="/Users/henry/Documents/任務檔案/投影片轉換/images/...">
```

### Q: 新產品要加進 Landing Page？

編輯 `showcase/landing.html`（或根目錄 `index.html`）：

1. 複製現有 `.card` 區塊
2. 更換內容（標題、描述、連結、分數）
3. 選一個 accent color（或新增 CSS 變數）
4. 重新部署

---

## 附錄：目前部署狀態

| 項目 | 狀態 |
|------|:---:|
| GitHub Pages | ✅ https://fattymanaw.github.io/pptx-to-html-slides/ |
| gh-pages 分支 | ✅ 159 files |
| Landing Page (index.html) | ✅ P100 Lighthouse |
| 润思 IMPACTS | ✅ P85 / QA 92% |
| APS AI Agent | ✅ P100 / QA 85% |
| CRIS IMPACTs | ✅ P100 / QA 85% |
| 三份 README | ✅ 完成 |
| PLAYBOOK.md | ✅ Smart 完成 |
| QA Cron | ✅ Technus 完成 |
| **本文件** | ✅ v1.0 |

---

*最後更新：2026-05-20 · Power Squad · v1.0*