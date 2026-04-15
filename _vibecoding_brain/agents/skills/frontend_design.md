## Skill: Frontend Design Patterns (Montrroase) — v2
> Injected for: architect, implementer, impl-frontend on FRONTEND / FULLSTACK / DESIGN tasks.
> **Authority:** `context/design_system.md` is the source of truth. This skill encodes the checks and heuristics that catch "blank-hospital-white" output before it ships. When this skill and `design_system.md` appear to conflict, `design_system.md` wins — and `design_system.md` should be updated to resolve the conflict.

---

### The Blank-Page Smell Test — run BEFORE you write a single line

Before writing any frontend code, answer these in your `<planning_and_design>` block:

1. **Canvas vs surface:** What is `body`'s background? (Must be `--color-canvas` `#F5F7FA`, never pure white, never `#FAFAFA`.) What are the cards' backgrounds? (Must be `--color-surface` `#FFFFFF`.) Is there at least one nested element that uses `--color-surface-sunken`?
2. **Contrast:** For every card I'm adding, does it have BOTH a `1px solid --color-border` AND `--shadow-card`? If either is missing, the card will blend into the canvas. (This is the Section 0 Contrast Rule.)
3. **Interactive states:** For every clickable element (button, link, row, icon-button), which classes or styles cover hover, focus-visible, and pressed? If any of the three is missing, stop and add it before you write the markup.
4. **Elevation layering:** List the z-layers on this screen from canvas → cards → raised (dropdowns/popovers) → overlay (modals). Is each layer visually distinct from the one below it? (Section 2.)
5. **StatTile anatomy:** If there is a stat/KPI, does it have (a) a left status rail, (b) an icon in a 32px tinted square, (c) `tabular-nums` on the number, (d) a delta indicator where applicable? A number in plain body text on a plain white card is a **nude stat** — rejected.
6. **Motion:** Which interactions on this screen animate? For each one, which duration token + easing curve? (Section 7.3.) Use named tokens, never `duration-[220ms]`.
7. **Density:** What row height? (32 compact / 40 default / 48 comfortable — never more.) What card padding? (12/16/24.)

If you cannot answer every one of the above, you are not ready to write code. Re-read `design_system.md`.

---

### The Premium Feel Checklist — run BEFORE you submit

Once the code is written, run your diff against this list. If any answer is *no*, fix it before marking the task complete.

- [ ] Canvas is `--color-canvas`, not pure white or `#FAFAFA`.
- [ ] Every card has `1px solid --color-border` AND `var(--shadow-card)`.
- [ ] Every card lifts visibly off the canvas (contrast check passes by eye).
- [ ] Every interactive element has a defined hover state (bg shift, not just cursor).
- [ ] Every interactive element has a defined `focus-visible` state (ring via `--shadow-focus`).
- [ ] Every button has a pressed state (`scale(0.98)` OR bg darker).
- [ ] All numeric display uses `font-variant-numeric: tabular-nums lining-nums`.
- [ ] Stat tiles have a left status rail AND icon square AND delta (where relevant).
- [ ] Badges use tinted bg + 1px inset ring + darker text (not solid color).
- [ ] Radius is graduated (cards 8px, inputs 6px, badges 4px) — never uniform `rounded-2xl`.
- [ ] Max font-weight in body content is 600. Weight 700 only on page `<h1>`.
- [ ] Section headings use `-0.01em` letter-spacing; page headings `-0.025em`.
- [ ] Every list/table has an empty state with headline + description + CTA.
- [ ] Every data-fetching component has loading + error states.
- [ ] All animations use Framer Motion + `useReducedMotion()` hook.
- [ ] All motion uses named duration + easing tokens from `design_system.md` §7.
- [ ] No `bg-gradient-*`, no `from-*`/`to-*`, no `rounded-2xl`, no `lucide-react`, no emojis-as-UI.
- [ ] No raw `bg-zinc-*` / `bg-slate-*` / `bg-gray-*` — all colors via CSS custom properties.
- [ ] No hardcoded hex colors in JSX. No inline `style={{}}` for colors.

---

### Surface Hierarchy — what goes on what

```
Layer 0 (canvas):          var(--color-canvas)         #F5F7FA   ← body, page shell
Layer 1 (sidebar/wells):   var(--color-canvas-sunken)  #EEF1F6   ← sidebar bg, recessed wells
Layer 2 (cards):           var(--color-surface)        #FFFFFF   ← cards, panels, stat tiles
Layer 2-inset (nested):    var(--color-surface-sunken) #F8F9FB   ← nested wells INSIDE cards
Layer 3 (raised):          var(--color-surface)        + --shadow-raised   ← dropdowns, popovers
Layer 4 (overlay):         var(--color-surface)        + --shadow-overlay  ← modals, drawers
```

- **Sidebar is NEVER dark.** It uses `--color-canvas-sunken`, a hair darker than the canvas. Same warm-cool family.
- **Row hover uses `--color-surface-sunken`, not an accent tint.** Accent tint is reserved for *selected*, not *hovered*.
- **Modal overlay backdrop:** `rgba(15, 23, 42, 0.40)` + `backdrop-filter: blur(8px)`. Slate-tinted, not pure black.

---

### The 60-30-10 Rule (color discipline)

