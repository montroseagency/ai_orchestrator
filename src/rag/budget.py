"""
Token Budget Enforcer — Enforce token limits for historical context injection per agent.

Ensures each agent receives historical context within their configured token budget,
using sentence-aware truncation to avoid mid-word or mid-sentence cuts.
"""

from typing import Optional

# Try tiktoken for accurate token counting, fall back to char estimation
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


# Default token budgets per agent type (historical context only)
TOKEN_BUDGETS: dict[str, int] = {
    "conductor": 100,
    "planner": 300,
    "creative_brain": 200,
    "implementer": 150,
    "reviewer": 100,
}


class BudgetEnforcer:
    """
    Enforces token limits for historical context injection.

    Features:
    - Accurate token counting with tiktoken (falls back to char estimation)
    - Sentence-aware truncation (no mid-word cuts)
    - Per-agent budget configuration
    - Graceful handling of edge cases
    """

    # Average chars per token for fallback estimation
    CHARS_PER_TOKEN_ESTIMATE = 4

    def __init__(self, budgets: Optional[dict[str, int]] = None):
        """
        Initialize the budget enforcer.

        Args:
            budgets: Optional override for token budgets per agent type.
                    Uses defaults if not provided.
        """
        self.budgets = budgets or self._load_budgets()
        self._encoder = None

    def _load_budgets(self) -> dict[str, int]:
        """Load token budgets from Config if available, else use defaults."""
        try:
            from src.config import Config
            return getattr(Config, "TOKEN_BUDGETS", TOKEN_BUDGETS)
        except ImportError:
            return TOKEN_BUDGETS

    def _get_encoder(self):
        """Get or create tiktoken encoder (lazy loaded)."""
        if self._encoder is None and TIKTOKEN_AVAILABLE:
            try:
                # Use cl100k_base encoding (GPT-4/Claude compatible)
                self._encoder = tiktoken.get_encoding("cl100k_base")
            except Exception:
                pass
        return self._encoder

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Uses tiktoken if available, otherwise estimates based on ~4 chars/token.

        Args:
            text: Text to count tokens for

        Returns:
            Token count (exact with tiktoken, estimated otherwise)
        """
        if not text:
            return 0

        encoder = self._get_encoder()
        if encoder:
            try:
                return len(encoder.encode(text))
            except Exception:
                pass

        # Fallback: estimate ~4 chars per token
        return len(text) // self.CHARS_PER_TOKEN_ESTIMATE

    def get_budget(self, agent_type: str) -> int:
        """
        Get token budget for an agent type.

        Args:
            agent_type: Agent type name (conductor, planner, etc.)

        Returns:
            Token budget for the agent (defaults to 150 if not configured)
        """
        # Normalize agent type (handle variants like "implementer_frontend")
        base_type = agent_type.split("_")[0] if "_" in agent_type else agent_type
        return self.budgets.get(base_type, self.budgets.get("implementer", 150))

    def enforce(self, agent_type: str, context: str) -> str:
        """
        Truncate context to fit within agent's token budget.

        Uses sentence-aware truncation to avoid cutting mid-sentence.

        Args:
            agent_type: Agent type name
            context: Historical context to truncate

        Returns:
            Context truncated to fit within budget, preserving complete sentences
        """
        if not context:
            return ""

        budget = self.get_budget(agent_type)
        current_tokens = self.count_tokens(context)

        if current_tokens <= budget:
            return context

        # Need to truncate - use sentence-aware truncation
        return self._truncate_to_budget(context, budget)

    def _truncate_to_budget(self, text: str, budget: int) -> str:
        """
        Truncate text to fit within token budget, preserving complete sentences.

        Args:
            text: Text to truncate
            budget: Maximum tokens allowed

        Returns:
            Truncated text with complete sentences
        """
        # Split into sentences (rough but effective)
        sentences = self._split_sentences(text)

        if not sentences:
            # Fallback: character-based truncation
            char_limit = budget * self.CHARS_PER_TOKEN_ESTIMATE
            return text[:char_limit].rsplit(" ", 1)[0] + "..."

        # Accumulate sentences until we hit the budget
        result = []
        total_tokens = 0

        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)

            # Would exceed budget?
            if total_tokens + sentence_tokens > budget:
                # If we have at least one sentence, stop here
                if result:
                    break
                # Otherwise, truncate this sentence to fit
                truncated = self._truncate_sentence(sentence, budget)
                result.append(truncated)
                break

            result.append(sentence)
            total_tokens += sentence_tokens

        truncated_text = " ".join(result)

        # Add ellipsis if we truncated
        if len(result) < len(sentences):
            truncated_text += "..."

        return truncated_text

    def _split_sentences(self, text: str) -> list[str]:
        """
        Split text into sentences.

        Simple heuristic: split on ., !, ? followed by space or newline.
        """
        import re

        # Split on sentence-ending punctuation followed by whitespace
        pattern = r"(?<=[.!?])\s+"
        sentences = re.split(pattern, text.strip())

        # Filter empty sentences
        return [s.strip() for s in sentences if s.strip()]

    def _truncate_sentence(self, sentence: str, budget: int) -> str:
        """
        Truncate a single sentence to fit within budget.

        Preserves whole words.
        """
        words = sentence.split()
        result = []
        total_tokens = 0

        for word in words:
            word_tokens = self.count_tokens(word + " ")
            if total_tokens + word_tokens > budget:
                break
            result.append(word)
            total_tokens += word_tokens

        if result:
            return " ".join(result) + "..."
        else:
            # Extreme case: single word exceeds budget
            char_limit = budget * self.CHARS_PER_TOKEN_ESTIMATE
            return sentence[:char_limit] + "..."

    def format_with_budget(
        self,
        agent_type: str,
        sections: list[tuple[str, str]],
    ) -> str:
        """
        Format multiple sections within total budget, distributing tokens fairly.

        Args:
            agent_type: Agent type for budget lookup
            sections: List of (title, content) tuples

        Returns:
            Formatted context within budget
        """
        budget = self.get_budget(agent_type)

        if not sections:
            return ""

        # Calculate overhead (section headers)
        overhead_per_section = 5  # ~5 tokens for "## Title\n"
        total_overhead = overhead_per_section * len(sections)
        content_budget = max(budget - total_overhead, 50)

        # Distribute budget proportionally by content length
        total_length = sum(len(content) for _, content in sections)
        if total_length == 0:
            return ""

        result_parts = []
        for title, content in sections:
            # Proportional budget for this section
            section_budget = int((len(content) / total_length) * content_budget)
            section_budget = max(section_budget, 20)  # Minimum 20 tokens

            truncated = self._truncate_to_budget(content, section_budget)
            if truncated:
                result_parts.append(f"## {title}\n{truncated}")

        return "\n\n".join(result_parts)


# Singleton instance
_enforcer_instance: Optional[BudgetEnforcer] = None


def get_budget_enforcer() -> BudgetEnforcer:
    """Get or create singleton BudgetEnforcer instance."""
    global _enforcer_instance
    if _enforcer_instance is None:
        _enforcer_instance = BudgetEnforcer()
    return _enforcer_instance
