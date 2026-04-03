# Apple Glass UI Theme — Dark Mode
> The dark counterpart to `apple_glass_theme.md`. Same frosted-glass design language, same component API — tuned for dark backgrounds.  
> Drop the CSS into any HTML file alongside the light theme and toggle via `data-theme="dark"` on `<html>`. For Streamlit, copy the `[theme]` block into `.streamlit/config.toml`.

---

## 1. Design Tokens (CSS Variables)

```css
[data-theme="dark"] {
  /* Backgrounds */
  --bg:           #111318;                      /* page background */
  --glass:        rgba(255,255,255,0.055);       /* default glass fill */
  --glass-strong: rgba(255,255,255,0.095);       /* elevated glass fill */
  --glass-border: rgba(255,255,255,0.11);        /* glass border */

  /* Shadows */
  --shadow:    0 8px 40px rgba(0,0,8,0.55), 0 1px 4px rgba(0,0,0,0.35);
  --shadow-lg: 0 18px 60px rgba(0,0,8,0.70), 0 2px 8px rgba(0,0,0,0.45);

  /* Typography */
  --text:   #eef0f8;   /* primary text */
  --text-2: #9aa0bc;   /* secondary text */
  --text-3: #525870;   /* tertiary / placeholder */

  /* Accent palette — slightly lifted for dark backgrounds */
  --blue:   #4d8ef7;
  --indigo: #7b79e8;
  --teal:   #3dcde8;
  --green:  #3dd471;
  --orange: #f5b731;
  --red:    #f05252;

  /* Structural */
  --sep:    rgba(200,210,240,0.08);   /* divider / separator */
  --r:      18px;
  --r-sm:   12px;

  /* Font — unchanged */
  --font: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}
```

**Google Fonts import** (add to `<head>` — same as light theme):
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400&display=swap" rel="stylesheet">
```

> **Token philosophy:** glass fills use white-on-dark at very low opacity (0.05–0.10) to simulate frosted depth. Borders are kept subtle at 0.11 opacity. Accents are 15–25% lighter than their light-mode counterparts to maintain contrast ratios.

---

## 2. Animated Mesh Background

Same structure as light theme — swap gradient colours for richer, deeper jewel tones.

```css
[data-theme="dark"] #bg {
  background:
    radial-gradient(ellipse 1000px 800px at 10% 5%,  rgba(60,110,255,0.18) 0%, transparent 65%),
    radial-gradient(ellipse  700px 600px at 90% 90%, rgba(100,90,230,0.16) 0%, transparent 60%),
    radial-gradient(ellipse  600px 500px at 85% 10%, rgba(42,185,212,0.12) 0%, transparent 55%),
    radial-gradient(ellipse  500px 400px at 15% 90%, rgba(48,196,100,0.10) 0%, transparent 55%),
    linear-gradient(160deg, #111318 0%, #131720 50%, #10131c 100%);
  animation: breatheDark 22s ease-in-out infinite alternate;
}

@keyframes breatheDark {
  0%   { filter: hue-rotate(0deg)  brightness(1);    }
  50%  { filter: hue-rotate(8deg)  brightness(1.04); }
  100% { filter: hue-rotate(-6deg) brightness(0.97); }
}
```

---

## 3. Glass Surface Classes

```css
[data-theme="dark"] .glass {
  background: var(--glass);
  backdrop-filter: blur(28px) saturate(1.4);
  -webkit-backdrop-filter: blur(28px) saturate(1.4);
  border: 1px solid var(--glass-border);
  border-radius: var(--r);
  box-shadow: var(--shadow);
}

