# Modal Building Guide — Montrroase
> Read this before creating or modifying ANY modal in the project.
> Last updated: 2026-04-04

## Imports

```tsx
// Always import from these paths — never build custom overlays
import { Modal, ModalHeader, ModalTitle, ModalDescription, ModalContent, ModalFooter } from '@/components/ui/modal';
import { SimpleModal } from '@/components/ui/modal'; // convenience wrapper
import { Button } from '@/components/ui/button';

// Icons — ALWAYS Phosphor, NEVER Lucide
import { X, Plus, Trash, MagnifyingGlass, WarningCircle, CheckCircle, Info } from '@phosphor-icons/react';
```

## Component API

### Modal (base container)
```tsx
<Modal
  isOpen={boolean}       // controls visibility + animation
  onClose={() => void}   // called on ESC, overlay click, close button
  size="sm | md | lg | xl | full"  // default: "md"
  className=""           // optional extra classes on the panel
>
```
**Built-in features (you get these for free):**
- Framer Motion entrance/exit animations
- Portal rendering to `document.body`
- Focus trap (Tab/Shift+Tab cycling)
- Scroll lock (body doesn't scroll behind modal)
- ESC key to close
- `role="dialog"` + `aria-modal="true"`
- `aria-labelledby` auto-linked to ModalTitle
- `aria-describedby` auto-linked to ModalDescription
- `useReducedMotion` support

**Sizes:**
| Size | Width | Use for |
|------|-------|---------|
| `sm` | 384px | Confirmations, alerts, simple pickers |
| `md` | 512px | Standard forms, account settings (DEFAULT) |
| `lg` | 672px | Multi-section forms, detail views |
| `xl` | 896px | Data tables, previews, multi-step wizards |
| `full` | 80rem | Full editors (quote builder, etc.) |

### ModalHeader
```tsx
<ModalHeader onClose={onClose} className="">
  {/* children are optional — if empty, just renders close button */}
  <ModalTitle>Title Text</ModalTitle>
  <ModalDescription>Optional subtitle</ModalDescription>
</ModalHeader>
```
- White background (transparent) — NEVER add a colored bg
- Close button auto-rendered when `onClose` is provided (or pulled from Modal context)
- Close button: 32x32, rounded-[6px], Phosphor `X` icon at size 18 weight bold

### ModalTitle
```tsx
<ModalTitle>Create New Client</ModalTitle>
```
- Renders as `<h2>`, 16px/600 weight, `text-primary`
- Auto-gets `id` from Modal context for `aria-labelledby`

### ModalDescription
```tsx
<ModalDescription>Fill in the details below to add a client.</ModalDescription>
```
- Renders as `<p>`, 14px/400 weight, `text-secondary`
- Auto-gets `id` from Modal context for `aria-describedby`

### ModalContent
```tsx
<ModalContent className="">
  {/* scrollable body area */}
</ModalContent>
```
- `px-6 py-4`, overflow-y-auto with thin scrollbar, flex-1

### ModalFooter
```tsx
<ModalFooter>
  <Button variant="outline" onClick={onClose}>Cancel</Button>
  <Button variant="primary" onClick={handleSubmit}>Create</Button>
</ModalFooter>
```
- Right-aligned buttons with gap-2
- `border-t border-border bg-surface-subtle rounded-b-[12px]`
- Cancel/secondary button first (left), primary action last (right)

### SimpleModal (convenience wrapper)
```tsx
<SimpleModal title="Edit Item" onClose={onClose} size="md">
  {/* children go into ModalContent */}
</SimpleModal>
```
- Always renders with `isOpen={true}` — parent controls visibility via conditional rendering
- Good for simple modals. For complex modals with footers, use the full compound API.

---

## Patterns

### 1. Standard Form Modal
```tsx
export function CreateItemModal({ isOpen, onClose, onSuccess }: Props) {
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await ApiService.createItem(data);
      onSuccess();
      onClose();
    } catch (err) {
      // handle error
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="md">
      <ModalHeader onClose={onClose}>
        <ModalTitle>Create Item</ModalTitle>
        <ModalDescription>Add a new item to the system.</ModalDescription>
      </ModalHeader>

      <ModalContent>
        <form id="create-item-form" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-secondary mb-1">
                Name <span className="text-status-error">*</span>
              </label>
              <input
                className="w-full px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-accent focus:border-transparent bg-surface text-primary"
              />
            </div>
          </div>
        </form>
      </ModalContent>

      <ModalFooter>
        <Button variant="outline" onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          variant="primary"
          type="submit"
          form="create-item-form"
          isLoading={loading}
        >
          Create Item
        </Button>
      </ModalFooter>
    </Modal>
  );
}
```

### 2. Confirmation Modal (use the built-in)
```tsx
import { ConfirmationModal } from '@/components/common/confirmation-modal';

<ConfirmationModal
  isOpen={showConfirm}
  onConfirm={handleDelete}
  onCancel={() => setShowConfirm(false)}
  title="Delete this client?"
  description="This will permanently remove the client and all their data."
  confirmLabel="Delete Client"
  cancelLabel="Keep"
  danger={true}
  isLoading={deleting}
/>
```

### 3. Error Modal (use the built-in)
```tsx
import ErrorModal from '@/components/ui/ErrorModal';

<ErrorModal
  isOpen={!!error}
  onClose={() => setError(null)}
  title="Upload Failed"
  message={error}
  actionLabel="Try Again"
  onAction={retryUpload}
/>
```

### 4. Modal with Icon Badge in Header
```tsx
<ModalHeader onClose={onClose}>
  <div className="flex items-center gap-3">
    <div className="w-9 h-9 rounded-lg bg-surface-muted flex items-center justify-center text-accent">
      <Users size={18} weight="duotone" />
    </div>
    <div>
      <ModalTitle>Assign Agent</ModalTitle>
      <ModalDescription>Choose an agent for this client.</ModalDescription>
    </div>
  </div>
</ModalHeader>
```

### 5. Multi-Step Wizard Modal
```tsx
<Modal isOpen={isOpen} onClose={onClose} size="xl">
  <ModalHeader onClose={onClose}>
    <ModalTitle>Create Campaign</ModalTitle>
    <ModalDescription>Step {step} of {totalSteps}</ModalDescription>
  </ModalHeader>

  <ModalContent>
    {/* Progress bar */}
    <div className="flex gap-1 mb-6">
      {Array.from({ length: totalSteps }).map((_, i) => (
        <div key={i} className={`h-1 flex-1 rounded-full ${i <= step ? 'bg-accent' : 'bg-surface-muted'}`} />
      ))}
    </div>

    {step === 0 && <StepOne />}
    {step === 1 && <StepTwo />}
  </ModalContent>

  <ModalFooter>
    {step > 0 && (
      <Button variant="outline" onClick={() => setStep(s => s - 1)}>Back</Button>
    )}
    <Button variant="outline" onClick={onClose}>Cancel</Button>
    {step < totalSteps - 1 ? (
      <Button variant="primary" onClick={() => setStep(s => s + 1)}>Next</Button>
    ) : (
      <Button variant="primary" onClick={handleSubmit} isLoading={loading}>Create</Button>
    )}
  </ModalFooter>
</Modal>
```

### 6. Preview/Detail Modal
```tsx
<Modal isOpen={isOpen} onClose={onClose} size="xl">
  <ModalHeader onClose={onClose}>
    <ModalTitle>{asset.name}</ModalTitle>
  </ModalHeader>

  <ModalContent>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* Preview pane */}
      <div className="bg-surface-subtle rounded-lg flex items-center justify-center min-h-[300px]">
        <img src={asset.url} alt={asset.name} className="max-w-full max-h-[400px] object-contain" />
      </div>
      {/* Metadata pane */}
      <div className="space-y-4">
        <div>
          <span className="text-sm text-muted">Type</span>
          <p className="text-sm text-primary font-medium">{asset.type}</p>
        </div>
      </div>
    </div>
  </ModalContent>

  <ModalFooter>
    <Button variant="ghost" size="sm" onClick={onClose}>Close</Button>
    <Button variant="primary" size="sm" onClick={handleSave} isLoading={saving}>
      Save Changes
    </Button>
  </ModalFooter>
</Modal>
```

---

## Styling Rules

### Colors (design tokens ONLY)
```
Text:       text-primary | text-secondary | text-muted | text-accent | text-status-error | text-status-success | text-status-warning
Background: bg-surface | bg-surface-subtle | bg-surface-muted | bg-accent | bg-accent-light
Border:     border-border
Status bg:  bg-[#FEE2E2] (error) | bg-[#DCFCE7] (success) | bg-[#FEF9C3] (warning) | bg-accent-light (info)
```

**NEVER use:** `bg-gray-*`, `text-gray-*`, `border-gray-*`, `bg-red-*`, `bg-blue-*`, `bg-purple-*`, `text-slate-*`, etc.

### Form Inputs Inside Modals
```
className="w-full px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-accent focus:border-transparent bg-surface text-primary"
```

### Labels
```
className="block text-sm font-medium text-secondary mb-1"
```

### Helper Text
```
className="text-xs text-muted mt-1"
```

### Error Messages (inline)
```
className="text-sm text-status-error mt-1"
```

### Error Alert Box
```tsx
{error && (
  <div className="mb-4 p-3 bg-[#FEE2E2] border border-border rounded-lg text-status-error text-sm flex items-center gap-2">
    <WarningCircle size={16} weight="fill" />
    {error}
  </div>
)}
```

### Selected State (pills, cards, toggles)
```
// Selected:   border-accent bg-accent-light text-accent
// Unselected: border-border bg-surface text-secondary hover:border-secondary
```

---

## Icons

**Library:** `@phosphor-icons/react` — NEVER `lucide-react`

**Common mappings (if migrating from Lucide):**
| Lucide | Phosphor |
|--------|----------|
| `X` | `X` |
| `Plus` | `Plus` |
| `Trash2` | `Trash` |
| `Edit2` / `Edit3` | `PencilSimple` |
| `Search` | `MagnifyingGlass` |
| `ChevronLeft` / `ChevronRight` | `CaretLeft` / `CaretRight` |
| `ChevronDown` / `ChevronUp` | `CaretDown` / `CaretUp` |
| `AlertCircle` | `WarningCircle` |
| `CheckCircle` | `CheckCircle` |
| `Eye` / `EyeOff` | `Eye` / `EyeSlash` |
| `Loader2` | `CircleNotch` (with `className="animate-spin"`) |
| `Download` | `DownloadSimple` |
| `Upload` | `UploadSimple` |
| `Users` | `Users` or `UsersThree` |
| `ArrowRight` / `ArrowLeft` | `ArrowRight` / `ArrowLeft` |
| `Save` | `FloppyDisk` |
| `Copy` | `Copy` |
| `Folder` / `FolderOpen` | `FolderSimple` / `FolderOpen` |
| `Globe` | `GlobeSimple` |
| `Calendar` | `CalendarBlank` |
| `Phone` / `PhoneOff` | `Phone` / `PhoneDisconnect` |
| `Video` | `VideoCamera` |
| `Instagram` | `InstagramLogo` |
| `Facebook` | `FacebookLogo` |
| `Youtube` | `YoutubeLogo` |
| `Twitter` | `XLogo` |
| `Linkedin` | `LinkedinLogo` |
| `Sparkles` | `Sparkle` |
| `RefreshCw` | `ArrowsClockwise` |
| `GripVertical` | `DotsSixVertical` |

**Usage:**
```tsx
// Phosphor uses size prop, not className for sizing
<MagnifyingGlass size={16} />           // body text companion
<Plus size={20} weight="bold" />         // toolbar/button
<WarningCircle size={20} weight="fill" /> // status icon with filled style
```

---

## NEVER Do These

1. **NEVER build a custom overlay** — no `<div className="fixed inset-0 bg-black...">`. Use `<Modal>`.
2. **NEVER use a colored modal header** — no `bg-accent text-white` on the header. White only.
3. **NEVER import from `lucide-react`** — Phosphor icons only.
4. **NEVER use `font-bold`** — max weight is `font-semibold` (600). Only page h1 headings use 700.
5. **NEVER use raw Tailwind colors** — no `bg-gray-100`, `text-slate-500`, `border-gray-300`.
6. **NEVER use `bg-gradient-to-*`** — solid colors from design tokens only.
7. **NEVER use `rounded-2xl`** uniformly — modals are `rounded-[12px]` (handled by base Modal).
8. **NEVER use inline `style={{}}` for layout** — Tailwind classes only (exception: `boxShadow` and `maxHeight` on the Modal panel itself).
9. **NEVER skip `isOpen` prop** — modals must be controlled by parent state, not conditional rendering of the modal component itself.
10. **NEVER put a `<form>` around the entire modal** — put the form inside `<ModalContent>` and use `form="form-id"` on the submit button in `<ModalFooter>`.

---

## Hooks Available

### useFocusTrap (auto-used by Modal)
```ts
import { useFocusTrap } from '@/lib/hooks/useFocusTrap';
useFocusTrap(containerRef, isActive); // traps Tab/Shift+Tab inside container
```

### useScrollLock (auto-used by Modal)
```ts
import { useScrollLock } from '@/lib/hooks/useScrollLock';
useScrollLock(isLocked); // locks body scroll, preserves position
```

---

## Button Variants Reference
```tsx
<Button variant="primary">Create</Button>      // blue accent bg, white text
<Button variant="outline">Cancel</Button>       // border, transparent bg
<Button variant="ghost">Skip</Button>           // no border, transparent
<Button variant="danger">Delete</Button>        // red bg, white text
<Button variant="success">Approve</Button>      // green bg, white text
<Button size="sm">Small</Button>                // 32px height
<Button size="md">Medium</Button>               // 36px height (default)
<Button size="lg">Large</Button>                // 40px height
<Button isLoading={true}>Saving...</Button>      // shows spinner, disables
```
