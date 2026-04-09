Phase A — Foundation (must ship first, in order)                                                                                                    
                                                                                                                                                      
  A1. Backend foundation
  build: HQ Phase 1 — backend foundation. New Django app `team_workspace`. Models: TeamChannel, TeamChannelMember, TeamMessage,
  TeamMessageReadReceipt. Permission class IsAgentOrAdmin on all /api/team/ routes. DRF viewsets + URLs. New Socket.IO namespace /team on port 8004   
  (rooms: team:channel:{uuid}, team:dm:{a}:{b}). New Mongo DB montrose_team for realtime persistence. RabbitMQ routing key team.events. Feature flag  
  FEATURES.TEAM_WORKSPACE. Spec: workspace.md §6 Phase 1 + §7.1 + §7.2. No frontend in scope.
  Produces: data layer, permission boundary, realtime namespace. Nothing visible in the UI yet.
  Depends on: nothing.

  A2. Frontend shell + routing
  build: HQ frontend shell. Routes: /dashboard/admin/team/workspace, /dashboard/agent/marketing/management/workspace,
  /dashboard/agent/developer/management/workspace. Components: WorkspaceLayout (three-zone: rail | feature sidebar | canvas), HQRail (64px, 13 items +
   admin Settings), topbar integration preserving existing Montrroase sidebar. Empty states for all 12 categories using .empty-state. Global hotkey   
  Cmd+Shift+H. New team-socket-context.tsx wired to /team namespace (separate from existing socket-context.tsx). New client/lib/api/team.ts module    
  scaffold. Spec: workspace_ui.md §1-2, §16 (Theming + Deep Work placeholder). No section content yet.
  Produces: navigable shell — every rail item routes somewhere, every section shows an empty state.
  Depends on: A1 (needs /team namespace alive).

  ---
  Phase B — Chat Vertical Slice (proves the full stack)

  B1. Chat MVP — channels + DMs + threads
  build: HQ Chat MVP. Channels CRUD (agent-created topic channels + admin-seeded #general, #marketing, #dev, #announcements, #wins, #random).
  Agent-to-agent DMs. Threads (parent_message FK). @mention autocomplete + team_mention notifications via notification-realtime service (port 8000).  
  Pinned messages per channel. File uploads to B2 with team-files/ prefix. Message reactions (JSON column). Read receipts. Presence dots
  (online/offline/huddle — deep-work variant deferred). Spec: workspace.md §6 Phase 2 + workspace_ui.md §4.
  Produces: working internal chat end-to-end.
  Depends on: A1, A2.

  B2. Agent sidebar cleanup + migration script
  build: HQ Phase 2 tail — strip Groups and Channels tabs from /dashboard/agent/*/messages, flatten sidebar to client DMs sorted by last activity, add
   banner "Looking for team chat? Go to HQ →". Celery task migrate_internal_groups_to_hq: audit existing Message groups, classify agents-only vs      
  client-containing, copy eligible groups into TeamChannel with original timestamps, leave originals read-only with redirect banner. Spec:
  workspace.md §8 Migration Strategy.
  Produces: clean separation at the UI layer + historical team chats preserved.
  Depends on: B1.

  ---
  Phase C — Per-Category Builds (each is its own pipeline run)

  Each slice below is a separate build: command. The order is roughly "least dependent first" so each new feature can consume the previous ones'      
  notifications and presence. Skip any you decide to defer.

  C1. Directory (category 2)
  build: HQ Directory. Extend Agent model with public team profile fields: bio, pronouns, timezone, working hours, current focus, fun facts, birthday,
   work anniversary, skills. DRF endpoint /api/team/directory/. Frontend: department filter sidebar, card grid (workspace_ui.md §5), profile detail   
  page with About/Activity/Schedule/Kudos tabs. Live local-time updating. Respect existing Agent access controls — this is a public-to-team layer, not
   a new identity.

  C2. Announcements (category 3)
  build: HQ Announcements. New model TeamAnnouncement with category, title, cover image, body, author, read_receipts (M2M through
  TeamAnnouncementRead). Admin-only write. Pinned-unread banner component on HQ Home + per-section. Read-receipts drawer for admin. Frontend: feed of 
  cards, "unread only" filter, category filter pills. Spec: workspace_ui.md §6. Separate from the #announcements chat channel.

  C3. Wiki (category 4)
  build: HQ Wiki. New models: WikiPage (tree via parent FK, slug, body markdown, followers M2M), WikiPageVersion (history), WikiComment (inline,      
  anchor). Full-text search endpoint. Frontend: three-pane layout (tree | article | TOC) per workspace_ui.md §7. Markdown editor with Prism
  highlighting (reuse existing setup), contributor avatars, version history link. Drag-to-reorder tree.

  C4. Onboarding (category 5)
  build: HQ Onboarding. New models: OnboardingTrack, OnboardingStep (types: video, wiki_link, quiz, action, checklist), OnboardingAssignment (agent,  
  track, progress). Auto-enroll new Agents on hire signal. Completion triggers ActivityLog entry + auto-post to #wins channel. Frontend: track list   
  sidebar + vertical stepper canvas (workspace_ui.md §8). Admin drag-drop track editor.

  C5. Requests / HR-lite (category 6)
  build: HQ Requests. New models: TimeOffRequest, ExpenseRequest, EquipmentRequest, TrainingRequest, FeedbackSubmission (with anonymous flag —        
  sender_nullable=True). All flow through existing Approvals queue with a new `team_request` category + type discriminator. Frontend: agent view      
  (cards + typed modals per request type, workspace_ui.md §9). Admin view reuses Approvals portal patterns with filter chips + detail drawer. Receipt
  uploads to B2.

  C6. Growth (category 7)
  build: HQ Growth. Read-only aggregations from ProjectTask (hours logged vs estimated), client health scores, content approval rate (marketing) /    
  task completion (dev), Kudos received (depends on C7), Goals (new model Goal with progress_pct), OneOnOne (new model with shared agenda). Frontend: 
  KPI strip + 2x3 Recharts grid per workspace_ui.md §10. Agent-only canvas; admin reaches an agent's Growth page via Roster click-through.
  Depends on: ideally C7 for the Kudos panel — or stub it.

  C7. Recognition + Wins feed + Wallet (category 8 + Phase 3 culture)
  build: HQ Recognition. New models: Kudos (sender, recipient, category, message, public flag), Win (auto-generated from ActivityLog triggers:        
  project_complete, health_score_jump, campaign_milestone), LeaderboardOptIn, AgentWallet (balance), WalletTransaction, RedeemableItem,
  Birthday/Anniversary surface from Agent. Wins feed auto-poster listening on ActivityLog signals, cross-posts to #wins channel. Frontend: Wall / Wins
   Feed / Kudos / Leaderboards / Wallet sub-views per workspace_ui.md §11. Subtle leaderboards — opt-in only, no aggressive gamification.

  C8. Calendar (category 9)
  build: HQ Calendar. New model AgencyEvent (type: holiday, ooo, all_hands, client_launch, deadline; layer; attendees M2M; linked_project FK nullable;
   linked_client FK nullable). Overlays existing AgentTimeBlock without duplicating data — OOO entries surface from approved TimeOffRequest (C5).     
  Frontend: month/week/day toggle, toggleable layer legend, side drawer per workspace_ui.md §12. Agents propose; admin approves.
  Depends on: C5 for OOO overlay.

  C9. Resources (category 10)
  build: HQ Resources. New models: Resource (type: tool, license, vendor, account), Credential (encrypted at rest, audit-logged reveal), access_level 
  (public/team/admin). Category tree sidebar. Credential reveal action logs to ActivityLog and auto-blurs after 30s. Admin-only resources hidden      
  entirely from agents (not just disabled). Spec: workspace_ui.md §13.

  C10. Polls (category 11)
  build: HQ Polls. New models: Poll (question, type: single/multi/ranked, anonymous flag, duration, eligible_voters M2M), PollOption, PollVote,       
  PollComment. Live results setting. Frontend: active/closed/my polls sidebar, card canvas, new-poll modal per workspace_ui.md §14. Poll invitations  
  flow into Home feed.

  C11. Meetings Hub (category 12)
  build: HQ Meetings. New models: Meeting (title, time, attendees, linked_huddle FK nullable, linked_wiki FK nullable), MeetingRecording (B2 URL,     
  transcript), MeetingNote (collaborative markdown), ActionItem (assignee, due_date, status). Upcoming / Archive tabs. Spec: workspace_ui.md §15.     
  Huddle integration stub — real huddle connection lands in D3.

  ---
  Phase D — Cross-Cutting & Polish

  D1. Presence + Deep Work indicator
  build: HQ Presence + Deep Work. Extend realtime presence to emit on AgentTimeBlock type=deep_work start/end. Frontend: avatar DND ring (2px
  accent-light + moon badge), amber banner on DMs to deep-work users ("Alex is in Deep Work until 3:00 PM. Send anyway?"), Directory card ring, Home  
  Who's-online dim. Spec: workspace.md §6 Phase 3 + workspace_ui.md §16.
  Depends on: A1 (presence), C1 (Directory), B1 (Chat).

  D2. HQ Home landing page
  build: HQ Home. Personalized feed aggregating recent @mentions (B1), wins (C7), new followed wiki pages (C3), poll invitations (C10), kudos received
   (C7), onboarding continue (C4). Three-column layout per workspace_ui.md §3: feed + continue-where-you-left-off (left 2/3), Today card + birthdays +
   quick actions + who's online (right 1/3). Pinned announcement banner (C2) at top.
  Depends on: B1, C1, C2, C3, C4, C7, C10. Ship last for this reason.

  D3. Cmd+K HQ command palette
  build: HQ command palette. Cmd+K inside HQ opens scoped palette searching across channels (B1), messages, wiki (C3), directory (C1), resources (C9),
   polls (C10). Results grouped by category with Phosphor icons. Outside HQ, Cmd+K remains global Montrroase palette. Spec: workspace_ui.md §16.      
  Depends on: the sections it searches across.

  D4. Mobile responsive sweep
  build: HQ mobile layouts. Rail collapses to bottom bar (Home, Chat, Announcements, Requests, More). Feature sidebar becomes a drawer. Canvas        
  full-width. Sweep across all 12 sections verifying layouts below 768px. Spec: workspace_ui.md §16.
  Depends on: all C slices shipped.

  D5. HQ Settings (admin-only rail item)
  build: HQ Settings. Admin-only rail item (gear icon, bottom of rail). Manages: channel archival, announcement templates, onboarding track
  assignment, leaderboard metrics config, wallet redeemable catalog, request category config, poll permissions, resource access levels. Spec:
  workspace_ui.md §2 (admin differences).
  Depends on: all C slices.

  ---
  Phase E — Advanced (Phase 4, optional)

  E1. Huddles — WebRTC audio rooms
  build: HQ Huddles. Persistent audio rooms per channel using existing Coturn + WebRTC setup. New models: Huddle, HuddleParticipant. Socket.IO events 
  on /team namespace. Frontend: huddle launcher in channel header, join/leave controls, participant list with mute/deafen, ambient amber presence dot 
  for users in huddle. Spec: workspace.md §6 Phase 4.
  Depends on: B1.

  E2. Knowledge Exchange channel
  build: HQ Knowledge Exchange. Extend existing Snippet model with visibility=team flag. New channel_type=knowledge_exchange TeamChannel that surfaces
   tagged team-visibility snippets as pinned library. Bi-directional link between Wiki pages and Snippets. Spec: workspace.md §6 Phase 4.
  Depends on: B1, C3.

  E3. Team engagement analytics
  build: HQ Analytics. New admin-only dashboard in Team Portal: channel activity heatmap, DAU/WAU/MAU, announcement read rates, onboarding completion 
  funnel, kudos distribution, poll participation, wiki edit velocity. Recharts visualizations. Spec: workspace.md §6 Phase 4.
  Depends on: all C slices for real data.

  ---
  Summary — 23 pipeline runs total

  ┌──────────────────────────┬───────┬────────┐
  │          Phase           │ Count │  Runs  │
  ├──────────────────────────┼───────┼────────┤
  │ A — Foundation           │ 2     │ A1, A2 │
  ├──────────────────────────┼───────┼────────┤
  │ B — Chat vertical slice  │ 2     │ B1, B2 │
  ├──────────────────────────┼───────┼────────┤
  │ C — Per-category         │ 11    │ C1–C11 │
  ├──────────────────────────┼───────┼────────┤
  │ D — Cross-cutting polish │ 5     │ D1–D5  │
  ├──────────────────────────┼───────┼────────┤
  │ E — Advanced (optional)  │ 3     │ E1–E3  │
  └──────────────────────────┴───────┴────────┘

  Recommended cadence: ship A → B → your visual review gate → then iterate through C/D at whatever pace you want. Don't batch. Each slice is
  deliberately sized so the pipeline's 8-iteration retry cap never trips.