[data-theme="dark"] .glass-strong {
  background: var(--glass-strong);
  backdrop-filter: blur(40px) saturate(1.6);
  -webkit-backdrop-filter: blur(40px) saturate(1.6);
  border: 1px solid var(--glass-border);
  border-radius: var(--r);
  box-shadow: var(--shadow);
}
```

---

## 4. Typography Scale

Typography classes are **unchanged** — they inherit `--text`, `--text-2`, `--text-3` from the token block, so they automatically adapt in dark mode. No extra overrides needed.

```css
/* These already work in both themes via CSS variables */
.eyebrow  { color: var(--blue); }
.title    { color: var(--text); }
.subtitle { color: var(--text-2); }
.body-text{ color: var(--text-2); }
.caption  { color: var(--text-3); }
```

### Presentation / Distance-Readable Scale

Same clamp values as light theme — copy from `apple_glass_theme.md §4 ¶Presentation`. No dark-mode overrides needed.

---

## 5. Separator

```css
[data-theme="dark"] .sep {
  background: var(--sep);   /* rgba(200,210,240,0.08) */
}
```

---

## 6. Pills / Badges

Fill opacities are bumped slightly so pills are legible against dark glass.

```css
[data-theme="dark"] .p-blue   { background: rgba(77,142,247,0.18);  color: var(--blue);   }
[data-theme="dark"] .p-indigo { background: rgba(123,121,232,0.18); color: var(--indigo); }
[data-theme="dark"] .p-teal   { background: rgba(61,205,232,0.18);  color: var(--teal);   }
[data-theme="dark"] .p-green  { background: rgba(61,212,113,0.18);  color: var(--green);  }
[data-theme="dark"] .p-orange { background: rgba(245,183,49,0.18);  color: var(--orange); }
[data-theme="dark"] .p-red    { background: rgba(240,82,82,0.18);   color: var(--red);    }
```

---

## 7. Card

```css
[data-theme="dark"] .card:hover {
  box-shadow: 0 16px 56px rgba(0,0,0,0.65), 0 2px 10px rgba(0,0,0,0.45);
}

[data-theme="dark"] .card-formula {
  background: rgba(77,142,247,0.12);
  border-color: rgba(77,142,247,0.20);
}
```

---

## 8. Grid Layouts

No dark-mode overrides needed — grids are structural only.

---

## 9. Quote / Callout Block

```css
[data-theme="dark"] .callout {
  background: rgba(77,142,247,0.10);
  border-left-color: var(--blue);
  color: var(--text-2);
}
[data-theme="dark"] .callout strong { color: var(--blue); }
```

---

## 10–17. Component Overrides

Most components inherit automatically via CSS variables. Only elements with **hardcoded light colours** need explicit dark-mode rules:

```css
/* Frosted Nav Bar */
[data-theme="dark"] #nav {
  background: rgba(17,19,24,0.82);
  border-top-color: rgba(255,255,255,0.08);
}

/* Sidebar Navigation */
[data-theme="dark"] #sidebar {
  background: rgba(17,19,24,0.92);
  border-right-color: rgba(255,255,255,0.08);
}
[data-theme="dark"] .sitem:hover      { background: rgba(77,142,247,0.10); }
[data-theme="dark"] .sitem.active     { background: rgba(77,142,247,0.18); border-color: rgba(77,142,247,0.28); }
[data-theme="dark"] .sitem-num        { background: rgba(200,210,240,0.10); }
[data-theme="dark"] .sitem.active .sitem-num { background: var(--blue); }

/* Progress Bar — unchanged, already uses CSS vars */

/* Metric toggle buttons (chart slide) */
[data-theme="dark"] .mtog-btn:not(.active) {
  color: var(--text-2);
  border-color: rgba(200,210,240,0.15);
}
[data-theme="dark"] .mtog-btn:not(.active):hover {
  border-color: var(--blue); color: var(--blue);
}

/* Code blocks */
[data-theme="dark"] .code-block {
  background: rgba(8,10,16,0.92);
  border-color: rgba(255,255,255,0.07);
}

/* Loop step dividers */
[data-theme="dark"] .loop-step { border-right-color: var(--sep); }
```

---

## 18. Theme Toggle — Smooth Transition

Add this block **once** to your base CSS. It makes every token-driven property animate smoothly when `data-theme` changes.

```css
/* ── Smooth light ↔ dark transition ────────────────────────────── */
*, *::before, *::after {
  transition:
    background-color  0.35s cubic-bezier(.4,0,.2,1),
    background        0.35s cubic-bezier(.4,0,.2,1),
    border-color      0.35s cubic-bezier(.4,0,.2,1),
    color             0.25s cubic-bezier(.4,0,.2,1),
    box-shadow        0.35s cubic-bezier(.4,0,.2,1),
    backdrop-filter   0.35s cubic-bezier(.4,0,.2,1);
}

