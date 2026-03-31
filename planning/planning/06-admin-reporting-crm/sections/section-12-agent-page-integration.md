# Section 12: Agent Client Page Integration

## Overview

Wire the `ClientDetailHub` component (built in section 08) into the existing marketing and developer agent client detail pages. Both pages currently render a simple hand-rolled layout with contact info, a stats row, a recent-items list, and quick action buttons. This section replaces those layouts with `<ClientDetailHub />`, delegating all tab/data rendering to the hub.

**Dependency:** Section 08 (`ClientDetailHub` component) must be complete before this section can be implemented.

---

## Files to Modify / Create

| Action | Path |
|--------|------|
| Modify | `client/app/dashboard/agent/marketing/clients/[id]/page.tsx` |
| Modify | `client/app/dashboard/agent/developer/clients/[id]/page.tsx` |
| Create | `client/app/dashboard/agent/marketing/clients/[id]/__tests__/page.test.tsx` |
| Create | `client/app/dashboard/agent/developer/clients/[id]/__tests__/page.test.tsx` |

---

## Tests First

Both test files follow the same pattern. Create them before modifying the pages.

### `client/app/dashboard/agent/marketing/clients/[id]/__tests__/page.test.tsx`

```typescript
import { renderWithQuery } from '@/test-utils/scheduling';
import { screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';

// Mock ClientDetailHub to avoid rendering the full component tree
vi.mock('@/components/portal/crm/ClientDetailHub', () => ({
  ClientDetailHub: ({ clientId, agentType }: { clientId: string; agentType: string }) => (
    <div data-testid="client-detail-hub" data-client-id={clientId} data-agent-type={agentType} />
  ),
}));

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useParams: () => ({ id: 'test-client-123' }),
  useRouter: () => ({ back: vi.fn(), push: vi.fn() }),
}));

// Mock api.getClient
vi.mock('@/lib/api', () => ({
  default: {
    getClient: vi.fn().mockResolvedValue({ id: 'test-client-123', name: 'Acme Corp' }),
  },
}));

describe('MarketingClientDetailPage', () => {
  it('renders ClientDetailHub with agentType="marketing"', async () => {
    /**
     * Renders the page and asserts that ClientDetailHub receives
     * the correct agentType prop for marketing agents.
     */
  });

  it('passes clientId from route params to ClientDetailHub', async () => {
    /**
     * Asserts that ClientDetailHub receives clientId="test-client-123"
     * matching the mocked useParams return value.
     */
  });

  it('shows loading state while client data is fetching', () => {
    /**
     * Mock api.getClient to return a never-resolving promise.
     * Assert a loading spinner or skeleton is visible.
     */
  });

  it('shows error state if client fetch fails', async () => {
    /**
     * Mock api.getClient to reject.
     * Assert an error/empty state is rendered with a back-to-clients link.
     */
  });
});
```

### `client/app/dashboard/agent/developer/clients/[id]/__tests__/page.test.tsx`

```typescript
import { renderWithQuery } from '@/test-utils/scheduling';
import { screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';

vi.mock('@/components/portal/crm/ClientDetailHub', () => ({
  ClientDetailHub: ({ clientId, agentType }: { clientId: string; agentType: string }) => (
    <div data-testid="client-detail-hub" data-client-id={clientId} data-agent-type={agentType} />
  ),
}));

vi.mock('next/navigation', () => ({
  useParams: () => ({ id: 'test-client-456' }),
  useRouter: () => ({ back: vi.fn(), push: vi.fn() }),
}));

vi.mock('@/lib/api', () => ({
  default: {
    getClient: vi.fn().mockResolvedValue({ id: 'test-client-456', name: 'Dev Client' }),
  },
}));

describe('DeveloperClientDetailPage', () => {
  it('renders ClientDetailHub with agentType="developer"', async () => {
    /**
     * Renders the page and asserts ClientDetailHub receives agentType="developer".
     */
  });

  it('passes clientId from route params to ClientDetailHub', async () => {
    /**
     * Asserts ClientDetailHub receives clientId="test-client-456".
     */
  });

  it('shows loading state while client data is fetching', () => {
    /**
     * Mock api.getClient to return a never-resolving promise.
     * Assert a loading spinner or skeleton is visible.
     */
  });

  it('shows error state if client fetch fails', async () => {
    /**
     * Mock api.getClient to reject.
     * Assert an error/empty state is rendered with back-to-clients link pointing
     * to /dashboard/agent/developer/clients.
     */
  });
});
```

---

## Implementation

### What the current pages look like

Both pages follow the same structure:

1. `useParams()` to get `clientId`
2. `useQuery` for `api.getClient(clientId)` — loading/error guards
3. A secondary `useQuery` for supplementary data (posts for marketing, website projects for developer)
4. A hand-rolled JSX layout: header row, contact info + stats grid, recent items list, quick actions grid

### What to change

Replace step 3 and 4 entirely. The `ClientDetailHub` component owns all secondary data fetching and all tab content. The page file's only job after this change is:

- Extract `clientId` from params
- Guard loading and error states (keep existing spinners and `EmptyState` — they are fine as-is)
- Render `<ClientDetailHub clientId={clientId} agentType="marketing"|"developer" />`

**Do not** remove the loading and error guards. They provide the initial client-not-found protection before `ClientDetailHub` mounts.

The secondary `useQuery` calls (posts for marketing, projects for developer) should be removed from the page file — `ClientDetailHub` and its tab components handle all secondary data internally.

---

### Marketing Agent Page

**File:** `client/app/dashboard/agent/marketing/clients/[id]/page.tsx`

**Current exports:** `MarketingClientDetailPage` (default export)

**After the change, the page should:**

- Import `ClientDetailHub` from `@/components/portal/crm/ClientDetailHub`
- Keep `useQuery` for `api.getClient(clientId)` (for the loading/error gate)
- Remove the `useQuery` for `api.getMarketingPosts(...)` (no longer needed at this level)
- Replace the full JSX return body (after the loading/error guards) with:

```tsx
return <ClientDetailHub clientId={clientId} agentType="marketing" />;
```

- Keep all existing imports that are still used by loading/error states (`EmptyState`, `Surface`, `Users`, `ArrowLeft`, `Button`, etc. — trim any that become unused after removing the old layout)

**Imports to remove** (become unused): `Badge`, `Mail`, `Phone`, `Building`, `Calendar`, `FileText`, `MessageSquare`, `Lightbulb`, `TrendingUp`, `Instagram`, `Youtube`, `Facebook`

---

### Developer Agent Page

**File:** `client/app/dashboard/agent/developer/clients/[id]/page.tsx`

**Current exports:** `DeveloperClientDetailPage` (default export)

**After the change:**

- Import `ClientDetailHub` from `@/components/portal/crm/ClientDetailHub`
- Keep `useQuery` for `api.getClient(clientId)` (loading/error gate)
- Remove the `useQuery` for `api.request('/website-projects/...')` (no longer needed at this level)
- Replace the JSX return body (after guards) with:

```tsx
return <ClientDetailHub clientId={clientId} agentType="developer" />;
```

- Trim unused imports after removing the old layout

**Imports to remove** (become unused): `Badge`, `Mail`, `Phone`, `Building`, `Calendar`, `Globe`, `FolderOpen`, `Code`

---

### ClientDetailHub import path

Section 08 places the component at:

```
client/components/portal/crm/ClientDetailHub.tsx
```

Import as:

```typescript
import { ClientDetailHub } from '@/components/portal/crm/ClientDetailHub';
```

(Named export — section 08 uses named export convention consistent with other portal components.)

---

## Minimal Page Shape After Change

Both pages will look structurally identical after the refactor. The marketing version:

```typescript
'use client';

import { useRouter, useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { Surface } from '@/components/ui/Surface';
import { EmptyState } from '@/components/ui/empty-state';
import { Users } from 'lucide-react';
import { ClientDetailHub } from '@/components/portal/crm/ClientDetailHub';

export default function MarketingClientDetailPage() {
  const router = useRouter();
  const params = useParams();
  const clientId = params.id as string;

  const { isLoading, error } = useQuery({
    queryKey: ['client', clientId],
    queryFn: () => api.getClient(clientId),
  });

  if (isLoading) {
    // existing loading spinner
  }

  if (error) {
    // existing EmptyState with back link
  }

  return <ClientDetailHub clientId={clientId} agentType="marketing" />;
}
```

The developer page is identical except the function name, `agentType="developer"`, and the back-link target in the error state.

---

## Checklist

- [ ] Write test file for marketing page
- [ ] Write test file for developer page
- [ ] Remove secondary `useQuery` (posts) from marketing page
- [ ] Remove secondary `useQuery` (projects) from developer page
- [ ] Add `ClientDetailHub` import to both pages
- [ ] Replace old JSX layout bodies with `<ClientDetailHub />` in both pages
- [ ] Remove now-unused imports from both pages
- [ ] Run `npx vitest run` — all 4 new tests pass
- [ ] Run TypeScript check (`npx tsc --noEmit`) — no new errors
