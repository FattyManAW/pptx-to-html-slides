# Gate 1 — HTML 簡報線 正式提案（Power Squad · Smart）

> 提交: Smart · 2026-05-22 12:23 CST
> 參照 Gate 0: `showcase/gate0-benchmark-html.md`（Christine PASS ✅ 11:51）
> 六項必備模板 v1.1

---

## 1. 具體交付物（5 項 · P0 only）

| # | 交付物 | 摘要 |
|:--:|------|------|
| 1 | 鍵盤導航全線補齊 | APS/CRIS/潤思 + OTD 系列 4 頁共 7 頁 keydown + tabindex |
| 2 | prefers-reduced-motion 全線 | 7 頁動畫 wrap `@media (prefers-reduced-motion: reduce)` |
| 3 | 三產品 Theme Toggle | APS 已有 → 移植 CRIS + 潤思，三產品選用 auto/light/dark |
| 4 | `?` 快速鍵面板 | shortcut cheat sheet overlay，全線可用 |
| 5 | Hero Number 潤思補齊 | 潤思 62p 缺少 hero number slide → 加 2 張 |

---

## 2. 參照標竿（≥2，含 URL + 元素）

| 標竿 | URL | 引用元素 |
|------|------|------|
| Linear | https://linear.app/features | Keyboard shortcut panel (`?`), hover micro-interaction |
| Apple HIG | https://developer.apple.com/design/human-interface-guidelines/ | Keyboard navigation, reduced motion, focus indicators |
| WCAG 2.1 AA | https://www.w3.org/TR/WCAG21/ | 2.1.1 Keyboard, 2.3.3 Animation from Interactions, 2.4.7 Focus Visible |
| Stripe Sessions | https://stripe.com/sessions | One number per screen, 60% whitespace, hero gradient |

---

## 3. 對應缺口（量化 before → after）

| # | Gap | Before | After | 量化 |
|:--:|------|------|------|:--:|
| 1 | 鍵盤導航 | 2/7 頁有 keydown（29%） | 7/7 頁（100%） | +5 頁 |
| 2 | reduced-motion | 2/7 頁（29%） | 7/7 頁（100%） | +5 頁 |
| 3 | Theme Toggle | 僅 APS | APS+CRIS+潤思 | +2 產品 |
| 4 | 快速鍵面板 | 0（`F`=全螢幕 only） | `?`→ 7 shortcut overlay | +10 快速鍵 |
| 5 | Hero Number 潤思 | 0 hero slide | +2 hero slides (100% OTD, -12.5% delay) | +2 |

---

## 4. 執行步驟（到 command）

### Step 1: 鍵盤導航 + reduced-motion（20m）

```bash
# 目標檔案: html/aps-ai-agent.html, html/cris-impacts-carbon.html,
#          html/runs-impacts-aps-partner.html,
#          html/otd-storyboard.html, html/christina-portfolio.html,
#          html/otd-dashboard-standalone.html, html/otd-domain-model.html
```

```css
/* 注入到每頁 </style> 前 */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

```js
// 注入到每頁 <script> 區塊
document.addEventListener('keydown', e => {
  if (e.key === 'ArrowRight' || e.key === ' ') next();
  if (e.key === 'ArrowLeft') prev();
  if (e.key === 'Home') go(0);
  if (e.key === 'End') go(total-1);
  if (e.key === '?' || (e.key === '/' && e.shiftKey)) toggleShortcuts();
});
```

### Step 2: Theme Toggle 移植（15m）

```css
/* 從 APS 提取 theme toggle CSS → CRIS + 潤思 */
[data-theme="light"] { /* light color scheme */ }
```

```js
// 三產品統一 ThemeToggle 三段式
function toggleTheme() {
  const themes = ['auto','light','dark'];
  const next = themes[(themes.indexOf(current)+1)%3];
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
}
```

### Step 3: `?` 快速鍵面板（10m）

```html
<!-- overlay HTML，注入到 </body> 前 -->
<div class="shortcuts-panel" id="shortcuts" style="display:none">
  <div class="shortcuts-content">
    <h3>快速鍵</h3>
    <table>
      <tr><td><kbd>←</kbd> <kbd>→</kbd></td><td>切換投影片</td></tr>
      <tr><td><kbd>Home</kbd> <kbd>End</kbd></td><td>第一/最後頁</td></tr>
      <tr><td><kbd>F</kbd></td><td>全螢幕</td></tr>
      <tr><td><kbd>ESC</kbd></td><td>鳥瞰模式</td></tr>
      <tr><td><kbd>?</kbd></td><td>此面板</td></tr>
      <tr><td>← → 滑動</td><td>觸控換頁</td></tr>
    </table>
  </div>
</div>
```

### Step 4: 潤思 Hero Number（10m）

```html
<!-- 插入潤思 runs-impacts-aps-partner.html → 兩張 hero slides -->
<div class="slide hero-slide">
  <div class="slide-inner" style="/* centering */">
    <p class="hero-number">100<small>%</small></p>
    <p class="hero-label">OTD 準時達交率 — 精準排程驅動零延遲交付</p>
  </div>
</div>
```

### Step 5: sync → showcase → push → deploy（5m）

```bash
cp html/aps-ai-agent.html showcase/
cp html/cris-impacts-carbon.html showcase/
cp html/runs-impacts-aps-partner.html showcase/
git add showcase/ && git commit -m "feat(gate3): P0 — a11y + theme + shortcuts + hero"
git push origin main
# CI auto-deploy → GH Pages
```

---

## 5. 預估時間

| # | 步驟 | 估時 | Buffer |
|:--:|------|:--:|:--:|
| 1 | 鍵盤導航 + reduced-motion | 20m | +5m |
| 2 | Theme Toggle 移植 | 15m | +5m |
| 3 | `?` 快速鍵面板 | 10m | +5m |
| 4 | 潤思 Hero Number | 10m | +5m |
| 5 | sync → push → deploy | 5m | +5m |
| **合計** | | **60m** | **85m** |

---

## 6. 驗收標準（7 AC）

| # | AC | 如何驗證 |
|:--:|------|------|
| 1 | 7/7 頁有 keydown 事件 | `grep -c 'keydown' html/*.html` = 7 |
| 2 | 7/7 頁有 prefers-reduced-motion | `grep -c 'prefers-reduced-motion' html/*.html` = 7 |
| 3 | CRIS + 潤思有 ThemeToggle | `grep -c 'data-theme' html/cris*.html html/runs*.html` ≥ 2 |
| 4 | 三產品 `?` 快速鍵 | `grep -c 'shortcuts-panel' html/{aps,cris,runs}*.html` = 3 |
| 5 | 潤思 hero-slide ≥ 2 | `grep -c 'hero-slide' html/runs*.html` ≥ 2 |
| 6 | GH Pages 三產品 200 | `curl -sI <URL> | head -1` |
| 7 | QA 零 regression | `run_qa.py --ci` PASS |

---

## 簽核

| Gate | 審核人 | 狀態 |
|:--:|------|:--:|
| Gate 0 | Christine | ✅ PASS |
| Gate 1 | Christine + Commander-D | ⏳ 待審 |
| Gate 2 | Allen | 🔒 |
| Gate 3 | Smart | 🔒 |
| Gate 4 | Christine + Commander-D | 🔒 |

