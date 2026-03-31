---
description: Run only the Reviewer agent on recently changed files — quick quality check without full pipeline
---

# /review-only — Quick Review Pass

Run the Reviewer agent only, against files you specify or recently modified files.

**Example:** `/review-only client/components/agent/TaskBoard.tsx`

---

## Step 1: Load Context

Read:
- `c:\Users\User\Documents\GitHub\agentic_workflow\_vibecoding_brain\AGENTS.md`
- `c:\Users\User\Documents\GitHub\agentic_workflow\_vibecoding_brain\agents\reviewer.md`

---

## Step 2: Read Target Files

If the user provided file paths, read those files.
Otherwise, ask: "Which files would you like me to review?"

---

## Step 3: Review

Act as the Reviewer following the reviewer.md system prompt.
Produce a complete review.md covering:
- Correctness
- AGENTS.md architecture compliance
- Design system compliance (if frontend)
- TypeScript type safety
- Security

---

## Step 4: Report

Show the review to the user with PASS/FAIL verdict.
If FAIL, offer to fix the issues immediately.
