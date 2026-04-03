# Apple Glass UI Theme
> A frosted-glass, light-mode design system inspired by macOS/iOS aesthetics.  
> Drop the CSS block into any HTML file and use the component classes directly.

---

## 1. Design Tokens (CSS Variables)

```css
:root {
  /* Backgrounds */
  --bg:           #eef2f8;          /* page background */
  --glass:        rgba(255,255,255,0.58);   /* default glass fill */
  --glass-strong: rgba(255,255,255,0.80);   /* elevated glass fill */
  --glass-border: rgba(255,255,255,0.88);   /* glass border */

  /* Shadows */
  --shadow:    0 8px 40px rgba(0,0,0,0.09), 0 1px 4px rgba(0,0,0,0.05);
  --shadow-lg: 0 18px 60px rgba(0,0,0,0.13), 0 2px 8px rgba(0,0,0,0.06);

  /* Typography */
  --text:   #17191f;   /* primary text */
  --text-2: #525870;   /* secondary text */
  --text-3: #9099b2;   /* tertiary / placeholder */

  /* Accent palette */
  --blue:   #1a6cf5;
  --indigo: #5856d6;
  --teal:   #2ab9d4;
  --green:  #30c464;
  --orange: #f09000;
  --red:    #e03030;

  /* Structural */
  --sep:    rgba(50,55,80,0.09);    /* divider / separator */
  --r:      18px;                   /* border-radius large */
  --r-sm:   12px;                   /* border-radius small */

  /* Font */
  --font: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}
```

**Google Fonts import** (add to `<head>`):
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400&display=swap" rel="stylesheet">
```

---

## 2. Animated Mesh Background

A slow-breathing radial gradient mesh. Apply to a `position:fixed` full-screen element.

```css
#bg {
  position: fixed; inset: 0; z-index: 0;
  background:
    radial-gradient(ellipse 1000px 800px at 10% 5%,  rgba(80,140,255,0.16) 0%, transparent 65%),
    radial-gradient(ellipse  700px 600px at 90% 90%, rgba(88,86,214,0.13) 0%, transparent 60%),
    radial-gradient(ellipse  600px 500px at 85% 10%, rgba(42,185,212,0.10) 0%, transparent 55%),
    radial-gradient(ellipse  500px 400px at 15% 90%, rgba(48,196,100,0.09) 0%, transparent 55%),
    linear-gradient(160deg, #e8eef9 0%, #eceff9 50%, #e5ebf7 100%);
  animation: breathe 20s ease-in-out infinite alternate;
}

@keyframes breathe {
  0%   { filter: hue-rotate(0deg)  brightness(1);    }
  50%  { filter: hue-rotate(7deg)  brightness(1.015);}
  100% { filter: hue-rotate(-5deg) brightness(0.99); }
}
```

```html
<div id="bg"></div>
```

> **Tip:** Swap the radial-gradient positions (`10% 5%`, `90% 90%` etc.) to shift where the colour blooms appear.

---

## 3. Glass Surface Classes

Two tiers — use `.glass` for default cards and `.glass-strong` for elevated / hero elements.

```css
.glass {
  background: var(--glass);
  backdrop-filter: blur(26px) saturate(1.6);
  -webkit-backdrop-filter: blur(26px) saturate(1.6);
  border: 1px solid var(--glass-border);
  border-radius: var(--r);
  box-shadow: var(--shadow);
}

.glass-strong {
  background: var(--glass-strong);
  backdrop-filter: blur(38px) saturate(1.8);
  -webkit-backdrop-filter: blur(38px) saturate(1.8);
  border: 1px solid var(--glass-border);
  border-radius: var(--r);
  box-shadow: var(--shadow);
}
```

```html
<!-- Default glass card -->
<div class="glass" style="padding: 1.5rem;">
  Content here
</div>

<!-- Elevated glass card -->
<div class="glass-strong" style="padding: 1.5rem;">
  Hero or modal content
</div>
```

---

## 4. Typography Scale

```css
/* Eyebrow label — used above headings */
.eyebrow {
  font-size: .68rem; font-weight: 600;
  letter-spacing: .16em; text-transform: uppercase;
  color: var(--blue); margin-bottom: .75rem;
}

