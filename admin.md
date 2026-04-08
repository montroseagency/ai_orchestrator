# Montrroase Admin Dashboard — Complete Redesign Architecture

---

## Executive Summary

The current admin dashboard fails because it treats the admin as a passive viewer with scattered, disconnected pages. The redesign transforms it into a **mission control center** built around three core portals — **CRM**, **Team**, and **Operations** — each functioning as a self-contained command center with deep drill-down capabilities. The admin becomes the strategic operator of the agency, not a glorified client.

### Core Problems Solved

| Problem | Current State | New State |
|---|---|---|
| CRM is just "add client" | Single form page | Full CRM portal with pipeline, analytics, work tracking, team assignments |
| No visibility into work | Admin can't see what agents do | Every client card shows real-time work feed, agent activity, deliverables |
| Agent management is flat | Basic list view | Team portal with performance dashboards, task delegation, messaging, capacity planning |
| Messaging buried in sidebar | Disconnected chat page | Messaging embedded contextually in Team portal and CRM |
| Admin = Client identity | Company page is a client profile | Dedicated Company Settings with agency identity, branding, bank config, service catalog |
| Reports don't work | Placeholder pages | Functional reporting engine in every portal with exports |
| Single agent per type | One marketing + one dev agent per client | Multi-agent teams per client with role assignments |
| No task delegation | Admin can't assign work | Full task system: admin → agent, with tracking in both dashboards |

---

## 1. Information Architecture

### 1.1 New Sidebar Structure

```
┌─────────────────────────────────┐
│  MONTRROASE                     │
│  [Agency Logo]                  │
│                                 │
│  ◆ Command Center     ← HOME   │
│                                 │
│  ─── PORTALS ───                │
│  ◆ CRM Portal                  │
│  ◆ Team Portal                 │
│  ◆ Operations Portal            │
│                                 │
│  ─── TOOLS ───                  │
│  ◆ Approvals                    │
│  ◆ Reports Hub                  │
│  ◆ Courses Manager              │
│                                 │
│  ─── SETTINGS ───               │
│  ◆ Company Settings             │
│  ◆ Service Catalog              │
│  ◆ Notifications                │
│                                 │
│  [Admin Avatar]                 │
│  [Notification Bell]            │
└─────────────────────────────────┘
```

**What's removed from the sidebar:**
- Messaging (→ moved into Team Portal)
- Client Management (→ absorbed into CRM Portal)
- Agent Management (→ absorbed into Team Portal)
- Revenue Analytics (→ absorbed into Operations Portal)
- Invoice Management (→ absorbed into Operations Portal)
- Support (→ absorbed into Operations Portal)

**Key principle:** The sidebar has exactly 3 portals + 3 tools + 3 settings. Everything else is accessed by drilling into a portal. This eliminates the "20 sidebar items" problem.

---

## 2. Command Center (Home Dashboard)

**Route:** `/dashboard/admin/`

The landing page. A single-screen strategic overview that answers: "What needs my attention right now?"

### 2.1 Layout Structure

