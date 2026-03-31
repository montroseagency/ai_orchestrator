# Section 07: Entry Animation (`management/template.tsx`)

## Overview

Add a fade-in + slide-up animation on portal page navigation using Next.js `template.tsx` (remounts on every nav within its route segment).

**File created:** `client/app/dashboard/agent/marketing/management/template.tsx`

**Dependencies:** Section 05 ✓

---

## Actual Implementation

```tsx
'use client'
import { motion } from 'framer-motion'

export default function ManagementTemplate({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, ease: 'easeOut' }}
    >
      {children}
    </motion.div>
  )
}
```

Entry-only animation. No exit animation (avoids Next.js internals coupling). framer-motion@11 was already installed.

Code review: Approved without changes.

**Test file:** `client/app/dashboard/agent/marketing/management/template.test.tsx` — 2 tests, all pass
