# Montrroase Design System — Non-Negotiables

> **The taste floor.** Everything below is **non-negotiable** and supersedes any suggestion from a plugin, an agent's intuition, or a borrowed pattern.
>
> Everything NOT specified here is delegated to the `ui-ux-pro-max` and `frontend-design` plugins at agent runtime. Do not re-add taste decisions to this file without an explicit brand-owner sign-off — the plugins can reason about the current task; this file cannot.
>
> **On conflict: this file wins.** If a plugin suggests a pattern that violates any section below, the agent overrides it and notes the override in its summary.

---

## §0 — The Contrast Rule (the taste floor)

Every surface must be visually distinguishable from its immediate parent by at least one of:
- (a) a ≥4% lightness delta, OR
- (b) a visible 1px border + a visible shadow combo.

Pure `#FFFFFF` on `#FAFAFA` is **NOT** layering — those two are ~1.5% apart and the eye reads them as the same color. The canvas is tinted. Cards are pure white with a crisp border and a shadow. That contrast is what makes the card feel real.

Shipping a page where you can't see where a card ends and the background begins is an **instant fail**, even if the code compiles.

---

## §1 — Brand Tokens

```css
/* Canvas & surface — the layering system */
--color-canvas:         #F5F7FA   /* Page bg. Never pure white, never #FAFAFA. */
--color-surface:        #FFFFFF   /* Cards, panels, modals, toolbars. */
--color-surface-sunken: #F8F9FB   /* Nested wells inside a card. */

/* Text — slate undertone, not zinc */
--color-text:           #0F172A
--color-text-secondary: #475569
--color-text-muted:     #64748B

/* Primary accent — Montrroase blue */
--color-accent:         #2563EB
--color-accent-hover:   #1D4ED8
--color-accent-pressed: #1E40AF
--color-accent-subtle:  #EFF4FF

/* Border — visible, not hairline */
--color-border:         #E4E4E7
```

Status colors, chart palettes, secondary accents, elevation ramps, and shadow recipes — **delegated to `ui-ux-pro-max`** per task. The plugin must respect the tokens above; anything outside this file is its call.

- **Icons:** Phosphor (`@phosphor-icons/react`) only. Lucide is banned.
- **Fonts:** Inter (body) + Geist Mono (code/IDs). No other families.

---

## §2 — Typography Discipline

- **Body default: 14px.** SaaS density standard. Never 16px body by default.
- **Weights in body: 400, 500, 600 only.** Weight 700 is reserved for page `<h1>`. Never 800, never 900, never 300.
- **All numeric display** (stat values, table metrics, timestamps, IDs): `font-variant-numeric: tabular-nums lining-nums`. Non-negotiable. Tailwind: `tabular-nums slashed-zero lining-nums`.
- **Headings ≥20px:** `letter-spacing: -0.02em`. Tighter tracking reads premium.
- Never `font-bold` / `font-[700]` / `font-black` in body, table cells, or stat values.

---

## §3 — Graduated Radius Scale

```css
--radius-xs:    4px    /* tags, chips, small buttons */
--radius-sm:    6px    /* inputs, list items, segmented tabs, badges */
--radius-md:    8px    /* cards, panels, default surfaces */
--radius-lg:   12px    /* modals, popovers, large containers */
--radius-full: 9999px  /* avatars, pills, status dots */
```

**Banned:** one radius everywhere. `rounded-2xl` on cards is instant fail. Nested radii always **decrease** toward the leaf — card (8px) > its button (6px) > its badge (4px).

---

## §4 — Motion Tokens

```css
--duration-instant: 80ms    --duration-fast:    120ms
--duration-default: 180ms   --duration-enter:   220ms
--duration-exit:    160ms   --duration-slow:    280ms
```

- **Linear easing is banned** on any visible UI change. Always a curve.
- **Exit is always faster than enter** (160ms exit vs 220ms enter) — feels snappier.
- Every animation respects `useReducedMotion()` — duration drops to 0, opacity still transitions.
- **Arbitrary values like `duration-[235ms]` are banned.** Pick a token or stop.

Easing curves, choreography, scroll-linked motion — **delegated to `frontend-design` / `ui-ux-pro-max`** per task.

---

## §5 — Red Lines (instant-fail patterns)

The quality gate's banned-pattern scan (CLAUDE.md Step 8) greps for these. Any match blocks the merge.

| # | Pattern | Why |
|---|---|---|
| 1 | `bg-gradient-to-*`, `from-purple`, `to-blue`, `from-indigo` | AI-slop gradient |
| 2 | `bg-white` on `<body>` / page shell / layout wrapper; `background: #FFFFFF` or `#FAFAFA` on canvas | Hospital white — violates §0 |
| 3 | `rounded-2xl` on cards | Use graduated radius (§3) |
| 4 | `import ... from 'lucide-react'` | Phosphor only |
| 5 | `font-bold`, `font-[700]`, `font-black` in body text | Max weight 600 (§2) |
| 6 | `bg-purple-*`, `bg-pink-*`, rainbow color mixing | Not brand |
| 7 | `bg-zinc-*`, `bg-slate-*`, `bg-gray-*`, `text-indigo-*` | Use CSS custom props from §1 |
| 8 | Emojis as UI elements (labels, bullets, status icons) | Phosphor icons only |
| 9 | `box-shadow: 0 ... rgba(0, 0, 0, ...)` (pure-black shadows) | Use slate-tinted `rgba(16, 24, 40, …)` |
| 10 | `.badge-*` with solid background, no inset ring | Tinted-ring variants only: `badge-success/warning/error/info` |
| 11 | `.card-surface` / card missing BOTH border AND shadow | Nude card — violates §0 |
| 12 | `<button>` / `<a>` / `<Link>` / `role="button"` missing `hover:` OR `focus-visible:` | Dead interactive |
| 13 | `StatTile` / `.kpi-item` missing `tabular-nums` OR a `status-rail-*` class | Nude stat |
| 14 | `backdrop-filter: blur()` outside modal/drawer overlays and command palette | Glassmorphism slop |
| 15 | `duration-[\d+ms]` arbitrary values | Use motion tokens (§4) |
| 16 | Inline `style={{}}` for colors/spacing | Use tokens |

---

## What's NOT in this file (delegated to plugins)

- **Component anatomy recipes** (StatTile, SectionCard, PageHeader layouts) → `ui-ux-pro-max` picks composition per task
- **Color ramps beyond brand** (success/warning/error/info shades, chart palettes, secondary accents) → plugin recommends per task, within §1 constraints
- **Elevation tiers and shadow recipes** → plugin picks per surface
- **Density decisions** (row heights, card padding sizes) → plugin picks per data density
- **Interactive-state recipes** (hover tint, pressed transform, selected highlight) → plugin proposes; agent verifies against §5
- **Accessibility tactics** (ARIA, focus order, screen-reader copy, tap-target sizing) → orchestrator runs `chrome-devtools-mcp:a11y-debugging` post-implementation (CLAUDE.md Step 8.6)
- **Empty-state patterns, animation choreography, iconography sizing conventions** → plugin owned

On conflict, this file wins. Agents must cite any plugin override in their summary.
