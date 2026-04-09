## RULE-11: [FRONTEND] Destructive Actions Must Be Enforced in UI, Not Just Warned

**Why:** A delete confirmation dialog showed warning text ("This agent has active clients") but the delete button remained enabled. Users could still accidentally delete agents with active assignments. Root cause: the form state logic was incomplete — only the warning message was rendered, but the button wasn't disabled and the mutation wasn't blocked. The safety guard was purely informational.

**How to apply:** For any destructive action with preconditions (entity has dependencies, active assignments, unsaved changes, etc.):
1. **Disable the action button** when the precondition is unmet — `disabled={hasActiveAssignments}` — not just hidden or styled differently
2. **Show inline error/block message** explaining why the action is blocked, not just a generic warning
3. **Prevent mutation submission** — if the button is somehow triggered (keyboard, race condition), guard at the mutation call site too:
   ```tsx
   const handleDelete = () => {
     if (hasActiveAssignments) return; // guard at call site
     deleteMutation.mutate(agentId);
   };
   ```
4. **Test the disabled state** — confirm the button has `disabled` attribute in the rendered DOM when preconditions aren't met
5. Warning text alone (yellow banner, tooltip, etc.) is NOT sufficient. It must be enforced, not just communicated.

This applies to: delete actions, archive actions, bulk operations, irreversible state changes, and any form submission that would cause data loss.
