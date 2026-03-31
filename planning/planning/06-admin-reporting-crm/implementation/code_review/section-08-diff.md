diff --git a/client/components/management/tasks/TaskFilterBar.tsx b/client/components/management/tasks/TaskFilterBar.tsx
index f0356d5e5..e26b8290d 100644
--- a/client/components/management/tasks/TaskFilterBar.tsx
+++ b/client/components/management/tasks/TaskFilterBar.tsx
@@ -8,7 +8,11 @@ import { useDebounce } from '@/lib/hooks/useDebounce';
 import { ClientBadge } from './ClientBadge';
 import type { GlobalTaskStatus, TaskPriority } from '@/lib/types/scheduling';
 
-export function TaskFilterBar() {
+interface TaskFilterBarProps {
+  showClientFilter?: boolean
+}
+
+export function TaskFilterBar({ showClientFilter = true }: TaskFilterBarProps) {
   const {
     selectedClientIds,
     selectedCategoryIds,
@@ -65,32 +69,34 @@ export function TaskFilterBar() {
   return (
     <div className="flex flex-wrap gap-2 items-center p-3 bg-surface-subtle rounded-lg border border-border-subtle">
       {/* Client multi-select */}
-      <div className="flex flex-wrap gap-1 items-center">
-        <select
-          id="filter-client"
-          aria-label="Filter by client"
-          onChange={handleClientSelect}
-          disabled={clientsLoading}
-          defaultValue=""
-          className="text-sm bg-surface border border-border rounded-lg px-2 py-1.5 text-secondary focus:outline-none focus:ring-2 focus:ring-accent disabled:opacity-60"
-        >
-          <option value="">{clientsLoading ? 'Loading…' : 'Filter by client'}</option>
-          {clients.map((c) => (
-            <option key={c.id} value={c.id}>
-              {c.name}
-            </option>
+      {showClientFilter && (
+        <div className="flex flex-wrap gap-1 items-center">
+          <select
+            id="filter-client"
+            aria-label="Filter by client"
+            onChange={handleClientSelect}
+            disabled={clientsLoading}
+            defaultValue=""
+            className="text-sm bg-surface border border-border rounded-lg px-2 py-1.5 text-secondary focus:outline-none focus:ring-2 focus:ring-accent disabled:opacity-60"
+          >
+            <option value="">{clientsLoading ? 'Loading…' : 'Filter by client'}</option>
+            {clients.map((c) => (
+              <option key={c.id} value={c.id}>
+                {c.name}
+              </option>
+            ))}
+          </select>
+          {/* Client chips */}
+          {selectedClientIds.map((id) => (
+            <ClientBadge
+              key={id}
+              clientId={id}
+              clientName={clientNameMap[id] ?? id}
+              onRemove={() => removeClient(id)}
+            />
           ))}
-        </select>
-        {/* Client chips */}
-        {selectedClientIds.map((id) => (
-          <ClientBadge
-            key={id}
-            clientId={id}
-            clientName={clientNameMap[id] ?? id}
-            onRemove={() => removeClient(id)}
-          />
-        ))}
-      </div>
+        </div>
+      )}
 
       {/* Category single-select */}
       <select
diff --git a/client/components/portal/crm/ClientDetailHub.tsx b/client/components/portal/crm/ClientDetailHub.tsx
new file mode 100644
index 000000000..6129fdf9f
--- /dev/null
+++ b/client/components/portal/crm/ClientDetailHub.tsx
@@ -0,0 +1,113 @@
+'use client'
+
+import React, { useState } from 'react'
+import { useRouter } from 'next/navigation'
+import { useQuery } from '@tanstack/react-query'
+import { ArrowLeft } from 'lucide-react'
+import { Badge } from '@/components/ui/badge'
+import api from '@/lib/api'
+import { OverviewTab } from './tabs/OverviewTab'
+import { TasksTab } from './tabs/TasksTab'
+import { MarketingPlanTab } from './tabs/MarketingPlanTab'
+import { TimeCapacityTab } from './tabs/TimeCapacityTab'
+
+type TabId = 'overview' | 'tasks' | 'marketing-plan' | 'time-capacity'
+
+interface ClientInfo {
+  id: string
+  name: string
+  company: string
+  status: string
+}
+
+interface ClientDetailHubProps {
+  clientId: string
+  agentType: 'marketing' | 'developer'
+  client?: { name: string; company: string; status: string }
+}
+
+const TABS: { id: TabId; label: string }[] = [
+  { id: 'overview', label: 'Overview' },
+  { id: 'tasks', label: 'Tasks' },
+  { id: 'marketing-plan', label: 'Marketing Plan' },
+  { id: 'time-capacity', label: 'Time & Capacity' },
+]
+
+export function ClientDetailHub({ clientId, agentType, client: clientProp }: ClientDetailHubProps) {
+  const router = useRouter()
+  const [activeTab, setActiveTab] = useState<TabId>('overview')
+
+  const { data: fetchedClient } = useQuery<ClientInfo>({
+    queryKey: ['client', clientId],
+    queryFn: () => api.getClient(clientId),
+    enabled: !!clientId && !clientProp,
+    staleTime: 300_000,
+  })
+
+  const client = clientProp
+    ? { id: clientId, ...clientProp }
+    : fetchedClient
+
+  return (
+    <div className="flex flex-col gap-0">
+      {/* Header */}
+      <div className="flex items-center gap-3 px-6 py-4 border-b border-border">
+        <button
+          type="button"
+          onClick={() => router.back()}
+          className="flex items-center gap-1 text-secondary hover:text-primary transition-colors"
+          aria-label="Go back"
+        >
+          <ArrowLeft size={18} />
+        </button>
+        <div className="flex-1 flex items-center gap-3">
+          <h1 className="text-xl font-semibold text-primary">
+            {client?.name ?? '—'}
+          </h1>
+          {client?.status && (
+            <Badge variant="default" className="capitalize text-xs">
+              {client.status}
+            </Badge>
+          )}
+          {client?.company && (
+            <span className="text-secondary text-sm">{client.company}</span>
+          )}
+        </div>
+      </div>
+
+      {/* Tab bar */}
+      <div className="flex gap-0 border-b border-border px-6">
+        {TABS.map((tab) => (
+          <button
+            key={tab.id}
+            type="button"
+            onClick={() => setActiveTab(tab.id)}
+            className={`px-4 py-3 text-sm font-medium transition-colors -mb-px ${
+              activeTab === tab.id
+                ? 'border-b-2 border-accent text-primary'
+                : 'text-secondary hover:text-primary border-b-2 border-transparent'
+            }`}
+          >
+            {tab.label}
+          </button>
+        ))}
+      </div>
+
+      {/* Tab content */}
+      <div className="p-6">
+        {activeTab === 'overview' && (
+          <OverviewTab clientId={clientId} client={client} />
+        )}
+        {activeTab === 'tasks' && (
+          <TasksTab clientId={clientId} agentType={agentType} />
+        )}
+        {activeTab === 'marketing-plan' && (
+          <MarketingPlanTab clientId={clientId} />
+        )}
+        {activeTab === 'time-capacity' && (
+          <TimeCapacityTab clientId={clientId} />
+        )}
+      </div>
+    </div>
+  )
+}
diff --git a/client/components/portal/crm/__tests__/ClientDetailHub.test.tsx b/client/components/portal/crm/__tests__/ClientDetailHub.test.tsx
new file mode 100644
index 000000000..72c20c805
--- /dev/null
+++ b/client/components/portal/crm/__tests__/ClientDetailHub.test.tsx
@@ -0,0 +1,96 @@
+import { render, screen, fireEvent } from '@testing-library/react'
+import { describe, it, expect, vi, beforeEach } from 'vitest'
+import React from 'react'
+import { renderWithQuery } from '@/test-utils/scheduling'
+
+// ── Mocks ───────────────────────────────────────────────────────────────────
+
+vi.mock('next/navigation', () => ({
+  useRouter: () => ({ back: vi.fn() }),
+}))
+
+vi.mock('@/lib/api', () => ({
+  default: { request: vi.fn().mockResolvedValue({}), getClient: vi.fn().mockResolvedValue({ id: 'client-1', name: 'Acme Corp', company: 'Acme Inc', status: 'active' }) },
+}))
+
+vi.mock('@/components/portal/crm/tabs/OverviewTab', () => ({
+  OverviewTab: () => <div data-testid="overview-tab">OverviewTab</div>,
+}))
+
+vi.mock('@/components/portal/crm/tabs/TasksTab', () => ({
+  TasksTab: ({ agentType }: { agentType: string }) => (
+    <div data-testid="tasks-tab" data-agent-type={agentType}>TasksTab</div>
+  ),
+}))
+
+vi.mock('@/components/portal/crm/tabs/MarketingPlanTab', () => ({
+  MarketingPlanTab: () => <div data-testid="marketing-plan-tab">MarketingPlanTab</div>,
+}))
+
+vi.mock('@/components/portal/crm/tabs/TimeCapacityTab', () => ({
+  TimeCapacityTab: () => <div data-testid="time-capacity-tab">TimeCapacityTab</div>,
+}))
+
+// ── Tests ───────────────────────────────────────────────────────────────────
+
+async function getHub() {
+  const { ClientDetailHub } = await import('@/components/portal/crm/ClientDetailHub')
+  return ClientDetailHub
+}
+
+describe('ClientDetailHub', () => {
+  const clientProp = { name: 'Acme Corp', company: 'Acme Inc', status: 'active' }
+
+  it('renders 4 tabs labelled "Overview", "Tasks", "Marketing Plan", "Time & Capacity"', async () => {
+    const ClientDetailHub = await getHub()
+    renderWithQuery(<ClientDetailHub clientId="client-1" agentType="marketing" client={clientProp} />)
+    expect(screen.getByRole('button', { name: 'Overview' })).toBeInTheDocument()
+    expect(screen.getByRole('button', { name: 'Tasks' })).toBeInTheDocument()
+    expect(screen.getByRole('button', { name: 'Marketing Plan' })).toBeInTheDocument()
+    expect(screen.getByRole('button', { name: 'Time & Capacity' })).toBeInTheDocument()
+  })
+
+  it('"Overview" tab is active by default (has active styling)', async () => {
+    const ClientDetailHub = await getHub()
+    renderWithQuery(<ClientDetailHub clientId="client-1" agentType="marketing" client={clientProp} />)
+    const overviewBtn = screen.getByRole('button', { name: 'Overview' })
+    expect(overviewBtn.className).toMatch(/border-accent/)
+    expect(screen.getByTestId('overview-tab')).toBeInTheDocument()
+  })
+
+  it('clicking "Tasks" tab renders TasksTab, not OverviewTab', async () => {
+    const ClientDetailHub = await getHub()
+    renderWithQuery(<ClientDetailHub clientId="client-1" agentType="marketing" client={clientProp} />)
+    fireEvent.click(screen.getByRole('button', { name: 'Tasks' }))
+    expect(screen.getByTestId('tasks-tab')).toBeInTheDocument()
+    expect(screen.queryByTestId('overview-tab')).not.toBeInTheDocument()
+  })
+
+  it('clicking "Marketing Plan" tab renders MarketingPlanTab', async () => {
+    const ClientDetailHub = await getHub()
+    renderWithQuery(<ClientDetailHub clientId="client-1" agentType="marketing" client={clientProp} />)
+    fireEvent.click(screen.getByRole('button', { name: 'Marketing Plan' }))
+    expect(screen.getByTestId('marketing-plan-tab')).toBeInTheDocument()
+  })
+
+  it('clicking "Time & Capacity" tab renders TimeCapacityTab', async () => {
+    const ClientDetailHub = await getHub()
+    renderWithQuery(<ClientDetailHub clientId="client-1" agentType="marketing" client={clientProp} />)
+    fireEvent.click(screen.getByRole('button', { name: 'Time & Capacity' }))
+    expect(screen.getByTestId('time-capacity-tab')).toBeInTheDocument()
+  })
+
+  it('passes agentType="marketing" prop down to TasksTab', async () => {
+    const ClientDetailHub = await getHub()
+    renderWithQuery(<ClientDetailHub clientId="client-1" agentType="marketing" client={clientProp} />)
+    fireEvent.click(screen.getByRole('button', { name: 'Tasks' }))
+    expect(screen.getByTestId('tasks-tab')).toHaveAttribute('data-agent-type', 'marketing')
+  })
+
+  it('passes agentType="developer" prop down to TasksTab', async () => {
+    const ClientDetailHub = await getHub()
+    renderWithQuery(<ClientDetailHub clientId="client-1" agentType="developer" client={clientProp} />)
+    fireEvent.click(screen.getByRole('button', { name: 'Tasks' }))
+    expect(screen.getByTestId('tasks-tab')).toHaveAttribute('data-agent-type', 'developer')
+  })
+})
diff --git a/client/components/portal/crm/__tests__/ExportReportModal.test.tsx b/client/components/portal/crm/__tests__/ExportReportModal.test.tsx
new file mode 100644
index 000000000..6975371c2
--- /dev/null
+++ b/client/components/portal/crm/__tests__/ExportReportModal.test.tsx
@@ -0,0 +1,87 @@
+import { render, screen, fireEvent } from '@testing-library/react'
+import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
+import React from 'react'
+
+// ── Tests ───────────────────────────────────────────────────────────────────
+
+async function getModal() {
+  const { ExportReportModal } = await import('@/components/portal/crm/export/ExportReportModal')
+  return ExportReportModal
+}
+
+const DEFAULT_PROPS = {
+  open: true,
+  onClose: vi.fn(),
+  clientId: 'client-1',
+  startDate: '2026-01-01',
+  endDate: '2026-03-31',
+}
+
+describe('ExportReportModal', () => {
+  let originalLocation: Location
+
+  beforeEach(() => {
+    originalLocation = window.location
+    Object.defineProperty(window, 'location', {
+      configurable: true,
+      writable: true,
+      value: { href: '' },
+    })
+  })
+
+  afterEach(() => {
+    Object.defineProperty(window, 'location', {
+      configurable: true,
+      writable: true,
+      value: originalLocation,
+    })
+    vi.clearAllMocks()
+  })
+
+  it('renders the current date range (start and end dates)', async () => {
+    const ExportReportModal = await getModal()
+    render(<ExportReportModal {...DEFAULT_PROPS} />)
+    expect(screen.getByText('2026-01-01')).toBeInTheDocument()
+    expect(screen.getByText('2026-03-31')).toBeInTheDocument()
+  })
+
+  it('CSV and PDF options are both present', async () => {
+    const ExportReportModal = await getModal()
+    render(<ExportReportModal {...DEFAULT_PROPS} />)
+    expect(screen.getByRole('radio', { name: 'CSV' })).toBeInTheDocument()
+    expect(screen.getByRole('radio', { name: 'PDF' })).toBeInTheDocument()
+  })
+
+  it('CSV is selected by default', async () => {
+    const ExportReportModal = await getModal()
+    render(<ExportReportModal {...DEFAULT_PROPS} />)
+    const csvRadio = screen.getByRole('radio', { name: 'CSV' }) as HTMLInputElement
+    expect(csvRadio.checked).toBe(true)
+  })
+
+  it('clicking "Download" navigates to the correct CSV URL', async () => {
+    const ExportReportModal = await getModal()
+    render(<ExportReportModal {...DEFAULT_PROPS} />)
+    fireEvent.click(screen.getByRole('button', { name: /download/i }))
+    expect(window.location.href).toBe(
+      '/agent/clients/client-1/report/export/?format=csv&start_date=2026-01-01&end_date=2026-03-31'
+    )
+  })
+
+  it('clicking "Download" with PDF selected uses format=pdf in URL', async () => {
+    const ExportReportModal = await getModal()
+    render(<ExportReportModal {...DEFAULT_PROPS} />)
+    fireEvent.click(screen.getByRole('radio', { name: 'PDF' }))
+    fireEvent.click(screen.getByRole('button', { name: /download/i }))
+    expect(window.location.href).toContain('format=pdf')
+  })
+
+  it('clicking Cancel closes the modal without navigating', async () => {
+    const onClose = vi.fn()
+    const ExportReportModal = await getModal()
+    render(<ExportReportModal {...DEFAULT_PROPS} onClose={onClose} />)
+    fireEvent.click(screen.getByRole('button', { name: /cancel/i }))
+    expect(onClose).toHaveBeenCalledOnce()
+    expect(window.location.href).toBe('')
+  })
+})
diff --git a/client/components/portal/crm/__tests__/MarketingPlanTab.test.tsx b/client/components/portal/crm/__tests__/MarketingPlanTab.test.tsx
new file mode 100644
index 000000000..50688a749
--- /dev/null
+++ b/client/components/portal/crm/__tests__/MarketingPlanTab.test.tsx
@@ -0,0 +1,117 @@
+import { screen, waitFor } from '@testing-library/react'
+import { describe, it, expect, vi } from 'vitest'
+import React from 'react'
+import { renderWithQuery } from '@/test-utils/scheduling'
+import { createMockMarketingPlan } from './factories'
+
+// ── Mocks ───────────────────────────────────────────────────────────────────
+
+const mockUsePlan = vi.fn()
+
+vi.mock('@/components/portal/crm/hooks/useClientMarketingPlan', () => ({
+  useClientMarketingPlan: (...args: unknown[]) => mockUsePlan(...args),
+}))
+
+// ── Tests ───────────────────────────────────────────────────────────────────
+
+async function getTab() {
+  const { MarketingPlanTab } = await import('@/components/portal/crm/tabs/MarketingPlanTab')
+  return MarketingPlanTab
+}
+
+describe('MarketingPlanTab', () => {
+  it('renders markdown from strategy_notes when non-empty', async () => {
+    mockUsePlan.mockReturnValue({
+      data: createMockMarketingPlan(),
+      isLoading: false,
+    })
+    const MarketingPlanTab = await getTab()
+    renderWithQuery(<MarketingPlanTab clientId="client-1" />)
+    await waitFor(() => {
+      expect(screen.getByText('Strategy')).toBeInTheDocument()
+    })
+    expect(screen.getByText(/Focus on content marketing/i)).toBeInTheDocument()
+  })
+
+  it('renders ContentPillar cards with name, description, and target_percentage', async () => {
+    mockUsePlan.mockReturnValue({
+      data: createMockMarketingPlan(),
+      isLoading: false,
+    })
+    const MarketingPlanTab = await getTab()
+    renderWithQuery(<MarketingPlanTab clientId="client-1" />)
+    await waitFor(() => {
+      expect(screen.getByText('Educational')).toBeInTheDocument()
+    })
+    expect(screen.getByText('Educational content')).toBeInTheDocument()
+    expect(screen.getByText('40%')).toBeInTheDocument()
+  })
+
+  it('renders AudiencePersona cards with name and description', async () => {
+    mockUsePlan.mockReturnValue({
+      data: createMockMarketingPlan(),
+      isLoading: false,
+    })
+    const MarketingPlanTab = await getTab()
+    renderWithQuery(<MarketingPlanTab clientId="client-1" />)
+    await waitFor(() => {
+      expect(screen.getByText('SMBs')).toBeInTheDocument()
+    })
+    expect(screen.getByText('Small and medium businesses')).toBeInTheDocument()
+  })
+
+  it('shows "Last updated: {date}" footer', async () => {
+    mockUsePlan.mockReturnValue({
+      data: createMockMarketingPlan(),
+      isLoading: false,
+    })
+    const MarketingPlanTab = await getTab()
+    renderWithQuery(<MarketingPlanTab clientId="client-1" />)
+    await waitFor(() => {
+      expect(screen.getByText(/Last updated:/i)).toBeInTheDocument()
+    })
+  })
+
+  it('shows EmptyState when strategy_notes is empty and no pillars/audiences', async () => {
+    mockUsePlan.mockReturnValue({
+      data: createMockMarketingPlan({ strategy_notes: '', pillars: [], audiences: [] }),
+      isLoading: false,
+    })
+    const MarketingPlanTab = await getTab()
+    renderWithQuery(<MarketingPlanTab clientId="client-1" />)
+    await waitFor(() => {
+      expect(screen.getByText('No marketing plan yet')).toBeInTheDocument()
+    })
+  })
+
+  it('<script> tag inside strategy_notes is NOT rendered in the DOM (XSS protection)', async () => {
+    mockUsePlan.mockReturnValue({
+      data: createMockMarketingPlan({
+        strategy_notes: 'Safe text <script>alert("xss")</script>',
+      }),
+      isLoading: false,
+    })
+    const MarketingPlanTab = await getTab()
+    const { container } = renderWithQuery(<MarketingPlanTab clientId="client-1" />)
+    await waitFor(() => {
+      expect(screen.getByText(/Safe text/i)).toBeInTheDocument()
+    })
+    expect(container.querySelector('script')).toBeNull()
+  })
+
+  it('raw <img> tags referencing external URLs are stripped by rehype-sanitize', async () => {
+    mockUsePlan.mockReturnValue({
+      data: createMockMarketingPlan({
+        strategy_notes: 'Hello ![evil](https://evil.example.com/tracker.gif)',
+      }),
+      isLoading: false,
+    })
+    const MarketingPlanTab = await getTab()
+    const { container } = renderWithQuery(<MarketingPlanTab clientId="client-1" />)
+    await waitFor(() => {
+      expect(screen.getByText(/Hello/i)).toBeInTheDocument()
+    })
+    const imgs = container.querySelectorAll('img[src*="evil.example.com"]')
+    expect(imgs.length).toBe(0)
+  })
+})
diff --git a/client/components/portal/crm/__tests__/OverviewTab.test.tsx b/client/components/portal/crm/__tests__/OverviewTab.test.tsx
new file mode 100644
index 000000000..373a00c1e
--- /dev/null
+++ b/client/components/portal/crm/__tests__/OverviewTab.test.tsx
@@ -0,0 +1,118 @@
+import { screen, waitFor } from '@testing-library/react'
+import { describe, it, expect, vi, beforeEach } from 'vitest'
+import React from 'react'
+import { renderWithQuery } from '@/test-utils/scheduling'
+import { createMockClientReport } from './factories'
+
+// ── Mocks ───────────────────────────────────────────────────────────────────
+
+const mockReport = createMockClientReport()
+
+const mockRequest = vi.fn()
+
+vi.mock('@/lib/api', () => ({
+  default: { request: mockRequest },
+}))
+
+vi.mock('@/components/portal/crm/hooks/useClientReport', () => ({
+  useClientReport: vi.fn().mockReturnValue({
+    data: mockReport,
+    isLoading: false,
+  }),
+}))
+
+// ── Tests ───────────────────────────────────────────────────────────────────
+
+async function getTab() {
+  const { OverviewTab } = await import('@/components/portal/crm/tabs/OverviewTab')
+  return OverviewTab
+}
+
+const client = { id: 'client-1', name: 'Acme Corp', company: 'Acme Inc', status: 'active' }
+
+describe('OverviewTab', () => {
+  beforeEach(() => {
+    mockRequest.mockResolvedValue([
+      {
+        id: 't-1', title: 'Design homepage', status: 'done',
+        updated_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
+        agent: 'a-1', description: '', priority: 'medium', client: 'client-1', client_name: 'Acme',
+        task_category_ref: null, task_category_detail: null, due_date: null, scheduled_date: null,
+        time_block: null, time_block_title: '', estimated_minutes: null, start_time: null,
+        end_time: null, order: 0, is_recurring: false, recurrence_frequency: null,
+        recurrence_days: null, recurrence_interval: 1, recurrence_end_type: 'never',
+        recurrence_end_date: null, recurrence_end_count: null, recurrence_parent: null,
+        recurrence_instance_number: 0, is_overdue: false, completed_at: null,
+        created_at: new Date().toISOString(),
+      },
+    ])
+  })
+
+  it('renders client name, company, status badge', async () => {
+    const OverviewTab = await getTab()
+    renderWithQuery(<OverviewTab clientId="client-1" client={client} />)
+    await waitFor(() => {
+      expect(screen.getByText('Acme Corp')).toBeInTheDocument()
+    })
+    expect(screen.getByText('Acme Inc')).toBeInTheDocument()
+    expect(screen.getByText('active')).toBeInTheDocument()
+  })
+
+  it('renders 5 stat cards: Total Tasks, Completed, In Progress, Days Worked, Total Hours', async () => {
+    const OverviewTab = await getTab()
+    renderWithQuery(<OverviewTab clientId="client-1" client={client} />)
+    await waitFor(() => {
+      expect(screen.getByText('Total Tasks')).toBeInTheDocument()
+    })
+    expect(screen.getByText('Completed')).toBeInTheDocument()
+    expect(screen.getByText('In Progress')).toBeInTheDocument()
+    expect(screen.getByText('Days Worked')).toBeInTheDocument()
+    expect(screen.getByText('Total Hours')).toBeInTheDocument()
+  })
+
+  it('stat values come from useClientReport summary', async () => {
+    const OverviewTab = await getTab()
+    renderWithQuery(<OverviewTab clientId="client-1" client={client} />)
+    await waitFor(() => {
+      expect(screen.getByText('10')).toBeInTheDocument() // total_tasks
+    })
+    expect(screen.getByText('7')).toBeInTheDocument()  // completed_tasks
+    expect(screen.getByText('2')).toBeInTheDocument()  // in_progress_tasks
+    expect(screen.getByText('30')).toBeInTheDocument() // days_worked
+    expect(screen.getByText('45.5')).toBeInTheDocument() // total_hours
+  })
+
+  it('renders recent activity feed with task titles', async () => {
+    const OverviewTab = await getTab()
+    renderWithQuery(<OverviewTab clientId="client-1" client={client} />)
+    await waitFor(() => {
+      expect(screen.getByText('Design homepage')).toBeInTheDocument()
+    })
+  })
+
+  it('each activity item shows relative time', async () => {
+    const OverviewTab = await getTab()
+    renderWithQuery(<OverviewTab clientId="client-1" client={client} />)
+    await waitFor(() => {
+      expect(screen.getByText(/ago/i)).toBeInTheDocument()
+    })
+  })
+
+  it('shows skeleton while data is loading', async () => {
+    const { useClientReport } = await import('@/components/portal/crm/hooks/useClientReport')
+    vi.mocked(useClientReport).mockReturnValueOnce({ data: undefined, isLoading: true } as any)
+    const OverviewTab = await getTab()
+    renderWithQuery(<OverviewTab clientId="client-1" client={client} />)
+    // Skeleton elements should appear (no stat cards rendered)
+    expect(screen.queryByText('Total Tasks')).not.toBeInTheDocument()
+  })
+
+  it('shows empty-state when no tasks exist', async () => {
+    mockRequest.mockResolvedValueOnce([])
+    const OverviewTab = await getTab()
+    renderWithQuery(<OverviewTab clientId="client-1" client={client} />)
+    await waitFor(() => {
+      expect(screen.getByText(/No activity yet/i)).toBeInTheDocument()
+    })
+  })
+})
diff --git a/client/components/portal/crm/__tests__/TasksTab.test.tsx b/client/components/portal/crm/__tests__/TasksTab.test.tsx
new file mode 100644
index 000000000..f89cae95d
--- /dev/null
+++ b/client/components/portal/crm/__tests__/TasksTab.test.tsx
@@ -0,0 +1,110 @@
+import { render, screen, fireEvent } from '@testing-library/react'
+import { describe, it, expect, vi, beforeEach } from 'vitest'
+import React from 'react'
+import { renderWithQuery } from '@/test-utils/scheduling'
+
+// ── Mocks ───────────────────────────────────────────────────────────────────
+
+vi.mock('@/lib/hooks/useScheduling', () => ({
+  useGlobalTasks: vi.fn().mockReturnValue({ data: [], isLoading: false }),
+  useTaskCategories: vi.fn().mockReturnValue({ data: [], isLoading: false }),
+}))
+
+vi.mock('@/lib/hooks/useTaskFilters', () => ({
+  useTaskFilters: () => ({
+    selectedClientIds: [],
+    selectedCategoryIds: [],
+    status: undefined,
+    priority: undefined,
+    search: '',
+    updateClients: vi.fn(),
+    updateCategories: vi.fn(),
+    updateStatus: vi.fn(),
+    updatePriority: vi.fn(),
+    updateSearch: vi.fn(),
+  }),
+}))
+
+vi.mock('@/lib/hooks/useClients', () => ({
+  useClients: () => ({ data: [], isLoading: false }),
+}))
+
+vi.mock('@/lib/hooks/useDebounce', () => ({
+  useDebounce: (val: string) => val,
+}))
+
+vi.mock('@/components/management/tasks/TasksKanbanView', () => ({
+  TasksKanbanView: () => <div data-testid="kanban-view">KanbanView</div>,
+}))
+
+vi.mock('@/components/management/tasks/TasksListView', () => ({
+  default: () => <div data-testid="list-view">ListView</div>,
+}))
+
+vi.mock('@/components/management/tasks/TaskModal', () => ({
+  TaskModal: () => <div data-testid="task-modal">TaskModal</div>,
+}))
+
+// ── Tests ───────────────────────────────────────────────────────────────────
+
+async function getTab() {
+  const { TasksTab } = await import('@/components/portal/crm/tabs/TasksTab')
+  return TasksTab
+}
+
+describe('TasksTab', () => {
+  beforeEach(() => {
+    localStorage.clear()
+  })
+
+  it('renders ViewToggle (list/kanban) button group', async () => {
+    const TasksTab = await getTab()
+    renderWithQuery(<TasksTab clientId="client-1" agentType="marketing" />)
+    expect(screen.getByRole('button', { name: /list view/i })).toBeInTheDocument()
+    expect(screen.getByRole('button', { name: /kanban view/i })).toBeInTheDocument()
+  })
+
+  it('renders TaskFilterBar with ClientFilter hidden', async () => {
+    const TasksTab = await getTab()
+    renderWithQuery(<TasksTab clientId="client-1" agentType="marketing" />)
+    // Client filter select should not be in the DOM
+    expect(screen.queryByRole('combobox', { name: /filter by client/i })).not.toBeInTheDocument()
+    // Other filters should still be present
+    expect(screen.getByRole('combobox', { name: /filter by category/i })).toBeInTheDocument()
+  })
+
+  it('agentType="marketing" — tasks list is filtered by clientId', async () => {
+    const { useGlobalTasks } = await import('@/lib/hooks/useScheduling')
+    const TasksTab = await getTab()
+    renderWithQuery(<TasksTab clientId="client-99" agentType="marketing" />)
+    expect(vi.mocked(useGlobalTasks)).toHaveBeenCalledWith(
+      expect.objectContaining({ client: 'client-99' })
+    )
+  })
+
+  it('agentType="developer" — same task list without "Project Milestones"... false', async () => {
+    const TasksTab = await getTab()
+    renderWithQuery(<TasksTab clientId="client-1" agentType="developer" />)
+    expect(screen.getByText('Project Milestones')).toBeInTheDocument()
+  })
+
+  it('"Project Milestones" section shows "Coming soon" placeholder text', async () => {
+    const TasksTab = await getTab()
+    renderWithQuery(<TasksTab clientId="client-1" agentType="developer" />)
+    expect(screen.getByText('Coming soon')).toBeInTheDocument()
+    expect(screen.getByText(/project milestone tracking will be available/i)).toBeInTheDocument()
+  })
+
+  it('marketing agentType does NOT show "Project Milestones"', async () => {
+    const TasksTab = await getTab()
+    renderWithQuery(<TasksTab clientId="client-1" agentType="marketing" />)
+    expect(screen.queryByText('Project Milestones')).not.toBeInTheDocument()
+  })
+
+  it('switching view toggle persists selection to localStorage', async () => {
+    const TasksTab = await getTab()
+    renderWithQuery(<TasksTab clientId="client-1" agentType="marketing" />)
+    fireEvent.click(screen.getByRole('button', { name: /list view/i }))
+    expect(localStorage.getItem('tasks-view-marketing')).toBe('list')
+  })
+})
diff --git a/client/components/portal/crm/__tests__/TimeCapacityTab.test.tsx b/client/components/portal/crm/__tests__/TimeCapacityTab.test.tsx
new file mode 100644
index 000000000..0ab83cdd1
--- /dev/null
+++ b/client/components/portal/crm/__tests__/TimeCapacityTab.test.tsx
@@ -0,0 +1,110 @@
+import { screen, fireEvent } from '@testing-library/react'
+import { describe, it, expect, vi, beforeEach } from 'vitest'
+import React from 'react'
+import { renderWithQuery } from '@/test-utils/scheduling'
+import { createMockClientReport } from './factories'
+
+// ── Mocks ───────────────────────────────────────────────────────────────────
+
+const mockUseReport = vi.fn()
+
+vi.mock('@/components/portal/crm/hooks/useClientReport', () => ({
+  useClientReport: (...args: unknown[]) => mockUseReport(...args),
+}))
+
+// Mock recharts so they render without canvas issues in jsdom
+vi.mock('recharts', () => ({
+  BarChart: ({ children }: any) => <div data-testid="bar-chart">{children}</div>,
+  Bar: () => null,
+  XAxis: () => null,
+  YAxis: () => null,
+  Tooltip: () => null,
+  ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
+  PieChart: ({ children }: any) => <div data-testid="pie-chart">{children}</div>,
+  Pie: () => null,
+  Cell: () => null,
+  Legend: () => null,
+}))
+
+vi.mock('@/components/portal/crm/export/ExportReportModal', () => ({
+  ExportReportModal: ({ open }: { open: boolean }) =>
+    open ? <div data-testid="export-modal">ExportModal</div> : null,
+}))
+
+// ── Tests ───────────────────────────────────────────────────────────────────
+
+async function getTab() {
+  const { TimeCapacityTab } = await import('@/components/portal/crm/tabs/TimeCapacityTab')
+  return TimeCapacityTab
+}
+
+describe('TimeCapacityTab', () => {
+  beforeEach(() => {
+    mockUseReport.mockReturnValue({
+      data: createMockClientReport(),
+      isLoading: false,
+    })
+  })
+
+  it('"Last 90d" button is active (highlighted) by default', async () => {
+    const TimeCapacityTab = await getTab()
+    renderWithQuery(<TimeCapacityTab clientId="client-1" />)
+    const btn = screen.getByRole('button', { name: 'Last 90d' })
+    expect(btn.className).toMatch(/bg-accent/)
+  })
+
+  it('clicking "Last 30d" calls useClientReport with updated date params', async () => {
+    const TimeCapacityTab = await getTab()
+    renderWithQuery(<TimeCapacityTab clientId="client-1" />)
+    fireEvent.click(screen.getByRole('button', { name: 'Last 30d' }))
+    // useClientReport should be called with a start date ~30 days ago
+    const calls = vi.mocked(mockUseReport).mock.calls
+    const lastCall = calls[calls.length - 1]
+    expect(lastCall[0]).toBe('client-1')
+    // start date should be different from the 90d default
+    expect(lastCall[1]).not.toBe(calls[0][1])
+  })
+
+  it('clicking "Last 6m" calls useClientReport with updated date params', async () => {
+    const TimeCapacityTab = await getTab()
+    renderWithQuery(<TimeCapacityTab clientId="client-1" />)
+    const initialStart = vi.mocked(mockUseReport).mock.calls[0]?.[1]
+    fireEvent.click(screen.getByRole('button', { name: 'Last 6m' }))
+    const calls = vi.mocked(mockUseReport).mock.calls
+    const lastStart = calls[calls.length - 1][1]
+    expect(lastStart).not.toBe(initialStart)
+  })
+
+  it('WeeklyBarChart renders when weekly_breakdown is non-empty', async () => {
+    const TimeCapacityTab = await getTab()
+    renderWithQuery(<TimeCapacityTab clientId="client-1" />)
+    expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
+  })
+
+  it('CategoryDonutChart renders when category_breakdown is non-empty', async () => {
+    const TimeCapacityTab = await getTab()
+    renderWithQuery(<TimeCapacityTab clientId="client-1" />)
+    expect(screen.getByTestId('pie-chart')).toBeInTheDocument()
+  })
+
+  it('monthly summary table renders one row per month entry', async () => {
+    const TimeCapacityTab = await getTab()
+    renderWithQuery(<TimeCapacityTab clientId="client-1" />)
+    expect(screen.getByText('2026-01')).toBeInTheDocument()
+  })
+
+  it('"Export Report" button opens ExportReportModal', async () => {
+    const TimeCapacityTab = await getTab()
+    renderWithQuery(<TimeCapacityTab clientId="client-1" />)
+    expect(screen.queryByTestId('export-modal')).not.toBeInTheDocument()
+    fireEvent.click(screen.getByRole('button', { name: /export report/i }))
+    expect(screen.getByTestId('export-modal')).toBeInTheDocument()
+  })
+
+  it('shows loading skeleton while report is fetching', async () => {
+    mockUseReport.mockReturnValueOnce({ data: undefined, isLoading: true })
+    const TimeCapacityTab = await getTab()
+    renderWithQuery(<TimeCapacityTab clientId="client-1" />)
+    expect(screen.queryByRole('button', { name: /export report/i })).not.toBeInTheDocument()
+  })
+})
diff --git a/client/components/portal/crm/__tests__/factories.ts b/client/components/portal/crm/__tests__/factories.ts
new file mode 100644
index 000000000..c2099cbd7
--- /dev/null
+++ b/client/components/portal/crm/__tests__/factories.ts
@@ -0,0 +1,45 @@
+import type { ClientReportResponse, MarketingPlanDetailResponse } from '@/lib/types/crm'
+
+export function createMockClientReport(
+  overrides?: Partial<ClientReportResponse>
+): ClientReportResponse {
+  return {
+    client: { id: 'client-1', name: 'Acme Corp', company: 'Acme Inc' },
+    period: { start: '2026-01-01', end: '2026-03-31' },
+    summary: {
+      total_tasks: 10,
+      completed_tasks: 7,
+      in_progress_tasks: 2,
+      total_hours: 45.5,
+      days_worked: 30,
+      unique_categories: ['Design', 'Dev'],
+    },
+    category_breakdown: [{ category: 'Design', hours: 20, task_count: 4 }],
+    weekly_breakdown: [{ week_start: '2026-01-06', hours: 8, tasks_completed: 2 }],
+    monthly_summary: [{ month: '2026-01', days: 10, hours: 20, tasks_completed: 4 }],
+    tasks: [],
+    ...overrides,
+  }
+}
+
+export function createMockMarketingPlan(
+  overrides?: Partial<MarketingPlanDetailResponse>
+): MarketingPlanDetailResponse {
+  return {
+    strategy_notes: '# Strategy\n\nFocus on content marketing.',
+    pillars: [
+      {
+        id: 'pillar-1',
+        name: 'Educational',
+        description: 'Educational content',
+        color: '#6366F1',
+        target_percentage: 40,
+      },
+    ],
+    audiences: [
+      { id: 'audience-1', name: 'SMBs', description: 'Small and medium businesses' },
+    ],
+    updated_at: '2026-03-01T00:00:00Z',
+    ...overrides,
+  }
+}
diff --git a/client/components/portal/crm/export/ExportReportModal.tsx b/client/components/portal/crm/export/ExportReportModal.tsx
new file mode 100644
index 000000000..3c3a6f653
--- /dev/null
+++ b/client/components/portal/crm/export/ExportReportModal.tsx
@@ -0,0 +1,84 @@
+'use client'
+
+import React, { useState } from 'react'
+import { Modal } from '@/components/ui/modal'
+import { Button } from '@/components/ui/button'
+
+interface ExportReportModalProps {
+  open: boolean
+  onClose: () => void
+  clientId: string
+  startDate: string
+  endDate: string
+}
+
+export function ExportReportModal({
+  open,
+  onClose,
+  clientId,
+  startDate,
+  endDate,
+}: ExportReportModalProps) {
+  const [format, setFormat] = useState<'csv' | 'pdf'>('csv')
+
+  function handleDownload() {
+    const url = `/agent/clients/${clientId}/report/export/?format=${format}&start_date=${startDate}&end_date=${endDate}`
+    window.location.href = url
+    onClose()
+  }
+
+  return (
+    <Modal isOpen={open} onClose={onClose} size="sm">
+      <div className="flex flex-col gap-4 p-6">
+        <h2 className="text-base font-semibold text-primary">Export Report</h2>
+
+        {/* Date range display */}
+        <p className="text-sm text-secondary">
+          Report period:{' '}
+          <span className="text-primary font-medium">{startDate}</span>
+          {' → '}
+          <span className="text-primary font-medium">{endDate}</span>
+        </p>
+
+        {/* Format picker */}
+        <div className="flex flex-col gap-2">
+          <p className="text-sm font-medium text-primary">Format</p>
+          <div className="flex gap-3">
+            <label className="flex items-center gap-2 cursor-pointer">
+              <input
+                type="radio"
+                name="export-format"
+                value="csv"
+                checked={format === 'csv'}
+                onChange={() => setFormat('csv')}
+                className="accent-accent"
+              />
+              <span className="text-sm text-primary">CSV</span>
+            </label>
+            <label className="flex items-center gap-2 cursor-pointer">
+              <input
+                type="radio"
+                name="export-format"
+                value="pdf"
+                checked={format === 'pdf'}
+                onChange={() => setFormat('pdf')}
+                className="accent-accent"
+              />
+              <span className="text-sm text-primary">PDF</span>
+            </label>
+          </div>
+        </div>
+
+        {/* Actions */}
+        <div className="flex justify-end gap-2 pt-2">
+          <Button variant="ghost" onClick={onClose}>
+            Cancel
+          </Button>
+          <Button variant="primary" onClick={handleDownload}>
+            Download
+          </Button>
+        </div>
+      </div>
+    </Modal>
+  )
+}
diff --git a/client/components/portal/crm/hooks/useClientMarketingPlan.ts b/client/components/portal/crm/hooks/useClientMarketingPlan.ts
new file mode 100644
index 000000000..201a9711c
--- /dev/null
+++ b/client/components/portal/crm/hooks/useClientMarketingPlan.ts
@@ -0,0 +1,17 @@
+import { useQuery, UseQueryResult } from '@tanstack/react-query'
+import api from '@/lib/api'
+import type { MarketingPlanDetailResponse } from '@/lib/types/crm'
+
+export function useClientMarketingPlan(
+  clientId: string
+): UseQueryResult<MarketingPlanDetailResponse> {
+  return useQuery<MarketingPlanDetailResponse>({
+    queryKey: ['client-marketing-plan', clientId],
+    queryFn: () =>
+      api.request<MarketingPlanDetailResponse>(
+        `/agent/clients/${clientId}/marketing-plan/`
+      ),
+    enabled: !!clientId,
+    staleTime: 60_000,
+  })
+}
diff --git a/client/components/portal/crm/hooks/useClientReport.ts b/client/components/portal/crm/hooks/useClientReport.ts
new file mode 100644
index 000000000..84b1bebef
--- /dev/null
+++ b/client/components/portal/crm/hooks/useClientReport.ts
@@ -0,0 +1,19 @@
+import { useQuery, UseQueryResult } from '@tanstack/react-query'
+import api from '@/lib/api'
+import type { ClientReportResponse } from '@/lib/types/crm'
+
+export function useClientReport(
+  clientId: string,
+  startDate: string,
+  endDate: string
+): UseQueryResult<ClientReportResponse> {
+  return useQuery<ClientReportResponse>({
+    queryKey: ['client-report', clientId, startDate, endDate],
+    queryFn: () =>
+      api.request<ClientReportResponse>(
+        `/agent/clients/${clientId}/report/?start_date=${startDate}&end_date=${endDate}`
+      ),
+    enabled: !!clientId,
+    staleTime: 60_000,
+  })
+}
diff --git a/client/components/portal/crm/tabs/MarketingPlanTab.tsx b/client/components/portal/crm/tabs/MarketingPlanTab.tsx
new file mode 100644
index 000000000..50d6ff45b
--- /dev/null
+++ b/client/components/portal/crm/tabs/MarketingPlanTab.tsx
@@ -0,0 +1,129 @@
+'use client'
+
+import React from 'react'
+import ReactMarkdown from 'react-markdown'
+import rehypeSanitize, { defaultSchema } from 'rehype-sanitize'
+import { format } from 'date-fns'
+import { Surface } from '@/components/ui/Surface'
+import { Skeleton } from '@/components/ui/skeleton'
+import { EmptyState } from '@/components/ui/empty-state'
+import { CodeBlock } from '@/components/ui/CodeBlock'
+import { useClientMarketingPlan } from '../hooks/useClientMarketingPlan'
+
+// Sanitization schema that disallows img elements (prevents external tracking pixels)
+const sanitizeSchema = {
+  ...defaultSchema,
+  tagNames: (defaultSchema.tagNames ?? []).filter((tag) => tag !== 'img'),
+}
+
+interface MarketingPlanTabProps {
+  clientId: string
+}
+
+export function MarketingPlanTab({ clientId }: MarketingPlanTabProps) {
+  const { data: plan, isLoading } = useClientMarketingPlan(clientId)
+
+  if (isLoading) {
+    return (
+      <div className="flex flex-col gap-4">
+        <Skeleton className="h-48 w-full rounded-xl" />
+        <Skeleton className="h-32 w-full rounded-xl" />
+      </div>
+    )
+  }
+
+  const isEmpty =
+    !plan ||
+    (!plan.strategy_notes && plan.pillars.length === 0 && plan.audiences.length === 0)
+
+  if (isEmpty) {
+    return (
+      <EmptyState
+        title="No marketing plan yet"
+        description="No marketing plan has been set for this client yet."
+      />
+    )
+  }
+
+  return (
+    <div className="flex flex-col gap-6">
+      {/* Strategy notes */}
+      {plan.strategy_notes && (
+        <Surface variant="outlined" padding="lg">
+          <h3 className="text-base font-semibold text-primary mb-4">Strategy Notes</h3>
+          <div className="prose prose-sm max-w-none text-primary">
+            <ReactMarkdown
+              rehypePlugins={[[rehypeSanitize, sanitizeSchema]]}
+              components={{
+                code({ className, children, ...props }) {
+                  const match = /language-(\w+)/.exec(className || '')
+                  const isBlock = !!(props as { node?: { type?: string } }).node
+                  if (match && isBlock) {
+                    return (
+                      <CodeBlock
+                        code={String(children).replace(/\n$/, '')}
+                        language={match[1]}
+                      />
+                    )
+                  }
+                  return (
+                    <code className="bg-surface-muted px-1 py-0.5 rounded text-sm font-mono" {...props}>
+                      {children}
+                    </code>
+                  )
+                },
+              }}
+            >
+              {plan.strategy_notes}
+            </ReactMarkdown>
+          </div>
+        </Surface>
+      )}
+
+      {/* Content Pillars */}
+      {plan.pillars.length > 0 && (
+        <div>
+          <h3 className="text-base font-semibold text-primary mb-4">Content Pillars</h3>
+          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
+            {plan.pillars.map((pillar) => (
+              <Surface key={pillar.id} variant="outlined" padding="md">
+                <div className="flex items-center gap-2 mb-2">
+                  <span
+                    className="w-3 h-3 rounded-full shrink-0"
+                    style={{ background: pillar.color }}
+                    aria-hidden="true"
+                  />
+                  <h4 className="font-medium text-primary text-sm">{pillar.name}</h4>
+                  <span className="ml-auto text-xs text-muted">{pillar.target_percentage}%</span>
+                </div>
+                <p className="text-secondary text-sm">{pillar.description}</p>
+              </Surface>
+            ))}
+          </div>
+        </div>
+      )}
+
+      {/* Audience Personas */}
+      {plan.audiences.length > 0 && (
+        <div>
+          <h3 className="text-base font-semibold text-primary mb-4">Audience Personas</h3>
+          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
+            {plan.audiences.map((persona) => (
+              <Surface key={persona.id} variant="outlined" padding="md">
+                <h4 className="font-medium text-primary text-sm mb-1">{persona.name}</h4>
+                <p className="text-secondary text-sm">{persona.description}</p>
+              </Surface>
+            ))}
+          </div>
+        </div>
+      )}
+
+      {/* Footer */}
+      {plan.updated_at && (
+        <p className="text-xs text-muted">
+          Last updated: {format(new Date(plan.updated_at), 'MMM d, yyyy')}
+        </p>
+      )}
+    </div>
+  )
+}
diff --git a/client/components/portal/crm/tabs/OverviewTab.tsx b/client/components/portal/crm/tabs/OverviewTab.tsx
new file mode 100644
index 000000000..ca4b4732a
--- /dev/null
+++ b/client/components/portal/crm/tabs/OverviewTab.tsx
@@ -0,0 +1,132 @@
+'use client'
+
+import React from 'react'
+import { useQuery } from '@tanstack/react-query'
+import { format, subDays, formatDistanceToNow } from 'date-fns'
+import { Surface } from '@/components/ui/Surface'
+import { Skeleton } from '@/components/ui/skeleton'
+import { Badge } from '@/components/ui/badge'
+import { EmptyState } from '@/components/ui/empty-state'
+import StatCard from '@/components/common/stat-card'
+import api from '@/lib/api'
+import { useClientReport } from '../hooks/useClientReport'
+import type { AgentGlobalTask } from '@/lib/types/scheduling'
+
+interface ClientInfo {
+  id: string
+  name: string
+  company: string
+  status: string
+  email?: string
+  phone?: string
+  created_at?: string
+}
+
+interface OverviewTabProps {
+  clientId: string
+  client: ClientInfo | undefined
+}
+
+export function OverviewTab({ clientId, client }: OverviewTabProps) {
+  const today = format(new Date(), 'yyyy-MM-dd')
+  const defaultStart = format(subDays(new Date(), 90), 'yyyy-MM-dd')
+
+  const { data: report, isLoading: reportLoading } = useClientReport(clientId, defaultStart, today)
+
+  const { data: activityTasks = [], isLoading: activityLoading } = useQuery<AgentGlobalTask[]>({
+    queryKey: ['client-tasks-activity', clientId],
+    queryFn: () =>
+      api.request<AgentGlobalTask[]>(
+        `/agent/tasks/?client=${clientId}&ordering=-updated_at&limit=10`
+      ),
+    enabled: !!clientId,
+    staleTime: 30_000,
+  })
+
+  const isLoading = reportLoading || activityLoading
+
+  if (isLoading) {
+    return (
+      <div className="flex flex-col gap-4">
+        <Skeleton className="h-32 w-full rounded-xl" />
+        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
+          {Array.from({ length: 5 }).map((_, i) => (
+            <Skeleton key={i} className="h-24 rounded-xl" />
+          ))}
+        </div>
+        <Skeleton className="h-48 w-full rounded-xl" />
+      </div>
+    )
+  }
+
+  const summary = report?.summary
+
+  return (
+    <div className="flex flex-col gap-6">
+      {/* Client info card */}
+      <Surface variant="outlined" padding="lg">
+        <div className="flex items-start justify-between gap-4">
+          <div>
+            <h2 className="text-lg font-semibold text-primary">{client?.name ?? '—'}</h2>
+            <p className="text-secondary text-sm">{client?.company}</p>
+            {client?.email && <p className="text-secondary text-sm mt-1">{client.email}</p>}
+            {client?.phone && <p className="text-secondary text-sm">{client.phone}</p>}
+          </div>
+          <div className="flex flex-col items-end gap-2">
+            {client?.status && (
+              <Badge variant="default" className="capitalize">
+                {client.status}
+              </Badge>
+            )}
+            {client?.created_at && (
+              <p className="text-muted text-xs">
+                Client since{' '}
+                {format(new Date(client.created_at), 'MMM yyyy')}
+              </p>
+            )}
+          </div>
+        </div>
+      </Surface>
+
+      {/* Stats row */}
+      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
+        <StatCard label="Total Tasks" value={summary?.total_tasks ?? 0} />
+        <StatCard label="Completed" value={summary?.completed_tasks ?? 0} />
+        <StatCard label="In Progress" value={summary?.in_progress_tasks ?? 0} />
+        <StatCard label="Days Worked" value={summary?.days_worked ?? 0} />
+        <StatCard label="Total Hours" value={summary?.total_hours ?? 0} />
+      </div>
+
+      {/* Recent activity feed */}
+      <Surface variant="outlined" padding="lg">
+        <h3 className="text-base font-semibold text-primary mb-4">Recent Activity</h3>
+        {activityTasks.length === 0 ? (
+          <EmptyState
+            title="No activity yet"
+            description="Tasks for this client will appear here."
+            size="sm"
+          />
+        ) : (
+          <ol className="flex flex-col gap-3">
+            {activityTasks.slice(0, 10).map((task) => (
+              <li
+                key={task.id}
+                className="flex items-center justify-between gap-2 py-2 border-b border-border-subtle last:border-0"
+              >
+                <div className="flex items-center gap-2 flex-1 min-w-0">
+                  <span className="text-sm text-primary truncate">{task.title}</span>
+                  <Badge variant="default" className="capitalize text-xs shrink-0">
+                    {task.status.replace('_', ' ')}
+                  </Badge>
+                </div>
+                <span className="text-xs text-muted shrink-0">
+                  {formatDistanceToNow(new Date(task.updated_at), { addSuffix: true })}
+                </span>
+              </li>
+            ))}
+          </ol>
+        )}
+      </Surface>
+    </div>
+  )
+}
diff --git a/client/components/portal/crm/tabs/TasksTab.tsx b/client/components/portal/crm/tabs/TasksTab.tsx
new file mode 100644
index 000000000..b55a1101c
--- /dev/null
+++ b/client/components/portal/crm/tabs/TasksTab.tsx
@@ -0,0 +1,100 @@
+'use client'
+
+import React, { useState } from 'react'
+import { Surface } from '@/components/ui/Surface'
+import { EmptyState } from '@/components/ui/empty-state'
+import { Skeleton } from '@/components/ui/skeleton'
+import { ViewToggle } from '@/components/management/tasks/ViewToggle'
+import { TaskFilterBar } from '@/components/management/tasks/TaskFilterBar'
+import { TasksKanbanView } from '@/components/management/tasks/TasksKanbanView'
+import TasksListView from '@/components/management/tasks/TasksListView'
+import { TaskModal } from '@/components/management/tasks/TaskModal'
+import { useGlobalTasks } from '@/lib/hooks/useScheduling'
+import type { AgentGlobalTask } from '@/lib/types/scheduling'
+
+interface TasksTabProps {
+  clientId: string
+  agentType: 'marketing' | 'developer'
+}
+
+export function TasksTab({ clientId, agentType }: TasksTabProps) {
+  const storageKey = `tasks-view-${agentType}`
+
+  const [view, setView] = useState<'kanban' | 'list'>(() => {
+    if (typeof window !== 'undefined') {
+      const saved = localStorage.getItem(storageKey)
+      if (saved === 'kanban' || saved === 'list') return saved
+    }
+    return 'kanban'
+  })
+
+  const [isModalOpen, setIsModalOpen] = useState(false)
+  const [editingTask, setEditingTask] = useState<AgentGlobalTask | undefined>(undefined)
+  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
+
+  const { data: tasks = [], isLoading } = useGlobalTasks({ client: clientId })
+
+  function handleViewChange(newView: 'kanban' | 'list') {
+    setView(newView)
+    localStorage.setItem(storageKey, newView)
+  }
+
+  function handleTaskEdit(task: AgentGlobalTask) {
+    setEditingTask(task)
+    setIsModalOpen(true)
+  }
+
+  function handleModalClose() {
+    setIsModalOpen(false)
+    setEditingTask(undefined)
+  }
+
+  if (isLoading) {
+    return <Skeleton className="h-64 w-full rounded-xl" />
+  }
+
+  return (
+    <div className="flex flex-col gap-4">
+      {/* Controls row */}
+      <div className="flex items-center justify-between gap-3 flex-wrap">
+        <ViewToggle currentView={view} onViewChange={handleViewChange} />
+      </div>
+
+      {/* Filter bar — client filter hidden since we're scoped to this client */}
+      <TaskFilterBar showClientFilter={false} />
+
+      {/* Task view */}
+      {view === 'kanban' ? (
+        <TasksKanbanView tasks={tasks} onTaskEdit={handleTaskEdit} />
+      ) : (
+        <TasksListView
+          tasks={tasks}
+          onTaskEdit={handleTaskEdit}
+          selectedIds={selectedIds}
+          onSelectionChange={setSelectedIds}
+        />
+      )}
+
+      {/* Developer-only: Project Milestones */}
+      {agentType === 'developer' && (
+        <Surface variant="outlined" padding="lg" className="mt-2">
+          <h3 className="text-base font-semibold text-primary mb-4">Project Milestones</h3>
+          <EmptyState
+            title="Coming soon"
+            description="Project milestone tracking will be available in a future update."
+            size="sm"
+          />
+        </Surface>
+      )}
+
+      {/* Task modal */}
+      {isModalOpen && (
+        <TaskModal
+          isOpen={isModalOpen}
+          onClose={handleModalClose}
+          task={editingTask}
+        />
+      )}
+    </div>
+  )
+}
diff --git a/client/components/portal/crm/tabs/TimeCapacityTab.tsx b/client/components/portal/crm/tabs/TimeCapacityTab.tsx
new file mode 100644
index 000000000..b927b81dd
--- /dev/null
+++ b/client/components/portal/crm/tabs/TimeCapacityTab.tsx
@@ -0,0 +1,220 @@
+'use client'
+
+import React, { useState } from 'react'
+import { format, subDays, subMonths } from 'date-fns'
+import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts'
+import { Surface } from '@/components/ui/Surface'
+import { Skeleton } from '@/components/ui/skeleton'
+import { Button } from '@/components/ui/button'
+import { useClientReport } from '../hooks/useClientReport'
+import { ExportReportModal } from '../export/ExportReportModal'
+
+type DateRange = 'last-30d' | 'last-90d' | 'last-6m' | 'custom'
+
+interface TimeCapacityTabProps {
+  clientId: string
+}
+
+const CHART_COLORS = [
+  '#6366F1', '#EC4899', '#06B6D4', '#10B981', '#F59E0B',
+  '#8B5CF6', '#EF4444', '#14B8A6', '#F97316', '#3B82F6',
+]
+
+function deriveRange(dateRange: DateRange, customStart: string, customEnd: string): { startDate: string; endDate: string } {
+  const today = format(new Date(), 'yyyy-MM-dd')
+  switch (dateRange) {
+    case 'last-30d':
+      return { startDate: format(subDays(new Date(), 30), 'yyyy-MM-dd'), endDate: today }
+    case 'last-90d':
+      return { startDate: format(subDays(new Date(), 90), 'yyyy-MM-dd'), endDate: today }
+    case 'last-6m':
+      return { startDate: format(subMonths(new Date(), 6), 'yyyy-MM-dd'), endDate: today }
+    case 'custom':
+      return { startDate: customStart, endDate: customEnd }
+  }
+}
+
+export function TimeCapacityTab({ clientId }: TimeCapacityTabProps) {
+  const [dateRange, setDateRange] = useState<DateRange>('last-90d')
+  const today = format(new Date(), 'yyyy-MM-dd')
+  const [customStart, setCustomStart] = useState(format(subDays(new Date(), 90), 'yyyy-MM-dd'))
+  const [customEnd, setCustomEnd] = useState(today)
+  const [showExportModal, setShowExportModal] = useState(false)
+
+  const { startDate, endDate } = deriveRange(dateRange, customStart, customEnd)
+
+  const { data: report, isLoading } = useClientReport(clientId, startDate, endDate)
+
+  const DATE_RANGE_OPTIONS: { id: DateRange; label: string }[] = [
+    { id: 'last-30d', label: 'Last 30d' },
+    { id: 'last-90d', label: 'Last 90d' },
+    { id: 'last-6m', label: 'Last 6m' },
+    { id: 'custom', label: 'Custom' },
+  ]
+
+  if (isLoading) {
+    return (
+      <div className="flex flex-col gap-4">
+        <Skeleton className="h-10 w-72 rounded-lg" />
+        <div className="grid grid-cols-3 gap-4">
+          {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-20 rounded-xl" />)}
+        </div>
+        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
+          <Skeleton className="h-56 rounded-xl" />
+          <Skeleton className="h-56 rounded-xl" />
+        </div>
+      </div>
+    )
+  }
+
+  return (
+    <div className="flex flex-col gap-6">
+      {/* Date range selector */}
+      <div className="flex items-center gap-2 flex-wrap">
+        <div className="flex rounded-lg border border-border overflow-hidden">
+          {DATE_RANGE_OPTIONS.map((opt) => (
+            <button
+              key={opt.id}
+              type="button"
+              onClick={() => setDateRange(opt.id)}
+              className={`px-3 py-1.5 text-sm font-medium transition-colors ${
+                dateRange === opt.id
+                  ? 'bg-accent text-white'
+                  : 'bg-surface text-secondary hover:text-primary'
+              }`}
+            >
+              {opt.label}
+            </button>
+          ))}
+        </div>
+
+        {dateRange === 'custom' && (
+          <div className="flex items-center gap-2">
+            <input
+              type="date"
+              value={customStart}
+              onChange={(e) => setCustomStart(e.target.value)}
+              className="text-sm border border-border rounded-lg px-2 py-1.5 bg-surface text-primary"
+            />
+            <span className="text-secondary text-sm">→</span>
+            <input
+              type="date"
+              value={customEnd}
+              onChange={(e) => setCustomEnd(e.target.value)}
+              className="text-sm border border-border rounded-lg px-2 py-1.5 bg-surface text-primary"
+            />
+          </div>
+        )}
+      </div>
+
+      {/* Stats row */}
+      <div className="grid grid-cols-3 gap-4">
+        <Surface variant="outlined" padding="md">
+          <p className="text-2xl font-bold text-primary">{report?.summary.days_worked ?? 0}</p>
+          <p className="text-sm text-secondary">Days Worked</p>
+        </Surface>
+        <Surface variant="outlined" padding="md">
+          <p className="text-2xl font-bold text-primary">{report?.summary.total_hours ?? 0}</p>
+          <p className="text-sm text-secondary">Total Hours</p>
+        </Surface>
+        <Surface variant="outlined" padding="md">
+          <p className="text-2xl font-bold text-primary">
+            {report?.summary.unique_categories.length ?? 0}
+          </p>
+          <p className="text-sm text-secondary">Unique Categories</p>
+        </Surface>
+      </div>
+
+      {/* Charts */}
+      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
+        {/* Weekly bar chart */}
+        <Surface variant="outlined" padding="md">
+          <h3 className="text-sm font-semibold text-primary mb-3">Weekly Hours</h3>
+          {report?.weekly_breakdown && report.weekly_breakdown.length > 0 ? (
+            <ResponsiveContainer width="100%" height={200}>
+              <BarChart data={report.weekly_breakdown}>
+                <XAxis dataKey="week_start" tick={{ fontSize: 10 }} />
+                <YAxis tick={{ fontSize: 10 }} />
+                <Tooltip />
+                <Bar dataKey="hours" fill="var(--color-accent)" radius={[3, 3, 0, 0]} />
+              </BarChart>
+            </ResponsiveContainer>
+          ) : (
+            <p className="text-secondary text-sm py-8 text-center">No weekly data available</p>
+          )}
+        </Surface>
+
+        {/* Category donut chart */}
+        <Surface variant="outlined" padding="md">
+          <h3 className="text-sm font-semibold text-primary mb-3">Hours by Category</h3>
+          {report?.category_breakdown && report.category_breakdown.length > 0 ? (
+            <ResponsiveContainer width="100%" height={200}>
+              <PieChart>
+                <Pie
+                  data={report.category_breakdown}
+                  dataKey="hours"
+                  nameKey="category"
+                  cx="50%"
+                  cy="50%"
+                  outerRadius={70}
+                  innerRadius={35}
+                >
+                  {report.category_breakdown.map((_, idx) => (
+                    <Cell key={idx} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
+                  ))}
+                </Pie>
+                <Tooltip />
+                <Legend iconSize={10} wrapperStyle={{ fontSize: 11 }} />
+              </PieChart>
+            </ResponsiveContainer>
+          ) : (
+            <p className="text-secondary text-sm py-8 text-center">No category data available</p>
+          )}
+        </Surface>
+      </div>
+
+      {/* Monthly summary table */}
+      {report?.monthly_summary && report.monthly_summary.length > 0 && (
+        <Surface variant="outlined" padding="lg">
+          <h3 className="text-sm font-semibold text-primary mb-3">Monthly Summary</h3>
+          <table className="w-full text-sm">
+            <thead>
+              <tr className="border-b border-border text-left">
+                <th className="pb-2 font-medium text-secondary">Month</th>
+                <th className="pb-2 font-medium text-secondary">Days</th>
+                <th className="pb-2 font-medium text-secondary">Hours</th>
+                <th className="pb-2 font-medium text-secondary">Tasks Completed</th>
+              </tr>
+            </thead>
+            <tbody>
+              {report.monthly_summary.map((row) => (
+                <tr key={row.month} className="border-b border-border-subtle last:border-0">
+                  <td className="py-2 text-primary">{row.month}</td>
+                  <td className="py-2 text-secondary">{row.days}</td>
+                  <td className="py-2 text-secondary">{row.hours}</td>
+                  <td className="py-2 text-secondary">{row.tasks_completed}</td>
+                </tr>
+              ))}
+            </tbody>
+          </table>
+        </Surface>
+      )}
+
+      {/* Export button */}
+      <div className="flex justify-end">
+        <Button variant="outline" onClick={() => setShowExportModal(true)}>
+          Export Report
+        </Button>
+      </div>
+
+      {/* Export modal */}
+      <ExportReportModal
+        open={showExportModal}
+        onClose={() => setShowExportModal(false)}
+        clientId={clientId}
+        startDate={startDate}
+        endDate={endDate}
+      />
+    </div>
+  )
+}
diff --git a/client/lib/types/crm.ts b/client/lib/types/crm.ts
new file mode 100644
index 000000000..aeed57665
--- /dev/null
+++ b/client/lib/types/crm.ts
@@ -0,0 +1,69 @@
+// CRM Hub types for client reports and marketing plans
+
+export interface ClientReportSummary {
+  total_tasks: number
+  completed_tasks: number
+  in_progress_tasks: number
+  total_hours: number
+  days_worked: number
+  unique_categories: string[]
+}
+
+export interface CategoryBreakdownItem {
+  category: string
+  hours: number
+  task_count: number
+}
+
+export interface WeeklyBreakdownItem {
+  week_start: string // YYYY-MM-DD
+  hours: number
+  tasks_completed: number
+}
+
+export interface MonthlySummaryItem {
+  month: string // YYYY-MM
+  days: number
+  hours: number
+  tasks_completed: number
+}
+
+export interface ReportTaskItem {
+  id: string
+  title: string
+  status: string
+  category: string
+  hours_spent: number
+  completed_at: string | null
+}
+
+export interface ClientReportResponse {
+  client: { id: string; name: string; company: string }
+  period: { start: string; end: string }
+  summary: ClientReportSummary
+  category_breakdown: CategoryBreakdownItem[]
+  weekly_breakdown: WeeklyBreakdownItem[]
+  monthly_summary: MonthlySummaryItem[]
+  tasks: ReportTaskItem[]
+}
+
+export interface ContentPillar {
+  id: string
+  name: string
+  description: string
+  color: string
+  target_percentage: number
+}
+
+export interface AudiencePersona {
+  id: string
+  name: string
+  description: string
+}
+
+export interface MarketingPlanDetailResponse {
+  strategy_notes: string
+  pillars: ContentPillar[]
+  audiences: AudiencePersona[]
+  updated_at: string | null
+}
diff --git a/client/package-lock.json b/client/package-lock.json
index 71612b9ae..4bbad96da 100644
--- a/client/package-lock.json
+++ b/client/package-lock.json
@@ -24,7 +24,9 @@
         "react-chartjs-2": "^5.3.1",
         "react-dom": "19.2.0",
         "react-image-crop": "^11.0.10",
+        "react-markdown": "^10.1.0",
         "recharts": "^2.15.4",
+        "rehype-sanitize": "^6.0.0",
         "simple-peer": "^9.11.1",
         "socket.io-client": "^4.8.1",
         "sonner": "^1.7.3",
@@ -2456,6 +2458,15 @@
       "integrity": "sha512-Ps3T8E8dZDam6fUyNiMkekK3XUsaUEik+idO9/YjPtfj2qruF8tFBXS7XhtE4iIXBLxhmLjP3SXpLhVf21I9Lw==",
       "license": "MIT"
     },
+    "node_modules/@types/debug": {
+      "version": "4.1.13",
+      "resolved": "https://registry.npmjs.org/@types/debug/-/debug-4.1.13.tgz",
+      "integrity": "sha512-KSVgmQmzMwPlmtljOomayoR89W4FynCAi3E8PPs7vmDVPe84hT+vGPKkJfThkmXs0x0jAaa9U8uW8bbfyS2fWw==",
+      "license": "MIT",
+      "dependencies": {
+        "@types/ms": "*"
+      }
+    },
     "node_modules/@types/deep-eql": {
       "version": "4.0.2",
       "resolved": "https://registry.npmjs.org/@types/deep-eql/-/deep-eql-4.0.2.tgz",
@@ -2467,9 +2478,26 @@
       "version": "1.0.8",
       "resolved": "https://registry.npmjs.org/@types/estree/-/estree-1.0.8.tgz",
       "integrity": "sha512-dWHzHa2WqEXI/O1E9OjrocMTKJl2mSrEolh1Iomrv6U+JuNwaHXsXx9bLu5gG7BUWFIN0skIQJQ/L1rIex4X6w==",
-      "dev": true,
       "license": "MIT"
     },
+    "node_modules/@types/estree-jsx": {
+      "version": "1.0.5",
+      "resolved": "https://registry.npmjs.org/@types/estree-jsx/-/estree-jsx-1.0.5.tgz",
+      "integrity": "sha512-52CcUVNFyfb1A2ALocQw/Dd1BQFNmSdkuC3BkZ6iqhdMfQz7JWOFRuJFloOzjk+6WijU56m9oKXFAXc7o3Towg==",
+      "license": "MIT",
+      "dependencies": {
+        "@types/estree": "*"
+      }
+    },
+    "node_modules/@types/hast": {
+      "version": "3.0.4",
+      "resolved": "https://registry.npmjs.org/@types/hast/-/hast-3.0.4.tgz",
+      "integrity": "sha512-WPs+bbQw5aCj+x6laNGWLH3wviHtoCv/P3+otBhbOhJgG8qtpdAMlTCxLtsTWA7LH1Oh/bFCHsBn0TPS5m30EQ==",
+      "license": "MIT",
+      "dependencies": {
+        "@types/unist": "*"
+      }
+    },
     "node_modules/@types/json-schema": {
       "version": "7.0.15",
       "resolved": "https://registry.npmjs.org/@types/json-schema/-/json-schema-7.0.15.tgz",
@@ -2484,6 +2512,21 @@
       "dev": true,
       "license": "MIT"
     },
+    "node_modules/@types/mdast": {
+      "version": "4.0.4",
+      "resolved": "https://registry.npmjs.org/@types/mdast/-/mdast-4.0.4.tgz",
+      "integrity": "sha512-kGaNbPh1k7AFzgpud/gMdvIm5xuECykRR+JnWKQno9TAXVa6WIVCGTPvYGekIDL4uwCZQSYbUxNBSb1aUo79oA==",
+      "license": "MIT",
+      "dependencies": {
+        "@types/unist": "*"
+      }
+    },
+    "node_modules/@types/ms": {
+      "version": "2.1.0",
+      "resolved": "https://registry.npmjs.org/@types/ms/-/ms-2.1.0.tgz",
+      "integrity": "sha512-GsCCIZDE/p3i96vtEqx+7dBUGXrc7zeSK3wwPHIaRThS+9OhWIXRqzs4d6k1SVU8g91DrNRWxWUGhp5KXQb2VA==",
+      "license": "MIT"
+    },
     "node_modules/@types/node": {
       "version": "20.19.26",
       "resolved": "https://registry.npmjs.org/@types/node/-/node-20.19.26.tgz",
@@ -2504,7 +2547,6 @@
       "version": "19.2.7",
       "resolved": "https://registry.npmjs.org/@types/react/-/react-19.2.7.tgz",
       "integrity": "sha512-MWtvHrGZLFttgeEj28VXHxpmwYbor/ATPYbBfSFZEIRK0ecCFLl2Qo55z52Hss+UV9CRN7trSeq1zbgx7YDWWg==",
-      "dev": true,
       "license": "MIT",
       "dependencies": {
         "csstype": "^3.2.2"
@@ -2530,6 +2572,12 @@
         "@types/node": "*"
       }
     },
+    "node_modules/@types/unist": {
+      "version": "3.0.3",
+      "resolved": "https://registry.npmjs.org/@types/unist/-/unist-3.0.3.tgz",
+      "integrity": "sha512-ko/gIFJRv177XgZsZcBwnqJN5x/Gien8qNOn0D5bQU/zAzVf9Zt3BlcUiLqhV9y4ARk0GbT3tnUiPNgnTXzc/Q==",
+      "license": "MIT"
+    },
     "node_modules/@typescript-eslint/eslint-plugin": {
       "version": "8.49.0",
       "resolved": "https://registry.npmjs.org/@typescript-eslint/eslint-plugin/-/eslint-plugin-8.49.0.tgz",
@@ -2812,6 +2860,12 @@
         "url": "https://opencollective.com/typescript-eslint"
       }
     },
+    "node_modules/@ungap/structured-clone": {
+      "version": "1.3.0",
+      "resolved": "https://registry.npmjs.org/@ungap/structured-clone/-/structured-clone-1.3.0.tgz",
+      "integrity": "sha512-WmoN8qaIAo7WTYWbAZuG8PYEhn5fkz7dZrqTBZ7dtt//lL2Gwms1IcnQ5yHqjDfX8Ft5j4YzDM23f87zBfDe9g==",
+      "license": "ISC"
+    },
     "node_modules/@unrs/resolver-binding-android-arm-eabi": {
       "version": "1.11.1",
       "resolved": "https://registry.npmjs.org/@unrs/resolver-binding-android-arm-eabi/-/resolver-binding-android-arm-eabi-1.11.1.tgz",
@@ -3527,6 +3581,16 @@
         "node": ">= 0.4"
       }
     },
+    "node_modules/bail": {
+      "version": "2.0.2",
+      "resolved": "https://registry.npmjs.org/bail/-/bail-2.0.2.tgz",
+      "integrity": "sha512-0xO6mYd7JB2YesxDKplafRpsiOzPt9V02ddPCLbY1xYGPOX24NTyN50qnUxgCPcSoYMhKpAuBTjQoRZCAkUDRw==",
+      "license": "MIT",
+      "funding": {
+        "type": "github",
+        "url": "https://github.com/sponsors/wooorm"
+      }
+    },
     "node_modules/balanced-match": {
       "version": "1.0.2",
       "resolved": "https://registry.npmjs.org/balanced-match/-/balanced-match-1.0.2.tgz",
@@ -3736,6 +3800,16 @@
       ],
       "license": "CC-BY-4.0"
     },
+    "node_modules/ccount": {
+      "version": "2.0.1",
+      "resolved": "https://registry.npmjs.org/ccount/-/ccount-2.0.1.tgz",
+      "integrity": "sha512-eyrF0jiFpY+3drT6383f1qhkbGsLSifNAjA61IUjZjmLCWjItY6LB9ft9YhoDgwfmclB2zhu51Lc7+95b8NRAg==",
+      "license": "MIT",
+      "funding": {
+        "type": "github",
+        "url": "https://github.com/sponsors/wooorm"
+      }
+    },
     "node_modules/chai": {
       "version": "6.2.2",
       "resolved": "https://registry.npmjs.org/chai/-/chai-6.2.2.tgz",
@@ -3763,6 +3837,46 @@
         "url": "https://github.com/chalk/chalk?sponsor=1"
       }
     },
+    "node_modules/character-entities": {
+      "version": "2.0.2",
+      "resolved": "https://registry.npmjs.org/character-entities/-/character-entities-2.0.2.tgz",
+      "integrity": "sha512-shx7oQ0Awen/BRIdkjkvz54PnEEI/EjwXDSIZp86/KKdbafHh1Df/RYGBhn4hbe2+uKC9FnT5UCEdyPz3ai9hQ==",
+      "license": "MIT",
+      "funding": {
+        "type": "github",
+        "url": "https://github.com/sponsors/wooorm"
+      }
+    },
+    "node_modules/character-entities-html4": {
+      "version": "2.1.0",
+      "resolved": "https://registry.npmjs.org/character-entities-html4/-/character-entities-html4-2.1.0.tgz",
+      "integrity": "sha512-1v7fgQRj6hnSwFpq1Eu0ynr/CDEw0rXo2B61qXrLNdHZmPKgb7fqS1a2JwF0rISo9q77jDI8VMEHoApn8qDoZA==",
+      "license": "MIT",
+      "funding": {
+        "type": "github",
+        "url": "https://github.com/sponsors/wooorm"
+      }
+    },
+    "node_modules/character-entities-legacy": {
+      "version": "3.0.0",
+      "resolved": "https://registry.npmjs.org/character-entities-legacy/-/character-entities-legacy-3.0.0.tgz",
+      "integrity": "sha512-RpPp0asT/6ufRm//AJVwpViZbGM/MkjQFxJccQRHmISF/22NBtsHqAWmL+/pmkPWoIUJdWyeVleTl1wydHATVQ==",
+      "license": "MIT",
+      "funding": {
+        "type": "github",
+        "url": "https://github.com/sponsors/wooorm"
+      }
+    },
+    "node_modules/character-reference-invalid": {
+      "version": "2.0.1",
+      "resolved": "https://registry.npmjs.org/character-reference-invalid/-/character-reference-invalid-2.0.1.tgz",
+      "integrity": "sha512-iBZ4F4wRbyORVsu0jPV7gXkOsGYjGHPmAyv+HiHG8gi5PtC9KI2j1+v8/tlibRvjoWX027ypmG/n0HtO5t7unw==",
+      "license": "MIT",
+      "funding": {
+        "type": "github",
+        "url": "https://github.com/sponsors/wooorm"
+      }
+    },
     "node_modules/chart.js": {
       "version": "4.5.1",
       "resolved": "https://registry.npmjs.org/chart.js/-/chart.js-4.5.1.tgz",
@@ -3810,6 +3924,16 @@
       "dev": true,
       "license": "MIT"
     },
+    "node_modules/comma-separated-tokens": {
+      "version": "2.0.3",
+      "resolved": "https://registry.npmjs.org/comma-separated-tokens/-/comma-separated-tokens-2.0.3.tgz",
+      "integrity": "sha512-Fu4hJdvzeylCfQPp9SGWidpzrMs7tTrlu6Vb8XGaRGck8QSNZJJp538Wrb60Lax4fPwR64ViY468OIUTbRlGZg==",
+      "license": "MIT",
+      "funding": {
+        "type": "github",
+        "url": "https://github.com/sponsors/wooorm"
+      }
+    },
     "node_modules/concat-map": {
       "version": "0.0.1",
       "resolved": "https://registry.npmjs.org/concat-map/-/concat-map-0.0.1.tgz",
@@ -4102,6 +4226,19 @@
       "integrity": "sha512-qIMFpTMZmny+MMIitAB6D7iVPEorVw6YQRWkvarTkT4tBeSLLiHzcwj6q0MmYSFCiVpiqPJTJEYIrpcPzVEIvg==",
       "license": "MIT"
     },
+    "node_modules/decode-named-character-reference": {
+      "version": "1.3.0",
+      "resolved": "https://registry.npmjs.org/decode-named-character-reference/-/decode-named-character-reference-1.3.0.tgz",
+      "integrity": "sha512-GtpQYB283KrPp6nRw50q3U9/VfOutZOe103qlN7BPP6Ad27xYnOIWv4lPzo8HCAL+mMZofJ9KEy30fq6MfaK6Q==",
+      "license": "MIT",
+      "dependencies": {
+        "character-entities": "^2.0.0"
+      },
+      "funding": {
+        "type": "github",
+        "url": "https://github.com/sponsors/wooorm"
+      }
+    },
     "node_modules/deep-is": {
       "version": "0.1.4",
       "resolved": "https://registry.npmjs.org/deep-is/-/deep-is-0.1.4.tgz",
@@ -4149,9 +4286,7 @@
       "version": "2.0.3",
       "resolved": "https://registry.npmjs.org/dequal/-/dequal-2.0.3.tgz",
       "integrity": "sha512-0je+qPKHEMohvfRTCEo3CrPG6cAzAYgmzKyxRiYSSDkS6eGJdyVJm7WaYA5ECaAD9wLB2T4EEeymA5aFVcYXCA==",
-      "dev": true,
       "license": "MIT",
-      "peer": true,
       "engines": {
         "node": ">=6"
       }
@@ -4166,6 +4301,19 @@
         "node": ">=8"
       }
     },
+    "node_modules/devlop": {
+      "version": "1.1.0",
+      "resolved": "https://registry.npmjs.org/devlop/-/devlop-1.1.0.tgz",
+      "integrity": "sha512-RWmIqhcFf1lRYBvNmr7qTNuyCt/7/ns2jbpp1+PalgE/rDQcBT0fioSMUpJ93irlUhC5hrg4cYqe6U+0ImW0rA==",
+      "license": "MIT",
+      "dependencies": {
+        "dequal": "^2.0.0"
+      },
+      "funding": {
+        "type": "github",
+        "url": "https://github.com/sponsors/wooorm"
+      }
+    },
     "node_modules/doctrine": {
       "version": "2.1.0",
       "resolved": "https://registry.npmjs.org/doctrine/-/doctrine-2.1.0.tgz",
@@ -4919,6 +5067,16 @@
         "node": ">=4.0"
       }
     },
+    "node_modules/estree-util-is-identifier-name": {
+      "version": "3.0.0",
+      "resolved": "https://registry.npmjs.org/estree-util-is-identifier-name/-/estree-util-is-identifier-name-3.0.0.tgz",
+      "integrity": "sha512-hFtqIDZTIUZ9BXLb8y4pYGyk6+wekIivNVTcmvk8NoOh+VeRn5y6cEHzbURrWbfp1fIqdVipilzj+lfaadNZmg==",
+      "license": "MIT",
+      "funding": {
+        "type": "opencollective",
+        "url": "https://opencollective.com/unified"
+      }
+    },
     "node_modules/estree-walker": {
       "version": "3.0.3",
       "resolved": "https://registry.npmjs.org/estree-walker/-/estree-walker-3.0.3.tgz",
@@ -4955,6 +5113,12 @@
         "node": ">=12.0.0"
       }
     },
+    "node_modules/extend": {
+      "version": "3.0.2",
+      "resolved": "https://registry.npmjs.org/extend/-/extend-3.0.2.tgz",
+      "integrity": "sha512-fjquC59cD7CyW6urNXK0FBufkZcoiGG80wTuPujX590cB5Ttln20E2UB4S/WARVqhXffZl2LNgS+gQdPIIim/g==",
+      "license": "MIT"
+    },
     "node_modules/fast-deep-equal": {
       "version": "3.1.3",
       "resolved": "https://registry.npmjs.org/fast-deep-equal/-/fast-deep-equal-3.1.3.tgz",
@@ -5441,6 +5605,61 @@
         "node": ">= 0.4"
       }
     },
