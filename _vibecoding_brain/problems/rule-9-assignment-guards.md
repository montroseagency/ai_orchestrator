## RULE-9: [BACKEND] Assignment Guard Pattern for Delete Operations

**Why:** `DELETE /admin/agents/{id}/` always succeeded even when the agent was assigned to active clients. This allowed deleting agents with active work, creating data orphaning risk. Root cause: the new delete view wasn't aligned with the existing assignment-check pattern already established in `client_assignment_views.py`. The guard pattern existed but wasn't applied consistently.

**How to apply:** Before allowing deletion of any entity that can be assigned to other records, check for active assignments in two places:
1. `ClientTeamAssignment` records where `is_active=True` and the entity FK matches
2. Direct FK assignments on the Client model (e.g., `marketing_agent`, `website_agent`, or equivalent fields)

```python
# Example guard pattern (follow existing client_assignment_views.py implementation)
active_assignments = ClientTeamAssignment.objects.filter(agent=agent, is_active=True)
direct_assignments = Client.objects.filter(
    Q(marketing_agent=agent) | Q(website_agent=agent)
)
if active_assignments.exists() or direct_assignments.exists():
    return Response(
        {"error": "Cannot delete agent with active client assignments."},
        status=status.HTTP_400_BAD_REQUEST
    )
```

3. Return HTTP 400 (not 403 or 404) with a descriptive error message listing the blocking assignments
4. Review `client_assignment_views.py` before writing any new delete view for entities with assignment relationships — follow the same guard pattern exactly

This applies to agents, clients, or any entity that participates in assignment relationships.
