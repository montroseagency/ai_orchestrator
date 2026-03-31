"""
Implementer Agent — Produces production-quality code.
Parameterized by domain: frontend | backend | fullstack
"""

import json
from src.agents.base import BaseAgent
from src.config import AGENTS_DIR, Config


class ImplementerAgent(BaseAgent):
    """
    Implements code changes based on plan.md and design_brief.md.
    Returns structured JSON with file operations.
    """

    def __init__(self, domain: str = "frontend"):
        """
        Args:
            domain: One of 'frontend', 'backend', 'fullstack'
        """
        self.domain = domain
        super().__init__(
            name=f"Implementer ({domain})",
            system_prompt_path=AGENTS_DIR / "implementer.md",
            model=Config.IMPLEMENTER_MODEL,
        )

    async def implement(
        self,
        context_package: str,
        session_id: str,
        retry_count: int = 0,
        fix_instructions: str | None = None,
    ) -> dict:
        """
        Generate code for the given context package.

        Args:
            context_package: Assembled context from ContextBuilder
            session_id: Current session ID
            retry_count: Number of retries so far
            fix_instructions: Reviewer's fix instructions (if retrying)

        Returns:
            Parsed JSON dict with 'files', 'implementation_summary', 'notes', etc.
        """
        retry_prefix = ""
        if retry_count > 0 and fix_instructions:
            remaining = Config.MAX_REVIEW_RETRIES - retry_count
            retry_prefix = (
                f"# FIX INSTRUCTIONS (Retry #{retry_count})\n"
                f"The Reviewer found issues in your last implementation. "
                f"You have {remaining} attempt(s) remaining.\n\n"
                f"{fix_instructions}\n\n"
                f"Apply ALL fixes listed above. Do not change anything marked as correct.\n\n"
                f"---\n\n"
            )

        # Add reflection prompt if retrying
        reflection = ""
        if retry_count > 0:
            reflection = (
                f"\n\nBefore implementing: reflect on what failed in your previous attempt "
                f"and confirm your specific fix approach in the `implementation_summary` field."
            )

        extra_system = (
            f"DOMAIN: {self.domain.upper()}\n"
            f"You are implementing the {self.domain} portion of this task.\n"
            f"Session: {session_id}\n"
            f"Retry attempt: {retry_count}"
        )

        user_message = (
            f"{retry_prefix}"
            f"{context_package}\n\n"
            f"---\n\n"
            f"Session ID: `{session_id}`{reflection}\n\n"
            f"Produce the implementation as a single JSON object following the format "
            f"in your system prompt. Include ALL files needed. "
            f"Output ONLY the JSON — no prose before or after."
        )

        response = await self.call(
            user_message=user_message,
            temperature=0.2,  # Very low — deterministic code generation
            max_tokens=16384,  # Large budget for full file contents
            extra_system=extra_system,
        )

        return self.extract_json(response)
