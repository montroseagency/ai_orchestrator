"""Tests for coordination messages and router."""

import asyncio
import pytest
from src.coordination.messages import (
    AgentMessage,
    AgentResponse,
    NegotiationResult,
    MessageType,
    Priority,
    ResponseStatus,
    create_question,
    create_constraint,
    create_suggestion,
    create_feasibility_check,
    create_design_feedback,
    create_response,
    format_messages_for_prompt,
    group_messages_by_type,
    filter_messages_by_priority,
)
from src.coordination.router import MessageRouter, RouterConfig, reset_router


# ═══════════════════════════════════════════════════════════════
# Message Tests
# ═══════════════════════════════════════════════════════════════


class TestCreateQuestion:
    def test_basic_question(self):
        msg = create_question(
            from_agent="implementer",
            to_agent="planner",
            question="Should validation happen client-side?",
        )
        assert msg.from_agent == "implementer"
        assert msg.to_agent == "planner"
        assert msg.message_type == MessageType.QUESTION
        assert msg.requires_response is True
        assert msg.priority == Priority.NORMAL

    def test_with_context_and_priority(self):
        msg = create_question(
            from_agent="implementer",
            to_agent="planner",
            question="Is this approach viable?",
            context="Working on auth module",
            priority=Priority.HIGH,
        )
        assert msg.context == "Working on auth module"
        assert msg.priority == Priority.HIGH


class TestCreateConstraint:
    def test_basic_constraint(self):
        msg = create_constraint(
            from_agent="reviewer",
            to_agent="implementer",
            constraint="Must handle loading state",
        )
        assert msg.message_type == MessageType.CONSTRAINT
        assert msg.priority == Priority.HIGH
        assert msg.requires_response is False


class TestCreateSuggestion:
    def test_basic_suggestion(self):
        msg = create_suggestion(
            from_agent="creative_brain",
            to_agent="implementer",
            suggestion="Use skeleton loader for better UX",
        )
        assert msg.message_type == MessageType.SUGGESTION
        assert msg.requires_response is False


class TestCreateFeasibilityCheck:
    def test_feasibility_check(self):
        msg = create_feasibility_check(
            from_agent="planner",
            to_agent="implementer",
            proposal="Use WebSocket",
            constraints=["No new deps", "Django only"],
        )
        assert msg.message_type == MessageType.FEASIBILITY_CHECK
        assert "WebSocket" in msg.content
        assert "No new deps" in msg.content


class TestCreateDesignFeedback:
    def test_design_feedback(self):
        msg = create_design_feedback(
            from_agent="creative_brain",
            to_agent="implementer",
            feedback="Follow 8px grid",
            severity="requirement",
            affected_component="LoginForm",
        )
        assert msg.message_type == MessageType.DESIGN_FEEDBACK
        assert msg.priority == Priority.HIGH
        assert "LoginForm" in msg.content


class TestPromptFormat:
    def test_message_to_prompt(self):
        msg = create_question(
            from_agent="implementer",
            to_agent="planner",
            question="How to handle this?",
        )
        formatted = msg.to_prompt_format()
        assert "implementer" in formatted
        assert "How to handle this?" in formatted

    def test_critical_message_shows_priority(self):
        msg = create_question(
            from_agent="reviewer",
            to_agent="implementer",
            question="Fix this bug",
            priority=Priority.CRITICAL,
        )
        formatted = msg.to_prompt_format()
        assert "[CRITICAL]" in formatted


class TestCreateResponse:
    def test_accepted_response(self):
        msg = create_question("a", "b", "test?")
        resp = create_response(msg, "b", ResponseStatus.ACCEPTED, "Yes")
        assert resp.status == ResponseStatus.ACCEPTED
        assert resp.to_agent == "a"
        assert resp.from_agent == "b"

    def test_response_with_alternative(self):
        msg = create_question("a", "b", "use X?")
        resp = create_response(
            msg, "b", ResponseStatus.REJECTED, "No",
            alternative_proposal="Use Y instead",
        )
        assert resp.alternative_proposal == "Use Y instead"


class TestFormatMessages:
    def test_empty_list(self):
        assert format_messages_for_prompt([]) == ""

    def test_formats_messages(self):
        msgs = [
            create_question("a", "b", "question 1"),
            create_constraint("c", "b", "constraint 1"),
        ]
        formatted = format_messages_for_prompt(msgs)
        assert "## Pending Messages" in formatted
        assert "question 1" in formatted
        assert "constraint 1" in formatted


