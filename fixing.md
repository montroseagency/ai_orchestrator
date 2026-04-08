read the last two _vibecoding_brain/sessions and admin.md and:
You are working on **Montrroase**, a marketing agency management SaaS platform

There are several critical broken areas and missing features that need a comprehensive fix and redesign. Work through them in phases, fully implementing each before moving to the next.

---

## PHASE 1 — FIX & REDESIGN: ADMIN CRM PORTAL

### 1.1 Fix Client Creation (BROKEN)
The CRM portal currently cannot create clients successfully. Audit and fix the full client creation flow:
- Find the create-client form/wizard in the admin frontend and trace its API call
- Check `POST /api/admin/crm/clients/` (or whatever endpoint handles creation) in Django views
- Fix any serializer validation errors, missing required fields, or incorrect field mapping
- Ensure the `ClientServiceSettings` object is created alongside the client
- Ensure `ClientTeamAssignment`, `Wallet`, and `ClientHealthScore` records are created on client save (via signals or the view)
- After fix, test the full happy path: form submission → client appears in the list

### 1.2 Remove Pipeline / Replace with Client Cards View
The admin does NOT want a Kanban pipeline. Remove it entirely. Replace with:

**Default View: Client Cards Grid**
- Display ALL clients as profile cards in a responsive grid (3 columns desktop, 2 tablet, 1 mobile)
- Each card contains:
  - Company logo/avatar (initials fallback)
  - Company name (bold, large)
  - Industry badge
  - Plan tier badge (Starter / Pro / Premium) with color coding
  - Status badge (Active / Paused / Pending / Cancelled)
  - Assigned marketing agent(s) — avatar stack
  - Assigned developer agent(s) — avatar stack
  - Health score ring (0–100, colored: green 80+, blue 60–79, yellow 40–59, red <40)
  - MRR amount
  - Last activity timestamp
  - Payment status indicator (paid / overdue / pending)
- Search bar at top filters cards in real time
- Filter chips: All / Active / Paused / Overdue / At-Risk
- Sort dropdown: Name / MRR / Health / Last Activity / Date Added
- "+ Add Client" button opens a multi-step wizard (fix this — see 1.1)
- Keep a compact Table View toggle for power users (columns: Company, Status, Plan, MRR, Health, Agents, Last Activity)

### 1.3 Client Detail Page — Complete & Comprehensive
When any client card is clicked, open `/dashboard/admin/crm/[clientId]` as a full-page detail view with:

**Header:**
- Back arrow → CRM
- Company name + logo
- Status badge + plan badge + MRR
- Health score pill
- Action menu: Message Client, Create Invoice, Edit Client, Pause/Cancel

**7 Tabs:**

**[Overview]**
- Two-column layout: left = company info (name, industry, contact email, phone, website, timezone, company size, tax ID, preferred contact method); right = service toggles (marketing active Y/N, website active Y/N, courses active Y/N)
- Health score breakdown card: 4 component bars (Billing Health, Engagement Health, Deliverable Health, Satisfaction Health) + overall score with color ring
- Key metrics strip: Posts this month, Project completion %, Open invoices count, Last client login

**[Work Feed]**
- Chronological infinite-scroll feed of ALL activity for this client, powered by `ActivityLog` model
- Each entry: timestamp, agent avatar + name, action description, entity type icon, clickable link to the source entity
- Filter bar: All / Posts / Website / Billing / Support / Notes
- Date range picker
- This is the most important tab — admin must see EVERYTHING that happened for this client

**[Marketing]**
- Read-only view of all marketing posts for this client: gallery grid with status badges (planned / in_production / in_review / client_review / approved / scheduled / posted)
- Active campaigns list with progress bars and phase status
- Content calendar (month view, read-only, showing scheduled posts per platform)
- Social account metrics: per-platform follower count, engagement rate, reach (last 30 days)
- Platform breakdown donut chart

