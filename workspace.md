# Team Workspace ("HQ") — Plan

# UI spec: see workspace_ui.md

## 1. Purpose

Montrroase currently mixes three audiences — admin, agents, and clients — into a single messaging inbox. Agents see client DMs next to internal team chats, with no structural boundary between "talking to the customer" and "talking to my coworkers." This is noisy and risks sensitive internal chatter leaking into client-adjacent threads.

**This plan splits messaging into two surfaces** and introduces a dedicated internal space ("HQ") that becomes the agency's internal operating system — the third side of the product alongside client-facing work and the admin's view of that work.

## 2. Goals

- **Hard separation** between client messaging and internal team comms at the data layer (not just UI).
- **Dedicated internal surface** (HQ) that agents and admin share, clients can never access.
- **Foundation for culture + ops features** — directory, wiki, announcements, recognition, HR-lite, etc. — without re-plumbing later.
- **Reuse existing infra** — Socket.IO realtime service, Backblaze B2, notification service, RabbitMQ — no parallel stacks.

## 3. Non-Goals

- Not replacing client messaging — that stays where it is, just simplified.
- Not a general-purpose Slack clone for external use.
- Not rebuilding the admin's management tooling (Agent Roster, Workload Matrix). HQ is the agent-facing counterpart, not a replacement.

## 4. Mental Model

Montrroase today has two clear sides:

1. **Client-facing work** — CRM, projects, marketing output
2. **Admin's view of that work** — management, oversight, approvals

What's missing is a third side: **the inside of the agency itself.** HQ is where agents exist as employees of a company, not just as executors of client work. The difference between "my Jira board" and "my company intranet + Slack + HR portal."

## 5. Scope

### 5.1 In scope — the Split

Two distinct surfaces, backed by the same realtime infrastructure but scoped apart at the data layer.

**Client Messaging (existing, simplified)**
- Lives at `/dashboard/agent/*/messages` and `/dashboard/client/*/messages`
- Agent sidebar stripped down: client DMs only, no Groups tab, no Channels tab
- Purpose: 1:1 client communication, quote discussions, content approval back-and-forth
- Admin retains full access

**Team Workspace — "HQ" (new)**
- New dedicated page, agents + admin only, clients cannot see or be added
- Slack-style: channels, threads, DMs, pinned announcements, presence
- Entry points:
  - Admin: `/dashboard/admin/team/workspace` (new tab in Team Portal, beside Overview / Roster / Workload Matrix)
  - Agent: `/dashboard/agent/marketing/management/workspace` and `/dashboard/agent/developer/management/workspace`

### 5.2 Feature Surface (full menu, phased)

HQ can eventually host twelve categories. Only category 1 (+ partial category 8) is specced in detail. The rest are surfaced here so the data model doesn't paint us into a corner.