/* Exempt elements where transitions cause jank */
canvas, img, video, svg { transition: none !important; }
```

> **Note:** Place this block *before* component styles so it can be selectively overridden. The `canvas` exclusion prevents Chart.js animations from fighting the theme transition.

### Toggle Button HTML

```html
<button id="theme-toggle" class="glass" aria-label="Toggle theme"
  style="position:fixed;top:16px;right:16px;z-index:300;
         width:40px;height:40px;border-radius:50%;border:none;
         cursor:pointer;font-size:18px;display:flex;align-items:center;justify-content:center;">
  🌙
</button>
```

### Toggle JavaScript

```js
const root   = document.documentElement;
const btn    = document.getElementById('theme-toggle');
const stored = localStorage.getItem('theme') || 'light';

// Apply on load
root.setAttribute('data-theme', stored);
btn.textContent = stored === 'dark' ? '☀️' : '🌙';

btn.addEventListener('click', () => {
  const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  root.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
  btn.textContent = next === 'dark' ? '☀️' : '🌙';
});

// Honour OS preference on first visit
if (!localStorage.getItem('theme')) {
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  if (prefersDark) {
    root.setAttribute('data-theme', 'dark');
    btn.textContent = '☀️';
  }
}
```

---

## 19. Streamlit Dark Theme

Copy this block into `.streamlit/config.toml`:

```toml
[theme]
base                   = "dark"
primaryColor           = "#4d8ef7"
backgroundColor        = "#111318"
secondaryBackgroundColor = "#1a1f2c"
textColor              = "#eef0f8"
font                   = "sans serif"
```

**Streamlit custom CSS** (inject via `st.markdown` with `unsafe_allow_html=True`):

```python
import streamlit as st

st.markdown("""
<style>
/* Glass card effect */
.stApp > section > div[data-testid="stVerticalBlock"] > div {
  background: rgba(255,255,255,0.06);
  backdrop-filter: blur(24px) saturate(1.4);
  border: 1px solid rgba(255,255,255,0.11);
  border-radius: 18px;
  box-shadow: 0 8px 40px rgba(0,0,8,0.55);
  padding: 1.5rem;
  margin-bottom: 1rem;
}

/* Accent buttons */
.stButton > button {
  background: rgba(77,142,247,0.15);
  color: #4d8ef7;
  border: 1.5px solid rgba(77,142,247,0.30);
  border-radius: 100px;
  font-weight: 600;
  transition: background 0.2s, box-shadow 0.2s;
}
.stButton > button:hover {
  background: rgba(77,142,247,0.28);
  box-shadow: 0 4px 20px rgba(77,142,247,0.25);
}

/* Metric cards */
[data-testid="metric-container"] {
  background: rgba(255,255,255,0.07);
  border: 1px solid rgba(255,255,255,0.11);
  border-radius: 14px;
  padding: 1rem 1.2rem;
}

/* Sidebar */
[data-testid="stSidebar"] {
  background: rgba(17,19,24,0.92);
  border-right: 1px solid rgba(255,255,255,0.08);
}

/* Divider */
hr { border-color: rgba(200,210,240,0.08); }
</style>
""", unsafe_allow_html=True)
```

---

## 20. Complete Dual-Theme Boilerplate

Starter HTML with both themes wired and toggle button included.

```html
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Your Title</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400&display=swap" rel="stylesheet">
<style>
  /* ── Light tokens (apple_glass_theme.md §1) ── */
  :root {
    --bg: #eef2f8;
    --glass: rgba(255,255,255,0.58);
    --glass-strong: rgba(255,255,255,0.80);
    --glass-border: rgba(255,255,255,0.88);
    --shadow:    0 8px 40px rgba(0,0,0,0.09), 0 1px 4px rgba(0,0,0,0.05);
    --shadow-lg: 0 18px 60px rgba(0,0,0,0.13), 0 2px 8px rgba(0,0,0,0.06);
    --text: #17191f; --text-2: #525870; --text-3: #9099b2;
    --blue: #1a6cf5; --indigo: #5856d6; --teal: #2ab9d4;
    --green: #30c464; --orange: #f09000; --red: #e03030;
    --sep: rgba(50,55,80,0.09);
    --r: 18px; --r-sm: 12px;
    --font: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  }

  /* ── Dark tokens (apple_glass_dark_theme.md §1) ── */
  [data-theme="dark"] {
    --bg: #111318;
    --glass: rgba(255,255,255,0.055);
    --glass-strong: rgba(255,255,255,0.095);
    --glass-border: rgba(255,255,255,0.11);
    --shadow:    0 8px 40px rgba(0,0,8,0.55), 0 1px 4px rgba(0,0,0,0.35);
    --shadow-lg: 0 18px 60px rgba(0,0,8,0.70), 0 2px 8px rgba(0,0,0,0.45);
    --text: #eef0f8; --text-2: #9aa0bc; --text-3: #525870;
    --blue: #4d8ef7; --indigo: #7b79e8; --teal: #3dcde8;
    --green: #3dd471; --orange: #f5b731; --red: #f05252;
    --sep: rgba(200,210,240,0.08);
  }

  /* ── Smooth transition ── */
  *, *::before, *::after {
    transition: background-color 0.35s cubic-bezier(.4,0,.2,1),
                background       0.35s cubic-bezier(.4,0,.2,1),
                border-color     0.35s cubic-bezier(.4,0,.2,1),
                color            0.25s cubic-bezier(.4,0,.2,1),
                box-shadow       0.35s cubic-bezier(.4,0,.2,1);
  }
  canvas, img, video, svg { transition: none !important; }

  /* ── Base ── */
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { min-height: 100%; font-family: var(--font); background: var(--bg); color: var(--text); -webkit-font-smoothing: antialiased; }

  /* ── paste remaining component CSS from both theme files here ── */
