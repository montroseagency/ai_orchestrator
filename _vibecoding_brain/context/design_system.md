# Montrroase Design System — v2

> **Source of truth.** RAG-indexed. Read by implementer / impl-frontend / architect.
> When `globals.css` and this file disagree, **this file wins** and `globals.css` must be updated to match.
> **Design philosophy:** premium SaaS on par with Linear / Vercel / Stripe / Notion. Minimalist but **never blank**. Contrast comes from *layering*, not from saturation. No AI slop.

---

## 0. The Contrast Rule (non-negotiable)

> **Every surface must be visually distinguishable from its immediate parent by at least one of:**
> (a) a ≥4% lightness delta, OR
> (b) a 1px border + visible shadow combo.
>
> **Pure `#FFFFFF` on `#FAFAFA` is NOT layering.** Those two values are ~1.5% apart — the human eye reads them as the same color. The page canvas is never pure white. Cards are pure white, borders are crisp, shadows are layered. That is how a card stands out.

If an implementer ships a page where you can't see where a card ends and the background begins, that is an **instant fail**. The card must lift off the canvas.

---

## 1. Color Tokens

### 1.1 Surface Elevation Ramp — THREE layers, not two

```css
--color-canvas:           #F5F7FA   /* Page background — cool slate tint. NEVER pure white. */
--color-canvas-sunken:    #EEF1F6   /* Sidebar, recessed wells, page footers */
--color-surface:          #FFFFFF   /* Default card/panel — pops against canvas */
--color-surface-sunken:   #F8F9FB   /* Nested container inside a card (e.g., code block, quote, form well) */
--color-surface-raised:   #FFFFFF   /* Dropdowns, tooltips, popovers — same color but stronger shadow */
--color-surface-overlay:  #FFFFFF   /* Modals — same color, strongest shadow */
```

**Why this works:** Canvas is tinted (~1.8% darker than white, with a cool slate undertone) so pure-white cards visibly lift off it. Nested sunken containers are 1.2% darker than the card they live in, so forms and wells are distinguishable without borders. The ramp has three clear levels: canvas → surface → surface-raised.

**Hard rule:** `body { background: var(--color-canvas) }`. Never `background: white`. Never `background: #FAFAFA`.

### 1.2 Borders — crisper than before

```css
--color-border:           #E3E5EA   /* Default card edge — visible, not wimpy */
--color-border-subtle:    #EDEFF3   /* Interior dividers (section header underlines, table row dividers) */
--color-border-strong:    #D0D5DD   /* Inputs, focus-adjacent emphasis */
```

Borders are defined, not hairlines. A card without a border is a card you can't see.

### 1.3 Text — warmth via subtle slate undertone

```css
--color-text:             #0F172A   /* Slate-900 — primary body text, stat values, headings */
--color-text-secondary:   #475569   /* Slate-600 — secondary copy, subtitles, metadata */
--color-text-muted:       #64748B   /* Slate-500 — captions, timestamps, labels */
--color-text-subtle:      #94A3B8   /* Slate-400 — placeholders, disabled, decorative */
```

Slate reads warmer and more premium than pure zinc on tinted canvases. Zinc is colder and looks hospital-sterile on white.

### 1.4 Primary Accent — brand blue, expanded

```css
--color-accent:           #2563EB   /* Blue-600 — primary CTAs, links, brand */
--color-accent-hover:     #1D4ED8   /* Blue-700 */
--color-accent-pressed:   #1E40AF   /* Blue-800 */
--color-accent-subtle:    #EFF4FF   /* Blue-50 — selected rows, active nav tint */
--color-accent-ring:      rgba(37, 99, 235, 0.12)   /* Focus halo */
--color-accent-border:    #BFD7FE   /* Blue-200 — tinted-ring badge borders */
```

### 1.5 Secondary Accent — teal (for data-viz and non-primary emphasis)

```css
--color-accent-2:         #0D9488   /* Teal-600 */
--color-accent-2-subtle:  #ECFDF9   /* Teal-50 */
--color-accent-2-ring:    rgba(13, 148, 136, 0.12)
```

