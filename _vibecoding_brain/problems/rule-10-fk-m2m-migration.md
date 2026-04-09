## RULE-10: [FULLSTACK] FK-to-M2M Migration Must Update All Frontend References

**Why:** A model field was changed from FK (singular, e.g., `specialization`) to M2M (plural, e.g., `specializations: [...]`). The backend serializer was updated, but the frontend type definition still had `specialization: string`. All form submissions using the singular field name silently sent wrong data. Multi-specialization agents couldn't round-trip through the edit form — data loss on every update. Root cause: contract verification happened late (after implementation), after the frontend had already been built against the old type shape.

**How to apply:**
1. When migrating a model field from FK to M2M (or any structural shape change), treat it as a breaking API contract change — update ALL of these together:
   - Django model field definition
   - DRF serializer field (FK → `ManyRelatedField` or `PrimaryKeyRelatedField(many=True)`)
   - Frontend type in `client/lib/types.ts` (singular `string` → `string[]` or similar)
   - All components that read or write that field (forms, display tables, detail views)
   - API method in `client/lib/api.ts` — verify request body shape matches new serializer expectations
2. Use the code-reviewer to verify all references are updated before marking the task done — search for the old field name with `grep -r "specialization" client/` (singular form) after migrating to plural
3. Test round-trip: create → edit → save → verify all values persisted, especially for multi-value cases
4. Never assume renaming a field in the serializer is isolated to the backend — grep the entire codebase for the old field name before shipping

This applies to any field shape change: FK→M2M, string→array, integer→object, etc.
