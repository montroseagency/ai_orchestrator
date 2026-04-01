"""Tests for progressive retrieval."""

import pytest
from unittest.mock import MagicMock, patch
from src.rag.retriever import (
    ProgressiveRetriever,
    DetailLevel,
    RetrievedSession,
    RetrievedContext,
    AGENT_DETAIL_LEVELS,
)
from src.rag.budget import BudgetEnforcer


class TestDetailLevel:
    def test_ordering(self):
        assert DetailLevel.METADATA.value < DetailLevel.SUMMARY.value
        assert DetailLevel.SUMMARY.value < DetailLevel.FULL.value


class TestAgentDetailLevels:
    def test_conductor_gets_metadata(self):
        assert AGENT_DETAIL_LEVELS["conductor"] == DetailLevel.METADATA

    def test_planner_gets_summary(self):
        assert AGENT_DETAIL_LEVELS["planner"] == DetailLevel.SUMMARY

    def test_reviewer_gets_metadata(self):
        assert AGENT_DETAIL_LEVELS["reviewer"] == DetailLevel.METADATA


class TestRetrievedSession:
    def test_default_values(self):
        session = RetrievedSession(
            session_id="test-123",
            relevance=0.85,
            outcome="pass",
            detail_level=DetailLevel.METADATA,
        )
        assert session.session_id == "test-123"
        assert session.relevance == 0.85
        assert session.issues == []
        assert session.summary == ""
        assert session.full_plan is None


class TestProgressiveRetriever:
    @pytest.fixture
    def mock_rag(self):
        rag = MagicMock()
        rag.search_sessions.return_value = [
            {
                "session_id": "test-1",
                "relevance": 0.9,
                "outcome": "pass",
                "summary": "Added dark mode",
                "files_touched": "App.tsx,theme.ts",
                "review_issues": "typescript_any_type",
                "prompt": "Add dark mode toggle",
            }
        ]
        rag.search_lessons.return_value = [
            {
                "issue_type": "typescript_any_type",
                "fix": "Use unknown instead of any",
                "relevance": 0.85,
            }
        ]
        return rag

    @pytest.fixture
    def mock_deduplicator(self):
        dedup = MagicMock()
        # Make dedupe pass through (no duplicates found)
        dedup.dedupe_sessions.return_value = MagicMock(kept=[
            {
                "session_id": "test-1",
                "relevance": 0.9,
                "outcome": "pass",
                "summary": "Added dark mode",
                "files_touched": "App.tsx,theme.ts",
                "review_issues": "typescript_any_type",
                "prompt": "Add dark mode toggle",
            }
        ])
        dedup.dedupe_lessons.return_value = MagicMock(kept=[
            {
                "issue_type": "typescript_any_type",
                "fix": "Use unknown instead of any",
                "relevance": 0.85,
            }
        ])
        return dedup

    @pytest.fixture
    def retriever(self, mock_rag, mock_deduplicator):
        return ProgressiveRetriever(
            rag=mock_rag,
            budget_enforcer=BudgetEnforcer(),
            deduplicator=mock_deduplicator,
        )

    def test_get_detail_level(self, retriever):
        assert retriever.get_detail_level("conductor") == DetailLevel.METADATA
        assert retriever.get_detail_level("planner") == DetailLevel.SUMMARY
        assert retriever.get_detail_level("implementer_frontend") == DetailLevel.SUMMARY

    def test_get_context(self, retriever):
        result = retriever.get_context("Add dark mode", "planner")
        assert isinstance(result, RetrievedContext)
        assert result.agent_type == "planner"
        assert len(result.sessions) >= 0

    def test_format_for_context(self, retriever):
        context = RetrievedContext(
            agent_type="planner",
            query="test",
            sessions=[
                RetrievedSession(
                    session_id="test-1",
                    relevance=0.9,
                    outcome="pass",
                    detail_level=DetailLevel.SUMMARY,
                    summary="Added dark mode",
                    issues=["typescript_any_type"],
                )
            ],
            lessons=[{"issue_type": "ts_any", "fix": "Use unknown"}],
        )
        formatted = retriever.format_for_context(context, "planner")
        assert isinstance(formatted, str)

    def test_format_empty_context(self, retriever):
        context = RetrievedContext(agent_type="planner", query="test")
        formatted = retriever.format_for_context(context, "planner")
        assert formatted == ""


class TestBuildSession:
    @pytest.fixture
    def retriever(self):
        return ProgressiveRetriever(
            rag=MagicMock(),
            budget_enforcer=BudgetEnforcer(),
            deduplicator=MagicMock(),
        )

    def test_metadata_level(self, retriever):
        raw = {
            "session_id": "test-1",
            "relevance": 0.9,
            "outcome": "pass",
            "review_issues": "typescript_any_type,error_handling",
        }
        session = retriever._build_session(raw, DetailLevel.METADATA)
        assert session.session_id == "test-1"
        assert len(session.issues) <= 3
        assert session.summary == ""  # Not loaded at METADATA level

    def test_summary_level(self, retriever):
        raw = {
            "session_id": "test-1",
            "relevance": 0.9,
            "outcome": "pass",
            "summary": "Added authentication flow",
            "files_touched": "auth.py,login.tsx",
            "prompt": "Add auth",
            "review_issues": "",
        }
        session = retriever._build_session(raw, DetailLevel.SUMMARY)
        assert session.summary == "Added authentication flow"
        assert len(session.files) > 0
