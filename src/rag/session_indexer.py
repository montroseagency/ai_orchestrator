"""
Session Indexer — Indexes completed sessions into ChromaDB with pre-computed summaries.

Key features:
- Pre-indexed summaries (computed once at index time, not per query)
- Extracts files touched from implementation logs
- Categorizes review issues for pattern matching
- Supports backfill of existing sessions
"""

import asyncio
import json
import re
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import anthropic

from src.config import Config, SESSIONS_DIR
from .server import get_rag_client


class SessionIndexer:
    """
    Indexes completed sessions with pre-computed summaries for token efficiency.

    Instead of summarizing at query time, we generate a concise summary once
    when the session completes and store it in ChromaDB for instant retrieval.
    """

    # Maximum tokens for pre-indexed summary
    SUMMARY_MAX_TOKENS = 150

    # Model for summarization
    SUMMARIZER_MODEL = "claude-haiku-4-5"

    def __init__(self, rag_client=None):
        """
        Initialize the session indexer.

        Args:
            rag_client: Optional RagServer instance (uses singleton if not provided)
        """
        self.rag = rag_client or get_rag_client()
        self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    async def index_session(self, session_dir: Path) -> dict:
        """
        Index a completed session into ChromaDB.

        Args:
            session_dir: Path to session directory containing state.json and artifacts

        Returns:
            Status dict with session_id and success/error info
        """
        state_file = session_dir / "state.json"
        if not state_file.exists():
            return {"status": "error", "error": "No state.json found"}

        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            return {"status": "error", "error": f"Invalid state.json: {e}"}

        session_id = state.get("session_id", session_dir.name)
        prompt = state.get("prompt", "")

        if not prompt:
            return {"status": "error", "error": "No prompt in state.json"}

        # Determine outcome
        phases = state.get("phases_completed", [])
        outcome = "pass" if "reviewer_pass" in phases else "fail"
        retry_count = state.get("iterations", 0)

        # Load artifacts
        plan = self._read_artifact(session_dir, "plan.md")
        review = self._read_artifact(session_dir, "review.md")
        walkthrough = self._read_artifact(session_dir, "walkthrough.md")
        impl_log = self._read_artifact(session_dir, "implementation_log.md")

        # Extract metadata
        files_touched = self._extract_files_from_impl_log(impl_log)
        review_issues = self._extract_issues_from_review(review)

        # Generate pre-indexed summary
        summary = await self._generate_summary(
            prompt=prompt,
            outcome=outcome,
            files=files_touched,
            review=review,
            walkthrough=walkthrough,
        )

        # Index into ChromaDB
        result = self.rag.index_session(
            session_id=session_id,
            prompt=prompt,
            outcome=outcome,
            summary=summary,
            files_touched=files_touched,
            review_issues=review_issues,
            retry_count=retry_count,
            full_plan_path=str(session_dir / "plan.md") if plan else None,
            full_review_path=str(session_dir / "review.md") if review else None,
        )

        return result

    async def _generate_summary(
        self,
        prompt: str,
        outcome: str,
        files: list[str],
        review: Optional[str],
        walkthrough: Optional[str],
    ) -> str:
        """
        Generate a concise summary of the session at index time.

        This runs once per session completion, not per query.
        """
        # Build context for summarization
        learnings = ""
        if review:
            # Extract key learnings from review
            learnings = self._extract_learnings(review)

        walkthrough_summary = ""
        if walkthrough:
            # Take first 500 chars of walkthrough
            walkthrough_summary = walkthrough[:500]

        summarization_prompt = f"""Summarize this completed coding task in <100 words:

Task: {prompt}
Outcome: {outcome}
Files modified: {', '.join(files[:10])}

{"Key learnings from review:" + learnings if learnings else ""}
{"What was done:" + walkthrough_summary if walkthrough_summary else ""}

Output a brief summary that captures:
1. What was accomplished
2. Key approach/patterns used
3. Any important lessons learned

Be specific and actionable. No fluff."""

        try:
            # Use Haiku for fast, cheap summarization
            response = self.client.messages.create(
                model=self.SUMMARIZER_MODEL,
                max_tokens=self.SUMMARY_MAX_TOKENS,
                temperature=0.3,
                messages=[{"role": "user", "content": summarization_prompt}],
            )
            return response.content[0].text.strip()
        except Exception as e:
            # Fallback to simple summary
            return f"Task: {prompt[:100]}. Outcome: {outcome}. Files: {len(files)} modified."

    def _read_artifact(self, session_dir: Path, name: str) -> Optional[str]:
        """Read a session artifact if it exists."""
        path = session_dir / name
        if path.exists():
            try:
                return path.read_text(encoding="utf-8")
            except Exception:
                return None
        return None

    def _extract_files_from_impl_log(self, impl_log: Optional[str]) -> list[str]:
        """Extract file paths from implementation log."""
        if not impl_log:
            return []

        # Match file paths in the log (backticked paths)
        files = re.findall(r"`([^`]+\.[a-zA-Z]{1,6})`", impl_log)
        return list(set(files))[:20]  # Dedupe and limit

    def _extract_issues_from_review(self, review: Optional[str]) -> list[str]:
        """Extract and categorize issues from review content."""
        if not review:
            return []

        issues = []

        # Common issue patterns
        issue_patterns = [
            (r"typescript.*any", "typescript_any_type"),
            (r"missing.*type", "missing_types"),
            (r"error.*handling", "error_handling"),
            (r"loading.*state", "loading_state"),
            (r"validation", "validation"),
            (r"security", "security"),
            (r"performance", "performance"),
            (r"accessibility", "accessibility"),
            (r"test.*missing", "missing_tests"),
            (r"import.*error", "import_error"),
        ]

        review_lower = review.lower()
        for pattern, issue_type in issue_patterns:
            if re.search(pattern, review_lower):
                issues.append(issue_type)

        return list(set(issues))

    def _extract_learnings(self, review: str) -> str:
        """Extract key learnings from review content."""
        # Look for fix instructions or important notes
        learnings = []

        # Find lines that look like fix instructions
        for line in review.split("\n"):
            line = line.strip()
            if any(keyword in line.lower() for keyword in ["fix:", "should", "must", "need to", "don't", "avoid"]):
                learnings.append(line)
                if len(learnings) >= 5:
                    break

        return "\n".join(learnings)

    async def backfill_all_sessions(self) -> dict:
        """
        Backfill all existing sessions into ChromaDB.

        Returns:
            Summary of backfill results
        """
        results = {"indexed": 0, "errors": 0, "skipped": 0, "details": []}

        if not SESSIONS_DIR.exists():
            return {"status": "error", "error": "Sessions directory not found"}

        for session_dir in SESSIONS_DIR.iterdir():
            if not session_dir.is_dir():
                continue

            if not (session_dir / "state.json").exists():
                results["skipped"] += 1
                continue

            result = await self.index_session(session_dir)

            if result.get("status") == "ok":
                results["indexed"] += 1
            else:
                results["errors"] += 1
                results["details"].append({
                    "session": session_dir.name,
                    "error": result.get("error"),
                })

        return results


async def main():
    """CLI entrypoint for backfilling sessions."""
    import sys

    if "--backfill" in sys.argv:
        print("Backfilling all sessions...")
        indexer = SessionIndexer()
        results = await indexer.backfill_all_sessions()
        print(f"Indexed: {results['indexed']}")
        print(f"Errors: {results['errors']}")
        print(f"Skipped: {results['skipped']}")
        if results.get("details"):
            print("\nErrors:")
            for detail in results["details"]:
                print(f"  - {detail['session']}: {detail['error']}")
    else:
        print("Usage: python -m src.rag.session_indexer --backfill")


if __name__ == "__main__":
    asyncio.run(main())
