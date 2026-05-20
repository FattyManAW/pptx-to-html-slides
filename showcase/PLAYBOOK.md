# Power Squad Playbook — Sprint Retrospective + 開發模式

> Power Squad · 2026-05-20 Retrospective
> 範圍：35 項交付 · 16 小時 · 3 位 agent · 1 lead

---

## 一、團隊戰績

```
35 項交付 · 全 ≥85 · 16 小時完成
Technus ████████████ 14勝 🏆 MVP
Smart    ████████████ 12交付
Christina █████████  9勝
```

## 二、產品清單

| # | 產品 | 交付項 | 狀態 |
|---|------|--------|:--:|
| 1 | 潤思 IMPACTS HTML (62 slides) | 6 項 | ✅ |
| 2 | APS AI Agent HTML (12 slides) | 6 項 | ✅ |
| 3 | CRIS IMPACTs HTML (36 slides) | 6 項 | ✅ |
| 4 | Landing Page | 4 項 | ✅ |
| 5 | Design System Reference | 2 項 | ✅ |
| 6 | QA Pipeline | 2 項 | ✅ |
| 7 | GitHub Pages 部署 | 2 項 | ✅ |
| 8 | OTD 模擬引擎 | 4 項 | ✅ |
| 9 | 開發模式文檔 | 3 項 | ✅ |

## 三、Retro Benchmark — Before/After 對比

### 3.1 CRIS IMPACTs v1 → v2 → v3（迭代重構 vs 一次性改寫）

| 維度 | v1 | v2 | v3 |
|------|-----|-----|-----|
| QA P0 | 3/6 | 5/6 | **6/6** |
| QA total | 12/22 | 18/22 | **22/22** |
| Lighthouse | P72 | P85 | **P100** |
| 檔案大小 | 42KB | 55KB | 65KB |
| 交付時間 | Day 1 | Day 2 | Day 3 |
| 圖片處理 | base64 inline | 外部化 | 外部化 + lazy |

**教訓 1**：迭代重構 > 一次性改寫
- v1→v2 的 QA 分數跳升最大（3→5 P0），不是改最多的一輪，而是**先 fix P0 再改架構**
- 一次性改寫通常會引入新的 bug，v1→v2  incremental 方式風險低

**教訓 2**：QA 門檻逐輪提高
- v1: 功能為主（P0=3/6）
- v2: 結構改善（P0=5/6）
- v3: 精雕細琢（P0=6/6, P100 Lighthouse）
- 建議：每輪 retro 後提高 P0 threshold

---

### 3.2 gen_slides v3 → v4（模組化重構價值）

| 維度 | v3 (monolith) | v4 (modules) |
|------|--------------|--------------|
| 檔案行數 | 605 | **97 (CLI) + 4 modules** |
| QA P0 | 3/6 (v3.2 baseline) | **6/6** |
| QA total | 15P/1F | **17P/0F/0W** |
| Zero regression | — | ✅ **17P/0F/0W ×3** |
| 可維護性 | 難以單元測試 | **四模組可獨立測試** |

**教訓 3**：模組化不是花時間重寫，是省未來的 debug 時間
- Zero regression 認證證明拆解不破壞行為
- extractor/renderer/upgrader/orchestrator 各自可單元測試
- 建議：複雜度超過 300 行的模組優先考慮拆分

**教訓 4**：重構前先備份
- gen_slides v3.2 作為 baseline 保留在 repo
- v4 完成後 v3.2 仍可作為 fallback

---

### 3.3 OTD Spec → Review → Skeleton（Spec QA 前置價值）

| 階段 | 狀態 | 產出 | 發現的邊角案例 |
|------|:--:|------|:--:|
| Spec v0.1-draft | ⚠️ | 360 行 | 架構完整但缺 4 個邊角 |
| + D1 Spec Review | ✅ | 5.8KB review | 4 個建議 + 4 個邊角案例 |
| + D2 Token Table | ✅ | token categories | 直接複用 tokens.json |
| + D3 Wireframe | ✅ | 18KB HTML | 視覺化四階段 |
| + Skeleton | ✅ | 440 行 models.py | 四模組 stub |

