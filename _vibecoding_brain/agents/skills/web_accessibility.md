## Skill: Web Accessibility (WCAG 2.1 AA)
> Always injected for: UI/UX Tester on FRONTEND and FULLSTACK tasks.

### Contrast Ratios (WCAG AA — non-negotiable)
- Normal text (< 18px or < 14px bold): minimum **4.5:1**
- Large text (≥ 18px or ≥ 14px bold): minimum **3:1**
- UI components / graphical objects (icons, borders of inputs): minimum **3:1**
- Montrroase token audit: `zinc-900 on white ✓` | `zinc-600 on white ✓` | `zinc-400 on white ✗` (decorative use only)

### ARIA Requirements
- Icon-only buttons: `aria-label="[action verb]"` on the button + `aria-hidden="true"` on the icon itself
- Decorative images: `alt=""` (empty string, not missing attribute)
- Meaningful images: `alt="[description of what it shows]"` — never filename or "image"
- Dialog/modal: `role="dialog"` + `aria-modal="true"` + `aria-labelledby` pointing to the visible title element
- Live regions (real-time data updates): `aria-live="polite"` — use `"assertive"` only for urgent errors
- Status messages appearing without focus change: `role="status"` or `aria-live="polite"`
- Loading spinners: `aria-label="Loading"` + `role="status"`

### Keyboard Navigation
- Tab order must match visual reading order — never use `tabindex` > 0
- All interactive elements (buttons, links, inputs, selects) reachable via Tab
- Activated via Enter (links, buttons) or Space (buttons, checkboxes) — both must work
- Escape closes all modal, dialog, dropdown, and popover overlays
- Arrow keys navigate within composite widgets: menus (up/down), radio groups (up/down), tabs (left/right)
- Skip-to-main-content link must be the first focusable element on page-level components

### Focus Management
- Modal opens → focus moves immediately to first focusable element inside modal
- Modal closes → focus returns to the element that triggered it
- Item deleted from list → focus moves to next item; if last item, to parent or previous item
- Tab panel switched → focus stays on the active tab (not moved into panel content)
- Toast/notification appearing → do NOT steal focus; it is non-interactive
- Focus ring: `focus-visible:ring-2 ring-offset-2 ring-accent` on every interactive element — **never** `outline: none` without a visible replacement

### Forms
- Every `<input>`, `<select>`, `<textarea>` must have a `<label>` with matching `for`/`id` pair — placeholder text alone is not a label
- Error messages linked to their input: `aria-describedby="error-id"` on the input
- Required fields: `aria-required="true"` in addition to visual asterisk
- Inline errors appear below the field they belong to, not only at the top of the form
- Fieldsets with `<legend>` for grouped radio/checkbox controls

### Reduced Motion
- ALL Framer Motion animations must respect `prefers-reduced-motion`:
  ```tsx
  const prefersReducedMotion = useReducedMotion()
  transition={{ duration: prefersReducedMotion ? 0 : 0.2 }}
  ```
- Use Framer Motion's `useReducedMotion()` hook — do not query the media query manually
- Animations that convey meaning (progress, state change) must have a non-animated fallback