+    "node_modules/hast-util-sanitize": {
+      "version": "5.0.2",
+      "resolved": "https://registry.npmjs.org/hast-util-sanitize/-/hast-util-sanitize-5.0.2.tgz",
+      "integrity": "sha512-3yTWghByc50aGS7JlGhk61SPenfE/p1oaFeNwkOOyrscaOkMGrcW9+Cy/QAIOBpZxP1yqDIzFMR0+Np0i0+usg==",
+      "license": "MIT",
+      "dependencies": {
+        "@types/hast": "^3.0.0",
+        "@ungap/structured-clone": "^1.0.0",
+        "unist-util-position": "^5.0.0"
+      },
+      "funding": {
+        "type": "opencollective",
+        "url": "https://opencollective.com/unified"
+      }
+    },
+    "node_modules/hast-util-to-jsx-runtime": {
+      "version": "2.3.6",
+      "resolved": "https://registry.npmjs.org/hast-util-to-jsx-runtime/-/hast-util-to-jsx-runtime-2.3.6.tgz",
+      "integrity": "sha512-zl6s8LwNyo1P9uw+XJGvZtdFF1GdAkOg8ujOw+4Pyb76874fLps4ueHXDhXWdk6YHQ6OgUtinliG7RsYvCbbBg==",
+      "license": "MIT",
+      "dependencies": {
+        "@types/estree": "^1.0.0",
+        "@types/hast": "^3.0.0",
+        "@types/unist": "^3.0.0",
+        "comma-separated-tokens": "^2.0.0",
+        "devlop": "^1.0.0",
+        "estree-util-is-identifier-name": "^3.0.0",
+        "hast-util-whitespace": "^3.0.0",
+        "mdast-util-mdx-expression": "^2.0.0",
+        "mdast-util-mdx-jsx": "^3.0.0",
+        "mdast-util-mdxjs-esm": "^2.0.0",
+        "property-information": "^7.0.0",
+        "space-separated-tokens": "^2.0.0",
+        "style-to-js": "^1.0.0",
+        "unist-util-position": "^5.0.0",
+        "vfile-message": "^4.0.0"
+      },
+      "funding": {
+        "type": "opencollective",
+        "url": "https://opencollective.com/unified"
+      }
+    },
+    "node_modules/hast-util-whitespace": {
+      "version": "3.0.0",
+      "resolved": "https://registry.npmjs.org/hast-util-whitespace/-/hast-util-whitespace-3.0.0.tgz",
+      "integrity": "sha512-88JUN06ipLwsnv+dVn+OIYOvAuvBMy/Qoi6O7mQHxdPXpjy+Cd6xRkWwux7DKO+4sYILtLBRIKgsdpS2gQc7qw==",
+      "license": "MIT",
+      "dependencies": {
+        "@types/hast": "^3.0.0"
+      },
+      "funding": {
+        "type": "opencollective",
+        "url": "https://opencollective.com/unified"
+      }
+    },
     "node_modules/hermes-estree": {
       "version": "0.25.1",
       "resolved": "https://registry.npmjs.org/hermes-estree/-/hermes-estree-0.25.1.tgz",
@@ -5471,6 +5690,16 @@
         "node": "^20.19.0 || ^22.12.0 || >=24.0.0"
       }
     },
