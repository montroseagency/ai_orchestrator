# Montrroase — Complete Application Guide

> Business domain reference for agent context. Explains what Montrroase IS, how it works, every feature, every user role, every data flow.

---

## 1. What is Montrroase

Montrroase is a **marketing agency management SaaS** platform. It allows a marketing agency to manage its clients, agents (employees), marketing campaigns, website development projects, billing, and internal operations — all from a single web application.

**Business model:** The agency (admin) onboards clients who pay for marketing and/or website development services. Agents (employees) are assigned to clients and execute the work. Clients can view progress, approve content, manage billing, and communicate with their agents.

**Two service lines:**
- **Marketing** — Social media management, content creation, campaigns, ads, funnels, email/SMS, branding, SEM
- **Website Development** — Website building, hosting, domains, SEO, project management with phases

---

## 2. User Roles & Portals

### 2.1 Admin (`/dashboard/admin/`)
The agency owner/manager. Full system access. The admin dashboard is structured as a **mission control center** with three core portals.

**Sidebar Structure (3+3+3):**
- **Home:** Command Center (`/dashboard/admin/`) — Strategic overview with attention panel, KPI strip, revenue chart, activity feed
- **Portals:** CRM Portal (`/crm`), Team Portal (`/team`), Operations Portal (`/operations`)
- **Tools:** Approvals (`/approvals`), Reports Hub (`/reports`), Courses Manager (`/courses`)
- **Settings:** Company Settings (`/settings/company`), Service Catalog (`/settings/catalog`), Notifications (`/settings/notifications`)

**Capabilities:**
- **CRM Portal** — Full client relationship management: Pipeline (kanban), Board, Table views; Client Detail with 7 tabs (Overview, Work Feed, Marketing, Website, Team, Billing, Notes); multi-agent team assignment per client; client health scoring (0-100, auto-calculated daily)
- **Team Portal** — Full team management: Overview, Roster, Workload Matrix; Agent Detail with 6 tabs; Team Messaging (moved from sidebar); Admin Task delegation system
- **Operations Portal** — Financial operations: Revenue Dashboard, Invoice Manager with aging, Payment Verification queue, Support Manager, Audit Log
- **Approvals** — Centralized queue for content, billing, agent request, and client change approvals
- **Reports Hub** — Client, Financial, Team, Marketing, Website reports with save/schedule
- **Company Settings** — Agency profile (not a Client record), branding, banking, integrations, security
- **Service Catalog** — Marketing plans and pricing tiers, website project types, add-ons
- Multi-agent team assignment per client (lead/support/reviewer roles per department)
- Client health monitoring (automated scoring: billing, engagement, deliverables, satisfaction)
- Admin task delegation to agents (visible in agent Command Center)
- Universal activity log tracking all platform events
- Admin notes per client (private, tagged, pinnable)
- Daily admin digest (email) + daily health score recalculation (3AM Celery task)

### 2.2 Marketing Agent (`/dashboard/agent/marketing/`)
An agency employee in the marketing department.

**Capabilities:**
- View and manage assigned clients (CRM view via Management Portal)
- Content calendar with drag-and-drop scheduling
- Create/edit/schedule marketing posts across platforms
- Campaign management (create campaigns, phases, milestones)
- Ads Manager (full Meta/social ads suite — campaigns, ad sets, ads, audiences, funnels, planner, reports)
- Email/SMS campaign creation and analytics
- Funnel builder (stages, landing pages, A/B tests, lead magnets, CTA tracking)
- Brand guidelines management (positioning, audits, consistency checks)
- SEM tools (SEO keywords, content briefs, audit items, paid ad campaigns)
- Asset library (global assets, music, transitions, animations, editing styles, folder templates)
- Content templates
- Task management
- Client notes
- Social account management (connect, sync metrics)
- Schedule management (day/week views, recurring blocks, focus timer, command center)
- Messaging with clients and admin
- Client reports with export

### 2.3 Developer Agent (`/dashboard/agent/developer/`)
An agency employee in the website development department.

