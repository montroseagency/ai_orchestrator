"""
Base Agent — Common interface for all Vibe Coding Team agents.
"""

import asyncio
import json
import re
from typing import Any
import anthropic

from src.config import Config


class BaseAgent:
    """Base class for all agents in the Vibe Coding Team."""

    def __init__(self, name: str, system_prompt_path: str, model: str = None):
        self.name = name
        self.system_prompt_path = Path(system_prompt_path)
        self.model = model or Config.DEFAULT_MODEL
        self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        self._system_prompt: str | None = None

    def _load_system_prompt(self) -> str:
        """Load and cache system prompt from markdown file."""
        if self._system_prompt is None:
            if not self.system_prompt_path.exists():
                raise FileNotFoundError(
                    f"System prompt not found: {self.system_prompt_path}"
                )
            self._system_prompt = self.system_prompt_path.read_text(encoding="utf-8")
        return self._system_prompt

    async def call(
        self,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 8192,
        extra_system: str = "",
    ) -> str:
        """
        Call the Claude API asynchronously.

        Args:
            user_message: The human turn message
            temperature: Sampling temperature (0=deterministic, 1=creative)
            max_tokens: Max response tokens
            extra_system: Optional additional system instructions appended to base prompt
        """
        system = self._load_system_prompt()
        if extra_system:
            system = f"{system}\n\n---\n\n{extra_system}"

        # Run synchronous API call in thread pool to not block event loop
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=[{"role": "user", "content": user_message}],
            ),
        )

        return response.content[0].text

    def extract_json(self, text: str) -> dict:
        """
        Extract JSON object from agent response text.
        Handles both raw JSON and JSON wrapped in markdown code blocks.
        """
        # Try to find JSON in code block first
        code_block_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if code_block_match:
            return json.loads(code_block_match.group(1))

        # Try parsing the whole response as JSON
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        # Try to find the largest JSON object in the text
        # Look for outermost { ... }
        start = text.find("{")
        if start != -1:
            depth = 0
            for i, char in enumerate(text[start:], start):
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[start : i + 1])
                        except json.JSONDecodeError:
                            break

        raise ValueError(
            f"Could not extract valid JSON from {self.name} response. "
            f"Response preview: {text[:200]}..."
        )
