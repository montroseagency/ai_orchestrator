# Section 10: TimeBlockCard

## Overview

`TimeBlockCard` is the absolutely-positioned card component rendered inside `DayColumn` for each scheduled time block. It contains two independent `useDraggable` instances — one for moving the block and one for resizing it — plus a click handler that opens the existing `TimeBlockEditor` modal. This section is in **Batch 3** and can be implemented in parallel with sections 06, 07, 08, and 12 once sections 01, 02, and 04 are complete.

---

## Dependencies

| Dependency | What is needed |
|---|---|
| `section-01-test-utils` | `createMockTimeBlock()`, `renderWithQuery()`, `mockUseSchedulingEngine()` |
| `section-02-shared-utils` | `getEventStyle()` from `timeUtils.ts` |
| `section-04-data-hook` | `useSchedulingEngine` hook signature (activeId, mutations) |

`TimeBlockCard` does **not** call any mutations itself. It receives `activeId` as a prop from `SchedulingEngine` and exposes two draggable handles whose drag data is consumed by `SchedulingEngine.onDragEnd`. It also receives an `onEdit` callback prop rather than calling the hook directly, keeping it presentational.

---

## File to Create

```
client/components/portal/calendar/TimeBlockCard.tsx
```

Test file:

```
client/components/portal/calendar/TimeBlockCard.test.tsx
```

---

## Tests First

Write the following tests before implementing the component. Use `createMockTimeBlock()` from `client/test-utils/scheduling.tsx` and stub `@dnd-kit/core` as described in the test utils section.

All tests go in `client/components/portal/calendar/TimeBlockCard.test.tsx`.

### Rendering

- **renders block title and client name** — given a mock time block, the card shows `block.title` and `block.client_name`
- **renders with `position: absolute`** — the card root element has `style.position === 'absolute'`
- **top and height come from `getEventStyle`** — given `start_time="07:00"`, `end_time="08:00"`, `startHour=6`, `hourHeight=60`, the card renders with `top: 60px` and `height: 60px`
- **left border color matches `block.color`** — the card element has an inline `borderLeftColor` matching `block.color`
- **background is block color at 10% opacity** — check `backgroundColor` is the hex color at `1a` opacity (e.g., `#6366F11a` or equivalent rgba)
- **client/category text is rendered in `text-xs`** — `task_category_detail.name` (or `client_name` fallback) appears in a small text element

### Active / Ghost States

- **when `activeId === 'move-{block.id}'`, card has opacity 0.5 and dashed border** — pass the matching `activeId` prop; assert `style.opacity === '0.5'` and the border style contains `dashed`
- **when `activeId` is a different id, card renders at full opacity** — pass a non-matching `activeId`; assert no opacity reduction
- **when `activeId === 'resize-{block.id}'`, card has accent border color** — assert a CSS class or inline style that signals the resize-active state

### Resize Handle

- **resize handle div is present at the bottom of the card** — query by `data-testid="resize-handle"` (or role); assert it exists
- **resize handle has `cursor-ns-resize` style** — assert `cursor: ns-resize` on the handle element
- **`onPointerDown` on resize handle calls `stopPropagation`** — create a mock event with `stopPropagation` as a `vi.fn()`, fire `pointerdown` on the handle, assert `stopPropagation` was called
- **resize handle is positioned at the bottom 6px of the card** — assert `bottom: 0`, `height: 6px` (or equivalent Tailwind classes)

### Click to Edit

- **clicking the card body calls `onEdit` with the block** — fire a `click` on the card body (not the resize handle), assert the `onEdit` prop was called with the block object
- **clicking the resize handle does NOT call `onEdit`** — fire a `click` on the resize handle element; assert `onEdit` was not called

### Collision Layout Props

- **`left` and `width` props from collision layout are applied** — pass `left="50%"` and `width="50%"` as props; assert `style.left === '50%'` and `style.width === '50%'`
- **defaults to `left="0%"` and `width="100%"` when no collision layout props given** — omit layout props; assert the defaults

---

## Component Specification

### Props Interface

```typescript
interface TimeBlockCardProps {
  block: AgentTimeBlock
  activeId: string | null         // from SchedulingEngine state
  startHour: number               // layout constant (6)
  hourHeight: number              // layout constant (60)
  left?: string                   // from getSideBySideLayout, default "0%"
  width?: string                  // from getSideBySideLayout, default "100%"
  onEdit: (block: AgentTimeBlock) => void
}
```

### Two Draggable Instances

