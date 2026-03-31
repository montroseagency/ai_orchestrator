# `components/` Deep Audit

> **Scope**: Every folder and loose file inside `client/components/`. All file sizes and counts are exact. Pathologies are numbered for reference.

---

## Full Inventory

```
components/                             25 entries total
│
│ ── LOOSE FILES (7) ─────────────────────────────────────────────
├── AboutSectionOptimized.tsx           5.9 KB   [P1]
├── QuestionnaireWizard.tsx            10.3 KB   [P1]
├── ServiceSelector.tsx                 4.0 KB   [P1]
├── ServiceSwitcher.tsx                 6.0 KB   [P1]
├── image-carousel.tsx                 10.1 KB   [P1]
├── interactive-glow-background.tsx     3.5 KB   [P1]
├── masonry-parallax-grid.tsx          15.7 KB   [P1]
│
│ ── ROLE-SCOPED FOLDERS ────────────────────────────────────────
├── admin/                              2 files  [P2]
│   ├── AddClientModal.tsx             20.9 KB
│   └── TransferAgentModal.tsx         11.9 KB
│
├── agent/                              3 sub-dirs
│   ├── dashboard/                      9 files (overview widgets)
│   └── scheduling/                    14 files (CommandCenter, DaySchedule, etc.)
│
├── client/                             1 file!  [P3]
│   └── PhaseCountdownCard.tsx          4.1 KB
│
│ ── FEATURE-SCOPED FOLDERS ─────────────────────────────────────
├── auth/                               2 files
│   ├── AuthForm.tsx                   39.5 KB
│   └── AuthModal.tsx                  26.1 KB
│
├── call/                              10 files  [P4]
│   ├── AnimatedStats.tsx               3.3 KB   <- product marketing page component
│   ├── CallControls.tsx                3.1 KB   <- WebRTC runtime
│   ├── CallProvider.tsx               19.0 KB   <- WebRTC runtime (context)
│   ├── CallWindow.tsx                  4.1 KB   <- WebRTC runtime
│   ├── CapabilitiesAccordion.tsx       6.4 KB   <- product marketing page component
│   ├── FloatingCallWidget.tsx          6.4 KB   <- WebRTC runtime
│   ├── IncomingCallModal.tsx           5.2 KB   <- WebRTC runtime
│   ├── ParticipantGrid.tsx             5.2 KB   <- WebRTC runtime
│   ├── UseCasesCarousel.tsx            8.3 KB   <- product marketing page component
│   └── index.ts
│
├── developer/                          7 files  [P5]
│   ├── EnvVariablesManager.tsx        11.1 KB
│   ├── ProjectNotes.tsx                8.5 KB
│   ├── ProjectTimeline.tsx            37.0 KB   <- 37KB god component
│   ├── QuestionnaireDisplay.tsx       25.8 KB
│   ├── SnippetFolderSidebar.tsx        8.7 KB
│   ├── TaskManager.tsx                40.2 KB   <- 40KB god component
│   └── index.ts
│
├── messaging/                          4 files  [P11]
│   ├── FloatingChatWidget.tsx         10.5 KB
│   ├── MarketingChatWidget.tsx         2.4 KB
│   ├── MessagingInterface.tsx         50.4 KB   <- 50KB god component
│   └── WebsiteChatWidget.tsx           1.7 KB
│
├── profile/                            1 file!  [P3]
│   └── AgentProfileCard.tsx            4.4 KB
│
├── quotes/                            12 files
│   ├── QuoteBuilder.tsx               51.4 KB   <- 51KB god component [P6]
│   ├── QuoteLineItemForm.tsx          14.7 KB
│   └── ... (10 more)
│
├── scheduler/                          2 files  [P7]
│   ├── FaqSection.tsx                  5.9 KB   <- FAQ for /product/connect page
│   └── SimplesFaq.tsx                  4.8 KB   <- another FAQ variant
│
├── services/                           8 files  [P8]
│   ├── AnimatedCounter.tsx             1.4 KB
│   ├── AnimatedCounterOptimized.tsx    2.0 KB   <- duplicate + Optimized variant
│   ├── FeatureGrid.tsx                 1.7 KB
│   ├── FeatureGridOptimized.tsx        1.9 KB   <- duplicate + Optimized variant
│   ├── SectionHeader.tsx               2.7 KB   <- THIRD SectionHeader [P9]
│   ├── ServiceCard.tsx                 2.6 KB
│   └── ServiceCardOptimized.tsx        2.8 KB   <- duplicate + Optimized variant
│
├── settings/                           1 file!  [P3]
│   └── PushNotificationSettings.tsx    3.6 KB
│
│ ── UI-AREA FOLDERS ────────────────────────────────────────────
├── dashboard/                         24 files + 8 sub-dirs  [P10]
│   ├── sidebar.tsx                    24.1 KB
│   ├── topbar.tsx                     16.9 KB
│   ├── ManagementSidebar.tsx           8.2 KB
│   ├── CommandPalette.tsx             15.4 KB   <- feature, not a shell component
│   ├── NavGroup.tsx / breadcrumb.tsx  <- atomic utilities
│   ├── GuestTopbar.tsx / guest-sidebar.tsx <- role variants
│   ├── dashboard-grid.tsx              0 B      <- EMPTY FILE
│   ├── admin/    7 files
│   ├── client/   9 files
│   ├── billing/  5 files
│   ├── charts/   3 files
│   ├── content/  5 files
│   ├── dialogs/  4 files
│   ├── messaging/ 8 files  [P11 - competes with components/messaging/]
│   └── social/   6 files
│
├── management/                         1 sub-dir
│   └── tasks/                         14 files (the "full" task system)
│
├── portal/                             2 sub-dirs  [P12]
│   ├── calendar/                      11 files + SchedulingEngine.tsx  [P13]
│   └── crm/                           ClientDetailHub + tabs + hooks + export
│
│ ── TRULY SHARED ────────────────────────────────────────────────
├── common/                            15 files  [P14]
│
└── ui/                                37 files + 1 sub-dir
│
│ ── THE MARKETING MEGA-DUMP ─────────────────────────────────────
└── marketing/                         MIXED public website + SaaS feature  [P15]
    ├── navigation.tsx         39.6 KB <- public website MEGA-NAV (LARGEST FILE)
    ├── hero.tsx, footer.tsx, about.tsx, contact-form.tsx, testimonials.tsx, etc.
    ├── landing/  10 files     <- public website landing sections
    │
    ├── accounts/  1 file
    ├── ads-manager/ 21 files
    ├── assets/    9 files
    ├── calendar/  3 files
    ├── campaigns/ 3 files
    ├── dnd/       4 files
    ├── library/   8 files
    ├── notes/     3 files
    ├── overview/  7 files
    ├── plan/      7 files
    ├── posts/    15 files
    ├── shared/   11 files
    ├── tasks/     5 files <- conflicts with management/tasks/
    ├── templates/ 2 files
    └── widget/    5 files
```

