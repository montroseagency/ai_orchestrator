## RULE-8: [BACKEND + FRONTEND] DRF Serializer update() Must Handle Related Model Fields Explicitly

**Why:** `PATCH /admin/agents/` with `first_name` or `last_name` silently ignored those fields — data appeared to save successfully but never persisted to the database. Root cause: the serializer used `setattr(agent_instance, 'first_name', value)` but `first_name`/`last_name` belong to the related `User` model, not the `Agent` model. Django silently discarded the setattr call with no error.

**How to apply:**
1. When writing `serializer.update()` for a model with related objects (FK or OneToOne), identify which fields belong to the related model vs the primary model
2. For related model fields, explicitly fetch and update the related instance:
   ```python
   user = instance.user  # or instance.profile, etc.
   user.first_name = validated_data.pop('first_name', user.first_name)
   user.save()
   ```
3. Always call `.save()` on the related instance separately — changes to it won't be saved by saving the primary instance
4. Test with partial PATCH requests that include only related-model fields to confirm persistence
5. On the frontend, verify that form submissions map field names to the correct request body keys — if the serializer accepts `first_name` at the top level but stores it via a nested model, integration tests should cover the full round-trip

This applies to any serializer where `Meta.fields` includes fields from a related model (via `source=` or nested logic).