/* Page / section title */
.title {
  font-size: clamp(1.9rem, 3.3vw, 2.7rem);
  font-weight: 700; letter-spacing: -.028em;
  color: var(--text); line-height: 1.08;
}

/* Hero title (large format) */
.hero-title {
  font-size: clamp(2.8rem, 5.8vw, 4.6rem);
  font-weight: 700; letter-spacing: -.04em;
  color: var(--text); line-height: 1.0;
}

/* Subtitle / lead */
.subtitle {
  font-size: .92rem; font-weight: 400;
  color: var(--text-2); line-height: 1.65;
  margin-top: .55rem; max-width: 54ch;
}

/* Body text */
.body-text {
  font-size: .84rem; color: var(--text-2); line-height: 1.65;
}

/* Tertiary / caption */
.caption {
  font-size: .7rem; color: var(--text-3);
  letter-spacing: .04em;
}

/* Monospace (formulas, code) */
.mono {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: .8rem;
}
```

```html
<div class="eyebrow">Section Label</div>
<h1 class="title">Main Heading</h1>
<p class="subtitle">A supporting description that gives context.</p>
```

### Presentation / Distance-Readable Scale

Use these overrides when building slide decks or content that will be viewed from a distance (projector, large monitor, seminar room). The clamp ranges ensure legibility at all viewport sizes.

```css
/* Presentation typography — readable from ~3–5 metres */
h1   { font-size: clamp(34px, 4.5vw, 56px); font-weight: 800; line-height: 1.12; }
h2   { font-size: clamp(26px, 3.5vw, 44px); font-weight: 700; line-height: 1.2;  }
h3   { font-size: clamp(20px, 2.5vw, 28px); font-weight: 600; }
p    { font-size: clamp(16px, 1.7vw, 20px); line-height: 1.7; }
.lead{ font-size: clamp(18px, 1.9vw, 24px); line-height: 1.7; }

.slide-label { font-size: 13px;  } /* eyebrow above heading */
.pill        { font-size: 14px;  }
.stat-label  { font-size: 16px;  }
.stat-sub    { font-size: 13px;  }

/* Card-level body copy */
.card-title  { font-size: 17px;  }
.card-body   { font-size: 15px;  }

/* List items inside cards */
.list-item   { font-size: 15px;  }

/* Code / JSON blocks */
.code-block  { font-size: 14px;  }
```

> **Rule of thumb:** no body text below `15px` in a presentation context. Prefer `clamp()` so the scale degrades gracefully on laptops used as a mirror display.

---

## 5. Separator

```css
.sep {
  height: 1px;
  background: var(--sep);
  margin: 1.1rem 0;
}
```

```html
<div class="sep"></div>
```

---

## 6. Pills / Badges

Colour variants for each accent. Mix and match.

```css
.pill {
  display: inline-flex; align-items: center; gap: .3rem;
  padding: .26rem .7rem; border-radius: 100px;
  font-size: .7rem; font-weight: 500;
}

/* Colour variants */
.p-blue   { background: rgba(26,108,245,0.10); color: var(--blue);   }
.p-indigo { background: rgba(88,86,214,0.10);  color: var(--indigo); }
.p-teal   { background: rgba(42,185,212,0.11); color: var(--teal);   }
.p-green  { background: rgba(48,196,100,0.11); color: var(--green);  }
.p-orange { background: rgba(240,144,0,0.11);  color: var(--orange); }
.p-red    { background: rgba(224,48,48,0.10);  color: var(--red);    }
```

```html
<span class="pill p-blue">Label</span>
<span class="pill p-indigo">Label</span>
<span class="pill p-teal">Label</span>
<span class="pill p-green">Label</span>
<span class="pill p-orange">Label</span>
<span class="pill p-red">Label</span>
```

---

## 7. Card

Standard content card with hover lift. Nest inside `.glass` or `.glass-strong`.

```css
.card {
  padding: 1.25rem 1.4rem;
  transition: transform .22s ease, box-shadow .22s ease;
}
.card:hover {
  transform: translateY(-3px);
  box-shadow: 0 14px 50px rgba(0,0,0,0.13), 0 2px 8px rgba(0,0,0,0.08);
}

.card-eyebrow {
  font-size: .65rem; font-weight: 600;
  letter-spacing: .13em; text-transform: uppercase;
  margin-bottom: .45rem;
}
.card-title {
  font-size: .98rem; font-weight: 600;
  color: var(--text); margin-bottom: .35rem;
}
.card-body {
  font-size: .81rem; color: var(--text-2); line-height: 1.65;
}