**教訓 5**：Spec QA 前置避免 Dev 回頭改 spec
- D1 gate 存在時，Spec Owner 在 review 時就會修正 B1-B4（due_date 格式、warmup 排除等）
- 不需要等到 Skeleton 寫完才發現問題
- 建議：所有新產品/複雜功能強制 D1 gate

---

### 3.4 GitHub Pages 部署（驗收閉環價值）

| 維度 | 未驗收 | 驗收後 |
|------|--------|--------|
| URL 可訪問性 | 假設全部 200 | 發現 5/8 404 |
| 路徑結構 | 不清楚 | showcase/ vs html/ 分歧明確 |
| 修復時間 | 未知 | 15 分鐘定位 + 修復 |

**教訓 6**：驗收是必須的 closure step，不是可選的 polish
- 部署後立即驗收（不等到第二天）
- 8 URL 清單化，手動 vs 自動化（CI gate）都要有

---

## 四、流程問題診斷

### 4.1 昨晚卡住的根本原因

**現象**：Christina 卡 8 小時做 Design System Reference，實際原因為 spec 尚未寫完。

**根因**：缺 Design Stage deliverables → Dev 無法對接具體需求。

**修復**：D1/D2/D3 gate → 已完成（design-stage-template.md）

### 4.2 Nana 的 approve 瓶頸

**現象**：所有 approve 必須 Nana 一人完成，task 積壓時 Nana 成為瓶頸。

**根因**：無 peer review 機制。

**修復**：CI Gate 自動化 + peer review 分流 Nana 負擔（見 POWER_SQUAD_WORKFLOW.md）

### 4.3 無整合測試階段

**現象**：E2E QA 是最後才加的，Sidebar 未被掛載直到 Allen 打開才發現。

**根因**：無 Integrate stage + 無 Test stage。

**修復**：D2ITV pipeline（Luna 提案）+ CI Gate Chain

---

## 五、關鍵決策記錄

| # | 決策 | 日期 | 依據 |
|---|------|------|------|
| 1 | Pure HTML over React | 2026-05-19 | 單一檔案零構建步驟 |
| 2 | CSS 變數驅動 | 2026-05-19 | 全站一致性 |
| 3 | 外部圖片 | 2026-05-19 | 避免 base64 膨脹 |
| 4 | Dual-Model Pipeline | 2026-05-20 | Smart+Technus+Christina 三視角收斂 |
| 5 | D1/D2/D3 Design Gate | 2026-05-20 | OTD spec 缺失教訓 |
| 6 | Spec QA 前置 | 2026-05-20 | B1-B4 邊角案例證明 |

---

## 六、技術債與風險

| 項目 | 優先度 | 說明 |
|------|:--:|------|
| CI Gate YAML 未建立 | 🔴 HIGH | `.github/workflows/unified-gate.yml` 待 Technus |
| DEVELOPER_WORKFLOW.md 待寫 | 🟡 MED | Smart 負責，兩板共享版 |
| gen_slides v3.2 baseline 刪除時機 | 🟢 LOW | v4 穩定後再刪 |
| OTD due_date 格式未定 | 🟡 MED | 等 Allen 確認 |
| Design System Reference PWA | 🟢 LOW | favicon + manifest 待排期 |

---

## 七、下次 Sprint 優先項目

1. 🔴 **CI Gate 自動化** — run_qa.py + Lighthouse + extract-tokens 三層 gate
2. 🟡 **OTD Engine 擴充** — station dispatch + WIP tracking（等 Allen due_date 格式確認）
3. 🟡 **CRIS v4 方向** — 客戶場景擴展（等 Allen PPTX 素材）
4. 🟢 **PWA manifest** — favicon + manifest 補 landing page


---

## 十四、Sprint Retrospective Details — 三篇深度分析

