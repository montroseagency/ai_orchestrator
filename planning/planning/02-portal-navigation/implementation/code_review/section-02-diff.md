diff --git a/client/app/dashboard/layout.test.tsx b/client/app/dashboard/layout.test.tsx
new file mode 100644
index 000000000..545f89972
--- /dev/null
+++ b/client/app/dashboard/layout.test.tsx
@@ -0,0 +1,170 @@
+import { render, screen } from '@testing-library/react'
+import { describe, it, expect, vi, beforeEach } from 'vitest'
+import React from 'react'
+import DashboardLayout from './layout'
+
+// --- Navigation mocks ---
+const mockUsePathname = vi.fn()
+vi.mock('next/navigation', () => ({
+  usePathname: () => mockUsePathname(),
+  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
+}))
+
+vi.mock('next/link', () => ({
+  default: ({ href, children, ...props }: any) => (
+    <a href={href} {...props}>{children}</a>
+  ),
+}))
+
+// --- Auth mock ---
+vi.mock('@/lib/hooks/useAuth', () => ({
+  useAuth: () => ({
+    user: { role: 'agent', id: 1 },
+    isAuthenticated: true,
+    loading: false,
+    logout: vi.fn(),
+  }),
+}))
+
+// --- Component mocks: Sidebar is the key observable ---
+vi.mock('@/components/dashboard/sidebar', () => ({
+  Sidebar: () => <div data-testid="global-sidebar" />,
+}))
+vi.mock('@/components/dashboard/topbar', () => ({
+  Topbar: () => <div data-testid="topbar" />,
+}))
+vi.mock('@/components/dashboard/ProfileIncompleteBanner', () => ({
+  ProfileIncompleteBanner: () => null,
+}))
+vi.mock('@/components/messaging/MarketingChatWidget', () => ({
+  MarketingChatWidget: () => null,
+}))
+vi.mock('@/components/messaging/WebsiteChatWidget', () => ({
+  WebsiteChatWidget: () => null,
+}))
+
+// --- Provider mocks: pass children through ---
+vi.mock('@/lib/socket-context', () => ({
+  SocketProvider: ({ children }: any) => <>{children}</>,
+}))
+vi.mock('@/lib/notification-socket-context', () => ({
+  NotificationSocketProvider: ({ children }: any) => <>{children}</>,
+}))
+vi.mock('@/lib/unread-messages-context', () => ({
+  UnreadMessagesProvider: ({ children }: any) => <>{children}</>,
+}))
+vi.mock('@/components/call', () => ({
+  CallProvider: ({ children }: any) => <>{children}</>,
+  useCall: () => ({ incomingCall: null, activeCall: null }),
+  IncomingCallModal: () => null,
+  CallWindow: () => null,
+  FloatingCallWidget: () => null,
+}))
+vi.mock('@/lib/providers/ReactQueryProvider', () => ({
+  default: ({ children }: any) => <>{children}</>,
+}))
+vi.mock('sonner', () => ({
+  Toaster: () => null,
+}))
+
+// --- Stub localStorage ---
+const localStorageMock = (() => {
+  const store: Record<string, string> = {}
+  return {
+    getItem: (key: string) => store[key] ?? null,
+    setItem: (key: string, value: string) => { store[key] = value },
+    removeItem: (key: string) => { delete store[key] },
+    clear: () => { Object.keys(store).forEach((k) => delete store[k]) },
+    length: 0,
+    key: () => null,
+  }
+})()
+Object.defineProperty(window, 'localStorage', { value: localStorageMock, writable: true })
+
+describe('DashboardLayout — portal detection', () => {
+  beforeEach(() => {
+    vi.clearAllMocks()
+    localStorageMock.clear()
+    vi.useFakeTimers()
+  })
+
+  afterEach(() => {
+    vi.useRealTimers()
+  })
+
+  // --- isInPortal true: Sidebar should NOT render ---
+
+  it('isInPortal is true when pathname is /dashboard/agent/marketing/management', () => {
+    mockUsePathname.mockReturnValue('/dashboard/agent/marketing/management')
+    render(<DashboardLayout>content</DashboardLayout>)
+    expect(screen.queryByTestId('global-sidebar')).not.toBeInTheDocument()
+  })
+
+  it('isInPortal is true when pathname is /dashboard/agent/marketing/management/', () => {
+    mockUsePathname.mockReturnValue('/dashboard/agent/marketing/management/')
+    render(<DashboardLayout>content</DashboardLayout>)
+    expect(screen.queryByTestId('global-sidebar')).not.toBeInTheDocument()
+  })
+
+  it('isInPortal is true when pathname is /dashboard/agent/marketing/management/tasks', () => {
+    mockUsePathname.mockReturnValue('/dashboard/agent/marketing/management/tasks')
+    render(<DashboardLayout>content</DashboardLayout>)
+    expect(screen.queryByTestId('global-sidebar')).not.toBeInTheDocument()
+  })
+
+  it('isInPortal is true when pathname is /dashboard/agent/marketing/management/clients/abc123', () => {
+    mockUsePathname.mockReturnValue('/dashboard/agent/marketing/management/clients/abc123')
+    render(<DashboardLayout>content</DashboardLayout>)
+    expect(screen.queryByTestId('global-sidebar')).not.toBeInTheDocument()
+  })
+
+  // --- isInPortal false: Sidebar SHOULD render ---
+
+  it('isInPortal is false when pathname is /dashboard/agent/marketing', () => {
+    mockUsePathname.mockReturnValue('/dashboard/agent/marketing')
+    render(<DashboardLayout>content</DashboardLayout>)
+    expect(screen.getByTestId('global-sidebar')).toBeInTheDocument()
+  })
+
+  it('isInPortal is false when pathname is /dashboard/agent/marketing/schedule', () => {
+    mockUsePathname.mockReturnValue('/dashboard/agent/marketing/schedule')
+    render(<DashboardLayout>content</DashboardLayout>)
+    expect(screen.getByTestId('global-sidebar')).toBeInTheDocument()
+  })
+
+  it('isInPortal is false for /dashboard/agent/marketing/management-reports (false-positive guard)', () => {
+    mockUsePathname.mockReturnValue('/dashboard/agent/marketing/management-reports')
+    render(<DashboardLayout>content</DashboardLayout>)
+    expect(screen.getByTestId('global-sidebar')).toBeInTheDocument()
+  })
+
+  // --- Sidebar conditional render ---
+
+  it('global Sidebar is NOT rendered when isInPortal is true', () => {
+    mockUsePathname.mockReturnValue('/dashboard/agent/marketing/management/tasks')
+    render(<DashboardLayout>children</DashboardLayout>)
+    expect(screen.queryByTestId('global-sidebar')).not.toBeInTheDocument()
+  })
+
+  it('global Sidebar IS rendered when isInPortal is false', () => {
+    mockUsePathname.mockReturnValue('/dashboard/agent/marketing')
+    render(<DashboardLayout>children</DashboardLayout>)
+    expect(screen.getByTestId('global-sidebar')).toBeInTheDocument()
+  })
+
+  // --- Sidebar margin classes ---
+
+  it('main content wrapper does NOT have sidebar-offset margin when isInPortal is true', () => {
+    mockUsePathname.mockReturnValue('/dashboard/agent/marketing/management/tasks')
+    const { container } = render(<DashboardLayout>content</DashboardLayout>)
+    const mainWrapper = container.querySelector('[data-testid="main-content"]')
+    expect(mainWrapper?.className ?? '').not.toMatch(/md:ml-/)
+  })
+
+  it('main content wrapper has sidebar-offset margin when isInPortal is false', () => {
+    mockUsePathname.mockReturnValue('/dashboard/agent/marketing')
+    const { container } = render(<DashboardLayout>content</DashboardLayout>)
+    const mainWrapper = container.querySelector('[data-testid="main-content"]')
+    expect(mainWrapper?.className ?? '').toMatch(/md:ml-/)
+  })
+})
diff --git a/client/app/dashboard/layout.tsx b/client/app/dashboard/layout.tsx
index bea0406e6..dea102e17 100644
--- a/client/app/dashboard/layout.tsx
+++ b/client/app/dashboard/layout.tsx
@@ -83,6 +83,12 @@ export default function DashboardLayout({
   // Check if this is a guest route
   const isGuest = isGuestRoute(pathname);
 
+  // Portal detection: suppress global sidebar when inside the management portal.
+  // Handle both /management (no trailing slash) and /management/* (sub-routes).
+  const isInPortal =
+    pathname === '/dashboard/agent/marketing/management' ||
+    (!!pathname && pathname.startsWith('/dashboard/agent/marketing/management/'));
+
   // Sync sidebar collapsed state with localStorage
   useEffect(() => {
     const savedCollapsed = localStorage.getItem('sidebar-collapsed');
@@ -164,14 +170,15 @@ export default function DashboardLayout({
             <GlobalCallUI />
 
             <div className="flex h-screen bg-surface-subtle overflow-hidden">
-              {/* Sidebar */}
-              <Sidebar />
+              {/* Global Sidebar — suppressed inside the management portal */}
+              {!isInPortal && <Sidebar />}
 
               {/* Main Content Area */}
               <div
+                data-testid="main-content"
                 className={cn(
                   'flex-1 flex flex-col h-screen transition-all duration-200',
-                  sidebarCollapsed ? 'md:ml-16' : 'md:ml-60'
+                  !isInPortal && (sidebarCollapsed ? 'md:ml-16' : 'md:ml-60')
                 )}
               >
                 {/* Topbar */}