**Capabilities:**
- Website project management (full lifecycle: questionnaire → valuation → demo → development → review → completed)
- Phase management (timeline phases for workflow, payment phases for billing)
- Phase image uploads and update logs
- Domain management (registration, DNS records, expiration tracking)
- Hosting management (multi-provider: Vercel, Netlify, AWS, DigitalOcean, Cloudflare)
- SSL certificate and DNS configuration
- Quote generation (line items, auto-fill from questionnaire/phases, AI suggestions, PDF, public links)
- Project tasks with subtasks, dependencies, time tracking
- Project milestones and timeline
- Project plans (implementation, architecture, migration, feature, fix, refactor)
- Project strategies
- Code snippets library with sharing
- Scratchpad for notes
- Schedule management (same as marketing agent)
- Client communication hub (status updates, pricing requests, timeline requests, issue escalation)
- Messaging

### 2.4 Client (`/dashboard/client/`)
A business that contracts the agency for services.

**Capabilities:**
- Marketing overview (posts, calendar, analytics, connected social accounts, plan review)
- Website builder (start new project via questionnaire, track phases, view demos)
- Website management (domains, hosting, SEO, analytics)
- Course catalog (browse, purchase with wallet/PayPal, track progress, earn certificates)
- Support tickets (create, track, message)
- Messaging with assigned agents
- Billing (view invoices, pay, manage payment methods)
- Wallet (balance, transactions, top-up, auto-recharge, redeem codes)
- Quote review and acceptance (with digital signature)
- Settings (profile, billing, wallet, preferences)

### 2.5 Guest (`/dashboard/guest/`)
Unauthenticated visitor exploring services.

**Capabilities:**
- View pricing
- Browse project types
- Start website questionnaire (data transfers to account on registration)
- Marketing information

---

## 3. Key Business Concepts

### 3.1 Client
A business contracting the agency. Core entity linking to almost everything.

- **Status:** active, pending, paused, cancelled
- **Payment status:** paid, overdue, pending, none
- **Plan tier:** starter, pro, premium, none (PayPal subscription-based)
- **Agent assignments:** `marketing_agent` and `website_agent` ForeignKeys (deprecated — kept for backward compat) + `ClientTeamAssignment` M2M (new — supports multiple agents per client with lead/support/reviewer roles per department)
- **Multi-service:** can activate marketing, website, and courses independently via ClientServiceSettings
- **Profile:** company, industry, website URL, company size, tax ID, timezone, language, preferred contact method
- **Social accounts:** OAuth-connected (Instagram, TikTok, YouTube, Twitter, LinkedIn, Facebook) with encrypted tokens
- **Wallet:** one-to-one wallet for payments, giveaway credits, auto-recharge

### 3.2 Agent
An agency employee assigned to clients.

- **Department:** marketing OR website development
- **Specialization:** text field for area of expertise
- **Capacity:** max_clients limit with current_client_count tracking
- **Schedule:** time-blocked calendar with day/week views, recurring blocks
- **Task categories:** admin-configurable categories with colors, icons, department scoping

### 3.3 Marketing Plan
One per client. Contains the strategic marketing framework.

- **Content pillars:** themed content categories with target percentages and guidelines
- **Audience personas:** target audience definitions
- **Platforms:** Instagram, TikTok, YouTube, Facebook, Twitter/X, LinkedIn, Pinterest
- **Content formats:** Reel, Video, Carousel, Single Photo
- **Hashtag management:** organized hashtag blocks

### 3.4 Marketing Post
Individual content pieces created by agents for clients.

- **Lifecycle:** planned → in_production → in_review → client_review → approved → scheduled → posted
- **Tied to:** client, plan, platform, content format, pillar, social account, campaign
- **Features:** day ordering, client approval workflow, scheduled publishing, live URL tracking
- **Media:** image or video content type
- **Associations:** audiences (M2M), hashtags (M2M)

### 3.5 Marketing Campaign
Organized marketing efforts spanning multiple posts.

- **Status:** draft, active, paused, completed, cancelled
- **Structure:** campaign → phases → milestones
- **Phases:** named periods with date ranges and colors
- **Milestones:** trackable dates within phases
- **Pillars:** M2M relationship with content pillars

### 3.6 Ads Manager
Full advertising campaign management (Meta/social platform ads).

