"""
Lesson Extractor — Extracts learnable patterns from successful review retries.

When a review fails but the subsequent retry passes, the fix instructions
that worked become valuable lessons to store for future sessions.
"""

import json
import re
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from .server import get_rag_client


@dataclass
class ExtractedLesson:
    """A lesson extracted from a successful fix."""
    issue_type: str
    fix_description: str
    context: str
    source_session: str
    confidence: float  # How confident we are this is a useful lesson


class LessonExtractor:
    """
    Extracts lessons from sessions where review retries succeeded.

    Logic:
    1. Find review attempts (review_attempt_1.md, review_attempt_2.md, etc.)
    2. If attempt N failed but attempt N+1 exists, the fix instructions likely worked
    3. Extract and categorize those fix instructions as lessons
    """

    # Issue type patterns for categorization
    ISSUE_PATTERNS = {
        "typescript_any_type": [
            r"any\s+type",
            r"don't use any",
            r"avoid any",
            r"use unknown instead of any",
        ],
        "missing_error_handling": [
            r"error handling",
            r"catch.*error",
            r"try.*catch",
            r"handle.*exception",
        ],
        "missing_loading_state": [
            r"loading state",
            r"isLoading",
            r"loading indicator",
            r"skeleton",
        ],
        "missing_validation": [
            r"validation",
            r"validate input",
            r"input sanitization",
        ],
        "accessibility": [
            r"accessibility",
            r"aria-",
            r"screen reader",
            r"keyboard navigation",
        ],
        "security": [
            r"security",
            r"xss",
            r"injection",
            r"sanitize",
            r"escape",
        ],
        "performance": [
            r"performance",
            r"memoize",
            r"useMemo",
            r"useCallback",
            r"optimize",
        ],
        "import_error": [
            r"import.*error",
            r"module not found",
            r"cannot find module",
        ],
        "type_mismatch": [
            r"type.*mismatch",
            r"incompatible type",
            r"expected.*got",
        ],
        "missing_tests": [
            r"test.*missing",
            r"add.*test",
            r"unit test",
        ],
    }

    def __init__(self, rag_client=None):
        """
        Initialize the lesson extractor.

        Args:
            rag_client: Optional RagServer instance
        """
        self.rag = rag_client or get_rag_client()

    def extract_lessons_from_session(self, session_dir: Path) -> list[ExtractedLesson]:
        """
        Extract lessons from a session's review attempts.

        Args:
            session_dir: Path to session directory

        Returns:
            List of extracted lessons
        """
        lessons = []

        # Find all review attempt files
        review_files = sorted(session_dir.glob("review_attempt_*.md"))

        if len(review_files) < 2:
            # Need at least 2 attempts (one failure + one success)
            return lessons

        # Check each consecutive pair
        for i in range(len(review_files) - 1):
            current_review = review_files[i]
            next_review = review_files[i + 1]

            # Read the failed review to extract fix instructions
            try:
                review_content = current_review.read_text(encoding="utf-8")
            except Exception:
                continue

            # Only extract if this was a failure (next attempt exists = retry happened)
            if self._is_failed_review(review_content):
                extracted = self._extract_fix_instructions(review_content)
                for fix in extracted:
                    lesson = self._create_lesson(
                        fix_instruction=fix["instruction"],
                        context=fix["context"],
                        source_session=session_dir.name,
                    )
                    if lesson:
                        lessons.append(lesson)

        return lessons

    def _is_failed_review(self, review_content: str) -> bool:
        """Check if a review indicates failure."""
        # Look for common failure indicators
        fail_patterns = [
            r"# Review:\s*FAIL",
            r"##\s*Status:\s*FAIL",
            r"VERDICT:\s*FAIL",
            r"\bFAIL\b",
        ]
        for pattern in fail_patterns:
            if re.search(pattern, review_content, re.IGNORECASE):
                return True
        return False

    def _extract_fix_instructions(self, review_content: str) -> list[dict]:
        """Extract fix instructions from a failed review."""
        fixes = []

        # Pattern 1: Lines starting with "Fix:" or "- Fix:"
        fix_pattern = r"[-*]?\s*Fix:\s*(.+?)(?=\n[-*]|\n\n|\Z)"
        for match in re.finditer(fix_pattern, review_content, re.IGNORECASE | re.DOTALL):
            fixes.append({
                "instruction": match.group(1).strip(),
                "context": self._get_context(review_content, match.start()),
            })

        # Pattern 2: Lines with "should" or "must" (imperative fixes)
        imperative_pattern = r"[-*]\s*(\w+\s+(?:should|must|needs? to)\s+.+?)(?=\n[-*]|\n\n|\Z)"
        for match in re.finditer(imperative_pattern, review_content, re.IGNORECASE | re.DOTALL):
            instruction = match.group(1).strip()
            if len(instruction) > 20:  # Avoid short fragments
                fixes.append({
                    "instruction": instruction,
                    "context": self._get_context(review_content, match.start()),
                })

        # Pattern 3: Numbered issues with descriptions
        numbered_pattern = r"\d+\.\s*\*\*\[([A-Z]+)\]\*\*\s*(.+?)(?=\n\d+\.|\n\n|\Z)"
        for match in re.finditer(numbered_pattern, review_content, re.DOTALL):
            severity = match.group(1)
            description = match.group(2).strip()
            if severity in ("CRITICAL", "ERROR", "INCORRECT"):
                fixes.append({
                    "instruction": description,
                    "context": f"Severity: {severity}",
                })

        return fixes

    def _get_context(self, content: str, position: int) -> str:
        """Get surrounding context for a fix instruction."""
        # Get the section header (## or ###) above this position
        lines_before = content[:position].split("\n")
        for line in reversed(lines_before):
            if line.startswith("#"):
                return line.strip("# ").strip()
        return ""

    def _categorize_issue(self, instruction: str) -> str:
        """Categorize a fix instruction into an issue type."""
        instruction_lower = instruction.lower()

        for issue_type, patterns in self.ISSUE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, instruction_lower):
                    return issue_type

        return "general"

    def _create_lesson(
        self,
        fix_instruction: str,
        context: str,
        source_session: str,
    ) -> Optional[ExtractedLesson]:
        """Create a lesson from a fix instruction."""
        if len(fix_instruction) < 20:
            return None

        issue_type = self._categorize_issue(fix_instruction)

        # Calculate confidence based on specificity
        confidence = 0.5
        if len(fix_instruction) > 50:
            confidence += 0.1
        if issue_type != "general":
            confidence += 0.2
        if context:
            confidence += 0.1

        return ExtractedLesson(
            issue_type=issue_type,
            fix_description=fix_instruction[:500],
            context=context[:200],
            source_session=source_session,
            confidence=min(confidence, 1.0),
        )

    def record_lessons(self, lessons: list[ExtractedLesson]) -> dict:
        """
        Record extracted lessons to the RAG database.

        Args:
            lessons: List of lessons to record

        Returns:
            Summary of recording results
        """
        results = {"recorded": 0, "errors": 0}

        for lesson in lessons:
            if lesson.confidence < 0.5:
                continue

            # Generate unique lesson ID
            lesson_id = hashlib.md5(
                f"{lesson.issue_type}:{lesson.fix_description[:100]}".encode()
            ).hexdigest()[:16]

            result = self.rag.record_lesson(
                lesson_id=lesson_id,
                issue_type=lesson.issue_type,
                fix_that_worked=lesson.fix_description,
                context=lesson.context,
                source_session=lesson.source_session,
            )

            if result.get("status") == "ok":
                results["recorded"] += 1
            else:
                results["errors"] += 1

        return results

    def process_session(self, session_dir: Path) -> dict:
        """
        Extract and record lessons from a single session.

        Args:
            session_dir: Path to session directory

        Returns:
            Processing results
        """
        lessons = self.extract_lessons_from_session(session_dir)
        if not lessons:
            return {"status": "no_lessons", "count": 0}

        result = self.record_lessons(lessons)
        return {
            "status": "ok",
            "extracted": len(lessons),
            **result,
        }


