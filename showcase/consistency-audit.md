# 跨產品一致性審計報告

> 生成時間: 2026-05-20 06:50 CST  
> 範圍: showcase/ 下四套產品（APS AI Agent · CRIS IMPACTs · 潤思 IMPACTs · Landing Page）  
> 工具: extract-tokens.py + 手動標註

---

## 1. Token 缺口矩陣

### 1.1 總覽

| 指標 | 值 |
|------|-----|
| APS tokens | 74 |
| CRIS tokens | 62 |
| 潤思 tokens | 64 |
| 共用 (all 3) | 32 |
| 唯一 token | 105 |
| 缺漏 slot | 115 |

### 1.2 分類缺口（三套投影片互比）

| 分類 | 總 token | 三套共用 | 缺漏 |
|------|----------|----------|------|
| 🎨 Color Palette | 16 | 0 | 21 |
| 🎨 Semantic Colors | 20 | 8 | 16 |
| 🎨 Accent | 7 | 1 | 11 |
| 🎭 Project Theme | 9 | 0 | 17 |
| 🔮 Blur | 13 | 8 | 9 |
| 🔲 Border Radius | 4 | 0 | 8 |
| 🔤 Heading Scale | 4 | 0 | 7 |
| 🔤 Body Scale | 3 | 0 | 6 |
| 🔤 Display Scale | 3 | 0 | 5 |
| ⏱️ Easing | 3 | 1 | 4 |
| 🔲 Border | 3 | 1 | 3 |
| 🖤 Background | 2 | 0 | 2 |
| 🖤 Surface | 2 | 0 | 2 |
| ⚙️ Data Attributes | 1 | 0 | 2 |
| 🖤 Material | 1 | 0 | 1 |
| 🖤 Shadow | 1 | 0 | 1 |
| ✅ Spacing (8px grid) | 10 | 10 | **0** ✨ |
| ✅ Timing | 3 | 3 | **0** ✨ |

### 1.3 核心缺口矩陣（P0 級）

| Token | APS | CRIS | 潤思 | 影響 |
|-------|:---:|:----:|:----:|------|
| `--c-bg` (深色底色) | ❌ | ✅ | ✅ | APS 無法跨主題切換背景 |
| `--c-bg2` (次要背景) | ❌ | ✅ | ✅ | APS 無材質層次第二層 |
| `--c-bg3` (卡片背景) | ❌ | ✅ | ✅ | APS 卡片缺少標準背景變數 |
| `--c-glass` (毛玻璃) | ❌ | ✅ | ✅ | APS 導航欄無 backdrop-filter token |
| `--c-border` (分割線) | ❌ | ✅ | ✅ | APS 分割線色彩不可控 |
| `--c-surface` (浮層) | ❌ | ✅ | ✅ | APS 缺少材質浮層 token |
| `--c-surface2` (hover 浮層) | ❌ | ✅ | ✅ | APS hover 狀態不一致 |
| `--c-teal` (主題色) | ❌ | ✅ | ✅ | APS 用 multi-accent 體系（設計意圖） |
| `--shadow` | ❌ | ✅ | ✅ | APS 無統一陰影 token |

**結論**: APS 自成體系（自訂 multi-accent + `--c-600~950` palette），CRIS = 潤思子集（0 unique token）。Spacing 和 Timing 是唯一完美一致的兩個類別。

### 1.4 Naming Scheme 分歧

| 概念 | APS | CRIS/潤思 | 建議統一 |
|------|-----|-----------|----------|
| 色階 50-950 | `--c-600~950` | `--ink-50~950` | `--ds-ink-*` |
| 文字層級 | `--c-t1~4` | `--c-t1~4` | ✅ 已統一 |
| 主題 accent | `--accent, --accent-2, --accent-*` | `--accent, --accent-mid` | `--ds-accent` + `--ds-accent-*` |
| Typography scale | `--heading-1~3, --body-1~3, --text-display-1~2` | `--display, --heading` | `--ds-text-*` |
| Border radius | `--r-sm/md/lg/xl` | ❌ 無 | `--ds-r-*` |
| Easing | `--ease, --ease-in, --ease-out` | `--ease` | `--ds-ease-*` |

---

## 2. 動畫模式差異

| 項目 | APS | CRIS | 潤思 | Landing |
|------|:---:|:----:|:----:|:-------:|
| `@keyframes` 數 | 7 | 5 | 5 | 0 |
| `data-stagger` 使用 | 10 處 | 6 處 | **539 處** | 1 處 |
| `scroll-driven` | 1 | 0 | 0 | 1 |
| 純動畫宣告 | 7 | 2 | 3 | 0 |
| transition 宣告 | 7 | 5 | 5 | 6 |

### 2.1 動畫清單

| @keyframes | APS | CRIS | 潤思 | Playbook 允許？ |
|-----------|:---:|:----:|:----:|:--------------:|
| `springIn` | ✅ | ✅ | ✅ | ✅ |
| `slideUp` | ✅ | ✅ | ✅ | ✅ (實戰許可) |
| `slideFromRight` | ✅ | ✅ | ✅ | ✅ (實戰許可) |
| `slideExit` / `slideExitLeft` | ✅ | ✅ | ✅ | ✅ (實戰許可) |
| `slideIn` | ✅ | ❌ | ❌ | ✅ |
| `shimmer` | ✅ | ✅ | ✅ | ✅ (裝飾用) |

### 2.2 關鍵發現