- **Campaign:** objectives (awareness, traffic, engagement, leads, app_promotion, sales), budget (daily/lifetime), buying type (auction/reservation), special ad categories
- **Ad Set:** conversion location, optimization goal, bid strategy, placements (automatic/manual), audience targeting, scheduling
- **Ad:** individual creative with format, media, copy
- **Audience:** saved audience definitions for targeting
- **Funnel:** ads funnel stages for conversion tracking
- **Planner:** scenario-based campaign planning and forecasting
- **Reports:** custom report views with saved configurations
- **Benchmarks:** performance benchmark data for comparison
- **Export:** Meta campaign ID sync, export status tracking

### 3.7 Funnels
Marketing funnel management for conversion optimization.

- **Stages:** funnel stages with ordering
- **Landing pages:** associated landing page tracking
- **A/B tests:** split testing management
- **Lead magnets:** downloadable/gated content offers
- **CTA performance:** call-to-action tracking and analytics

### 3.8 Email/SMS Campaigns
Direct marketing campaigns via email and SMS.

- **Campaigns:** create and manage email/SMS campaigns
- **Templates:** reusable email/SMS templates
- **Analytics:** open rates, click rates, delivery metrics

### 3.9 Website Project
Client website development tracked through a phased lifecycle.

- **Lifecycle:** questionnaire → questionnaire_submitted → valuation → demo → payment_pending → in_development → review → completed
- **Project types:** new, improve, fix
- **Complexity:** low, medium, high (AI-assessed)
- **AI Valuation:** estimated cost range, hours, timeline, complexity score, recommendations
- **Admin overrides:** final fixed cost and timeline
- **Template:** selected template with customizations
- **Demo:** demo URL and screenshots
- **Infrastructure:** GitHub repo, dashboard URL, domain, server status, SEO status, analytics status
- **Domain:** selected domain, TLD, yearly price, registration/expiration dates
- **Hosting:** hosting plan, monthly price, purchase date
- **Assigned developer:** FK to Agent

### 3.10 Website Phases (Two Types)

**Payment Phases (WebsitePhase):**
- Billing milestones for the project
- Fields: phase number, title, amount, billing type (one_time/recurring), status, deliverables, payment due date

**Timeline Phases (WebsiteProjectPhase):**
- Development workflow stages (Discovery, Design, Development, etc.)
- Fields: order, name, status, client/agent notes, GitHub commits, price, timeline days, deadline
- Phase updates, images, and interaction logs

### 3.11 Project Tasks
Hierarchical task management within website projects.

- **Categories:** coding, planning, review, devops, communication, admin, research
- **Status:** pending, in_progress, completed
- **Priority:** low, medium, high
- **Subtask support:** parent_task FK for nesting
- **Time tracking:** estimated_hours, actual_hours
- **Plan linking:** source_plan FK, source_plan_step

### 3.12 Invoicing
Multi-type invoice system.

- **Types:** marketing_subscription, website_phase, domain, hosting, one_time, other
- **Payment methods:** cash, bank_transfer, paypal, other
- **Status:** paid, pending, overdue
- **Features:** line items (JSON), auto-generation from phases, admin notes

### 3.13 Wallet & Transactions
Client wallet system for flexible payments.

- **Transaction types:** topup, payment, refund, giveaway, bonus
- **Auto-recharge:** threshold-based automatic top-up via saved payment method
- **Redeem codes:** promotional codes with value, usage limits, expiration

### 3.14 Quotes
Service quotation system with full lifecycle.

- **Status:** draft → pending_admin → admin_approved → sent_to_client → client_approved / revision_requested / expired → converted / cancelled
- **Features:** line items with reordering, auto-fill from questionnaire or project phases, AI-powered suggestions
- **Public links:** shareable quote URLs with optional password protection
- **PDF export:** generated quote PDFs
- **Conversion:** quote-to-invoice conversion

### 3.15 Courses
Educational content platform for clients.

- **Structure:** Course → Modules → Lessons (video, text, quiz, assignment)
- **Access:** tier-based (free, starter, pro, premium) or individual purchase
- **Progress:** per-user tracking with completion percentage
- **Certificates:** auto-generated on completion

### 3.16 Support
Client support ticket system.

- **Categories:** technical, billing, feature_request, general, project_update
- **Priority:** low, medium, high, urgent
- **Lifecycle:** open → in_progress → waiting_client → resolved → closed
- **Ticket numbers:** auto-generated (TKT-XXXXXX format)
- **Messages:** threaded conversation with attachments

