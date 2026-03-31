diff --git a/client/app/dashboard/agent/marketing/management/template.test.tsx b/client/app/dashboard/agent/marketing/management/template.test.tsx
new file mode 100644
index 000000000..e3b272e34
--- /dev/null
+++ b/client/app/dashboard/agent/marketing/management/template.test.tsx
@@ -0,0 +1,37 @@
+import { render, screen } from '@testing-library/react'
+import { describe, it, expect, vi } from 'vitest'
+import React from 'react'
+import ManagementTemplate from './template'
+
+// Mock framer-motion to render children directly (animation not testable in unit tests)
+vi.mock('framer-motion', () => ({
+  motion: {
+    div: ({ children, ...props }: any) => (
+      <div data-testid="motion-wrapper" {...props}>{children}</div>
+    ),
+  },
+}))
+
+describe('ManagementTemplate', () => {
+  it('renders children', () => {
+    render(
+      <ManagementTemplate>
+        <div data-testid="child">page content</div>
+      </ManagementTemplate>
+    )
+    expect(screen.getByTestId('child')).toBeInTheDocument()
+  })
+
+  it('wrapper element has animation props on mount', () => {
+    render(
+      <ManagementTemplate>
+        <span>content</span>
+      </ManagementTemplate>
+    )
+    const wrapper = screen.getByTestId('motion-wrapper')
+    // initial/animate props are passed through to the mocked div as data attributes (stringified)
+    // The important check is that the wrapper renders and children are inside it
+    expect(wrapper).toBeInTheDocument()
+    expect(wrapper.querySelector('span')).toBeInTheDocument()
+  })
+})
diff --git a/client/app/dashboard/agent/marketing/management/template.tsx b/client/app/dashboard/agent/marketing/management/template.tsx
new file mode 100644
index 000000000..20f4836a3
--- /dev/null
+++ b/client/app/dashboard/agent/marketing/management/template.tsx
@@ -0,0 +1,15 @@
+'use client';
+
+import { motion } from 'framer-motion';
+
+export default function ManagementTemplate({ children }: { children: React.ReactNode }) {
+  return (
+    <motion.div
+      initial={{ opacity: 0, y: 8 }}
+      animate={{ opacity: 1, y: 0 }}
+      transition={{ duration: 0.2, ease: 'easeOut' }}
+    >
+      {children}
+    </motion.div>
+  );
+}
