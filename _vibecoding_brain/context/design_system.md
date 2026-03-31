# Montrroase Design System
> For Creative Brain agent. Full design token reference.

## Color Palette
```
Accent (Blue):
  DEFAULT: #2563EB   (blue-600)
  light:   #DBEAFE   (blue-100) ← backgrounds, active states
  dark:    #1D4ED8   (blue-700) ← hover

Surfaces:
  DEFAULT: #FFFFFF   ← cards, modals
  subtle:  #FAFAFA   ← page background
  muted:   #F4F4F5   (zinc-100) ← secondary backgrounds

Text:
  DEFAULT:   #18181B   (zinc-900)
  secondary: #52525B   (zinc-600)
  muted:     #A1A1AA   (zinc-400)

Borders:
  DEFAULT: #E4E4E7   (zinc-200)
  subtle:  #F4F4F5   (zinc-100)

Status:
  success: #16A34A  bg: #DCFCE7
  warning: #CA8A04  bg: #FEF9C3
  error:   #DC2626  bg: #FEE2E2
  info:    #2563EB  bg: #DBEAFE
```

## Spacing Scale
```
xs:  4px   sm:  8px   md: 12px
lg: 16px   xl: 24px   2xl: 32px   3xl: 40px
```

## Border Radius
```
surface:    8px   (most elements)
surface-lg: 16px  (modals, large cards)
```

## Shadows
```
sm:      0 1px 2px rgba(0,0,0,0.04)
surface: 0 2px 8px rgba(0,0,0,0.06)   ← cards default
lg:      0 4px 16px rgba(0,0,0,0.08)   ← elevated panels
```

## Typography
```
Page title:    text-2xl font-semibold tracking-tight   (1.5rem/600)
Section title: text-lg font-medium                      (1.125rem/500)
Body:          text-sm                                  (0.875rem/400)
Body large:    text-base                                (1rem/400)
Label:         text-sm font-medium                      (0.875rem/500)
Muted caption: text-xs text-muted                       (0.75rem/400)
```

## Layout
```
Sidebar expanded:  240px
Sidebar collapsed: 64px
Topbar height:     56px
Content max-width: 1280px
Content padding:   24px
```

## Animation
```
Durations: fast=150ms  default=200ms  slow=300ms
Library: Framer Motion (framer-motion v11)
Easing: ease-in-out for transitions, spring for interactions

Common patterns:
  Page enter:    opacity 0→1, y: 8→0, duration: 200ms
  Modal enter:   opacity 0→1, scale: 0.96→1, duration: 200ms
  Sidebar:       width animate with transition-default ease-in-out
  Hover lift:    y: 0→-2px, shadow increase, duration: fast
  Button press:  scale: 1→0.97, duration: fast
```

## Component Utility Classes (globals.css)
```css
.card-surface          /* white bg, border, 8px radius, surface shadow */
.surface-outlined      /* same as card-surface */
.surface-subtle        /* bg-surface-subtle only */
.badge-success/warning/error/info   /* colored badge variants */
.kpi-strip             /* horizontal KPI row */
.action-bar            /* flex row with md gap */
.empty-state           /* centered empty state */
.content-container     /* max-width + padding */
.section-header        /* flex space-between row */
.nav-item-active       /* sidebar active state */
.scrollbar-thin        /* thin scrollbar styling */
```

## Component Patterns

### Cards
```tsx
<div className="card-surface p-surface">
  <h3 className="text-section-title mb-2">Title</h3>
  <p className="text-sm text-secondary">Content</p>
</div>
```

### Buttons
```tsx
// Primary
<button className="bg-accent text-white px-4 py-2 rounded-surface text-sm font-medium hover:bg-accent-dark transition-sidebar">
// Ghost
<button className="border border-border text-secondary px-4 py-2 rounded-surface text-sm hover:bg-surface-subtle">
```

### Status Badges
```tsx
<span className="badge-success text-xs font-medium px-2 py-0.5 rounded-full">Active</span>
```

### Data Tables
```tsx
<tr className="table-row-hover border-b border-border">
  <td className="py-3 px-4 text-sm">...</td>
</tr>
```

## Icon Library
Using `lucide-react` (v0.552). Always prefer icons from this library.

## Design Principles
1. **Density:** Information-dense layouts. Minimal whitespace waste. SaaS power-user aesthetic.
2. **Consistency:** Never invent new colors or spacing not in this system.
3. **Clarity:** Labels, tooltips, empty states — always explain what's happening.
4. **Speed feel:** Optimistic UI updates + smooth 200ms transitions.
5. **No decoration for its own sake:** Every animation must aid comprehension or feel.
