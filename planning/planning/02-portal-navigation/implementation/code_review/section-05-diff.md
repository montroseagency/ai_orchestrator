diff --git a/client/app/dashboard/agent/marketing/management/layout.test.tsx b/client/app/dashboard/agent/marketing/management/layout.test.tsx
new file mode 100644
index 000000000..614c8f476
--- /dev/null
+++ b/client/app/dashboard/agent/marketing/management/layout.test.tsx
@@ -0,0 +1,75 @@
+import { render, screen } from '@testing-library/react'
+import { describe, it, expect, vi, beforeEach } from 'vitest'
+import React from 'react'
+import ManagementLayout from './layout'
+
+vi.mock('next/navigation', () => ({
+  usePathname: () => '/dashboard/agent/marketing/management',
+  useRouter: () => ({ push: vi.fn() }),
+}))
+
+vi.mock('next/link', () => ({
+  default: ({ href, children, ...props }: any) => (
+    <a href={href} {...props}>{children}</a>
+  ),
+}))
+
+vi.mock('@/components/dashboard/ManagementSidebar', () => ({
+  default: () => <div data-testid="management-sidebar" />,
+  ManagementSidebar: () => <div data-testid="management-sidebar" />,
+}))
+
+vi.mock('@/components/dashboard/breadcrumb', () => ({
+  default: () => <div data-testid="breadcrumb" />,
+  Breadcrumb: () => <div data-testid="breadcrumb" />,
+}))
+
+describe('ManagementLayout', () => {
+  beforeEach(() => vi.clearAllMocks())
+
+  it('renders ManagementSidebar', () => {
+    render(<ManagementLayout>page content</ManagementLayout>)
+    expect(screen.getByTestId('management-sidebar')).toBeInTheDocument()
+  })
+
+  it('renders Breadcrumb component', () => {
+    render(<ManagementLayout>page content</ManagementLayout>)
+    expect(screen.getByTestId('breadcrumb')).toBeInTheDocument()
+  })
+
+  it('renders children inside the main content area', () => {
+    render(<ManagementLayout><div data-testid="child">hello</div></ManagementLayout>)
+    const child = screen.getByTestId('child')
+    expect(child).toBeInTheDocument()
+    // Child should be inside a <main> element
+    expect(child.closest('main')).toBeInTheDocument()
+  })
+
+  it('main content area has topbar-height top padding applied', () => {
+    const { container } = render(<ManagementLayout>page content</ManagementLayout>)
+    const main = container.querySelector('main')
+    expect(main?.className ?? '').toMatch(/pt-14|pt-\[var\(--topbar-height\)\]/)
+  })
+
+  it('error boundary catches render error in children and shows fallback UI', () => {
+    // Suppress console.error for expected error
+    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
+
+    function BrokenChild() {
+      throw new Error('Test portal crash')
+    }
+
+    render(
+      <ManagementLayout>
+        <BrokenChild />
+      </ManagementLayout>
+    )
+
+    // Should show fallback instead of crashing
+    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument()
+    expect(screen.getByText(/return to dashboard/i)).toBeInTheDocument()
+    expect(screen.queryByText('Test portal crash')).not.toBeInTheDocument()
+
+    spy.mockRestore()
+  })
+})
diff --git a/client/app/dashboard/agent/marketing/management/layout.tsx b/client/app/dashboard/agent/marketing/management/layout.tsx
new file mode 100644
index 000000000..0ca00b5b8
--- /dev/null
+++ b/client/app/dashboard/agent/marketing/management/layout.tsx
@@ -0,0 +1,24 @@
+import React from 'react';
+import ManagementSidebar from '@/components/dashboard/ManagementSidebar';
+import Breadcrumb from '@/components/dashboard/breadcrumb';
+import { PortalErrorBoundary } from '@/components/common/error-boundary';
+
+export default function ManagementLayout({
+  children,
+}: {
+  children: React.ReactNode;
+}) {
+  return (
+    <div className="flex h-screen">
+      <ManagementSidebar />
+      <main className="flex-1 overflow-y-auto pt-14">
+        <div className="px-6 pt-4 pb-2">
+          <Breadcrumb />
+        </div>
+        <PortalErrorBoundary>
+          {children}
+        </PortalErrorBoundary>
+      </main>
+    </div>
+  );
+}
diff --git a/client/components/common/error-boundary.tsx b/client/components/common/error-boundary.tsx
index e69de29bb..83046bccd 100644
--- a/client/components/common/error-boundary.tsx
+++ b/client/components/common/error-boundary.tsx
@@ -0,0 +1,46 @@
+'use client';
+
+import React from 'react';
+import Link from 'next/link';
+
+interface ErrorBoundaryState {
+  hasError: boolean;
+}
+
+export class PortalErrorBoundary extends React.Component<
+  { children: React.ReactNode },
+  ErrorBoundaryState
+> {
+  constructor(props: { children: React.ReactNode }) {
+    super(props);
+    this.state = { hasError: false };
+  }
+
+  static getDerivedStateFromError(): ErrorBoundaryState {
+    return { hasError: true };
+  }
+
+  componentDidCatch(error: Error, info: React.ErrorInfo) {
+    console.error('Portal error boundary caught:', error, info);
+  }
+
+  render() {
+    if (this.state.hasError) {
+      return (
+        <div className="flex flex-col items-center justify-center min-h-[40vh] gap-4 p-8 text-center">
+          <p className="text-secondary text-sm">
+            Something went wrong in Command Centre.
+          </p>
+          <Link
+            href="/dashboard/agent/marketing/"
+            className="text-sm text-accent underline hover:no-underline"
+          >
+            Return to Dashboard
+          </Link>
+        </div>
+      );
+    }
+
+    return this.props.children;
+  }
+}
