# Montrroase Project Index
> Quick file lookup for all agents. One line per file. Updated by Conductor when new files are created.
> Last updated: auto

## Client — App Routes
| File | Purpose |
|------|---------|
| `client/app/layout.tsx` | Root layout, providers, font setup |
| `client/app/globals.css` | Design system tokens, global CSS |
| `client/app/page.tsx` | Marketing homepage |
| `client/app/auth/` | Login, register, password reset |
| `client/app/dashboard/` | Agent dashboard (main portal) |
| `client/app/courses/` | Course management pages |
| `client/app/pricing/` | Pricing page |
| `client/app/services/` | Services showcase |
| `client/middleware.ts` | Auth route protection |

## Client — Components
| File | Purpose |
|------|---------|
| `client/components/ui/` | Primitive UI (Button, Input, Modal, etc.) |
| `client/components/common/` | Shared across roles |
| `client/components/admin/` | Admin portal components |
| `client/components/agent/` | Agent portal components |
| `client/components/client/` | Client portal components |
| `client/components/marketing/` | Marketing management UI |
| `client/components/management/` | Agency management UI |
| `client/components/messaging/` | Real-time chat components |
| `client/components/portal/` | Portal shell (sidebar, topbar, layout) |
| `client/components/settings/` | User/org settings |
| `client/components/profile/` | Profile management |
| `client/components/dashboard/` | Dashboard widgets and charts |
| `client/components/sections/` | Homepage marketing sections |
| `client/components/call/` | Video call components (WebRTC) |

## Client — Library
| File | Purpose |
|------|---------|
| `client/lib/api.ts` | **MAIN** — all typed API calls (83KB) |
| `client/lib/types.ts` | Core TypeScript types (15KB) |
| `client/lib/websiteTypes.ts` | Website/landing page types |
| `client/lib/design-tokens.ts` | JS design token constants |
| `client/lib/auth-context.tsx` | JWT auth context + provider |
| `client/lib/sidebar-context.tsx` | Sidebar expand/collapse state |
| `client/lib/socket-context.tsx` | WebSocket connection context |
| `client/lib/notification-socket-context.tsx` | Real-time notifications |
| `client/lib/use-messaging.ts` | Messaging hooks |
| `client/lib/hooks/` | Custom React Query hooks |
| `client/lib/providers/` | React context providers |
| `client/lib/utils/` | Utility functions |
| `client/lib/api/` | Modular API client sub-modules |

## Client — Styles
| File | Purpose |
|------|---------|
| `client/styles/animations.css` | Keyframe animations library |
| `client/styles/dashboard.css` | Dashboard-specific styles |
| `client/styles/marketing.css` | Marketing page styles |

## Server — Core
| File | Purpose |
|------|---------|
| `server/api/urls.py` | ALL API URL registrations (34KB) |
| `server/api/models/` | Django ORM models directory |
| `server/api/views/` | DRF viewsets directory |
| `server/api/serializers/` | DRF serializers directory |
| `server/api/tasks/` | Celery async task definitions |
| `server/api/services/` | Business logic layer |
| `server/api/utils/` | Shared server utilities |
| `server/api/admin.py` | Django admin registrations |
| `server/api/signals.py` | Django model signals |
| `server/api/storage.py` | Custom storage backend |
| `server/config/` | Django settings, wsgi, asgi |
| `server/manage.py` | Django management entry point |

## Client — Hooks
| File | Purpose |
|------|---------|
| `client/lib/hooks/useFocusTrap.ts` | Focus trap for modals — Tab/Shift+Tab cycling |
| `client/lib/hooks/useScrollLock.ts` | Body scroll lock with position preservation |

## Orchestrator — Context Docs
| File | Purpose |
|------|---------|
| `_vibecoding_brain/context/montrroase_guide.md` | Business domain, roles, features, data flows, infrastructure |
| `_vibecoding_brain/context/design_system.md` | Design tokens, component patterns, animation guide |
| `_vibecoding_brain/context/modal_guide.md` | **Modal building patterns, API reference, do's and don'ts** |
| `_vibecoding_brain/context/tech_stack.md` | Stack decisions, testing, deployment |
| `_vibecoding_brain/context/project_index.md` | This file — key files with descriptions |
| `_vibecoding_brain/AGENTS.md` | Project constitution — stack, rules, design system summary |
