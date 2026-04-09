HQ — UI Plan
workspace.md → > UI spec: see workspace_ui.md

Since all 12 categories are in scope, HQ needs to be structured as a mini-app inside Montrroase with its own persistent navigation, not just a single page. Here's how I'd lay it out end-to-end.
1. Entry & Global Shell
HQ lives inside the existing Montrroase shell (topbar + main sidebar stay), but when a user enters HQ the content area transforms into a two-level layout: a narrow HQ rail on the far left of the content area, then the HQ feature panel, then the working canvas. The main Montrroase sidebar stays where it is — HQ is a destination inside the app, not a replacement for it.
Entry points:

Admin: clicking "Team Portal → Workspace" tab loads HQ in the content area
Marketing agent: sidebar item "HQ" under Management opens it
Developer agent: same, under Management
Global hotkey: Cmd+Shift+H jumps to HQ from anywhere

Shell structure when HQ is active:
┌─────────────────────────────────────────────────────────────┐
│  Montrroase Topbar (56px)                                    │
├──────┬──────────────────────────────────────────────────────┤
│      │ HQ   │ Feature Sidebar │ Working Canvas              │
│ Main │ Rail │ (contextual)    │                             │
│ Side │ 64px │ 260px           │ flex-1                      │
│ bar  │      │                 │                             │
│240px │      │                 │                             │
└──────┴──────┴─────────────────┴─────────────────────────────┘
When the main Montrroase sidebar is collapsed (64px), HQ gets more room. On screens under 1280px the HQ rail collapses into icons only.
2. The HQ Rail (64px, always visible inside HQ)
This is the top-level navigation across the 12 categories. Icon-only with tooltips on hover, grouped with thin dividers. Uses Phosphor icons throughout.
┌──────┐
│  🏠  │  Home              ← HQ landing / personalized feed
│  💬  │  Chat              ← Communication (channels + DMs)
├──────┤
│  👥  │  Directory         ← Team profiles
│  📢  │  Announcements     ← Company news
│  📚  │  Wiki              ← Knowledge base
│  🎓  │  Onboarding        ← New-hire tracks
├──────┤
│  📥  │  Requests          ← HR-lite (PTO, expenses, etc.)
│  📈  │  Growth            ← Personal performance
│  🏆  │  Recognition       ← Wins, kudos, leaderboards
├──────┤
│  📅  │  Calendar          ← Agency-wide
│  🧰  │  Resources         ← Tools + credentials library
│  🗳  │  Polls             ← Decisions + voting
│  🎥  │  Meetings          ← Hub + recordings
├──────┤
│  ⚙  │  HQ Settings       ← (admin only)
└──────┘
Active item gets the nav-item-active treatment: blue-100 background, accent blue icon, left 2px accent border. Unread badges appear as a small red dot in the top-right of each icon.
Admin vs. Agent differences: admins see an extra ⚙ HQ Settings at the bottom for managing channels, permissions, announcement templates, onboarding tracks. Everything else is identical — HQ is deliberately a shared space, not an admin tool with an agent view.
3. Home (HQ Landing)
The first thing users see when opening HQ. A personalized feed + quick glances. Three-column grid on desktop, stacks on mobile.
Left column (wide, 2/3 width):

Pinned announcement banner at the top if there's an unread company announcement — full-width card with accent border, "Mark as read" action
Your feed — a reverse-chronological stream mixing: recent @mentions, wins from the Recognition system, new wiki pages in areas you follow, poll invitations, kudos received. Each item is a card-surface with icon + actor + action + timestamp + inline quick action
Continue where you left off — unfinished onboarding steps, draft wiki pages, open polls you haven't voted on

Right column (1/3 width):

Today card — your focus block (from AgentTimeBlock), next meeting, OOO teammates today
Birthdays & anniversaries — compact list with emoji
Quick actions — buttons: New Post, Request Time Off, Ask the Team, Start a Huddle
Who's online — 8-10 avatars with presence dots; Deep Work users show the DND ring

4. Chat (Communication)
When Chat is selected in the rail, the feature sidebar (260px) shows:
┌─ Feature Sidebar (260px) ────────┐
│  🔍 Search HQ...                  │
│  ────────────────                 │
│  📢 Announcements        (3)      │  ← admin-only write
│  ⭐ Starred                        │
│  ────────────────                 │
│  CHANNELS                    +    │
│    # general                      │
│    # marketing                    │
│    # dev                          │
│    # wins                         │
│    # random                       │
│    # design-review           (2)  │
│  ────────────────                 │
│  DIRECT MESSAGES             +    │
│    ● Sarah M.                     │
│    ◐ Alex K.   (deep work)        │
│    ○ James L.                     │
│  ────────────────                 │
│  HUDDLES                          │
│    🔊 Design Review  (3 in)       │
│    🔊 Quiet Room                  │
└──────────────────────────────────┘
Working canvas (channel view):

