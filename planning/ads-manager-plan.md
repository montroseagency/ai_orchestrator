# Ads Manager Implementation Plan

> **Version:** 1.1 | **Date:** March 18, 2026 | **Type:** Internal Strategy Document
>
> This document is the complete specification for the Ads Manager module. When building, reference the specific section called out in the prompt. Always check Section 12 (Data Architecture) for schema context regardless of which page you're building.

---

## Implementation Progress Tracker

> **Overall Progress: ~50%** (Phases 1-2 complete, Phases 3-4 remaining)

### Phase 1: Foundation — COMPLETED (March 18, 2026)

All Phase 1 deliverables have been implemented. Here is what was built:

#### Backend (Django)
| File | Status | Description |
|------|--------|-------------|
| `server/api/models/ads_manager.py` | Done | 4 models: `AdsCampaign`, `AdSet`, `Ad`, `AdsCampaignActivity` with all Meta API-mapped fields, UUID PKs, TextChoices enums, JSON fields, indexes on `(client, status)`, `(client, objective)`, `(campaign, status)`, `(ad_set, status)` |
| `server/api/serializers/ads_manager.py` | Done | 7 serializers: List + Detail for Campaign/AdSet/Ad + Activity. Annotated `ad_set_count`, `ads_count`, `audience_summary`, `created_by_name` |
| `server/api/views/marketing/ads_manager_views.py` | Done | 4 ViewSets: `AdsCampaignViewSet` (CRUD + `toggle_status`, `duplicate`, `export`), `AdSetViewSet` (CRUD), `AdViewSet` (CRUD + `generate_utm`), `AdsCampaignActivityViewSet` (read-only). All with role-based queryset filtering (admin/agent/client) |
| `server/api/migrations/0061_adscampaign_adset_adscampaignactivity_ad_and_more.py` | Done | Migration with 4 tables, 4 indexes |
| `server/api/models/__init__.py` | Modified | Added `from .ads_manager import *` |
| `server/api/serializers/__init__.py` | Modified | Added `from .ads_manager import *` |
| `server/api/views/marketing/__init__.py` | Modified | Added ViewSet imports |
| `server/api/urls.py` | Modified | 4 routes: `ads-campaigns`, `ads-ad-sets`, `ads-ads`, `ads-campaign-activity` |

#### Frontend Foundation
| File | Status | Description |
|------|--------|-------------|
| `client/lib/types/ads-manager.ts` | Done | All type unions (AdsObjective, AdsCampaignStatus, etc.), interfaces (AdsCampaign, AdSet, Ad, etc.), request/filter types, display label maps, Meta conversion events list, placement options |
| `client/lib/api/adsManager.ts` | Done | Full API wrapper: CRUD for campaigns/ad-sets/ads + `toggleCampaignStatus`, `duplicateCampaign`, `exportCampaign`, `generateAdUtm`, `getCampaignActivities` |
| `client/lib/hooks/marketing/useAdsManager.ts` | Done | React Query hooks with structured query keys, `staleTime: 30_000` on lists, cascading cache invalidation on mutations |

#### Sidebar
| File | Status | Description |
|------|--------|-------------|
| `client/components/dashboard/sidebar.tsx` | Modified | Added `Radio` icon import, `adsManager` nav group with 3 sub-items (Campaigns, Ad Sets, Ads), JSX rendering block after Services |

#### Shared Components (`client/components/marketing/ads-manager/`)
| Component | Status | Description |
|-----------|--------|-------------|
| `ObjectiveBadge.tsx` | Done | Color-coded badge for 6 ODAX objectives |
| `CampaignStatusToggle.tsx` | Done | On/off switch for active/paused with loading state |
| `DeliveryStatusBadge.tsx` | Done | Status badge supporting all entity statuses + export status |
| `BulkActionBar.tsx` | Done | Bulk actions: Activate, Pause, Archive, Duplicate, Delete |
| `AdsManagerBreadcrumb.tsx` | Done | Breadcrumb nav with "Ads Manager" root |
| `CampaignTable.tsx` | Done | DataTable with checkbox selection, 12 columns, bulk actions |
| `CampaignCreateWizard.tsx` | Done | 4-step modal: Objective, Settings, Schedule, Review |
| `AdSetTable.tsx` | Done | DataTable with optional campaign column, conversion/audience/placement columns |
| `AdSetCreateWizard.tsx` | Done | 5-step modal: Conversion, Audience, Placements, Budget & Schedule, Review |
| `AdTable.tsx` | Done | DataTable with thumbnail, format, headline, CTA, destination columns |

#### Pages (`client/app/dashboard/agent/marketing/ads-manager/`)
| Page | Status | Description |
|------|--------|-------------|
| `layout.tsx` | Done | Shared layout with `AdsManagerContext` (selectedClientId) + ClientSelector |
| `page.tsx` | Done | Redirect to `/campaigns` |
| `campaigns/page.tsx` | Done | Campaigns list with search, status filter tabs, create wizard trigger |
| `campaigns/[id]/page.tsx` | Done | Campaign detail: header, budget summary, performance strip (dashes pre-API), embedded ad sets table, export panel (JSON), activity log |
| `ad-sets/page.tsx` | Done | Ad Sets list with campaign filter badge, search, status tabs |
| `ad-sets/[id]/page.tsx` | Done | Ad Set detail: conversion/budget/audience info, embedded ads table |
| `ads/page.tsx` | Done | Ads list with ad_set/campaign filter badges, search, status tabs |
| `ads/[id]/page.tsx` | Done | Two-panel ad editor: left = format/creative/copy/destination/UTM, right = feed + story CSS preview mockups |

#### What Phase 1 Did NOT Include (deferred to later phases)
- Funnel Builder page (Phase 2)
- Audiences page with dedicated models (Phase 2 — currently inline JSON `audience_config` in AdSet)
- Datasets & Tracking page (Phase 2)
- Campaign Planner / Forecasting (Phase 3)
- Reports & Dashboards (Phase 3)
- Manual performance data re-entry (Phase 3)
- PDF export (Phase 1 uses JSON export)
- Asset Browser integration in Ad Editor creative section (placeholder drag-drop zone exists)
- DnD carousel card reordering in Ad Editor
- Agent collaboration / cross-agent task system (Phase 2)
- Meta Marketing API sync layer (Phase 4)

---

### Phase 2: Intelligence Layer — COMPLETED (March 19, 2026)

All Phase 2 deliverables have been implemented. Here is what was built:

#### Backend (Django)
| File | Status | Description |
|------|--------|-------------|
| `server/api/models/ads_manager.py` | Done | Added 6 new models: `AdsFunnel`, `AdsFunnelStage` (TOFU/MOFU/BOFU with campaign/landing page links), `AdsAudience` (saved/custom/lookalike with targeting_config JSON), `AdsDataset` (pixel code, installation status, CAPI, domain verification), `AdsConversionEvent` (standard/custom with implementation tracking), `AdsAgentTask` (cross-agent task system with 6 task types). Also added `audience` FK to `AdSet` model. 8 new indexes. |
| `server/api/serializers/ads_manager.py` | Done | 9 new serializers: `AdsFunnelStageSerializer`, `AdsFunnelListSerializer` (with stages_count), `AdsFunnelDetailSerializer` (nested stages), `AdsAudienceListSerializer` (with used_in_count), `AdsAudienceDetailSerializer`, `AdsConversionEventSerializer`, `AdsDatasetSerializer` (nested events), `AdsAgentTaskListSerializer`, `AdsAgentTaskDetailSerializer` |
| `server/api/views/marketing/ads_manager_views.py` | Done | 6 new ViewSets: `AdsFunnelViewSet` (CRUD + `create_from_template` with 5 templates), `AdsFunnelStageViewSet` (CRUD + `request_landing_page`), `AdsAudienceViewSet` (CRUD with audience_type/status filtering), `AdsDatasetViewSet` (CRUD + `generate_pixel_code`, `request_pixel_install`, `request_domain_verification`), `AdsConversionEventViewSet` (CRUD + `request_implementation`), `AdsAgentTaskViewSet` (CRUD + `complete` with auto-update of linked objects) |
| `server/api/migrations/0062_*.py` | Done | Migration for 6 new tables, audience FK on AdSet, 8 indexes |
| `server/api/urls.py` | Modified | 6 new routes: `ads-funnels`, `ads-funnel-stages`, `ads-audiences`, `ads-datasets`, `ads-conversion-events`, `ads-agent-tasks` |

