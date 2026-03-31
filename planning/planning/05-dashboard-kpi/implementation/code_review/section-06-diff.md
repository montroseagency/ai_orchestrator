diff --git a/client/app/dashboard/agent/marketing/page.tsx b/client/app/dashboard/agent/marketing/page.tsx
index e97f6c62c..79b0b07b6 100644
--- a/client/app/dashboard/agent/marketing/page.tsx
+++ b/client/app/dashboard/agent/marketing/page.tsx
@@ -1,480 +1,87 @@
-'use client';
+'use client'
 
-import React, { useState, useEffect, useMemo } from 'react';
-import Link from 'next/link';
-import { useRouter } from 'next/navigation';
+import React from 'react'
+import { useCommandCenter } from '@/lib/hooks/useScheduling'
 import {
-  Plus,
-  Calendar,
-  Target,
-  Library,
-  BarChart3,
-  Users,
-  FileText,
-  CheckCircle2,
-  Circle,
-  Clock,
-  MessageSquare,
-  Sparkles,
-  ChevronRight,
-} from 'lucide-react';
-import { Surface } from '@/components/ui/Surface';
-import { SectionHeader } from '@/components/ui/SectionHeader';
-import { DataTable, Column } from '@/components/ui/DataTable';
-import { EmptyState } from '@/components/ui/empty-state';
-import { StatusBadge } from '@/components/ui/badge';
-import { Button } from '@/components/ui/button';
-import { ClientSelector } from '@/components/marketing/shared/ClientSelector';
-import { PlatformIcon } from '@/components/marketing/shared/PlatformIcon';
-import { useMarketingPosts } from '@/lib/hooks/marketing/useMarketingPosts';
-import ApiService from '@/lib/api';
-import type { MarketingPostListItem } from '@/lib/types/marketing';
-
-interface Task {
-  id: string;
-  label: string;
-  count?: number;
-  completed: boolean;
-  href: string;
-  priority: 'high' | 'medium' | 'low';
-}
-
-interface MarketingSubscription {
-  id: string;
-  tier: {
-    id: string;
-    name: string;
-    price_monthly: number;
-    posts_per_month: number;
-  };
-  status: string;
-  current_period_end?: string;
-}
-
-export default function AgentMarketingOverviewPage() {
-  const router = useRouter();
-  const [selectedClient, setSelectedClient] = useState<string>('');
-  const [socialAccounts, setSocialAccounts] = useState<any[]>([]);
-  const [accountsLoading, setAccountsLoading] = useState(false);
-  const [subscription, setSubscription] = useState<MarketingSubscription | null>(null);
-  const [subscriptionLoading, setSubscriptionLoading] = useState(false);
-
-  const { data: recentPosts, isLoading: postsLoading } = useMarketingPosts(
-    selectedClient
-      ? {
-          client: selectedClient,
-          ordering: '-created_at',
-          limit: 10,
-        }
-      : undefined
-  );
-
-  // Load social accounts and subscription when client changes
-  useEffect(() => {
-    const loadAccounts = async () => {
-      if (!selectedClient) {
-        setSocialAccounts([]);
-        return;
-      }
-      try {
-        setAccountsLoading(true);
-        const accounts = await ApiService.getSocialAccountsForClient(selectedClient);
-        setSocialAccounts(Array.isArray(accounts) ? accounts : []);
-      } catch (error) {
-        console.error('Failed to load accounts:', error);
-        setSocialAccounts([]);
-      } finally {
-        setAccountsLoading(false);
-      }
-    };
-    loadAccounts();
-  }, [selectedClient]);
-
-  // Load client's marketing subscription
-  useEffect(() => {
-    const loadSubscription = async () => {
-      if (!selectedClient) {
-        setSubscription(null);
-        return;
-      }
-      try {
-        setSubscriptionLoading(true);
-        const response = await ApiService.get(`/marketing-subscriptions/?client_id=${selectedClient}`);
-        const subs = Array.isArray(response) ? response : response.results || [];
-        // Find active or pending subscription
-        const activeSub = subs.find((s: any) => s.status === 'active' || s.status === 'pending');
-        setSubscription(activeSub || null);
-      } catch (error) {
-        console.error('Failed to load subscription:', error);
-        setSubscription(null);
-      } finally {
-        setSubscriptionLoading(false);
-      }
-    };
-    loadSubscription();
-  }, [selectedClient]);
-
-  // Filter posts by status
-  const pendingPosts = recentPosts?.filter(p => p.status === 'in_production' || p.status === 'in_review') || [];
-  const clientReviewPosts = recentPosts?.filter(p => p.status === 'client_review') || [];
-  const approvedPosts = recentPosts?.filter(p => p.status === 'approved' || p.status === 'scheduled') || [];
-  const needsRevisionPosts = recentPosts?.filter(p => p.status === 'needs_revision') || [];
-
-  // Generate dynamic tasks based on data
-  const tasks: Task[] = useMemo(() => {
-    const taskList: Task[] = [];
-
-    if (needsRevisionPosts.length > 0) {
-      taskList.push({
-        id: 'revisions',
-        label: `Address ${needsRevisionPosts.length} post revision${needsRevisionPosts.length > 1 ? 's' : ''}`,
-        count: needsRevisionPosts.length,
-        completed: false,
-        href: '/dashboard/agent/marketing/calendar?status=needs_revision',
-        priority: 'high',
-      });
-    }
-
-    if (pendingPosts.length > 0) {
-      taskList.push({
-        id: 'pending',
-        label: `Complete ${pendingPosts.length} post${pendingPosts.length > 1 ? 's' : ''} in production`,
-        count: pendingPosts.length,
-        completed: false,
-        href: '/dashboard/agent/marketing/calendar?status=in_production',
-        priority: 'medium',
-      });
-    }
-
-    if (clientReviewPosts.length > 0) {
-      taskList.push({
-        id: 'review',
-        label: `${clientReviewPosts.length} post${clientReviewPosts.length > 1 ? 's' : ''} awaiting client review`,
-        count: clientReviewPosts.length,
-        completed: false,
-        href: '/dashboard/agent/marketing/calendar?status=client_review',
-        priority: 'low',
-      });
-    }
-
-    if (approvedPosts.length > 0) {
-      taskList.push({
-        id: 'approved',
-        label: `${approvedPosts.length} post${approvedPosts.length > 1 ? 's' : ''} ready to schedule`,
-        count: approvedPosts.length,
-        completed: true,
-        href: '/dashboard/agent/marketing/calendar?status=approved',
-        priority: 'low',
-      });
-    }
-
-    return taskList;
-  }, [pendingPosts, clientReviewPosts, approvedPosts, needsRevisionPosts]);
-
-  const columns: Column<MarketingPostListItem>[] = [
-    {
-      key: 'topic',
-      header: 'Post',
-      render: (row) => (
-        <div className="flex items-center gap-3">
-          {row.media_urls?.[0] ? (
-            <img src={row.media_urls[0]} alt="" className="w-10 h-10 rounded-surface object-cover" />
-          ) : (
-            <div className="w-10 h-10 rounded-surface bg-surface-muted flex items-center justify-center">
-              <FileText className="w-4 h-4 text-muted" />
-            </div>
-          )}
-          <div>
-            <p className="font-medium text-primary truncate max-w-[180px]">{row.topic || 'Untitled'}</p>
-            <p className="text-xs text-muted">{row.pillar_name}</p>
-          </div>
+  CurrentTaskKpi,
+  DashboardStatsRow,
+  DashboardTaskList,
+  ReadOnlySchedule,
+} from '@/components/agent/dashboard'
+import { Skeleton } from '@/components/ui/skeleton'
+
+export default function AgentDashboardPage() {
+  const agentType = 'marketing'
+  const todayStr = new Date().toISOString().slice(0, 10)
+  const { data, isLoading, isError, isFetching, refetch } = useCommandCenter()
+
+  if (isLoading) {
+    return (
+      <div className="space-y-6" data-testid="dashboard-skeleton">
+        {/* KPI skeleton */}
+        <Skeleton className="h-40 w-full rounded-2xl" />
+        {/* Stats row skeleton */}
+        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
+          <Skeleton className="h-20 rounded-xl" />
+          <Skeleton className="h-20 rounded-xl" />
+          <Skeleton className="h-20 rounded-xl" />
+          <Skeleton className="h-20 rounded-xl" />
         </div>
-      ),
-    },
-    {
-      key: 'platform',
-      header: 'Platform',
-      width: '100px',
-      render: (row) => (
-        <div className="flex items-center gap-2">
-          <PlatformIcon platform={row.platform.name} size={16} />
-          <span className="text-sm">{row.platform.name}</span>
+        {/* Two-column skeleton */}
+        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
+          <Skeleton className="h-64 rounded-xl lg:col-span-2" />
+          <Skeleton className="h-64 rounded-xl lg:col-span-3" />
         </div>
-      ),
-    },
-    {
-      key: 'date',
-      header: 'Date',
-      width: '100px',
-      render: (row) => (
-        <span className="text-sm">
-          {new Date(row.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
-        </span>
-      ),
-    },
-    {
-      key: 'status',
-      header: 'Status',
-      width: '120px',
-      render: (row) => <StatusBadge status={row.status} />,
-    },
-  ];
-
-  // Quick access items
-  const quickAccessItems = [
-    { label: 'Calendar', icon: Calendar, href: '/dashboard/agent/marketing/calendar' },
-    { label: 'Library', icon: Library, href: '/dashboard/agent/marketing/library' },
-    { label: 'Strategy', icon: Target, href: '/dashboard/agent/marketing/plan' },
-    { label: 'AI Ideas', icon: Sparkles, href: '/dashboard/agent/marketing/ideas' },
-    { label: 'Analytics', icon: BarChart3, href: '/dashboard/agent/marketing/analytics' },
-  ];
+      </div>
+    )
+  }
+
+  if (isError) {
+    return (
+      <div
+        className="flex flex-col items-center justify-center py-16 gap-4"
+        data-testid="dashboard-error"
+      >
+        <p className="text-secondary text-sm">Failed to load dashboard data.</p>
+        <button
+          onClick={() => refetch()}
+          className="px-4 py-2 rounded-lg bg-accent text-white text-sm font-medium hover:bg-accent/90 transition-colors"
+        >
+          Retry
+        </button>
+      </div>
+    )
+  }
 
   return (
     <div className="space-y-6">
-      {/* Page Header with Client Selector */}
-      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
-        <div>
-          <h1 className="text-page-title text-primary">Marketing Overview</h1>
-          <p className="text-secondary mt-1">Manage your clients' social media marketing</p>
-        </div>
-        <div className="flex items-center gap-3">
-          <div className="w-64">
-            <ClientSelector
-              value={selectedClient}
-              onChange={setSelectedClient}
-              placeholder="Select client..."
-            />
-          </div>
-          {selectedClient && (
-            <Button
-              size="sm"
-              onClick={() => router.push('/dashboard/agent/marketing/calendar')}
-            >
-              <Plus className="w-4 h-4 mr-2" />
-              Create Post
-            </Button>
-          )}
-        </div>
-      </div>
-
-      {selectedClient ? (
-        <>
-          {/* Two Column Layout: Tasks + Overview */}
-          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
-            {/* Today's Tasks - Hero Section */}
-            <div className="lg:col-span-2">
-              <Surface variant="outlined" padding="none">
-                <div className="p-4 border-b border-border">
-                  <SectionHeader
-                    title="Today's Tasks"
-                    description="Action items for this client"
-                  />
-                </div>
-                <div className="p-4">
-                  {postsLoading ? (
-                    <div className="py-8 flex items-center justify-center">
-                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent"></div>
-                    </div>
-                  ) : tasks.length > 0 ? (
-                    <div className="space-y-2">
-                      {tasks.map((task) => (
-                        <Link
-                          key={task.id}
-                          href={task.href}
-                          className={`flex items-center gap-3 p-3 rounded-lg border transition-colors ${
-                            task.completed
-                              ? 'border-border bg-surface-subtle'
-                              : task.priority === 'high'
-                              ? 'border-red-200 bg-red-50 hover:bg-red-100'
-                              : 'border-border hover:bg-surface-subtle'
-                          }`}
-                        >
-                          {task.completed ? (
-                            <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0" />
-                          ) : task.priority === 'high' ? (
-                            <Circle className="w-5 h-5 text-red-500 flex-shrink-0" />
-                          ) : (
-                            <Circle className="w-5 h-5 text-muted flex-shrink-0" />
-                          )}
-                          <span className={`flex-1 text-sm ${task.completed ? 'text-muted line-through' : 'text-primary'}`}>
-                            {task.label}
-                          </span>
-                          <ChevronRight className="w-4 h-4 text-muted" />
-                        </Link>
-                      ))}
-                    </div>
-                  ) : (
-                    <div className="py-8 text-center">
-                      <CheckCircle2 className="w-10 h-10 text-green-600 mx-auto mb-3" />
-                      <p className="text-sm font-medium text-primary">All caught up!</p>
-                      <p className="text-xs text-muted mt-1">No pending tasks for this client</p>
-                    </div>
-                  )}
-                </div>
-              </Surface>
-            </div>
-
-            {/* Client Overview - Right Panel */}
-            <div className="space-y-4">
-              {/* Marketing Plan/Subscription Info */}
-              <Surface variant="outlined" padding="md">
-                <h3 className="text-sm font-medium text-primary mb-3">Marketing Plan</h3>
-                {subscriptionLoading ? (
-                  <div className="py-2">
-                    <div className="animate-pulse h-4 bg-surface-muted rounded w-24"></div>
-                  </div>
-                ) : subscription ? (
-                  <div className="space-y-3">
-                    <div className="flex items-center justify-between">
-                      <span className="text-lg font-semibold text-primary">{subscription.tier?.name || 'Unknown Plan'}</span>
-                      <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${
-                        subscription.status === 'active'
-                          ? 'bg-green-100 text-green-700'
-                          : subscription.status === 'pending'
-                          ? 'bg-yellow-100 text-yellow-700'
-                          : 'bg-gray-100 text-gray-700'
-                      }`}>
-                        {subscription.status}
-                      </span>
-                    </div>
-                    <div className="flex items-center justify-between text-sm">
-                      <span className="text-secondary">Posts/month</span>
-                      <span className="font-medium text-primary">{subscription.tier?.posts_per_month || 'Unlimited'}</span>
-                    </div>
-                    <div className="flex items-center justify-between text-sm">
-                      <span className="text-secondary">Price</span>
-                      <span className="font-medium text-primary">${subscription.tier?.price_monthly || 0}/mo</span>
-                    </div>
-                    {subscription.current_period_end && (
-                      <div className="flex items-center justify-between text-sm">
-                        <span className="text-secondary">Renews</span>
-                        <span className="font-medium text-primary">
-                          {new Date(subscription.current_period_end).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
-                        </span>
-                      </div>
-                    )}
-                  </div>
-                ) : (
-                  <div className="text-center py-3">
-                    <p className="text-sm text-muted">No active marketing plan</p>
-                    <p className="text-xs text-muted mt-1">Client hasn't subscribed yet</p>
-                  </div>
-                )}
-              </Surface>
-
-              {/* Stats Overview */}
-              <Surface variant="outlined" padding="md">
-                <h3 className="text-sm font-medium text-primary mb-4">Stats Overview</h3>
-                <div className="space-y-4">
-                  <div className="flex items-center justify-between">
-                    <span className="text-sm text-secondary">Connected Accounts</span>
-                    <span className="text-sm font-semibold text-primary">
-                      {accountsLoading ? '...' : socialAccounts.length}
-                    </span>
-                  </div>
-                  <div className="flex items-center justify-between">
-                    <span className="text-sm text-secondary">Posts This Month</span>
-                    <span className="text-sm font-semibold text-primary">
-                      {recentPosts?.length || 0}
-                    </span>
-                  </div>
-                  <div className="flex items-center justify-between">
-                    <span className="text-sm text-secondary">Awaiting Review</span>
-                    <span className="text-sm font-semibold text-warning">
-                      {clientReviewPosts.length}
-                    </span>
-                  </div>
-                  <div className="flex items-center justify-between">
-                    <span className="text-sm text-secondary">Approved</span>
-                    <span className="text-sm font-semibold text-green-600">
-                      {approvedPosts.length}
-                    </span>
-                  </div>
-                </div>
-
-                {/* Connected accounts list */}
-                {socialAccounts.length > 0 && (
-                  <div className="mt-4 pt-4 border-t border-border">
-                    <p className="text-xs text-muted mb-2">Connected Platforms</p>
-                    <div className="flex flex-wrap gap-2">
-                      {socialAccounts.map((account) => (
-                        <div
-                          key={account.id}
-                          className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-surface-subtle text-xs"
-                        >
-                          <PlatformIcon platform={account.platform} size={12} />
-                          <span className="text-primary">@{account.username}</span>
-                        </div>
-                      ))}
-                    </div>
-                  </div>
-                )}
-              </Surface>
-            </div>
-          </div>
+      {isFetching && (
+        <div
+          className="animate-pulse bg-accent/30 h-0.5 w-full rounded"
+          aria-hidden="true"
+        />
+      )}
 
-          {/* Quick Access - Compact Button Navigation */}
-          <div className="flex flex-wrap gap-2">
-            {quickAccessItems.map((item) => (
-              <Link
-                key={item.label}
-                href={item.href}
-                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-border bg-surface hover:bg-surface-subtle transition-colors text-sm font-medium text-primary"
-              >
-                <item.icon className="w-4 h-4 text-muted" />
-                {item.label}
-              </Link>
-            ))}
-          </div>
+      <CurrentTaskKpi timeBlocks={data!.time_blocks} agentType={agentType} />
 
-          {/* Recent Posts DataTable */}
-          <Surface variant="outlined" padding="none">
-            <div className="p-4 border-b border-border">
-              <SectionHeader
-                title="Recent Posts"
-                description={`${recentPosts?.length || 0} posts`}
-                action={{
-                  label: 'View All',
-                  onClick: () => router.push('/dashboard/agent/marketing/calendar'),
-                  variant: 'secondary',
-                }}
-              />
-            </div>
+      <DashboardStatsRow stats={data!.stats} />
 
-            {postsLoading ? (
-              <div className="p-8 flex items-center justify-center">
-                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent"></div>
-              </div>
-            ) : recentPosts && recentPosts.length > 0 ? (
-              <DataTable
-                columns={columns}
-                data={recentPosts.slice(0, 5)}
-                onRowClick={(row) => router.push(`/dashboard/agent/marketing/posts/${row.id}`)}
-                getRowKey={(row) => row.id}
-              />
-            ) : (
-              <EmptyState
-                icon={FileText}
-                title="No posts yet"
-                description="Create your first post for this client"
-                action={{
-                  label: 'Create Post',
-                  onClick: () => router.push('/dashboard/agent/marketing/calendar'),
-                }}
-                size="sm"
-              />
-            )}
-          </Surface>
-        </>
-      ) : (
-        <Surface variant="outlined" padding="none">
-          <EmptyState
-            icon={Users}
-            title="Select a Client"
-            description="Choose a client above to view their marketing dashboard, create posts, and manage their content strategy."
+      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
+        <div className="lg:col-span-2">
+          <DashboardTaskList
+            globalTasks={data!.todays_global_tasks}
+            clientTasks={data!.todays_client_tasks}
+            agentType={agentType}
           />
-        </Surface>
-      )}
+        </div>
+        <div className="lg:col-span-3">
+          <ReadOnlySchedule
+            timeBlocks={data!.time_blocks}
+            date={todayStr}
+            agentType={agentType}
+          />
+        </div>
+      </div>
     </div>
-  );
+  )
 }
diff --git a/client/components/agent/dashboard/__tests__/AgentDashboardPage.test.tsx b/client/components/agent/dashboard/__tests__/AgentDashboardPage.test.tsx
new file mode 100644
index 000000000..e468d9d4b
--- /dev/null
+++ b/client/components/agent/dashboard/__tests__/AgentDashboardPage.test.tsx
@@ -0,0 +1,172 @@
+import React from 'react'
+import { describe, it, expect, vi, beforeEach } from 'vitest'
+import { screen } from '@testing-library/react'
+import userEvent from '@testing-library/user-event'
+import { renderWithQuery, makeMockCommandCenterData } from '@/test-utils/scheduling'
+import AgentDashboardPage from '@/app/dashboard/agent/marketing/page'
+
+// Mock child components so tests focus on page-level orchestration
+vi.mock('@/components/agent/dashboard', () => ({
+  CurrentTaskKpi: () => <div data-testid="current-task-kpi" />,
+  DashboardStatsRow: () => <div data-testid="dashboard-stats-row" />,
+  DashboardTaskList: () => <div data-testid="dashboard-task-list" />,
+  ReadOnlySchedule: () => <div data-testid="readonly-schedule" />,
+}))
+
+vi.mock('@/lib/hooks/useScheduling', () => ({
+  useCommandCenter: vi.fn(),
+  useUpdateGlobalTask: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
+  SCHEDULE_KEYS: { commandCenter: () => ['command-center'] },
+}))
+
+import { useCommandCenter } from '@/lib/hooks/useScheduling'
+const mockUseCommandCenter = vi.mocked(useCommandCenter)
+
+function makeLoadedReturn(overrides: Record<string, unknown> = {}) {
+  return {
+    isLoading: false,
+    isError: false,
+    isFetching: false,
+    data: makeMockCommandCenterData(),
+    refetch: vi.fn(),
+    ...overrides,
+  }
+}
+
+// ---------------------------------------------------------------------------
+// Loading state
+// ---------------------------------------------------------------------------
+describe('AgentDashboardPage — loading state', () => {
+  beforeEach(() => {
+    mockUseCommandCenter.mockReturnValue({
+      isLoading: true,
+      isError: false,
+      isFetching: false,
+      data: undefined,
+      refetch: vi.fn(),
+    } as any)
+  })
+
+  it('renders a skeleton when isLoading is true', () => {
+    renderWithQuery(<AgentDashboardPage />)
+    expect(screen.getByTestId('dashboard-skeleton')).toBeInTheDocument()
+  })
+
+  it('does not render child components while loading', () => {
+    renderWithQuery(<AgentDashboardPage />)
+    expect(screen.queryByTestId('current-task-kpi')).not.toBeInTheDocument()
+    expect(screen.queryByTestId('dashboard-stats-row')).not.toBeInTheDocument()
+    expect(screen.queryByTestId('dashboard-task-list')).not.toBeInTheDocument()
+    expect(screen.queryByTestId('readonly-schedule')).not.toBeInTheDocument()
+  })
+})
+
+// ---------------------------------------------------------------------------
+// Error state
+// ---------------------------------------------------------------------------
+describe('AgentDashboardPage — error state', () => {
+  beforeEach(() => {
+    mockUseCommandCenter.mockReturnValue({
+      isLoading: false,
+      isError: true,
+      isFetching: false,
+      data: undefined,
+      refetch: vi.fn(),
+    } as any)
+  })
+
+  it('renders an error state with a retry button when isError is true', () => {
+    renderWithQuery(<AgentDashboardPage />)
+    expect(screen.getByTestId('dashboard-error')).toBeInTheDocument()
+    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
+  })
+
+  it('does not render child components in error state', () => {
+    renderWithQuery(<AgentDashboardPage />)
+    expect(screen.queryByTestId('current-task-kpi')).not.toBeInTheDocument()
+    expect(screen.queryByTestId('dashboard-stats-row')).not.toBeInTheDocument()
+    expect(screen.queryByTestId('dashboard-task-list')).not.toBeInTheDocument()
+    expect(screen.queryByTestId('readonly-schedule')).not.toBeInTheDocument()
+  })
+
+  it('calls refetch when retry button is clicked', async () => {
+    const refetch = vi.fn()
+    mockUseCommandCenter.mockReturnValue({
+      isLoading: false,
+      isError: true,
+      isFetching: false,
+      data: undefined,
+      refetch,
+    } as any)
+    const user = userEvent.setup()
+    renderWithQuery(<AgentDashboardPage />)
+    await user.click(screen.getByRole('button', { name: /retry/i }))
+    expect(refetch).toHaveBeenCalledOnce()
+  })
+})
+
+// ---------------------------------------------------------------------------
+// Loaded state
+// ---------------------------------------------------------------------------
+describe('AgentDashboardPage — loaded state', () => {
+  beforeEach(() => {
+    mockUseCommandCenter.mockReturnValue(makeLoadedReturn() as any)
+  })
+
+  it('renders CurrentTaskKpi section when data is loaded', () => {
+    renderWithQuery(<AgentDashboardPage />)
+    expect(screen.getByTestId('current-task-kpi')).toBeInTheDocument()
+  })
+
+  it('renders DashboardStatsRow section when data is loaded', () => {
+    renderWithQuery(<AgentDashboardPage />)
+    expect(screen.getByTestId('dashboard-stats-row')).toBeInTheDocument()
+  })
+
+  it('renders DashboardTaskList section when data is loaded', () => {
+    renderWithQuery(<AgentDashboardPage />)
+    expect(screen.getByTestId('dashboard-task-list')).toBeInTheDocument()
+  })
+
+  it('renders ReadOnlySchedule section when data is loaded', () => {
+    renderWithQuery(<AgentDashboardPage />)
+    expect(screen.getByTestId('readonly-schedule')).toBeInTheDocument()
+  })
+})
+
+// ---------------------------------------------------------------------------
+// Layout ordering
+// ---------------------------------------------------------------------------
+describe('AgentDashboardPage — layout ordering', () => {
+  beforeEach(() => {
+    mockUseCommandCenter.mockReturnValue(makeLoadedReturn() as any)
+  })
+
+  it('CurrentTaskKpi is the first major section in document order', () => {
+    renderWithQuery(<AgentDashboardPage />)
+    const kpi = screen.getByTestId('current-task-kpi')
+    const stats = screen.getByTestId('dashboard-stats-row')
+    // DOCUMENT_POSITION_FOLLOWING means stats appears after kpi in the DOM
+    expect(
+      kpi.compareDocumentPosition(stats) & Node.DOCUMENT_POSITION_FOLLOWING,
+    ).toBeTruthy()
+  })
+})
+
+// ---------------------------------------------------------------------------
+// Mobile layout
+// ---------------------------------------------------------------------------
+describe('AgentDashboardPage — mobile layout', () => {
+  beforeEach(() => {
+    mockUseCommandCenter.mockReturnValue(makeLoadedReturn() as any)
+  })
+
+  it('all sections are present in the DOM on a narrow viewport', () => {
+    renderWithQuery(<AgentDashboardPage />)
+    // Layout is CSS-only — all four sections are always rendered
+    expect(screen.getByTestId('current-task-kpi')).toBeInTheDocument()
+    expect(screen.getByTestId('dashboard-stats-row')).toBeInTheDocument()
+    expect(screen.getByTestId('dashboard-task-list')).toBeInTheDocument()
+    expect(screen.getByTestId('readonly-schedule')).toBeInTheDocument()
+  })
+})
diff --git a/client/components/agent/dashboard/index.ts b/client/components/agent/dashboard/index.ts
new file mode 100644
index 000000000..27cf1e509
--- /dev/null
+++ b/client/components/agent/dashboard/index.ts
@@ -0,0 +1,4 @@
+export { CurrentTaskKpi } from './CurrentTaskKpi'
+export { DashboardStatsRow } from './DashboardStatsRow'
+export { DashboardTaskList } from './DashboardTaskList'
+export { ReadOnlySchedule } from './ReadOnlySchedule'