```
┌──────────────────────────────────────────────────────────────┐
│  Good morning, [Name]                     [Search] [⚡ Quick Actions]  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─── ATTENTION REQUIRED ──────────────────────────────────┐ │
│  │ 🔴 3 overdue invoices ($4,200)    [View]                │ │
│  │ 🟡 2 client reviews waiting       [Review]              │ │
│  │ 🟡 1 agent request pending        [Approve]             │ │
│  │ 🔵 5 support tickets open         [Triage]              │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌─── KPI STRIP ──────────────────────────────────────────┐  │
│  │ MRR          Active       Capacity    Client Health     │  │
│  │ $24,500      18 clients   72%         ████████░░ 82%    │  │
│  │ ▲ 12% MoM   +2 this mo   3 slots     2 at-risk         │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─── REVENUE (30d) ────┐  ┌─── CLIENT PIPELINE ─────────┐  │
│  │                       │  │                              │  │
│  │  [Area chart]         │  │  Lead → Onboarding → Active │  │
│  │  Recurring / OneTime  │  │  [Funnel visualization]     │  │
│  │                       │  │                              │  │
│  └───────────────────────┘  └──────────────────────────────┘  │
│                                                              │
│  ┌─── RECENT ACTIVITY FEED ──────────────────────────────┐   │
│  │ 10:32  Agent Sarah posted 3 pieces for ClientX        │   │
│  │ 10:15  Invoice #INV-0042 paid by ClientY ($800)       │   │
│  │ 09:50  Website project "ClientZ" moved to Review      │   │
│  │ 09:30  New support ticket from ClientW (billing)      │   │
│  │ [Load more...]                                        │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─── TEAM SNAPSHOT ──────┐  ┌─── UPCOMING ──────────────┐   │
│  │ Online: 4/6 agents      │  │ Today: 3 deadlines        │   │
│  │ [Avatar] Sarah - 4 tasks│  │ This week: 2 renewals     │   │
│  │ [Avatar] Mike - 2 tasks │  │ Invoice due: $3,400       │   │
│  │ [Avatar] Ana - idle     │  │ [Full calendar →]         │   │
│  └─────────────────────────┘  └───────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Components Breakdown

**Attention Required Panel**
- Aggregates all actionable items from across the platform
- Sorted by urgency (overdue → pending → informational)
- Each item is clickable → deep-links to the relevant portal/page
- Badge count shown on the Command Center sidebar icon
- Categories: overdue invoices, pending approvals, client reviews, support tickets, agent requests, expiring domains/SSL, at-risk clients

**KPI Strip**
- 4 key metrics with sparkline trends
- MRR (Monthly Recurring Revenue) with month-over-month delta
- Active Clients count with net change
- Team Capacity (aggregate percentage across all agents)
- Client Health Score (average, with count of at-risk)

**Revenue Chart**
- 30-day rolling area chart
- Stacked: recurring revenue vs one-time revenue
- Hover for daily breakdown
- Quick toggles: 7d / 30d / 90d / YTD

**Client Pipeline**
- Horizontal funnel: Lead → Onboarding → Active → At-Risk → Churned
- Click any stage → filters CRM Portal to that segment

**Activity Feed**
- Chronological feed of all significant platform events
- Filterable by: clients, agents, billing, projects, content
- Each entry links to the source

**Team Snapshot**
- Online status of all agents (from Socket.IO presence)
- Current task count per agent
- Click agent → opens their profile in Team Portal

**Upcoming**
- Next 7 days of deadlines, renewals, invoice due dates
- Click → opens relevant item

### 2.3 Quick Actions (⚡ Button)

A command-palette-style dropdown for common admin actions:

- Add New Client
- Create Invoice
- Assign Agent to Client
- Send Announcement to All Agents
- Create Task for Agent
- Generate Report
- Create Redemption Code

---

## 3. CRM Portal

**Route:** `/dashboard/admin/crm`

This replaces the old "Client Management" page. It's a full command-center-style portal (matching the agent's command center pattern) dedicated to client relationship management.

### 3.1 CRM Portal Layout

```
┌──────────────────────────────────────────────────────────────┐
│  CRM Portal                    [Search] [Filters] [+ Client] │
├──────────┬───────────────────────────────────────────────────┤
│          │                                                    │
│  VIEWS   │  ┌─ PIPELINE VIEW (default) ─────────────────────┐│
│          │  │                                                ││
│ ◆Pipeline│  │  LEAD    ONBOARDING   ACTIVE   AT-RISK  PAUSED││
│ ◆Board   │  │  ┌───┐   ┌───┐       ┌───┐    ┌───┐   ┌───┐ ││
│ ◆Table   │  │  │   │   │   │       │   │    │   │   │   │ ││
│ ◆Map     │  │  │C1 │   │C4 │       │C6 │    │C9 │   │C11│ ││
│          │  │  │   │   │   │       │C7 │    └───┘   └───┘ ││
│ ──────── │  │  │C2 │   │C5 │       │C8 │                   ││
│          │  │  │   │   └───┘       └───┘                   ││
│ SEGMENTS │  │  │C3 │                                        ││
│          │  │  └───┘                                        ││
│ All (18) │  │                                                ││
│ Active(12)│ │  [Drag clients between columns]                ││
│ At-Risk(2)│ └────────────────────────────────────────────────┘│
│ Overdue(3)│                                                   │
│ New (1)  │                                                    │
│          │                                                    │
│ ──────── │                                                    │
│ TAGS     │                                                    │
│ #ecomm   │                                                    │
│ #saas    │                                                    │
│ #local   │                                                    │
└──────────┴───────────────────────────────────────────────────┘
```

### 3.2 CRM Views

**Pipeline View (Kanban)**
- Drag-and-drop clients between status columns
- Columns: Lead → Onboarding → Active → At-Risk → Paused → Churned
- Each card shows: company name, logo, MRR, health score, assigned team, days in stage
- Color-coded by health: green (healthy), yellow (needs attention), red (at-risk)

**Board View**
- Card grid layout, larger cards with more detail
- Sortable by: revenue, health, last activity, name
- Group by: status, industry, plan tier, assigned agent

**Table View**
- Spreadsheet-style with sortable/filterable columns
- Columns: Company, Status, Plan, MRR, Health, Marketing Agent(s), Dev Agent(s), Last Activity, Payment Status
- Inline editing for quick status changes
- Bulk actions: assign agent, change status, export

**Map View (optional/future)**
- Geographic view of clients if location data exists

### 3.3 Client Detail Page

**Route:** `/dashboard/admin/crm/[clientId]`

When you click any client card, you enter a full client detail page with tabbed navigation:

```
┌──────────────────────────────────────────────────────────────┐
│  ← Back to CRM    ClientX Corp                [⋯ Actions]    │
│  ████ Health: 85/100    Plan: Pro    MRR: $1,200    Active   │
├──────────────────────────────────────────────────────────────┤
│  [Overview] [Work Feed] [Marketing] [Website] [Team] [Billing] [Notes] │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  (Tab content renders here)                                  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Tab: Overview**
- Client info card (company, industry, contact, timezone, size)
- Service settings (which services are active)
- Health score breakdown (billing health, engagement, deliverable quality, response time)
- Key metrics: posts this month, project progress %, open invoices, last login
- Quick actions: message client, create invoice, assign agent

**Tab: Work Feed**
This is the critical missing piece — a chronological feed of ALL work done for this client:
- Marketing posts created/published
- Website phase completions
- Invoices sent/paid
- Agent notes added
- Support tickets opened/resolved
- Campaign launches
- Meetings/calls logged
- Each entry shows: timestamp, agent who did it, description, status
- Filterable by: date range, agent, work type
- This gives the admin full visibility into what has actually been done

