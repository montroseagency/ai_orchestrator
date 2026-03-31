"""
Reviewer Agent — Adversarial quality gate.
Reads implementation diffs and produces a PASS/FAIL verdict with actionable issues.
"""

from src.agents.base import BaseAgent
from src.config import AGENTS_DIR, Config


class ReviewerAgent(BaseAgent):
    """
    Adversarial reviewer — finds bugs, style violations, and architecture issues
    that the implementer cannot see in their own code.
    """

    def __init__(self):
        super().__init__(
            name="Reviewer",
            system_prompt_path=AGENTS_DIR / "reviewer.md",
            model=Config.REVIEWER_MODEL,
        )

    async def review(
        self,
        context_package: str,
        session_id: str,
        retry_count: int = 0,
    ) -> tuple[bool, str, str | None]:
        """
        Review the implementation and return a verdict.

        Args:
            context_package: Assembled reviewer context with diffs + plan
            session_id: Current session ID
            retry_count: How many reviewer rounds have happened

        Returns:
            Tuple of:
                - passed: bool (True = PASS, False = FAIL)
                - review_content: Full review.md content
                - fix_instructions: Compact fix instructions if FAIL, else None
        """
        user_message = (
            f"{context_package}\n\n"
            f"---\n\n"
            f"Session ID: `{session_id}`\n"
            f"Review attempt: {retry_count + 1}\n\n"
            f"Produce a complete `review.md` following the exact format in your system prompt.\n"
            f"Be specific — cite file paths and approximate line numbers.\n"
            f"If FAIL, also produce a compact `fix_instructions.md` block at the end of your response, "
            f"clearly separated with `---FIX_INSTRUCTIONS---` on its own line."
        )

        response = await self.call(
            user_message=user_message,
            temperature=0.2,  # Deterministic — consistent quality standards
            max_tokens=4096,
        )

        # Parse verdict
        passed = "✅ PASS" in response or "Verdict: PASS" in response
        if not passed and "PASS" in response and "FAIL" not in response:
            passed = True  # Fallback: if only PASS mentioned

        # Split review from fix instructions
        fix_instructions = None
        if "---FIX_INSTRUCTIONS---" in response:
            parts = response.split("---FIX_INSTRUCTIONS---", 1)
            review_content = parts[0].strip()
            fix_instructions = parts[1].strip()
        else:
            review_content = response

        return passed, review_content, fix_instructions

    async def write_walkthrough(
        self,
        prompt: str,
        plan_content: str,
        implementation_files: list[dict],
        review_content: str,
        session_id: str,
    ) -> str:
        """
        After a PASS, generate a walkthrough.md summarizing the completed work.
        """
        files_summary = "\n".join(
            f"- `{f['path']}` — {f.get('change_summary', f['operation'])}"
            for f in implementation_files
        )

        user_message = (
            f"# Completed Task\n{prompt}\n\n"
            f"# Plan Summary\n{plan_content[:1500]}...\n\n"
            f"# Files Changed\n{files_summary}\n\n"
            f"# Reviewer Verdict\n{review_content[:800]}...\n\n"
            f"Write a concise `walkthrough.md` (max 400 words) that:\n"
            f"1. Summarizes what was built and why\n"
            f"2. Lists files changed with one-line descriptions\n"
            f"3. Notes any important architectural decisions made\n"
            f"4. Lists any follow-up items (from implementer notes)\n"
            f"Use markdown. Start with `# Walkthrough: [Task Name]`"
        )

        return await self.call(
            user_message=user_message,
            temperature=0.4,
            max_tokens=1024,
        )