- **APS 動畫最豐富**（7 keyframes + 10 處 stagger），但 Playbook 僅允許 `slideIn` + `springIn`。
- **潤思 data-stagger=539** — 遠超 CRIS(6) 和 APS(10)，因為每張 slide 的每個子元素都有獨立 `data-stagger` 屬性。這會增加 HTML 體積（潤思 105KB vs CRIS 37KB vs APS 44KB）。
- **CRIS = 0 stagger 階梯** — 沒實現 Timing 階梯原則（§4.2），這是 CRIS QA 只有 80% 的主因之一。
- **Landing 無 @keyframes** — 靜態展示頁，動畫非必要，但缺少進場效果。

---

## 3. Responsive Breakpoint 偏差

| 斷點 | APS | CRIS | 潤思 | Landing | Playbook 標準 |
|------|:---:|:----:|:----:|:-------:|:------------:|
| 平板 (1024px) | ✅ 1024 | ✅ 1024 | ✅ 1024 | ❌ (960) | **1024** |
| 手機 (768px) | ✅ 768 | ✅ 768 | ✅ 768 | ❌ (700) | **768** |
| 小手機 (480px) | ✅ 480 | ✅ 480 | ✅ 480 | ❌ (640/460) | **480** |

### 3.1 偏差分析

| 產品 | 偏差 | 影響 |
|------|------|------|
| **Landing Page** | 960/700/640/460 | 四斷點全偏離三套投影片的標準 1024/768/480。在 iPad Pro (1024px) 上會落入「無斷點」區間 |
| APS/CRIS/潤思 | 全對齊 | ✅ 三套投影片斷點一致 |

**建議**: Landing Page 對齊 1024/768/480 標準。如果要保留中間斷點（640/700），應在 1024/768 的基礎上追加，而非取代。

---

## 4. 字體 Weight 使用分佈

### 4.1 數量分佈

| Font-Weight | APS | CRIS | 潤思 | Landing |
|-------------|:---:|:----:|:----:|:-------:|
| 300 (Light) | 7 次 | 5 | 5 | 2 |
| 400 (Regular) | 4 次 | 0 | 0 | 0 |
| 500 (Medium) | 4 次 | 2 | 2 | 2 |
| 600 (SemiBold) | 13 次 | 6 | 6 | 2 |
| 700 (Bold) | 2 次 | 5 | 5 | 7 |
| 800 (ExtraBold) | 1 次 | 1 | 1 | 1 |
| 900 (Black) | 0 | 2 | 2 | 0 |

### 4.2 字體層級分析

| 要求 | APS | CRIS | 潤思 | Landing |
|------|:---:|:----:|:----:|:-------:|
| ≥3 font-weight 級數 | ✅ 6 | ✅ 6 | ✅ 6 | ✅ 5 |
| Display 用於封面/章節 | ✅ Playfair 800 | ✅ Playfair 900 | ✅ Playfair 900 | ✅ Playfair 700 |
| Heading 用於卡片標題 | ✅ Inter 600 | ❌ 無 Inter | ❌ 無 Inter | ❌ 無 Inter |
| Body 用於內文 | ✅ 300/400/500/600 | ❌ 無 400 | ❌ 無 400 | ❌ 無 400 |

### 4.3 關鍵發現

- **CRIS/潤思 缺 font-weight: 400** — 雖然 300 (Light) 可用於內文，但缺少 Regular 級別降低了可讀性選項。
- **APS 字體系統最完整**：6 級 weight + 獨立 body scale (`--body-1/2/3`) + heading scale (`--heading-1/2/3`)。
- **Landing: Bold 多於 Regular** — 7 次 700 vs 2 次 300，視覺層次偏重。

---

## 5. 綜合評分

| 維度 | APS | CRIS | 潤思 | Landing | 平均 |
|------|:---:|:----:|:----:|:-------:|:----:|
| Token 完整性 | 🅱️ 74 | 🅱️ 62 | 🅱️ 64 | — | 67 |
| Token 共用度 | ⚠️ 32/74 | ⚠️ 32/62 | ⚠️ 32/64 | — | 43% |
| 動畫合規 | ⚠️ 7 kf | ⚠️ 5 kf | ⚠️ 5 kf | — | — |
| Stagger 實作 | ✅ 10 | ❌ 0 | ⚠️ 539 過多 | ❌ 1 | — |
| 響應式對齊 | ✅ | ✅ | ✅ | ❌ | 75% |
| 字體層級 | ✅ 6級 | ✅ 6級 | ✅ 6級 | ✅ 5級 | ✅ |
| **一致性等級** | 🅱️ | 🅱️ | 🅱️ | ⚠️ | **B** |

### 5.1 優先修復建議

| 優先級 | 項目 | 影響範圍 | 難度 |
|--------|------|----------|:----:|
| P0 | CRIS 補 stagger 階梯 | CRIS QA 80%→85% | 低 |
| P0 | Landing 對齊 1024/768/480 斷點 | Landing 響應式 | 低 |
| P1 | APS 對齊 `--c-bg` / `--c-surface` token | APS 材質層次 | 中 |
| P1 | CRIS/潤思 補 font-weight: 400 | CRIS/潤思 可讀性 | 低 |
| P2 | 潤思 539 stagger → 降為 5 層 | 潤思 105KB → ~70KB | 中 |
| P2 | Token naming 統一 (`--ds-*` canonical) | 三套全部 | 高 |

---

## 6. 方法論

本報告基於以下工具產出：

| 工具 | 覆蓋範圍 |
|------|----------|
| `extract-tokens.py --json` | Token 缺口矩陣 (1) |
| `grep @keyframes / data-stagger / animation / transition` | 動畫模式 (2) |
| `grep @media` | 響應式斷點 (3) |
| `grep font-weight` | 字體分佈 (4) |

**可重現**: 所有數據可透過上述命令重新生成。

---

> *一致性審計報告 v1.0 · 2026-05-20 · Power Squad*