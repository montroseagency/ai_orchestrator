"""
Reflection Engine — Post-task reflection for continuous self-improvement.

After each pipeline run, generates a structured reflection capturing:
- What went well / what didn't
- Surprising findings or edge cases
- Concrete prompt improvements for future sessions
- AGENTS.md update suggestions

Inspired by Addy Osmani's "Self-Improving Coding Agents" pattern:
agents that reflect on each task compound knowledge faster than
agents that just move on.
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import anthropic

from src.config import Config


@dataclass
class Reflection:
    """Structured reflection from a completed pipeline run."""
    session_id: str

    # What happened
    went_well: list[str] = field(default_factory=list)
    went_poorly: list[str] = field(default_factory=list)
    surprises: list[str] = field(default_factory=list)

    # Actionable improvements
    prompt_improvements: list[str] = field(default_factory=list)
    agents_md_updates: list[str] = field(default_factory=list)
    process_improvements: list[str] = field(default_factory=list)

    # Metrics
    quality_score: float = 0.0
    retry_count: int = 0
    healing_attempts: int = 0

    # Metadata
    created_at: str = ""
    model_used: str = ""

    def to_markdown(self) -> str:
        """Format reflection as markdown for storage."""
        lines = [
            f"# Reflection: {self.session_id}",
            f"> Generated: {self.created_at}",
            f"> Quality: {self.quality_score:.0%} | Retries: {self.retry_count} | Heals: {self.healing_attempts}",
            "",
        ]

        if self.went_well:
            lines.append("## What Went Well")
            for item in self.went_well:
                lines.append(f"- {item}")
            lines.append("")

        if self.went_poorly:
            lines.append("## What Went Poorly")
            for item in self.went_poorly:
                lines.append(f"- {item}")
            lines.append("")

        if self.surprises:
            lines.append("## Surprises")
            for item in self.surprises:
                lines.append(f"- {item}")
            lines.append("")

        if self.prompt_improvements:
            lines.append("## Prompt Improvements")
            for item in self.prompt_improvements:
                lines.append(f"- {item}")
            lines.append("")

        if self.agents_md_updates:
            lines.append("## Suggested AGENTS.md Updates")
            for item in self.agents_md_updates:
                lines.append(f"- {item}")
            lines.append("")

        if self.process_improvements:
            lines.append("## Process Improvements")
            for item in self.process_improvements:
                lines.append(f"- {item}")
            lines.append("")

        return "\n".join(lines)


class ReflectionEngine:
    """
    Generates post-task reflections using LLM analysis of pipeline artifacts.

    Uses Haiku for cheap, fast reflection generation. Reflections are
    stored as session artifacts and key learnings feed back into AGENTS.md
    and the RAG system.
    """

    REFLECTOR_MODEL = "claude-haiku-4-5"

    REFLECTION_PROMPT = """Analyze this completed coding task and generate a structured reflection.

## Original Task
{prompt}

## Plan
{plan}

## Implementation Result
Status: {status}
Files: {file_count} modified
Retries: {retry_count}
Quality Score: {quality_score}

## Review Feedback
{review}

## Errors Encountered
{errors}

Generate a reflection as JSON:
{{
  "went_well": ["1-3 things that worked well"],
  "went_poorly": ["1-3 things that didn't work or caused retries"],
  "surprises": ["0-2 unexpected findings or edge cases"],
  "prompt_improvements": ["1-3 specific changes to make prompts better for similar tasks"],
  "agents_md_updates": ["0-2 patterns/conventions to document for future sessions"],
  "process_improvements": ["0-2 changes to the pipeline process itself"]
}}

Be specific and actionable. Focus on learnings that apply to FUTURE tasks, not just this one.
Output ONLY the JSON."""

    def __init__(self, model: Optional[str] = None):
        self.model = model or self.REFLECTOR_MODEL
        self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    async def reflect(
        self,
        session_id: str,
        prompt: str,
        plan_content: str,
        status: str,
        review_content: str = "",
        files: list[dict] = None,
        retry_count: int = 0,
        quality_score: float = 0.0,
        healing_result=None,
        errors: list[str] = None,
    ) -> Reflection:
        """
        Generate a reflection for a completed pipeline run.

        Args:
            session_id: Session identifier
            prompt: Original user prompt
            plan_content: The plan.md content
            status: Final status (pass/fail)
            review_content: Review feedback
            files: Implementation files
            retry_count: Number of review retries
            quality_score: Quality score from QualityScorer
            healing_result: Result from SelfHealingLoop
            errors: List of error messages encountered

        Returns:
            Structured Reflection
        """
        file_count = len(files) if files else 0
        healing_attempts = healing_result.attempts if healing_result else 0

        # Format errors
        error_text = "\n".join(errors[:5]) if errors else "None"
        if healing_result and healing_result.fix_instructions:
            error_text += "\n\nSelf-healing errors:\n"
            error_text += healing_result.fix_instructions[0][:500] if healing_result.fix_instructions else ""

        reflection_prompt = self.REFLECTION_PROMPT.format(
            prompt=prompt[:500],
            plan=plan_content[:1000],
            status=status,
            file_count=file_count,
            retry_count=retry_count,
            quality_score=f"{quality_score:.0%}" if quality_score else "N/A",
            review=review_content[:1000] if review_content else "No review",
            errors=error_text[:1000],
        )

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.messages.create(
                    model=self.model,
                    max_tokens=600,
                    temperature=0.3,
                    messages=[{"role": "user", "content": reflection_prompt}],
                ),
            )

            return self._parse_reflection(
                response.content[0].text.strip(),
                session_id=session_id,
                quality_score=quality_score,
                retry_count=retry_count,
                healing_attempts=healing_attempts,
                model_used=self.model,
            )

        except Exception as e:
            # Return minimal reflection on failure
            return Reflection(
                session_id=session_id,
                went_poorly=[f"Reflection generation failed: {str(e)}"],
                quality_score=quality_score,
                retry_count=retry_count,
                healing_attempts=healing_attempts,
                created_at=datetime.now(timezone.utc).isoformat(),
            )

    def _parse_reflection(
        self,
        response_text: str,
        session_id: str,
        quality_score: float,
        retry_count: int,
        healing_attempts: int,
        model_used: str,
    ) -> Reflection:
        """Parse LLM response into Reflection."""
        try:
            import re
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found")

            data = json.loads(json_match.group())

            return Reflection(
                session_id=session_id,
                went_well=data.get("went_well", [])[:3],
                went_poorly=data.get("went_poorly", [])[:3],
                surprises=data.get("surprises", [])[:2],
                prompt_improvements=data.get("prompt_improvements", [])[:3],
                agents_md_updates=data.get("agents_md_updates", [])[:2],
                process_improvements=data.get("process_improvements", [])[:2],
                quality_score=quality_score,
                retry_count=retry_count,
                healing_attempts=healing_attempts,
                created_at=datetime.now(timezone.utc).isoformat(),
                model_used=model_used,
            )

        except (json.JSONDecodeError, ValueError):
            return Reflection(
                session_id=session_id,
                went_poorly=["Could not parse reflection response"],
                quality_score=quality_score,
                retry_count=retry_count,
                healing_attempts=healing_attempts,
                created_at=datetime.now(timezone.utc).isoformat(),
                model_used=model_used,
            )

    def save_reflection(self, reflection: Reflection, session_dir: Path) -> Path:
        """
        Save reflection as session artifact.

        Args:
            reflection: The reflection to save
            session_dir: Session directory path

        Returns:
            Path to saved reflection file
        """
        path = session_dir / "reflection.md"
        path.write_text(reflection.to_markdown(), encoding="utf-8")
        return path
