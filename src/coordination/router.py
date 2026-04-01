"""
Message Router — Routes messages between agents and handles negotiations.

Provides message queuing, routing, multi-round negotiation support,
and escalation to the Conductor when agents can't reach agreement.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Callable, Any, Awaitable
import uuid

from .messages import (
    AgentMessage,
    AgentResponse,
    NegotiationRound,
    NegotiationResult,
    MessageType,
    Priority,
    ResponseStatus,
    create_response,
    format_messages_for_prompt,
)


@dataclass
class RouterConfig:
    """Configuration for the message router."""
    max_negotiation_rounds: int = 3
    default_timeout: float = 30.0
    queue_size_limit: int = 100


# Type alias for async message handlers
MessageHandler = Callable[[AgentMessage], Awaitable[AgentResponse]]


class MessageRouter:
    """
    Central router for inter-agent communication.

    Responsibilities:
    - Queue messages for later delivery
    - Route messages directly to agent handlers
    - Manage multi-round negotiations
    - Escalate unresolved negotiations to Conductor
    """

    def __init__(self, config: Optional[RouterConfig] = None):
        """
        Initialize the message router.

        Args:
            config: Router configuration (uses defaults if not provided)
        """
        self.config = config or self._load_config()

        # Registered agent handlers
        self._handlers: dict[str, MessageHandler] = {}

        # Message queues per agent
        self._queues: dict[str, list[AgentMessage]] = {}

        # Active negotiations
        self._negotiations: dict[str, NegotiationResult] = {}

        # Response tracking
        self._pending_responses: dict[str, asyncio.Future] = {}

        # Message history (for debugging/logging)
        self._history: list[tuple[AgentMessage, Optional[AgentResponse]]] = []

    def _load_config(self) -> RouterConfig:
        """Load configuration from Config class if available."""
        try:
            from src.config import Config
            return RouterConfig(
                max_negotiation_rounds=getattr(Config, "MAX_NEGOTIATION_ROUNDS", 3),
                default_timeout=getattr(Config, "COORDINATION_TIMEOUT", 30.0),
            )
        except ImportError:
            return RouterConfig()

    def register_agent(self, agent_name: str, handler: MessageHandler):
        """
        Register an agent's message handler.

        Args:
            agent_name: Name of the agent
            handler: Async function that takes AgentMessage and returns AgentResponse
        """
        self._handlers[agent_name] = handler
        if agent_name not in self._queues:
            self._queues[agent_name] = []

    def unregister_agent(self, agent_name: str):
        """Unregister an agent."""
        self._handlers.pop(agent_name, None)

    def queue_message(self, message: AgentMessage) -> bool:
        """
        Queue a message for later delivery.

        Messages are queued when the target agent isn't ready to receive
        or when batching is preferred.

        Args:
            message: Message to queue

        Returns:
            True if queued successfully, False if queue is full
        """
        to_agent = message.to_agent

        if to_agent not in self._queues:
            self._queues[to_agent] = []

        if len(self._queues[to_agent]) >= self.config.queue_size_limit:
            return False

        self._queues[to_agent].append(message)
        return True

    def get_pending_messages(self, agent_name: str) -> list[AgentMessage]:
        """
        Get all pending messages for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            List of pending messages (does not clear the queue)
        """
        return list(self._queues.get(agent_name, []))

    def clear_pending_messages(self, agent_name: str) -> list[AgentMessage]:
        """
        Get and clear all pending messages for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            List of messages that were pending
        """
        messages = self._queues.get(agent_name, [])
        self._queues[agent_name] = []
        return messages

    async def route(
        self,
        message: AgentMessage,
        timeout: Optional[float] = None,
    ) -> Optional[AgentResponse]:
        """
        Route a message to its target agent and wait for response.

        Args:
            message: Message to route
            timeout: Timeout in seconds (uses config default if not specified)

        Returns:
            AgentResponse if handler exists and responds, None otherwise
        """
        to_agent = message.to_agent
        timeout = timeout or message.timeout_seconds or self.config.default_timeout

        handler = self._handlers.get(to_agent)
        if not handler:
            # No handler registered - queue for later
            self.queue_message(message)
            return None

        try:
            response = await asyncio.wait_for(
                handler(message),
                timeout=timeout,
            )
            self._history.append((message, response))
            return response

        except asyncio.TimeoutError:
            # Create timeout response
            response = create_response(
                message=message,
                from_agent=to_agent,
                status=ResponseStatus.PENDING,
                content="Response timed out",
            )
            self._history.append((message, response))
            return response

        except Exception as e:
            # Create error response
            response = create_response(
                message=message,
                from_agent=to_agent,
                status=ResponseStatus.REJECTED,
                content=f"Error processing message: {str(e)}",
            )
            self._history.append((message, response))
            return response

    async def negotiate(
        self,
        initiator: str,
        topic: str,
        responder: str,
        initial_message: AgentMessage,
        max_rounds: Optional[int] = None,
    ) -> NegotiationResult:
        """
        Manage a multi-round negotiation between two agents.

        Args:
            initiator: Name of initiating agent
            topic: Topic of negotiation
            responder: Name of responding agent
            initial_message: First message in negotiation
            max_rounds: Maximum rounds (uses config default if not specified)

        Returns:
            NegotiationResult with full history and outcome
        """
        negotiation_id = str(uuid.uuid4())[:8]
        max_rounds = max_rounds or self.config.max_negotiation_rounds

        result = NegotiationResult(
            negotiation_id=negotiation_id,
            initiator=initiator,
            responder=responder,
            topic=topic,
        )

        current_message = initial_message
        current_message.thread_id = negotiation_id

        for round_num in range(1, max_rounds + 1):
            round_result = NegotiationRound(
                round_number=round_num,
                initiator_message=current_message,
            )

            # Route to responder
            response = await self.route(current_message)
            round_result.responder_response = response

            result.rounds.append(round_result)

            if response is None:
                # No handler - escalate
                result.final_status = ResponseStatus.ESCALATED
                result.escalated = True
                break

            # Check if resolved
            if response.status == ResponseStatus.ACCEPTED:
                round_result.resolved = True
                result.final_status = ResponseStatus.ACCEPTED
                result.resolution = response.content
                break

            if response.status == ResponseStatus.REJECTED:
                if response.alternative_proposal:
                    # Continue negotiation with counter-proposal
                    current_message = AgentMessage(
                        message_id=str(uuid.uuid4())[:8],
                        from_agent=responder,
                        to_agent=initiator,
                        message_type=MessageType.SUGGESTION,
                        content=response.alternative_proposal,
                        thread_id=negotiation_id,
                    )
                else:
                    # No alternative - deadlock
                    result.final_status = ResponseStatus.REJECTED
                    break

            if response.status == ResponseStatus.NEEDS_CLARIFICATION:
                # Create clarification request
                if response.clarification_needed:
                    current_message = AgentMessage(
                        message_id=str(uuid.uuid4())[:8],
                        from_agent=responder,
                        to_agent=initiator,
                        message_type=MessageType.QUESTION,
                        content=response.clarification_needed,
                        thread_id=negotiation_id,
                    )
                else:
                    result.final_status = ResponseStatus.NEEDS_CLARIFICATION
                    break

        # Max rounds reached without resolution
        if result.final_status == ResponseStatus.PENDING:
            result.final_status = ResponseStatus.ESCALATED
            result.escalated = True

        self._negotiations[negotiation_id] = result
        return result

    async def escalate_to_conductor(
        self,
        negotiation: NegotiationResult,
    ) -> Optional[AgentResponse]:
        """
        Escalate an unresolved negotiation to the Conductor.

        Args:
            negotiation: NegotiationResult to escalate

        Returns:
            Conductor's response if available
        """
        # Build escalation message
        summary = negotiation.summary()

        # Include last few messages for context
        context_parts = []
        for round_obj in negotiation.rounds[-2:]:  # Last 2 rounds
            context_parts.append(round_obj.initiator_message.to_prompt_format())
            if round_obj.responder_response:
                context_parts.append(round_obj.responder_response.to_prompt_format())

        escalation_message = AgentMessage(
            message_id=str(uuid.uuid4())[:8],
            from_agent="router",
            to_agent="conductor",
            message_type=MessageType.ESCALATION,
            content=f"Negotiation requires escalation:\n\n{summary}",
            context="\n\n".join(context_parts),
            priority=Priority.HIGH,
            requires_response=True,
        )

        return await self.route(escalation_message)

    def format_pending_for_prompt(self, agent_name: str) -> str:
        """
        Get pending messages formatted for injection into agent prompt.

        Args:
            agent_name: Name of the agent

        Returns:
            Markdown-formatted string with pending messages
        """
        messages = self.get_pending_messages(agent_name)
        if not messages:
            return ""

        return format_messages_for_prompt(messages)

    def get_negotiation(self, negotiation_id: str) -> Optional[NegotiationResult]:
        """Get a negotiation by ID."""
        return self._negotiations.get(negotiation_id)

    def get_history(
        self,
        agent_name: Optional[str] = None,
        limit: int = 50,
    ) -> list[tuple[AgentMessage, Optional[AgentResponse]]]:
        """
        Get message history, optionally filtered by agent.

        Args:
            agent_name: Filter to messages involving this agent
            limit: Maximum entries to return

        Returns:
            List of (message, response) tuples
        """
        history = self._history

        if agent_name:
            history = [
                (msg, resp) for msg, resp in history
                if msg.from_agent == agent_name or msg.to_agent == agent_name
            ]

        return history[-limit:]

    def clear_history(self):
        """Clear message history."""
        self._history.clear()

    def stats(self) -> dict:
        """Get router statistics."""
        return {
            "registered_agents": list(self._handlers.keys()),
            "queued_messages": {
                agent: len(msgs) for agent, msgs in self._queues.items()
            },
            "active_negotiations": len(self._negotiations),
            "history_size": len(self._history),
        }


# Singleton instance
_router_instance: Optional[MessageRouter] = None


def get_router() -> MessageRouter:
    """Get or create singleton MessageRouter instance."""
    global _router_instance
    if _router_instance is None:
        _router_instance = MessageRouter()
    return _router_instance


def reset_router():
    """Reset the singleton router (useful for testing)."""
    global _router_instance
    _router_instance = None