### 3.17 Messaging
Real-time chat powered by Socket.IO microservice.

- **Direct messages:** 1:1 between any users
- **Group chat:** multi-participant with member management, message pinning
- **Channels:** organized messaging channels
- **Features:** file uploads, message editing/deletion, read receipts, online status
- **Persistence:** MongoDB (realtime service)

### 3.18 Notifications
Multi-channel notification system.

- **20+ types:** task lifecycle, payment events, content workflow, website phases, course events, subscription events, general
- **Delivery:** in-app (WebSocket via notification-realtime service), browser push (VAPID/Web Push)
- **Persistence:** MongoDB (notification service)

### 3.19 Giveaways
Promotional campaigns for social media.

- **Platforms:** Instagram, TikTok, Facebook
- **Lifecycle:** active → ended → processing → completed
- **Winners:** tracked with wallet credit distribution and claim status

### 3.20 Agent Scheduling
Time management system for agents.

- **Time blocks:** typed slots (deep_work, reactive, creative, analytical, admin, strategy, communication, break, coding, planning, review, content_creation, client_calls)
- **Views:** day, week, all-tasks, recurring
- **Features:** recurring blocks, focus timer (Pomodoro), command center, cross-client task view, conflict detection
- **Task categories:** admin-configurable with colors, icons, department scoping, review requirements

### 3.21 WebRTC Video Calling
Peer-to-peer video calling between users.

- **TURN server:** Coturn with HMAC-SHA1 credentials (24h TTL)
- **Features:** video/audio calls, screen sharing, multi-participant, call controls
- **Frontend:** simple-peer library wrapping WebRTC

### 3.22 Social Media Integration
OAuth-connected social accounts with metrics tracking.

- **Platforms:** Instagram, TikTok, YouTube, Twitter/X, LinkedIn, Facebook
- **OAuth:** platform-specific OAuth2 flows with encrypted token storage (Fernet)
- **Metrics:** real-time per-account (followers, engagement, reach, impressions) and per-post (likes, comments, shares, saves)
- **Sync:** manual trigger + Celery-scheduled (Instagram every 4h, YouTube every 6h)

### 3.23 Admin Dashboard Models (New)
New models added in the admin dashboard redesign. In `server/api/models/admin_dashboard.py`.

- **AgencyProfile** — Singleton model for the agency's own identity (name, legal_name, logo, branding colors, banking defaults). NOT a Client. Only one AgencyProfile per system.
- **ClientTeamAssignment** — M2M bridge between Client and Agent with role (lead/support/reviewer) and department (marketing/development). Replaces single-FK pattern. unique_together on [client, agent].
- **ClientHealthScore** — OneToOne with Client. Stores auto-calculated scores: billing_health, engagement_health, deliverable_health, satisfaction_health, overall_score (0-100). Recalculated daily at 3AM.
- **AdminTask** — Tasks created by admin and assigned to agents. Has priority (low/medium/high/urgent), status (pending/acknowledged/in_progress/completed/cancelled), category, due_date. Appears in agent's Command Center under "From Admin" section.
- **ActivityLog** — Universal event tracking. Records actor, action, entity_type, entity_id, client, agent, description, metadata. Indexed on [client, -created_at], [agent, -created_at], [entity_type, -created_at]. Populated by signal handlers and `log_activity` Celery task. Powers the Work Feed, Audit Log, and Agent Work Log.
- **AdminNote** — Admin's private notes about clients. Supports tags (JSONField), pinning, searching.
- **SavedReport** — Saved report configurations with optional schedule (none/weekly/monthly) for automated generation.

---

## 4. Data Flow Patterns

### 4.1 Authentication
1. User submits credentials → `POST /api/auth/jwt/login/` → receives access + refresh JWT tokens
2. Tokens stored in memory (auth-context.tsx) → attached to every API request via Authorization header
3. Access token expires → automatic refresh via `POST /api/auth/jwt/refresh/`
4. Refresh token expires → user redirected to login
5. Google OAuth: redirect to Google → callback to `/api/auth/google/callback/` → JWT tokens issued
6. Email verification: register → send code → verify code → account activated

### 4.2 API Communication
1. All frontend API calls go through `ApiService` singleton in `client/lib/api.ts`
2. ApiService handles: JWT header injection, token refresh on 401, error formatting, pagination
3. React Query (`@tanstack/react-query`) manages caching, refetching, optimistic updates
4. No direct `fetch()` calls anywhere in the frontend