**Rules for secondary accent:**
- Used ONLY in charts, pills for non-primary categories, and as a second data series.
- NEVER used on a primary CTA. Primary CTAs are always `--color-accent`.
- NEVER mixed with primary accent in the same component (no blue-and-teal buttons).

### 1.6 Data-viz Palette (Recharts)

```css
--chart-1:  #2563EB   /* blue — primary series */
--chart-2:  #0D9488   /* teal — secondary series */
--chart-3:  #CA8A04   /* amber — tertiary */
--chart-4:  #DC2626   /* red — negative/delta-down */
--chart-5:  #7C3AED   /* violet — fifth series, sparingly */
--chart-6:  #64748B   /* slate — neutral baseline, grid lines */
```

Use in order. Never introduce a seventh color — merge smaller categories into "Other".

### 1.7 Status Colors — tinted-ring variant

```css
/* success */
--color-success:          #15803D   /* text */
--color-success-bg:       #F0FDF4   /* bg tint */
--color-success-border:   #86EFAC   /* 1px inset ring */

/* warning */
--color-warning:          #A16207   /* darker than before for AA contrast on bg */
--color-warning-bg:       #FEFCE8
--color-warning-border:   #FDE68A

/* error */
--color-error:            #B91C1C
--color-error-bg:         #FEF2F2
--color-error-border:     #FCA5A5

/* info — same as accent */
--color-info:             #1D4ED8
--color-info-bg:          #EFF4FF
--color-info-border:      #BFD7FE
```

Badges use **tinted bg + 1px inset ring of the matching border color + darker text**. Flat solid badges are banned — they read as stickers, not data.

---

## 2. Elevation & Shadows — layered, cool-tinted

Shadows use **slate-tinted dark** (`rgba(16, 24, 40, …)`) instead of pure black. This is the Figma/Linear/Stripe shadow recipe. Pure-black shadows look cheap.

```css
--shadow-xs:       0 1px 2px rgba(16, 24, 40, 0.05);
--shadow-card:     0 1px 3px rgba(16, 24, 40, 0.06), 0 1px 2px rgba(16, 24, 40, 0.04);
--shadow-raised:   0 4px 8px -2px rgba(16, 24, 40, 0.10), 0 2px 4px -2px rgba(16, 24, 40, 0.06);
--shadow-overlay:  0 20px 32px -8px rgba(16, 24, 40, 0.16), 0 8px 16px -4px rgba(16, 24, 40, 0.08);
--shadow-focus:    0 0 0 3px var(--color-accent-ring);
```

### Elevation table

| Layer | Element | Shadow | Border |
|---|---|---|---|
| 0 | Canvas (body) | — | — |
| 1 | Card / SectionCard / StatTile | `--shadow-card` | `1px solid --color-border` |
| 2 | Dropdown / Tooltip / Popover | `--shadow-raised` | `1px solid --color-border` |
| 3 | Modal / Drawer | `--shadow-overlay` | `1px solid --color-border` |

**Never skip the shadow on a card.** A borderless, shadowless card is just a rectangle of the same color as its neighbors — it has no identity. Cards get a visible shadow *and* a visible border. Both.

---

## 3. Radius — graduated scale

```css
--radius-xs:   4px   /* Small buttons, tags, chips */
--radius-sm:   6px   /* Inputs, list items, segmented tabs, badges */
--radius-md:   8px   /* Cards, panels, default surfaces */
--radius-lg:   12px  /* Modals, popovers, large containers */
--radius-xl:   16px  /* Full-page overlays (rare) */
--radius-full: 9999px /* Avatars, status dots, round icon buttons */
```

**Banned:** using a single radius everywhere. `rounded-2xl` on cards is AI slop — instant fail. A card has `--radius-md` (8px), its enclosed button has `--radius-sm` (6px), its badge has `--radius-xs` (4px). Nested radii always decrease toward the leaf.

---

## 4. Typography

