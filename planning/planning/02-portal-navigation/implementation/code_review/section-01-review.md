# Code Review: section-01-gateway-link

## Summary

One functional change: `href` in `sidebar.tsx` for marketing agent "Command Center" updated from `/dashboard/agent/marketing/schedule` to `/dashboard/agent/marketing/management/`, plus Vitest + RTL infrastructure bootstrapped.

## Issues

**Medium — Trailing slash inconsistency**
New href `/dashboard/agent/marketing/management/` has a trailing slash; no other nav items do. Without `trailingSlash: true` in next.config, this causes a 308 redirect. Should normalize to `/dashboard/agent/marketing/management` to match other nav items.

**Medium — Regression test tightly coupled to developer href**
Test 2 asserts developer "Command Center" still points to `/dashboard/agent/developer/schedule`. If that href is later intentionally changed, the test will fail for the wrong reason. Needs a clarifying comment.

**Low — `waitFor` vs `findBy` inconsistency across tests**
Test 1 uses `waitFor(() => getByRole(...))`, test 2 uses `findByRole`. Both work; the inconsistency is mildly confusing. Could unify to `findByRole` + assertion.

**Low — `@testing-library/user-event` installed but unused**
Fine to keep if more tests are planned; otherwise an unused dependency.

**Low — `globals: true` in vitest.config not reflected in tsconfig**
Without `"types": ["vitest/globals"]` in tsconfig, TypeScript may complain about undeclared globals in CI.

## Verdict

**Approve with minor fixes** — fix trailing slash before commit; rest are low-priority polish.
