diff --git a/client/app/dashboard/admin/approvals/__tests__/ApprovalsPage.test.tsx b/client/app/dashboard/admin/approvals/__tests__/ApprovalsPage.test.tsx
new file mode 100644
index 000000000..6c91d3f10
--- /dev/null
+++ b/client/app/dashboard/admin/approvals/__tests__/ApprovalsPage.test.tsx
@@ -0,0 +1,188 @@
+import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
+import { describe, it, expect, vi, beforeEach } from 'vitest'
+import React from 'react'
+import { renderWithQuery } from '@/test-utils/scheduling'
+
+// ── Local factory stub ────────────────────────────────────────────────────
+
+function createMockApprovalTask(overrides?: Partial<Record<string, unknown>>) {
+  return {
+    id: 'task-1',
+    title: 'Test Task',
+    description: 'Task description',
+    status: 'in_review',
+    review_feedback: '',
+    agent: { id: 'agent-1', name: 'Agent Smith' },
+    client: { id: 'client-1', name: 'Nike', company: 'Nike Inc.' },
+    task_category_detail: { name: 'Copywriting', color: '#6366F1' },
+    updated_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
+    ...overrides,
+  }
+}
+
+// ── Mocks ─────────────────────────────────────────────────────────────────
+
+const mockRequest = vi.fn()
+const mockPost = vi.fn()
+
+vi.mock('@/lib/api', () => ({
+  default: { request: mockRequest, post: mockPost },
+}))
+
+vi.mock('@/lib/socket-context', () => ({
+  useSocket: () => ({ on: vi.fn(), off: vi.fn(), socket: null, isConnected: false }),
+}))
+
+vi.mock('sonner', () => ({
+  toast: { success: vi.fn(), error: vi.fn() },
+}))
+
+// ── Tests ─────────────────────────────────────────────────────────────────
+
+async function getPage() {
+  const mod = await import('@/app/dashboard/admin/approvals/page')
+  return mod.default
+}
+
+describe('ApprovalsPage', () => {
+  beforeEach(() => {
+    vi.clearAllMocks()
+    mockRequest.mockResolvedValue([createMockApprovalTask()])
+    mockPost.mockResolvedValue({})
+  })
+
+  it('fetches and renders table of in_review tasks on mount', async () => {
+    const ApprovalsPage = await getPage()
+    renderWithQuery(<ApprovalsPage />)
+    await waitFor(() => {
+      expect(screen.getByText('Agent Smith')).toBeInTheDocument()
+    })
+  })
+
+  it('table shows Agent, Task, Client, Submitted columns', async () => {
+    const ApprovalsPage = await getPage()
+    renderWithQuery(<ApprovalsPage />)
+    await waitFor(() => {
+      expect(screen.getByText('Agent')).toBeInTheDocument()
+    })
+    expect(screen.getByText('Task')).toBeInTheDocument()
+    expect(screen.getByText('Client')).toBeInTheDocument()
+    expect(screen.getByText('Submitted')).toBeInTheDocument()
+  })
+
+  it('clicking a row opens the review Drawer', async () => {
+    const ApprovalsPage = await getPage()
+    renderWithQuery(<ApprovalsPage />)
+    await waitFor(() => screen.getByText('Agent Smith'))
+    // Find and click the view button to open drawer
+    const viewBtn = screen.getAllByRole('button').find(b => b.getAttribute('aria-label') === 'Review task')
+    if (viewBtn) fireEvent.click(viewBtn)
+    else fireEvent.click(screen.getByText('Agent Smith'))
+    await waitFor(() => {
+      expect(screen.getByText('Test Task')).toBeInTheDocument()
+    })
+  })
+
+  it('Drawer shows task title, agent, client, description', async () => {
+    const ApprovalsPage = await getPage()
+    renderWithQuery(<ApprovalsPage />)
+    await waitFor(() => screen.getByText('Agent Smith'))
+    fireEvent.click(screen.getByText('Agent Smith'))
+    await waitFor(() => {
+      expect(screen.getAllByText('Test Task').length).toBeGreaterThan(0)
+      expect(screen.getAllByText('Agent Smith').length).toBeGreaterThan(0)
+      expect(screen.getByText('Nike Inc.')).toBeInTheDocument()
+      expect(screen.getByText('Task description')).toBeInTheDocument()
+    })
+  })
+
+  it('"Approve" button calls approve endpoint and removes row from table on success', async () => {
+    const { toast } = await import('sonner')
+    const ApprovalsPage = await getPage()
+    renderWithQuery(<ApprovalsPage />)
+    await waitFor(() => screen.getByText('Agent Smith'))
+    fireEvent.click(screen.getByText('Agent Smith'))
+    await waitFor(() => screen.getByRole('button', { name: /approve/i }))
+    fireEvent.click(screen.getByRole('button', { name: /approve/i }))
+    await waitFor(() => {
+      expect(mockPost).toHaveBeenCalledWith(
+        expect.stringContaining('/admin/approvals/task-1/approve/'),
+        expect.anything()
+      )
+    })
+    await waitFor(() => {
+      expect(toast.success).toHaveBeenCalled()
+      expect(screen.queryByText('Agent Smith')).not.toBeInTheDocument()
+    })
+  })
+
+  it('"Reject" button is disabled when feedback textarea is empty', async () => {
+    const ApprovalsPage = await getPage()
+    renderWithQuery(<ApprovalsPage />)
+    await waitFor(() => screen.getByText('Agent Smith'))
+    fireEvent.click(screen.getByText('Agent Smith'))
+    await waitFor(() => screen.getByRole('button', { name: /reject/i }))
+    const rejectBtn = screen.getByRole('button', { name: /reject/i })
+    expect(rejectBtn).toBeDisabled()
+  })
+
+  it('"Reject" button calls reject endpoint with feedback and removes row on success', async () => {
+    const { toast } = await import('sonner')
+    const ApprovalsPage = await getPage()
+    renderWithQuery(<ApprovalsPage />)
+    await waitFor(() => screen.getByText('Agent Smith'))
+    fireEvent.click(screen.getByText('Agent Smith'))
+    await waitFor(() => screen.getByRole('textbox'))
+    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'Needs improvement' } })
+    await waitFor(() => {
+      const rejectBtn = screen.getByRole('button', { name: /reject/i })
+      expect(rejectBtn).not.toBeDisabled()
+    })
+    fireEvent.click(screen.getByRole('button', { name: /reject/i }))
+    await waitFor(() => {
+      expect(mockPost).toHaveBeenCalledWith(
+        expect.stringContaining('/admin/approvals/task-1/reject/'),
+        expect.objectContaining({ feedback: 'Needs improvement' })
+      )
+      expect(toast.success).toHaveBeenCalled()
+    })
+  })
+
+  it('shows error toast on approve/reject API failure', async () => {
+    mockPost.mockRejectedValueOnce(new Error('Server error'))
+    const { toast } = await import('sonner')
+    const ApprovalsPage = await getPage()
+    renderWithQuery(<ApprovalsPage />)
+    await waitFor(() => screen.getByText('Agent Smith'))
+    fireEvent.click(screen.getByText('Agent Smith'))
+    await waitFor(() => screen.getByRole('button', { name: /approve/i }))
+    fireEvent.click(screen.getByRole('button', { name: /approve/i }))
+    await waitFor(() => {
+      expect(toast.error).toHaveBeenCalled()
+      // Row should still be visible
+      expect(screen.getByText('Agent Smith')).toBeInTheDocument()
+    })
+  })
+
+  it('shows empty state when no pending approvals exist', async () => {
+    mockRequest.mockResolvedValue([])
+    const ApprovalsPage = await getPage()
+    renderWithQuery(<ApprovalsPage />)
+    await waitFor(() => {
+      expect(screen.getByText('No pending approvals')).toBeInTheDocument()
+    })
+  })
+
+  it('nav badge shows count of pending approvals', async () => {
+    mockRequest.mockResolvedValue([
+      createMockApprovalTask({ id: 'task-1' }),
+      createMockApprovalTask({ id: 'task-2' }),
+      createMockApprovalTask({ id: 'task-3' }),
+    ])
+    const ApprovalsPage = await getPage()
+    renderWithQuery(<ApprovalsPage />)
+    await waitFor(() => {
+      expect(screen.getByText('3')).toBeInTheDocument()
+    })
+  })
+})
diff --git a/client/app/dashboard/admin/approvals/page.tsx b/client/app/dashboard/admin/approvals/page.tsx
new file mode 100644
index 000000000..54b4bae43
--- /dev/null
+++ b/client/app/dashboard/admin/approvals/page.tsx
@@ -0,0 +1,297 @@
+'use client';
+
+import React, { useState, useEffect, useCallback } from 'react';
+import { formatDistanceToNow } from 'date-fns';
+import { Eye, CheckCircle2 } from 'lucide-react';
+import { toast } from 'sonner';
+import { DataTable, Column } from '@/components/ui/DataTable';
+import { Drawer } from '@/components/ui/drawer';
+import { Button } from '@/components/ui/button';
+import { Textarea } from '@/components/ui/textarea';
+import { Badge } from '@/components/ui/badge';
+import InlineError from '@/components/ui/InlineError';
+import api from '@/lib/api';
+import { useSocket } from '@/lib/socket-context';
+
+// ── Types ─────────────────────────────────────────────────────────────────
+
+interface ApprovalAgent {
+  id: string;
+  name: string;
+}
+
+interface ApprovalClient {
+  id: string;
+  name: string;
+  company: string;
+}
+
+type ApprovalTask = {
+  id: string;
+  title: string;
+  description: string;
+  status: string;
+  review_feedback: string;
+  agent: ApprovalAgent;
+  client: ApprovalClient;
+  task_category_detail: { name: string; color: string } | null;
+  updated_at: string;
+} & Record<string, unknown>;
+
+// ── Page ──────────────────────────────────────────────────────────────────
+
+export default function AdminApprovalsPage() {
+  const [tasks, setTasks] = useState<ApprovalTask[]>([]);
+  const [isLoading, setIsLoading] = useState(true);
+  const [fetchError, setFetchError] = useState('');
+  const [selectedTask, setSelectedTask] = useState<ApprovalTask | null>(null);
+  const [drawerOpen, setDrawerOpen] = useState(false);
+  const [feedback, setFeedback] = useState('');
+  const [isSubmitting, setIsSubmitting] = useState(false);
+  const [feedbackError, setFeedbackError] = useState('');
+
+  const { on, off } = useSocket();
+
+  const fetchApprovals = useCallback(async () => {
+    try {
+      const data = await api.request<ApprovalTask[]>('/admin/approvals/');
+      setTasks(data);
+      setFetchError('');
+    } catch {
+      setFetchError('Failed to load approvals. Please refresh.');
+    } finally {
+      setIsLoading(false);
+    }
+  }, []);
+
+  // Initial fetch
+  useEffect(() => {
+    fetchApprovals();
+  }, [fetchApprovals]);
+
+  // 60-second polling
+  useEffect(() => {
+    const interval = setInterval(fetchApprovals, 60_000);
+    return () => clearInterval(interval);
+  }, [fetchApprovals]);
+
+  // Socket.IO real-time refresh
+  useEffect(() => {
+    const handler = () => { fetchApprovals(); };
+    on('task_review_submitted', handler);
+    return () => { off('task_review_submitted', handler); };
+  }, [on, off, fetchApprovals]);
+
+  function openDrawer(task: ApprovalTask) {
+    setSelectedTask(task);
+    setFeedback('');
+    setFeedbackError('');
+    setDrawerOpen(true);
+  }
+
+  function closeDrawer() {
+    setDrawerOpen(false);
+    setSelectedTask(null);
+  }
+
+  function removeTask(taskId: string) {
+    setTasks(prev => prev.filter(t => t.id !== taskId));
+  }
+
+  async function handleApprove() {
+    if (!selectedTask) return;
+    setIsSubmitting(true);
+    try {
+      await api.post(`/admin/approvals/${selectedTask.id}/approve/`, {});
+      toast.success('Task approved');
+      removeTask(selectedTask.id);
+      closeDrawer();
+    } catch (err: unknown) {
+      const status = (err as { status?: number })?.status;
+      if (status === 409) {
+        toast.error('This task has already been reviewed.');
+        removeTask(selectedTask.id);
+        closeDrawer();
+      } else {
+        toast.error('Failed to approve task');
+      }
+    } finally {
+      setIsSubmitting(false);
+    }
+  }
+
+  async function handleReject() {
+    if (!selectedTask) return;
+    if (!feedback.trim()) {
+      setFeedbackError('Feedback is required to reject a task.');
+      return;
+    }
+    setIsSubmitting(true);
+    try {
+      await api.post(`/admin/approvals/${selectedTask.id}/reject/`, { feedback });
+      toast.success('Task returned to agent');
+      removeTask(selectedTask.id);
+      closeDrawer();
+    } catch (err: unknown) {
+      const status = (err as { status?: number })?.status;
+      if (status === 409) {
+        toast.error('This task has already been reviewed.');
+        removeTask(selectedTask.id);
+        closeDrawer();
+      } else {
+        toast.error('Failed to reject task');
+      }
+    } finally {
+      setIsSubmitting(false);
+    }
+  }
+
+  const columns: Column<ApprovalTask>[] = [
+    {
+      key: 'agent',
+      header: 'Agent',
+      render: (row) => (
+        <div className="flex items-center gap-2">
+          <span className="w-7 h-7 rounded-full bg-accent text-white text-xs flex items-center justify-center font-medium shrink-0">
+            {row.agent.name.charAt(0).toUpperCase()}
+          </span>
+          <span className="text-sm text-primary">{row.agent.name}</span>
+        </div>
+      ),
+    },
+    {
+      key: 'title',
+      header: 'Task',
+      render: (row) => <span className="font-medium text-sm">{row.title}</span>,
+    },
+    {
+      key: 'client',
+      header: 'Client',
+      render: (row) => <span className="text-sm text-secondary">{row.client.company}</span>,
+    },
+    {
+      key: 'updated_at',
+      header: 'Submitted',
+      render: (row) => (
+        <span className="text-sm text-secondary">
+          {formatDistanceToNow(new Date(row.updated_at), { addSuffix: true })}
+        </span>
+      ),
+    },
+    {
+      key: 'actions',
+      header: '',
+      render: (row) => (
+        <Button
+          variant="ghost"
+          onClick={(e) => { e.stopPropagation(); openDrawer(row); }}
+          aria-label="Review task"
+          className="p-1"
+        >
+          <Eye className="w-4 h-4" />
+        </Button>
+      ),
+    },
+  ];
+
+  return (
+    <div className="flex flex-col gap-6 p-6">
+      {/* Header with pending badge */}
+      <div className="flex items-center gap-3">
+        <h1 className="text-xl font-semibold text-primary">Approvals</h1>
+        {tasks.length > 0 && (
+          <Badge variant="warning" className="text-xs font-semibold">
+            {tasks.length}
+          </Badge>
+        )}
+      </div>
+
+      {fetchError && <InlineError message={fetchError} />}
+
+      <DataTable<ApprovalTask>
+        columns={columns}
+        data={tasks}
+        isLoading={isLoading}
+        onRowClick={(row) => openDrawer(row)}
+        getRowKey={(row) => row.id}
+        emptyState={{
+          title: 'No pending approvals',
+          description: 'All tasks have been reviewed.',
+          icon: CheckCircle2,
+        }}
+      />
+
+      {/* Review Drawer */}
+      <Drawer isOpen={drawerOpen} onClose={closeDrawer} side="right" size="lg">
+        {selectedTask && (
+          <div className="flex flex-col gap-4 p-6 h-full overflow-y-auto">
+            {/* Header */}
+            <div>
+              <h2 className="text-base font-semibold text-primary">
+                Review: {selectedTask.title}
+              </h2>
+              <p className="text-xs text-muted mt-1">
+                Agent: {selectedTask.agent.name} · Client: {selectedTask.client.company}
+                {selectedTask.task_category_detail && ` · ${selectedTask.task_category_detail.name}`}
+              </p>
+              <p className="text-xs text-muted">
+                {formatDistanceToNow(new Date(selectedTask.updated_at), { addSuffix: true })}
+              </p>
+            </div>
+
+            <hr className="border-border" />
+
+            {/* Task description */}
+            <div>
+              <p className="text-sm font-semibold text-primary mb-2">Task Description</p>
+              <p className="text-sm text-secondary">{selectedTask.description}</p>
+            </div>
+
+            <hr className="border-border" />
+
+            {/* Feedback */}
+            <div>
+              <p className="text-sm font-semibold text-primary mb-2">
+                Feedback (required for rejection)
+              </p>
+              <Textarea
+                value={feedback}
+                onChange={(e) => {
+                  setFeedback(e.target.value);
+                  if (e.target.value.trim()) setFeedbackError('');
+                }}
+                placeholder="Provide feedback for the agent…"
+                rows={4}
+              />
+              {feedbackError && (
+                <p className="text-xs text-red-600 mt-1">{feedbackError}</p>
+              )}
+            </div>
+
+            <hr className="border-border" />
+
+            {/* Actions */}
+            <div className="flex flex-col sm:flex-row gap-2">
+              <Button
+                variant="success"
+                onClick={handleApprove}
+                disabled={isSubmitting}
+                className="flex-1"
+              >
+                Approve
+              </Button>
+              <Button
+                variant="danger"
+                onClick={handleReject}
+                disabled={isSubmitting || !feedback.trim()}
+                className="flex-1"
+              >
+                Reject &amp; Return
+              </Button>
+            </div>
+          </div>
+        )}
+      </Drawer>
+    </div>
+  );
+}
diff --git a/client/components/dashboard/sidebar.tsx b/client/components/dashboard/sidebar.tsx
index e2663006c..dc652b5c8 100644
--- a/client/components/dashboard/sidebar.tsx
+++ b/client/components/dashboard/sidebar.tsx
@@ -43,12 +43,15 @@ import {
   Radio,
   LayoutDashboard,
   Repeat,
+  CheckCircle2,
+  Tag,
 } from 'lucide-react';
 import { useAuth } from '@/lib/hooks/useAuth';
 import { NavGroup, NavItem } from './NavGroup';
 import ApiService from '@/lib/api';
 import { cn } from '@/lib/utils';
 import { useUnreadMessages } from '@/lib/unread-messages-context';