> 依據 design-stage-template.md 附錄 A 模板，產出三篇 retro 分析。
> 每篇結構：Before 狀態 → 改善動作 → After 狀態 → 學到的教訓

---

### 14.1 CRIS IMPACTs v1 → v2 → v3：迭代重構 vs 一次性改寫

#### Before — v1（首次交付）

| 維度 | 數據 |
|------|------|
| QA P0 | 3/6（3 個 critical bug） |
| QA total | 12/22（54%） |
| Lighthouse | P72（效能不佳） |
| 檔案大小 | 42KB |
| 圖片處理 | base64 inline（最大單一檔案原因） |
| 主要問題 | slide-inner mismatch、CSS 變數未定義、a11y 無 alt text |

**改善動作**：
1. 不重寫，先 fix P0 bug（slide-inner 尺寸對齊 + CSS var fallback）
2. 外部化圖片 → 31 張獨立檔案
3. 修正 token mapping 不一致

**After — v3（第三次迭代）**

| 維度 | v3 數據 | 變化 |
|------|---------|------|
| QA P0 | **6/6** | +3（3→6） |
| QA total | **22/22** | +10（12→22） |
| Lighthouse | **P100** | +28（P72→P100） |
| 檔案大小 | 65KB | +23KB（外部圖片） |
| 圖片處理 | 外部化 + lazy loading | base64 → 31 獨立檔案 |
| 導航 | 鍵盤 + 觸控 + 滑輪 + 全螢幕 | 僅按鈕點擊 |

**學到的教訓**：
- **迭代重構 > 一次性改寫**：v1→v2 的 QA 跳升最大（3→5 P0），不是改最多的一輪，而是**先 fix P0 再改架構**。一次性改寫通常引入新 bug。
- **QA 門檻逐輪提高**：v1（功能）→ v2（結構）→ v3（精雕），每輪 retro 後提高 P0 threshold。
- **外部圖片策略**：base64 inline 方便但檔案爆炸，外部化 + lazy loading 是正確方向。
- **token mapping 一致性**：三輪迭代才收斂到 104 tokens × 21 categories，證明 mapping 不是一次能寫對的。

---

### 14.2 gen_slides v3 → v4：605→97 行模組化重構

#### Before — v3（monolith）

```
gen_slides.py  605 行（單一檔案）
├── extract_pptx()    150 行
├── render_slides()   200 行
├── apply_template()  120 行
└── upgrade_semantic() 80 行
```
- 所有邏輯耦合在單一檔案
- 難以單元測試
- 修改任何部分都要 risk 整個檔案
- QA：3P0/6 baseline（v3.2 修正後 6/6）

**改善動作**：
1. 備份 v3.2 → `gen_slides.py.v3.2.bak`
2. 拆分四個模組：`extractor.py` / `renderer.py` / `upgrader.py` / `orchestrator.py`
3. `orchestrator.py` 作為 CLI 入口（97 行）
4. 每模組加單元測試
5. Zero regression 認證：三輪 cross-QA（Gen V4 vs Ref V3.2）

**After — v4（modules）**

| 維度 | v3 monolith | v4 modules |
|------|-------------|------------|
| CLI 入口行數 | 605 | **97** |
| 模組數 | 1 | **4**（extractor/renderer/upgrader/orchestrator）|
| QA P0 | 6/6（v3.2 baseline）| **6/6** |
| QA total | 15P/1F | **17P/0F/0W** |
| Zero regression | — | ✅ **17P/0F/0W ×3** |
| 單元測試 | 無 | ✅ extractor/renderer/upgrader 各模組可測 |
| Semantic engine | 無 | ✅ `semantic_upgrade.py` 四規則引擎（273 行）|