- **60%** neutral surfaces — canvas, surface, sunken (the layering ramp)
- **30%** text hierarchy — primary / secondary / muted / subtle
- **10%** accent + status + secondary accent + data-viz

Brand blue (`--color-accent`) appears ONLY on:
- Primary CTA buttons
- Active nav item (subtle tint bg + 2px left border)
- Links, focus rings, progress indicators
- Primary chart series
- Selected-row backgrounds and left borders

**NEVER** on: sidebar bg, toolbar bg, table headers, modal headers, section backgrounds, decorative icons.

---

### Typography Rules

```
Page title (<h1>):  24px / 600 / -0.025em / 1.2
Section title:      16px / 600 / -0.01em  / 1.3
Body default:       14px / 400
Body small:         13px / 400
Label:              13px / 500
Caption:            12px / 500
Overline:           11px / 500 / uppercase / 0.06em
Stat value:         28px / 600 / -0.025em / tabular-nums
```

- **14px body, not 16px.** SaaS density standard.
- **Max weight 600 in body.** Weight 700 only on page `<h1>`.
- **Numeric data always `tabular-nums lining-nums`.** No exceptions.
- **Code, IDs, timestamps:** Geist Mono / JetBrains Mono.

---

### Spacing — 4px grid

Use the token scale. No arbitrary values.

```
--space-1 4   --space-2 8   --space-3 12   --space-4 16
--space-5 20  --space-6 24  --space-7 32   --space-8 40
```

Card padding: `12px` (sm) / `16px` (md, default) / `24px` (lg).
Section gap (distance between stacked cards): `20px`.
Page padding: `24px` desktop, `16px` mobile.

---

### Motion

Named tokens only — never arbitrary milliseconds.

| Interaction | Duration | Easing |
|---|---|---|
| Button hover | instant (80ms) | out-quint |
| Button press | fast (120ms) | spring |
| Row hover | instant (80ms) | out-quint |
| Focus ring | fast (120ms) | out-quint |
| Dropdown open | default (180ms) | out-quint |
| Modal enter | enter (220ms) | out-expo |
| Modal exit | exit (160ms) | in-out |
| Page enter | enter (220ms) | out-quint |
| Sidebar collapse | default (180ms) | in-out |

**Every animation must respect `useReducedMotion()`** — use Framer Motion's hook, never manually query the media query.

---

### Phosphor Icons — sizes and weights

- **14px** — inline badges, dense tables
- **16px** — body text, buttons, row actions
- **20px** — toolbars, stat-tile icons
- **24px** — page-header actions
- **40px** — empty-state illustrations

Weight defaults:
- `regular` — UI default
- `bold` — active/selected nav state
- `fill` — selected tab icon

Icons inherit `currentColor`. Never multi-colored. Never decorative rainbow.

---

### Modal Standards

- Header: white bg, matches body — **NO colored header**
- Overlay: `rgba(15, 23, 42, 0.40)` + `backdrop-filter: blur(8px)`
- Widths: 384px (alert) / 512px (form) / 672px (settings) / 896px (complex)
- Max height: 85vh with internal scroll
- Padding: 24px
- Close button: top-right, `aria-label="Close"`
- Enter: `scale(0.96) → 1`, `opacity 0 → 1`, `--duration-enter` (220ms), `--ease-out-expo`
- Exit: `scale(1 → 0.98)`, `--duration-exit` (160ms), `--ease-in-out` — **faster than enter**
- Focus returns to triggering element on close
- `role="dialog"` + `aria-modal="true"` + `aria-labelledby`

---

### Anti-AI-Slop — INSTANT FAIL patterns

Mirrors `design_system.md` §12. These 15 patterns are NEVER acceptable:

| # | Pattern | Why |
|---|---|---|
| 1 | `bg-gradient-to-*`, `from-*`, `to-*` as decoration | AI-slop gradient |
| 2 | `bg-white` on body / page shell, or `--background: #FFFFFF` | Hospital white — use `--color-canvas` |
| 3 | `rounded-2xl` on cards | Use graduated radius |
| 4 | `from 'lucide-react'` | Phosphor only |
| 5 | `font-bold` / `font-[700]` / `font-black` in body | Max weight 600 |
| 6 | `bg-purple-*`, `bg-pink-*`, `from-purple` → `to-blue` | Not in palette |
| 7 | Raw Tailwind neutrals: `bg-zinc-*`, `bg-slate-*`, `bg-gray-*` | Use custom properties |
| 8 | Emojis as UI elements | Phosphor icons only |
| 9 | `box-shadow: 0 ... rgba(0,0,0,…)` | Use `rgba(16, 24, 40, …)` cool-tint |
| 10 | Solid-color badges without inset ring | Must use tinted-ring variant |
| 11 | Stat tile missing left rail OR missing `tabular-nums` | Nude stat |
| 12 | Interactive element missing `:hover` OR `:focus-visible` | Section 8 violation |
| 13 | `backdrop-filter: blur()` on non-overlay surfaces | Glassmorphism slop |
| 14 | Inline `style={{}}` for colors/spacing | Use tokens |
| 15 | `duration-[XXXms]` arbitrary values | Use motion tokens |

---

### When in doubt

Ask: *"Would Linear / Vercel / Stripe / Notion ship this?"*

If the answer is "no, it looks like an empty Google Doc," you have failed the Contrast Rule and need to re-read `design_system.md` §0.