---

## Pathology Register

### [P1] — 7 Loose Files at the Root of `components/`

| File | Size | Where it belongs |
|---|---|---|
| `AboutSectionOptimized.tsx` | 5.9 KB | `sections/` or `marketing/landing/` |
| `QuestionnaireWizard.tsx` | 10.3 KB | `features/onboarding/` |
| `ServiceSelector.tsx` | 4.0 KB | `common/` |
| `ServiceSwitcher.tsx` | 6.0 KB | `common/` |
| `image-carousel.tsx` | 10.1 KB | `ui/` |
| `interactive-glow-background.tsx` | 3.5 KB | `ui/` |
| `masonry-parallax-grid.tsx` | 15.7 KB | `ui/` or `sections/` |

`AboutSectionOptimized` has the `Optimized` suffix like the `services/` variants — it was a performance iteration where the original was never deleted.

---

### [P2] — `admin/` Has Only 2 Files While Admin UI Lives Elsewhere

`components/admin/` = 2 modals.
`components/dashboard/admin/` = 7 dashboard widgets.
`app/dashboard/admin/*/page.tsx` = 32 inline page components.

Three locations for admin UI. No rule for which to use.

---

### [P3] — Three Single-File Folders (False Intent)

| Folder | File |
|---|---|
| `client/` | `PhaseCountdownCard.tsx` |
| `profile/` | `AgentProfileCard.tsx` |
| `settings/` | `PushNotificationSettings.tsx` |

Each folder name implies a complete feature slice that was never built.

---


### [P4] — `call/` Mixes WebRTC Runtime with Product Marketing Page Components

Of the 9 components in `call/`:

**WebRTC runtime** (used in live dashboard calls):
- `CallProvider.tsx`, `CallControls.tsx`, `CallWindow.tsx`, `FloatingCallWidget.tsx`, `IncomingCallModal.tsx`, `ParticipantGrid.tsx`

**Product marketing** (used on `/product/connect/*` public pages):
- `AnimatedStats.tsx`, `CapabilitiesAccordion.tsx`, `UseCasesCarousel.tsx`

These three landing-page components have no runtime dependency on calling infrastructure. They describe the feature for prospective customers and belong in `sections/product/`.

---

### [P5] — `developer/` Has 40KB+ God Components with Zero Decomposition

- `TaskManager.tsx` — **40.2 KB** — a complete task management UI in one file
- `ProjectTimeline.tsx` — **37.0 KB** — a complete project timeline in one file
- `QuestionnaireDisplay.tsx` — **25.8 KB** — another monolith