/* Optional: formula / code block inside card */
.card-formula {
  display: inline-block; margin-top: .65rem;
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: .76rem; padding: .3rem .65rem;
  background: rgba(26,108,245,0.07);
  border: 1px solid rgba(26,108,245,0.14);
  border-radius: 7px; color: var(--blue);
}
```

```html
<div class="card glass">
  <div class="card-eyebrow" style="color: var(--blue)">Category</div>
  <div class="card-title">Card Title</div>
  <div class="card-body">Supporting description goes here with enough detail to be useful.</div>
  <div class="card-formula">formula or code</div>
</div>
```

---

## 8. Grid Layouts

```css
.grid-2 { display: grid; grid-template-columns: 1fr 1fr;       gap: 1rem; }
.grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr;   gap: 1rem; }
.grid-4 { display: grid; grid-template-columns: repeat(4,1fr); gap: 1rem; }
```

```html
<div class="grid-3">
  <div class="card glass"> … </div>
  <div class="card glass"> … </div>
  <div class="card glass"> … </div>
</div>
```

---

## 9. Quote / Callout Block

Left-bordered callout. Swap `var(--blue)` for any accent colour.

```css
.callout {
  padding: .85rem 1.1rem;
  background: rgba(26,108,245,0.06);
  border-radius: var(--r-sm);
  border-left: 3px solid var(--blue);
  font-size: .82rem; color: var(--text-2);
  font-style: italic; line-height: 1.65;
}
.callout strong { font-style: normal; color: var(--blue); font-weight: 600; }
```

```html
<!-- Blue (default) -->
<div class="callout">
  A key insight or quotable line. <strong>Emphasis works here.</strong>
</div>

<!-- Orange warning variant -->
<div class="callout" style="background:rgba(240,144,0,0.07); border-left-color:var(--orange);">
  <strong style="color:var(--orange)">Watch out:</strong> something to be cautious about.
</div>

<!-- Green success/transition variant -->
<div class="callout" style="background:rgba(48,196,100,0.07); border-left-color:var(--green);">
  <strong style="color:var(--green)">Next:</strong> a transition or positive note.
</div>
```

---

## 10. Horizontal Step / Loop Row

Multi-step process displayed side-by-side inside a glass panel.

```css
.loop-row {
  display: flex; align-items: stretch; gap: 0;
}

.loop-step {
  flex: 1; padding: 1rem 1.2rem;
  display: flex; flex-direction: column; gap: .25rem;
  border-right: 1px solid var(--sep);
}
.loop-step:last-child { border-right: none; }

.ls-num     { font-size: .6rem; font-weight: 600; letter-spacing: .1em; color: var(--text-3); }
.ls-name    { font-size: .9rem; font-weight: 600; color: var(--text); }
.ls-body    { font-size: .76rem; color: var(--text-2); line-height: 1.6; margin-top: .1rem; }
.ls-formula {
  margin-top: .4rem;
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: .72rem; padding: .25rem .55rem;
  border-radius: 7px; display: inline-block;
}
```

```html
<div class="glass" style="border-radius: var(--r); overflow: hidden;">
  <div class="loop-row">
    <div class="loop-step">
      <span class="ls-num">01</span>
      <span class="ls-name">Step One</span>
      <p class="ls-body">Brief description of what happens here.</p>
      <span class="ls-formula" style="background:rgba(26,108,245,0.07); color:var(--blue)">expr = value</span>
    </div>
    <div class="loop-step">
      <span class="ls-num">02</span>
      <span class="ls-name">Step Two</span>
      <p class="ls-body">Brief description of what happens here.</p>
      <span class="ls-formula" style="background:rgba(88,86,214,0.08); color:var(--indigo)">expr = value</span>
    </div>
    <div class="loop-step">
      <span class="ls-num">03</span>
      <span class="ls-name">Step Three</span>
      <p class="ls-body">Brief description of what happens here.</p>
      <span class="ls-formula" style="background:rgba(48,196,100,0.08); color:var(--green)">expr = value</span>
    </div>
  </div>