```
Display (page title):   24px / 600 / -0.025em / 1.2       var(--font-sans)
Section heading:        16px / 600 / -0.01em  / 1.3       var(--font-sans)
Label:                  13px / 500 / 0        / 1.4       var(--font-sans)
Body default:           14px / 400 / 0        / 1.5       var(--font-sans)
Body small:             13px / 400 / 0        / 1.5       var(--font-sans)
Caption:                12px / 500 / 0        / 1.4       var(--font-sans)
Overline:               11px / 500 / 0.06em uppercase / 1.4  var(--font-sans)
Stat value:             28px / 600 / -0.025em / 1.1  + tabular-nums   var(--font-sans)
Code / ID / timestamp:  13px / 500 / 0        / 1.5       var(--font-mono)  /* Geist Mono */
```

**Rules:**
- Max font-weight in body: **600**. Weight 700 is reserved for page `<h1>` headings only.
- **All numeric display (stat tiles, table metrics, timestamps, IDs):** `font-variant-numeric: tabular-nums lining-nums`. Non-negotiable.
- Headings ≥20px get `letter-spacing: -0.02em` (tighter = more premium).
- Body text is 14px, not 16px. SaaS density standard.
- Never use `font-bold` or `font-[700]` on stat values or table cells.

---

## 5. Spacing — 4px grid

```css
--space-0:   0;
--space-1:   4px;
--space-2:   8px;
--space-3:   12px;
--space-4:   16px;
--space-5:   20px;
--space-6:   24px;
--space-7:   32px;
--space-8:   40px;
--space-9:   48px;
--space-10:  64px;
```

**Rules:**
- No arbitrary values (no `gap-[13px]`, no `p-[18px]`). If you need something off-grid, update the scale.
- Card internal padding defaults: **16px (md)**. Dense cards use **12px (sm)**. Hero cards use **24px (lg)**.
- Section gap (distance between cards in a stack): **20px**.
- Page padding: **24px** desktop, **16px** mobile.

---

## 6. Density — row heights

```
Row compact:       32px   (dense tables, power-user lists)
Row default:       40px   (standard tables, most lists)
Row comfortable:   48px   (mobile, touch, sparse content)
```

Never exceed 48px. A dashboard row that is 64px tall is wasting half your screen.

---

## 7. Motion — tokens, easing, and recipes

### 7.1 Duration tokens

```css
--duration-instant:  80ms    /* hover bg tint, row highlight */
--duration-fast:     120ms   /* focus ring, small state changes */
--duration-default:  180ms   /* button press, dropdown, tab switch */
--duration-enter:    220ms   /* modal enter, page enter */
--duration-exit:     160ms   /* modal exit — always faster than enter */
--duration-slow:     280ms   /* complex layout transitions (rare) */
```

### 7.2 Easing curves

```css
--ease-out-quint:  cubic-bezier(0.22, 1, 0.36, 1);      /* standard enter — decelerating */
--ease-out-expo:   cubic-bezier(0.16, 1, 0.3, 1);       /* prominent enter — sharper decel */
--ease-in-out:     cubic-bezier(0.65, 0, 0.35, 1);      /* symmetric */
--ease-spring:     cubic-bezier(0.34, 1.56, 0.64, 1);   /* playful press — use sparingly */
```

**Hard rule:** linear easing is banned on any visible UI change. Always use a curve.

### 7.3 Standard interaction recipes

| Interaction | Duration | Easing | What animates |
|---|---|---|---|
| Button hover | instant (80ms) | out-quint | `background-color` |
| Button press | fast (120ms) | spring | `transform: scale(0.98)` |
| Row hover | instant (80ms) | out-quint | `background-color` → `--color-surface-sunken` |
| Focus ring appear | fast (120ms) | out-quint | `box-shadow` |
| Dropdown open | default (180ms) | out-quint | `opacity 0→1`, `y: -4px → 0` |
| Modal enter | enter (220ms) | out-expo | `opacity 0→1`, `scale: 0.96 → 1` |
| Modal exit | exit (160ms) | in-out | `opacity 1→0`, `scale: 1 → 0.98` |
| Page enter | enter (220ms) | out-quint | `opacity 0→1`, `y: 8 → 0` |
| Sidebar collapse | default (180ms) | in-out | `width` |
| Toast slide-in | default (180ms) | out-expo | `opacity 0→1`, `y: 12 → 0` |

**Every animation must respect `useReducedMotion()` (Framer Motion hook).** When reduced motion is on, duration → 0 but opacity still transitions (accessible fade).

---