+    "node_modules/html-url-attributes": {
+      "version": "3.0.1",
+      "resolved": "https://registry.npmjs.org/html-url-attributes/-/html-url-attributes-3.0.1.tgz",
+      "integrity": "sha512-ol6UPyBWqsrO6EJySPz2O7ZSr856WDrEzM5zMqp+FJJLGMW35cLYmmZnl0vztAZxRUoNZJFTCohfjuIJ8I4QBQ==",
+      "license": "MIT",
+      "funding": {
+        "type": "opencollective",
+        "url": "https://opencollective.com/unified"
+      }
+    },
     "node_modules/ieee754": {
       "version": "1.2.1",
       "resolved": "https://registry.npmjs.org/ieee754/-/ieee754-1.2.1.tgz",
@@ -5544,6 +5773,12 @@
       "integrity": "sha512-k/vGaX4/Yla3WzyMCvTQOXYeIHvqOKtnqBduzTHpzpQZzAskKMhZ2K+EnBiSM9zGSoIFeMpXKxa4dYeZIQqewQ==",
       "license": "ISC"
     },
+    "node_modules/inline-style-parser": {
+      "version": "0.2.7",
+      "resolved": "https://registry.npmjs.org/inline-style-parser/-/inline-style-parser-0.2.7.tgz",
+      "integrity": "sha512-Nb2ctOyNR8DqQoR0OwRG95uNWIC0C1lCgf5Naz5H6Ji72KZ8OcFZLz2P5sNgwlyoJ8Yif11oMuYs5pBQa86csA==",
+      "license": "MIT"
+    },
     "node_modules/internal-slot": {
       "version": "1.1.0",
       "resolved": "https://registry.npmjs.org/internal-slot/-/internal-slot-1.1.0.tgz",
@@ -5568,6 +5803,30 @@
         "node": ">=12"
       }
     },