#### Frontend Foundation
| File | Status | Description |
|------|--------|-------------|
| `client/lib/types/ads-manager.ts` | Done | Phase 2 types: Funnel types (FunnelStageType, FunnelTemplateType, AdsFunnel, AdsFunnelStage), Audience types (AudienceType, AudienceSourceType, AudienceStatus, AdsAudience), Dataset types (InstallationStatus, CAPIStatus, AdsDataset, AdsConversionEvent), Agent Task types (AgentTaskType, AgentTaskStatus, AdsAgentTask). All with display label records and request/filter interfaces. |
| `client/lib/api/adsManager.ts` | Done | Phase 2 API methods: Funnels CRUD + createFromTemplate + stages CRUD + requestLandingPage, Audiences CRUD, Datasets CRUD + generatePixelCode + requestPixelInstall + requestDomainVerification, Conversion Events CRUD + requestEventImplementation, Agent Tasks CRUD + completeAdsAgentTask |
| `client/lib/hooks/marketing/useAdsManager.ts` | Done | Phase 2 hooks: 6 new query key groups (funnels, funnelStages, audiences, datasets, conversionEvents, agentTasks), 30+ new hooks with cascading cache invalidation |

#### Sidebar
| File | Status | Description |
|------|--------|-------------|
| `client/components/dashboard/sidebar.tsx` | Modified | Added 3 new sub-items to adsManager nav group: Funnels, Audiences, Datasets |

#### Pages (`client/app/dashboard/agent/marketing/ads-manager/`)
| Page | Status | Description |
|------|--------|-------------|
| `funnels/page.tsx` | Done | Funnels list with grid cards, search, create modal, template selector (5 pre-built templates: E-Commerce, Lead Gen, App Install, Local Business, B2B SaaS) |
| `funnels/[id]/page.tsx` | Done | Three-panel funnel builder: left=stage list with drag handles, center=visual funnel with tapering width bands (TOFU blue/MOFU yellow/BOFU red), right=stage detail editor with campaign linking and "Request Landing Page" button |
| `audiences/page.tsx` | Done | 3-tab audience management (Saved/Custom/Lookalike), data table with type/source/status badges, create modal with type-specific forms (demographics for saved, event/retention for custom, source/percentage slider for lookalike), edit modal |
| `datasets/page.tsx` | Done | Multi-section page: dataset cards with traffic-light installation status, pixel code generator with copy-to-clipboard, installation request, domain verification request, CAPI status, conversion events registry table with add/request implementation, agent tasks list |

#### What Phase 2 Did NOT Include (deferred)
- DnD drag reordering of funnel stages (visual handle exists, reorder logic deferred)
- Asset Browser integration in Ad Editor (Phase 2 plan item, deferred to Phase 3)
- Campaign Planner page (moved to Phase 3)
- Full CAPI configuration wizard (placeholder checklist exists)

---

### Phase 3: Analytics & Planning — COMPLETE (March 19, 2026)

**Delivered:**

#### Backend (4 models, 7 serializers, 4 viewsets, 4 routes, 1 migration)

| Model | Key Fields | Constraints |
|-------|-----------|-------------|
| `AdsBenchmarkData` | client, industry (16 choices), objective, avg_cpm/cpc/ctr/cvr/frequency | `unique_together = (client, industry, objective)` |
| `AdsPlannerScenario` | Input: name, objective, industry, location, audience_size, budget, duration_days, placements (JSON), cpm_override. Output: projected_reach/impressions/frequency/cpm/results/cost_per_result, budget_curve_data (JSON) | Index on `(client, objective)` |
| `AdsReportView` | name, columns (JSON), custom_metrics (JSON), breakdown_filters (JSON), is_template | Index on `(client, is_template)` |
| `AdsManualDataEntry` | campaign, ad_set, ad, date, breakdown_type/value, 30+ nullable metric fields (impressions through purchase_value) | `unique_together = (campaign, ad_set, ad, date, breakdown_type, breakdown_value)` |

| Serializer | Purpose |
|-----------|---------|
| `AdsBenchmarkDataSerializer` | Full CRUD |
| `AdsPlannerScenarioListSerializer` | Summary for lists |
| `AdsPlannerScenarioDetailSerializer` | Full detail + created_by_name |
| `AdsReportViewListSerializer` / `DetailSerializer` | List/detail views |
| `AdsManualDataEntrySerializer` | Full CRUD + campaign/ad_set/ad names |
| `AdsManualDataEntryBulkSerializer` | Accepts `entries` list for bulk create |

| ViewSet | Custom Actions |
|---------|---------------|
| `AdsBenchmarkDataViewSet` | `seed_defaults` — seeds 16 industries × 6 objectives |
| `AdsPlannerScenarioViewSet` | `recalculate`, `compare` — benchmark-based projection with logarithmic budget curve |
| `AdsReportViewViewSet` | `create_full_funnel` (17-column template), `export_report` (CSV/XLSX/PDF) |
| `AdsManualDataEntryViewSet` | `bulk_create` (idempotent via update_or_create), `aggregated` (Sum/Avg with day/week/month grouping) |

| Route | Path |
|-------|------|
| `ads-benchmarks` | `/api/ads-benchmarks/` |
| `ads-planner-scenarios` | `/api/ads-planner-scenarios/` |
| `ads-report-views` | `/api/ads-report-views/` |
| `ads-manual-data` | `/api/ads-manual-data/` |

Migration: `0063_phase3_analytics_planning_models.py`

#### Frontend (2 pages, 11 components, ~20 API methods, ~22 hooks)

| Page | Path | Description |
|------|------|-------------|
| Planner | `/ads-manager/planner` | Scenario CRUD, benchmark editor, 2-col input/output layout, budget utilization chart, scenario comparison |
| Reports | `/ads-manager/reports` | Saved reports list, 3-tab view (Configure, Enter Data, View Report), export bar |

| Component | Purpose |
|-----------|---------|
| `PlannerInputPanel` | Form: objective, industry, location, audience_size, budget, duration, placements, CPM override |
| `PlannerOutputPanel` | 6 stat cards with K/M number formatting |
| `BudgetUtilizationChart` | Recharts dual-axis AreaChart (cumulative reach + spend) |
| `ScenarioComparisonTable` | Side-by-side table with green best-value highlights |
| `BenchmarkEditor` | Inline editable benchmark table + seed defaults |
| `ColumnCustomizer` | Two-panel metric selector grouped by funnel stage (TOFU/MOFU/BOFU/Macro) |
| `CustomMetricCreator` | Formula builder with `{metric}` syntax + clickable metric chips |
| `ManualDataEntryForm` | Campaign selector, date, breakdown, editable metric grid, bulk save |
| `ReportTable` | Sortable data table with custom metric evaluation + totals footer |
| `ReportExportBar` | Date range, campaign filter, CSV/XLSX/PDF export buttons |
| `SavedReportsList` | Report card grid with selection highlighting + "Create Full Funnel" |

Types added: `BenchmarkIndustry` (16 values), `BreakdownType`, `AVAILABLE_REPORT_METRICS` (24 metrics), 10 interfaces, 3 request types, 3 filter types.

Sidebar updated: "Planner" and "Reports" nav items added under Ads Manager group.

---

### Phase 4: API Integration — NOT STARTED (Post-Meta Registration)

**Target deliverables:**

| Feature | Description |
|---------|-------------|
| **Campaign Push** | "Publish to Meta" button replaces Export. Sends config via Marketing API |
| **Insights Pull** | Scheduled sync (1-6 hour interval) pulls performance data from Insights API |
| **Audience Sync** | Bidirectional: create audiences in Meta, sync back IDs |
| **Event Verification** | Events Manager API for real-time pixel/CAPI firing status |
| **Delivery Status** | Real-time status sync (Learning, Active, Limited, Error) |
| **Reach & Frequency** | Campaign Planner connects to Meta's prediction API |
| **Conflict Resolution** | Bidirectional sync handles edits made in both platform and Meta native |

---

### Progress Summary

| Phase | Status | Estimated Completion | Key Metric |
|-------|--------|---------------------|------------|
| **Phase 1: Foundation** | **COMPLETE** | March 18, 2026 | 3 pages (Campaigns, Ad Sets, Ads) + detail pages + editor + CRUD + sidebar |
| **Phase 2: Intelligence** | **COMPLETE** | March 19, 2026 | 6 new models, 3 additional pages (Funnels, Audiences, Datasets), cross-agent task system, sidebar expansion |
| **Phase 3: Analytics** | **COMPLETE** | March 19, 2026 | 4 models, 2 pages (Planner, Reports), 11 components, manual data entry, benchmark forecasting, CSV/XLSX/PDF export |
| **Phase 4: API Sync** | Not started (blocked on Meta registration) | — | Sync layer, no new pages |

