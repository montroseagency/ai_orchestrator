"""
Backend Tester Agent — Backend adversarial quality gate.
Specializes in logic correctness, security, Django/DRF patterns, and data integrity.
Skill injected at call time: code_review (always).
"""

from src.agents.base import BaseAgent
from src.config import AGENTS_DIR, Config


class BackendTesterAgent(BaseAgent):
    """
    Backend-only adversarial tester.
    Checks logic correctness, security, Django/DRF compliance, and data integrity.
    Receives code_review skill (always).
    """

    def __init__(self):
        super().__init__(
            name="Backend Tester",
            system_prompt_path=AGENTS_DIR / "backend_tester.md",
            model=Config.BACKEND_TESTER_MODEL,
        )

    async def test(
        self,
        context_package: str,
        session_id: str,
        retry_count: int = 0,
        extra_system: str = "",
    ) -> tuple[bool, str, str | None]:
        """
        Test the backend implementation and return a verdict.

        Args:
            context_package: Assembled context with implementation files + plan
            session_id: Current session ID
            retry_count: How many test rounds have happened
            extra_system: Injected skills (code_review always)

        Returns:
            Tuple of:
                - passed: bool (True = PASS, False = FAIL)
                - test_content: Full test report content
                - fix_instructions: Compact fix instructions if FAIL, else None
        """
        user_message = (
            f"{context_package}\n\n"
            f"---\n\n"
            f"Session ID: `{session_id}`\n"
            f"Test attempt: {retry_count + 1}\n\n"
            f"Produce a complete backend test report following the exact format in your system prompt.\n"
            f"Be specific — cite file paths and approximate line numbers.\n"
            f"If FAIL, also produce a compact fix block at the end, "
            f"clearly separated with `---FIX_INSTRUCTIONS---` on its own line."
        )

        response = await self.call(
            user_message=user_message,
            temperature=0.2,
            max_tokens=4096,
            extra_system=extra_system,
        )

        passed = "✅ PASS" in response or "Verdict: PASS" in response
        if not passed and "PASS" in response and "FAIL" not in response:
            passed = True

        fix_instructions = None
        if "---FIX_INSTRUCTIONS---" in response:
            parts = response.split("---FIX_INSTRUCTIONS---", 1)
            test_content = parts[0].strip()
            fix_instructions = parts[1].strip()
        else:
            test_content = response

        return passed, test_content, fix_instructions

    async def write_walkthrough(
        self,
        prompt: str,
        plan_content: str,
        implementation_files: list[dict],
        review_content: str,
        session_id: str,
    ) -> str:
        """Generate a walkthrough.md after a PASS verdict."""
        files_summary = "\n".join(
            f"- `{f['path']}` — {f.get('change_summary', f['operation'])}"
            for f in implementation_files
        )

        user_message = (
            f"# Completed Task\n{prompt}\n\n"
            f"# Plan Summary\n{plan_content[:1500]}...\n\n"
            f"# Files Changed\n{files_summary}\n\n"
            f"# Test Verdict\n{review_content[:800]}...\n\n"
            f"Write a concise `walkthrough.md` (max 400 words) that:\n"
            f"1. Summarizes what was built and why\n"
            f"2. Lists files changed with one-line descriptions\n"
            f"3. Notes any important architectural decisions or data integrity considerations\n"
            f"4. Lists any follow-up items (from implementer notes)\n"
            f"Use markdown. Start with `# Walkthrough: [Task Name]`"
        )

        return await self.call(
            user_message=user_message,
            temperature=0.4,
            max_tokens=1024,
        )