+    "node_modules/is-alphabetical": {
+      "version": "2.0.1",
+      "resolved": "https://registry.npmjs.org/is-alphabetical/-/is-alphabetical-2.0.1.tgz",
+      "integrity": "sha512-FWyyY60MeTNyeSRpkM2Iry0G9hpr7/9kD40mD/cGQEuilcZYS4okz8SN2Q6rLCJ8gbCt6fN+rC+6tMGS99LaxQ==",
+      "license": "MIT",
+      "funding": {
+        "type": "github",
+        "url": "https://github.com/sponsors/wooorm"
+      }
+    },
+    "node_modules/is-alphanumerical": {
+      "version": "2.0.1",
+      "resolved": "https://registry.npmjs.org/is-alphanumerical/-/is-alphanumerical-2.0.1.tgz",
+      "integrity": "sha512-hmbYhX/9MUMF5uh7tOXyK/n0ZvWpad5caBA17GsC6vyuCqaWliRG5K1qS9inmUhEMaOBIW7/whAnSwveW/LtZw==",
+      "license": "MIT",
+      "dependencies": {
+        "is-alphabetical": "^2.0.0",
+        "is-decimal": "^2.0.0"
+      },
+      "funding": {
+        "type": "github",
+        "url": "https://github.com/sponsors/wooorm"
+      }
+    },
     "node_modules/is-array-buffer": {
       "version": "3.0.5",
       "resolved": "https://registry.npmjs.org/is-array-buffer/-/is-array-buffer-3.0.5.tgz",
@@ -5726,6 +5985,16 @@
         "url": "https://github.com/sponsors/ljharb"
       }
     },
