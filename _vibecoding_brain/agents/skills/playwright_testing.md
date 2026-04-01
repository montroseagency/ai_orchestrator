## Skill: Playwright Testing Patterns
> Conditionally injected for: UI/UX Tester — only when Config.PLAYWRIGHT_SERVER_URL is set.

### Connection
Server URL available at: `{PLAYWRIGHT_SERVER_URL}`

Use Playwright's CDP connection to connect to the running dev server before running assertions.

### Priority Test Sequence (run in order)

1. **Render check** — navigate to the component/page URL; assert no JS errors in console
2. **Keyboard navigation** — Tab through all interactive elements; verify focus ring is visible on each
3. **Mobile viewport** — resize to 375×812; verify no horizontal scroll; verify touch targets ≥ 44×44px
4. **State coverage** — trigger each state: Loading (intercept API), Empty (empty response), Error (500 response)
5. **Primary interaction** — click the main CTA; verify optimistic UI responds before server confirms
6. **Animation completion** — verify transitions reach their final state (no stuck half-opacity or mid-translate)
7. **Screen reader tree** — call `page.accessibility.snapshot()` and verify landmark roles and button labels are coherent

### Montrroase Selector Conventions
Prefer semantic selectors over CSS/testid:
- Buttons: `getByRole('button', { name: 'exact label' })`
- Form inputs: `getByLabel('Field name')`
- Navigation links: `getByRole('link', { name: 'exact text' })`
- Headings: `getByRole('heading', { name: 'Page title', level: 1 })`
- `data-testid` only when semantic selectors are impossible

### Key Assertion Patterns
```python
# No console errors
errors = []
page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
# ...navigate and interact...
assert errors == [], f"Console errors: {errors}"

# Focus management after modal open
await page.click('[aria-label="Open settings"]')
focused_label = await page.evaluate("document.activeElement.getAttribute('aria-label')")
assert focused_label is not None, "Focus did not move into modal"

# Mobile: no horizontal scroll
await page.set_viewport_size({"width": 375, "height": 812})
overflow = await page.evaluate("document.body.scrollWidth > document.body.clientWidth")
assert not overflow, "Horizontal scroll present on mobile"

# Touch target size
small_targets = await page.evaluate("""
  [...document.querySelectorAll('button, a, [role=button]')]
    .filter(el => { const r = el.getBoundingClientRect(); return r.width < 44 || r.height < 44; })
    .map(el => el.outerHTML.slice(0, 80))
""")
assert small_targets == [], f"Touch targets too small: {small_targets}"
```

### Report Format
Prepend a `## Playwright Results` section to the test output before the main checklist:
```markdown
## Playwright Results
- Render: ✅ / ❌ [error message]
- Keyboard nav: ✅ / ❌ [what failed]
- Mobile (375px): ✅ / ❌ [overflow / small targets]
- State coverage: ✅ / ❌ [which state failed]
- Primary interaction: ✅ / ❌
- Animations: ✅ / ❌
- Screen reader tree: ✅ / ❌ [missing labels]
```

If Playwright server is unreachable, note `## Playwright Results: Server unavailable — skipped` and continue with static code review only.