| # | Category | Description | Phase |
|---|---|---|---|
| 1 | **Communication** | Channels, DMs, threads, announcements, huddles | **Phase 1–2** |
| 2 | Team Directory & Profiles | Agent-facing profiles: bio, timezone, working hours, focus, birthdays | Deferred |
| 3 | Announcements & Company News | Structured admin posts with read receipts (distinct from #announcements channel) | Deferred |
| 4 | Knowledge Base / Wiki | SOPs, onboarding docs, playbooks, post-mortems — agency's shared brain | Deferred |
| 5 | Onboarding Hub | New-hire checklist, required reading, first-week tasks (extends Courses model) | Deferred |
| 6 | Internal Requests / HR-lite | PTO, expenses, equipment, training budget, anonymous feedback (extends Approvals queue) | Deferred |
| 7 | Performance & Growth | Agent-facing personal dashboard: hours, health scores, goals, 1-on-1 history, reviews | Deferred |
| 8 | Recognition & Culture | Wins feed, kudos, leaderboards, agent wallet, birthdays/anniversaries | **Phase 3** (partial) |
| 9 | Team Calendar | Agency-wide: holidays, OOO, all-hands, launch dates (overlays AgentTimeBlock) | Deferred |
| 10 | Resources & Tools Library | Links, credentials, licenses, vendor contacts | Deferred |
| 11 | Polls & Decisions | Lightweight voting: snacks, logo A/B, whether to take a client | Deferred |
| 12 | Meetings Hub | All-hands recordings, notes archive, agenda drafting (integrates with huddles) | Deferred |

### 5.3 Naming

Currently placeheld as **HQ** throughout.

## 6. Phased Rollout

### Phase 1 — Foundation
Backend data split and infrastructure. No user-visible changes.
- Models, migrations, permissions
- DRF viewsets
- Realtime namespace (`/team`)
- Migration script for eligible existing groups

### Phase 2 — HQ MVP + Agent Sidebar Cleanup
First end-to-end user-visible slice.
- Strip Groups + Channels tabs from agent messages page; add "Looking for team chat? Go to HQ →" banner
- Ship HQ: channels, agent-to-agent DMs, threads, @mentions, file uploads, pinned messages
- Admin + agents can use it end-to-end

### Phase 3 — Culture Layer
- Announcements channel (admin-only write, landing spot when opening HQ)
- Wins feed — auto-posts from `ActivityLog` to `#wins` on trigger events (project complete, health score jump, campaign milestone)
- Presence + Deep Work indicator — `AgentTimeBlock` of type `deep_work` sets DND ring + soft warning on incoming DMs

### Phase 4 — Advanced 
- Huddles — persistent audio rooms per channel using existing Coturn/WebRTC
- Knowledge Exchange channel — extends `Snippet` model with `visibility=team`
- Team engagement analytics in admin Team Portal

## 7. Technical Plan

### 7.1 Backend (`server/api/`)

**New app or extend `messaging`** — the decision here affects migration blast radius. New app is cleaner.

**Data model:**

```
TeamChannel
  - id (UUID), name, slug, description
  - channel_type: general | department | topic | announcements | wins
  - department: marketing | development | all (nullable)
  - is_announcement_only: bool
  - created_by (FK Agent/Admin), created_at

TeamChannelMember
  - channel (FK), user (FK User), role: member | admin
  - joined_at, last_read_at, muted
  - unique_together: [channel, user]

TeamMessage
  - channel (FK, nullable for DMs), sender (FK User)
  - recipient (FK User, nullable for channel msgs)   ← agent-to-agent DMs
  - content, attachments (JSON), parent_message (FK self for threads)
  - pinned, edited_at, deleted_at
  - reactions (JSON)

TeamMessageReadReceipt
  - message, user, read_at
```

**Key architectural decision:** `TeamMessage` is a **separate model** from the existing `Message`, not a scope field on the same table. This gives:
- Hard permission boundary — no risk of a client ever querying a team message
- Independent indexing and retention policies
- Clean migration — existing messages stay put

**Permissions:**
- New permission class `IsAgentOrAdmin` on all `/api/team/` endpoints
- ViewSet-level check: `request.user.role in ['admin', 'agent']` — clients get 403 even if they guess the URL

### 7.2 Realtime (port 8004)

- New Socket.IO namespace: `/team` (existing `/messaging` untouched)
- New rooms: `team:channel:{uuid}` and `team:dm:{user_a}:{user_b}`
- Persistence: new MongoDB collection `team_messages` in `montrose_realtime` DB (or a new `montrose_team` DB for full isolation — decision pending)
- RabbitMQ: new routing key `team.events` alongside existing `marketing.events` / `website.events`

### 7.3 Frontend (`client/`)

**Sidebar cleanup (Phase 2):**
- In `/dashboard/agent/*/messages`, remove Groups + Channels tabs
- Sidebar becomes a flat list of client DMs, sorted by last activity
- Add banner: "Looking for team chat? Go to HQ →"

**New component tree:**

```
components/team-workspace/
  WorkspaceLayout.tsx         ← 3-column: channels | messages | member list
  ChannelSidebar.tsx          ← channel list + DM list + create channel
  ChannelHeader.tsx           ← name, topic, pin count, member count
  MessagePane.tsx             ← message list, thread support, scroll anchor
  MessageComposer.tsx         ← rich text, attachments, @mention autocomplete
  ThreadPanel.tsx             ← right-side drawer for thread replies
  MemberList.tsx              ← online agents with presence indicators
  PinnedMessagesDrawer.tsx
  AnnouncementBanner.tsx      ← top of every channel if unread announcement
```

**API module:** new `client/lib/api/team.ts` — typed functions for channels, messages, DMs, reactions, pins.

**Context:** new `team-socket-context.tsx` using `/team` namespace, **separate** from existing `socket-context.tsx` — the two systems must not cross-contaminate.

**Routes:**
- `app/dashboard/admin/team/workspace/page.tsx`
- `app/dashboard/agent/marketing/workspace/page.tsx`
- `app/dashboard/agent/developer/workspace/page.tsx`
- All three render the same `WorkspaceLayout`; only the sidebar entry point differs

### 7.4 Notifications

New `team_mention` notification type, routed through existing notification-realtime service (port 8000).

### 7.5 File Uploads

Reuse Backblaze B2 storage with a new `team-files/` prefix.

## 8. Migration Strategy

1. **Audit** existing group chats in the current `Message` model. One-off script classifies each group:
   - Agents-only → eligible to migrate into HQ as a topic channel
   - Contains any client → stays in client messaging, untouched
2. **Migration Celery task** `migrate_internal_groups_to_hq` — for eligible groups, create matching `TeamChannel`, copy members, copy messages with original timestamps
3. **Feature flag** `FEATURES.TEAM_WORKSPACE` — roll out to a test agent first
4. **Grace period** — leave old groups visible (read-only) for 2 weeks with a banner pointing to the new channel, then archive

## 9. Open Decisions

These need answers before Phase 1 starts:

1. **Name** — HQ
2. **Mongo DB isolation** — new realtime service for teams
3. **New Django app** new app (`team_workspace`) for hard boundary
4. **Deferred categories** — are categories 2–7 + 9–12 truly deferred, or is any of them in scope now? (Matters for `TeamMessage` vs. `Snippet` / `Course` / `Approval` boundaries.) everything should be in scope
5. **Anonymous feedback** (category 6) — if in scope later, changes the sender-nullable constraint on `TeamMessage`

## 10. Success Criteria

- Zero client-visible team messages (verified by permission tests + integration tests against a client JWT)
- Agent messages page no longer shows internal group chats
- All eligible pre-existing internal groups migrated without message loss
- HQ usable end-to-end by admin + at least one agent of each department (marketing, developer)
- Realtime latency on `/team` within 20% of existing `/messaging` namespace
