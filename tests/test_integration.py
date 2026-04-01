"""Integration tests for the self-improving agent architecture."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from src.rag.budget import BudgetEnforcer
from src.rag.retriever import ProgressiveRetriever, DetailLevel, RetrievedContext, RetrievedSession
from src.coordination.messages import (
    create_question,
    create_constraint,
    ResponseStatus,
    Priority,
)
from src.coordination.router import MessageRouter, RouterConfig


class TestBudgetRetrieverIntegration:
    """Test BudgetEnforcer + ProgressiveRetriever working together."""

    def test_format_respects_budget(self):
        enforcer = BudgetEnforcer()
        retriever = ProgressiveRetriever(
            rag=MagicMock(),
            budget_enforcer=enforcer,
            deduplicator=MagicMock(),
        )

        # Create a context with many sessions
        context = RetrievedContext(
            agent_type="conductor",
            query="test query",
            sessions=[
                RetrievedSession(
                    session_id=f"session-{i}",
                    relevance=0.9 - i * 0.1,
                    outcome="pass",
                    detail_level=DetailLevel.METADATA,
                    issues=["error_handling"],
                )
                for i in range(5)
            ],
        )

        formatted = retriever.format_for_context(context, "conductor")
        # Conductor has 100 token budget — should be truncated
        token_count = enforcer.count_tokens(formatted)
        assert token_count <= 120  # Allow small tolerance


class TestBaseAgentCommunication:
    """Test BaseAgent communication methods."""

    def test_ask_creates_message(self):
        from src.agents.base import BaseAgent
        # Patch to avoid loading system prompt
        with patch.object(BaseAgent, '__init__', lambda self, *a, **kw: None):
            agent = BaseAgent.__new__(BaseAgent)
            agent.name = "implementer"
            agent.outbox = []
            agent.can_communicate_with = ["planner", "conductor"]

            result = agent.ask("planner", "How should I approach this?")
            assert result is True
            assert len(agent.outbox) == 1
            assert agent.outbox[0].to_agent == "planner"

    def test_cannot_send_to_unauthorized(self):
        from src.agents.base import BaseAgent
        with patch.object(BaseAgent, '__init__', lambda self, *a, **kw: None):
            agent = BaseAgent.__new__(BaseAgent)
            agent.name = "reviewer"
            agent.outbox = []
            agent.can_communicate_with = ["conductor", "implementer"]

            result = agent.ask("planner", "Not allowed")
            assert result is False
            assert len(agent.outbox) == 0

    def test_flush_outbox(self):
        from src.agents.base import BaseAgent
        with patch.object(BaseAgent, '__init__', lambda self, *a, **kw: None):
            agent = BaseAgent.__new__(BaseAgent)
            agent.name = "implementer"
            agent.outbox = []
            agent.can_communicate_with = ["planner"]

            agent.ask("planner", "q1")
            agent.suggest("planner", "s1")

            messages = agent.flush_outbox()
            assert len(messages) == 2
            assert agent.has_pending_messages() is False


class TestRouterNegotiation:
    """Test multi-round negotiation."""

    @pytest.mark.asyncio
    async def test_negotiation_with_counter_proposal(self):
        from src.coordination.messages import create_response as _create_response

        router = MessageRouter(RouterConfig(max_negotiation_rounds=3))

        call_count = 0

        async def handler(msg):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _create_response(
                    msg, "responder", ResponseStatus.REJECTED,
                    "No, not X",
                    alternative_proposal="Let's do Y instead",
                )
            else:
                return _create_response(
                    msg, "responder", ResponseStatus.ACCEPTED,
                    "Y is good",
                )

        router.register_agent("responder", handler)
        router.register_agent("initiator", handler)

        msg = create_question("initiator", "responder", "Should we use X?")
        result = await router.negotiate("initiator", "approach", "responder", msg)

        assert result.final_status in (ResponseStatus.ACCEPTED, ResponseStatus.REJECTED, ResponseStatus.ESCALATED)
        assert len(result.rounds) >= 1


class TestContextBuilderRAG:
    """Test ContextBuilder RAG integration."""

    @pytest.mark.asyncio
    async def test_with_historical_context_disabled(self):
        from src.context_builder import ContextBuilder

        with patch('src.context_builder.Config') as mock_config:
            mock_config.ENABLE_HISTORICAL_CONTEXT = False
            builder = ContextBuilder()
            result = await builder.with_historical_context(
                "test prompt", "base context", "planner"
            )
            assert result == "base context"

    @pytest.mark.asyncio
    async def test_with_lesson_injections_no_issues(self):
        from src.context_builder import ContextBuilder

        with patch('src.context_builder.Config') as mock_config:
            mock_config.ENABLE_HISTORICAL_CONTEXT = True
            builder = ContextBuilder()
            result = await builder.with_lesson_injections(
                "base context", [], "planner"
            )
            assert result == "base context"


class TestGracefulDegradation:
    """Test that everything works when RAG is disabled."""

    def test_budget_enforcer_with_no_config(self):
        enforcer = BudgetEnforcer(budgets={"test": 100})
        assert enforcer.get_budget("test") == 100

    def test_retriever_without_rag(self):
        retriever = ProgressiveRetriever(
            rag=MagicMock(),
            budget_enforcer=BudgetEnforcer(),
            deduplicator=MagicMock(),
        )
        assert retriever.get_detail_level("planner") == DetailLevel.SUMMARY

    @pytest.mark.asyncio
    async def test_router_without_handlers(self):
        router = MessageRouter()
        msg = create_question("a", "nonexistent", "test?")
        resp = await router.route(msg)
        assert resp is None
