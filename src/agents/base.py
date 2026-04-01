"""
Base Agent — Common interface for all Vibe Coding Team agents.

Supports two backends:
  - API mode (default): direct Anthropic API calls using ANTHROPIC_API_KEY
  - CLI mode: spawns `claude --print` subprocesses, works with Claude Pro/Max subscription
"""

import asyncio
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Optional

from src.config import Config


class BaseAgent:
    """Base class for all agents in the Vibe Coding Team."""

    # Default agents this agent type can communicate with
    DEFAULT_COMMUNICATION_TARGETS: dict[str, list[str]] = {
        "conductor": ["planner", "creative_brain", "implementer", "reviewer"],
        "planner": ["conductor", "implementer", "creative_brain"],
        "creative_brain": ["conductor", "planner", "implementer"],
        "implementer": ["conductor", "planner", "creative_brain", "reviewer"],
        "reviewer": ["conductor", "implementer"],
    }

    def __init__(self, name: str, system_prompt_path: str, model: str = None):
        self.name = name
        self.system_prompt_path = Path(system_prompt_path)
        self.model = model or Config.DEFAULT_MODEL
        self._system_prompt: str | None = None

        # Only import anthropic and create client in API mode
        if not Config.USE_CLAUDE_CLI:
            import anthropic as _anthropic
            self.client = _anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        else:
            self.client = None

        # Communication support
        self.outbox: list = []  # Pending AgentMessage objects
        self.can_communicate_with: list[str] = self._get_communication_targets()

    def _get_communication_targets(self) -> list[str]:
        """Get list of agents this agent can communicate with."""
        # Normalize name (e.g., "implementer_frontend" -> "implementer")
        base_name = self.name.lower().split("_")[0] if "_" in self.name.lower() else self.name.lower()
        return self.DEFAULT_COMMUNICATION_TARGETS.get(base_name, [])

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
        thinking_tokens: int = 0,
    ) -> str:
        """
        Call Claude asynchronously — routes to API or CLI backend automatically.

        Args:
            user_message: The human turn message
            temperature: Sampling temperature (ignored in CLI mode)
            max_tokens: Max response tokens (output only; thinking budget added on top)
            extra_system: Optional additional system instructions appended to base prompt
            thinking_tokens: Extended thinking budget (0 = disabled).
                             CLI mode maps this to --effort level instead.
        """
        system = self._load_system_prompt()
        if extra_system:
            system = f"{system}\n\n---\n\n{extra_system}"

        if Config.USE_CLAUDE_CLI:
            return await self._call_cli(system, user_message, thinking_tokens)
        else:
            return await self._call_api(system, user_message, temperature, max_tokens, thinking_tokens)

    async def _call_api(
        self,
        system: str,
        user_message: str,
        temperature: float,
        max_tokens: int,
        thinking_tokens: int,
    ) -> str:
        """Direct Anthropic API call with prompt caching and optional extended thinking."""

        # Prompt caching: ~90% token savings on repeated system prompt calls
        system_blocks = [
            {"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}
        ]

        kwargs: dict = dict(
            model=self.model,
            system=system_blocks,
            messages=[{"role": "user", "content": user_message}],
        )

        if thinking_tokens > 0:
            # Extended thinking requires temperature=1.0 (API requirement)
            # max_tokens must cover thinking budget + desired output tokens
            kwargs["thinking"] = {"type": "enabled", "budget_tokens": thinking_tokens}
            kwargs["temperature"] = 1.0
            kwargs["max_tokens"] = thinking_tokens + max_tokens
        else:
            kwargs["temperature"] = temperature
            kwargs["max_tokens"] = max_tokens

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.client.messages.create(**kwargs),
        )

        # Skip thinking blocks — return first text block
        for block in response.content:
            if block.type == "text":
                return block.text
        return ""

    async def _call_cli(
        self,
        system: str,
        user_message: str,
        thinking_tokens: int,
    ) -> str:
        """
        Call Claude via `claude --print` subprocess.

        Uses your logged-in Claude Pro/Max subscription account — no API key needed.
        Extended thinking is mapped to --effort levels (low/medium/high/max).
        """
        # Map thinking_tokens → --effort level
        if thinking_tokens == 0:
            effort = Config.CLAUDE_CLI_EFFORT_FAST
        elif thinking_tokens <= 5000:
            effort = Config.CLAUDE_CLI_EFFORT_NORMAL
        elif thinking_tokens <= 10000:
            effort = Config.CLAUDE_CLI_EFFORT_HEAVY
        else:
            effort = "max"

        # Map internal model IDs to CLI-accepted aliases
        _model_map = {
            "claude-haiku-4-5-20251001": "haiku",
            "claude-haiku-4-5": "haiku",
            "claude-sonnet-4-5": "sonnet",
            "claude-opus-4-5": "opus",
            "claude-opus-4-6": "opus",
        }
        model = _model_map.get(self.model, self.model)

        cmd = [
            Config.CLAUDE_CLI_PATH,
            "--print",
            "--model", model,
            "--system-prompt", system,
            "--effort", effort,
            "--output-format", "json",
            "--no-session-persistence",
            "--tools", "",          # disable built-in file tools — agents use prompt context
            "--dangerously-skip-permissions",  # non-interactive, no file writes
            user_message,
        ]

        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=600,
                )
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"[{self.name}] Claude CLI timed out after 600s")

        if result.returncode != 0:
            stderr = result.stderr.strip()
            raise RuntimeError(f"[{self.name}] Claude CLI failed (exit {result.returncode}): {stderr}")

        # Parse JSON output — Claude CLI returns {"result": "...", "type": "result", ...}
        stdout = result.stdout.strip()
        try:
            data = json.loads(stdout)
            return data.get("result", stdout)
        except json.JSONDecodeError:
            return stdout

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

    # ─────────────────────────────────────────────────────────────────
    # Inter-Agent Communication
    # ─────────────────────────────────────────────────────────────────

    def ask(
        self,
        target: str,
        question: str,
        msg_type: str = "QUESTION",
        priority: str = "normal",
        context: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> bool:
        """
        Queue a question to another agent.

        Args:
            target: Name of target agent
            question: Question to ask
            msg_type: Message type ("QUESTION", "FEASIBILITY_CHECK", "IMPLEMENTATION_QUESTION")
            priority: Priority level ("low", "normal", "high", "critical")
            context: Optional additional context
            session_id: Optional session ID for tracking

        Returns:
            True if message was queued, False if target not allowed
        """
        if not self._can_send_to(target):
            return False

        try:
            from src.coordination import create_question, Priority, MessageType

            priority_enum = getattr(Priority, priority.upper(), Priority.NORMAL)

            message = create_question(
                from_agent=self.name,
                to_agent=target,
                question=question,
                context=context,
                priority=priority_enum,
                session_id=session_id,
            )

            # Override message type if specified
            if msg_type != "QUESTION":
                message.message_type = getattr(MessageType, msg_type, MessageType.QUESTION)

            self.outbox.append(message)
            return True

        except ImportError:
            return False

    def constrain(
        self,
        target: str,
        constraint: str,
        context: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> bool:
        """
        Send a constraint to another agent.

        Args:
            target: Name of target agent
            constraint: Constraint requirement
            context: Optional additional context
            session_id: Optional session ID

        Returns:
            True if message was queued
        """
        if not self._can_send_to(target):
            return False

        try:
            from src.coordination import create_constraint

            message = create_constraint(
                from_agent=self.name,
                to_agent=target,
                constraint=constraint,
                context=context,
                session_id=session_id,
            )
            self.outbox.append(message)
            return True

        except ImportError:
            return False

    def suggest(
        self,
        target: str,
        suggestion: str,
        context: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> bool:
        """
        Send a suggestion to another agent.

        Args:
            target: Name of target agent
            suggestion: Suggested approach or idea
            context: Optional additional context
            session_id: Optional session ID

        Returns:
            True if message was queued
        """
        if not self._can_send_to(target):
            return False

        try:
            from src.coordination import create_suggestion

            message = create_suggestion(
                from_agent=self.name,
                to_agent=target,
                suggestion=suggestion,
                context=context,
                session_id=session_id,
            )
            self.outbox.append(message)
            return True

        except ImportError:
            return False

    def flush_outbox(self) -> list:
        """
        Get and clear all pending messages from outbox.

        Returns:
            List of AgentMessage objects that were pending
        """
        messages = list(self.outbox)
        self.outbox.clear()
        return messages

    def has_pending_messages(self) -> bool:
        """Check if there are pending messages in the outbox."""
        return len(self.outbox) > 0

    def _can_send_to(self, target: str) -> bool:
        """Check if this agent can send messages to the target."""
        # Normalize target name
        target_base = target.lower().split("_")[0] if "_" in target.lower() else target.lower()
        allowed_bases = [t.lower() for t in self.can_communicate_with]
        return target_base in allowed_bases or target.lower() in [t.lower() for t in self.can_communicate_with]