### 4.3 Real-Time (Socket.IO)
1. **Messaging:** Client connects to realtime service (port 8004) via `socket-context.tsx`
2. **Notifications:** Separate connection to notification-realtime service (port 8000) via `notification-socket-context.tsx`
3. Both services validate JWT tokens on connection
4. Messages persisted in MongoDB, events broadcast via RabbitMQ between services
5. Django triggers events → RabbitMQ → Node.js services → Socket.IO → connected clients

### 4.4 Background Tasks (Celery)
- **Broker:** RabbitMQ (with Redis as result backend)
- **Queues:** instagram, youtube, sync, analytics, maintenance, reports
- **Scheduled tasks:**
  - Social media sync: Instagram every 4h, YouTube every 6h
  - Analytics aggregation: daily at 2 AM
  - Weekly reports: Mondays 9 AM
  - Invoice notifications: daily 9 AM
  - Task overdue checks: daily 9 AM
  - Monthly performance: 1st of month 10 AM
  - Recurring time block generation: daily midnight

### 4.5 File Storage
- **Backend:** Backblaze B2 via `django-storages` (custom `MontroseB2Storage`)
- **Uploads:** avatars, phase images, chat files, website versions (zip), course thumbnails
- **Static files:** collected to `staticfiles/`, served by Nginx with long cache headers

### 4.6 Inter-Service Communication
```
Django ──RabbitMQ──→ Realtime Service (Socket.IO → clients)
Django ──RabbitMQ──→ Notification Service (Socket.IO → clients)

Django ──HTTP──→ Realtime Service (internal API calls)
Notification Service ──HTTP──→ Django (validate tokens, fetch data)
Celery Worker ──same DB──→ PostgreSQL (shared with Django)
Analytics Worker ──MongoDB──→ Realtime DB
```

---

## 5. Module/Feature Map

### 5.1 Frontend Routes → Backend Mapping

