diff --git a/client/components/dashboard/sidebar.test.tsx b/client/components/dashboard/sidebar.test.tsx
new file mode 100644
index 000000000..23c8741ce
--- /dev/null
+++ b/client/components/dashboard/sidebar.test.tsx
@@ -0,0 +1,88 @@
+import { render, screen, waitFor } from '@testing-library/react'
+import { describe, it, expect, vi, beforeEach } from 'vitest'
+import React from 'react'
+import { Sidebar } from './sidebar'
+
+// Mock Next.js navigation
+vi.mock('next/navigation', () => ({
+  usePathname: () => '/dashboard/agent/marketing',
+  useRouter: () => ({ push: vi.fn() }),
+}))
+
+// Mock Next.js Link to render as plain <a>
+vi.mock('next/link', () => ({
+  default: ({ href, children, ...props }: any) => (
+    <a href={href} {...props}>
+      {children}
+    </a>
+  ),
+}))
+
+// Mock auth as vi.fn() so each test can override the return value
+const mockUseAuth = vi.fn()
+vi.mock('@/lib/hooks/useAuth', () => ({
+  useAuth: () => mockUseAuth(),
+}))
+
+// Mock unread messages context
+vi.mock('@/lib/unread-messages-context', () => ({
+  useUnreadMessages: () => ({ totalUnread: 0 }),
+}))
+
+// Mock ApiService as vi.fn() so each test can override getMe
+const mockGetMe = vi.fn()
+vi.mock('@/lib/api', () => ({
+  default: { getMe: (...args: any[]) => mockGetMe(...args) },
+}))
+
+// Stub localStorage
+const localStorageMock = (() => {
+  const store: Record<string, string> = {}
+  return {
+    getItem: (key: string) => store[key] ?? null,
+    setItem: (key: string, value: string) => { store[key] = value },
+    removeItem: (key: string) => { delete store[key] },
+    clear: () => { Object.keys(store).forEach((k) => delete store[k]) },
+  }
+})()
+Object.defineProperty(window, 'localStorage', { value: localStorageMock, writable: true })
+
+describe('Sidebar — gateway link', () => {
+  beforeEach(() => {
+    localStorageMock.clear()
+    vi.clearAllMocks()
+  })
+
+  it('marketing agent Command Center nav item href is /dashboard/agent/marketing/management/', async () => {
+    mockUseAuth.mockReturnValue({
+      user: { role: 'agent', id: 1, email: 'marketing@test.com' },
+      logout: vi.fn(),
+    })
+    mockGetMe.mockResolvedValue({ agent_profile: { department: 'marketing' } })
+
+    render(<Sidebar />)
+
+    // After agentDepartment is set via async useEffect, the marketing nav renders.
+    // Use waitFor so we retry until the href is correct (avoids matching the
+    // initial developer fallback nav).
+    await waitFor(() => {
+      const link = screen.getByRole('link', { name: /command center/i })
+      expect(link).toHaveAttribute('href', '/dashboard/agent/marketing/management/')
+    })
+  })
+
+  it('no other sidebar nav items changed — developer Command Center still points to schedule', async () => {
+    mockUseAuth.mockReturnValue({
+      user: { role: 'agent', id: 2, email: 'dev@test.com' },
+      logout: vi.fn(),
+    })
+    mockGetMe.mockResolvedValue({ agent_profile: { department: 'developer' } })
+
+    render(<Sidebar />)
+
+    // Developer nav is the initial fallback (agentDepartment === null uses developerAgentNavGroups),
+    // so the link appears immediately.
+    const link = await screen.findByRole('link', { name: /command center/i })
+    expect(link).toHaveAttribute('href', '/dashboard/agent/developer/schedule')
+  })
+})
diff --git a/client/components/dashboard/sidebar.tsx b/client/components/dashboard/sidebar.tsx
index a04aef88e..9c33173ee 100644
--- a/client/components/dashboard/sidebar.tsx
+++ b/client/components/dashboard/sidebar.tsx
@@ -215,7 +215,7 @@ export function Sidebar({ isGuestMode = false, onGuestSignIn }: SidebarProps) {
   // Marketing Agent navigation
   const marketingAgentNavGroups = {
     main: [
-      { href: '/dashboard/agent/marketing/schedule', label: 'Command Center', icon: <LayoutDashboard className="w-5 h-5" /> },
+      { href: '/dashboard/agent/marketing/management/', label: 'Command Center', icon: <LayoutDashboard className="w-5 h-5" /> },
       { href: '/dashboard/agent/marketing', label: 'Overview', icon: <Home className="w-5 h-5" /> },
     ],
     content: [
diff --git a/client/package.json b/client/package.json
index 2ea131aa7..ad3086257 100644
--- a/client/package.json
+++ b/client/package.json
@@ -6,7 +6,8 @@
     "dev": "next dev",
     "build": "next build --no-lint",
     "start": "next start",
-    "lint": "eslint"
+    "lint": "eslint",
+    "test": "vitest"
   },
   "dependencies": {
     "@dnd-kit/core": "^6.3.1",
@@ -19,26 +20,32 @@
     "framer-motion": "^11.11.17",
     "lucide-react": "^0.552.0",
     "next": "^15.5.12",
+    "prism-react-renderer": "^2.3.1",
     "react": "19.2.0",
     "react-chartjs-2": "^5.3.1",
     "react-dom": "19.2.0",
     "react-image-crop": "^11.0.10",
+    "recharts": "^2.15.3",
     "simple-peer": "^9.11.1",
     "socket.io-client": "^4.8.1",
-    "prism-react-renderer": "^2.3.1",
-    "recharts": "^2.15.3",
     "sonner": "^1.7.3",
     "tailwind-merge": "^3.4.0"
   },
   "devDependencies": {
     "@tailwindcss/postcss": "^4",
+    "@testing-library/jest-dom": "^6.9.1",
+    "@testing-library/react": "^16.3.2",
+    "@testing-library/user-event": "^14.6.1",
     "@types/node": "^20",
     "@types/react": "^19",
     "@types/react-dom": "^19",
     "@types/simple-peer": "^9.11.8",
+    "@vitejs/plugin-react": "^6.0.1",
     "eslint": "^9",
     "eslint-config-next": "16.0.1",
+    "jsdom": "^29.0.1",
     "tailwindcss": "^4",
-    "typescript": "^5"
+    "typescript": "^5",
+    "vitest": "^4.1.2"
   }
 }
diff --git a/client/vitest.config.ts b/client/vitest.config.ts
new file mode 100644
index 000000000..957761c9a
--- /dev/null
+++ b/client/vitest.config.ts
@@ -0,0 +1,17 @@
+import { defineConfig } from 'vitest/config'
+import react from '@vitejs/plugin-react'
+import path from 'path'
+
+export default defineConfig({
+  plugins: [react()],
+  test: {
+    environment: 'jsdom',
+    setupFiles: ['./vitest.setup.ts'],
+    globals: true,
+  },
+  resolve: {
+    alias: {
+      '@': path.resolve(__dirname, '.'),
+    },
+  },
+})
diff --git a/client/vitest.setup.ts b/client/vitest.setup.ts
new file mode 100644
index 000000000..c44951a68
--- /dev/null
+++ b/client/vitest.setup.ts
@@ -0,0 +1 @@
+import '@testing-library/jest-dom'
