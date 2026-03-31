diff --git a/client/components/dashboard/breadcrumb.test.tsx b/client/components/dashboard/breadcrumb.test.tsx
new file mode 100644
index 000000000..6ac7bbf82
--- /dev/null
+++ b/client/components/dashboard/breadcrumb.test.tsx
@@ -0,0 +1,89 @@
+import { render, screen } from '@testing-library/react'
+import { describe, it, expect, vi, beforeEach } from 'vitest'
+import React from 'react'
+import { Breadcrumb } from './breadcrumb'
+
+const mockUsePathname = vi.fn()
+vi.mock('next/navigation', () => ({
+  usePathname: () => mockUsePathname(),
+}))
+
+vi.mock('next/link', () => ({
+  default: ({ href, children, ...props }: any) => (
+    <a href={href} {...props}>{children}</a>
+  ),
+}))
+
+describe('Breadcrumb — portal segment labels', () => {
+  beforeEach(() => vi.clearAllMocks())
+
+  // --- Individual segment mapping tests ---
+
+  it('"management" segment maps to "Command Centre"', () => {
+    mockUsePathname.mockReturnValue('/dashboard/agent/marketing/management')
+    render(<Breadcrumb />)
+    expect(screen.getByText('Command Centre')).toBeInTheDocument()
+  })
+
+  it('"tasks" segment maps to "Tasks"', () => {
+    mockUsePathname.mockReturnValue('/dashboard/agent/marketing/management/tasks')
+    render(<Breadcrumb />)
+    expect(screen.getByText('Tasks')).toBeInTheDocument()
+  })
+
+  it('"calendar" segment maps to "Calendar"', () => {
+    mockUsePathname.mockReturnValue('/dashboard/agent/marketing/management/calendar')
+    render(<Breadcrumb />)
+    expect(screen.getByText('Calendar')).toBeInTheDocument()
+  })
+
+  it('"clients" segment maps to "Clients"', () => {
+    mockUsePathname.mockReturnValue('/dashboard/agent/marketing/management/clients')
+    render(<Breadcrumb />)
+    expect(screen.getByText('Clients')).toBeInTheDocument()
+  })
+
+  it('"notes" segment maps to "Notes"', () => {
+    mockUsePathname.mockReturnValue('/dashboard/agent/marketing/management/notes')
+    render(<Breadcrumb />)
+    expect(screen.getByText('Notes')).toBeInTheDocument()
+  })
+
+  // --- Full breadcrumb trail tests ---
+
+  it('/management: "Command Centre" renders as non-linked last segment (span)', () => {
+    mockUsePathname.mockReturnValue('/dashboard/agent/marketing/management')
+    render(<Breadcrumb />)
+    const item = screen.getByText('Command Centre')
+    expect(item.tagName).toBe('SPAN')
+  })
+
+  it('/management/tasks: "Command Centre" is a link; "Tasks" is the non-linked last segment', () => {
+    mockUsePathname.mockReturnValue('/dashboard/agent/marketing/management/tasks')
+    render(<Breadcrumb />)
+    expect(screen.getByText('Command Centre').tagName).toBe('A')
+    expect(screen.getByText('Tasks').tagName).toBe('SPAN')
+  })
+
+  it('/management/clients/abc123: "Clients" is a link; dynamic id is last non-linked segment', () => {
+    mockUsePathname.mockReturnValue('/dashboard/agent/marketing/management/clients/abc123')
+    render(<Breadcrumb />)
+    expect(screen.getByText('Clients').tagName).toBe('A')
+    // Dynamic segment: abc123 → first char uppercased by the fallback label logic
+    expect(screen.getByText('Abc123').tagName).toBe('SPAN')
+  })
+
+  it('/management/clients/abc123: "Command Centre" segment is clickable (has href)', () => {
+    mockUsePathname.mockReturnValue('/dashboard/agent/marketing/management/clients/abc123')
+    render(<Breadcrumb />)
+    const link = screen.getByText('Command Centre')
+    expect(link).toHaveAttribute('href')
+  })
+
+  it('/management: "Command Centre" is not clickable when it is the last segment', () => {
+    mockUsePathname.mockReturnValue('/dashboard/agent/marketing/management')
+    render(<Breadcrumb />)
+    const item = screen.getByText('Command Centre')
+    expect(item).not.toHaveAttribute('href')
+  })
+})
diff --git a/client/components/dashboard/breadcrumb.tsx b/client/components/dashboard/breadcrumb.tsx
index b98ffd6e9..5263ef506 100644
--- a/client/components/dashboard/breadcrumb.tsx
+++ b/client/components/dashboard/breadcrumb.tsx
@@ -57,6 +57,9 @@ const pathLabels: Record<string, string> = {
   revenue: 'Revenue',
   purchases: 'Purchases',
   developer: 'Developer',
+  management: 'Command Centre',
+  tasks: 'Tasks',
+  notes: 'Notes',
 };
 
 export function Breadcrumb({ items, className }: BreadcrumbProps) {