| Feature | Frontend Route | Backend View Package | Key Models |
|---------|---------------|---------------------|------------|
| Auth | `/auth/*` | `views/auth/` | User |
| Admin Dashboard | `/dashboard/admin/overview` | `views/admin/dashboard_views` | User, Client, Agent |
| Client Management | `/dashboard/admin/clients/*` | `views/admin/client_assignment_views` | Client, Agent, ClientServiceSettings |
| Agent Management | `/dashboard/admin/agents/*` | `views/agent/agent_profile_views` | Agent, User |
| Revenue Analytics | `/dashboard/admin/analytics/*` | `views/admin/analytics_views` | Invoice, Client, Transaction |
| Approvals | `/dashboard/admin/approvals` | `views/admin/approval_views` | AgentTimeBlock, TaskCategory |
| Invoicing | `/dashboard/admin/invoices/*` | `views/admin/invoice_views` | Invoice, Client |
| Marketing Posts | `/dashboard/agent/marketing/posts/*` | `views/marketing/marketing_views` | MarketingPost, MarketingPlan, ContentPillar |
| Content Calendar | `/dashboard/agent/marketing/calendar` | `views/marketing/marketing_views` | MarketingPost, SocialPlatform, ContentFormat |
| Campaigns | `/dashboard/agent/marketing/campaigns/*` | `views/marketing/marketing_views` | MarketingCampaign, CampaignPhase, CampaignMilestone |
| Ads Manager | `/dashboard/agent/marketing/ads-manager/*` | `views/marketing/marketing_views` | AdsCampaign, AdSet, Ad, AdsAudience |
| Funnels | `/dashboard/agent/marketing/funnels` | `views/marketing/marketing_views` | FunnelStage, LandingPage, ABTest, LeadMagnet |
| Email/SMS | `/dashboard/agent/marketing/email-sms` | `views/marketing/marketing_views` | EmailSmsCampaign, EmailSmsTemplate |
| Branding | `/dashboard/agent/marketing/branding` | `views/marketing/marketing_views` | BrandGuideline, BrandPositioning, BrandAudit |
| SEM | `/dashboard/agent/marketing/sem` | `views/marketing/marketing_views` | SeoKeyword, ContentBrief, PaidAdCampaign |
| Asset Library | `/dashboard/agent/marketing/library` | `views/marketing/marketing_views` | GlobalAsset, AssetCategory, PostAssetLink |
| Website Projects | `/dashboard/agent/developer/website/*` | `views/website/website_views` | WebsiteProject, WebsitePhase, WebsiteProjectPhase |
| Domain Management | `/dashboard/agent/developer/website/domains` | `views/agent/website_views` | WebsiteHosting (domain fields), DomainConfiguration |
| Hosting Management | `/dashboard/agent/developer/website/hosting` | `views/agent/website_views` | WebsiteHosting, HostingPlan |
| Project Tasks | `/dashboard/agent/developer/tasks` | `views/agent/developer_views` | ProjectTask, ProjectMilestone |
| Quotes | `/dashboard/agent/developer/*/quotes/*` | `views/billing/quote_views` | Quote, QuoteLineItem |
| Code Snippets | `/dashboard/agent/developer/snippets/*` | `views/agent/developer_views` | Snippet, SnippetFolder |
| Scheduling | `/dashboard/agent/*/schedule/*` | `views/agent/scheduling_views` | AgentTimeBlock, TaskCategory, WeeklyPlan, RecurringBlock |
| Client Marketing | `/dashboard/client/marketing/*` | `views/marketing/marketing_views` | MarketingPost, MarketingPlan, ClientSocialAccount |
| Client Website | `/dashboard/client/website/*` | `views/client/service_management_views` | WebsiteProject, WebsitePhase |
| Website Builder | `/dashboard/client/website-builder/*` | `views/website/website_views` | WebsiteProject, WebsiteCategory, WebsiteType |
| Courses | `/dashboard/client/courses/*` | `views/courses/course_views` | Course, CourseModule, CourseLesson, CourseProgress |
| Support | `/dashboard/client/support/*` | `views/support/support_views` | SupportTicket, TicketMessage |
| Messaging | `/dashboard/*/messages` | `views/messaging/messaging_views` | Message (Django) + MongoDB (realtime) |
| Billing | `/dashboard/client/billing/*` | `views/billing/billing_views` | Invoice, ClientMarketingSubscription, MarketingPlanTier |
| Wallet | `/dashboard/client/wallet` | `views/billing/billing_views` | Wallet, Transaction, RedeemCode |
| Notifications | `/dashboard/*/notifications` | `views/notifications/notification_views` | Notification + MongoDB (notification service) |
| Video Calls | (overlay component) | `views/communication/communication_views` | — (WebRTC peer-to-peer) |

### 5.2 API Sub-Modules (Frontend)

| Module File | Domain | Key Functions |
|-------------|--------|---------------|
| `lib/api/auth.ts` | Authentication | login, register, OAuth, verification |
| `lib/api/billing.ts` | Billing & Payments | subscriptions, invoices, payment methods |
| `lib/api/clients.ts` | Client Management | CRUD, assignment, status updates |
| `lib/api/content.ts` | Content Management | posts, scheduling, calendar |
| `lib/api/developer.ts` | Developer Tools | projects, phases, tasks, snippets, plans |
| `lib/api/marketing.ts` | Marketing | plans, pillars, audiences, templates |
| `lib/api/messaging.ts` | Messaging | DMs, groups, channels, file uploads |
| `lib/api/projects.ts` | Project Management | project details, questionnaire |
| `lib/api/quotes.ts` | Quotes | CRUD, line items, public links, PDF, AI suggestions |
| `lib/api/scheduling.ts` | Scheduling | time blocks, recurring, weekly plans |
| `lib/api/search.ts` | Global Search | cross-domain search |
| `lib/api/social.ts` | Social Media | accounts, metrics, OAuth |
| `lib/api/adsManager.ts` | Ads Manager | campaigns, ad sets, ads, audiences, reports |

---

## 6. Component Architecture

### 6.1 Key Component Counts
- **Total components:** 359
- **Admin:** 15+ components
- **Agent/Scheduling:** 15+ components (CommandCenter, DaySchedule, WeeklyPlanView, FocusTimer, etc.)
- **Marketing:** 60+ components across 15 subdirectories
- **Ads Manager:** 22 components (wizards, tables, charts, planners)
- **Developer/Website:** 20+ components
- **Client:** 10+ components
- **Call/WebRTC:** 8 components (CallProvider, CallWindow, CallControls, ParticipantGrid, etc.)
- **Common/UI:** 30+ reusable components
- **Dashboard layout:** 40+ components (navigation, billing, content, dialogs, messaging, social)
- **Portal/CRM:** 10+ components with tests
- **Quotes:** 10+ components

