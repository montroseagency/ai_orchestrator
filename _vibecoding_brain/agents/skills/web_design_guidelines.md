## Skill: Web Design Guidelines (Modern SaaS)
> Injected for: creative_brain, ui_ux_tester on FRONTEND / FULLSTACK / DESIGN tasks.
> Opinionated toward the Linear/Vercel/Stripe aesthetic that Montrroase targets.

### Design Philosophy
Montrroase targets the premium SaaS tier: tools like Linear, Vercel, Stripe, Notion.
The common thread is **restraint** -- fewer colors, tighter spacing, faster animations, denser information.

### Core Principles

**1. Information Density First**
- SaaS users are power users. Don't waste their screen space.
- Tables > cards for list views. Compact rows (36-44px) by default.
- Sidebars show navigation, not decoration.
- Every pixel should serve a purpose.

**2. Progressive Disclosure**
- Show the 80% case by default. Advanced options behind expandable sections or settings.
- Modals for focused tasks. Slide-overs for detail panels.
- Tooltips for secondary information. Never hide critical actions.

**3. Neutral Foundation, Selective Color**
- Gray surfaces establish hierarchy. Color is reserved for meaning.
- Status colors (green/yellow/red/blue) always semantic -- never decorative.
- Brand color < 10% of visible area. Used for primary actions and active states only.

**4. Typography Does the Heavy Lifting**
- Size and weight create hierarchy -- not color or decoration.
- 14px body text (not 16px). Dense but readable.
- Two font weights for most UI: 400 (body) and 500 (labels/emphasis).
- 600 for section headers. 700 reserved for page titles only.

**5. Borders Over Shadows**
- 1px borders define card edges. Shadows reserved for elevated elements (dropdowns, modals).
- Consistent border color across the app (one token, not per-component).
- No double borders (border on card inside bordered container).

**6. Speed is a Feature**
- Optimistic UI: show result immediately, reconcile with server after.
- Animations under 300ms. Most interactions under 200ms.
- Skeleton loaders for initial load. Subtle spinners for background fetching.
- No blocking spinners for mutations -- use optimistic updates.

### Responsive Design Breakpoints
```
Mobile:   < 768px   -- single column, bottom nav, full-width cards
Tablet:   768-1024px -- collapsed sidebar, 2-column where needed
Desktop:  > 1024px   -- full sidebar, multi-column layouts
Wide:     > 1440px   -- max-width container (1280px), centered
```

Rules:
- Mobile-first is NOT required for internal SaaS tools -- desktop-first is acceptable
- Sidebar collapses to icon-only on tablet, hidden on mobile
- Tables become card lists on mobile (not horizontal scroll)
- Modals become full-screen on mobile (< 768px)

### Dark Mode Considerations
- If implementing dark mode: invert surface hierarchy (dark bg, lighter cards)
- Use CSS custom properties for all colors -- never hardcoded hex in components
- Test contrast ratios in both modes
- `prefers-color-scheme` media query for system preference
- Provide explicit toggle (don't rely on system preference alone)

### Micro-Interaction Patterns

**Hover States**
- Every interactive element MUST have a visible hover state
- Buttons: subtle bg darken (100ms transition)
- Rows: bg highlight to gray-100 (50-75ms)
- Links: underline or color shift
- Cards (if clickable): subtle lift (y: -2px) + shadow increase

**Focus States**
- `focus-visible` ring on all interactive elements (not `focus`)
- Ring: 2px offset, accent color, 150ms transition
- Never `outline: none` without a visible replacement

**Loading States**
- `isLoading` (first load): skeleton placeholders matching content shape
- `isFetching` (refetch): subtle indicator, content stays visible
- Mutations: optimistic update, revert on error with toast

**Empty States**
- Illustration or icon (subtle, not colorful)
- Clear headline: what this area is for
- Description: why it's empty
- Primary CTA: how to add the first item
- Never leave an area completely blank

**Error States**
- Inline errors below the relevant field (forms)
- Toast for transient errors (network, timeout)
- Full-page error for critical failures (auth, 500)
- Always show: what went wrong + what the user can do about it
- Never show raw error messages or stack traces

### Data Visualization (Recharts)
- Use Montrroase color tokens for chart colors
- Label axes clearly. Include units.
- Tooltips on hover with formatted values
- Responsive: charts resize with container
- Accessibility: provide data table alternative for screen readers
- No 3D effects, no excessive gradients, no decorative chart elements

### Performance-Conscious Design
- Lazy load below-fold content and heavy components
- Use `loading="lazy"` on images
- Virtualize long lists (> 50 items) with react-window or similar
- Defer non-critical animations (intersection observer)
- Prefer CSS transitions for simple hover/focus states (cheaper than Framer Motion)
- Use Framer Motion only for complex multi-step or layout animations