+import { useSocket } from '@/lib/socket-context';
 
 interface SidebarProps {
   isGuestMode?: boolean;
@@ -59,9 +62,11 @@ export function Sidebar({ isGuestMode = false, onGuestSignIn }: SidebarProps) {
   const { user, logout } = useAuth();
   const pathname = usePathname();
   const { totalUnread } = useUnreadMessages();
+  const { on, off } = useSocket();
   const [isOpen, setIsOpen] = useState(false);
   const [isCollapsed, setIsCollapsed] = useState(false);
   const [agentDepartment, setAgentDepartment] = useState<string | null>(null);
+  const [pendingApprovalsCount, setPendingApprovalsCount] = useState(0);
 
   // Load collapsed state from localStorage
   useEffect(() => {
@@ -93,6 +98,29 @@ export function Sidebar({ isGuestMode = false, onGuestSignIn }: SidebarProps) {
     }
   }, [user]);
 
+  // Fetch pending approvals count for admin badge
+  useEffect(() => {
+    if (user?.role !== 'admin') return;
+    const fetchCount = async () => {
+      try {
+        const data = await ApiService.request<{ id: string }[]>('/admin/approvals/');
+        setPendingApprovalsCount(data.length);
+      } catch {
+        // ignore — badge stays at 0
+      }
+    };
+    fetchCount();
+    const handler = () => { fetchCount(); };
+    on('task_review_submitted', handler);
+    on('task_approved', handler);
+    on('task_rejected', handler);
+    return () => {
+      off('task_review_submitted', handler);
+      off('task_approved', handler);
+      off('task_rejected', handler);
+    };
+  }, [user?.role, on, off]);
+
   const handleLogout = async () => {
     await logout();
   };
@@ -102,6 +130,7 @@ export function Sidebar({ isGuestMode = false, onGuestSignIn }: SidebarProps) {
   };
 
   const messageBadge = totalUnread > 0 ? (totalUnread > 9 ? '9+' : totalUnread) : undefined;
+  const approvalsBadge = pendingApprovalsCount > 0 ? String(pendingApprovalsCount) : undefined;
 
   // Admin navigation structure
   const adminNavGroups = {
@@ -122,6 +151,12 @@ export function Sidebar({ isGuestMode = false, onGuestSignIn }: SidebarProps) {
           { href: '/dashboard/admin/analytics/revenue', label: 'Revenue' },
         ],
       },
+      {
+        href: '/dashboard/admin/approvals',
+        label: 'Approvals',
+        icon: <CheckCircle2 className="w-5 h-5" />,
+        badge: approvalsBadge,
+      },
     ],
     team: [
       {
@@ -163,6 +198,13 @@ export function Sidebar({ isGuestMode = false, onGuestSignIn }: SidebarProps) {
       },
       { href: '/dashboard/admin/messages', label: 'Messages', icon: <MessageSquare className="w-5 h-5" />, badge: messageBadge },
     ],
+    settings: [
+      {
+        href: '/dashboard/admin/settings/categories',
+        label: 'Categories',
+        icon: <Tag className="w-5 h-5" />,
+      },
+    ] as NavItem[],
     bottom: [] as NavItem[],
   };
 
@@ -405,6 +447,12 @@ export function Sidebar({ isGuestMode = false, onGuestSignIn }: SidebarProps) {
                 collapsed={isCollapsed}
                 onItemClick={() => setIsOpen(false)}
               />
+              <NavGroup
+                label="Settings"
+                items={(navGroups as typeof adminNavGroups).settings}
+                collapsed={isCollapsed}
+                onItemClick={() => setIsOpen(false)}
+              />
             </>
           )}
 