Channel header (56px): # channel-name, topic, member count, pin count icon, huddle button, settings. Border-bottom zinc-200.
Message list — scrollable, grouped by day with "Today / Yesterday / Mar 12" dividers. Each message: avatar, name, timestamp, body. Hover reveals reaction / thread / more actions row on the right. Threads show a "View thread (4 replies)" link below the parent.
Composer at bottom: rich text with / command menu, @mention autocomplete, attachment icon, emoji, send button. On Deep Work user DMs, a soft amber bar appears above: "Sarah is in Deep Work until 3:00 PM. Send anyway?"
Right-side thread drawer (360px) slides in when a thread is opened, pushes canvas left

Presence dots:

● green — online
◐ blue — Deep Work (DND ring on avatar)
○ gray — offline
◑ amber — in a huddle

5. Directory
Feature sidebar: department filter (All / Marketing / Developer / Admin), search, "sort by: name / timezone / join date."
Canvas: card grid, 3-4 per row using card-surface with hover lift.
Each card (200px tall):

Avatar (64px), presence dot
Name + role pill
"Marketing Lead · Tirana, AL · 🕐 local time"
Short bio (2 lines, truncated)
Skills as zinc-100 pill tags
Footer row: 💬 Message · 📅 Schedule · 👤 View profile

Profile detail page (clicking a card pushes the profile in):

Hero band (full-width, 200px) with large avatar, name, role, department pill, location, local time updating live, working hours, current focus block if any
Tabs below: About (bio, skills, fun facts, birthday, anniversary), Activity (recent wins, kudos received, posts), Schedule (read-only view of their public time blocks), Kudos wall (public thanks from teammates)

6. Announcements
Distinct from the #announcements channel — these are structured posts with read tracking.
Feature sidebar: filter by category (Company / Policy / Wins / Events), "unread only" toggle.
Canvas: feed of announcement cards, each a large card-surface with:

Category pill top-left, date top-right
Title (text-section-title)
Cover image optional
Body preview (3 lines) with "Read more"
Footer: author avatar, read count ("34 of 42 have read"), reactions row
Unread items get a subtle blue-100 left border + "NEW" badge

Admin view adds: a "New announcement" button (top-right), and clicking any announcement shows a read receipts drawer listing everyone who has/hasn't seen it.
7. Wiki
Three-pane layout replaces the standard canvas:
┌──────────────┬──────────────────────┬─────────────┐
│ Page tree    │ Article              │ TOC + meta  │
│ 240px        │ flex-1               │ 220px       │
│              │                      │             │
│ > Handbook   │ # Article Title      │ On this pg  │
│   > Culture  │                      │  Intro      │
│   > Benefits │ Lorem ipsum...       │  Section 1  │
│ > SOPs       │                      │  Section 2  │
│ > Playbooks  │                      │             │
│ > Post-morts │                      │ Last edited │
│ + New page   │                      │ Contributors│
└──────────────┴──────────────────────┴─────────────┘

Page tree supports drag-to-reorder, nested folders, icons per page
Article area is Markdown with Prism highlighting (reusing your existing setup), inline comments, "Edit" button top-right
Right rail has table of contents, last edited timestamp, contributor avatars, version history link
Top of article: breadcrumb + star/follow button + share link
Search bar at top searches full content, shows matches with highlighted snippets

8. Onboarding
Feature sidebar: list of tracks (Marketing Agent Onboarding, Developer Onboarding, Admin Onboarding, custom tracks).
Canvas: Track view with a vertical stepper on the left and content on the right.

Stepper shows checklist items with completion state (pending / in progress / done), connected by a thin line
Clicking a step loads its content: could be a video (embedded), a wiki page (inline), a quiz, a "schedule intro call with X" action, or a checklist
Progress bar at top: "4 of 12 complete · Est. 2 days remaining"
Completion triggers a celebratory toast + an activity log entry + auto-post to #wins

Admin view adds a track editor — drag-drop builder for creating/editing tracks, assigning them to agents on hire.
9. Requests (HR-lite)
Feature sidebar: tabs for request types (Time Off / Expenses / Equipment / Training / Feedback), "My requests" vs "All" (admin only).
Canvas for agents: card list of their own requests with status pills (pending / approved / denied / in review). Top-right "New request" button opens a typed modal — each request type has its own form:

Time Off: date range picker, type (vacation/sick/personal), reason, balance display
Expenses: amount, category, receipt upload to B2, description
Equipment: item, justification, urgency
Training: event name, cost, dates, justification
Feedback: anonymous toggle, category, message

Canvas for admin: unified queue similar to the existing Approvals portal, with filter chips per type, bulk actions, and a detail drawer on click showing full request + approve/deny/comment.
10. Growth (Personal Performance)
Agent-only by default; admin sees an agent's growth page by clicking through from the Roster.
Canvas layout — dashboard style:

KPI strip at top (uses .kpi-strip): Hours This Week, Client Health Avg, Tasks On-Time %, Kudos Received
Grid below (2x3):

Hours logged vs. estimated — Recharts line, last 8 weeks
Client health trend — Recharts multi-line, one line per assigned client
Content approval rate (marketing) / Task completion (dev) — donut chart
Goals panel — list of active goals with progress bars, "Add goal" button
1-on-1 history — list of past syncs with shared agendas, "Next 1-on-1: Friday" card
Recognition received — recent kudos + wins



11. Recognition
Feature sidebar: Wall / Wins Feed / Kudos / Leaderboards / Wallet.
Wins Feed view:
Facebook-style timeline in the canvas. Each auto-generated win is a card:

Icon + trigger type (project complete, health jump, campaign milestone)
"Sarah M. shipped the Acme website 🚀"
Optional screenshot / metric
Reactions row (tap to add), comment thread inline

Kudos view:

"Give kudos" card at top: recipient picker, message, category (Helpful / Creative / Leadership / Above & Beyond), public toggle
Below: feed of recent public kudos as cards

Leaderboards view:

Tabs by metric, opt-in (users who opted out don't appear)
Top 10 list with rank, avatar, name, metric, delta from last period
Subtle — no trophies, no aggressive gamification; designed to encourage not shame

Wallet view:

Balance card (top), recent transactions, "Redeem" button with a catalog (bonuses, PTO days, gear)
Admin sees distribution tools: give points, create redeemable items, set exchange rates

12. Calendar
Canvas is a full-width calendar (month/week/day toggle, top-right).
Overlays multiple layers (toggleable in a legend):

Company holidays (zinc)
OOO / time off (amber)
All-hands & meetings (accent blue)
Client launches (green)
Deadlines (red)

Clicking any event opens a side drawer with details, attendees, related client/project link, and actions.
Agents can propose events; admin approves or auto-approves depending on type. The existing AgentTimeBlock data is not duplicated here — this calendar is the agency-wide layer above individual schedules.
13. Resources
Feature sidebar: category tree (Tools / Credentials / Licenses / Vendors / Accounts).
Canvas: searchable card grid. Each resource card shows:

Logo/icon
Name + category pill
Short description
Tags
Access level badge (Public / Team / Admin only)

Clicking opens a detail drawer. Credentials are never shown in cards — the drawer has a "Reveal" action that logs access to ActivityLog and blurs after 30 seconds. Admin-only resources are hidden from agents entirely.
14. Polls
Feature sidebar: Active / Closed / My polls.
Canvas: card list. Each active poll card:

Question (text-section-title)
Options as clickable rows with a thin bar showing current vote distribution (only visible after voting, or if admin allows live results)
Total votes, time remaining
"Add comment" link that opens a discussion thread below

"New poll" button opens a modal: question, options (dynamic add/remove), type (single/multi/ranked), anonymous toggle, duration, who can vote.
15. Meetings
Canvas split into two tabs: Upcoming and Archive.
Upcoming: list of scheduled meetings with title, time, attendees, linked agenda. "Join huddle" button when time arrives.
Archive: searchable list of past meetings. Click opens a detail view with:

Video recording (if from a huddle) with scrubbable player
Auto-generated transcript (if enabled)
Manual notes section (editable collaboratively)
Action items list with assignees
Linked wiki pages, linked requests, linked polls

16. Cross-Cutting UI Details
Deep Work indicator: when active, the user's avatar gets a 2px accent-light ring + a small moon icon badge bottom-right. In chat DMs to them, the composer shows an amber-bg banner: "Alex is in Deep Work until 3:00 PM." In the Directory, their card gets the DND ring. In Home "Who's online," they appear dimmed.
Notifications: every HQ event (mention, kudos, announcement, request status change, poll invite, onboarding step assigned) flows through the existing notification-realtime service. A notification drawer already exists in Montrroase — HQ just adds new team_* notification types that route there. In-HQ, each rail item gets an unread dot when relevant.
Search: Cmd+K inside HQ opens a scoped command palette that searches across channels, messages, wiki, directory, resources, polls. Results are grouped by category with icons. Outside HQ, Cmd+K remains the global Montrroase palette.
Empty states: every section gets a real empty state using .empty-state — illustration (simple Phosphor icon in a circle), headline, one-line explanation, primary action button. No blank screens.
Mobile: HQ rail collapses to a bottom bar with the 4-5 most-used sections (Home, Chat, Announcements, Requests, More). Feature sidebar becomes a drawer. Canvas is full-width.
Theming: strict adherence to your design tokens. Accent blue (#2563EB) is reserved for active nav + primary actions + mentions. All surfaces use card-surface. All spacing on the 4px scale. Framer Motion with 200ms default transitions for page enter, drawer slides, and tab switches.