</div>
```

---

## 11. Pipeline / Icon Steps Grid

Card grid with emoji icons and numbered steps — good for workflows.

```css
.pipeline-steps {
  display: grid; grid-template-columns: repeat(6,1fr); gap: .7rem;
}

/* Reduce columns on narrower content */
/* For 4 steps: grid-template-columns: repeat(4,1fr) */

.ps {
  padding: 1.1rem 1rem;
  display: flex; flex-direction: column; gap: .3rem;
  transition: transform .2s;
}
.ps:hover { transform: translateY(-4px); }

.ps-icon {
  width: 28px; height: 28px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: .85rem; margin-bottom: .2rem;
}
.ps-num  { font-size: .6rem; font-weight: 600; letter-spacing: .1em; text-transform: uppercase; color: var(--text-3); }
.ps-name { font-size: .88rem; font-weight: 600; color: var(--text); line-height: 1.25; }
.ps-desc { font-size: .71rem; color: var(--text-2); line-height: 1.5; margin-top: .15rem; }
```

```html
<div class="pipeline-steps">
  <div class="ps glass">
    <div class="ps-icon" style="background:rgba(26,108,245,0.10)">🎯</div>
    <div class="ps-num">Step 01</div>
    <div class="ps-name">Define</div>
    <div class="ps-desc">Short description of this step in the process.</div>
  </div>
  <div class="ps glass">
    <div class="ps-icon" style="background:rgba(88,86,214,0.10)">🗂</div>
    <div class="ps-num">Step 02</div>
    <div class="ps-name">Collect</div>
    <div class="ps-desc">Short description of this step in the process.</div>
  </div>
  <!-- repeat as needed -->
</div>
```

---

## 12. Frosted Nav Bar (Bottom-fixed)

```css
#nav {
  position: fixed; bottom: 0; left: 0; right: 0;
  display: flex; align-items: center; justify-content: center; gap: 1rem;
  padding: .85rem 0 1rem;
  z-index: 100;
  background: rgba(238,242,248,0.78);
  backdrop-filter: blur(20px) saturate(1.5);
  -webkit-backdrop-filter: blur(20px) saturate(1.5);
  border-top: 1px solid rgba(255,255,255,0.72);
}

.nav-btn {
  background: var(--glass-strong);
  border: 1px solid rgba(255,255,255,0.85);
  color: var(--blue);
  font-family: var(--font); font-size: .78rem; font-weight: 500;
  padding: .4rem 1.1rem; border-radius: 100px; cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.07);
  transition: background .18s, box-shadow .18s, transform .15s;
}
.nav-btn:hover {
  background: rgba(26,108,245,0.09);
  box-shadow: 0 4px 16px rgba(26,108,245,0.15);
  transform: scale(1.03);
}
.nav-btn:disabled { opacity: .28; pointer-events: none; }
```

```html
<div id="nav">
  <button class="nav-btn" id="bp">← Previous</button>
  <span style="font-size:.7rem; font-weight:500; color:var(--text-3);">1 of 5</span>
  <button class="nav-btn" id="bn">Next →</button>
</div>
```

---

## 13. Progress Bar (Top-fixed)

```css
#ptrack {
  position: fixed; top: 0; left: 0; right: 0;
  height: 2px;
  background: rgba(0,0,0,0.05);
  z-index: 200;
}
#pfill {
  height: 100%;
  background: linear-gradient(90deg, var(--blue), var(--indigo));
  transition: width .45s cubic-bezier(.4,0,.2,1);
  border-radius: 0 2px 2px 0;
}
```

```html
<div id="ptrack">
  <div id="pfill" style="width: 0%"></div>
</div>
```

Update via JS:
```js
document.getElementById('pfill').style.width = `${percent}%`;
```

---

## 14. Floating Orbs (Hero Decoration)

Layered radial blobs — position relative to a container with `position:relative`.

```css
.orb {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
}

/* Usage: stack 2–3 orbs of descending size */
.orb-outer {
  width: 280px; height: 280px;
  background: radial-gradient(circle,
    rgba(26,108,245,0.13) 0%,
    rgba(88,86,214,0.07) 45%,
    transparent 75%);
  animation: orbFloat 7s ease-in-out infinite alternate;
}
.orb-mid {
  width: 160px; height: 160px;
  background: radial-gradient(circle, rgba(42,185,212,0.15) 0%, transparent 70%);
  animation: orbFloat 5s ease-in-out infinite alternate-reverse;
}
.orb-core {
  width: 90px; height: 90px;
  background: rgba(255,255,255,0.55);
  backdrop-filter: blur(18px);
  border: 1px solid rgba(255,255,255,0.8);
  box-shadow: 0 8px 32px rgba(26,108,245,0.18);
}

