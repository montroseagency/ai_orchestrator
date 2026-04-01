"""
Planner Agent — Task decomposition specialist.
Produces plan.md from a raw task description.
"""

from src.agents.base import BaseAgent
from src.config import AGENTS_DIR, Config


class PlannerAgent(BaseAgent):
    """Decomposes tasks into an explicit, structured plan.md."""

    def __init__(self):
        super().__init__(
            name="Planner",
            system_prompt_path=AGENTS_DIR / "planner.md",
            model=Config.PLANNER_MODEL,
        )

    async def plan(self, context_package: str, session_id: str) -> str:
        """
        Generate a plan.md for the given task context.

        Returns:
            The plan.md content as a string.
        """
        user_message = (
            f"{context_package}\n\n"
            f"---\n\n"
            f"Session ID: `{session_id}`\n\n"
            f"Produce a complete `plan.md` following the exact format in your system prompt. "
            f"Be specific about file paths — use paths relative to `Montrroase_website/` root. "
            f"Do NOT write any code. Output only the plan.md content."
        )

        return await self.call(
            user_message=user_message,
            temperature=0.3,  # Ignored when thinking_tokens > 0 (forced to 1.0)
            max_tokens=4096,
            thinking_tokens=Config.PLANNER_THINKING_TOKENS,
        )
