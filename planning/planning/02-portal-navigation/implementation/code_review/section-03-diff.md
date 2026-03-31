diff --git a/client/components/dashboard/ManagementSidebar.test.tsx b/client/components/dashboard/ManagementSidebar.test.tsx
new file mode 100644
index 000000000..e165ee9bc
--- /dev/null
+++ b/client/components/dashboard/ManagementSidebar.test.tsx
@@ -0,0 +1,192 @@
+import { render, screen, fireEvent, waitFor } from '@testing-library/react'
+import { describe, it, expect, vi, beforeEach } from 'vitest'
+import React from 'react'
+import { ManagementSidebar } from './ManagementSidebar'
+
+const mockUsePathname = vi.fn()
+vi.mock('next/navigation', () => ({
+  usePathname: () => mockUsePathname(),
+  useRouter: () => ({ push: vi.fn() }),
+}))
+
+vi.mock('next/link', () => ({
+  default: ({ href, children, ...props }: any) => (
+    <a href={href} {...props}>{children}</a>
+  ),
+}))
+
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
+describe('ManagementSidebar', () => {
+  beforeEach(() => {
+    vi.clearAllMocks()
+    localStorageMock.clear()
+    mockUsePathname.mockReturnValue('/dashboard/agent/marketing/management')
+  })
+
+  // --- Nav item presence ---
+
+  it('renders all 5 nav items', () => {
+    render(<ManagementSidebar />)
+    expect(screen.getByText('Overview')).toBeInTheDocument()
+    expect(screen.getByText('Tasks')).toBeInTheDocument()
+    expect(screen.getByText('Calendar')).toBeInTheDocument()
+    expect(screen.getByText('Clients')).toBeInTheDocument()
+    expect(screen.getByText('Notes')).toBeInTheDocument()
+  })
+
+  it('renders "Command Centre" header', () => {
+    render(<ManagementSidebar />)
+    expect(screen.getByText('Command Centre')).toBeInTheDocument()
+  })
+
+  it('"Return to Dashboard" button links to /dashboard/agent/marketing/', () => {
+    render(<ManagementSidebar />)
+    const returnLink = screen.getByText('Return to Dashboard')
+    expect(returnLink.closest('a')).toHaveAttribute('href', '/dashboard/agent/marketing/')
+  })
+
+  // --- Active states ---
+
+  it('Overview nav item has active class when pathname is exactly /management', () => {
+    mockUsePathname.mockReturnValue('/dashboard/agent/marketing/management')
+    render(<ManagementSidebar />)
+    const overviewLink = screen.getByText('Overview').closest('a')
+    expect(overviewLink?.className).toMatch(/nav-item-active|accent|bg-accent/)
+  })
+
+  it('Overview nav item does NOT have active class when pathname is /management/tasks', () => {
+    mockUsePathname.mockReturnValue('/dashboard/agent/marketing/management/tasks')
+    render(<ManagementSidebar />)
+    const overviewLink = screen.getByText('Overview').closest('a')
+    expect(overviewLink?.className ?? '').not.toMatch(/nav-item-active/)
+  })
+
+  it('Tasks nav item has active class when pathname is /management/tasks', () => {
+    mockUsePathname.mockReturnValue('/dashboard/agent/marketing/management/tasks')
+    render(<ManagementSidebar />)
+    const tasksLink = screen.getByText('Tasks').closest('a')
+    expect(tasksLink?.className).toMatch(/nav-item-active|accent|bg-accent/)
+  })
+
+  it('Clients nav item has active class when pathname is /management/clients', () => {
+    mockUsePathname.mockReturnValue('/dashboard/agent/marketing/management/clients')
+    render(<ManagementSidebar />)
+    const clientsLink = screen.getByText('Clients').closest('a')
+    expect(clientsLink?.className).toMatch(/nav-item-active|accent|bg-accent/)
+  })
+
+  it('Clients nav item has active class when on /management/clients/[id] (startsWith)', () => {
+    mockUsePathname.mockReturnValue('/dashboard/agent/marketing/management/clients/abc123')
+    render(<ManagementSidebar />)
+    const clientsLink = screen.getByText('Clients').closest('a')
+    expect(clientsLink?.className).toMatch(/nav-item-active|accent|bg-accent/)
+  })
+
+  // --- Collapse toggle ---
+
+  it('collapse toggle has aria-expanded="false" when sidebar is expanded', () => {
+    render(<ManagementSidebar />)
+    const toggle = screen.getByRole('button', { name: /collapse|expand/i })
+    expect(toggle).toHaveAttribute('aria-expanded', 'false')
+  })
+
+  it('collapse toggle has aria-expanded="true" when sidebar is collapsed', async () => {
+    render(<ManagementSidebar />)
+    const toggle = screen.getByRole('button', { name: /collapse|expand/i })
+    fireEvent.click(toggle)
+    await waitFor(() => {
+      expect(toggle).toHaveAttribute('aria-expanded', 'true')
+    })
+  })
+
+  it('collapse toggle has aria-controls matching the sidebar element id', () => {
+    render(<ManagementSidebar />)
+    const toggle = screen.getByRole('button', { name: /collapse|expand/i })
+    const ariaControls = toggle.getAttribute('aria-controls')
+    expect(ariaControls).toBeTruthy()
+    const sidebar = document.getElementById(ariaControls!)
+    expect(sidebar).toBeInTheDocument()
+  })
+
+  it('clicking collapse toggle changes sidebar from w-60 to w-16', async () => {
+    const { container } = render(<ManagementSidebar />)
+    const aside = container.querySelector('aside')
+    expect(aside?.className).toMatch(/w-60/)
+    const toggle = screen.getByRole('button', { name: /collapse|expand/i })
+    fireEvent.click(toggle)
+    await waitFor(() => {
+      expect(aside?.className).toMatch(/w-16/)
+    })
+  })
+
+  it('clicking collapse toggle again restores sidebar to w-60', async () => {
+    const { container } = render(<ManagementSidebar />)
+    const aside = container.querySelector('aside')
+    const toggle = screen.getByRole('button', { name: /collapse|expand/i })
+    fireEvent.click(toggle)
+    await waitFor(() => expect(aside?.className).toMatch(/w-16/))
+    fireEvent.click(toggle)
+    await waitFor(() => expect(aside?.className).toMatch(/w-60/))
+  })
+
+  // --- localStorage persistence ---
+
+  it('collapse state is written to localStorage on toggle', async () => {
+    render(<ManagementSidebar />)
+    const toggle = screen.getByRole('button', { name: /collapse|expand/i })
+    fireEvent.click(toggle)
+    await waitFor(() => {
+      expect(localStorageMock.getItem('management-sidebar-collapsed')).toBe('true')
+    })
+  })
+
+  it('collapse state is hydrated from localStorage on mount', async () => {
+    localStorageMock.setItem('management-sidebar-collapsed', 'true')
+    const { container } = render(<ManagementSidebar />)
+    const aside = container.querySelector('aside')
+    await waitFor(() => {
+      expect(aside?.className).toMatch(/w-16/)
+    })
+  })
+
+  // --- Mobile drawer ---
+
+  it('mobile drawer opens when hamburger button is clicked', () => {
+    render(<ManagementSidebar />)
+    const hamburger = screen.getByRole('button', { name: /menu|open/i })
+    fireEvent.click(hamburger)
+    expect(screen.getByRole('dialog')).toBeInTheDocument()
+  })
+
+  it('mobile drawer has role="dialog" and aria-modal="true"', () => {
+    render(<ManagementSidebar />)
+    const hamburger = screen.getByRole('button', { name: /menu|open/i })
+    fireEvent.click(hamburger)
+    const dialog = screen.getByRole('dialog')
+    expect(dialog).toHaveAttribute('aria-modal', 'true')
+  })
+
+  it('mobile drawer closes when backdrop is clicked', async () => {
+    render(<ManagementSidebar />)
+    const hamburger = screen.getByRole('button', { name: /menu|open/i })
+    fireEvent.click(hamburger)
+    const backdrop = document.querySelector('[data-testid="mobile-backdrop"]')
+    expect(backdrop).toBeInTheDocument()
+    fireEvent.click(backdrop!)
+    await waitFor(() => {
+      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
+    })
+  })
+})
diff --git a/client/components/dashboard/ManagementSidebar.tsx b/client/components/dashboard/ManagementSidebar.tsx
new file mode 100644
index 000000000..c3ccaa410
--- /dev/null
+++ b/client/components/dashboard/ManagementSidebar.tsx
@@ -0,0 +1,259 @@
+'use client';
+
+import Link from 'next/link';
+import { usePathname } from 'next/navigation';
+import { useState, useEffect, useRef } from 'react';
+import {
+  Home,
+  CheckSquare,
+  Calendar,
+  Users,
+  StickyNote,
+  ChevronLeft,
+  ChevronRight,
+  Menu,
+  X,
+  ArrowLeft,
+} from 'lucide-react';
+import { cn } from '@/lib/utils';
+
+const SIDEBAR_ID = 'management-sidebar-nav';
+
+interface NavItem {
+  href: string;
+  label: string;
+  icon: React.ReactNode;
+  exact?: boolean;
+}
+
+const NAV_ITEMS: NavItem[] = [
+  {
+    href: '/dashboard/agent/marketing/management',
+    label: 'Overview',
+    icon: <Home className="w-5 h-5" />,
+    exact: true,
+  },
+  {
+    href: '/dashboard/agent/marketing/management/tasks',
+    label: 'Tasks',
+    icon: <CheckSquare className="w-5 h-5" />,
+  },
+  {
+    href: '/dashboard/agent/marketing/management/calendar',
+    label: 'Calendar',
+    icon: <Calendar className="w-5 h-5" />,
+  },
+  {
+    href: '/dashboard/agent/marketing/management/clients',
+    label: 'Clients',
+    icon: <Users className="w-5 h-5" />,
+  },
+  {
+    href: '/dashboard/agent/marketing/management/notes',
+    label: 'Notes',
+    icon: <StickyNote className="w-5 h-5" />,
+  },
+];
+
+function useIsActive(href: string, exact?: boolean) {
+  const pathname = usePathname();
+  if (!pathname) return false;
+  if (exact) return pathname === href || pathname === href + '/';
+  return pathname === href || pathname.startsWith(href + '/');
+}
+
+function NavLink({ item, collapsed, onClick }: { item: NavItem; collapsed: boolean; onClick?: () => void }) {
+  const active = useIsActive(item.href, item.exact);
+
+  return (
+    <Link
+      href={item.href}
+      onClick={onClick}
+      className={cn(
+        'relative flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all',
+        collapsed ? 'justify-center' : '',
+        active
+          ? 'nav-item-active bg-accent-light text-accent border-l-2 border-accent -ml-[2px] pl-[calc(0.75rem+2px)]'
+          : 'text-secondary hover:bg-surface-subtle hover:text-primary'
+      )}
+      aria-current={active ? 'page' : undefined}
+    >
+      <span className={cn('flex-shrink-0', active ? 'text-accent' : 'text-secondary')}>
+        {item.icon}
+      </span>
+      {!collapsed && <span className="flex-1 truncate">{item.label}</span>}
+    </Link>
+  );
+}
+
+export function ManagementSidebar() {
+  const [isCollapsed, setIsCollapsed] = useState(false);
+  const [isMobileOpen, setIsMobileOpen] = useState(false);
+  const drawerRef = useRef<HTMLDivElement>(null);
+
+  // Hydrate collapse state from localStorage
+  useEffect(() => {
+    const saved = localStorage.getItem('management-sidebar-collapsed');
+    if (saved !== null) {
+      setIsCollapsed(JSON.parse(saved));
+    }
+  }, []);
+
+  // Persist collapse state to localStorage
+  const toggleCollapse = () => {
+    setIsCollapsed((prev) => {
+      const next = !prev;
+      localStorage.setItem('management-sidebar-collapsed', JSON.stringify(next));
+      return next;
+    });
+  };
+
+  // Focus trap for mobile drawer
+  useEffect(() => {
+    if (!isMobileOpen || !drawerRef.current) return;
+
+    const focusable = drawerRef.current.querySelectorAll<HTMLElement>(
+      'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])'
+    );
+    const first = focusable[0];
+    const last = focusable[focusable.length - 1];
+
+    first?.focus();
+
+    const onKeyDown = (e: KeyboardEvent) => {
+      if (e.key !== 'Tab') return;
+      if (e.shiftKey) {
+        if (document.activeElement === first) {
+          e.preventDefault();
+          last?.focus();
+        }
+      } else {
+        if (document.activeElement === last) {
+          e.preventDefault();
+          first?.focus();
+        }
+      }
+    };
+
+    document.addEventListener('keydown', onKeyDown);
+    return () => document.removeEventListener('keydown', onKeyDown);
+  }, [isMobileOpen]);
+
+  const sidebarContent = (collapsed: boolean, onItemClick?: () => void) => (
+    <div className="flex flex-col h-full">
+      {/* Header */}
+      <div className={cn(
+        'flex items-center h-14 border-b border-border flex-shrink-0',
+        collapsed ? 'justify-center px-2' : 'px-4'
+      )}>
+        {!collapsed && (
+          <span className="text-lg font-semibold font-display text-primary">Command Centre</span>
+        )}
+      </div>
+
+      {/* Return to Dashboard */}
+      {!collapsed && (
+        <div className="px-3 pt-3 pb-1">
+          <Link
+            href="/dashboard/agent/marketing/"
+            onClick={onItemClick}
+            className="flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg border border-border text-secondary hover:bg-surface-subtle hover:text-primary transition-all"
+          >
+            <ArrowLeft className="w-4 h-4 flex-shrink-0" />
+            <span>Return to Dashboard</span>
+          </Link>
+        </div>
+      )}
+
+      {/* Nav items */}
+      <nav
+        id={SIDEBAR_ID}
+        className={cn('flex-1 overflow-y-auto py-3', collapsed ? 'px-2' : 'px-3')}
+      >
+        <div className="space-y-1">
+          {NAV_ITEMS.map((item) => (
+            <NavLink key={item.href} item={item} collapsed={collapsed} onClick={onItemClick} />
+          ))}
+        </div>
+      </nav>
+
+      {/* Collapse toggle */}
+      <div className={cn('border-t border-border p-2', collapsed ? 'flex justify-center' : '')}>
+        <button
+          onClick={toggleCollapse}
+          aria-expanded={isCollapsed}
+          aria-controls={SIDEBAR_ID}
+          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
+          className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-secondary hover:bg-surface-subtle hover:text-primary transition-all w-full justify-center md:justify-start"
+        >
+          {isCollapsed ? (
+            <ChevronRight className="w-5 h-5 flex-shrink-0" />
+          ) : (
+            <>
+              <ChevronLeft className="w-5 h-5 flex-shrink-0" />
+              <span>Collapse</span>
+            </>
+          )}
+        </button>
+      </div>
+    </div>
+  );
+
+  return (
+    <>
+      {/* Mobile hamburger button — visible below md */}
+      <div className="md:hidden fixed top-4 left-4 z-50">
+        <button
+          onClick={() => setIsMobileOpen(true)}
+          aria-label="Open menu"
+          className="bg-surface p-2 rounded-lg shadow-surface border border-border"
+        >
+          <Menu className="w-6 h-6" />
+        </button>
+      </div>
+
+      {/* Desktop sidebar */}
+      <aside
+        id={SIDEBAR_ID + '-desktop'}
+        className={cn(
+          'hidden md:flex flex-col fixed left-0 top-0 h-screen bg-surface border-r border-border z-40 transition-all duration-200',
+          isCollapsed ? 'w-16' : 'w-60'
+        )}
+      >
+        {sidebarContent(isCollapsed)}
+      </aside>
+
+      {/* Mobile drawer */}
+      {isMobileOpen && (
+        <>
+          <div
+            data-testid="mobile-backdrop"
+            className="fixed inset-0 bg-black/40 z-40 md:hidden"
+            onClick={() => setIsMobileOpen(false)}
+          />
+          <div
+            ref={drawerRef}
+            role="dialog"
+            aria-modal="true"
+            aria-label="Navigation menu"
+            className="fixed left-0 top-0 h-screen w-60 bg-surface border-r border-border z-50 md:hidden flex flex-col"
+          >
+            {/* Close button */}
+            <div className="flex justify-end p-2 border-b border-border">
+              <button
+                onClick={() => setIsMobileOpen(false)}
+                aria-label="Close menu"
+                className="p-2 rounded-lg hover:bg-surface-subtle transition-colors"
+              >
+                <X className="w-5 h-5" />
+              </button>
+            </div>
+            {sidebarContent(false, () => setIsMobileOpen(false))}
+          </div>
+        </>
+      )}
+    </>
+  );
+}
+
+export default ManagementSidebar;