@keyframes orbFloat {
  0%   { transform: translateY(-52%); }
  100% { transform: translateY(-48%); }
}
```

```html
<div style="position:relative; width:300px; height:300px;">
  <div class="orb orb-outer"  style="top:50%; right:0; transform:translateY(-50%)"></div>
  <div class="orb orb-mid"    style="top:50%; right:2rem; transform:translateY(-50%)"></div>
  <div class="orb orb-core"   style="top:50%; right:4rem; transform:translateY(-50%)"></div>
</div>
```

---

## 15. Slide Transition (Presentation Mode)

Smooth enter/exit for stacked full-screen panels.

```css
.slide {
  position: absolute; inset: 0;
  opacity: 0; pointer-events: none;
  transform: translateY(20px) scale(0.99);
  transition: opacity .5s cubic-bezier(.4,0,.2,1),
              transform .5s cubic-bezier(.4,0,.2,1);
}
.slide.active {
  opacity: 1; pointer-events: all;
  transform: translateY(0) scale(1);
}
.slide.exit {
  opacity: 0;
  transform: translateY(-18px) scale(1.005);
  transition: opacity .35s ease, transform .35s ease;
  pointer-events: none;
}
```

```js
function go(n) {
  if (n < 0 || n >= slides.length || busy) return;
  busy = true;
  const prev = cur;
  slides[prev].classList.remove('active');
  slides[prev].classList.add('exit');
  cur = n;
  slides[cur].classList.add('active');
  setTimeout(() => { slides[prev].classList.remove('exit'); busy = false; }, 420);
}
```

---

## 16. Two-Column Contrast Layout

Side-by-side panels — good for before/after, option A vs. B.

```css
.contrast-row {
  display: grid; grid-template-columns: 1fr 1fr; gap: 1.1rem;
}
.contrast-card {
  padding: 1.5rem 1.6rem;
  display: flex; flex-direction: column; gap: .6rem;
}
.cc-label { font-size: .65rem; font-weight: 600; letter-spacing: .14em; text-transform: uppercase; }
.cc-title { font-size: 1.1rem; font-weight: 700; color: var(--text); }
.cc-body  { font-size: .82rem; color: var(--text-2); line-height: 1.65; flex: 1; }
```

```html
<div class="contrast-row">
  <div class="contrast-card glass">
    <div class="cc-label" style="color: var(--text-3)">Before</div>
    <div class="cc-title">Old Approach</div>
    <div class="cc-body">Explanation of the original method or concept.</div>
  </div>
  <div class="contrast-card glass-strong">
    <div class="cc-label" style="color: var(--blue)">After</div>
    <div class="cc-title">New Approach</div>
    <div class="cc-body">Explanation of the improved method or concept.</div>
  </div>
</div>
```

---

## 17. Hover-Lift Interactive Chip

Clickable discussion chip with lift on hover.

```css
.q-chip {
  padding: .75rem 1.2rem;
  font-size: .78rem; color: var(--text-2);
  font-style: italic; cursor: pointer;
  text-align: center; line-height: 1.5;
  transition: transform .2s, box-shadow .2s, color .2s;
}
.q-chip:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  color: var(--blue);
}
```

```html
<div class="q-chip glass">A provocative question or discussion prompt here?</div>
```

---

## 18. Complete Page Boilerplate

Copy-paste starter with all foundational pieces wired up.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Your Title</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400&display=swap" rel="stylesheet">
<style>
  /* ── paste token block (Section 1) here ── */
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  html, body {
    width: 100%; min-height: 100%;
    font-family: var(--font);
    background: var(--bg);
    -webkit-font-smoothing: antialiased;
  }

  /* ── paste mesh background (Section 2) here ── */
  /* ── paste glass classes (Section 3) here ── */
  /* ── paste typography (Section 4) here ── */
  /* ── paste separator (Section 5) here ── */
  /* ── paste pills (Section 6) here ── */
  /* ── paste card (Section 7) here ── */
  /* ── paste grid layouts (Section 8) here ── */
  /* ── add any other components you need ── */
</style>
</head>
<body>

<div id="bg"></div>

<main style="position:relative; z-index:1; max-width:1100px; margin:0 auto; padding:3rem 2rem;">

  <!-- your content here -->
  <div class="eyebrow">Section Label</div>
  <h1 class="title">Page Title</h1>
  <p class="subtitle">A supporting description.</p>
  <div class="sep"></div>

  <div class="grid-3">
    <div class="card glass">
      <div class="card-eyebrow" style="color:var(--blue)">Category</div>
      <div class="card-title">Card One</div>
      <div class="card-body">Content here.</div>
    </div>
    <div class="card glass">
      <div class="card-eyebrow" style="color:var(--indigo)">Category</div>
      <div class="card-title">Card Two</div>
      <div class="card-body">Content here.</div>
    </div>
    <div class="card glass">
      <div class="card-eyebrow" style="color:var(--teal)">Category</div>
      <div class="card-title">Card Three</div>
      <div class="card-body">Content here.</div>
    </div>
  </div>

</main>

</body>
</html>
```

