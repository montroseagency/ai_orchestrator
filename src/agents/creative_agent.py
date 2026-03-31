"""
Creative Brain Agent — Design and UX specialist.
Produces design_brief.md from plan.md + design system context.
"""

from src.agents.base import BaseAgent
from src.config import AGENTS_DIR, Config


class CreativeAgent(BaseAgent):
    """Design/UX specialist — creates concrete visual and interaction specs."""

    def __init__(self):
        super().__init__(
            name="Creative Brain",
            system_prompt_path=AGENTS_DIR / "creative_brain.md",
            model=Config.CREATIVE_MODEL,
        )

    async def design(self, context_package: str, session_id: str) -> str:
        """
        Generate a design_brief.md for the given plan and design system context.

        Returns:
            The design_brief.md content as a string.
        """
        user_message = (
            f"{context_package}\n\n"
            f"---\n\n"
            f"Session ID: `{session_id}`\n\n"
            f"Produce a complete `design_brief.md` following the exact format in your system prompt. "
            f"Be precise — the Implementer needs unambiguous design instructions. "
            f"Use ONLY Montrroase design system tokens. Output only the design_brief.md content."
        )

        return await self.call(
            user_message=user_message,
            temperature=0.7,  # Higher temp — we want creative, non-formulaic design choices
            max_tokens=4096,
        )
