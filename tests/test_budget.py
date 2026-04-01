"""Tests for token budget enforcement."""

import pytest
from src.rag.budget import BudgetEnforcer, TOKEN_BUDGETS


@pytest.fixture
def enforcer():
    return BudgetEnforcer(budgets=TOKEN_BUDGETS)


class TestCountTokens:
    def test_empty_string(self, enforcer):
        assert enforcer.count_tokens("") == 0

    def test_short_text(self, enforcer):
        count = enforcer.count_tokens("Hello world")
        assert count > 0

    def test_longer_text_has_more_tokens(self, enforcer):
        short = enforcer.count_tokens("Hello")
        long = enforcer.count_tokens("Hello world this is a much longer sentence with many words")
        assert long > short


class TestGetBudget:
    def test_known_agent_types(self, enforcer):
        assert enforcer.get_budget("conductor") == 100
        assert enforcer.get_budget("planner") == 300
        assert enforcer.get_budget("creative_brain") == 200
        assert enforcer.get_budget("reviewer") == 100

    def test_implementer_variants(self, enforcer):
        assert enforcer.get_budget("implementer") == 150
        assert enforcer.get_budget("implementer_frontend") == 150
        assert enforcer.get_budget("implementer_backend") == 150

    def test_unknown_agent_falls_back(self, enforcer):
        budget = enforcer.get_budget("unknown_agent")
        assert budget == 150  # Falls back to implementer default


class TestEnforce:
    def test_short_text_unchanged(self, enforcer):
        text = "Short text."
        result = enforcer.enforce("planner", text)
        assert result == text

    def test_truncates_long_text(self, enforcer):
        # Generate text that exceeds conductor budget (100 tokens)
        long_text = ". ".join([f"This is sentence number {i}" for i in range(50)])
        result = enforcer.enforce("conductor", long_text)
        assert enforcer.count_tokens(result) <= 110  # Small tolerance for truncation

    def test_empty_text(self, enforcer):
        assert enforcer.enforce("planner", "") == ""

    def test_preserves_sentence_boundaries(self, enforcer):
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        result = enforcer.enforce("conductor", text)
        # Should not cut mid-sentence
        assert not result.endswith(" sente")


class TestFormatWithBudget:
    def test_single_section(self, enforcer):
        sections = [("Title", "Some content here")]
        result = enforcer.format_with_budget("planner", sections)
        assert "## Title" in result
        assert "Some content here" in result

    def test_empty_sections(self, enforcer):
        assert enforcer.format_with_budget("planner", []) == ""

    def test_multiple_sections(self, enforcer):
        sections = [
            ("Past Tasks", "Task A was successful"),
            ("Lessons", "Always validate inputs"),
        ]
        result = enforcer.format_with_budget("planner", sections)
        assert "## Past Tasks" in result
        assert "## Lessons" in result