---

## 19. Sidebar Navigation (Presentation Mode)

Replaces the bottom dots/pill nav. Fixed left panel with grouped page-name menu — lets you jump to any slide non-linearly during a live presentation.

```css
#sidebar {
  position: fixed; top: 0; left: 0; bottom: 0; width: 220px; z-index: 100;
  display: flex; flex-direction: column;
  background: var(--glass-strong);
  backdrop-filter: blur(32px) saturate(200%);
  -webkit-backdrop-filter: blur(32px) saturate(200%);
  border-right: 1.5px solid var(--glass-border);
  box-shadow: 4px 0 32px rgba(80,100,160,0.13);
  padding: 0 0 16px;
  overflow-y: auto;
}
#sidebar-header {
  padding: 20px 18px 14px;
  border-bottom: 1px solid rgba(144,153,178,0.15);
  flex-shrink: 0;
}
#sidebar-title {
  font-size: 11px; font-weight: 700; letter-spacing: 2px;
  text-transform: uppercase; color: var(--blue); margin-bottom: 2px;
}
#sidebar-sub { font-size: 10px; color: var(--text-3); font-weight: 500; }

#sidebar-menu {
  flex: 1; display: flex; flex-direction: column; gap: 2px;
  padding: 10px 10px 0; list-style: none;
}

/* Section group label */
.sitem-section {
  font-size: 10px; font-weight: 700; letter-spacing: 1.5px;
  text-transform: uppercase; color: var(--text-3);
  padding: 12px 10px 4px; margin-top: 4px;
}

/* Individual menu item */
.sitem {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 10px; border-radius: 10px; cursor: pointer;
  transition: all 0.2s ease; border: 1px solid transparent;
}
.sitem:hover { background: rgba(26,108,245,0.07); border-color: rgba(26,108,245,0.12); }
.sitem.active { background: rgba(26,108,245,0.12); border-color: rgba(26,108,245,0.22); }

.sitem-num {
  width: 22px; height: 22px; border-radius: 6px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 10px; font-weight: 700;
  background: rgba(144,153,178,0.15); color: var(--text-3);
  transition: all 0.2s;
}
.sitem.active .sitem-num { background: var(--blue); color: #fff; }

.sitem-label {
  font-size: 12px; font-weight: 500; color: var(--text-2);
  line-height: 1.3; transition: color 0.2s;
}
.sitem.active .sitem-label { color: var(--blue); font-weight: 600; }
.sitem:hover  .sitem-label { color: var(--text); }

#sidebar-footer {
  padding: 12px 18px 0; border-top: 1px solid rgba(144,153,178,0.15);
  margin-top: 8px; flex-shrink: 0;
}
#sidebar-counter { font-size: 11px; color: var(--text-3); font-weight: 500; text-align: center; }

/* Offset deck so it doesn't sit under the sidebar */
#deck { position: fixed; left: 220px; width: calc(100vw - 220px); height: 100vh; }
```