+    "node_modules/is-decimal": {
+      "version": "2.0.1",
+      "resolved": "https://registry.npmjs.org/is-decimal/-/is-decimal-2.0.1.tgz",
+      "integrity": "sha512-AAB9hiomQs5DXWcRB1rqsxGUstbRroFOPPVAomNk/3XHR5JyEZChOyTWe2oayKnsSsr/kcGqF+z6yuH6HHpN0A==",
+      "license": "MIT",
+      "funding": {
+        "type": "github",
+        "url": "https://github.com/sponsors/wooorm"
+      }
+    },
     "node_modules/is-extglob": {
       "version": "2.1.1",
       "resolved": "https://registry.npmjs.org/is-extglob/-/is-extglob-2.1.1.tgz",
@@ -5785,6 +6054,16 @@
         "node": ">=0.10.0"
       }
     },
+    "node_modules/is-hexadecimal": {
+      "version": "2.0.1",
+      "resolved": "https://registry.npmjs.org/is-hexadecimal/-/is-hexadecimal-2.0.1.tgz",
+      "integrity": "sha512-DgZQp241c8oO6cA1SbTEWiXeoxV42vlcJxgH+B3hi1AiqqKruZR3ZGF8In3fj4+/y/7rHvlOZLZtgJ/4ttYGZg==",
+      "license": "MIT",
+      "funding": {
+        "type": "github",
+        "url": "https://github.com/sponsors/wooorm"
+      }
+    },
     "node_modules/is-map": {
       "version": "2.0.3",
       "resolved": "https://registry.npmjs.org/is-map/-/is-map-2.0.3.tgz",
@@ -5838,6 +6117,18 @@
         "url": "https://github.com/sponsors/ljharb"
       }
     },
+    "node_modules/is-plain-obj": {
+      "version": "4.1.0",
+      "resolved": "https://registry.npmjs.org/is-plain-obj/-/is-plain-obj-4.1.0.tgz",
+      "integrity": "sha512-+Pgi+vMuUNkJyExiMBt5IlFoMyKnr5zhJ4Uspz58WOhBF5QoIZkFyNHIbBAtHwzVAgk5RtndVNsDRN61/mmDqg==",
+      "license": "MIT",
+      "engines": {
+        "node": ">=12"
+      },
+      "funding": {
+        "url": "https://github.com/sponsors/sindresorhus"
+      }
+    },
     "node_modules/is-potential-custom-element-name": {
       "version": "1.0.1",
       "resolved": "https://registry.npmjs.org/is-potential-custom-element-name/-/is-potential-custom-element-name-1.0.1.tgz",
@@ -6499,6 +6790,16 @@
       "dev": true,
       "license": "MIT"
     },