**[Website]**
- Active website project card: status, complexity, current phase, progress bar
- Timeline phases list with status badges and completion dates
- Payment phases with amounts and paid/pending status
- Domain info (domain name, registrar, expiry date, SSL status)
- Hosting info (provider, plan, monthly cost)
- Quote history table (status, amount, date)
- GitHub repo link + demo URL if available

**[Team]**
- Marketing team section: cards for each assigned marketing agent showing their role (Lead / Support / Reviewer), posts created for this client, and a Remove button
- Development team section: same for dev agents
- "+ Assign Agent" button per section: opens modal to search agents by department, shows their current capacity, lets admin pick role
- Uses `ClientTeamAssignment` model (NOT the deprecated single FK fields)
- Assignment history log below

**[Billing]**
- Invoice table: invoice number, type, amount, status, due date, payment method, actions (View PDF, Mark Paid, Send Reminder)
- Revenue chart: bar chart of monthly revenue from this client (last 12 months)
- Subscription details: plan, billing cycle, next renewal, PayPal subscription ID
- Wallet: current balance, transaction list (topup / payment / refund / giveaway)
- Outstanding balance alert if overdue

**[Notes]**
- Admin-only private notes (never visible to client or agents)
- Each note: content (markdown), tags (chips), pinned toggle, created timestamp
- Pin notes float to top
- Search notes by content or tag
- Create note inline (no modal needed)

---

## PHASE 2 — FIX & REDESIGN: ADMIN TEAM PORTAL

### 2.1 Team Overview
- Capacity bar chart: each agent with filled/total clients, color-coded (green <80%, yellow 80–90%, red 100%)
- Online status (from Socket.IO presence) shown as green/grey dot
- Team-wide stats: total agents, online count, average capacity %, tasks completed this week
- Activity feed: recent actions by all agents (last 20 entries from ActivityLog filtered by agent)

### 2.2 Agent Roster
- Card grid matching the style of the client cards
- Each card: avatar, name, department badge, specialization, capacity meter (X/max clients), online status, 30-day stats (posts / phases / tasks completed), action buttons: [View Profile] [Message] [Assign to Client]

### 2.3 Agent Detail Page `/dashboard/admin/team/[agentId]`
**6 tabs: Overview / Clients / Work Log / Tasks / Schedule / Reports**

**[Overview]** — profile, capacity, key 30-day metrics, performance trend chart

**[Clients]** — list of assigned clients with this agent's role, contribution count, quick re-assign capability

**[Work Log]** — ActivityLog filtered by this agent, same feed component as client Work Feed but scoped to agent. Filterable by client and date range.

**[Tasks]** — All AdminTask records assigned to this agent. Admin can create new tasks here. Task card shows: title, priority badge, status, due date, client link, agent notes. Status flow: pending → acknowledged → in_progress → completed.

**[Schedule]** — Read-only view of the agent's AgentTimeBlock calendar (week view). Admin sees how the agent allocates time across clients.

**[Reports]** — Agent performance report: posts/phases/tasks per week chart, client satisfaction scores, comparison to team average

### 2.4 Workload Matrix
- Grid: rows = clients, columns = agents
- Cell: role badge (lead/support/reviewer) if assigned, empty if not
- Capacity row at bottom showing percentage per agent
- Drag to reassign (or click cell to assign/remove)

### 2.5 Admin Task Delegation (Fix & Complete)
- Admin Task Board: Kanban with columns by status (Pending / Acknowledged / In Progress / Completed)
- Create Task modal: title, description, assign to agent (searchable), link to client (optional), priority (low/medium/high/urgent), category, due date
- Tasks created here MUST appear in the assigned agent's Command Center under a dedicated "From Admin" section
- Agent can: acknowledge, add notes, update status
- Admin sees status changes in real time (or on refresh)
- Ensure the `AdminTask` model, serializer, viewset, and frontend hook `useAdminTasks` all exist and are wired correctly

### 2.6 Team Messaging (Already exists — verify it's accessible from Team Portal)
- Messaging should be reachable via `/dashboard/admin/team/messages`
- Verify channels, DMs, group chats all work
- Fix any broken routes or missing navigation links

---

## PHASE 3 — FIX & REDESIGN: MARKETING AGENT PORTAL (Comprehensive)