```html
<nav id="sidebar">
  <div id="sidebar-header">
    <div id="sidebar-title">Event / Short Title</div>
    <div id="sidebar-sub">Track · Subtitle</div>
  </div>

  <ul id="sidebar-menu">
    <li class="sitem-section">Overview</li>
    <li class="sitem active" onclick="goTo(0)">
      <div class="sitem-num">1</div>
      <div class="sitem-label">Title</div>
    </li>
    <li class="sitem" onclick="goTo(1)">
      <div class="sitem-num">2</div>
      <div class="sitem-label">Slide Name</div>
    </li>

    <li class="sitem-section">Section Two</li>
    <li class="sitem" onclick="goTo(2)">
      <div class="sitem-num">3</div>
      <div class="sitem-label">Slide Name</div>
    </li>
    <!-- repeat as needed -->
  </ul>

  <div id="sidebar-footer">
    <div id="sidebar-counter">1 / N</div>
  </div>
</nav>
```

```js
const TOTAL = 13; // total slide count
let current = 0;
const slides    = document.querySelectorAll('.slide');
const sideItems = document.querySelectorAll('.sitem[onclick]');
const counterEl = document.getElementById('sidebar-counter');
const progressEl= document.getElementById('progress');

function goTo(n) {
  const prev = current;
  slides[prev].classList.remove('active');
  slides[prev].classList.add('exit-left');
  setTimeout(() => slides[prev].classList.remove('exit-left'), 500);

  current = Math.max(0, Math.min(n, TOTAL - 1));
  slides[current].classList.add('active');

  sideItems.forEach((item, i) => item.classList.toggle('active', i === current));
  sideItems[current].scrollIntoView({ block: 'nearest', behavior: 'smooth' });

  counterEl.textContent  = `${current + 1} / ${TOTAL}`;
  progressEl.style.width = `${((current + 1) / TOTAL) * 100}%`;
}

document.addEventListener('keydown', e => {
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown' || e.key === ' ')
    { e.preventDefault(); goTo(current + 1); }
  if (e.key === 'ArrowLeft'  || e.key === 'ArrowUp')
    { e.preventDefault(); goTo(current - 1); }
});

progressEl.style.width = `${(1/TOTAL)*100}%`;
```

> **Notes:**
> - Group slides under `<li class="sitem-section">` labels for semantic chunking.
> - The `.sitem[onclick]` selector counts only clickable items — section labels are automatically skipped.
> - Keyboard arrow navigation still works alongside the sidebar.
> - Remove the old `#nav` (dot/pill) block and `#counter` fixed element when switching to this pattern.

---

## Quick Reference

| Token | Value | Use for |
|---|---|---|
| `--blue` | `#1a6cf5` | Primary actions, links, eyebrows |
| `--indigo` | `#5856d6` | Secondary accent, slides |
| `--teal` | `#2ab9d4` | Process steps, info |
| `--green` | `#30c464` | Success, transitions |
| `--orange` | `#f09000` | Warnings, caution |
| `--red` | `#e03030` | Errors, critical |
| `--glass` | `rgba(255,255,255,0.58)` | Default card |
| `--glass-strong` | `rgba(255,255,255,0.80)` | Elevated / hero |
| `--r` | `18px` | Card radius |
| `--r-sm` | `12px` | Inner element radius |

| Component | Class(es) | Section |
|---|---|---|
| Background mesh | `#bg` | §2 |
| Glass card | `.glass` / `.glass-strong` | §3 |
| Eyebrow | `.eyebrow` | §4 |
| Heading | `.title` / `.hero-title` | §4 |
| Pill badge | `.pill .p-{color}` | §6 |
| Content card | `.card .glass` | §7 |
| Grid | `.grid-2/3/4` | §8 |
| Callout / quote | `.callout` | §9 |
| Step row | `.loop-row > .loop-step` | §10 |
| Pipeline grid | `.pipeline-steps > .ps` | §11 |
| Nav bar | `#nav > .nav-btn` | §12 |
| Progress bar | `#ptrack > #pfill` | §13 |
| Orbs | `.orb .orb-{outer/mid/core}` | §14 |
| Slide transition | `.slide .active .exit` | §15 |
| Contrast layout | `.contrast-row > .contrast-card` | §16 |
| Hover chip | `.q-chip` | §17 |
| Boilerplate | — | §18 |
| Sidebar nav (presentation) | `#sidebar > #sidebar-menu > .sitem` | §19 |
| Presentation font scale | `h1/h2/h3/p` clamp overrides | §4 ¶Presentation |