+    "node_modules/longest-streak": {
+      "version": "3.1.0",
+      "resolved": "https://registry.npmjs.org/longest-streak/-/longest-streak-3.1.0.tgz",
+      "integrity": "sha512-9Ri+o0JYgehTaVBBDoMqIl8GXtbWg711O3srftcHhZ0dqnETqLaoIK0x17fUw9rFSlK/0NlsKe0Ahhyl5pXE2g==",
+      "license": "MIT",
+      "funding": {
+        "type": "github",
+        "url": "https://github.com/sponsors/wooorm"
+      }
+    },
     "node_modules/loose-envify": {
       "version": "1.4.0",
       "resolved": "https://registry.npmjs.org/loose-envify/-/loose-envify-1.4.0.tgz",
@@ -6561,84 +6862,679 @@
         "node": ">= 0.4"
       }
     },
-    "node_modules/mdn-data": {
-      "version": "2.27.1",
-      "resolved": "https://registry.npmjs.org/mdn-data/-/mdn-data-2.27.1.tgz",
-      "integrity": "sha512-9Yubnt3e8A0OKwxYSXyhLymGW4sCufcLG6VdiDdUGVkPhpqLxlvP5vl1983gQjJl3tqbrM731mjaZaP68AgosQ==",
-      "dev": true,
-      "license": "CC0-1.0"
-    },
-    "node_modules/merge2": {
-      "version": "1.4.1",
-      "resolved": "https://registry.npmjs.org/merge2/-/merge2-1.4.1.tgz",
-      "integrity": "sha512-8q7VEgMJW4J8tcfVPy8g09NcQwZdbwFEqhe/WZkoIzjn/3TGDwtOCYtXGxA3O8tPzpczCCDgv+P2P5y00ZJOOg==",
-      "dev": true,
+    "node_modules/mdast-util-from-markdown": {
+      "version": "2.0.3",
+      "resolved": "https://registry.npmjs.org/mdast-util-from-markdown/-/mdast-util-from-markdown-2.0.3.tgz",
+      "integrity": "sha512-W4mAWTvSlKvf8L6J+VN9yLSqQ9AOAAvHuoDAmPkz4dHf553m5gVj2ejadHJhoJmcmxEnOv6Pa8XJhpxE93kb8Q==",
       "license": "MIT",
-      "engines": {
-        "node": ">= 8"
+      "dependencies": {
+        "@types/mdast": "^4.0.0",
+        "@types/unist": "^3.0.0",
+        "decode-named-character-reference": "^1.0.0",
+        "devlop": "^1.0.0",
+        "mdast-util-to-string": "^4.0.0",
+        "micromark": "^4.0.0",
+        "micromark-util-decode-numeric-character-reference": "^2.0.0",
+        "micromark-util-decode-string": "^2.0.0",
+        "micromark-util-normalize-identifier": "^2.0.0",
+        "micromark-util-symbol": "^2.0.0",
+        "micromark-util-types": "^2.0.0",
+        "unist-util-stringify-position": "^4.0.0"
+      },
+      "funding": {
+        "type": "opencollective",
+        "url": "https://opencollective.com/unified"
       }
     },
-    "node_modules/micromatch": {
-      "version": "4.0.8",
-      "resolved": "https://registry.npmjs.org/micromatch/-/micromatch-4.0.8.tgz",
-      "integrity": "sha512-PXwfBhYu0hBCPw8Dn0E+WDYb7af3dSLVWKi3HGv84IdF4TyFoC0ysxFd0Goxw7nSv4T/PzEJQxsYsEiFCKo2BA==",
-      "dev": true,
+    "node_modules/mdast-util-mdx-expression": {
+      "version": "2.0.1",
+      "resolved": "https://registry.npmjs.org/mdast-util-mdx-expression/-/mdast-util-mdx-expression-2.0.1.tgz",
+      "integrity": "sha512-J6f+9hUp+ldTZqKRSg7Vw5V6MqjATc+3E4gf3CFNcuZNWD8XdyI6zQ8GqH7f8169MM6P7hMBRDVGnn7oHB9kXQ==",
       "license": "MIT",
       "dependencies": {
-        "braces": "^3.0.3",
-        "picomatch": "^2.3.1"
+        "@types/estree-jsx": "^1.0.0",
+        "@types/hast": "^3.0.0",
+        "@types/mdast": "^4.0.0",
+        "devlop": "^1.0.0",
+        "mdast-util-from-markdown": "^2.0.0",
+        "mdast-util-to-markdown": "^2.0.0"
       },
-      "engines": {
-        "node": ">=8.6"
+      "funding": {
+        "type": "opencollective",
+        "url": "https://opencollective.com/unified"
       }
     },
-    "node_modules/min-indent": {
-      "version": "1.0.1",
-      "resolved": "https://registry.npmjs.org/min-indent/-/min-indent-1.0.1.tgz",
-      "integrity": "sha512-I9jwMn07Sy/IwOj3zVkVik2JTvgpaykDZEigL6Rx6N9LbMywwUSMtxET+7lVoDLLd3O3IXwJwvuuns8UB/HeAg==",
-      "dev": true,
+    "node_modules/mdast-util-mdx-jsx": {
+      "version": "3.2.0",
+      "resolved": "https://registry.npmjs.org/mdast-util-mdx-jsx/-/mdast-util-mdx-jsx-3.2.0.tgz",
+      "integrity": "sha512-lj/z8v0r6ZtsN/cGNNtemmmfoLAFZnjMbNyLzBafjzikOM+glrjNHPlf6lQDOTccj9n5b0PPihEBbhneMyGs1Q==",
       "license": "MIT",
-      "engines": {
-        "node": ">=4"
+      "dependencies": {
+        "@types/estree-jsx": "^1.0.0",
+        "@types/hast": "^3.0.0",
+        "@types/mdast": "^4.0.0",
+        "@types/unist": "^3.0.0",
+        "ccount": "^2.0.0",
+        "devlop": "^1.1.0",
+        "mdast-util-from-markdown": "^2.0.0",
+        "mdast-util-to-markdown": "^2.0.0",
+        "parse-entities": "^4.0.0",
+        "stringify-entities": "^4.0.0",
+        "unist-util-stringify-position": "^4.0.0",
+        "vfile-message": "^4.0.0"
+      },
+      "funding": {
+        "type": "opencollective",
+        "url": "https://opencollective.com/unified"
       }
     },
-    "node_modules/minimatch": {
-      "version": "3.1.5",
-      "resolved": "https://registry.npmjs.org/minimatch/-/minimatch-3.1.5.tgz",
-      "integrity": "sha512-VgjWUsnnT6n+NUk6eZq77zeFdpW2LWDzP6zFGrCbHXiYNul5Dzqk2HHQ5uFH2DNW5Xbp8+jVzaeNt94ssEEl4w==",
-      "dev": true,
-      "license": "ISC",
+    "node_modules/mdast-util-mdxjs-esm": {
+      "version": "2.0.1",
+      "resolved": "https://registry.npmjs.org/mdast-util-mdxjs-esm/-/mdast-util-mdxjs-esm-2.0.1.tgz",
+      "integrity": "sha512-EcmOpxsZ96CvlP03NghtH1EsLtr0n9Tm4lPUJUBccV9RwUOneqSycg19n5HGzCf+10LozMRSObtVr3ee1WoHtg==",
+      "license": "MIT",
       "dependencies": {
-        "brace-expansion": "^1.1.7"
+        "@types/estree-jsx": "^1.0.0",
+        "@types/hast": "^3.0.0",
+        "@types/mdast": "^4.0.0",
+        "devlop": "^1.0.0",
+        "mdast-util-from-markdown": "^2.0.0",
+        "mdast-util-to-markdown": "^2.0.0"
       },
-      "engines": {
-        "node": "*"
+      "funding": {
+        "type": "opencollective",
+        "url": "https://opencollective.com/unified"
       }
     },
-    "node_modules/minimist": {
-      "version": "1.2.8",
-      "resolved": "https://registry.npmjs.org/minimist/-/minimist-1.2.8.tgz",
-      "integrity": "sha512-2yyAR8qBkN3YuheJanUpWC5U3bb5osDywNB8RzDVlDwDHbocAJveqqj1u8+SVD7jkWT4yvsHCpWqqWqAxb0zCA==",
-      "dev": true,
+    "node_modules/mdast-util-phrasing": {
+      "version": "4.1.0",
+      "resolved": "https://registry.npmjs.org/mdast-util-phrasing/-/mdast-util-phrasing-4.1.0.tgz",
+      "integrity": "sha512-TqICwyvJJpBwvGAMZjj4J2n0X8QWp21b9l0o7eXyVJ25YNWYbJDVIyD1bZXE6WtV6RmKJVYmQAKWa0zWOABz2w==",
       "license": "MIT",
+      "dependencies": {
+        "@types/mdast": "^4.0.0",
+        "unist-util-is": "^6.0.0"
+      },
       "funding": {
-        "url": "https://github.com/sponsors/ljharb"
+        "type": "opencollective",
+        "url": "https://opencollective.com/unified"
       }
     },
-    "node_modules/motion-dom": {
-      "version": "11.18.1",
-      "resolved": "https://registry.npmjs.org/motion-dom/-/motion-dom-11.18.1.tgz",
-      "integrity": "sha512-g76KvA001z+atjfxczdRtw/RXOM3OMSdd1f4DL77qCTF/+avrRJiawSG4yDibEQ215sr9kpinSlX2pCTJ9zbhw==",
+    "node_modules/mdast-util-to-hast": {
+      "version": "13.2.1",
+      "resolved": "https://registry.npmjs.org/mdast-util-to-hast/-/mdast-util-to-hast-13.2.1.tgz",
+      "integrity": "sha512-cctsq2wp5vTsLIcaymblUriiTcZd0CwWtCbLvrOzYCDZoWyMNV8sZ7krj09FSnsiJi3WVsHLM4k6Dq/yaPyCXA==",
       "license": "MIT",
       "dependencies": {
-        "motion-utils": "^11.18.1"
+        "@types/hast": "^3.0.0",
+        "@types/mdast": "^4.0.0",
+        "@ungap/structured-clone": "^1.0.0",
+        "devlop": "^1.0.0",
+        "micromark-util-sanitize-uri": "^2.0.0",
+        "trim-lines": "^3.0.0",
+        "unist-util-position": "^5.0.0",
+        "unist-util-visit": "^5.0.0",
+        "vfile": "^6.0.0"
+      },
+      "funding": {
+        "type": "opencollective",
+        "url": "https://opencollective.com/unified"
       }
     },
-    "node_modules/motion-utils": {
-      "version": "11.18.1",
-      "resolved": "https://registry.npmjs.org/motion-utils/-/motion-utils-11.18.1.tgz",
-      "integrity": "sha512-49Kt+HKjtbJKLtgO/LKj9Ld+6vw9BjH5d9sc40R/kVyH8GLAXgT42M2NnuPcJNuA3s9ZfZBUcwIgpmZWGEE+hA==",
-      "license": "MIT"
+    "node_modules/mdast-util-to-markdown": {
+      "version": "2.1.2",
+      "resolved": "https://registry.npmjs.org/mdast-util-to-markdown/-/mdast-util-to-markdown-2.1.2.tgz",
+      "integrity": "sha512-xj68wMTvGXVOKonmog6LwyJKrYXZPvlwabaryTjLh9LuvovB/KAH+kvi8Gjj+7rJjsFi23nkUxRQv1KqSroMqA==",
+      "license": "MIT",
+      "dependencies": {
+        "@types/mdast": "^4.0.0",
+        "@types/unist": "^3.0.0",
+        "longest-streak": "^3.0.0",
+        "mdast-util-phrasing": "^4.0.0",
+        "mdast-util-to-string": "^4.0.0",
+        "micromark-util-classify-character": "^2.0.0",
+        "micromark-util-decode-string": "^2.0.0",
+        "unist-util-visit": "^5.0.0",
+        "zwitch": "^2.0.0"
+      },
+      "funding": {
+        "type": "opencollective",
+        "url": "https://opencollective.com/unified"
+      }
+    },
+    "node_modules/mdast-util-to-string": {
+      "version": "4.0.0",
+      "resolved": "https://registry.npmjs.org/mdast-util-to-string/-/mdast-util-to-string-4.0.0.tgz",
+      "integrity": "sha512-0H44vDimn51F0YwvxSJSm0eCDOJTRlmN0R1yBh4HLj9wiV1Dn0QoXGbvFAWj2hSItVTlCmBF1hqKlIyUBVFLPg==",
+      "license": "MIT",
+      "dependencies": {
+        "@types/mdast": "^4.0.0"
+      },
+      "funding": {
+        "type": "opencollective",
+        "url": "https://opencollective.com/unified"
+      }
+    },
+    "node_modules/mdn-data": {
+      "version": "2.27.1",
+      "resolved": "https://registry.npmjs.org/mdn-data/-/mdn-data-2.27.1.tgz",
+      "integrity": "sha512-9Yubnt3e8A0OKwxYSXyhLymGW4sCufcLG6VdiDdUGVkPhpqLxlvP5vl1983gQjJl3tqbrM731mjaZaP68AgosQ==",
+      "dev": true,
+      "license": "CC0-1.0"
+    },
+    "node_modules/merge2": {
+      "version": "1.4.1",
+      "resolved": "https://registry.npmjs.org/merge2/-/merge2-1.4.1.tgz",
+      "integrity": "sha512-8q7VEgMJW4J8tcfVPy8g09NcQwZdbwFEqhe/WZkoIzjn/3TGDwtOCYtXGxA3O8tPzpczCCDgv+P2P5y00ZJOOg==",
+      "dev": true,
+      "license": "MIT",
+      "engines": {
+        "node": ">= 8"
+      }
+    },
+    "node_modules/micromark": {
+      "version": "4.0.2",
+      "resolved": "https://registry.npmjs.org/micromark/-/micromark-4.0.2.tgz",
+      "integrity": "sha512-zpe98Q6kvavpCr1NPVSCMebCKfD7CA2NqZ+rykeNhONIJBpc1tFKt9hucLGwha3jNTNI8lHpctWJWoimVF4PfA==",
+      "funding": [
+        {
+          "type": "GitHub Sponsors",
+          "url": "https://github.com/sponsors/unifiedjs"
+        },
+        {
+          "type": "OpenCollective",
+          "url": "https://opencollective.com/unified"
+        }
+      ],
+      "license": "MIT",
+      "dependencies": {
+        "@types/debug": "^4.0.0",
+        "debug": "^4.0.0",
+        "decode-named-character-reference": "^1.0.0",
+        "devlop": "^1.0.0",
+        "micromark-core-commonmark": "^2.0.0",
+        "micromark-factory-space": "^2.0.0",
+        "micromark-util-character": "^2.0.0",
+        "micromark-util-chunked": "^2.0.0",
+        "micromark-util-combine-extensions": "^2.0.0",
+        "micromark-util-decode-numeric-character-reference": "^2.0.0",
+        "micromark-util-encode": "^2.0.0",
+        "micromark-util-normalize-identifier": "^2.0.0",
+        "micromark-util-resolve-all": "^2.0.0",
+        "micromark-util-sanitize-uri": "^2.0.0",
+        "micromark-util-subtokenize": "^2.0.0",
+        "micromark-util-symbol": "^2.0.0",
+        "micromark-util-types": "^2.0.0"
+      }
+    },
+    "node_modules/micromark-core-commonmark": {
+      "version": "2.0.3",
+      "resolved": "https://registry.npmjs.org/micromark-core-commonmark/-/micromark-core-commonmark-2.0.3.tgz",
+      "integrity": "sha512-RDBrHEMSxVFLg6xvnXmb1Ayr2WzLAWjeSATAoxwKYJV94TeNavgoIdA0a9ytzDSVzBy2YKFK+emCPOEibLeCrg==",
+      "funding": [
+        {
+          "type": "GitHub Sponsors",
+          "url": "https://github.com/sponsors/unifiedjs"
+        },
+        {
+          "type": "OpenCollective",
+          "url": "https://opencollective.com/unified"
+        }
+      ],
+      "license": "MIT",
+      "dependencies": {
+        "decode-named-character-reference": "^1.0.0",
+        "devlop": "^1.0.0",
+        "micromark-factory-destination": "^2.0.0",
+        "micromark-factory-label": "^2.0.0",
+        "micromark-factory-space": "^2.0.0",
+        "micromark-factory-title": "^2.0.0",
+        "micromark-factory-whitespace": "^2.0.0",
+        "micromark-util-character": "^2.0.0",
+        "micromark-util-chunked": "^2.0.0",
+        "micromark-util-classify-character": "^2.0.0",
+        "micromark-util-html-tag-name": "^2.0.0",
+        "micromark-util-normalize-identifier": "^2.0.0",
+        "micromark-util-resolve-all": "^2.0.0",
+        "micromark-util-subtokenize": "^2.0.0",
+        "micromark-util-symbol": "^2.0.0",
+        "micromark-util-types": "^2.0.0"
+      }
+    },
+    "node_modules/micromark-factory-destination": {
+      "version": "2.0.1",
+      "resolved": "https://registry.npmjs.org/micromark-factory-destination/-/micromark-factory-destination-2.0.1.tgz",
+      "integrity": "sha512-Xe6rDdJlkmbFRExpTOmRj9N3MaWmbAgdpSrBQvCFqhezUn4AHqJHbaEnfbVYYiexVSs//tqOdY/DxhjdCiJnIA==",
+      "funding": [
+        {
+          "type": "GitHub Sponsors",
+          "url": "https://github.com/sponsors/unifiedjs"
+        },
+        {
+          "type": "OpenCollective",
+          "url": "https://opencollective.com/unified"
+        }
+      ],
+      "license": "MIT",
+      "dependencies": {
+        "micromark-util-character": "^2.0.0",
+        "micromark-util-symbol": "^2.0.0",
+        "micromark-util-types": "^2.0.0"
+      }
+    },
+    "node_modules/micromark-factory-label": {
+      "version": "2.0.1",
+      "resolved": "https://registry.npmjs.org/micromark-factory-label/-/micromark-factory-label-2.0.1.tgz",
+      "integrity": "sha512-VFMekyQExqIW7xIChcXn4ok29YE3rnuyveW3wZQWWqF4Nv9Wk5rgJ99KzPvHjkmPXF93FXIbBp6YdW3t71/7Vg==",
+      "funding": [
+        {
+          "type": "GitHub Sponsors",
+          "url": "https://github.com/sponsors/unifiedjs"
+        },
+        {
+          "type": "OpenCollective",
+          "url": "https://opencollective.com/unified"
+        }
+      ],
+      "license": "MIT",
+      "dependencies": {
+        "devlop": "^1.0.0",
+        "micromark-util-character": "^2.0.0",
+        "micromark-util-symbol": "^2.0.0",
+        "micromark-util-types": "^2.0.0"
+      }
+    },
+    "node_modules/micromark-factory-space": {
+      "version": "2.0.1",
+      "resolved": "https://registry.npmjs.org/micromark-factory-space/-/micromark-factory-space-2.0.1.tgz",
+      "integrity": "sha512-zRkxjtBxxLd2Sc0d+fbnEunsTj46SWXgXciZmHq0kDYGnck/ZSGj9/wULTV95uoeYiK5hRXP2mJ98Uo4cq/LQg==",
+      "funding": [
+        {
+          "type": "GitHub Sponsors",
+          "url": "https://github.com/sponsors/unifiedjs"
+        },
+        {
+          "type": "OpenCollective",
+          "url": "https://opencollective.com/unified"
+        }
+      ],
+      "license": "MIT",
+      "dependencies": {
+        "micromark-util-character": "^2.0.0",
+        "micromark-util-types": "^2.0.0"
+      }
+    },
+    "node_modules/micromark-factory-title": {
+      "version": "2.0.1",
+      "resolved": "https://registry.npmjs.org/micromark-factory-title/-/micromark-factory-title-2.0.1.tgz",
+      "integrity": "sha512-5bZ+3CjhAd9eChYTHsjy6TGxpOFSKgKKJPJxr293jTbfry2KDoWkhBb6TcPVB4NmzaPhMs1Frm9AZH7OD4Cjzw==",
+      "funding": [
+        {
+          "type": "GitHub Sponsors",
+          "url": "https://github.com/sponsors/unifiedjs"
+        },
+        {
+          "type": "OpenCollective",
+          "url": "https://opencollective.com/unified"
+        }
+      ],
+      "license": "MIT",
+      "dependencies": {
+        "micromark-factory-space": "^2.0.0",
+        "micromark-util-character": "^2.0.0",
+        "micromark-util-symbol": "^2.0.0",
+        "micromark-util-types": "^2.0.0"
+      }
+    },
+    "node_modules/micromark-factory-whitespace": {
+      "version": "2.0.1",
+      "resolved": "https://registry.npmjs.org/micromark-factory-whitespace/-/micromark-factory-whitespace-2.0.1.tgz",
+      "integrity": "sha512-Ob0nuZ3PKt/n0hORHyvoD9uZhr+Za8sFoP+OnMcnWK5lngSzALgQYKMr9RJVOWLqQYuyn6ulqGWSXdwf6F80lQ==",
+      "funding": [
+        {
+          "type": "GitHub Sponsors",
+          "url": "https://github.com/sponsors/unifiedjs"
+        },
+        {
+          "type": "OpenCollective",
+          "url": "https://opencollective.com/unified"
+        }
+      ],
+      "license": "MIT",
+      "dependencies": {
+        "micromark-factory-space": "^2.0.0",
+        "micromark-util-character": "^2.0.0",
+        "micromark-util-symbol": "^2.0.0",
+        "micromark-util-types": "^2.0.0"
+      }
+    },
+    "node_modules/micromark-util-character": {
+      "version": "2.1.1",
+      "resolved": "https://registry.npmjs.org/micromark-util-character/-/micromark-util-character-2.1.1.tgz",
+      "integrity": "sha512-wv8tdUTJ3thSFFFJKtpYKOYiGP2+v96Hvk4Tu8KpCAsTMs6yi+nVmGh1syvSCsaxz45J6Jbw+9DD6g97+NV67Q==",
+      "funding": [
+        {
+          "type": "GitHub Sponsors",
+          "url": "https://github.com/sponsors/unifiedjs"
+        },
+        {
+          "type": "OpenCollective",
+          "url": "https://opencollective.com/unified"
+        }
+      ],
+      "license": "MIT",
+      "dependencies": {
+        "micromark-util-symbol": "^2.0.0",
+        "micromark-util-types": "^2.0.0"
+      }
+    },
+    "node_modules/micromark-util-chunked": {
+      "version": "2.0.1",
+      "resolved": "https://registry.npmjs.org/micromark-util-chunked/-/micromark-util-chunked-2.0.1.tgz",
+      "integrity": "sha512-QUNFEOPELfmvv+4xiNg2sRYeS/P84pTW0TCgP5zc9FpXetHY0ab7SxKyAQCNCc1eK0459uoLI1y5oO5Vc1dbhA==",
+      "funding": [
+        {
+          "type": "GitHub Sponsors",
+          "url": "https://github.com/sponsors/unifiedjs"
+        },
+        {
+          "type": "OpenCollective",
+          "url": "https://opencollective.com/unified"
+        }
+      ],
+      "license": "MIT",
+      "dependencies": {
+        "micromark-util-symbol": "^2.0.0"
+      }
+    },
+    "node_modules/micromark-util-classify-character": {
+      "version": "2.0.1",
+      "resolved": "https://registry.npmjs.org/micromark-util-classify-character/-/micromark-util-classify-character-2.0.1.tgz",
+      "integrity": "sha512-K0kHzM6afW/MbeWYWLjoHQv1sgg2Q9EccHEDzSkxiP/EaagNzCm7T/WMKZ3rjMbvIpvBiZgwR3dKMygtA4mG1Q==",
+      "funding": [
+        {
+          "type": "GitHub Sponsors",
+          "url": "https://github.com/sponsors/unifiedjs"
+        },
+        {
+          "type": "OpenCollective",
+          "url": "https://opencollective.com/unified"
+        }
+      ],
+      "license": "MIT",
+      "dependencies": {
+        "micromark-util-character": "^2.0.0",
+        "micromark-util-symbol": "^2.0.0",
+        "micromark-util-types": "^2.0.0"
+      }
+    },
+    "node_modules/micromark-util-combine-extensions": {
+      "version": "2.0.1",
+      "resolved": "https://registry.npmjs.org/micromark-util-combine-extensions/-/micromark-util-combine-extensions-2.0.1.tgz",
+      "integrity": "sha512-OnAnH8Ujmy59JcyZw8JSbK9cGpdVY44NKgSM7E9Eh7DiLS2E9RNQf0dONaGDzEG9yjEl5hcqeIsj4hfRkLH/Bg==",
+      "funding": [
+        {
+          "type": "GitHub Sponsors",
+          "url": "https://github.com/sponsors/unifiedjs"
+        },
+        {
+          "type": "OpenCollective",
+          "url": "https://opencollective.com/unified"
+        }
+      ],
+      "license": "MIT",
+      "dependencies": {
+        "micromark-util-chunked": "^2.0.0",
+        "micromark-util-types": "^2.0.0"
+      }
+    },
+    "node_modules/micromark-util-decode-numeric-character-reference": {
+      "version": "2.0.2",
+      "resolved": "https://registry.npmjs.org/micromark-util-decode-numeric-character-reference/-/micromark-util-decode-numeric-character-reference-2.0.2.tgz",
+      "integrity": "sha512-ccUbYk6CwVdkmCQMyr64dXz42EfHGkPQlBj5p7YVGzq8I7CtjXZJrubAYezf7Rp+bjPseiROqe7G6foFd+lEuw==",
+      "funding": [
+        {
+          "type": "GitHub Sponsors",
+          "url": "https://github.com/sponsors/unifiedjs"
+        },
+        {
+          "type": "OpenCollective",
+          "url": "https://opencollective.com/unified"
+        }
+      ],
+      "license": "MIT",
+      "dependencies": {
+        "micromark-util-symbol": "^2.0.0"
+      }
+    },
+    "node_modules/micromark-util-decode-string": {
+      "version": "2.0.1",
+      "resolved": "https://registry.npmjs.org/micromark-util-decode-string/-/micromark-util-decode-string-2.0.1.tgz",
+      "integrity": "sha512-nDV/77Fj6eH1ynwscYTOsbK7rR//Uj0bZXBwJZRfaLEJ1iGBR6kIfNmlNqaqJf649EP0F3NWNdeJi03elllNUQ==",
+      "funding": [
+        {
+          "type": "GitHub Sponsors",
+          "url": "https://github.com/sponsors/unifiedjs"
+        },
+        {
+          "type": "OpenCollective",
+          "url": "https://opencollective.com/unified"
+        }
+      ],
+      "license": "MIT",
+      "dependencies": {
+        "decode-named-character-reference": "^1.0.0",
+        "micromark-util-character": "^2.0.0",
+        "micromark-util-decode-numeric-character-reference": "^2.0.0",
+        "micromark-util-symbol": "^2.0.0"
+      }
+    },
+    "node_modules/micromark-util-encode": {
+      "version": "2.0.1",
+      "resolved": "https://registry.npmjs.org/micromark-util-encode/-/micromark-util-encode-2.0.1.tgz",
+      "integrity": "sha512-c3cVx2y4KqUnwopcO9b/SCdo2O67LwJJ/UyqGfbigahfegL9myoEFoDYZgkT7f36T0bLrM9hZTAaAyH+PCAXjw==",
+      "funding": [
+        {
+          "type": "GitHub Sponsors",
+          "url": "https://github.com/sponsors/unifiedjs"
+        },
+        {
+          "type": "OpenCollective",
+          "url": "https://opencollective.com/unified"
+        }
+      ],
+      "license": "MIT"
+    },
+    "node_modules/micromark-util-html-tag-name": {
+      "version": "2.0.1",
+      "resolved": "https://registry.npmjs.org/micromark-util-html-tag-name/-/micromark-util-html-tag-name-2.0.1.tgz",
+      "integrity": "sha512-2cNEiYDhCWKI+Gs9T0Tiysk136SnR13hhO8yW6BGNyhOC4qYFnwF1nKfD3HFAIXA5c45RrIG1ub11GiXeYd1xA==",
+      "funding": [
+        {
+          "type": "GitHub Sponsors",
+          "url": "https://github.com/sponsors/unifiedjs"
+        },
+        {
+          "type": "OpenCollective",
+          "url": "https://opencollective.com/unified"
+        }
+      ],
+      "license": "MIT"
+    },
+    "node_modules/micromark-util-normalize-identifier": {
+      "version": "2.0.1",
+      "resolved": "https://registry.npmjs.org/micromark-util-normalize-identifier/-/micromark-util-normalize-identifier-2.0.1.tgz",
+      "integrity": "sha512-sxPqmo70LyARJs0w2UclACPUUEqltCkJ6PhKdMIDuJ3gSf/Q+/GIe3WKl0Ijb/GyH9lOpUkRAO2wp0GVkLvS9Q==",
+      "funding": [
+        {
+          "type": "GitHub Sponsors",
+          "url": "https://github.com/sponsors/unifiedjs"
+        },
+        {
+          "type": "OpenCollective",
+          "url": "https://opencollective.com/unified"
+        }
+      ],
+      "license": "MIT",
+      "dependencies": {
+        "micromark-util-symbol": "^2.0.0"
+      }
+    },
+    "node_modules/micromark-util-resolve-all": {
+      "version": "2.0.1",
+      "resolved": "https://registry.npmjs.org/micromark-util-resolve-all/-/micromark-util-resolve-all-2.0.1.tgz",
+      "integrity": "sha512-VdQyxFWFT2/FGJgwQnJYbe1jjQoNTS4RjglmSjTUlpUMa95Htx9NHeYW4rGDJzbjvCsl9eLjMQwGeElsqmzcHg==",
+      "funding": [
+        {
+          "type": "GitHub Sponsors",
+          "url": "https://github.com/sponsors/unifiedjs"
+        },
+        {
+          "type": "OpenCollective",
+          "url": "https://opencollective.com/unified"
+        }
+      ],
+      "license": "MIT",
+      "dependencies": {
+        "micromark-util-types": "^2.0.0"
+      }
+    },
+    "node_modules/micromark-util-sanitize-uri": {
+      "version": "2.0.1",
+      "resolved": "https://registry.npmjs.org/micromark-util-sanitize-uri/-/micromark-util-sanitize-uri-2.0.1.tgz",
+      "integrity": "sha512-9N9IomZ/YuGGZZmQec1MbgxtlgougxTodVwDzzEouPKo3qFWvymFHWcnDi2vzV1ff6kas9ucW+o3yzJK9YB1AQ==",
+      "funding": [
+        {
+          "type": "GitHub Sponsors",
+          "url": "https://github.com/sponsors/unifiedjs"
+        },
+        {
+          "type": "OpenCollective",
+          "url": "https://opencollective.com/unified"
+        }
+      ],
+      "license": "MIT",
+      "dependencies": {
+        "micromark-util-character": "^2.0.0",
+        "micromark-util-encode": "^2.0.0",
+        "micromark-util-symbol": "^2.0.0"
+      }
+    },
+    "node_modules/micromark-util-subtokenize": {
+      "version": "2.1.0",
+      "resolved": "https://registry.npmjs.org/micromark-util-subtokenize/-/micromark-util-subtokenize-2.1.0.tgz",
+      "integrity": "sha512-XQLu552iSctvnEcgXw6+Sx75GflAPNED1qx7eBJ+wydBb2KCbRZe+NwvIEEMM83uml1+2WSXpBAcp9IUCgCYWA==",
+      "funding": [
+        {
+          "type": "GitHub Sponsors",
+          "url": "https://github.com/sponsors/unifiedjs"
+        },
+        {
+          "type": "OpenCollective",
+          "url": "https://opencollective.com/unified"
+        }
+      ],
+      "license": "MIT",
+      "dependencies": {
+        "devlop": "^1.0.0",
+        "micromark-util-chunked": "^2.0.0",
+        "micromark-util-symbol": "^2.0.0",
+        "micromark-util-types": "^2.0.0"
+      }
+    },
+    "node_modules/micromark-util-symbol": {
+      "version": "2.0.1",
+      "resolved": "https://registry.npmjs.org/micromark-util-symbol/-/micromark-util-symbol-2.0.1.tgz",
+      "integrity": "sha512-vs5t8Apaud9N28kgCrRUdEed4UJ+wWNvicHLPxCa9ENlYuAY31M0ETy5y1vA33YoNPDFTghEbnh6efaE8h4x0Q==",
+      "funding": [
+        {
+          "type": "GitHub Sponsors",
+          "url": "https://github.com/sponsors/unifiedjs"
+        },
+        {
+          "type": "OpenCollective",
+          "url": "https://opencollective.com/unified"
+        }
+      ],
+      "license": "MIT"
+    },
+    "node_modules/micromark-util-types": {
+      "version": "2.0.2",
+      "resolved": "https://registry.npmjs.org/micromark-util-types/-/micromark-util-types-2.0.2.tgz",
+      "integrity": "sha512-Yw0ECSpJoViF1qTU4DC6NwtC4aWGt1EkzaQB8KPPyCRR8z9TWeV0HbEFGTO+ZY1wB22zmxnJqhPyTpOVCpeHTA==",
+      "funding": [
+        {
+          "type": "GitHub Sponsors",
+          "url": "https://github.com/sponsors/unifiedjs"
+        },
+        {
+          "type": "OpenCollective",
+          "url": "https://opencollective.com/unified"
+        }
+      ],
+      "license": "MIT"
+    },
+    "node_modules/micromatch": {
+      "version": "4.0.8",
+      "resolved": "https://registry.npmjs.org/micromatch/-/micromatch-4.0.8.tgz",
+      "integrity": "sha512-PXwfBhYu0hBCPw8Dn0E+WDYb7af3dSLVWKi3HGv84IdF4TyFoC0ysxFd0Goxw7nSv4T/PzEJQxsYsEiFCKo2BA==",
+      "dev": true,
+      "license": "MIT",
+      "dependencies": {
+        "braces": "^3.0.3",
+        "picomatch": "^2.3.1"
+      },
+      "engines": {
+        "node": ">=8.6"
+      }
+    },
+    "node_modules/min-indent": {
+      "version": "1.0.1",
+      "resolved": "https://registry.npmjs.org/min-indent/-/min-indent-1.0.1.tgz",
+      "integrity": "sha512-I9jwMn07Sy/IwOj3zVkVik2JTvgpaykDZEigL6Rx6N9LbMywwUSMtxET+7lVoDLLd3O3IXwJwvuuns8UB/HeAg==",
+      "dev": true,
+      "license": "MIT",
+      "engines": {
+        "node": ">=4"
+      }
+    },
+    "node_modules/minimatch": {
+      "version": "3.1.5",
+      "resolved": "https://registry.npmjs.org/minimatch/-/minimatch-3.1.5.tgz",
+      "integrity": "sha512-VgjWUsnnT6n+NUk6eZq77zeFdpW2LWDzP6zFGrCbHXiYNul5Dzqk2HHQ5uFH2DNW5Xbp8+jVzaeNt94ssEEl4w==",
+      "dev": true,
+      "license": "ISC",
+      "dependencies": {
+        "brace-expansion": "^1.1.7"
+      },
+      "engines": {
+        "node": "*"
+      }
+    },
+    "node_modules/minimist": {
+      "version": "1.2.8",
+      "resolved": "https://registry.npmjs.org/minimist/-/minimist-1.2.8.tgz",
+      "integrity": "sha512-2yyAR8qBkN3YuheJanUpWC5U3bb5osDywNB8RzDVlDwDHbocAJveqqj1u8+SVD7jkWT4yvsHCpWqqWqAxb0zCA==",
+      "dev": true,
+      "license": "MIT",
+      "funding": {
+        "url": "https://github.com/sponsors/ljharb"
+      }
+    },
+    "node_modules/motion-dom": {
+      "version": "11.18.1",
+      "resolved": "https://registry.npmjs.org/motion-dom/-/motion-dom-11.18.1.tgz",
+      "integrity": "sha512-g76KvA001z+atjfxczdRtw/RXOM3OMSdd1f4DL77qCTF/+avrRJiawSG4yDibEQ215sr9kpinSlX2pCTJ9zbhw==",
+      "license": "MIT",
+      "dependencies": {
+        "motion-utils": "^11.18.1"
+      }
+    },
+    "node_modules/motion-utils": {
+      "version": "11.18.1",
+      "resolved": "https://registry.npmjs.org/motion-utils/-/motion-utils-11.18.1.tgz",
+      "integrity": "sha512-49Kt+HKjtbJKLtgO/LKj9Ld+6vw9BjH5d9sc40R/kVyH8GLAXgT42M2NnuPcJNuA3s9ZfZBUcwIgpmZWGEE+hA==",
+      "license": "MIT"
     },
     "node_modules/ms": {
       "version": "2.1.3",
@@ -6988,6 +7884,31 @@
         "node": ">=6"
       }
     },
+    "node_modules/parse-entities": {
+      "version": "4.0.2",
+      "resolved": "https://registry.npmjs.org/parse-entities/-/parse-entities-4.0.2.tgz",
+      "integrity": "sha512-GG2AQYWoLgL877gQIKeRPGO1xF9+eG1ujIb5soS5gPvLQ1y2o8FL90w2QWNdf9I361Mpp7726c+lj3U0qK1uGw==",
+      "license": "MIT",
+      "dependencies": {
+        "@types/unist": "^2.0.0",
+        "character-entities-legacy": "^3.0.0",
+        "character-reference-invalid": "^2.0.0",
+        "decode-named-character-reference": "^1.0.0",
+        "is-alphanumerical": "^2.0.0",
+        "is-decimal": "^2.0.0",
+        "is-hexadecimal": "^2.0.0"
+      },
+      "funding": {
+        "type": "github",
+        "url": "https://github.com/sponsors/wooorm"
+      }
+    },
+    "node_modules/parse-entities/node_modules/@types/unist": {
+      "version": "2.0.11",
+      "resolved": "https://registry.npmjs.org/@types/unist/-/unist-2.0.11.tgz",
+      "integrity": "sha512-CmBKiL6NNo/OqgmMn95Fk9Whlp2mtvIv+KNpQKN2F4SjvrEesubTRWGYSg+BnWZOnlCaSTU1sMpsBOzgbYhnsA==",
+      "license": "MIT"
+    },
     "node_modules/parse5": {
       "version": "8.0.0",
       "resolved": "https://registry.npmjs.org/parse5/-/parse5-8.0.0.tgz",
@@ -7165,6 +8086,16 @@
         "react-is": "^16.13.1"
       }
     },
+    "node_modules/property-information": {
+      "version": "7.1.0",
+      "resolved": "https://registry.npmjs.org/property-information/-/property-information-7.1.0.tgz",
+      "integrity": "sha512-TwEZ+X+yCJmYfL7TPUOcvBZ4QfoT5YenQiJuX//0th53DE6w0xxLEtfK3iyryQFddXuvkIk51EEgrJQ0WJkOmQ==",
+      "license": "MIT",
+      "funding": {
+        "type": "github",
+        "url": "https://github.com/sponsors/wooorm"
+      }
+    },
     "node_modules/punycode": {
       "version": "2.3.1",
       "resolved": "https://registry.npmjs.org/punycode/-/punycode-2.3.1.tgz",
@@ -7250,6 +8181,33 @@
       "integrity": "sha512-24e6ynE2H+OKt4kqsOvNd8kBpV65zoxbA4BVsEOB3ARVWQki/DHzaUoC5KuON/BiccDaCCTZBuOcfZs70kR8bQ==",
       "license": "MIT"
     },
+    "node_modules/react-markdown": {
+      "version": "10.1.0",
+      "resolved": "https://registry.npmjs.org/react-markdown/-/react-markdown-10.1.0.tgz",
+      "integrity": "sha512-qKxVopLT/TyA6BX3Ue5NwabOsAzm0Q7kAPwq6L+wWDwisYs7R8vZ0nRXqq6rkueboxpkjvLGU9fWifiX/ZZFxQ==",
+      "license": "MIT",
+      "dependencies": {
+        "@types/hast": "^3.0.0",
+        "@types/mdast": "^4.0.0",
+        "devlop": "^1.0.0",
+        "hast-util-to-jsx-runtime": "^2.0.0",
+        "html-url-attributes": "^3.0.0",
+        "mdast-util-to-hast": "^13.0.0",
+        "remark-parse": "^11.0.0",
+        "remark-rehype": "^11.0.0",
+        "unified": "^11.0.0",
+        "unist-util-visit": "^5.0.0",
+        "vfile": "^6.0.0"
+      },
+      "funding": {
+        "type": "opencollective",
+        "url": "https://opencollective.com/unified"
+      },
+      "peerDependencies": {
+        "@types/react": ">=18",
+        "react": ">=18"
+      }
+    },
     "node_modules/react-smooth": {
       "version": "4.0.4",
       "resolved": "https://registry.npmjs.org/react-smooth/-/react-smooth-4.0.4.tgz",
@@ -7391,6 +8349,53 @@
         "url": "https://github.com/sponsors/ljharb"
       }
     },
+    "node_modules/rehype-sanitize": {
+      "version": "6.0.0",
+      "resolved": "https://registry.npmjs.org/rehype-sanitize/-/rehype-sanitize-6.0.0.tgz",
+      "integrity": "sha512-CsnhKNsyI8Tub6L4sm5ZFsme4puGfc6pYylvXo1AeqaGbjOYyzNv3qZPwvs0oMJ39eryyeOdmxwUIo94IpEhqg==",
+      "license": "MIT",
+      "dependencies": {
+        "@types/hast": "^3.0.0",
+        "hast-util-sanitize": "^5.0.0"
+      },
+      "funding": {
+        "type": "opencollective",
+        "url": "https://opencollective.com/unified"
+      }
+    },
+    "node_modules/remark-parse": {
+      "version": "11.0.0",
+      "resolved": "https://registry.npmjs.org/remark-parse/-/remark-parse-11.0.0.tgz",
+      "integrity": "sha512-FCxlKLNGknS5ba/1lmpYijMUzX2esxW5xQqjWxw2eHFfS2MSdaHVINFmhjo+qN1WhZhNimq0dZATN9pH0IDrpA==",
+      "license": "MIT",
+      "dependencies": {
+        "@types/mdast": "^4.0.0",
+        "mdast-util-from-markdown": "^2.0.0",
+        "micromark-util-types": "^2.0.0",
+        "unified": "^11.0.0"
+      },
+      "funding": {
+        "type": "opencollective",
+        "url": "https://opencollective.com/unified"
+      }
+    },
+    "node_modules/remark-rehype": {
+      "version": "11.1.2",
+      "resolved": "https://registry.npmjs.org/remark-rehype/-/remark-rehype-11.1.2.tgz",
+      "integrity": "sha512-Dh7l57ianaEoIpzbp0PC9UKAdCSVklD8E5Rpw7ETfbTl3FqcOOgq5q2LVDhgGCkaBv7p24JXikPdvhhmHvKMsw==",
+      "license": "MIT",
+      "dependencies": {
+        "@types/hast": "^3.0.0",
+        "@types/mdast": "^4.0.0",
+        "mdast-util-to-hast": "^13.0.0",
+        "unified": "^11.0.0",
+        "vfile": "^6.0.0"
+      },
+      "funding": {
+        "type": "opencollective",
+        "url": "https://opencollective.com/unified"
+      }
+    },
     "node_modules/require-from-string": {
       "version": "2.0.2",
       "resolved": "https://registry.npmjs.org/require-from-string/-/require-from-string-2.0.2.tgz",
@@ -7945,6 +8950,16 @@
         "node": ">=0.10.0"
       }
     },
+    "node_modules/space-separated-tokens": {
+      "version": "2.0.2",
+      "resolved": "https://registry.npmjs.org/space-separated-tokens/-/space-separated-tokens-2.0.2.tgz",
+      "integrity": "sha512-PEGlAwrG8yXGXRjW32fGbg66JAlOAwbObuqVoJpv/mRgoWDQfgH1wDPvtzWyUSNAXBGSk8h755YDbbcEy3SH2Q==",
+      "license": "MIT",
+      "funding": {
+        "type": "github",
+        "url": "https://github.com/sponsors/wooorm"
+      }
+    },
     "node_modules/stable-hash": {
       "version": "0.0.5",
       "resolved": "https://registry.npmjs.org/stable-hash/-/stable-hash-0.0.5.tgz",
@@ -8102,6 +9117,20 @@
         "url": "https://github.com/sponsors/ljharb"
       }
     },
+    "node_modules/stringify-entities": {
+      "version": "4.0.4",
+      "resolved": "https://registry.npmjs.org/stringify-entities/-/stringify-entities-4.0.4.tgz",
+      "integrity": "sha512-IwfBptatlO+QCJUo19AqvrPNqlVMpW9YEL2LIVY+Rpv2qsjCGxaDLNRgeGsQWJhfItebuJhsGSLjaBbNSQ+ieg==",
+      "license": "MIT",
+      "dependencies": {
+        "character-entities-html4": "^2.0.0",
+        "character-entities-legacy": "^3.0.0"
+      },
+      "funding": {
+        "type": "github",
+        "url": "https://github.com/sponsors/wooorm"
+      }
+    },
     "node_modules/strip-bom": {
       "version": "3.0.0",
       "resolved": "https://registry.npmjs.org/strip-bom/-/strip-bom-3.0.0.tgz",
@@ -8138,6 +9167,24 @@
         "url": "https://github.com/sponsors/sindresorhus"
       }
     },
+    "node_modules/style-to-js": {
+      "version": "1.1.21",
+      "resolved": "https://registry.npmjs.org/style-to-js/-/style-to-js-1.1.21.tgz",
+      "integrity": "sha512-RjQetxJrrUJLQPHbLku6U/ocGtzyjbJMP9lCNK7Ag0CNh690nSH8woqWH9u16nMjYBAok+i7JO1NP2pOy8IsPQ==",
+      "license": "MIT",
+      "dependencies": {
+        "style-to-object": "1.0.14"
+      }
+    },
+    "node_modules/style-to-object": {
+      "version": "1.0.14",
+      "resolved": "https://registry.npmjs.org/style-to-object/-/style-to-object-1.0.14.tgz",
+      "integrity": "sha512-LIN7rULI0jBscWQYaSswptyderlarFkjQ+t79nzty8tcIAceVomEVlLzH5VP4Cmsv6MtKhs7qaAiwlcp+Mgaxw==",
+      "license": "MIT",
+      "dependencies": {
+        "inline-style-parser": "0.2.7"
+      }
+    },
     "node_modules/styled-jsx": {
       "version": "5.1.6",
       "resolved": "https://registry.npmjs.org/styled-jsx/-/styled-jsx-5.1.6.tgz",
@@ -8365,6 +9412,26 @@
         "node": ">=20"
       }
     },
+    "node_modules/trim-lines": {
+      "version": "3.0.1",
+      "resolved": "https://registry.npmjs.org/trim-lines/-/trim-lines-3.0.1.tgz",
+      "integrity": "sha512-kRj8B+YHZCc9kQYdWfJB2/oUl9rA99qbowYYBtr4ui4mZyAQ2JpvVBd/6U2YloATfqBhBTSMhTpgBHtU0Mf3Rg==",
+      "license": "MIT",
+      "funding": {
+        "type": "github",
+        "url": "https://github.com/sponsors/wooorm"
+      }
+    },
+    "node_modules/trough": {
+      "version": "2.2.0",
+      "resolved": "https://registry.npmjs.org/trough/-/trough-2.2.0.tgz",
+      "integrity": "sha512-tmMpK00BjZiUyVyvrBK7knerNgmgvcV/KLVyuma/SC+TQN167GrMRciANTz09+k3zW8L8t60jWO1GpfkZdjTaw==",
+      "license": "MIT",
+      "funding": {
+        "type": "github",
+        "url": "https://github.com/sponsors/wooorm"
+      }
+    },
     "node_modules/ts-api-utils": {
       "version": "2.1.0",
       "resolved": "https://registry.npmjs.org/ts-api-utils/-/ts-api-utils-2.1.0.tgz",
@@ -8575,6 +9642,93 @@
       "dev": true,
       "license": "MIT"
     },
+    "node_modules/unified": {
+      "version": "11.0.5",
+      "resolved": "https://registry.npmjs.org/unified/-/unified-11.0.5.tgz",
+      "integrity": "sha512-xKvGhPWw3k84Qjh8bI3ZeJjqnyadK+GEFtazSfZv/rKeTkTjOJho6mFqh2SM96iIcZokxiOpg78GazTSg8+KHA==",
+      "license": "MIT",
+      "dependencies": {
+        "@types/unist": "^3.0.0",
+        "bail": "^2.0.0",
+        "devlop": "^1.0.0",
+        "extend": "^3.0.0",
+        "is-plain-obj": "^4.0.0",
+        "trough": "^2.0.0",
+        "vfile": "^6.0.0"
+      },
+      "funding": {
+        "type": "opencollective",
+        "url": "https://opencollective.com/unified"
+      }
+    },
+    "node_modules/unist-util-is": {
+      "version": "6.0.1",
+      "resolved": "https://registry.npmjs.org/unist-util-is/-/unist-util-is-6.0.1.tgz",
+      "integrity": "sha512-LsiILbtBETkDz8I9p1dQ0uyRUWuaQzd/cuEeS1hoRSyW5E5XGmTzlwY1OrNzzakGowI9Dr/I8HVaw4hTtnxy8g==",
+      "license": "MIT",
+      "dependencies": {
+        "@types/unist": "^3.0.0"
+      },
+      "funding": {
+        "type": "opencollective",
+        "url": "https://opencollective.com/unified"
+      }
+    },
+    "node_modules/unist-util-position": {
+      "version": "5.0.0",
+      "resolved": "https://registry.npmjs.org/unist-util-position/-/unist-util-position-5.0.0.tgz",
+      "integrity": "sha512-fucsC7HjXvkB5R3kTCO7kUjRdrS0BJt3M/FPxmHMBOm8JQi2BsHAHFsy27E0EolP8rp0NzXsJ+jNPyDWvOJZPA==",
+      "license": "MIT",
+      "dependencies": {
+        "@types/unist": "^3.0.0"
+      },
+      "funding": {
+        "type": "opencollective",
+        "url": "https://opencollective.com/unified"
+      }
+    },
+    "node_modules/unist-util-stringify-position": {
+      "version": "4.0.0",
+      "resolved": "https://registry.npmjs.org/unist-util-stringify-position/-/unist-util-stringify-position-4.0.0.tgz",
+      "integrity": "sha512-0ASV06AAoKCDkS2+xw5RXJywruurpbC4JZSm7nr7MOt1ojAzvyyaO+UxZf18j8FCF6kmzCZKcAgN/yu2gm2XgQ==",
+      "license": "MIT",
+      "dependencies": {
+        "@types/unist": "^3.0.0"
+      },
+      "funding": {
+        "type": "opencollective",
+        "url": "https://opencollective.com/unified"
+      }
+    },
+    "node_modules/unist-util-visit": {
+      "version": "5.1.0",
+      "resolved": "https://registry.npmjs.org/unist-util-visit/-/unist-util-visit-5.1.0.tgz",
+      "integrity": "sha512-m+vIdyeCOpdr/QeQCu2EzxX/ohgS8KbnPDgFni4dQsfSCtpz8UqDyY5GjRru8PDKuYn7Fq19j1CQ+nJSsGKOzg==",
+      "license": "MIT",
+      "dependencies": {
+        "@types/unist": "^3.0.0",
+        "unist-util-is": "^6.0.0",
+        "unist-util-visit-parents": "^6.0.0"
+      },
+      "funding": {
+        "type": "opencollective",
+        "url": "https://opencollective.com/unified"
+      }
+    },
+    "node_modules/unist-util-visit-parents": {
+      "version": "6.0.2",
+      "resolved": "https://registry.npmjs.org/unist-util-visit-parents/-/unist-util-visit-parents-6.0.2.tgz",
+      "integrity": "sha512-goh1s1TBrqSqukSc8wrjwWhL0hiJxgA8m4kFxGlQ+8FYQ3C/m11FcTs4YYem7V664AhHVvgoQLk890Ssdsr2IQ==",
+      "license": "MIT",
+      "dependencies": {
+        "@types/unist": "^3.0.0",
+        "unist-util-is": "^6.0.0"
+      },
+      "funding": {
+        "type": "opencollective",
+        "url": "https://opencollective.com/unified"
+      }
+    },
     "node_modules/unrs-resolver": {
       "version": "1.11.1",
       "resolved": "https://registry.npmjs.org/unrs-resolver/-/unrs-resolver-1.11.1.tgz",
@@ -8657,6 +9811,34 @@
       "integrity": "sha512-EPD5q1uXyFxJpCrLnCc1nHnq3gOa6DZBocAIiI2TaSCA7VCJ1UJDMagCzIkXNsUYfD1daK//LTEQ8xiIbrHtcw==",
       "license": "MIT"
     },
+    "node_modules/vfile": {
+      "version": "6.0.3",
+      "resolved": "https://registry.npmjs.org/vfile/-/vfile-6.0.3.tgz",
+      "integrity": "sha512-KzIbH/9tXat2u30jf+smMwFCsno4wHVdNmzFyL+T/L3UGqqk6JKfVqOFOZEpZSHADH1k40ab6NUIXZq422ov3Q==",
+      "license": "MIT",
+      "dependencies": {
+        "@types/unist": "^3.0.0",
+        "vfile-message": "^4.0.0"
+      },
+      "funding": {
+        "type": "opencollective",
+        "url": "https://opencollective.com/unified"
+      }
+    },
+    "node_modules/vfile-message": {
+      "version": "4.0.3",
+      "resolved": "https://registry.npmjs.org/vfile-message/-/vfile-message-4.0.3.tgz",
+      "integrity": "sha512-QTHzsGd1EhbZs4AsQ20JX1rC3cOlt/IWJruk893DfLRr57lcnOeMaWG4K0JrRta4mIJZKth2Au3mM3u03/JWKw==",
+      "license": "MIT",
+      "dependencies": {
+        "@types/unist": "^3.0.0",
+        "unist-util-stringify-position": "^4.0.0"
+      },
+      "funding": {
+        "type": "opencollective",
+        "url": "https://opencollective.com/unified"
+      }
+    },
     "node_modules/victory-vendor": {
       "version": "36.9.2",
       "resolved": "https://registry.npmjs.org/victory-vendor/-/victory-vendor-36.9.2.tgz",
@@ -9394,6 +10576,16 @@
       "peerDependencies": {
         "zod": "^3.25.0 || ^4.0.0"
       }
+    },
+    "node_modules/zwitch": {
+      "version": "2.0.4",
+      "resolved": "https://registry.npmjs.org/zwitch/-/zwitch-2.0.4.tgz",
+      "integrity": "sha512-bXE4cR/kVZhKZX/RjPEflHaKVhUVl85noU3v6b8apfQEc1x4A+zBxjZ4lN8LqGd6WZ3dl98pY4o717VFmoPp+A==",
+      "license": "MIT",
+      "funding": {
+        "type": "github",
+        "url": "https://github.com/sponsors/wooorm"
+      }
     }
   }
 }
diff --git a/client/package.json b/client/package.json
index 2480cd6df..89d582ce0 100644
--- a/client/package.json
+++ b/client/package.json
@@ -26,7 +26,9 @@
     "react-chartjs-2": "^5.3.1",
     "react-dom": "19.2.0",
     "react-image-crop": "^11.0.10",
+    "react-markdown": "^10.1.0",
     "recharts": "^2.15.4",
+    "rehype-sanitize": "^6.0.0",
     "simple-peer": "^9.11.1",
     "socket.io-client": "^4.8.1",
     "sonner": "^1.7.3",