### 6.2 Key Interactive Features

**Drag-and-Drop (dnd-kit):**
- Content calendar — drag posts between dates
- Task management — drag tasks between status columns
- Quote line items — reorder via drag
- Schedule time blocks — drag to reschedule

**Command Palette (Cmd+K):**
- Global search across all domains
- Quick navigation to any page
- Action shortcuts

**Focus Timer:**
- Pomodoro-style timer for agents
- Integrated with scheduling system

**Content Calendar:**
- Month/week/day views
- Drag-drop post scheduling
- Platform filtering
- Status color coding

**Rich Text/Markdown:**
- React Markdown with Prism syntax highlighting
- Used in project plans, strategy docs, notes

**Charts (Recharts):**
- Revenue charts, performance graphs
- Social media analytics
- Budget utilization
- Campaign performance

---

## 7. Infrastructure

### 7.1 Services Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Nginx (443/80)                       │
│   Reverse proxy, SSL termination, rate limiting          │
└──────┬──────────┬──────────┬──────────┬─────────────────┘
       │          │          │          │
  ┌────▼────┐ ┌──▼───┐ ┌───▼────┐ ┌───▼──────────┐
  │ Next.js │ │Django│ │Realtime│ │Notification  │
  │ :3000   │ │:8000 │ │:8004   │ │Realtime :8000│
  │ React19 │ │DRF   │ │SocketIO│ │SocketIO (TS) │
  └─────────┘ └──┬───┘ └───┬────┘ └──────┬───────┘
                 │         │              │
          ┌──────▼─────────▼──────────────▼──────┐
          │            RabbitMQ :5672              │
          │     (marketing.events, website.events) │
          └──────────────────────────────────────-─┘
                 │         │              │
          ┌──────▼──┐ ┌───▼────┐ ┌──────▼──┐
          │PostgreSQL│ │MongoDB │ │  Redis   │
          │  :5432   │ │ :27017 │ │  :6379   │
          │Core data │ │Messages│ │Cache/Sess│
          └──────────┘ └────────┘ └─────────┘
                 │
          ┌──────▼──────┐
          │Celery Worker │
          │(background)  │
          └──────────────┘

  Additional: Coturn (WebRTC TURN :3478), Prometheus (:9090), Grafana (:3000)