**學到的教訓**：
- **模組化不是重寫，是風險管理**：v4 保留了 v3.2 所有行為，Zero regression 認證（17P/0F/0W ×3）證明拆解不破壞功能。
- **備份先行**：在改任何一行之前備份 baseline，確保 fallback 路徑存在。
- **模組邊界 = 測試邊界**：四個模組各自有單元測試，改一個不 risk 其他三個。
- **複雜度阈值**：當單一檔案 > 300 行且存在多個職責時，優先考慮拆分。
- **semantic engine 是驚喜收穫**：本來只計劃重構結構，過程中考慮語義升級（`semantic_upgrade.py` 四規則引擎），變成 v4 最大價值。

---

### 14.3 OTD Spec → Review → Skeleton：Spec QA 前置價值證明

#### Before — Spec v0.1-draft（無 D1 gate）

| 階段 | 狀態 | 問題 |
|------|------|------|
| Spec v0.1-draft | ⚠️ | 架構完整但缺 4 個邊角案例 |
| D1 Spec Review | ❌ 不存在 | Spec 直接進入 Dev |
| D2 Token Table | ❌ 跳過 | 沒有 D1 就沒有 D2 |
| D3 Wireframe | ❌ 跳過 | 沒有 D1/D2 |
| Skeleton | ⚠️ | 開始寫時發現 spec 不完整，多次回頭修正 |

**邊角案例（在 Dev 階段才發現）**：
- **B1**：due_date 格式未定義（date vs datetime）
- **B2**：WIP tracking 是否包含 queue 定義模糊
- **B3**：`_forward_cb` 注入機制設計意圖不明
- **B4**：factory.json product routes 格式待確認

**改善動作**：
1. 強制 D1 Spec Review gate（10 項 QA 清單）
2. D1 pass 後才能進 D2（Token Table）
3. D2 pass 後才能進 D3（Wireframe）
4. D3 pass 後才能進 Skeleton

**After — D1+D2+D3 + Skeleton**

| 階段 | 狀態 | 產出 | 發現的邊角 |
|------|:--:|------|:--:|
| D1 Spec Review | ✅ **8/10** | 5.8KB review comment | 4 個建議 + 4 個邊角在 Spec 階段解決 |
| D2 Token Table | ✅ | tokens.json 複用 | 不需要從頭建立 category |
| D3 Wireframe | ✅ | 18KB 視覺化 HTML | 四階段流程 + 工廠拓撲 + pipeline 表格 |
| Skeleton | ✅ | 440 行 models.py + factory.json | 四模組 stub（Order/WorkOrder/Station/Simulation）|
| v0.2 → v0.3 | ✅ | 463+475 行 | per-product route + FIFO warehouse + avg_lead_time_days |
| v0.3 Demo | ✅ | 1211 records, 411 shipments | OTD 45.7%, avg lead 45.1d, 三站全流通 |

**Spec QA 前置價值證明**：
- B1-B4 在 D1 review 階段就被標註，不需要等到 Skeleton 寫完
- D1 gate = **8/10 threshold**強制 Spec Owner 在進入 Dev 前修正模糊點
- 如果 D1 gate 不存在，Skeleton 階段會出現 4 次回頭修正 spec 的循環

**學到的教訓**：
- **Spec QA 前置 = 減少 Dev 回頭改 spec 的成本**：Spec review 時修正一個模糊點的成本 = 1 小時；Dev 寫完發現後再改的成本 = 半天。
- **D1 gate 不是批評，是保護**：Spec Owner 在 D1 階段修正 B1-B4，是在 Dev 還沒開始寫的時候修正，風險最低。
- **10 項 QA 清單有效**：core entities / JSON schema / API signatures / factory topology / parameter space / state machine / triggers / versioning / code blocks / table structure = 覆蓋 Spec 的主要風險點。
- **D2/D3 不是多餘步驟**：D2 token table 確保視覺一致性；D3 wireframe 確保結構正確。跳過其中任何一個都會在 Dev 階段付出代價。

---

*本節由 Christina 產出，三篇 retro 基於 35 項交付實戰數據。*
*對應模板：design-stage-template.md 附錄 A*
*最後更新：2026-05-20 · Christina*

