"""
Message Protocol — Structured messages for inter-agent communication.

Defines message types, dataclasses, and factory functions for agents
to communicate constraints, questions, suggestions, and feedback.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any
import uuid


class MessageType(Enum):
    """Types of messages agents can send to each other."""
    # General communication
    QUESTION = "question"
    CONSTRAINT = "constraint"
    SUGGESTION = "suggestion"

    # Specialized communication
    FEASIBILITY_CHECK = "feasibility_check"
    DESIGN_FEEDBACK = "design_feedback"
    IMPLEMENTATION_QUESTION = "implementation_question"

    # Coordination
    HANDOFF = "handoff"
    STATUS_UPDATE = "status_update"
    ESCALATION = "escalation"


class Priority(Enum):
    """Message priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class ResponseStatus(Enum):
    """Status of a message response."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    NEEDS_CLARIFICATION = "needs_clarification"
    ESCALATED = "escalated"


@dataclass
class AgentMessage:
    """
    A message from one agent to another.

    Messages are structured to allow agents to communicate needs,
    constraints, and suggestions without losing context.
    """
    # Core fields
    message_id: str
    from_agent: str
    to_agent: str
    message_type: MessageType
    content: str

    # Optional fields
    priority: Priority = Priority.NORMAL
    context: Optional[str] = None  # Additional context
    requires_response: bool = True
    timeout_seconds: Optional[float] = None

    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    session_id: Optional[str] = None
    thread_id: Optional[str] = None  # For multi-turn conversations

    def to_prompt_format(self) -> str:
        """
        Format message for injection into agent prompt.

        Returns markdown-formatted message for LLM consumption.
        """
        priority_marker = ""
        if self.priority == Priority.HIGH:
            priority_marker = "[HIGH] "
        elif self.priority == Priority.CRITICAL:
            priority_marker = "[CRITICAL] "

        type_label = self.message_type.value.replace("_", " ").title()

        lines = [
            f"### {priority_marker}{type_label} from {self.from_agent}",
            "",
            self.content,
        ]

        if self.context:
            lines.extend(["", f"**Context:** {self.context}"])

        if self.requires_response:
            lines.extend(["", "_Response required._"])

        return "\n".join(lines)


@dataclass
class AgentResponse:
    """
    A response to an AgentMessage.
    """
    response_id: str
    message_id: str  # ID of message being responded to
    from_agent: str
    to_agent: str
    status: ResponseStatus
    content: str

    # Optional fields
    clarification_needed: Optional[str] = None
    alternative_proposal: Optional[str] = None
    confidence: float = 1.0

    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_prompt_format(self) -> str:
        """Format response for prompt injection."""
        status_emoji = {
            ResponseStatus.ACCEPTED: "",
            ResponseStatus.REJECTED: "",
            ResponseStatus.NEEDS_CLARIFICATION: "",
            ResponseStatus.ESCALATED: "",
            ResponseStatus.PENDING: "",
        }.get(self.status, "")

        lines = [
            f"### Response from {self.from_agent} {status_emoji}",
            f"**Status:** {self.status.value}",
            "",
            self.content,
        ]

        if self.clarification_needed:
            lines.extend(["", f"**Needs clarification:** {self.clarification_needed}"])

        if self.alternative_proposal:
            lines.extend(["", f"**Alternative proposal:** {self.alternative_proposal}"])

        return "\n".join(lines)


@dataclass
class NegotiationRound:
    """A single round in a multi-turn negotiation."""
    round_number: int
    initiator_message: AgentMessage
    responder_response: Optional[AgentResponse] = None
    resolved: bool = False


@dataclass
class NegotiationResult:
    """Result of a multi-round negotiation between agents."""
    negotiation_id: str
    initiator: str
    responder: str
    topic: str
    rounds: list[NegotiationRound] = field(default_factory=list)
    final_status: ResponseStatus = ResponseStatus.PENDING
    resolution: Optional[str] = None
    escalated: bool = False

    def summary(self) -> str:
        """Generate a summary of the negotiation."""
        lines = [
            f"## Negotiation: {self.topic}",
            f"Between: {self.initiator} <-> {self.responder}",
            f"Status: {self.final_status.value}",
            f"Rounds: {len(self.rounds)}",
        ]

        if self.resolution:
            lines.append(f"Resolution: {self.resolution}")

        if self.escalated:
            lines.append("*Escalated to Conductor*")

        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# Factory Functions
# ═══════════════════════════════════════════════════════════════

def _generate_id() -> str:
    """Generate a unique message/response ID."""
    return str(uuid.uuid4())[:8]


def create_question(
    from_agent: str,
    to_agent: str,
    question: str,
    context: Optional[str] = None,
    priority: Priority = Priority.NORMAL,
    session_id: Optional[str] = None,
) -> AgentMessage:
    """
    Create a question message from one agent to another.

    Example:
        msg = create_question(
            from_agent="implementer",
            to_agent="planner",
            question="Should the validation happen client-side or server-side?",
            context="Working on the form submission feature",
        )
    """
    return AgentMessage(
        message_id=_generate_id(),
        from_agent=from_agent,
        to_agent=to_agent,
        message_type=MessageType.QUESTION,
        content=question,
        context=context,
        priority=priority,
        session_id=session_id,
        requires_response=True,
    )


def create_constraint(
    from_agent: str,
    to_agent: str,
    constraint: str,
    context: Optional[str] = None,
    priority: Priority = Priority.HIGH,
    session_id: Optional[str] = None,
) -> AgentMessage:
    """
    Create a constraint message to inform another agent of a requirement.

    Example:
        msg = create_constraint(
            from_agent="reviewer",
            to_agent="implementer",
            constraint="Must handle the loading state before fetching data",
            context="Review finding from previous attempt",
        )
    """
    return AgentMessage(
        message_id=_generate_id(),
        from_agent=from_agent,
        to_agent=to_agent,
        message_type=MessageType.CONSTRAINT,
        content=constraint,
        context=context,
        priority=priority,
        session_id=session_id,
        requires_response=False,  # Constraints don't require explicit response
    )


def create_suggestion(
    from_agent: str,
    to_agent: str,
    suggestion: str,
    context: Optional[str] = None,
    session_id: Optional[str] = None,
) -> AgentMessage:
    """
    Create a suggestion message with a non-binding recommendation.

    Example:
        msg = create_suggestion(
            from_agent="creative_brain",
            to_agent="implementer",
            suggestion="Consider using a skeleton loader for better UX",
        )
    """
    return AgentMessage(
        message_id=_generate_id(),
        from_agent=from_agent,
        to_agent=to_agent,
        message_type=MessageType.SUGGESTION,
        content=suggestion,
        context=context,
        priority=Priority.NORMAL,
        session_id=session_id,
        requires_response=False,
    )


def create_feasibility_check(
    from_agent: str,
    to_agent: str,
    proposal: str,
    constraints: list[str],
    session_id: Optional[str] = None,
) -> AgentMessage:
    """
    Create a feasibility check message to validate a proposal.

    Example:
        msg = create_feasibility_check(
            from_agent="planner",
            to_agent="implementer",
            proposal="Use WebSocket for real-time updates",
            constraints=["Must work with existing Django backend", "No new dependencies"],
        )
    """
    content = f"**Proposal:** {proposal}\n\n"
    content += "**Constraints:**\n"
    for constraint in constraints:
        content += f"- {constraint}\n"
    content += "\nIs this feasible within the given constraints?"

    return AgentMessage(
        message_id=_generate_id(),
        from_agent=from_agent,
        to_agent=to_agent,
        message_type=MessageType.FEASIBILITY_CHECK,
        content=content,
        priority=Priority.HIGH,
        session_id=session_id,
        requires_response=True,
    )


def create_design_feedback(
    from_agent: str,
    to_agent: str,
    feedback: str,
    severity: str = "suggestion",
    affected_component: Optional[str] = None,
    session_id: Optional[str] = None,
) -> AgentMessage:
    """
    Create design feedback from creative_brain to implementer.

    Example:
        msg = create_design_feedback(
            from_agent="creative_brain",
            to_agent="implementer",
            feedback="The button spacing should follow the 8px grid system",
            severity="requirement",
            affected_component="LoginForm",
        )
    """
    content = f"**Feedback:** {feedback}\n"
    content += f"**Severity:** {severity}\n"
    if affected_component:
        content += f"**Component:** {affected_component}"

    priority = Priority.HIGH if severity == "requirement" else Priority.NORMAL

    return AgentMessage(
        message_id=_generate_id(),
        from_agent=from_agent,
        to_agent=to_agent,
        message_type=MessageType.DESIGN_FEEDBACK,
        content=content,
        priority=priority,
        session_id=session_id,
        requires_response=severity == "requirement",
    )


def create_response(
    message: AgentMessage,
    from_agent: str,
    status: ResponseStatus,
    content: str,
    clarification_needed: Optional[str] = None,
    alternative_proposal: Optional[str] = None,
    confidence: float = 1.0,
) -> AgentResponse:
    """
    Create a response to an AgentMessage.

    Example:
        response = create_response(
            message=question_msg,
            from_agent="planner",
            status=ResponseStatus.ACCEPTED,
            content="Client-side validation is preferred for UX",
        )
    """
    return AgentResponse(
        response_id=_generate_id(),
        message_id=message.message_id,
        from_agent=from_agent,
        to_agent=message.from_agent,
        status=status,
        content=content,
        clarification_needed=clarification_needed,
        alternative_proposal=alternative_proposal,
        confidence=confidence,
    )


# ═══════════════════════════════════════════════════════════════
# Utility Functions
# ═══════════════════════════════════════════════════════════════

def format_messages_for_prompt(messages: list[AgentMessage]) -> str:
    """
    Format multiple messages for injection into an agent's prompt.

    Args:
        messages: List of messages to format

    Returns:
        Markdown-formatted string with all messages
    """
    if not messages:
        return ""

    parts = ["## Pending Messages\n"]
    for msg in messages:
        parts.append(msg.to_prompt_format())
        parts.append("")

    return "\n".join(parts)


def group_messages_by_type(
    messages: list[AgentMessage]
) -> dict[MessageType, list[AgentMessage]]:
    """Group messages by their type."""
    grouped: dict[MessageType, list[AgentMessage]] = {}
    for msg in messages:
        if msg.message_type not in grouped:
            grouped[msg.message_type] = []
        grouped[msg.message_type].append(msg)
    return grouped


def filter_messages_by_priority(
    messages: list[AgentMessage],
    min_priority: Priority = Priority.NORMAL,
) -> list[AgentMessage]:
    """Filter messages to only include those at or above a priority level."""
    priority_order = [Priority.LOW, Priority.NORMAL, Priority.HIGH, Priority.CRITICAL]
    min_index = priority_order.index(min_priority)

    return [
        msg for msg in messages
        if priority_order.index(msg.priority) >= min_index
    ]