</style>
</head>
<body>

<!-- Theme toggle -->
<button id="theme-toggle" class="glass"
  style="position:fixed;top:16px;right:16px;z-index:300;
         width:40px;height:40px;border-radius:50%;border:none;
         cursor:pointer;font-size:18px;display:flex;align-items:center;justify-content:center;">
  🌙
</button>

<div id="bg"></div>

<main style="position:relative;z-index:1;max-width:1100px;margin:0 auto;padding:3rem 2rem;">
  <!-- your content here -->
</main>

<script>
const root = document.documentElement;
const btn  = document.getElementById('theme-toggle');

function applyTheme(t) {
  root.setAttribute('data-theme', t);
  btn.textContent = t === 'dark' ? '☀️' : '🌙';
  localStorage.setItem('theme', t);
}

const saved = localStorage.getItem('theme')
  || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
applyTheme(saved);

btn.addEventListener('click', () =>
  applyTheme(root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark')
);
</script>
</body>
</html>
```

---

## Quick Reference — Dark Token Overrides

| Token | Light | Dark |
|---|---|---|
| `--bg` | `#eef2f8` | `#111318` |
| `--glass` | `rgba(255,255,255,0.58)` | `rgba(255,255,255,0.055)` |
| `--glass-strong` | `rgba(255,255,255,0.80)` | `rgba(255,255,255,0.095)` |
| `--glass-border` | `rgba(255,255,255,0.88)` | `rgba(255,255,255,0.11)` |
| `--text` | `#17191f` | `#eef0f8` |
| `--text-2` | `#525870` | `#9aa0bc` |
| `--text-3` | `#9099b2` | `#525870` |
| `--blue` | `#1a6cf5` | `#4d8ef7` |
| `--indigo` | `#5856d6` | `#7b79e8` |
| `--teal` | `#2ab9d4` | `#3dcde8` |
| `--green` | `#30c464` | `#3dd471` |
| `--orange` | `#f09000` | `#f5b731` |
| `--red` | `#e03030` | `#f05252` |
| `--sep` | `rgba(50,55,80,0.09)` | `rgba(200,210,240,0.08)` |

> **Rule:** in dark mode, glass opacity drops dramatically (0.58 → 0.055) while border opacity also drops (0.88 → 0.11). Accents shift ~15% lighter. Shadows shift to near-black with higher opacity.