**Overall: ~75% complete.** Phases 1–3 deliver the complete campaign hierarchy (Campaign → Ad Set → Ad), all CRUD operations, creation wizards, the funnel builder with visual designer, audience management, datasets & tracking infrastructure, cross-agent task system, benchmark-based campaign planner with scenario comparison, configurable reports with custom metrics, manual data entry with aggregation, and multi-format report export. The remaining 25% is the Meta API sync layer (Phase 4), which is blocked on Meta app registration.

---

## Table of Contents

1. [Executive Summary & Constraints](#1-executive-summary--constraints)
2. [Sidebar Architecture Overview](#2-sidebar-architecture-overview)
3. [Page 1: Campaigns Hub](#3-page-1-campaigns-hub)
4. [Page 2: Ad Sets](#4-page-2-ad-sets)
5. [Page 3: Ads (Creative Studio)](#5-page-3-ads-creative-studio)
6. [Page 4: Funnel Builder](#6-page-4-funnel-builder)
7. [Page 5: Audiences](#7-page-5-audiences)
8. [Page 6: Datasets & Tracking](#8-page-6-datasets--tracking)
9. [Page 7: Campaign Planner (Forecasting)](#9-page-7-campaign-planner-forecasting)
10. [Page 8: Reports & Dashboards](#10-page-8-reports--dashboards)
11. [Agent Collaboration Model](#11-agent-collaboration-model)
12. [Data Architecture & Schema](#12-data-architecture--schema)
13. [Phased Rollout Plan](#13-phased-rollout-plan)
14. [Constraint Handling: Pre-API Operations](#14-constraint-handling-pre-api-operations)

---

## 1. Executive Summary & Constraints

This document defines the complete Ads Manager module to be integrated into the agency platform. The module is designed to mirror the operational logic and campaign hierarchy of Meta Ads Manager while remaining fully functional in a pre-API state. The goal is to give marketing agents a professional, structured environment for planning, building, and managing paid advertising campaigns for clients, and to create a tight collaboration loop between marketing agents and developer agents.

### 1.1 The Core Constraint: No Meta API Access Yet

Because the business is not yet registered with Meta, you cannot programmatically create campaigns, push ads, or pull performance data via the Marketing API. This means every feature must be designed around a **preparation-and-export workflow**: campaigns are built, reviewed, and approved entirely within the platform, then manually executed inside the native Meta Ads Manager by the marketing agent. Once API access is granted, the system flips from export mode to direct-push mode with minimal architectural changes.

> **KEY DESIGN PRINCIPLE:** Build the full data model and UI now. Every field, every dropdown, every relationship maps 1:1 to what the Meta Marketing API expects. When API access is granted, you add a sync layer on top of the existing schema — you do not rebuild.

### 1.2 What This Module Replaces

The current campaign page and funnel page on the platform are separate, loosely defined features. This plan merges and replaces them with a unified, eight-page Ads Manager section that enforces the three-tier campaign hierarchy (Campaign → Ad Set → Ad), links campaigns directly to funnels and landing pages, and provides a custom reporting dashboard that maps to the real Meta funnel metrics.

### 1.3 Agent Collaboration Principle

The marketing agent owns the entire Ads Manager section. The developer agent is pulled into specific tasks — primarily building landing pages, installing tracking pixels/CAPI, and configuring domain verification — via a task assignment system. Both agents see the same campaign data, but their editing permissions differ based on their role.

---

## 2. Sidebar Architecture Overview

The Ads Manager lives as a top-level section in the marketing agent's sidebar, nested under the client workspace. Here is the exact sidebar structure with the eight pages:

| Icon | Sidebar Label | Purpose & Description |
|------|--------------|----------------------|
| 📋 | **Campaigns** | The top-level hub. Shows all campaigns with status filters (Draft, Active, Paused, Completed). This is the entry point and master list. |
| 🎯 | **Ad Sets** | The tactical layer. Shows all ad sets across campaigns, with filtering by parent campaign. Defines audiences, budgets, placements, and scheduling. |
| 🖼️ | **Ads** | The creative execution layer. Shows all individual ads. This is where the marketing agent uploads visuals, writes copy, selects CTAs, and configures destination URLs with UTM parameters. |
| 🔄 | **Funnel Builder** | Visual funnel designer that maps the customer journey from awareness to purchase. Stages link directly to campaigns and landing pages. Replaces the old separate funnel page. |
| 👥 | **Audiences** | Audience definition and management page. Create saved audiences, custom audiences (based on pixel events or customer lists), and lookalike audience specs. |
| 📡 | **Datasets & Tracking** | Configuration hub for tracking infrastructure: pixel code generation, CAPI setup instructions, event definitions, and domain verification status. This is where developer agent tasks are triggered. |
| 📈 | **Campaign Planner** | Forecasting and simulation tool. Input hypothetical budgets, audiences, and objectives to model projected reach, CPM, and frequency before launching. |
| 📊 | **Reports** | Custom dashboard builder with drag-and-drop metric columns. This is where the agent builds the custom funnel dashboard with Hook Rate, Hold Rate, Quality Click Rate, CPA, and MER. |

**Navigation Logic:** The sidebar items are always visible. However, clicking into a specific Campaign from the Campaigns page automatically scopes the Ad Sets and Ads pages to show only children of that campaign. A breadcrumb bar at the top of every page shows: `Client Name > Ads Manager > [Current Page] > [Selected Campaign if scoped]`.

---

## 3. Page 1: Campaigns Hub

The Campaigns Hub is the strategic command center. It replaces the current basic campaign page with a fully structured interface that enforces the ODAX objective framework and integrates Campaign Budget Optimization settings from day one.

### 3.1 Page Layout

#### Top Bar

- Page title: "Campaigns" with the client name context
- Primary action button: "+ Create Campaign" (opens the creation modal)
- Filter tabs: All | Draft | Active | Paused | Completed | Archived
- Search bar with autocomplete across campaign names
- Bulk action toolbar (appears when campaigns are selected): Pause, Activate, Archive, Duplicate, Delete

#### Campaign List Table

Each campaign row displays the following columns in a data table:

| Column | Data Type | Description |
|--------|-----------|-------------|
| Status Toggle | Switch | On/Off toggle. Switches between Active and Paused. Draft campaigns show a grayed-out toggle. |
| Campaign Name | Text + Link | Clickable. Opens the Campaign Detail view. Shows a small icon indicating the ODAX objective. |
| Objective | Badge | Color-coded pill badge: Awareness (blue), Traffic (teal), Engagement (purple), Leads (orange), App Promotion (green), Sales (red). |
| Buying Type | Badge | Auction or Reservation. Defaults to Auction for most setups. |
| Budget Strategy | Text | Shows CBO or Ad Set Budget with the daily/lifetime amount. |
| Date Range | Date | Start and end dates. Shows "Ongoing" if no end date is set. |
| Ad Sets | Count + Link | Number of child ad sets. Clickable — navigates to Ad Sets page filtered by this campaign. |
| Ads | Count | Total number of ads across all ad sets in this campaign. |
| Linked Funnel | Link | If assigned, shows the funnel name as a clickable link to the Funnel Builder page. |
| Delivery Status | Badge | Pre-API: always shows "Ready to Export" or "Draft." Post-API: shows Learning, Active, Limited, etc. |
| Results | Number | Pre-API: "—" (dash). Post-API: populated from Meta with conversion count. |
| Cost per Result | Currency | Pre-API: "—". Post-API: calculated CPA/CPL/CPC based on objective. |
| Amount Spent | Currency | Pre-API: shows the planned budget. Post-API: actual spend synced from Meta. |

### 3.2 Create Campaign Modal (Redesigned)

The new creation modal is a multi-step wizard that enforces the ODAX hierarchy:

#### Step 1: Objective Selection

A full-width selection screen showing six large cards — one for each ODAX objective. Each card displays the objective name, a one-sentence description, the funnel stage it belongs to (shown as a colored tag: TOFU/MOFU/BOFU), and an icon. The marketing agent clicks one card to proceed. This is the most critical decision and must feel deliberate.

**The six ODAX objectives:**

| Objective | Funnel Stage | Algorithmic Behavior |
|-----------|-------------|---------------------|
| Awareness | TOFU | Maximizes broad brand visibility; targets users likely to remember the ad. |
| Traffic | TOFU | Drives outbound clicks; targets habitual link-clickers to build retargeting pools. |
| Engagement | MOFU | Generates social proof and conversational commerce; targets highly active engagers. |
| Leads | MOFU | Captures actionable prospect data; targets users willing to submit forms. |
| App Promotion | BOFU | Drives software downloads and usage; targets frequent app installers. |
| Sales | BOFU | Drives direct, measurable revenue; targets users with verified purchasing intent. |

#### Step 2: Campaign Settings

- Campaign Name (required, auto-suggested based on client + objective + date)
- Special Ad Categories: if applicable, select Housing, Credit, Employment, or Politics (affects targeting options)
- Campaign Budget Optimization (CBO): toggle on/off. When on, set the budget at this level and choose Daily or Lifetime.
- Budget amount input field with currency selector
- A/B Test toggle: if enabled, reserves a percentage of budget for a structured test
- Advantage Campaign Budget toggle: when enabled, Meta distributes budget across ad sets automatically

#### Step 3: Scheduling & Funnel Link

- Start Date and optional End Date
- Funnel Assignment dropdown: select an existing funnel from the Funnel Builder, or create a new one inline
- Campaign Tags: free-form tags for internal organization (e.g., "Q2-Launch", "Retargeting", "Brand")

#### Step 4: Review & Save

Summary card showing all selections. Two action buttons: "Save as Draft" and "Save & Create Ad Set" (which immediately opens the Ad Set creation flow within this campaign).

### 3.3 Campaign Detail View

When a marketing agent clicks into a specific campaign from the list, they enter the Campaign Detail View. This is a dedicated page with the following sections:

- **Header:** Campaign name, objective badge, status, date range, and quick-action buttons (Edit, Duplicate, Pause, Archive, Export)
- **Budget Summary Card:** Total budget, daily/lifetime, CBO status, and a visual bar showing planned vs. spent (post-API)
- **Performance Summary Strip:** A horizontal row of metric cards showing Results, Cost per Result, Reach, Impressions, Amount Spent, ROAS — all showing dashes pre-API
- **Ad Sets Table:** Embedded version of the Ad Sets page, filtered to this campaign. Agents can create new ad sets directly from here.
- **Linked Funnel Preview:** A miniaturized, read-only version of the funnel visualization showing which stage this campaign maps to
- **Activity Log:** Timestamped log of all changes made to this campaign (who changed what, when)
- **Export Panel:** A collapsible section showing the campaign's complete configuration in a format ready for manual entry into Meta Ads Manager. This is the critical pre-API workflow tool.

---

## 4. Page 2: Ad Sets

The Ad Sets page is the tactical engine room. This is where the marketing agent defines who sees the ads, where they see them, how much is spent per segment, and what conversion event the algorithm should optimize for. Each ad set belongs to exactly one parent campaign and contains one or more child ads.

### 4.1 Page Layout

The layout mirrors the Campaigns page with a filterable data table, but adds a campaign scope indicator at the top. When navigated to from a specific campaign, the table is pre-filtered. The agent can remove the filter to see all ad sets across all campaigns.

#### Ad Set List Columns

| Column | Description |
|--------|-------------|
| Status Toggle | On/Off switch for this ad set. |
| Ad Set Name | Clickable. Opens the Ad Set Detail view. |
| Parent Campaign | Shows the campaign name as a breadcrumb link. |
| Conversion Event | The specific event being optimized for: Purchase, Add to Cart, Lead, Landing Page View, Link Click, etc. |
| Conversion Location | Where the conversion happens: Website, App, Messenger, Instant Form, Calls. |
| Audience Summary | Abbreviated description: "Broad — US, 25–54, All Genders" or "Custom: Cart Abandoners 30d." |
| Placements | Shows "Advantage+ (Auto)" or a comma list of manual selections. |
| Budget | If CBO is off at campaign level, this shows the ad set's own daily/lifetime budget. |
| Schedule | Date range or "Ongoing." |
| Ads Count | Number of child ads. Clickable to navigate to the Ads page, filtered. |
| Delivery Status | Pre-API: "Ready" or "Incomplete." Post-API: Learning, Active, Learning Limited. |

### 4.2 Create Ad Set Modal (Multi-Step Wizard)

#### Step 1: Conversion Setup

- Conversion Location selector: Website, App, Messenger, Instagram Direct, WhatsApp, Instant Forms, Calls
- Conversion Event dropdown: dynamically populated based on the events defined in the Datasets & Tracking page (e.g., Purchase, AddToCart, Lead, CompleteRegistration, ViewContent)
- Optimization Goal: Maximize number of conversions, or maximize value of conversions (for value-based bidding)
- Cost Control: optional CPA cap or ROAS floor input

#### Step 2: Audience Definition

This step is heavily integrated with the Audiences page. The agent can either:

- Select a Saved Audience from the Audiences page
- Build a new audience inline using the audience builder (which also saves to the Audiences page)
- Use Broad Targeting (recommended default) and rely on creative as the targeting mechanism

The audience builder includes:

- **Location:** Country, State/Region, City, Zip code, radius targeting
- **Age Range:** 18–65+ slider
- **Gender:** All, Male, Female
- **Languages:** multi-select
- **Detailed Targeting:** interests, behaviors, demographics (searchable tags)
- **Custom Audiences:** include or exclude (pulled from Audiences page)
- **Lookalike Audiences:** select source and percentage
- **Advantage Detailed Targeting toggle:** allows Meta to expand beyond selected interests

#### Step 3: Placements

- **Default:** Advantage+ Placements (automatic). The platform recommends this with a note explaining why.
- **Manual Override:** checkboxes for each placement surface organized by platform:
  - **Facebook:** Feed, Stories, Reels, In-Stream Video, Search Results, Marketplace, Right Column
  - **Instagram:** Feed, Stories, Reels, Explore, Shop
  - **Messenger:** Inbox, Stories, Sponsored Messages
  - **Audience Network:** Native, Banner, Interstitial, Rewarded Video

#### Step 4: Budget & Schedule

- If CBO is disabled at the campaign level, the agent sets the budget here: Daily or Lifetime with amount
- Start and End dates (can inherit from campaign or override)
- Ad Scheduling (dayparting): optional toggle to run ads only during specific hours/days
- Bid Strategy: Lowest Cost (default), Cost Cap, Bid Cap, or Minimum ROAS

#### Step 5: Review & Save

Summary of all settings. Two buttons: "Save as Draft" and "Save & Create Ad."

---

## 5. Page 3: Ads (Creative Studio)

This is the creative execution layer and the most visually rich page in the Ads Manager. This is where the marketing agent builds the actual advertisements that users will see. It integrates directly with the existing media library, assets, and templates system.

### 5.1 Page Layout

The Ads page shows a table of all ads across all ad sets (or filtered by a specific ad set/campaign). Each row shows:

| Column | Description |
|--------|-------------|
| Thumbnail | A small preview of the primary creative asset (image or video frame). |
| Ad Name | Clickable, opens the Ad Editor. |
| Parent Ad Set | Breadcrumb link to the parent ad set. |
| Format | Badge: Single Image, Single Video, Carousel, Dynamic Product Ad, Collection. |
| Status | Draft, Ready, Active, Paused, Rejected (post-API for policy violations). |
| Preview Links | Buttons to generate previews for specific placements: Feed, Story, Reel. |
| Destination URL | The landing page URL with UTM parameters shown in truncated form. |
| Performance | Pre-API: dashes. Post-API: Impressions, Clicks, CTR, Conversions, CPA. |

### 5.2 Ad Creation / Editor (Full-Page Editor)

Unlike campaigns and ad sets which use modals, the Ad Editor opens as a full-page experience with a **two-panel layout**: the left panel is the configuration form, and the right panel is a live preview simulator.

#### Left Panel: Configuration

**Ad Name:** Auto-generated from campaign + ad set + variant number, editable.

**Identity:** Select the Facebook Page and Instagram Account (pulled from the client's linked accounts on the platform) that the ad will be published from.

**Creative Source section:**

- **Upload New:** drag-and-drop zone for images and videos with format specs displayed (1080x1080 for feed, 1080x1920 for stories, etc.)
- **From Library:** opens the existing media library widget (the current assets system). The agent can drag assets directly from the library panel into the ad.
- **From Templates:** opens the templates library for quick starting points
- **Existing Post:** select an already-published organic post to use as the ad creative (dark post vs. published post toggle)

**Ad Format selector:**

- **Single Image:** one image with text overlays
- **Single Video:** one video (shows duration, resolution, and aspect ratio validation)
- **Carousel:** 2–10 cards, each with its own image/video, headline, description, and URL
- **Collection:** a cover image/video with a product catalog grid (requires linked catalog)

**Copy & CTA section:**

- **Primary Text:** the main ad copy. Character count with recommended limits (125 for feed, 40 for headlines). Supports emoji picker.
- **Headline:** short, bold text below the creative
- **Description:** optional secondary text
- **Call to Action dropdown:** Shop Now, Learn More, Sign Up, Download, Book Now, Contact Us, Get Offer, Get Quote, Subscribe, Apply Now, etc.
- **Display Link:** optional vanity URL text

**Destination section:**

- **Website URL:** the landing page URL
- **UTM Parameter Builder:** auto-generates UTM tags based on campaign name, ad set name, and ad name. Fields for utm_source (auto-filled as "facebook" or "instagram"), utm_medium ("paid_social"), utm_campaign, utm_content, utm_term.
- **Deep Link:** for app promotion campaigns
- **Landing Page Assignment:** dropdown to link a specific landing page from the Funnel Builder. When selected, triggers a task notification to the developer agent if the page needs to be built.

**Tracking section:**

- **URL Parameters:** any additional tracking parameters
- **Pixel/Dataset:** auto-linked from the Datasets & Tracking page, shown as read-only confirmation
- **Conversion Event:** inherited from the parent ad set, shown as read-only

#### Right Panel: Preview Simulator

A live mockup renderer that shows exactly how the ad will appear across different placements. The agent selects placement tabs to see:

- Facebook Feed (desktop and mobile)
- Instagram Feed
- Instagram Stories / Reels (vertical full-screen mockup)
- Facebook Marketplace
- Audience Network banner

The preview updates in real-time as the agent types copy or uploads new creative assets. Each preview uses the actual Facebook/Instagram UI chrome (header bars, like buttons, comment sections) rendered as static mockup frames around the agent's content.

> **INTEGRATION WITH EXISTING SYSTEMS:** The Ad Editor's creative source section reuses the same Library and Assets sidebar widget already built for the posts system. The drag-and-drop from Library to Ad works identically to how it works in the post scripts tab. This means no new asset management code — just a new drop target.

---

## 6. Page 4: Funnel Builder

The Funnel Builder replaces the old, disconnected funnel page with a visual, drag-and-drop funnel designer that is directly linked to campaigns, ad sets, and landing pages. This is the strategic visualization layer that turns abstract campaign structures into a visible customer journey.

### 6.1 Page Layout

#### Left Panel: Funnel Stages

A vertical list of stages that the agent drags to reorder. Each stage is a card with:

- **Stage Name:** editable (e.g., "Awareness", "Consideration", "Cart Intent", "Purchase")
- **Stage Type dropdown:** TOFU, MOFU, or BOFU (auto-colors the card blue, yellow, or red)
- **Linked Campaign:** dropdown to assign a campaign from the Campaigns page. Multiple campaigns can feed one stage.
- **Linked Landing Page:** dropdown to select a landing page built by the developer agent (or mark as "Needed" to trigger a build request)
- **Conversion Event:** what event signifies a user moving to the next stage (e.g., Landing Page View → Add to Cart → Purchase)
- **Audience Passthrough:** defines a Custom Audience that feeds into the next stage's targeting (e.g., "All users who triggered ViewContent in the last 14 days become the audience for the MOFU stage")

#### Center Panel: Visual Funnel

A funnel-shaped SVG/canvas visualization. Stages are rendered as horizontal bands, widest at the top (TOFU) and narrowing toward the bottom (BOFU). Lines connect stages to show the user flow. Each band shows the linked campaign name, the conversion event, and — post-API — the actual number of users at each stage.

#### Right Panel: Stage Details

When a stage is selected, this panel shows all linked campaigns, their ad sets, the landing page preview (if assigned), and a mini performance snapshot (dashes pre-API).

### 6.2 Landing Page Integration (Cross-Agent Workflow)

This is where the two agents collaborate most intensely. The landing page workflow is:

1. The marketing agent creates a funnel stage and marks it as requiring a landing page.
2. The system generates a task request that appears in the developer agent's project management dashboard with the specifications: target audience description, the offer/message, the desired conversion event, and any brand guidelines.
3. The developer agent builds the landing page (within their existing project workflow) and deploys it.
4. The developer agent marks the task as complete and links the live URL.
5. The URL automatically populates back into the Funnel Builder stage and becomes available in the Ad Editor's destination URL dropdown.
6. The marketing agent can then preview the landing page directly within the Funnel Builder.

> **CROSS-AGENT TASK FLOW:** The task assignment uses the existing communication/messaging system. A special task-type message is sent to the developer agent's inbox with all the context. The developer does not need to access the Ads Manager section — they just see a task card in their own dashboard with the brief.

### 6.3 Funnel Templates

Pre-built funnel templates that the marketing agent can select as starting points:

- **E-Commerce Standard:** Awareness → Traffic → Retarget Viewers → Cart Recovery → Purchase
- **Lead Generation:** Awareness → Content Engagement → Lead Form → Thank You Page → Sales Handoff
- **App Install:** Awareness → App Install → Onboarding Event → In-App Purchase
- **Local Business:** Local Awareness → Store Directions → Offer Claim → In-Store Visit
- **B2B SaaS:** Thought Leadership → Whitepaper Download → Demo Request → Trial Signup → Closed Deal

---

## 7. Page 5: Audiences

The Audiences page is a dedicated management interface for all audience definitions used across campaigns. This centralizes audience strategy and prevents duplication.

### 7.1 Audience Types

#### Saved Audiences

Reusable demographic + interest combinations. Created using the same builder that exists in the Ad Set creation step, but saved here as standalone, named entities. These can be applied to any ad set across any campaign with a single dropdown selection. Fields include: name, location targeting, age range, gender, language, detailed targeting interests, and exclusions.

#### Custom Audiences

Audiences based on existing customer data. Since there is no API access yet, these are defined as specifications that will be created in Meta once access is granted. The agent fills out:

- **Source Type:** Website Traffic (pixel events), Customer List (email/phone CSV), App Activity, Engagement (video viewers, page engagers, form openers)
- **Event Definition:** for website traffic, which event and the lookback window (e.g., "All users who triggered AddToCart in the last 30 days")
- **List Upload Spec:** for customer lists, a placeholder showing required fields (email, phone, first name, last name, country) with a CSV template download
- **Retention Days:** how long a user stays in the audience (1–365 days)

#### Lookalike Audiences

Audiences that instruct Meta to find new users similar to a source audience. The agent defines:

- **Source Audience:** select from existing Custom Audiences
- **Location:** country or region for the lookalike expansion
- **Audience Size Percentage:** 1% (most similar) to 10% (broader reach), with a visual slider

### 7.2 Page Layout

A tabbed interface with three tabs: **Saved | Custom | Lookalike**. Each tab shows a table of audiences with columns for Name, Type, Estimated Size (placeholder pre-API), Date Created, Used In (count of ad sets referencing this audience), and Status (Ready, Pending Upload, Needs API).

> **PRE-API NOTE:** Custom and Lookalike audiences cannot be created in Meta without API access. The platform stores these as specifications/blueprints. When the agent exports a campaign for manual creation in Meta, the audience spec is included in the export document with step-by-step instructions for recreating it in Meta's native interface.

---

## 8. Page 6: Datasets & Tracking

This page is the data infrastructure control center. It manages the tracking technology that feeds conversion data back from the client's website to the campaign optimization system. This is the primary collaboration surface between the marketing agent and the developer agent.

### 8.1 Page Sections

#### Pixel / Dataset Configuration

A card showing the Dataset status for this client:

- **Dataset Name and ID** (placeholder until API-generated)
- **Associated Website Domain**
- **Base Pixel Code:** a read-only code block showing the standard Meta Pixel base code that needs to be installed on the client's website. The marketing agent can copy this and send it to the developer agent.
- **Installation Status:** a traffic-light indicator. Red = Not Installed, Yellow = Partially Installed, Green = Verified. Pre-API, the developer agent manually changes this status after installation.
- A **"Request Installation"** button that generates a task for the developer agent with the pixel code and installation instructions (which page, in the header, before the closing head tag).

#### Conversion Events Registry

A table defining all conversion events the business wants to track. Each row:

- **Event Name:** Standard events from Meta's catalog (ViewContent, AddToCart, InitiateCheckout, Purchase, Lead, CompleteRegistration, etc.)
- **Event Type:** Standard or Custom
- **Trigger Description:** human-readable description of when this event fires (e.g., "Fires when a user lands on any product page")
- **Parameter Specifications:** key-value pairs the event should pass (e.g., content_name, content_type, value, currency)
- **Implementation Status:** Not Started, In Progress, Installed, Verified
- **Assignment:** which agent is responsible (defaults to developer agent)

#### Conversions API (CAPI) Setup

A step-by-step guided checklist for implementing server-side tracking:

1. Generate Access Token (post-API only; pre-API, shows as "pending")
2. Select Integration Method: Partner Integration (Shopify, WordPress, etc.) or Direct Integration
3. Configure Server Events: which events should be sent server-side (mirrors the Events Registry)
4. Set Deduplication Strategy: event_id matching between browser and server events
5. Test Event Delivery: pre-API, this shows a test checklist the developer confirms manually; post-API, uses the Test Events tool

#### Domain Verification

- Domain Name input
- Verification Method selector: DNS TXT Record, HTML File Upload, or Meta Tag
- Verification instructions generated for the developer agent
- Status indicator: Pending, Verified, Failed
- A "Request Verification" button that sends a task to the developer agent

#### Event Match Quality (EMQ) Dashboard

Post-API, this will show the real EMQ score from Meta. Pre-API, it shows a checklist of factors that affect EMQ:

- Customer Information Parameters being sent (email, phone, name, city, state, zip, country, IP address, user agent, etc.)
- Each parameter shows a toggle to include/exclude it, with a visual quality score bar
- The marketing agent uses this to brief the developer agent on what customer data parameters need to be passed with each event

---

## 9. Page 7: Campaign Planner (Forecasting)

The Campaign Planner is a pre-launch simulation tool that helps the marketing agent model different budget scenarios before committing real money. This page is functional even without Meta API access because it uses benchmark data and internal calculations.

### 9.1 How It Works Pre-API

Without API access, you cannot pull Meta's proprietary auction prediction data. Instead, the Campaign Planner uses industry benchmark databases that you maintain and update manually based on published reports, historical client data, and the marketing agent's experience. The platform provides editable benchmark tables for each objective and industry vertical.

### 9.2 Page Layout

#### Input Panel (Left)

- **Objective:** dropdown matching the six ODAX objectives
- **Industry Vertical:** dropdown (E-Commerce, SaaS, Real Estate, Healthcare, Finance, Retail, Education, etc.)
- **Target Location:** country/region selector
- **Audience Size Estimate:** manual input or pulled from a Saved Audience on the Audiences page
- **Budget:** input field with daily/lifetime toggle
- **Duration:** number of days
- **Placements:** Automatic or manual selection
- **Historical CPM Override:** optional field for the agent to input a known CPM from past campaigns

#### Output Panel (Right)

Real-time calculated projections displayed as metric cards:

- **Estimated Reach:** total unique users expected to see the ad
- **Estimated Impressions:** total ad views (Reach × Estimated Frequency)
- **Estimated Frequency:** average number of times each user sees the ad
- **Estimated CPM:** cost per 1,000 impressions based on benchmarks
- **Estimated Results:** based on objective (clicks for Traffic, leads for Leads, purchases for Sales) using benchmark conversion rates
- **Estimated Cost per Result:** Budget ÷ Estimated Results
- **Budget Utilization Curve:** a chart showing the point of diminishing returns

#### Scenario Comparison

The agent can save multiple scenarios (e.g., "Conservative $1K", "Aggressive $5K", "Scale $10K") and display them side-by-side in a comparison table. Each scenario becomes a card that can be attached to the campaign when it's created, serving as the performance benchmark.

#### Shareable Report

A "Generate Report" button that creates a PDF or a shareable link showing the scenario comparison. This report can be sent to the client for approval before budget commitment, using the existing messaging system.

---

## 10. Page 8: Reports & Dashboards

The Reports page is the custom analytics dashboard builder. This is where the marketing agent constructs the funnel visualization dashboard with custom columns tracking Hook Rate, Hold Rate, Quality Click Rate, CPA, and MER. Pre-API, this page serves as a template builder; post-API, it populates with live data.

### 10.1 Dashboard Builder Interface

#### Column Customizer

A panel (accessed via "Customize Columns" button) that works like Meta's column customizer:

- **Available Metrics List:** a searchable, categorized list of all available metrics grouped by funnel stage
- **Selected Metrics List:** a reorderable list of currently visible columns. The agent drags metrics from Available to Selected.
- **Custom Metric Creator:** a formula builder where the agent defines new calculated metrics:
  - Metric Name input
  - Formula builder with dropdowns for existing metrics and mathematical operators (+, −, ×, ÷)
  - Preview showing the formula in plain English (e.g., "3-Second Video Plays divided by Impressions")

#### Pre-Built Funnel Dashboard Template

A one-click template called "Full Funnel Dashboard" that automatically arranges the following columns:

| Funnel Stage | Metric | Formula | What It Diagnoses |
|-------------|--------|---------|-------------------|
| TOFU | Amount Spent | Direct value | Total investment at this level |
| TOFU | Reach | Direct value | Unique audience size |
| TOFU | Impressions | Direct value | Total ad views |
| TOFU | Hook Rate | 3s Video Plays ÷ Impressions | Is the opening visual stopping the scroll? |
| TOFU | Hold Rate | ThruPlays ÷ Impressions | Is the full message being consumed? |
| MOFU | Link Clicks | Direct value | Volume of interest expressed |
| MOFU | CTR | Link Clicks ÷ Impressions | Overall click-through efficiency |
| MOFU | Landing Page Views | Direct value | Actual arrivals at the page |
| MOFU | Quality Click Rate | LPV ÷ Link Clicks | Are clicks actually loading the page? |
| BOFU | Content Views | Direct value | Product page browsing |
| BOFU | Add to Cart | Direct value | Purchase intent signal |
| BOFU | ATC Rate | ATC ÷ Link Clicks | Product desirability and pricing fit |
| BOFU | Checkouts Initiated | Direct value | Commitment signal |
| BOFU | Purchases | Direct value | Completed transactions |
| BOFU | CPA | Spend ÷ Purchases | Cost to acquire a customer |
| BOFU | ROAS | Revenue ÷ Spend | Return on ad spend |
| Macro | MER | Spend ÷ Revenue | Overall marketing efficiency ratio |

### 10.2 Breakdown Filters

Below the main data table, a "Breakdown" dropdown allows slicing the data by: Age, Gender, Country, Region, Device Type (Mobile, Desktop, Tablet), Platform (Facebook, Instagram, Messenger, Audience Network), Placement (Feed, Stories, Reels, Search, etc.)

### 10.3 Pre-API Data Entry Mode

Before API access, the marketing agent manually enters performance data from Meta's native Ads Manager into the Reports page. The interface provides a "Manual Data Entry" mode where each campaign's row has editable cells. The agent copies numbers from Meta and pastes them into the platform at whatever frequency they choose (daily, weekly). This keeps the dashboard functional and lets the agent present client reports from the platform rather than giving clients direct Meta access.

### 10.4 Saved Report Views

- The agent can save different column configurations as named views (e.g., "Client Monthly Report", "Creative Performance", "Funnel Diagnosis")
- **Scheduled Reports:** set a report to auto-generate and be sent to the client via the messaging system on a weekly or monthly basis
- **Export:** generate PDF, CSV, or XLSX exports of the current dashboard view

---

## 11. Agent Collaboration Model

The two-agent model is the competitive differentiator of the platform. Here is the precise division of labor within the Ads Manager context:

### 11.1 Marketing Agent Responsibilities

- Full ownership of all eight Ads Manager pages
- Creates and manages campaigns, ad sets, and ads
- Defines audience strategies and funnel architectures
- Writes ad copy, selects creative assets, configures UTM parameters
- Builds and maintains the reporting dashboard
- Exports campaign configurations for manual Meta execution (pre-API)
- Manually enters performance data from Meta into the Reports page (pre-API)
- Communicates with the client about campaign strategy and results

### 11.2 Developer Agent Responsibilities

- Builds landing pages specified in the Funnel Builder
- Installs the Meta Pixel base code on the client's website
- Implements specific conversion events as defined in the Events Registry
- Sets up Conversions API (CAPI) server-side integration
- Performs domain verification (DNS or HTML method)
- Configures website speed optimization for Quality Click Rate improvement
- Deploys A/B test landing page variants
- Does NOT access or modify campaign settings, audiences, or ad creative

### 11.3 Collaboration Touchpoints

| Trigger | Initiated By | Assigned To | Deliverable |
|---------|-------------|-------------|-------------|
| New landing page needed in funnel | Marketing Agent | Developer Agent | Deployed landing page URL |
| Pixel installation required | Marketing Agent | Developer Agent | Verified pixel on website |
| New conversion event needed | Marketing Agent | Developer Agent | Event firing confirmation |
| CAPI setup requested | Marketing Agent | Developer Agent | Server-side events verified |
| Domain verification needed | Marketing Agent | Developer Agent | Domain verified in DNS |
| Landing page A/B variant | Marketing Agent | Developer Agent | Second variant URL deployed |
| Page speed optimization | Marketing Agent | Developer Agent | Improved load time report |
| Landing page copy update | Marketing Agent | Developer Agent | Updated page confirmed |

### 11.4 Task Card Structure

When the marketing agent triggers a task for the developer agent, a task card is generated with:

- **Task Title** (auto-generated, e.g., "Build Landing Page: Summer Sale BOFU")
- **Priority:** Low, Medium, High, Urgent
- **Source Context:** link back to the specific funnel stage, campaign, or dataset page that triggered the task
- **Brief / Specifications:** auto-populated from the Ads Manager context (audience description, offer details, required events, brand assets link)
- **Deadline:** set by the marketing agent
- **Status:** To Do, In Progress, In Review, Complete
- **Deliverable Field:** where the developer agent enters the final URL or confirmation
- The task also appears as a message in the shared messaging channel between the two agents

---

## 12. Data Architecture & Schema

The entire Ads Manager module is built on a relational data model that mirrors Meta's own campaign hierarchy.

### 12.1 Core Entity Relationships

```
Client → has many Campaigns
Campaign → has many Ad Sets
Ad Set → has many Ads
Campaign → belongs to one Funnel (optional)
Funnel → has many Stages
Stage → links to one or more Campaigns
Stage → links to one Landing Page (optional)
Ad Set → references one Audience (Saved, Custom, or Lookalike)
Ad → references Assets from the media library
Client → has one Dataset configuration
Dataset → has many Conversion Events
Campaign Planner Scenario → belongs to one Client, optionally linked to a Campaign
Report View → belongs to one Client, references selected metrics and filters
```

### 12.2 Campaign Schema (Key Fields)

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| client_id | UUID FK | References the client entity |
| name | String | Campaign name |
| objective | Enum | AWARENESS, TRAFFIC, ENGAGEMENT, LEADS, APP_PROMOTION, SALES |
| status | Enum | DRAFT, ACTIVE, PAUSED, COMPLETED, ARCHIVED |
| buying_type | Enum | AUCTION, RESERVATION |
| cbo_enabled | Boolean | Campaign Budget Optimization toggle |
| budget_type | Enum | DAILY, LIFETIME |
| budget_amount | Decimal | Budget in client's currency |
| currency | String | ISO currency code |
| start_date | DateTime | Campaign start |
| end_date | DateTime | Nullable for ongoing campaigns |
| special_ad_category | Enum[] | HOUSING, CREDIT, EMPLOYMENT, POLITICS or empty |
| funnel_id | UUID FK | Nullable, links to funnel |
| tags | String[] | Free-form organizational tags |
| meta_campaign_id | String | Nullable. Populated post-API with Meta's ID for sync. |
| export_status | Enum | NOT_EXPORTED, EXPORTED, SYNCED |
| created_at | DateTime | Record creation timestamp |
| updated_at | DateTime | Last modification timestamp |
| created_by | UUID FK | Marketing agent who created this |

### 12.3 Ad Set Schema (Key Fields)

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| campaign_id | UUID FK | Parent campaign |
| name | String | Ad set name |
| conversion_location | Enum | WEBSITE, APP, MESSENGER, INSTAGRAM_DIRECT, WHATSAPP, INSTANT_FORMS, CALLS |
| conversion_event | String | Event name (e.g., "Purchase", "Lead") |
| optimization_goal | Enum | CONVERSIONS, VALUE |
| cost_control_type | Enum | NONE, CPA_CAP, ROAS_FLOOR |
| cost_control_amount | Decimal | Nullable |
| audience_id | UUID FK | References Audiences table |
| audience_config | JSON | Inline audience definition if not using saved audience |
| placements_type | Enum | AUTOMATIC, MANUAL |
| placements_config | JSON | Array of selected placements when manual |
| budget_type | Enum | DAILY, LIFETIME (only when campaign CBO is off) |
| budget_amount | Decimal | Nullable when campaign CBO is on |
| start_date | DateTime | Can inherit from campaign |
| end_date | DateTime | Nullable |
| dayparting_config | JSON | Nullable, schedule of active hours |
| bid_strategy | Enum | LOWEST_COST, COST_CAP, BID_CAP, MINIMUM_ROAS |
| status | Enum | DRAFT, ACTIVE, PAUSED, ARCHIVED |
| meta_adset_id | String | Nullable, populated post-API |
| created_at | DateTime | |
| updated_at | DateTime | |

### 12.4 Ad Schema (Key Fields)

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| adset_id | UUID FK | Parent ad set |
| name | String | Ad name |
| facebook_page_id | String | Publishing identity |
| instagram_account_id | String | Nullable |
| format | Enum | SINGLE_IMAGE, SINGLE_VIDEO, CAROUSEL, COLLECTION, DYNAMIC_PRODUCT |
| creative_assets | JSON | Array of asset references (media library IDs, order, per-card config for carousel) |
| primary_text | String | Main ad copy |
| headline | String | Headline text |
| description | String | Nullable, secondary text |
| cta_type | Enum | SHOP_NOW, LEARN_MORE, SIGN_UP, DOWNLOAD, BOOK_NOW, CONTACT_US, GET_OFFER, SUBSCRIBE, APPLY_NOW, etc. |
| display_link | String | Nullable, vanity URL |
| destination_url | String | Landing page URL |
| utm_source | String | Default: "facebook" |
| utm_medium | String | Default: "paid_social" |
| utm_campaign | String | Auto-populated from campaign name |
| utm_content | String | Auto-populated from ad name |
| utm_term | String | Nullable |
| landing_page_id | UUID FK | Nullable, references funnel landing page |
| url_parameters | String | Additional tracking params |
| status | Enum | DRAFT, READY, ACTIVE, PAUSED, REJECTED |
| meta_ad_id | String | Nullable, populated post-API |
| created_at | DateTime | |
| updated_at | DateTime | |

### 12.5 Funnel Schema

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| client_id | UUID FK | |
| name | String | Funnel name |
| template_type | String | Nullable (e.g., "ecommerce_standard") |
| created_at | DateTime | |
| updated_at | DateTime | |

### 12.6 Funnel Stage Schema

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| funnel_id | UUID FK | Parent funnel |
| name | String | Stage name |
| stage_type | Enum | TOFU, MOFU, BOFU |
| order | Integer | Sort position |
| campaign_ids | UUID[] | Linked campaigns (many-to-many) |
| landing_page_url | String | Nullable |
| landing_page_status | Enum | NOT_NEEDED, NEEDED, IN_PROGRESS, DEPLOYED |
| conversion_event | String | Event that moves user to next stage |
| audience_passthrough_config | JSON | Retargeting audience definition for next stage |
| task_id | UUID FK | Nullable, references developer task if landing page requested |

### 12.7 Audience Schema

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| client_id | UUID FK | |
| name | String | Audience name |
| type | Enum | SAVED, CUSTOM, LOOKALIKE |
| saved_config | JSON | For SAVED: locations, age, gender, interests, exclusions |
| custom_source_type | Enum | For CUSTOM: WEBSITE_TRAFFIC, CUSTOMER_LIST, APP_ACTIVITY, ENGAGEMENT |
| custom_event | String | For CUSTOM/WEBSITE_TRAFFIC: event name |
| custom_lookback_days | Integer | For CUSTOM: retention window |
| lookalike_source_id | UUID FK | For LOOKALIKE: source custom audience |
| lookalike_location | String | For LOOKALIKE: target country |
| lookalike_percentage | Decimal | For LOOKALIKE: 1–10% |
| estimated_size | Integer | Nullable, placeholder pre-API |
| status | Enum | READY, PENDING_UPLOAD, NEEDS_API |
| meta_audience_id | String | Nullable, populated post-API |
| created_at | DateTime | |
| updated_at | DateTime | |

### 12.8 Dataset Schema

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| client_id | UUID FK | |
| name | String | Dataset name |
| domain | String | Client's website domain |
| pixel_id | String | Nullable, Meta Pixel ID when available |
| pixel_base_code | Text | Generated base pixel code snippet |
| installation_status | Enum | NOT_INSTALLED, PARTIAL, VERIFIED |
| capi_status | Enum | NOT_STARTED, IN_PROGRESS, ACTIVE |
| capi_integration_method | Enum | PARTNER, DIRECT |
| domain_verification_status | Enum | PENDING, VERIFIED, FAILED |
| domain_verification_method | Enum | DNS_TXT, HTML_FILE, META_TAG |
| emq_config | JSON | Parameter toggles for EMQ optimization |

### 12.9 Conversion Event Schema

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| dataset_id | UUID FK | Parent dataset |
| event_name | String | e.g., "Purchase", "AddToCart" |
| event_type | Enum | STANDARD, CUSTOM |
| trigger_description | String | Human-readable trigger explanation |
| parameters | JSON | Key-value pairs the event passes |
| implementation_status | Enum | NOT_STARTED, IN_PROGRESS, INSTALLED, VERIFIED |
| assigned_to | UUID FK | Agent responsible (usually developer) |
| task_id | UUID FK | Nullable, references developer task |

### 12.10 Campaign Planner Scenario Schema

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| client_id | UUID FK | |
| name | String | Scenario name |
| objective | Enum | ODAX objective |
| industry_vertical | String | |
| target_location | String | |
| audience_size | Integer | |
| budget | Decimal | |
| budget_type | Enum | DAILY, LIFETIME |
| duration_days | Integer | |
| placements | Enum | AUTOMATIC, MANUAL |
| cpm_override | Decimal | Nullable |
| estimated_reach | Integer | Calculated |
| estimated_impressions | Integer | Calculated |
| estimated_frequency | Decimal | Calculated |
| estimated_cpm | Decimal | From benchmarks |
| estimated_results | Integer | Calculated |
| estimated_cost_per_result | Decimal | Calculated |
| linked_campaign_id | UUID FK | Nullable |
| created_at | DateTime | |

### 12.11 Report View Schema

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| client_id | UUID FK | |
| name | String | View name (e.g., "Full Funnel Dashboard") |
| columns | JSON | Ordered array of metric definitions |
| custom_metrics | JSON | Array of formula-based custom metrics |
| breakdowns | JSON | Active breakdown filters |
| date_range | JSON | Default date range for this view |
| is_template | Boolean | True for pre-built templates |
| schedule | JSON | Nullable, auto-report schedule config |

### 12.12 Manual Performance Data Schema

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| campaign_id | UUID FK | |
| adset_id | UUID FK | Nullable (can be campaign-level) |
| ad_id | UUID FK | Nullable (can be adset-level) |
| date | Date | The date this data represents |
| metrics | JSON | Key-value pairs of metric name to value |
| entered_by | UUID FK | Agent who entered the data |
| entered_at | DateTime | When the data was entered |
| source | Enum | MANUAL, API_SYNC |

---

## 13. Phased Rollout Plan

The implementation should be executed in four phases, each building on the previous one:

### Phase 1: Foundation (Weeks 1–4)

Build the core three-tier hierarchy: Campaigns, Ad Sets, and Ads pages with full creation workflows, detail views, and the data table interfaces. Replace the existing basic campaign page. Implement the export functionality so agents can generate configuration documents for manual Meta execution.

**Key deliverables:**
- Campaign schema and CRUD operations
- Ad Set schema and CRUD operations
- Ad schema and CRUD operations
- Three-tier navigation with breadcrumbs and scoping
- Campaign creation wizard (4-step ODAX flow)
- Ad Set creation wizard (5-step flow)
- Ad Editor (full-page two-panel layout)
- Export for Meta functionality

### Phase 2: Intelligence Layer (Weeks 5–8)

Build the Funnel Builder with visual stage mapping and the Audiences page with the three audience type builders. Implement the cross-agent task system for landing page requests and pixel installation. Build the Datasets & Tracking page with event registry and developer task triggers.

**Key deliverables:**
- Funnel schema and visual builder
- Funnel stage linking to campaigns and landing pages
- Cross-agent task generation system
- Audience schemas (Saved, Custom, Lookalike)
- Audience builder component (reused in Ad Set wizard)
- Dataset configuration page
- Conversion Events Registry
- Developer task cards for pixel/CAPI/domain work

### Phase 3: Analytics & Planning (Weeks 9–12)

Build the Campaign Planner with benchmark-based forecasting and scenario comparison. Build the Reports page with the custom column builder, custom metric formula creator, and the pre-built funnel dashboard template. Implement the manual data entry mode for pre-API performance tracking.

**Key deliverables:**
- Benchmark data tables (editable)
- Campaign Planner input/output panels
- Scenario save and comparison
- Reports column customizer
- Custom metric formula creator
- Full Funnel Dashboard template
- Manual Data Entry mode
- Breakdown filters
- Report export (PDF, CSV, XLSX)
- Scheduled report delivery

### Phase 4: API Integration (Post-Registration)

Once the business is registered with Meta: implement the Marketing API sync layer to push campaigns directly from the platform to Meta, pull real-time performance data into the Reports page, automate audience creation, and enable the real Campaign Planner predictions using Meta's auction data. Replace manual data entry with automated data ingestion. Update delivery statuses with real-time Meta statuses.

**Key deliverables:**
- Meta Marketing API integration layer
- Campaign push (create/update/pause in Meta)
- Insights API data pull (scheduled sync)
- Audience creation API sync
- Real delivery status updates
- Events Manager API connection for verification
- Reach & Frequency Prediction API for Campaign Planner
- Bidirectional sync conflict resolution

| Phase | Timeline | Key Deliverables | Pre-API Workaround |
|-------|----------|-----------------|-------------------|
| 1 | Weeks 1–4 | Campaigns, Ad Sets, Ads pages | Export configs for manual Meta entry |
| 2 | Weeks 5–8 | Funnels, Audiences, Datasets | Spec docs for audiences; manual pixel install tasks |
| 3 | Weeks 9–12 | Planner, Reports dashboard | Benchmark data; manual performance data entry |
| 4 | Post-registration | Full API sync layer | No workarounds needed — full automation |

---

## 14. Constraint Handling: Pre-API Operations

This section details exactly how each feature operates without Meta API access and what changes when access is granted.

### 14.1 The Export Workflow (Pre-API)

The most critical pre-API feature is the Campaign Export. When a marketing agent finishes building a campaign with all its ad sets and ads, they click "Export for Meta." The system generates a structured document (PDF or formatted text) that contains:

1. **Campaign Settings:** objective, budget, CBO status, schedule, special ad categories
2. **Ad Set 1 through N:** each with conversion event, audience definition (with step-by-step recreation instructions for Meta), placement selections, budget, schedule, and bid strategy
3. **Ad 1 through N:** each with the creative asset file names (with a zip file of all assets attached), primary text, headline, description, CTA, destination URL with UTM parameters, and tracking pixel instructions
4. **Audience Blueprints:** detailed instructions for creating each Custom and Lookalike audience in Meta's native interface
5. **Tracking Checklist:** confirmation that pixel is installed, events are firing, domain is verified

The agent then opens Meta Ads Manager in a separate browser tab and follows the export document step-by-step to manually create the campaign. Once created in Meta, the agent returns to the platform and updates the campaign's `meta_campaign_id` field and changes the `export_status` to EXPORTED.

### 14.2 Performance Data Re-Entry (Pre-API)

After a campaign is live in Meta, the marketing agent periodically (daily or weekly) copies the key performance metrics from Meta's native Ads Manager into the platform's Reports page. The Manual Data Entry mode provides a streamlined interface:

- Select the campaign and date range
- A form appears with all the columns from the active dashboard view as input fields
- The agent copies numbers from Meta and pastes them into the form
- The data is saved with a timestamp and the agent's ID for audit purposes
- The Reports dashboard immediately reflects the new data

### 14.3 Transition to API Mode

When Meta API access is granted, the following changes occur:

- **Campaign Push:** A "Publish to Meta" button replaces the "Export" button. Clicking it sends the campaign configuration directly to Meta via the Marketing API and stores the returned `meta_campaign_id`.
- **Real-Time Data Pull:** A scheduled sync job (every 1–6 hours) pulls performance data from the Insights API and populates the Reports page automatically. Manual data entry mode becomes optional (for override/correction).
- **Audience Sync:** Custom and Lookalike audiences are created directly in Meta and synced bidirectionally.
- **Event Verification:** The Datasets & Tracking page connects to the Events Manager API to show real-time event firing status and EMQ scores.
- **Delivery Status:** Campaign, Ad Set, and Ad statuses sync from Meta in near-real-time, showing actual delivery states (Learning, Active, Limited, Error).
- **Campaign Planner:** Connects to Meta's Reach & Frequency Prediction API for actual auction-based forecasting.

> **ZERO REBUILD PRINCIPLE:** Because every field in the database already maps to Meta's API parameters, the API integration layer is purely additive. You add sync functions that read existing data and push/pull via the API. No page layouts, no forms, no workflows need to change. The UI stays the same — only the data source and action buttons change.