This is a major overhaul. The marketing agent portal needs significant improvements in the Command Center, reporting, and admin connection and also design.

### 3.1 Command Center — Major Enhancement
The agent's Command Center (`/dashboard/agent/marketing/management/`) must be redesigned to include:

**Top Strip — KPIs:**
- Posts published this month / scheduled / pending approval
- Active clients count
- Tasks completed this week / overdue
- Upcoming deadlines (next 7 days)

**Attention Required Panel:**
- Posts awaiting client review (with client name + post thumbnail)
- Overdue tasks
- Admin tasks assigned to this agent (FROM ADMIN section — this is the critical missing piece)
- Clients with no activity this week (idle alert)

**"From Admin" Section (NEW — critical):**
- Dedicated card/section showing all `AdminTask` records where `assigned_to = this agent`
- Each item: task title, priority badge, client link, due date, status
- Agent can click to view full task detail and update status (acknowledge / mark in progress / complete / add notes)
- Unread/new tasks show a badge notification

**My Schedule (Today):**
- Today's time blocks from AgentTimeBlock calendar
- Current task highlight (what should I be working on RIGHT NOW)
- Focus Timer button (Pomodoro)

**Client Activity Strip:**
- Horizontal scroll of assigned client cards showing: pending posts, last post date, upcoming content deadline

**Quick Actions:**
- Create Post
- Schedule Time Block
- Message Client
- View Content Calendar

### 3.2 Reporting Tab (Fix — Currently Broken/Unusable)
Add a fully functional Reporting section to the marketing agent portal at `/dashboard/agent/marketing/management/reports`:

**Report Types available to marketing agent:**
1. **Client Performance Report** — select client, date range → shows: posts published, posts scheduled, engagement metrics per platform, audience growth, campaign progress
2. **Content Output Report** — posts created per week/month, breakdown by platform, by content format (Reel/Carousel/etc.), by content pillar
3. **Social Media Growth Report** — follower count trends, engagement rate trends per platform, best performing posts (by engagement)
4. **Campaign Report** — for a selected campaign: phases completed, milestones hit, posts within campaign, performance metrics

Each report:
- Date range picker
- Client selector (or "All Clients")
- Export as PDF button
- Print button
- Charts rendered with Recharts using the platform's design tokens

Fix any broken chart components, missing data hooks, or API endpoint issues.

### 3.3 Task Management — Complete & Connect to Admin
- Agent's own tasks at `/dashboard/agent/marketing/management/tasks`
- Two sections: "My Tasks" (self-created or peer-assigned) and "From Admin" (AdminTask records)
- Kanban view and List view toggle
- Create task: title, description, client (optional), priority, due date, category
- Admin tasks are READ-ONLY for editing the core fields but agent can: acknowledge, add progress notes, mark complete
- Overdue tasks highlighted in red

### 3.4 Approvals Section (Fix — Currently Errors)
Fix the approvals page for the marketing agent:
- Show posts that are in `client_review` status awaiting client approval — agent can see these and follow up
- Show posts that require admin approval — agent submits, sees pending status
- Fix any 500 errors or broken API calls in the approvals components
- Remove non-functional UI elements

### 3.5 Client Management Portal (Agent's CRM View)
- Agent sees only their assigned clients
- Same card view as admin but scoped to their clients
- Clicking a client shows a simplified client detail: Overview, Posts, Campaigns, Social Metrics, Messages
- Agent CANNOT see billing tab or admin notes

---

## PHASE 4 — FIX & REDESIGN: DEVELOPER AGENT PORTAL (Comprehensive)

### 4.1 Command Center Enhancement
Similar improvements as marketing agent:
- KPI strip: active projects, phases in progress, overdue tasks, upcoming deadlines
- "From Admin" section (AdminTask records for this agent)
- Today's schedule
- Project status quick view: each active project with phase progress bar

### 4.2 Approvals (Fix)
- Show website phases awaiting client approval
- Show quotes sent to client (pending acceptance)
- Fix any broken components/errors