## 8. Interactive States — mandatory on every interactive element

Every `<button>`, `<a>`, `<Link>`, form control, clickable card, and interactive row **must** define these four states:

1. **Default** — resting appearance
2. **Hover** — bg shift (never pure color change on text, that looks broken)
3. **Focus-visible** — 2px accent ring with 2px offset, via `box-shadow: var(--shadow-focus)`
4. **Pressed / active** — either bg darker OR `scale(0.98)` transform

Plus, where applicable:
5. **Selected** — `--color-accent-subtle` bg + 2px left border `--color-accent` (nav items, rows)
6. **Disabled** — opacity 0.5, cursor not-allowed, no hover response

**Missing any of these four base states = fail.** A button that doesn't visibly respond to hover is broken UX, not "minimalist."

---

## 9. Component Anatomy — the recipes implementers must follow

### 9.1 StatTile — the card that shows one KPI

```
┌───────────────────────────┐
│ ▌ [icon] ACTIVE CLIENTS   │   ← 3px left status rail (accent/success/warning/error)
│ ▌                         │     icon in 32px tinted square (bg-accent-subtle)
│ ▌ 1,284                   │     overline label 11px/500/uppercase
│ ▌ ↑ 4.2% vs last week     │     stat value 28px/600/tabular-nums
└───────────────────────────┘     delta in badge-success/error inline
  --color-surface
  1px --color-border
  --shadow-card
  --radius-md
  padding 16px
```

**Instant-fail checks for a StatTile:**
- No left status rail → fail
- No icon square → fail
- Stat value not `tabular-nums` → fail
- Plain number on white with no other visual hierarchy → fail ("nude stat")

### 9.2 SectionCard

```
┌───────────────────────────┐
│ Section Title    [action] │   ← header: 16px pad, border-bottom --color-border-subtle
├───────────────────────────┤
│                           │
│   [body content]          │   ← body: 16px pad (or 0 for full-bleed tables)
│                           │
├───────────────────────────┤
│ footer (optional)         │   ← footer: 12px pad, border-top --color-border-subtle
└───────────────────────────┘
  --color-surface, --color-border, --shadow-card, --radius-md
```

Header always has a visible divider. Header-less cards look like empty text boxes.

### 9.3 PageHeader

```
Breadcrumb (optional, 12px/500/muted)
[Title — display 24px/600]     [primary button] [icon button]
Subtitle — body secondary 14px
```

Padding: 20px block, 24px inline. Always includes an action or feels empty.

### 9.4 Badge (tinted-ring)

```css
.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: var(--radius-xs);
  font-size: 12px;
  font-weight: 500;
  line-height: 1.4;
  white-space: nowrap;
}
.badge-success {
  background: var(--color-success-bg);
  color: var(--color-success);
  box-shadow: inset 0 0 0 1px var(--color-success-border);
}
/* same pattern for warning / error / info */
```

Solid-color badges are banned. Every badge has tinted bg + 1px inset ring + darker text.

### 9.5 Button — primary

```css
.btn-primary {
  background: var(--color-accent);
  color: #FFFFFF;
  padding: 8px 14px;
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 500;
  box-shadow: var(--shadow-xs), inset 0 1px 0 rgba(255, 255, 255, 0.12);
  transition: background-color var(--duration-instant) var(--ease-out-quint),
              transform var(--duration-fast) var(--ease-spring);
}
.btn-primary:hover { background: var(--color-accent-hover); }
.btn-primary:active { transform: scale(0.98); background: var(--color-accent-pressed); }
.btn-primary:focus-visible { box-shadow: var(--shadow-xs), var(--shadow-focus); outline: none; }
```

The `inset 0 1px 0 rgba(255,255,255,0.12)` is a subtle top-edge highlight. It's what makes the button look lit instead of flat.

### 9.6 Interactive row (table / list)

```css
.row {
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border-subtle);
  transition: background-color var(--duration-instant) var(--ease-out-quint);
}
.row:hover { background: var(--color-surface-sunken); }
.row[aria-selected="true"] {
  background: var(--color-accent-subtle);
  box-shadow: inset 2px 0 0 var(--color-accent);
}
```

