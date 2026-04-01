"""
Coordination module — Inter-agent communication and negotiation.

Provides:
- Structured message types for agent communication
- Message routing and queuing
- Multi-round negotiation support
- Conductor escalation for unresolved conflicts
"""

from .messages import (
    # Enums
    MessageType,
    Priority,
    ResponseStatus,
    # Dataclasses
    AgentMessage,
    AgentResponse,
    NegotiationRound,
    NegotiationResult,
    # Factory functions
    create_question,
    create_constraint,
    create_suggestion,
    create_feasibility_check,
    create_design_feedback,
    create_response,
    # Utility functions
    format_messages_for_prompt,
    group_messages_by_type,
    filter_messages_by_priority,
)

from .router import (
    RouterConfig,
    MessageRouter,
    MessageHandler,
    get_router,
    reset_router,
)

__all__ = [
    # Message types
    "MessageType",
    "Priority",
    "ResponseStatus",
    # Message dataclasses
    "AgentMessage",
    "AgentResponse",
    "NegotiationRound",
    "NegotiationResult",
    # Factory functions
    "create_question",
    "create_constraint",
    "create_suggestion",
    "create_feasibility_check",
    "create_design_feedback",
    "create_response",
    # Utility functions
    "format_messages_for_prompt",
    "group_messages_by_type",
    "filter_messages_by_priority",
    # Router
    "RouterConfig",
    "MessageRouter",
    "MessageHandler",
    "get_router",
    "reset_router",
]
