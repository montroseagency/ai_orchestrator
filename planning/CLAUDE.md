# Montrroase Agency Platform (Claude Context Guidelines)

You are an autonomous AI working on the Montrroase Next.js + Django platform. 

## Architectural Context
- **Backend:** Django (`server/` and `server/api/`). Python APIs.
- **Frontend:** Next.js (`client/`). React, TypeScript.
- **Microservices:** Custom agents and integrations under `services/`.
- **Planning & Strategy:** Always check `planning/project-manifest.md` for current execution splits and project priorities.

## 🛑 STRICT SEARCH PROHIBITION (SAVE TOKENS) 🛑
**DO NOT blindly search, `grep`, or use heavy MCP tools (`search_codebase`) to blindly hunt for project structure!** 
To navigate the codebase instantly and accurately, use our static repository map strategy:

### How you MUST navigate:
1. First, search or read `repomap.txt` (located at the root of the project). This is a map of ALL active files and their functions/classes/exports.
2. Second, use the `get_file` MCP or read the exact file line ranges you identified in `repomap.txt`.
3. Only if a specific logic question cannot be answered by `repomap.txt`, should you fall back on `search_codebase` semantic RAG.

## UI/UX Guidelines & Component Ecosystem
We strictly adhere to the `Ui-Ux-Pro-Max` design language. Always consult `planning/project-manifest.md` for UI styling alignment, and prioritize clean, functional, high-end agency designs for all frontend implementations.

### 🛑 STOP! DO NOT REINVENT THE WHEEL 🛑
Before building a new UI element, check if it already exists here. We have a massive repository of pre-built, reusable components and libraries. **Do not create custom modal implementations, custom drag-and-drop logic, or custom complex inputs from scratch.**

#### 1. Pre-Installed Third-Party Libraries (`client/package.json`)
- **Drag and Drop:** `@dnd-kit/core`, `@dnd-kit/sortable`, `@dnd-kit/utilities` 
- **Charts / Data Viz:** `chart.js`, `react-chartjs-2`, `recharts`
- **Animations:** `framer-motion`
- **Icons:** `lucide-react`
- **Toast Notifications:** `sonner`
- **Code/Rich Text Display:** `prism-react-renderer`
- **Image Editing:** `react-image-crop`

#### 2. Local Reusable UI Components (`client/components/ui/`)
- **Layout & Overlays:** `modal.tsx`, `drawer.tsx`, `bottom-sheet.tsx`, `Surface.tsx`, `card.tsx`
- **Navigation:** `tabs.tsx`, `pagination.tsx`
- **Forms & Inputs:** `button.tsx`, `input.tsx`, `textarea.tsx`, `select.tsx`, `checkbox.tsx`, `radio.tsx`, `date-picker.tsx`, `time-picker.tsx`, `ImageUpload.tsx`, `file-upload.tsx`, `form.tsx`
- **Advanced State/Data:** `DataTable.tsx`, `CodeBlock.tsx` (Syntax highlighted), `ImageSlider.tsx`
- **Feedback:** `spinner.tsx`, `skeleton.tsx`, `alert.tsx`, `tooltip.tsx`, `badge.tsx`, `progress.tsx`, `empty-state.tsx`, `InlineError.tsx`, `ErrorModal.tsx`
- **Context:** `context-menu.tsx`, `dropdown.tsx`

#### 3. Core Common Components (`client/components/common/`)
- `Avatar.tsx` and `AvatarUpload.tsx`
- `error-boundary.tsx`, `error-message.tsx`, `success-message.tsx`
- `stat-card.tsx`, `pricing-card.tsx`, `portfolio-card.tsx`, `testimonial-card.tsx`
- `confirmation-modal.tsx`
