## Skill: Frontend Design Patterns (Montrroase)
> Injected for: creative_brain, implementer on FRONTEND / FULLSTACK / DESIGN tasks.
> When this skill conflicts with Montrroase design_system.md tokens, design_system.md takes precedence.

### Anti-AI-Slop Patterns -- INSTANT FAIL
These 12 patterns are NEVER acceptable in Montrroase UI code:

| # | Pattern | Why it fails |
|---|---------|-------------|
| 1 | `bg-gradient-to-r from-indigo-500 to-purple-600` | AI-generated gradient slop |
| 2 | Emojis as section headers or status indicators | Unprofessional SaaS UI |
| 3 | `rounded-2xl` applied uniformly | Must use graduated radius (4/6/8/12px) |
| 4 | Cards nested > 2 levels deep | Visual noise, flat hierarchy preferred |
| 5 | Lucide icons (`lucide-react`) | Phosphor icons only |
| 6 | Rainbow-colored icons | Icons use `currentColor`, monochrome |
| 7 | `backdrop-filter: blur()` on surfaces | Glass effect only for overlays/command palette |
| 8 | Dark sidebar (`bg-slate-900`) | Sidebar uses `gray-50` (#FAFAF8) |
| 9 | `font-bold` / weight 700+ in body | Max weight 600; 700 only page headings |
| 10 | Raw Tailwind colors (`bg-zinc-100`) | Use Montrroase design tokens only |
| 11 | Inline `style={{}}` | Tailwind classes or CSS custom properties |
| 12 | `box-shadow` on regular cards | Use `border` for card edges; shadow only on elevated panels |

### Surface Hierarchy (Premium SaaS Standard)
Depth comes from color shifts, not shadows:

```
Layer 0 (page canvas):     gray-50  (#FAFAF8)
Layer 1 (cards/panels):    white    (#FFFFFF) + border gray-200
Layer 2 (recessed areas):  gray-100 (#F5F5F0)
Layer 3 (inputs/wells):    white    (#FFFFFF) + inset border
```

- Page background is NEVER pure white -- always `gray-50`
- Cards create contrast by being white ON gray-50
- Sidebar matches page canvas (`gray-50`), NOT dark
- Row hover: `gray-100`, NOT colored tint
- Selected state: `accent-50` (`#EEF2FF`), subtle tint

### Graduated Border Radius Scale
```
4px  -- buttons, small interactive elements
6px  -- list items, tags, badges
8px  -- cards, surfaces, inputs (default)
12px -- modals, popovers, large containers
16px -- full-page overlays (rare)
```
NEVER use a single radius for everything. NEVER use `rounded-2xl` (16px) on cards.

### Brand Color Discipline (60-30-10 Rule)
- **60%** neutral surfaces (white, gray-50, gray-100)
- **30%** gray text hierarchy (zinc-900, zinc-600, zinc-400)
- **10%** accent + status colors

Brand blue (`#2563EB`) appears ONLY on:
- Primary CTA buttons
- Active nav item (bg tint + text)
- Links and focus rings
- Progress indicators

NEVER on: sidebar bg, toolbar bg, table headers, modal headers, section bg

### Typography System
```
14px (text-sm)  -- default body text (NOT 16px)
Weights: 400 (normal), 500 (medium), 600 (semibold)
Weight 700: ONLY page-level h1 headings

Numeric data: tabular-nums lining-nums
Headings 20px+: letter-spacing -0.02em
Code/IDs/timestamps: monospace font (Geist Mono / JetBrains Mono)
```

### Spacing Grid
All spacing on 4px base grid: 4, 8, 12, 16, 20, 24, 32, 40px.
No arbitrary pixel values. No `gap-[13px]` or `p-[18px]`.

### Component Architecture Patterns
- Server Components by default -- `'use client'` only when needed (hooks, events, browser APIs)
- React Query for all server state -- never raw `fetch()`
- Framer Motion for all animations -- no CSS transitions for multi-step motion
- Phosphor icons at correct sizes: 16px (body), 20px (toolbar), 24px (headers)
- Empty states always present with actionable UX copy
- Loading: skeleton for `isLoading`, subtle spinner for `isFetching`
- Error states with user-facing copy (never raw error messages)

### Modal Standards
- Header: white bg (matches body), NO colored header
- Overlay: `rgba(0,0,0,0.5)` + `backdrop-filter: blur(8px)`
- Widths: 384px (alert), 512px (form), 672px (settings), 896px (complex)
- Max height: 85vh with internal scroll
- Padding: 24px (p-6)
- Close button: top-right, `aria-label="Close"`
- Enter: `scale(0.95) -> 1` at 200ms (NEVER from `scale(0)`)
- Exit: 150ms (faster than enter)

### Animation Timing Reference
```
100ms -- hover bg change, row highlight
150ms -- button press, focus ring, dropdown open
200ms -- modal open, page enter, sidebar toggle
300ms -- slow/complex transitions (MAXIMUM)
```
Easing: `cubic-bezier(0.16, 1, 0.3, 1)` for enters, `ease-out` for exits.
All animations MUST use `useReducedMotion()` hook for accessibility.