### 4.3 Reports (Fix & Implement)
At `/dashboard/agent/developer/management/reports`:
1. **Project Status Report** — all active projects, phase completion, timeline vs estimated
2. **Task Completion Report** — tasks done, overdue, time tracked (estimated vs actual hours)
3. **Domain/Hosting Report** — domains expiring in next 60 days, SSL expiry warnings

---

## PHASE 5 — FIX: OPERATIONS PORTAL & APPROVALS HUB (Admin)

### 5.1 Operations Portal
Verify all sub-sections work:
- Revenue Dashboard: MRR chart, revenue by client, revenue by service line — fix any broken Recharts components or missing API responses
- Invoice Manager: table with filters, aging report — fix any broken pagination or filter bugs
- Payment Verification queue — fix if broken
- Support Manager — fix if errors
- Audit Log — verify ActivityLog data is being written and displayed

### 5.2 Approvals Hub (Admin)
Fix the admin Approvals hub at `/dashboard/admin/team/approvals`:
- Content approvals: posts submitted for admin review show up here
- Billing approvals: bank transfer proofs pending verification
- Agent requests: task category requests, time-off, etc.
- Each item has a clear [Approve] / [Reject] / [Review] action that actually works
- Fix any non-functional buttons or broken API calls
- Remove placeholder/fake UI that does nothing

---

## PHASE 6 — CROSS-CUTTING FIXES

### 6.1 ActivityLog — Ensure It's Being Populated
The `ActivityLog` model is the backbone of Work Feeds. Verify signal handlers exist and are firing for:
- MarketingPost status changes (especially `posted`, `approved`, `client_review`)
- WebsiteProjectPhase status changes
- Invoice status changes (paid)
- SupportTicket creation and resolution
- AdminTask status changes
- ClientTeamAssignment creation/removal

If signals are missing, add them in `server/api/signals.py` with `log_activity.delay(...)` Celery calls.

### 6.2 Navigation & Routing Audit
- Ensure all sidebar links in all portals (admin, marketing agent, developer agent) go to real, implemented routes — remove or hide any links to pages that don't exist yet
- Fix any 404s caused by broken route definitions in Next.js
- Ensure back navigation works correctly on all detail pages

### 6.3 API Error Handling
- All API calls should show meaningful toast error messages (not silent failures)
- Loading states should be implemented on all data-fetching components (skeletons, not spinners where possible)
- Empty states should be informative (e.g., "No clients yet — click + Add Client to get started")

### 6.4 Mobile Responsiveness
- Admin CRM cards grid: responsive breakpoints
- Agent Command Center: readable on tablet
- Client detail tabs: scrollable tab bar on mobile

---

## IMPLEMENTATION RULES

1. **Always use `ApiService` singleton** from `lib/api.ts` — never raw `fetch()`
2. **React Query** for all server state — use `useQuery` and `useMutation` with proper cache invalidation
3. **Phosphor icons only** — NOT Lucide
4. **Framer Motion** for all animations — duration tokens: fast=150ms, default=200ms, slow=300ms
5. **Design tokens** from `lib/design-tokens.ts` and CSS custom properties in `globals.css` — do not hardcode colors
6. **TypeScript strict** — every new component, hook, and API function must be fully typed using types from `lib/types.ts` and `lib/types/`
7. **No `any`** — if a type is unknown, define it properly
8. **`'use client'`** only where interactivity requires it — prefer server components
9. **ActivityLog** entries should always be created via the `log_activity` Celery task, not synchronously in views
10. **Multi-agent assignment** — always use `ClientTeamAssignment` model, never the deprecated `marketing_agent` / `website_agent` FK fields on `Client`
11. When fixing backend: check `server/api/views/`, `server/api/serializers/`, `server/api/models/` — follow existing patterns
12. When creating new Django models, always create and run migrations
13. Test each phase by tracing the full data flow: form input → API call → Django view → serializer → DB → response → React Query cache → UI render

Start with Phase 1 (fix client creation first, then the CRM redesign) and work through each phase sequentially. After completing each phase, summarize what was changed before moving on.