**Tab: Marketing**
- Content calendar (read-only view of agent's calendar for this client)
- Post gallery with statuses
- Campaign list with progress bars
- Social account metrics (followers, engagement trends)
- Platform breakdown charts

**Tab: Website**
- Project status with phase progress
- Timeline visualization
- Phase details with images and updates
- Domain/hosting status
- Quote history

**Tab: Team**
- Assigned agents list (multiple marketing + multiple dev agents)
- Agent assignment manager:
  ```
  ┌─ ASSIGNED TEAM ────────────────────────────┐
  │                                              │
  │  Marketing Team                              │
  │  ┌──────────┐  ┌──────────┐  [+ Assign]    │
  │  │ Sarah M. │  │ James K. │                 │
  │  │ Lead     │  │ Support  │                 │
  │  │ 12 posts │  │ 4 posts  │                 │
  │  └──────────┘  └──────────┘                 │
  │                                              │
  │  Development Team                            │
  │  ┌──────────┐  [+ Assign]                   │
  │  │ Mike R.  │                                │
  │  │ Lead Dev │                                │
  │  │ Phase 3  │                                │
  │  └──────────┘                                │
  └──────────────────────────────────────────────┘
  ```
- Each agent card shows their contribution to this specific client
- Role within client team: Lead, Support, Reviewer
- Assignment history (who was assigned when, for how long)

**Tab: Billing**
- Invoice history table
- Payment timeline
- Outstanding balance
- Subscription details
- Wallet balance and transactions
- Revenue from this client over time (chart)

**Tab: Notes**
- Admin's private notes about this client
- Tagged, searchable
- Timeline of important decisions/conversations

### 3.4 Multi-Agent Team Assignment (Data Model Change)

**Current model:** Client has `marketing_agent` (FK) and `website_agent` (FK) — one each.

**New model:**

```python
class ClientTeamAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='team_assignments')
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='client_assignments')
    role = models.CharField(max_length=20, choices=[
        ('lead', 'Lead'),
        ('support', 'Support'),
        ('reviewer', 'Reviewer'),
    ])
    department = models.CharField(max_length=20, choices=[
        ('marketing', 'Marketing'),
        ('development', 'Development'),
    ])
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['client', 'agent']  # An agent can only be assigned once per client
        ordering = ['department', 'role']
```

**Migration path:** Keep the old FK fields as deprecated, create a data migration that copies existing assignments into the new M2M table, then gradually update all views/serializers to use the new model.

### 3.5 Client Health Score (New Feature)

Automated health scoring that gives the admin an at-a-glance understanding of each client relationship:

```python
class ClientHealthScore(models.Model):
    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name='health_score')
    overall_score = models.IntegerField(default=100)  # 0-100

    # Component scores (0-100 each)
    billing_health = models.IntegerField(default=100)
    # On-time payments, no outstanding invoices = 100
    # Overdue invoices, failed payments = decreases

    engagement_health = models.IntegerField(default=100)
    # Client login frequency, content approvals speed, response time

    deliverable_health = models.IntegerField(default=100)
    # Are posts being created on schedule? Are project phases on time?

    satisfaction_health = models.IntegerField(default=100)
    # Support ticket frequency, sentiment of communications

    last_calculated = models.DateTimeField(auto_now=True)
```

**Celery task:** Recalculate health scores daily at 3 AM. When score drops below 60, flag as "at-risk" and add to the admin's Attention Required panel.

---

## 4. Team Portal

**Route:** `/dashboard/admin/team`

Replaces the old "Agent Management" page AND absorbs the sidebar Messaging page. This is the admin's hub for managing the entire team.

### 4.1 Team Portal Layout

```
┌──────────────────────────────────────────────────────────────┐
│  Team Portal                   [Search] [+ Add Agent]        │
├──────────┬───────────────────────────────────────────────────┤
│          │                                                    │
│  VIEWS   │  (Active view content)                             │
│          │                                                    │
│ ◆Overview│                                                    │
│ ◆Roster  │                                                    │
│ ◆Workload│                                                    │
│ ◆Messages│                                                    │
│ ◆Tasks   │                                                    │
│          │                                                    │
│ ──────── │                                                    │
│          │                                                    │
│ DEPTS    │                                                    │
│ All (6)  │                                                    │
│ Mktg (4) │                                                    │
│ Dev (2)  │                                                    │
│          │                                                    │
│ ──────── │                                                    │
│ ONLINE   │                                                    │
│ 🟢Sarah  │                                                    │
│ 🟢Mike   │                                                    │
│ 🟡Ana    │                                                    │
│ ⚫James  │                                                    │
└──────────┴───────────────────────────────────────────────────┘
```

### 4.2 Team Overview

The default landing view. A dashboard showing team-wide metrics:

```
┌─── TEAM HEALTH ────────────────────────────────────────────┐
│                                                             │
│  Total Agents: 6    Online: 4    Avg Capacity: 72%         │
│                                                             │
│  ┌── Capacity Bars ──────────────────────────────────────┐  │
│  │ Sarah    ████████████████░░░░  80% (4/5 clients)      │  │
│  │ Mike     ████████████░░░░░░░░  60% (3/5 clients)      │  │
│  │ Ana      ██████████████████░░  90% (9/10 clients)     │  │
│  │ James    ████████░░░░░░░░░░░░  40% (2/5 clients)      │  │
│  │ Lisa     ████████████████████  100% (5/5 clients) ⚠️  │  │
│  │ Tom      ██████░░░░░░░░░░░░░░  30% (3/10 clients)     │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌── Performance (30d) ────┐  ┌── Task Completion ───────┐  │
│  │ [Stacked bar chart]     │  │ [Donut chart]            │  │
│  │ Posts / Phases / Tasks  │  │ Done: 42  In Progress: 8 │  │
│  │ per agent               │  │ Overdue: 3               │  │
│  └─────────────────────────┘  └──────────────────────────┘  │
│                                                             │
│  ┌── Recent Agent Activity ──────────────────────────────┐  │
│  │ Sarah published 3 posts for ClientX           10:32   │  │
│  │ Mike moved Phase 3 to "Review" for ClientZ    10:15   │  │
│  │ Ana created campaign "Summer Push"            09:50   │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 Team Roster

Grid or list of all agents with detailed cards:

```
┌─── AGENT CARD ──────────────────────┐
│  [Avatar]  Sarah Mitchell           │
│  Marketing Agent · Senior           │
│  ──────────────────────────         │
│  Clients: 4/5       Posts (30d): 47 │
│  Tasks Done: 12     Rating: 4.8/5   │
│  ──────────────────────────         │
│  Assigned Clients:                  │
│  ClientX, ClientY, ClientZ, ClientW │
│  ──────────────────────────         │
│  [View Profile] [Message] [Assign]  │
└─────────────────────────────────────┘
```

Clicking "View Profile" opens the Agent Detail Page.

### 4.4 Agent Detail Page

**Route:** `/dashboard/admin/team/[agentId]`

```
┌──────────────────────────────────────────────────────────────┐
│  ← Back to Team    Sarah Mitchell          [Message] [Edit]  │
│  Marketing Agent · Senior · Online 🟢                        │
├──────────────────────────────────────────────────────────────┤
│  [Overview] [Clients] [Work Log] [Tasks] [Schedule] [Reports] │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  (Tab content)                                               │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Tab: Overview**
- Profile info, specialization, department
- Capacity meter (current clients vs max)
- Key stats: posts created (30d), tasks completed, avg response time
- Performance trend chart (monthly)
- Skills/certifications

**Tab: Clients**
- List of assigned clients with contribution summary
- For each client: what role (lead/support), posts created, hours logged
- Quick reassign capability

**Tab: Work Log**
- Chronological feed of everything this agent has done
- Posts published, phases completed, tasks finished, messages sent
- Filterable by client, date range, work type
- Exportable for performance reviews

**Tab: Tasks**
- All tasks assigned to this agent (both from admin and self-created)
- Status: pending, in progress, completed, overdue
- Admin can create new tasks directly here (these appear in the agent's command center)

**Tab: Schedule**
- Read-only view of the agent's time-block calendar
- See how they're allocating their time
- Identify availability for new assignments

**Tab: Reports**
- Agent-specific performance reports
- Weekly/monthly summaries
- Client satisfaction metrics
- Comparison to team averages

### 4.5 Workload View

A birds-eye capacity planning view:

```
┌─── WORKLOAD MATRIX ────────────────────────────────────────┐
│                                                             │
│              Sarah   Mike   Ana   James   Lisa   Tom        │
│  ClientX     ●lead                                         │
│  ClientY     ●supp          ●lead                          │
│  ClientZ            ●lead                  ●lead           │
│  ClientW     ●lead                 ●lead                   │
│  ClientV                    ●lead                  ●lead   │
│  ...                                                        │
│                                                             │
│  Capacity    80%    60%    90%    40%     100%    30%       │
│              4/5    3/5    9/10   2/5     5/5     3/10     │
│                                                             │
│  [Drag to reassign] [Auto-balance suggestion]              │
└─────────────────────────────────────────────────────────────┘
```

- Matrix showing which agent is on which client and in what role
- Capacity indicators per agent
- Drag-and-drop to reassign agents between clients
- "Auto-balance" button suggests optimal redistribution based on capacity and specialization

### 4.6 Team Messages (Replaces Sidebar Messaging)

**Route:** `/dashboard/admin/team/messages`

The full messaging interface, now contextually placed within the Team portal:

```
┌──────────────────────────────────────────────────────────────┐
│  Team Messages                            [New Message]      │
├────────────┬─────────────────────────────────────────────────┤
│            │                                                  │
│ CHANNELS   │  ┌─ #general ──────────────────────────────────┐│
│ #general   │  │                                              ││
│ #marketing │  │  Sarah: Hey, client X approved the batch     ││
│ #dev       │  │  Mike: Great, I'll update the phase          ││
│ #urgent    │  │  Admin: @Ana can you review the new posts?   ││
│            │  │                                              ││
│ ────────── │  │  [Message input]                             ││
│ DIRECT     │  └──────────────────────────────────────────────┘│
│ Sarah      │                                                  │
│ Mike       │                                                  │
│ Ana        │                                                  │
│            │                                                  │
│ ────────── │                                                  │
│ GROUPS     │                                                  │
│ ClientX Tm │                                                  │
│ Design Rev │                                                  │
└────────────┴─────────────────────────────────────────────────┘
```

Features:
- Team channels (department-based, project-based)
- Direct messages to any agent
- Client-team group chats (admin + assigned agents for a client)
- Message search
- File sharing
- Pinned messages
- @mentions with notifications

### 4.7 Admin Task Delegation System

**Route:** `/dashboard/admin/team/tasks`

A new feature allowing the admin to create and track tasks assigned to agents:

```python
class AdminTask(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_admin_tasks')
    assigned_to = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='admin_tasks')
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True)
    
    priority = models.CharField(max_length=10, choices=[
        ('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')
    ])
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('acknowledged', 'Acknowledged'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ])
    category = models.CharField(max_length=30, choices=[
        ('content_creation', 'Content Creation'),
        ('client_communication', 'Client Communication'),
        ('project_work', 'Project Work'),
        ('reporting', 'Reporting'),
        ('review', 'Review'),
        ('admin', 'Administrative'),
        ('other', 'Other'),
    ])
    
    due_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Agent's response
    agent_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Admin view:** Kanban board of all delegated tasks, filterable by agent, client, priority, status.

**Agent view:** These tasks appear in the agent's Command Center under a "From Admin" section, with the ability to acknowledge, update progress, and mark complete.

---

## 5. Operations Portal

**Route:** `/dashboard/admin/operations`

Consolidates all financial, support, and business operations into one portal.

### 5.1 Operations Portal Layout

```
┌──────────────────────────────────────────────────────────────┐
│  Operations Portal                         [Search] [Export]  │
├──────────┬───────────────────────────────────────────────────┤
│          │                                                    │
│  VIEWS   │  (Active view content)                             │
│          │                                                    │
│ ◆Revenue │                                                    │
│ ◆Invoices│                                                    │
│ ◆Payments│                                                    │
│ ◆Support │                                                    │
│ ◆Audit   │                                                    │
│          │                                                    │
└──────────┴───────────────────────────────────────────────────┘
```

### 5.2 Revenue Dashboard

Full financial analytics:

- MRR/ARR with trend
- Revenue by client (top 10 chart)
- Revenue by service line (marketing vs website)
- Revenue by plan tier
- Churn rate and churned revenue
- Payment collection rate
- Cash flow forecast (next 30/60/90 days based on invoices + subscriptions)
- Revenue cohort analysis (clients by signup month)

### 5.3 Invoice Management

Enhanced invoice system:

- Table of all invoices with filters (status, client, type, date range)
- Batch actions: send reminders, mark paid, export
- Invoice creation wizard
- Auto-invoice generation from phase completions
- Aging report (0-30, 31-60, 61-90, 90+ days)
- Payment verification queue (for bank transfers with proof uploads)

### 5.4 Payment Verification

Dedicated view for verifying bank transfer proofs:

```
┌─── PAYMENT VERIFICATION QUEUE ──────────────────────────────┐
│                                                               │
│  ┌─ PENDING (3) ──────────────────────────────────────────┐  │
│  │                                                         │  │
│  │  Invoice #INV-0042 · ClientX · $800                     │  │
│  │  Submitted: 2h ago                                      │  │
│  │  [View Proof Image]  [✓ Approve]  [✗ Reject]           │  │
│  │                                                         │  │
│  │  Invoice #INV-0038 · ClientY · $1,200                   │  │
│  │  Submitted: 5h ago                                      │  │
│  │  [View Proof Image]  [✓ Approve]  [✗ Reject]           │  │
│  │                                                         │  │
│  └─────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

### 5.5 Support Ticket Management

The admin's view of all support tickets:

- Queue with priority sorting
- Assignment to agents
- SLA tracking (response time, resolution time)
- Ticket categorization analytics
- Canned responses
- Escalation workflow

### 5.6 Audit Log

A searchable log of all system actions:

- Who did what, when, to which entity
- Filter by: user, action type, entity type, date range
- Export for compliance
- This is critical for the admin to understand what's happening

---

## 6. Company Settings (Replaces "Company = Client Profile")

**Route:** `/dashboard/admin/settings/company`

The admin's company is NOT a client. It has its own dedicated settings:

```
┌──────────────────────────────────────────────────────────────┐
│  Company Settings                                            │
├──────────────────────────────────────────────────────────────┤
│  [Profile] [Branding] [Banking] [Integrations] [Security]   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Tab: Profile                                                │
│  ─────────                                                   │
│  Agency Name: Montrroase                                     │
│  Legal Name: Montrroase LLC                                  │
│  Industry: Marketing Agency                                  │
│  Address: ...                                                │
│  Phone: ...                                                  │
│  Email: admin@montrroase.com                                 │
│  Tax ID: ...                                                 │
│  Timezone: ...                                               │
│                                                              │
│  Tab: Branding                                               │
│  ─────────                                                   │
│  Logo (light/dark variants)                                  │
│  Brand colors (used in invoices, quotes, emails)             │
│  Invoice header template                                     │
│  Email signature template                                    │
│  Quote cover page design                                     │
│                                                              │
│  Tab: Banking                                                │
│  ─────────                                                   │
│  Bank accounts for receiving payments                        │
│  PayPal merchant settings                                    │
│  Currency preferences                                        │
│  Payment terms defaults                                      │
│                                                              │
│  Tab: Integrations                                           │
│  ─────────                                                   │
│  PayPal API credentials                                      │
│  Social media API keys                                       │
│  Email provider (Resend) settings                            │
│  File storage (Backblaze) settings                           │
│                                                              │
│  Tab: Security                                               │
│  ─────────                                                   │
│  Two-factor authentication                                   │
│  Session management                                          │
│  API keys                                                    │
│  Audit log settings                                          │
│  Rate limit configuration                                    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Data model change:** Remove the pattern where admin has a Client record. Instead:

```python
class AgencyProfile(models.Model):
    """The agency's own profile — NOT a Client."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255, blank=True)
    logo = models.ImageField(upload_to='agency/', blank=True)
    logo_dark = models.ImageField(upload_to='agency/', blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField()
    tax_id = models.CharField(max_length=50, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    currency = models.CharField(max_length=3, default='USD')
    
    # Branding
    primary_color = models.CharField(max_length=7, default='#000000')
    secondary_color = models.CharField(max_length=7, default='#666666')
    accent_color = models.CharField(max_length=7, default='#0066FF')
    
    # Defaults
    default_payment_terms_days = models.IntegerField(default=30)
    invoice_prefix = models.CharField(max_length=10, default='INV')
    quote_prefix = models.CharField(max_length=10, default='QT')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

---

## 7. Service Catalog

**Route:** `/dashboard/admin/settings/catalog`

Manage the services the agency offers:

- Marketing plans and pricing tiers
- Website project types and base pricing
- Add-on services with pricing
- Course catalog management
- Redemption codes

This replaces scattered admin settings pages.

---

## 8. Approvals Hub

**Route:** `/dashboard/admin/approvals`

A centralized queue for everything requiring admin sign-off:

```
┌─── APPROVALS HUB ───────────────────────────────────────────┐
│                                                               │
│  [All] [Content] [Billing] [Agent Requests] [Client Changes] │
│                                                               │
│  ┌─ CONTENT APPROVALS (5) ─────────────────────────────────┐ │
│  │ Post batch from Sarah for ClientX (3 posts)    [Review] │ │
│  │ Campaign proposal "Summer Push" for ClientY    [Review] │ │
│  │ Website demo for ClientZ                       [Review] │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─ BILLING APPROVALS (2) ─────────────────────────────────┐ │
│  │ Bank transfer proof from ClientX ($800)     [Verify]    │ │
│  │ Discount request from Sarah for ClientW     [Review]    │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─ AGENT REQUESTS (1) ────────────────────────────────────┐ │
│  │ Mike requests new task category "UX Research" [Approve] │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## 9. Reports Hub

**Route:** `/dashboard/admin/reports`

Centralized reporting with templates and scheduling:

### Report Types:

**Client Reports**
- Individual client performance report
- Client health summary (all clients)
- Client retention/churn report

**Financial Reports**
- Monthly revenue report
- Invoice aging report
- Revenue by service line
- Profitability per client (revenue vs agent hours)

**Team Reports**
- Agent performance rankings
- Capacity utilization report
- Task completion rates
- Time allocation analysis

**Marketing Reports**
- Content output summary (posts per client, per platform)
- Social media growth report (followers, engagement across all clients)
- Campaign performance summary

**Website Reports**
- Project status summary (all active projects)
- Phase completion rates
- Average project timeline vs estimated

### Report Features:
- Schedule recurring reports (weekly/monthly email)
- Export as PDF or CSV
- Date range selection
- Compare periods (this month vs last month)
- Save custom report configurations

---

## 10. Route Architecture

```
/dashboard/admin/
├── /                                    → Command Center (home)
├── /crm/                               → CRM Portal (pipeline view)
│   ├── /crm/[clientId]/                → Client Detail (overview tab)
│   ├── /crm/[clientId]/work-feed       → Client Work Feed
│   ├── /crm/[clientId]/marketing       → Client Marketing View
│   ├── /crm/[clientId]/website         → Client Website View
│   ├── /crm/[clientId]/team            → Client Team Assignments
│   ├── /crm/[clientId]/billing         → Client Billing History
│   └── /crm/[clientId]/notes           → Client Notes
├── /team/                              → Team Portal (overview)
│   ├── /team/roster                    → Agent Roster
│   ├── /team/[agentId]/               → Agent Detail (overview tab)
│   ├── /team/[agentId]/clients        → Agent's Client List
│   ├── /team/[agentId]/work-log       → Agent Work Log
│   ├── /team/[agentId]/tasks          → Agent Tasks
│   ├── /team/[agentId]/schedule       → Agent Schedule View
│   ├── /team/[agentId]/reports        → Agent Reports
│   ├── /team/workload                 → Workload Matrix
│   ├── /team/messages/                → Team Messaging
│   └── /team/tasks/                   → Admin Task Board
├── /operations/                        → Operations Portal
│   ├── /operations/revenue            → Revenue Dashboard
│   ├── /operations/invoices           → Invoice Management
│   ├── /operations/payments           → Payment Verification
│   ├── /operations/support            → Support Tickets
│   └── /operations/audit              → Audit Log
├── /approvals/                         → Approvals Hub
├── /reports/                           → Reports Hub
├── /courses/                           → Course Management
└── /settings/
    ├── /settings/company              → Agency Profile
    ├── /settings/catalog              → Service Catalog
    └── /settings/notifications        → Notification Preferences
```

---

## 11. New Data Models Summary

```python
# ─── New Models ─────────────────────────────────────────

class AgencyProfile(models.Model):
    """Agency's own identity (replaces admin-as-client pattern)"""
    # See Section 6

class ClientTeamAssignment(models.Model):
    """M2M agent-client assignment with roles (replaces single FK)"""
    # See Section 3.4

class ClientHealthScore(models.Model):
    """Automated health scoring per client"""
    # See Section 3.5

class AdminTask(models.Model):
    """Tasks delegated by admin to agents"""
    # See Section 4.7

class ActivityLog(models.Model):
    """Universal activity tracking for feeds and audit"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    actor = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=50)  # created, updated, published, completed, etc.
    entity_type = models.CharField(max_length=50)  # post, phase, invoice, task, etc.
    entity_id = models.UUIDField()
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField()
    metadata = models.JSONField(default=dict)  # flexible extra data
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client', '-created_at']),
            models.Index(fields=['agent', '-created_at']),
            models.Index(fields=['entity_type', '-created_at']),
        ]

class AdminNote(models.Model):
    """Admin's private notes on clients"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    admin = models.ForeignKey(User, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='admin_notes')
    content = models.TextField()
    tags = models.JSONField(default=list)
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class SavedReport(models.Model):
    """Saved report configurations for recurring generation"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    report_type = models.CharField(max_length=50)
    config = models.JSONField()  # filters, date range, grouping, etc.
    schedule = models.CharField(max_length=20, choices=[
        ('none', 'Manual Only'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ], default='none')
    last_generated = models.DateTimeField(null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
```

---

## 12. Backend API Endpoints (New/Modified)

### CRM Endpoints
```
GET    /api/admin/crm/clients/                    → List with health scores, team, pipeline stage
GET    /api/admin/crm/clients/{id}/               → Full client detail
GET    /api/admin/crm/clients/{id}/work-feed/     → Paginated activity feed for client
GET    /api/admin/crm/clients/{id}/team/          → Team assignments for client
POST   /api/admin/crm/clients/{id}/team/          → Assign agent to client
DELETE /api/admin/crm/clients/{id}/team/{assignId} → Remove agent assignment
PATCH  /api/admin/crm/clients/{id}/team/{assignId} → Update role
GET    /api/admin/crm/clients/{id}/health/        → Health score breakdown
POST   /api/admin/crm/clients/{id}/notes/         → Create admin note
GET    /api/admin/crm/pipeline/                   → Pipeline summary (counts per stage)
```

### Team Endpoints
```
GET    /api/admin/team/overview/                   → Team metrics, capacity, activity
GET    /api/admin/team/agents/                     → Agent roster with stats
GET    /api/admin/team/agents/{id}/                → Agent detail
GET    /api/admin/team/agents/{id}/work-log/       → Agent activity feed
GET    /api/admin/team/agents/{id}/performance/    → Performance metrics
GET    /api/admin/team/workload/                   → Workload matrix data
POST   /api/admin/team/tasks/                      → Create admin task
GET    /api/admin/team/tasks/                      → List admin tasks
PATCH  /api/admin/team/tasks/{id}/                 → Update task status
```

### Operations Endpoints
```
GET    /api/admin/operations/revenue/              → Revenue analytics
GET    /api/admin/operations/revenue/forecast/     → Cash flow forecast
GET    /api/admin/operations/invoices/aging/       → Invoice aging report
GET    /api/admin/operations/support/stats/        → Support ticket analytics
GET    /api/admin/operations/audit-log/            → Paginated audit log
```

### Reports Endpoints
```
GET    /api/admin/reports/generate/                → Generate report by type + params
POST   /api/admin/reports/saved/                   → Save report config
GET    /api/admin/reports/saved/                    → List saved reports
POST   /api/admin/reports/saved/{id}/run/          → Run saved report
```

### Settings Endpoints
```
GET    /api/admin/settings/agency/                 → Agency profile
PATCH  /api/admin/settings/agency/                 → Update agency profile
GET    /api/admin/settings/catalog/                → Service catalog
```

---

## 13. Celery Tasks (New)

```python
# Health score recalculation — daily at 3 AM
@app.task(queue='analytics')
def recalculate_client_health_scores():
    """Recalculate health scores for all active clients."""
    pass

# Activity log aggregation — runs continuously
@app.task(queue='maintenance')
def log_activity(actor_id, action, entity_type, entity_id, client_id=None, agent_id=None, description='', metadata=None):
    """Create an ActivityLog entry. Called from signals and views."""
    pass

# Scheduled reports — based on SavedReport schedule field
@app.task(queue='reports')
def generate_scheduled_reports():
    """Find and generate all reports due today."""
    pass

# Admin daily digest — daily at 8 AM
@app.task(queue='reports')
def send_admin_daily_digest():
    """Email admin a summary: attention items, revenue, activity highlights."""
    pass
```

---

## 14. Signal Hooks for Activity Logging

```python
# In signals.py — auto-log important actions to ActivityLog

@receiver(post_save, sender=MarketingPost)
def log_post_activity(sender, instance, created, **kwargs):
    if instance.status == 'posted':
        log_activity.delay(
            actor_id=str(instance.created_by_id),
            action='published',
            entity_type='marketing_post',
            entity_id=str(instance.id),
            client_id=str(instance.client_id),
            description=f'Published post "{instance.title}" on {instance.platform}'
        )

@receiver(post_save, sender=Invoice)
def log_invoice_activity(sender, instance, **kwargs):
    if instance.status == 'paid':
        log_activity.delay(
            actor_id=str(instance.client.user_id),
            action='paid',
            entity_type='invoice',
            entity_id=str(instance.id),
            client_id=str(instance.client_id),
            description=f'Invoice #{instance.invoice_number} paid (${instance.total})'
        )

# Similar signals for: WebsiteProjectPhase, ProjectTask, SupportTicket, etc.
```

---

## 15. Frontend Component Architecture

### New Component Tree

```
components/dashboard/admin/
├── command-center/
│   ├── CommandCenter.tsx              → Main home dashboard
│   ├── AttentionPanel.tsx             → Urgent items queue
│   ├── KpiStrip.tsx                   → 4 KPI cards with sparklines
│   ├── RevenueChart.tsx               → 30d revenue area chart
│   ├── ClientPipeline.tsx             → Funnel visualization
│   ├── ActivityFeed.tsx               → Real-time activity stream
│   ├── TeamSnapshot.tsx               → Online agents + current tasks
│   ├── UpcomingPanel.tsx              → Deadlines/renewals
│   └── QuickActions.tsx               → Command palette for actions
│
├── crm/
│   ├── CrmPortal.tsx                  → Portal shell with sidebar
│   ├── views/
│   │   ├── PipelineView.tsx           → Kanban drag-drop
│   │   ├── BoardView.tsx              → Card grid
│   │   ├── TableView.tsx              → Spreadsheet view
│   │   └── ClientCard.tsx             → Reusable client card
│   ├── client-detail/
│   │   ├── ClientDetail.tsx           → Tabbed detail page shell
│   │   ├── ClientOverview.tsx         → Info + health + metrics
│   │   ├── ClientWorkFeed.tsx         → Activity timeline
│   │   ├── ClientMarketing.tsx        → Marketing read-only view
│   │   ├── ClientWebsite.tsx          → Website project view
│   │   ├── ClientTeam.tsx             → Team assignment manager
│   │   ├── ClientBilling.tsx          → Billing history
│   │   └── ClientNotes.tsx            → Admin notes
│   ├── HealthBadge.tsx                → Health score indicator
│   └── AddClientWizard.tsx            → Multi-step onboarding
│
├── team/
│   ├── TeamPortal.tsx                 → Portal shell with sidebar
│   ├── views/
│   │   ├── TeamOverview.tsx           → Team health dashboard
│   │   ├── TeamRoster.tsx             → Agent card grid/list
│   │   ├── WorkloadMatrix.tsx         → Capacity planning view
│   │   └── AgentCard.tsx              → Reusable agent card
│   ├── agent-detail/
│   │   ├── AgentDetail.tsx            → Tabbed agent page shell
│   │   ├── AgentOverview.tsx          → Profile + stats
│   │   ├── AgentClients.tsx           → Assigned clients
│   │   ├── AgentWorkLog.tsx           → Activity timeline
│   │   ├── AgentTasks.tsx             → Task list + create
│   │   ├── AgentSchedule.tsx          → Read-only calendar
│   │   └── AgentReports.tsx           → Performance reports
│   ├── messaging/
│   │   ├── TeamMessages.tsx           → Full messaging interface
│   │   ├── ChannelList.tsx            → Channel/DM sidebar
│   │   ├── MessageThread.tsx          → Message display
│   │   └── MessageInput.tsx           → Compose with file upload
│   └── tasks/
│       ├── AdminTaskBoard.tsx         → Kanban of delegated tasks
│       ├── TaskCreateModal.tsx        → Create task for agent
│       └── TaskCard.tsx               → Task display card
│
├── operations/
│   ├── OperationsPortal.tsx           → Portal shell
│   ├── RevenueDashboard.tsx           → Financial analytics
│   ├── InvoiceManager.tsx             → Invoice table + actions
│   ├── PaymentVerification.tsx        → Proof review queue
│   ├── SupportManager.tsx             → Ticket queue
│   └── AuditLog.tsx                   → Searchable log
│
├── approvals/
│   ├── ApprovalsHub.tsx               → Unified approval queue
│   ├── ContentApproval.tsx            → Content review
│   ├── BillingApproval.tsx            → Payment/discount review
│   └── AgentRequestApproval.tsx       → Agent request review
│
├── reports/
│   ├── ReportsHub.tsx                 → Report generator
│   ├── ReportBuilder.tsx              → Config builder
│   ├── ReportViewer.tsx               → Rendered report
│   └── SavedReports.tsx               → Saved configurations
│
└── settings/
    ├── CompanySettings.tsx            → Agency profile tabs
    ├── ServiceCatalog.tsx             → Service/pricing management
    └── NotificationSettings.tsx       → Alert preferences
```

### Key Shared Hooks

```typescript
// hooks/useAdminCRM.ts
export function useClientPipeline(filters: PipelineFilters) { ... }
export function useClientDetail(clientId: string) { ... }
export function useClientWorkFeed(clientId: string, page: number) { ... }
export function useClientHealth(clientId: string) { ... }
export function useClientTeam(clientId: string) { ... }

// hooks/useAdminTeam.ts
export function useTeamOverview() { ... }
export function useAgentDetail(agentId: string) { ... }
export function useAgentWorkLog(agentId: string, filters: WorkLogFilters) { ... }
export function useWorkloadMatrix() { ... }
export function useAdminTasks(filters: TaskFilters) { ... }

// hooks/useAdminOperations.ts
export function useRevenueDashboard(period: string) { ... }
export function useInvoiceAging() { ... }
export function useAuditLog(filters: AuditFilters) { ... }

// hooks/useAdminReports.ts
export function useReportGenerator(type: string, config: ReportConfig) { ... }
export function useSavedReports() { ... }
```

---

## 16. Implementation Priority & Phases

### Phase 1 — Foundation (Week 1-2)
1. Create `AgencyProfile` model and migrate admin away from client identity
2. Create `ClientTeamAssignment` model and migrate existing FK assignments
3. Create `ActivityLog` model and add signal hooks for key actions
4. Create `AdminTask` model
5. Restructure admin sidebar to new 3-portal layout
6. Build Command Center home page

### Phase 2 — CRM Portal (Week 3-4)
1. Build CRM Portal shell with pipeline/board/table views
2. Implement Client Detail page with all tabs
3. Build team assignment UI (multi-agent per client)
4. Implement Client Work Feed (powered by ActivityLog)
5. Build Client Health Score system + Celery task
6. Build Admin Notes feature

### Phase 3 — Team Portal (Week 5-6)
1. Build Team Portal shell with overview/roster/workload views
2. Implement Agent Detail page with all tabs
3. Build Workload Matrix with drag-drop reassignment
4. Move Messaging into Team Portal
5. Build Admin Task delegation system
6. Connect tasks to agent Command Center

### Phase 4 — Operations & Polish (Week 7-8)
1. Build Operations Portal with revenue dashboard
2. Enhanced invoice management with aging
3. Payment verification queue
4. Support ticket management view
5. Audit Log
6. Reports Hub with generation and scheduling
7. Company Settings pages
8. Service Catalog management

### Phase 5 — Refinement (Week 9-10)
1. Real-time updates (WebSocket for activity feed, task status changes)
2. Daily digest email for admin
3. Performance optimization (pagination, lazy loading, caching)
4. Mobile responsiveness for admin dashboard
5. Onboarding walkthrough for admin
6. Export/PDF generation for all reports

---

## 17. Key Interaction Flows

### Flow: Admin Onboards a New Client

```
1. Admin clicks [+ Client] in CRM Portal
2. Multi-step wizard:
   Step 1: Company info (name, industry, contact)
   Step 2: Services (marketing ✓, website ✓, courses ✓)
   Step 3: Plan selection (starter/pro/premium per service)
   Step 4: Team assignment (select marketing team + dev team)
   Step 5: Review & create
3. Client created → appears in Pipeline as "Onboarding"
4. Assigned agents get notified in their Command Center
5. Admin can track onboarding progress in client detail
```

### Flow: Admin Reviews Agent Work

```
1. Admin opens CRM Portal → clicks client
2. Goes to "Work Feed" tab
3. Sees chronological feed:
   - Posts created, approved, published
   - Website phases started, completed
   - Tasks finished
   - Messages exchanged
4. Can filter by agent to see individual contributions
5. Can drill into any item (click post → see post detail)
6. Notes any concerns → adds Admin Note
7. If issue found → creates AdminTask for agent
```

### Flow: Admin Delegates a Task

```
1. Admin opens Team Portal → Tasks view (or agent detail → Tasks tab)
2. Clicks [+ New Task]
3. Fills form: title, description, assign to agent, link to client (optional), priority, due date
4. Task created with status "pending"
5. Agent receives notification
6. Agent sees task in their Command Center under "From Admin" section
7. Agent clicks "Acknowledge" → status changes to "acknowledged"
8. Agent works on it, updates notes → status "in_progress"
9. Agent completes → status "completed"
10. Admin sees status update in real-time on their task board
```

### Flow: Admin Monitors Agency Health (Daily Routine)

```
1. Admin opens app → lands on Command Center
2. Checks Attention Required panel:
   - 2 overdue invoices → clicks [View] → goes to Operations/Invoices
   - 1 content waiting review → clicks [Review] → goes to Approvals
3. Glances at KPIs: MRR up 5%, one new client, capacity at 75%
4. Checks Activity Feed: sees Sarah finished a batch, Mike hit a blocker
5. Opens Team Portal → sees Mike is at 100% capacity
6. Opens Workload Matrix → drags one of Mike's clients to James (40% capacity)
7. Opens CRM → checks at-risk client → reviews health score breakdown
8. Sees billing health is low (overdue invoice) → creates reminder
9. Opens Reports → generates weekly performance PDF → emails to stakeholders
```

---

## 18. Design Tokens & Visual Language

To ensure the admin dashboard feels like a coherent mission control system:

### Color System
```css
/* Admin Portal uses a distinct palette from agent/client dashboards */
--admin-bg-primary: #0A0F1C;        /* Deep navy background */
--admin-bg-secondary: #111827;       /* Card backgrounds */
--admin-bg-tertiary: #1F2937;        /* Hover/active states */
--admin-border: #374151;             /* Subtle borders */

--admin-text-primary: #F9FAFB;       /* Primary text */
--admin-text-secondary: #9CA3AF;     /* Secondary text */
--admin-text-muted: #6B7280;         /* Muted text */

--admin-accent-blue: #3B82F6;        /* Primary actions */
--admin-accent-green: #10B981;       /* Success, revenue up */
--admin-accent-yellow: #F59E0B;      /* Warning, needs attention */
--admin-accent-red: #EF4444;         /* Urgent, overdue */
--admin-accent-purple: #8B5CF6;      /* Creative, campaigns */

/* Health score colors */
--health-excellent: #10B981;          /* 80-100 */
--health-good: #3B82F6;              /* 60-79 */
--health-warning: #F59E0B;           /* 40-59 */
--health-critical: #EF4444;          /* 0-39 */
```

### Typography
```css
--font-display: 'DM Sans', sans-serif;      /* Headers, KPIs */
--font-body: 'DM Sans', sans-serif;          /* Body text */
--font-mono: 'JetBrains Mono', monospace;    /* Data, codes */
```

### Component Patterns
- **Portal Shell:** Left sidebar (views/segments) + main content area. Consistent across CRM, Team, Operations.
- **Detail Pages:** Header with back nav + entity info → tab bar → tab content. Consistent for clients and agents.
- **Cards:** Rounded-lg, subtle border, hover elevation. Compact density for dashboards.
- **Activity Feed Items:** Avatar + timestamp + description + action link. Consistent everywhere feeds appear.
- **Status Badges:** Pill-shaped with color coding. Same color semantics across the entire admin dashboard.
- **Charts:** Recharts with the admin color palette. Consistent axis styling and tooltips.

---

This architecture gives the admin complete visibility and control over their agency. Every piece of information is at most 2 clicks away from the Command Center, and the three-portal structure (CRM, Team, Operations) creates clear mental models for where to find anything.