class PatternDetector:
    """
    Detects patterns across multiple lessons.

    When 3+ similar lessons are found, they become candidates for
    automatic prompt patching.
    """

    def __init__(self, rag_client=None):
        self.rag = rag_client or get_rag_client()

    def find_recurring_patterns(self, min_occurrences: int = 3) -> list[dict]:
        """
        Find issue types that recur frequently.

        Args:
            min_occurrences: Minimum times an issue must appear

        Returns:
            List of recurring patterns with their lessons
        """
        # Get all lessons
        all_lessons = self.rag.search_lessons("", n=100)

        # Group by issue type
        by_type: dict[str, list] = {}
        for lesson in all_lessons:
            issue_type = lesson.get("issue_type", "general")
            if issue_type not in by_type:
                by_type[issue_type] = []
            by_type[issue_type].append(lesson)

        # Filter to recurring patterns
        recurring = []
        for issue_type, lessons in by_type.items():
            if len(lessons) >= min_occurrences:
                recurring.append({
                    "issue_type": issue_type,
                    "occurrences": len(lessons),
                    "lessons": lessons[:5],  # Top 5 examples
                })

        return sorted(recurring, key=lambda x: x["occurrences"], reverse=True)

    def generate_patch_content(self, pattern: dict) -> str:
        """
        Generate prompt patch content from a recurring pattern.

        Args:
            pattern: Pattern dict from find_recurring_patterns

        Returns:
            Markdown content for the patch
        """
        issue_type = pattern["issue_type"]
        lessons = pattern["lessons"]

        # Format title
        title = issue_type.replace("_", " ").title()

        content = f"""# Patch: {title}
> Auto-generated from {pattern['occurrences']} similar review findings

## Rules to Follow

"""
        for i, lesson in enumerate(lessons[:3], 1):
            fix = lesson.get("fix", "")
            content += f"{i}. {fix}\n"

        content += """
## Context

This patch was automatically generated because similar issues appeared
in multiple review cycles. Following these rules should prevent future
review failures of this type.
"""

        return content