class TestGroupMessages:
    def test_groups_by_type(self):
        msgs = [
            create_question("a", "b", "q1"),
            create_question("a", "b", "q2"),
            create_constraint("c", "b", "c1"),
        ]
        grouped = group_messages_by_type(msgs)
        assert len(grouped[MessageType.QUESTION]) == 2
        assert len(grouped[MessageType.CONSTRAINT]) == 1


class TestFilterByPriority:
    def test_filter_normal_and_above(self):
        msgs = [
            create_question("a", "b", "q", priority=Priority.LOW),
            create_question("a", "b", "q", priority=Priority.NORMAL),
            create_question("a", "b", "q", priority=Priority.HIGH),
        ]
        filtered = filter_messages_by_priority(msgs, Priority.NORMAL)
        assert len(filtered) == 2

    def test_filter_critical_only(self):
        msgs = [
            create_question("a", "b", "q", priority=Priority.HIGH),
            create_question("a", "b", "q", priority=Priority.CRITICAL),
        ]
        filtered = filter_messages_by_priority(msgs, Priority.CRITICAL)
        assert len(filtered) == 1


# ═══════════════════════════════════════════════════════════════
# Router Tests
# ═══════════════════════════════════════════════════════════════


class TestMessageRouter:
    @pytest.fixture
    def router(self):
        reset_router()
        return MessageRouter(RouterConfig(max_negotiation_rounds=3, default_timeout=5.0))

    def test_queue_message(self, router):
        msg = create_question("a", "b", "test?")
        assert router.queue_message(msg) is True
        pending = router.get_pending_messages("b")
        assert len(pending) == 1

    def test_clear_pending(self, router):
        msg = create_question("a", "b", "test?")
        router.queue_message(msg)
        cleared = router.clear_pending_messages("b")
        assert len(cleared) == 1
        assert len(router.get_pending_messages("b")) == 0

    def test_format_pending(self, router):
        msg = create_question("a", "b", "test?")
        router.queue_message(msg)
        formatted = router.format_pending_for_prompt("b")
        assert "test?" in formatted

    def test_format_empty_pending(self, router):
        assert router.format_pending_for_prompt("nobody") == ""

    @pytest.mark.asyncio
    async def test_route_no_handler(self, router):
        msg = create_question("a", "b", "test?")
        resp = await router.route(msg)
        assert resp is None
        # Should be queued
        assert len(router.get_pending_messages("b")) == 1

    @pytest.mark.asyncio
    async def test_route_with_handler(self, router):
        async def handler(msg):
            return create_response(msg, "b", ResponseStatus.ACCEPTED, "OK")

        router.register_agent("b", handler)
        msg = create_question("a", "b", "test?")
        resp = await router.route(msg)
        assert resp.status == ResponseStatus.ACCEPTED
        assert resp.content == "OK"

    @pytest.mark.asyncio
    async def test_route_handler_error(self, router):
        async def bad_handler(msg):
            raise ValueError("broken")

        router.register_agent("b", bad_handler)
        msg = create_question("a", "b", "test?")
        resp = await router.route(msg)
        assert resp.status == ResponseStatus.REJECTED
        assert "broken" in resp.content

    @pytest.mark.asyncio
    async def test_negotiate_accepted(self, router):
        async def handler(msg):
            return create_response(msg, "b", ResponseStatus.ACCEPTED, "Agreed")

        router.register_agent("b", handler)
        msg = create_question("a", "b", "Shall we do X?")
        result = await router.negotiate("a", "approach", "b", msg)
        assert result.final_status == ResponseStatus.ACCEPTED
        assert result.resolution == "Agreed"
        assert len(result.rounds) == 1

    def test_stats(self, router):
        router.register_agent("agent_a", lambda msg: None)
        msg = create_question("x", "y", "test?")
        router.queue_message(msg)
        stats = router.stats()
        assert "agent_a" in stats["registered_agents"]
        assert stats["queued_messages"]["y"] == 1

    def test_unregister_agent(self, router):
        router.register_agent("a", lambda msg: None)
        router.unregister_agent("a")
        assert "a" not in router._handlers
