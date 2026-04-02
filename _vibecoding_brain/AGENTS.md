# AGENTS.md — Montrroase Project Constitution
> Loaded by every agent. Keep reads here to a minimum — use context/ docs for depth.

## Project Identity
- **Name:** Montrroase — a marketing agency management SaaS
- **Stack:** Next.js 15 (App Router, React 19, TailwindCSS v4) + Django 4 REST API + Celery + PostgreSQL + Redis + WebSockets
- **Repo root:** `agentic_workflow/Montrroase_website/`
- **Client:** `client/` — Next.js app
- **Server:** `server/` — Django, all API lives in `server/api/`

## Key Directories
| Path | Purpose |
|------|---------|
| `client/app/` | Next.js App Router pages |
| `client/components/` | React components (admin/, agent/, client/, common/, ui/) |
| `client/lib/` | API client (`api.ts`), types, hooks, contexts, design tokens |
| `client/styles/` | Global CSS, animations |
| `server/api/models/` | Django ORM models |
| `server/api/views/` | DRF viewsets |
| `server/api/serializers/` | DRF serializers |
| `server/api/urls.py` | All API URL registrations |

## Architecture Rules (NEVER violate)
1. **No `fetch()` directly** — always use the typed functions in `client/lib/api.ts`
2. **No inline styles** — use Tailwind classes or CSS custom properties from `globals.css`
3. **Server components by default** — only add `'use client'` when you need interactivity
4. **API routes** — backend uses DRF. New endpoints go in `server/api/views/` + registered in `server/api/urls.py`
5. **Auth** — JWT tokens, managed via `client/lib/auth-context.tsx`. Never bypass.
6. **Types** — shared types in `client/lib/types.ts` and `client/lib/websiteTypes.ts`
7. **State** — React Query for server state (`@tanstack/react-query`). No Redux.
8. **Animations** — Framer Motion only. Duration tokens: fast=150ms, default=200ms, slow=300ms

## Design System (see context/design_system.md for full detail)
- Accent: `#2563EB` (blue-600)
- Surfaces: white (#FFFFFF), subtle (#FAFAFA), muted (#F4F4F5)
- Border: `#E4E4E7` | Radius: 8px (surface), 16px (lg)
- Typography: Tailwind classes. Page title: `text-2xl font-semibold tracking-tight`
- Component classes: `.card-surface`, `.badge-success/warning/error/info`, `.surface-outlined`

## Context Index (read these when needed)
- `context/montrroase_guide.md` — Business domain, user roles, features, data flows, infrastructure
- `context/design_system.md` — Full design tokens, component patterns, animation guide
- `context/tech_stack.md` — Detailed stack decisions, testing, deployment
- `context/project_index.md` — Every key file with one-line description
- `agents/*.md` — Agent system prompts