```

### 7.2 Databases
- **PostgreSQL 15:** Core application data (users, clients, invoices, projects, marketing, etc.)
- **MongoDB 7:** Real-time data (messages, notifications) — two databases: `montrose_realtime`, `montrose_notifications`
- **Redis 7:** Session cache (db0), Celery results (db1), notification cache (db4)

### 7.3 Docker Compose
- **5 networks:** public_bridge (external), frontend-net, backend-net, db-net (isolated), egress-net (outbound only)
- **8 persistent volumes:** postgres, mongodb, redis, rabbitmq, prometheus, grafana, coturn
- **Health checks:** on all services (pg_isready, mongosh ping, redis-cli ping, HTTP health endpoints)

### 7.4 Security
- **Rate limiting:** API 60/min, auth 5/min, WebSocket 10/sec
- **HSTS:** enabled with preload
- **CORS:** restricted to localhost (dev) and montrose.agency (prod)
- **JWT:** access + refresh token rotation
- **Token encryption:** Fernet for social media OAuth tokens
- **Inter-service auth:** SERVICE_TO_SERVICE_SECRET for microservice communication
- **Secrets:** Infisical Machine Identity → injected at deploy time

### 7.5 Deployment
- **CI/CD:** GitHub Actions → self-hosted runner on production VPS
- **Process:** push to main → montrose-deploy-runner → pull code → load secrets from Infisical → rebuild Docker images → docker compose up -d → run migrations → collect static
- **SSL:** certificates mounted at /etc/nginx/certs/
- **Monitoring:** Prometheus scraping (Django, realtime, Nginx, RabbitMQ) → Grafana dashboards
- **VPN:** WireGuard on 10.8.0.x for admin access to Grafana/Prometheus

### 7.6 File Storage
- **Provider:** Backblaze B2 via django-storages
- **Custom storage:** `MontroseB2Storage` in `server/api/storage.py`
- **Types:** avatars (ImageField), phase images, chat files, website versions (zip), course thumbnails

---

## 8. Key Technical Patterns

### 8.1 Frontend Patterns
- **Server components by default** — `'use client'` only for interactivity
- **ApiService singleton** — all HTTP through `lib/api.ts`, never raw `fetch()`
- **React Query** — server state management, caching, optimistic updates
- **Typed API functions** — every endpoint has a typed function with proper generics
- **Context providers** — auth, sidebar, socket, notification-socket, guest, unread-messages
- **Custom hooks per domain** — useAdsManager, useDeveloperProjects, useSchedulingEngine, etc.
- **Design tokens** — `lib/design-tokens.ts` + CSS custom properties in `globals.css`
- **Phosphor icons** — NOT Lucide (this is an architecture rule)
- **Framer Motion** — all animations, duration tokens: fast=150ms, default=200ms, slow=300ms

### 8.2 Backend Patterns
- **DRF ViewSets** — ModelViewSet with role-based queryset scoping
- **Custom permissions** — IsAuthenticated, IsAgent, IsAdmin, IsClient
- **Service layer** — business logic in `server/api/services/`, not in views or serializers
- **Celery tasks** — async work in `server/api/tasks/`, routed to named queues
- **Signals** — `server/api/signals.py` for post-save triggers
- **UUID primary keys** — all models use UUID PKs
- **JSON fields** — used extensively for flexible data (questionnaire answers, line items, settings, commits)

### 8.3 Type System
- **Core types:** `client/lib/types.ts` — User, Client, Agent, Invoice, MarketingPost, etc.
- **Domain types:** `client/lib/types/` — ads-manager.ts, marketing.ts, scheduling.ts, developer.ts, crm.ts, quote.ts, categories.ts
- **Website types:** `client/lib/websiteTypes.ts` — WebsiteProject, Phase, Domain, Hosting
- **Strict TypeScript** — no `any`, all API responses typed

---

## 9. Celery Task Schedule

| Task | Schedule | Queue | Purpose |
|------|----------|-------|---------|
| Instagram sync | Every 4 hours | instagram | Sync account metrics |
| YouTube sync | Every 6 hours | youtube | Sync channel metrics |
| Analytics aggregation | Daily 2:00 AM | analytics | Aggregate daily metrics |
| **Client health score recalculation** | **Daily 3:00 AM** | **analytics** | **Recalculate ClientHealthScore for all active clients** |
| Weekly reports | Monday 9:00 AM | reports | Generate client reports |
| Invoice notifications | Daily 9:00 AM | maintenance | Send overdue reminders |
| Task overdue checks | Daily 9:00 AM | maintenance | Flag overdue tasks |
| Monthly performance | 1st of month 10:00 AM | reports | Generate monthly reports |
| Recurring time blocks | Daily midnight | maintenance | Generate recurring schedule blocks |
| **Generate scheduled reports** | **Daily 6:00 AM** | **reports** | **Run SavedReport configs with weekly/monthly schedules** |
| **Admin daily digest** | **Daily 8:00 AM** | **reports** | **Email admin summary: attention items, revenue, new clients, open tickets** |

---

## 10. External Integrations

| Service | Purpose | Configuration |
|---------|---------|---------------|
| **PayPal** | Subscriptions, one-time payments, course purchases | Client ID + Secret, webhook endpoint |
| **Google OAuth** | Social login, YouTube API access | Client ID + Secret + redirect URI |
| **Instagram API** | OAuth, metrics sync, post tracking | Client ID + Secret + redirect URI |
| **Backblaze B2** | File storage (avatars, uploads, versions) | Application Key + Key ID + Bucket |
| **Resend** | Transactional email delivery | API key |
| **Coturn** | WebRTC TURN server for video calls | Shared secret for HMAC credentials |
| **Infisical** | Secrets management (deploy-time injection) | Machine Identity token |
| **Sentry** | Error tracking and monitoring | DSN |
| **Cloudflare** | DNS, CDN, DDoS protection | Trusted proxy IPs in Nginx |
