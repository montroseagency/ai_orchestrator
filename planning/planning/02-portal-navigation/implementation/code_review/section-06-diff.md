diff --git a/client/app/dashboard/agent/marketing/management/calendar/page.tsx b/client/app/dashboard/agent/marketing/management/calendar/page.tsx
new file mode 100644
index 000000000..e3361af69
--- /dev/null
+++ b/client/app/dashboard/agent/marketing/management/calendar/page.tsx
@@ -0,0 +1,18 @@
+import Link from 'next/link';
+
+export default function CalendarPage() {
+  return (
+    <div className="p-6">
+      <h1 className="text-xl font-semibold text-primary">Calendar</h1>
+      <p className="mt-2 text-sm text-secondary">
+        This section is being built and will be available soon.
+      </p>
+      <Link
+        href="/dashboard/agent/marketing/management/"
+        className="mt-4 inline-block text-sm text-accent hover:underline"
+      >
+        Back to Command Centre
+      </Link>
+    </div>
+  );
+}
diff --git a/client/app/dashboard/agent/marketing/management/clients/[id]/page.tsx b/client/app/dashboard/agent/marketing/management/clients/[id]/page.tsx
new file mode 100644
index 000000000..c1a11d0fd
--- /dev/null
+++ b/client/app/dashboard/agent/marketing/management/clients/[id]/page.tsx
@@ -0,0 +1,18 @@
+import Link from 'next/link';
+
+export default function ClientDetailPage({ params }: { params: { id: string } }) {
+  return (
+    <div className="p-6">
+      <h1 className="text-xl font-semibold text-primary">Client Detail</h1>
+      <p className="mt-2 text-sm text-secondary">
+        Client ID: {params.id}
+      </p>
+      <Link
+        href="/dashboard/agent/marketing/management/clients/"
+        className="mt-4 inline-block text-sm text-accent hover:underline"
+      >
+        Back to Clients
+      </Link>
+    </div>
+  );
+}
diff --git a/client/app/dashboard/agent/marketing/management/clients/page.tsx b/client/app/dashboard/agent/marketing/management/clients/page.tsx
new file mode 100644
index 000000000..e09dcf5be
--- /dev/null
+++ b/client/app/dashboard/agent/marketing/management/clients/page.tsx
@@ -0,0 +1,18 @@
+import Link from 'next/link';
+
+export default function ClientsPage() {
+  return (
+    <div className="p-6">
+      <h1 className="text-xl font-semibold text-primary">Clients</h1>
+      <p className="mt-2 text-sm text-secondary">
+        This section is being built and will be available soon.
+      </p>
+      <Link
+        href="/dashboard/agent/marketing/management/"
+        className="mt-4 inline-block text-sm text-accent hover:underline"
+      >
+        Back to Command Centre
+      </Link>
+    </div>
+  );
+}
diff --git a/client/app/dashboard/agent/marketing/management/notes/page.tsx b/client/app/dashboard/agent/marketing/management/notes/page.tsx
new file mode 100644
index 000000000..9cb5c50d0
--- /dev/null
+++ b/client/app/dashboard/agent/marketing/management/notes/page.tsx
@@ -0,0 +1,18 @@
+import Link from 'next/link';
+
+export default function NotesPage() {
+  return (
+    <div className="p-6">
+      <h1 className="text-xl font-semibold text-primary">Notes</h1>
+      <p className="mt-2 text-sm text-secondary">
+        This section is being built and will be available soon.
+      </p>
+      <Link
+        href="/dashboard/agent/marketing/management/"
+        className="mt-4 inline-block text-sm text-accent hover:underline"
+      >
+        Back to Command Centre
+      </Link>
+    </div>
+  );
+}
diff --git a/client/app/dashboard/agent/marketing/management/page.tsx b/client/app/dashboard/agent/marketing/management/page.tsx
new file mode 100644
index 000000000..e6d3f2ec7
--- /dev/null
+++ b/client/app/dashboard/agent/marketing/management/page.tsx
@@ -0,0 +1,67 @@
+import Link from 'next/link';
+import {
+  CheckSquare,
+  Calendar,
+  Users,
+  StickyNote,
+} from 'lucide-react';
+
+const BASE = '/dashboard/agent/marketing/management';
+
+const sections = [
+  {
+    href: `${BASE}/tasks`,
+    label: 'Tasks',
+    icon: CheckSquare,
+    description: 'Unified task manager across all campaigns and projects.',
+  },
+  {
+    href: `${BASE}/calendar`,
+    label: 'Calendar',
+    icon: Calendar,
+    description: 'Scheduling engine and event timeline for all marketing activities.',
+  },
+  {
+    href: `${BASE}/clients`,
+    label: 'Clients',
+    icon: Users,
+    description: 'Client CRM hub and contact management.',
+  },
+  {
+    href: `${BASE}/notes`,
+    label: 'Notes',
+    icon: StickyNote,
+    description: 'Quick notes and reference materials for your team.',
+  },
+];
+
+export default function ManagementOverviewPage() {
+  return (
+    <div className="p-6 max-w-4xl">
+      <div className="mb-8">
+        <h1 className="text-2xl font-display font-semibold text-primary">Command Centre</h1>
+        <p className="mt-1 text-sm text-secondary">
+          Your unified workspace for managing marketing operations.
+        </p>
+      </div>
+
+      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
+        {sections.map(({ href, label, icon: Icon, description }) => (
+          <Link
+            key={href}
+            href={href}
+            className="flex items-start gap-4 p-5 bg-surface border border-border rounded-lg hover:bg-surface-subtle transition-colors"
+          >
+            <span className="flex-shrink-0 p-2 bg-accent-light rounded-md">
+              <Icon className="w-5 h-5 text-accent" />
+            </span>
+            <div>
+              <p className="text-sm font-semibold text-primary">{label}</p>
+              <p className="mt-0.5 text-xs text-secondary">{description}</p>
+            </div>
+          </Link>
+        ))}
+      </div>
+    </div>
+  );
+}
diff --git a/client/app/dashboard/agent/marketing/management/pages.test.tsx b/client/app/dashboard/agent/marketing/management/pages.test.tsx
new file mode 100644
index 000000000..c9e04e1e8
--- /dev/null
+++ b/client/app/dashboard/agent/marketing/management/pages.test.tsx
@@ -0,0 +1,95 @@
+import { render, screen } from '@testing-library/react'
+import { describe, it, expect, vi } from 'vitest'
+import React from 'react'
+
+vi.mock('next/link', () => ({
+  default: ({ href, children, ...props }: any) => (
+    <a href={href} {...props}>{children}</a>
+  ),
+}))
+
+// ── Overview page ──────────────────────────────────────────────────────────
+describe('Management Overview page', () => {
+  it('renders "Command Centre" heading', async () => {
+    const { default: Page } = await import('./page')
+    render(<Page />)
+    expect(screen.getByRole('heading', { name: /command centre/i })).toBeInTheDocument()
+  })
+
+  it('renders navigation cards for all 4 sub-sections', async () => {
+    const { default: Page } = await import('./page')
+    render(<Page />)
+    expect(screen.getByText('Tasks')).toBeInTheDocument()
+    expect(screen.getByText('Calendar')).toBeInTheDocument()
+    expect(screen.getByText('Clients')).toBeInTheDocument()
+    expect(screen.getByText('Notes')).toBeInTheDocument()
+  })
+
+  it('each navigation card links to the correct /management/[section] route', async () => {
+    const { default: Page } = await import('./page')
+    render(<Page />)
+    expect(screen.getByRole('link', { name: /tasks/i })).toHaveAttribute('href', expect.stringContaining('/management/tasks'))
+    expect(screen.getByRole('link', { name: /calendar/i })).toHaveAttribute('href', expect.stringContaining('/management/calendar'))
+    expect(screen.getByRole('link', { name: /clients/i })).toHaveAttribute('href', expect.stringContaining('/management/clients'))
+    expect(screen.getByRole('link', { name: /notes/i })).toHaveAttribute('href', expect.stringContaining('/management/notes'))
+  })
+})
+
+// ── Tasks page ────────────────────────────────────────────────────────────
+describe('Management Tasks page', () => {
+  it('renders page title', async () => {
+    const { default: Page } = await import('./tasks/page')
+    render(<Page />)
+    expect(screen.getByRole('heading', { name: /tasks/i })).toBeInTheDocument()
+  })
+
+  it('renders link back to /management', async () => {
+    const { default: Page } = await import('./tasks/page')
+    render(<Page />)
+    const backLink = screen.getByRole('link', { name: /back to command centre/i })
+    expect(backLink).toHaveAttribute('href', expect.stringContaining('/management'))
+  })
+})
+
+// ── Calendar page ─────────────────────────────────────────────────────────
+describe('Management Calendar page', () => {
+  it('renders page title', async () => {
+    const { default: Page } = await import('./calendar/page')
+    render(<Page />)
+    expect(screen.getByRole('heading', { name: /calendar/i })).toBeInTheDocument()
+  })
+})
+
+// ── Clients page ──────────────────────────────────────────────────────────
+describe('Management Clients page', () => {
+  it('renders page title', async () => {
+    const { default: Page } = await import('./clients/page')
+    render(<Page />)
+    expect(screen.getByRole('heading', { name: /clients/i })).toBeInTheDocument()
+  })
+})
+
+// ── Notes page ────────────────────────────────────────────────────────────
+describe('Management Notes page', () => {
+  it('renders page title', async () => {
+    const { default: Page } = await import('./notes/page')
+    render(<Page />)
+    expect(screen.getByRole('heading', { name: /notes/i })).toBeInTheDocument()
+  })
+})
+
+// ── Clients [id] page ─────────────────────────────────────────────────────
+describe('Management Clients [id] page', () => {
+  it('renders the id parameter value', async () => {
+    const { default: Page } = await import('./clients/[id]/page')
+    render(<Page params={{ id: 'client-abc' }} />)
+    expect(screen.getByText(/client-abc/i)).toBeInTheDocument()
+  })
+
+  it('renders link back to /management/clients', async () => {
+    const { default: Page } = await import('./clients/[id]/page')
+    render(<Page params={{ id: 'client-abc' }} />)
+    const backLink = screen.getByRole('link', { name: /back to clients/i })
+    expect(backLink).toHaveAttribute('href', expect.stringContaining('/management/clients'))
+  })
+})
diff --git a/client/app/dashboard/agent/marketing/management/tasks/page.tsx b/client/app/dashboard/agent/marketing/management/tasks/page.tsx
new file mode 100644
index 000000000..c70790a58
--- /dev/null
+++ b/client/app/dashboard/agent/marketing/management/tasks/page.tsx
@@ -0,0 +1,18 @@
+import Link from 'next/link';
+
+export default function TasksPage() {
+  return (
+    <div className="p-6">
+      <h1 className="text-xl font-semibold text-primary">Tasks</h1>
+      <p className="mt-2 text-sm text-secondary">
+        This section is being built and will be available soon.
+      </p>
+      <Link
+        href="/dashboard/agent/marketing/management/"
+        className="mt-4 inline-block text-sm text-accent hover:underline"
+      >
+        Back to Command Centre
+      </Link>
+    </div>
+  );
+}