No sub-components, no co-located tests, no sub-folders. Compare to `management/tasks/` which has 13 properly split files for similar functionality.

These files also have no sibling folder structure, meaning as sub-features are added they'll be added as new flat files in `developer/`, continuing to grow unchecked.

---

### [P6] — Five 25KB+ God Components Spread Across Unrelated Folders

| Component | Size | Location |
|---|---|---|
| `QuoteBuilder.tsx` | 51.4 KB | `quotes/` |
| `MessagingInterface.tsx` | 50.4 KB | `messaging/` |
| `TaskManager.tsx` | 40.2 KB | `developer/` |
| `navigation.tsx` | 39.6 KB | `marketing/` |
| `AuthForm.tsx` | 39.5 KB | `auth/` |
| `ProjectTimeline.tsx` | 37.0 KB | `developer/` |

Each should be decomposed. `MessagingInterface.tsx` is particularly egregious because `dashboard/messaging/` already has a properly decomposed version (8 files) — two messaging implementations coexist.

---

### [P7] — `scheduler/` Is a Ghost: It Contains Product Marketing FAQs

```
components/scheduler/
├── FaqSection.tsx      <- FAQ accordion for /product/connect/scheduler page
└── SimplesFaq.tsx      <- simpler FAQ variant
```

Zero relationship to the scheduling engine. The active scheduling engine is in `components/agent/scheduling/`. Any developer searching for scheduling components goes to the wrong place first.

---

### [P8] — `services/` Has Three Pairs of Originals + Optimized Duplicates

| Original | Optimized version |
|---|---|
| `AnimatedCounter.tsx` | `AnimatedCounterOptimized.tsx` |
| `FeatureGrid.tsx` | `FeatureGridOptimized.tsx` |
| `ServiceCard.tsx` | `ServiceCardOptimized.tsx` |

No deprecation notices, no migration comments, no tests. The `Optimized` versions were created during a performance pass but the originals were kept. New code being written cannot know which to import.

---

### [P9] — `SectionHeader` Defined in Three Separate Places

| Location | Purpose |
|---|---|
| `components/ui/SectionHeader.tsx` | Design system |
| `components/services/SectionHeader.tsx` | Services page reimplementation |
| `components/common/section.tsx` | Same concept, different name |

Whoever writes a new page section must choose between three implementations or create a fourth.

---

### [P10] — `dashboard/` Mixes Four Abstraction Levels + Contains a Ghost File

The `dashboard/` root has:

- **Shell** (sidebar, topbar, ManagementSidebar, MobileNav)
- **Atomic primitives** (NavGroup, breadcrumb, PlaceholderPage)
- **Features** (CommandPalette 15KB, ProfileIncompleteBanner)
- **Role variants** (GuestTopbar, guest-sidebar)
- **Role slices** (admin/, client/ sub-folders)
- **Feature slices** (billing/, charts/, content/, dialogs/, messaging/, social/)
- **Ghost file** (`dashboard-grid.tsx` — 0 bytes)

A developer cannot determine which level of abstraction any given component operates at without reading it. Shell components and atomic utilities sit side by side.

---

### [P11] — Two Competing Messaging Implementations

| Location | Approach | Files |
|---|---|---|
| `components/messaging/MessagingInterface.tsx` | 50KB monolith | 1 file |
| `components/dashboard/messaging/` | Properly decomposed | 8 files |

The `dashboard/messaging/` folder has two 0-byte stubs: `message-bubble.tsx` and `message-input.tsx` — a refactor that started but never completed. Both systems are active. The correct action is to designate `dashboard/messaging/` as canonical, extract bubble/input from the monolith, and delete `messaging/MessagingInterface.tsx`.

---

### [P12] — `portal/` Components Span Four Directories

The management portal is a coherent product shell. Its components live in:

1. `components/portal/calendar/` — 11 files: CalendarGrid, DayColumn, WeekGrid, SchedulingEngine
2. `components/portal/crm/` — ClientDetailHub, 4 tabs, hooks, export
3. `components/management/tasks/` — 14 files: TaskModal, TasksKanbanView, TasksListView
4. `components/dashboard/ManagementSidebar.tsx` — the sidebar

Four directories. No single entry point. No barrel export. A feature developer must know all four locations.

---

### [P13] — Two Things Named `SchedulingEngine`

- `components/portal/calendar/SchedulingEngine.tsx` (11 KB) — the calendar drag-drop renderer
- `lib/hooks/useSchedulingEngine.ts` (16.7 KB) — the scheduling data engine (hook)

Same name, two very different things. The component is not the engine used by the hook. This name collision causes immediate confusion.

---

### [P14] — `common/` Contains Feature-Specific Components

- `portfolio-card.tsx` — tied to the public portfolio page
- `pricing-card.tsx` — tied to the public pricing page
- `stat-card.tsx`, `feature-card.tsx`, `step-card.tsx` — public website visual language

