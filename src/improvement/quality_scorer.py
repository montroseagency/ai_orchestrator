"""
LLM-as-Judge Quality Scorer — Evaluate pipeline outputs on multiple dimensions.

Uses a cheap model (Haiku) to score each pipeline output, creating a
feedback signal for continuous improvement. Scores feed back into the
RAG system to help future sessions learn which approaches produce
high-quality results.

Dimensions scored:
- Correctness: Does the implementation match the plan?
- Completeness: Were all acceptance criteria addressed?
- Code quality: Style, patterns, error handling
- Architecture: Appropriate abstractions and separation
- Overall: Weighted composite score
"""

import asyncio
import json
from dataclasses import dataclass, field
from typing import Optional
import anthropic

from src.config import Config


@dataclass
class QualityScore:
    """Quality scores for a pipeline output."""
    correctness: float = 0.0    # 0-1: Does it match the plan?
    completeness: float = 0.0   # 0-1: All acceptance criteria met?
    code_quality: float = 0.0   # 0-1: Style, patterns, error handling
    architecture: float = 0.0   # 0-1: Appropriate abstractions
    overall: float = 0.0        # 0-1: Weighted composite

    # Qualitative feedback
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    improvement_suggestions: list[str] = field(default_factory=list)

    # Metadata
    model_used: str = ""
    tokens_used: int = 0

    def to_dict(self) -> dict:
        return {
            "correctness": self.correctness,
            "completeness": self.completeness,
            "code_quality": self.code_quality,
            "architecture": self.architecture,
            "overall": self.overall,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "improvement_suggestions": self.improvement_suggestions,
        }

    def summary(self) -> str:
        """One-line summary of scores."""
        return (
            f"Quality: {self.overall:.0%} "
            f"(correct={self.correctness:.0%}, "
            f"complete={self.completeness:.0%}, "
            f"quality={self.code_quality:.0%}, "
            f"arch={self.architecture:.0%})"
        )


class QualityScorer:
    """
    Evaluates pipeline outputs using an LLM-as-Judge pattern.

    Uses Haiku for fast, cheap evaluation. The scoring prompt is designed
    to produce structured JSON output with scores and qualitative feedback.
    """

    # Model for scoring (cheap and fast)
    SCORER_MODEL = "claude-haiku-4-5"

    # Weights for composite score
    WEIGHTS = {
        "correctness": 0.35,
        "completeness": 0.25,
        "code_quality": 0.25,
        "architecture": 0.15,
    }

    SCORING_PROMPT = """You are a code quality judge. Score this implementation on a 0.0-1.0 scale.

## Plan
{plan}

## Implementation Files
{implementation}

## Review Feedback
{review}

Score on these dimensions (0.0 = terrible, 1.0 = perfect):

1. **correctness**: Does the implementation match the plan's requirements?
2. **completeness**: Were all acceptance criteria addressed?
3. **code_quality**: Code style, patterns, error handling, readability
4. **architecture**: Appropriate abstractions, separation of concerns

Also provide:
- strengths: List of 1-3 things done well
- weaknesses: List of 1-3 things that need improvement
- improvement_suggestions: List of 1-3 actionable suggestions

Output ONLY valid JSON:
{{
  "correctness": 0.0,
  "completeness": 0.0,
  "code_quality": 0.0,
  "architecture": 0.0,
  "strengths": ["..."],
  "weaknesses": ["..."],
  "improvement_suggestions": ["..."]
}}"""

    def __init__(self, model: Optional[str] = None):
        """
        Initialize the quality scorer.

        Args:
            model: Model to use for scoring (defaults to Haiku)
        """
        self.model = model or self.SCORER_MODEL
        self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    async def score_implementation(
        self,
        plan_content: str,
        implementation_files: list[dict],
        review_content: str = "",
    ) -> QualityScore:
        """
        Score an implementation against the plan.

        Args:
            plan_content: The plan.md content
            implementation_files: List of file dicts from implementer
            review_content: Optional review feedback

        Returns:
            QualityScore with dimension scores and feedback
        """
        # Format implementation files
        impl_parts = []
        for f in implementation_files[:10]:  # Limit to 10 files
            path = f.get("path", "unknown")
            content = f.get("content", "")
            summary = f.get("change_summary", "")
            # Truncate content for budget
            if len(content) > 2000:
                content = content[:2000] + "\n... (truncated)"
            impl_parts.append(f"### {path}\n{summary}\n```\n{content}\n```")

        impl_text = "\n\n".join(impl_parts) if impl_parts else "No files produced"

        # Build prompt
        prompt = self.SCORING_PROMPT.format(
            plan=plan_content[:3000],
            implementation=impl_text,
            review=review_content[:1000] if review_content else "No review yet",
        )

        try:
            # Run scoring in thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.messages.create(
                    model=self.model,
                    max_tokens=500,
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}],
                ),
            )

            response_text = response.content[0].text.strip()
            tokens_used = response.usage.input_tokens + response.usage.output_tokens

            return self._parse_score(response_text, tokens_used)

        except Exception as e:
            # Return zero scores on failure
            return QualityScore(
                weaknesses=[f"Scoring failed: {str(e)}"],
                model_used=self.model,
            )

    def _parse_score(self, response_text: str, tokens_used: int) -> QualityScore:
        """Parse LLM response into QualityScore."""
        try:
            # Try to extract JSON from response
            import re

            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in response")

            data = json.loads(json_match.group())

            score = QualityScore(
                correctness=self._clamp(data.get("correctness", 0)),
                completeness=self._clamp(data.get("completeness", 0)),
                code_quality=self._clamp(data.get("code_quality", 0)),
                architecture=self._clamp(data.get("architecture", 0)),
                strengths=data.get("strengths", [])[:3],
                weaknesses=data.get("weaknesses", [])[:3],
                improvement_suggestions=data.get("improvement_suggestions", [])[:3],
                model_used=self.model,
                tokens_used=tokens_used,
            )

            # Calculate weighted composite
            score.overall = (
                score.correctness * self.WEIGHTS["correctness"] +
                score.completeness * self.WEIGHTS["completeness"] +
                score.code_quality * self.WEIGHTS["code_quality"] +
                score.architecture * self.WEIGHTS["architecture"]
            )

            return score

        except (json.JSONDecodeError, ValueError):
            return QualityScore(
                weaknesses=["Could not parse quality score"],
                model_used=self.model,
                tokens_used=tokens_used,
            )

    def _clamp(self, value: float) -> float:
        """Clamp a value to [0, 1] range."""
        try:
            return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            return 0.0

    async def score_plan(self, prompt: str, plan_content: str) -> QualityScore:
        """
        Score a plan's quality relative to the user prompt.

        Lighter evaluation focused on plan structure and coverage.
        """
        scoring_prompt = f"""Score this plan's quality on 0.0-1.0:

## User Request
{prompt[:1000]}

## Plan
{plan_content[:3000]}

Score:
1. correctness: Does the plan address the actual request?
2. completeness: Are all aspects of the request covered?
3. code_quality: Is the plan clear and well-structured?
4. architecture: Is the proposed approach sound?

Output ONLY valid JSON:
{{"correctness": 0.0, "completeness": 0.0, "code_quality": 0.0, "architecture": 0.0, "strengths": ["..."], "weaknesses": ["..."], "improvement_suggestions": ["..."]}}"""

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.messages.create(
                    model=self.model,
                    max_tokens=400,
                    temperature=0.1,
                    messages=[{"role": "user", "content": scoring_prompt}],
                ),
            )

            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            return self._parse_score(response.content[0].text.strip(), tokens_used)

        except Exception:
            return QualityScore(model_used=self.model)