The card sets up two `useDraggable` calls from `@dnd-kit/core`:

**Move draggable** — applied to the card body:
```typescript
useDraggable({
  id: `move-${block.id}`,
  data: { type: 'move', blockId: block.id, block }
})
```
The returned `listeners` and `attributes` spread onto the card's root `<div>`. The `transform` from `isDragging` is **not** applied to the card itself (it stays as the ghost-in-place); only the `<DragOverlay>` in `SchedulingEngine` shows the floating preview.

**Resize draggable** — applied to the bottom handle only:
```typescript
useDraggable({
  id: `resize-${block.id}`,
  data: { type: 'resize', blockId: block.id, originalEndTime: block.end_time }
})
```
The resize handle element must call `e.stopPropagation()` in its `onPointerDown` to prevent the card-level move drag from activating when the user grabs the resize zone.

### Positioning

Call `getEventStyle(block.start_time, block.end_time, startHour, hourHeight)` to get `{ top, height }` in pixels. Combine with the `left` and `width` collision layout props:

```typescript
const { top, height } = getEventStyle(block.start_time, block.end_time, startHour, hourHeight)
const style = {
  position: 'absolute' as const,
  top,
  height,
  left: left ?? '0%',
  width: width ?? '100%',
  borderLeftColor: block.color,
  backgroundColor: `${block.color}1a`,   // 10% opacity hex shorthand
}
```

### Active State Logic

Determine visual state based on `activeId`:

```typescript
const isMoving  = activeId === `move-${block.id}`
const isResizing = activeId === `resize-${block.id}`
```

- `isMoving`: add `opacity-50` (or `style.opacity = 0.5`) and `border-dashed border-2` on the card root
- `isResizing`: replace `border-l-4` left border with the project's `--color-accent-light` CSS variable (or Tailwind `border-indigo-400`); rest of card is unchanged

### Resize Handle

```tsx
<div
  data-testid="resize-handle"
  style={{ position: 'absolute', bottom: 0, left: 0, width: '100%', height: 6, cursor: 'ns-resize' }}
  onPointerDown={(e) => {
    e.stopPropagation()
    resizeListeners?.onPointerDown?.(e)
  }}
  {...resizeAttributes}
/>
```

The `resizeListeners` object from the second `useDraggable` call should be spread here but with the `onPointerDown` manually wrapped to ensure `stopPropagation` fires before dnd-kit's listener.

### Click to Edit

Attach an `onClick` handler to the card body that calls `onEdit(block)`. The resize handle should call `e.stopPropagation()` on click as well to prevent the card's `onClick` from firing. This ensures clicking in the resize zone does not open the editor.

### Layout Classes (Tailwind)

The card root `<div>` uses:
```
rounded-lg p-2 text-sm border-l-4 overflow-hidden cursor-grab select-none
```

Title: `font-medium text-text truncate`

Subtitle (client / category): `text-xs text-secondary truncate mt-0.5`

---

## Visual Reference

```
┌────────────────────────────────────┐
│▌ Title text (truncated)            │
│  client · category                 │
│                                    │
│                                    │
├────────────────────────────────────┤ ← resize handle (6px, cursor: ns-resize)
```

The colored left border (`▌`) is `border-l-4` with `borderLeftColor: block.color`. Background is `block.color` at 10% hex opacity.

---

## Integration Notes

`TimeBlockCard` does not import or call `useSchedulingEngine` directly. It is a controlled presentational component. The caller (`DayColumn`, which is built in section 09) is responsible for:

1. Calling `getOverlapGroups` + `getSideBySideLayout` to compute `left`/`width` per block
2. Passing `activeId` down from `SchedulingEngine`
3. Passing an `onEdit` callback that opens `TimeBlockEditor`

The `TimeBlockEditor` component already exists in the codebase. Do not modify it. Open it by lifting its open/block state into `DayColumn` or `SchedulingEngine` (to be decided in section 09).

---

## Edge Cases

- **Zero-duration or very short blocks** — if `height < 24px`, suppress the subtitle text to avoid overflow; show title only
- **Block color undefined or empty** — fall back to the project's `--color-accent-light` CSS variable; never render with no color
- **Hidden blocks from collision layout** — `DayColumn` will not render `TimeBlockCard` for blocks marked `hidden` by `getSideBySideLayout`; this component does not need to handle that case
- **Block extending past `endHour`** — `getEventStyle` will return a `height` that would overflow the column container; the parent `DayColumn` clips via `overflow: hidden`; the card itself does not need to self-clip