These are not general-purpose utilities. They belong in `sections/` alongside the public website components. `common/` should contain only genuinely cross-cutting components like `Avatar`, `ErrorBoundary`, and `ConfirmationModal`.

---

### [P15] — `marketing/` Is Two Codebases in One Folder

The folder name `marketing/` resolves to two entirely different things:

**A) Public website marketing pages** (12 files + `landing/`):
- `navigation.tsx` (39.6 KB) — public site nav with auth
- `hero.tsx`, `footer.tsx`, `about.tsx`, `testimonials.tsx`, `pricing-section.tsx`, etc.
- These are used by `app/page.tsx` and public product pages.

**B) Agent marketing SaaS feature** (16 sub-directories):
- `ads-manager/`, `assets/`, `calendar/`, `campaigns/`, `library/`, `notes/`, `posts/`, `plan/`, `shared/`, `tasks/`, `templates/`, etc.
- These are used by `app/dashboard/agent/marketing/*` routes.

The 39KB `navigation.tsx` (a public-facing authentication-aware mega-nav) sits as a direct sibling to `tasks/KanbanBoard.tsx` (an internal drag-drop task board). They should never be in the same folder.

---

### [P16] — Routes Without Components (`ideas/`, `funnels/`)

The routes `/agent/marketing/ideas` and `/agent/marketing/funnels` exist in `app/`. Their respective component folders `components/marketing/ideas/` and `components/marketing/funnels/` **do not exist**. Whatever renders at those routes is entirely inlined in the page files — which could explain why those pages may be stubs or placeholder content.

---

## The `BulkActionBar` as a Micro-Case Study

`BulkActionBar` is defined **three times**:

| File | Context | Different props |
|---|---|---|
| `marketing/assets/BulkActionBar.tsx` | Asset browser toolbar | `selectedCount`, `onDelete`, `onMove` |
| `marketing/ads-manager/BulkActionBar.tsx` | Campaign table toolbar | `selectedIds`, `onDelete`, `onDuplicate` |
| `management/tasks/BulkActionBar.tsx` | Task list toolbar | `selectedIds`, `onSelectionChange`, `tasks` |

Same UI pattern, three implementations, three prop shapes. Any accessibility fix, visual update, or keyboard shortcut must be applied to three separate files. This is the component organisation problem in microcosm.

---

## Recommended Canonical Structure

```
components/
├── ui/                   Design system primitives ONLY
│
├── layout/               App shell (extracted from dashboard/)
│   ├── Sidebar.tsx
│   ├── Topbar.tsx
│   ├── ManagementSidebar.tsx
│   ├── Breadcrumb.tsx
│   └── CommandPalette.tsx
│
├── sections/             Public website page sections
│   ├── Navigation.tsx    (the 39KB public mega-nav)
│   ├── Hero.tsx
│   ├── Footer.tsx
│   ├── landing/
│   └── product/          (AnimatedStats, CapabilitiesAccordion, FaqSection)
│
├── features/             SaaS feature UI (ONE folder per feature)
│   ├── marketing/
│   │   ├── tasks/        <- SINGLE canonical task implementation
│   │   ├── notes/
│   │   ├── posts/
│   │   ├── calendar/
│   │   ├── ads-manager/
│   │   ├── assets/
│   │   ├── library/
│   │   ├── plan/
│   │   └── shared/       <- BulkActionBar lives here ONCE
│   │
│   ├── scheduling/       <- SINGLE implementation
│   │   ├── CommandCenter.tsx
│   │   ├── DaySchedule.tsx
│   │   ├── CalendarGrid.tsx (from portal/calendar)
│   │   └── ...
│   │
│   ├── crm/              <- portal/crm merged here
│   ├── website/          <- developer/ components, decomposed
│   ├── messaging/        <- ONE implementation (from dashboard/messaging/)
│   ├── quotes/
│   ├── billing/
│   └── auth/
│
└── common/               True utilities ONLY
    ├── Avatar.tsx
    ├── ErrorBoundary.tsx
    ├── ConfirmationModal.tsx
    └── ImageWithFallback.tsx
```

**Key deletions:**
- `dashboard/dashboard-grid.tsx` (0 bytes)
- `dashboard/messaging/message-bubble.tsx` (0 bytes)
- `dashboard/messaging/message-input.tsx` (0 bytes)
- All `*Optimized.tsx` originals (keep the optimized version, rename it canonical)

**Key merges:**
- `marketing/tasks/` + `management/tasks/` → `features/marketing/tasks/`
- `agent/scheduling/` + `portal/calendar/` → `features/scheduling/`
- `messaging/MessagingInterface.tsx` → extract into `features/messaging/`
- `admin/` (2 files) + `dashboard/admin/` (7 files) → `features/admin/`