Hover bg is `--color-surface-sunken`, NOT an accent tint. Accent tint is reserved for *selected*, not *hovered*.

### 9.7 Empty state

```
     [subtle Phosphor icon — 40px, --color-text-muted]
     Clear headline: what this area is for (16px/600)
     Description: why it's empty (14px/400/secondary)
     [Primary CTA button — how to add the first item]
```

Centered, padding 40px. Never leave an area blank — even placeholder lists show an empty state.

---

## 10. Icons — Phosphor only

- **Library:** `@phosphor-icons/react`. Lucide is banned.
- **Weights:** `regular` (default UI), `bold` (active state), `fill` (selected tabs).
- **Sizes:** 14px (inline badges), 16px (body/buttons), 20px (toolbars, stat tiles), 24px (page headers), 40px (empty-state illustrations).
- **Color:** `currentColor`. Never multi-colored. Never rainbow.
- Icons inside stat tiles live in a 32px `--color-accent-subtle` square with `--radius-sm`.

---

## 11. Layout Tokens

```css
--sidebar-expanded:    240px;
--sidebar-collapsed:   64px;
--topbar-height:       56px;
--content-max-width:   1280px;
--content-padding:     24px;   /* desktop */
--content-padding-sm:  16px;   /* mobile */
```

---

## 12. Anti-AI-Slop Red Lines (INSTANT FAIL)

These are auto-checked by the quality gate. Appearing in modified files = blocked merge.

| # | Pattern | Why |
|---|---|---|
| 1 | `bg-gradient-to-*`, `from-*`, `to-*` as decoration | AI-slop gradient |
| 2 | Pure `#FFFFFF` body background, or `bg-white` on `<body>` / page shell | Hospital white, no contrast — **violates Section 0** |
| 3 | `rounded-2xl` on cards | Must use graduated radius (Section 3) |
| 4 | `import ... from 'lucide-react'` | Phosphor only |
| 5 | `font-bold` / `font-[700]` / `font-black` in body text | Max weight 600 |
| 6 | `bg-purple-*`, `bg-pink-*`, `from-purple` → `to-blue` | Not in palette |
| 7 | Raw Tailwind neutral scales: `bg-zinc-*`, `bg-slate-*`, `bg-gray-*`, `text-indigo-*` | Use CSS custom properties from this file |
| 8 | Emojis used as UI elements (labels, bullets, status icons) | Phosphor icons only |
| 9 | `box-shadow: 0 0 0 ...` (pure black shadows) | Use `rgba(16, 24, 40, …)` |
| 10 | Solid-color badges without inset ring | Must use tinted-ring variant (Section 9.4) |
| 11 | Stat tiles without left status rail OR without `tabular-nums` | Nude stat — violates Section 9.1 |
| 12 | Interactive element (button, link, clickable row) missing `:hover` OR `:focus-visible` | Violates Section 8 |
| 13 | `backdrop-filter: blur()` on anything other than modal overlays / command palette | Glassmorphism slop |
| 14 | Inline `style={{}}` for colors/spacing | Use tokens |
| 15 | `duration-[XXXms]` arbitrary values | Use motion tokens (Section 7.1) |

---

## 13. Design Principles (ranked)

1. **Contrast is structural, not decorative.** Layering creates hierarchy. If you can't see where one element ends and another begins, the design has failed — even if nothing is "wrong" on paper.
2. **Density is respect.** Our users are power users. Compact rows, tight spacing, 14px body. Whitespace is a tool, not a default.
3. **Color has meaning.** Blue = brand/action. Teal = secondary data. Status colors = semantics. Everything else is neutral. Never decorative color.
4. **Motion conveys causality.** An animation should answer "what just happened?" or "where did that come from?" Never "look at me."
5. **Typography does the heavy lifting.** Size and weight create hierarchy — not boxes, not color, not decoration.
6. **Every interactive element has four states.** Default / hover / focus / pressed. No exceptions. (Section 8.)
7. **The card always lifts off the canvas.** Border + shadow + pure white on tinted canvas. (Section 0.)
8. **No feature should look like an AI generated it.** Graduated radii, Phosphor icons, no gradients, no rainbow, no 2xl, max weight 600, tabular nums. (Section 12.)
