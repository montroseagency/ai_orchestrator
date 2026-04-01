"""
Stuck Detector — Detect agents looping on the same error and auto-escalate.

When an agent fails 3+ times on the same type of error, it's likely
stuck in a loop. This detector catches that pattern and can:
1. Kill the current approach
2. Suggest an alternative strategy
3. Escalate to the conductor with context

Inspired by: Addy Osmani's kill criteria pattern — "Kill agents stuck
3+ iterations on same error and reassign."
"""

import hashlib
import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class StuckState:
    """Tracks whether an agent is stuck."""
    is_stuck: bool = False
    error_signature: str = ""
    repetition_count: int = 0
    suggested_action: str = ""
    error_history: list[str] = field(default_factory=list)


class StuckDetector:
    """
    Detects when agents are stuck in error loops.

    Analyzes error patterns across iterations to determine if an agent
    is repeating the same mistake. Uses error fingerprinting to match
    similar (not just identical) errors.
    """

    # How many times the same error must repeat before "stuck"
    DEFAULT_THRESHOLD = 3

    # Maximum error history to keep
    MAX_HISTORY = 20

    def __init__(self, threshold: int = 3):
        """
        Initialize stuck detector.

        Args:
            threshold: Number of repeated errors before declaring stuck
        """
        self.threshold = threshold

        # Track errors per agent: {agent_name: [(signature, error_text)]}
        self._error_history: dict[str, list[tuple[str, str]]] = {}

        # Track consecutive same-error counts: {agent_name: {signature: count}}
        self._error_counts: dict[str, dict[str, int]] = {}

    def record_error(self, agent_name: str, error_text: str) -> StuckState:
        """
        Record an error and check if agent is stuck.

        Args:
            agent_name: Name of the agent
            error_text: Error message or output

        Returns:
            StuckState indicating whether agent is stuck
        """
        signature = self._fingerprint_error(error_text)

        # Initialize tracking
        if agent_name not in self._error_history:
            self._error_history[agent_name] = []
            self._error_counts[agent_name] = {}

        # Record error
        self._error_history[agent_name].append((signature, error_text))
        if len(self._error_history[agent_name]) > self.MAX_HISTORY:
            self._error_history[agent_name] = self._error_history[agent_name][-self.MAX_HISTORY:]

        # Count this error signature
        self._error_counts[agent_name][signature] = (
            self._error_counts[agent_name].get(signature, 0) + 1
        )

        count = self._error_counts[agent_name][signature]

        if count >= self.threshold:
            return StuckState(
                is_stuck=True,
                error_signature=signature,
                repetition_count=count,
                suggested_action=self._suggest_action(agent_name, error_text, count),
                error_history=[e[1][:200] for e in self._error_history[agent_name][-5:]],
            )

        return StuckState(
            is_stuck=False,
            error_signature=signature,
            repetition_count=count,
            error_history=[e[1][:200] for e in self._error_history[agent_name][-3:]],
        )

    def record_success(self, agent_name: str):
        """
        Record a success, resetting error counts for the agent.

        Args:
            agent_name: Name of the agent
        """
        self._error_counts.pop(agent_name, None)
        self._error_history.pop(agent_name, None)

    def is_stuck(self, agent_name: str) -> bool:
        """Check if an agent is currently stuck."""
        counts = self._error_counts.get(agent_name, {})
        return any(count >= self.threshold for count in counts.values())

    def get_state(self, agent_name: str) -> StuckState:
        """Get current stuck state for an agent."""
        counts = self._error_counts.get(agent_name, {})

        for signature, count in counts.items():
            if count >= self.threshold:
                recent_errors = [
                    e[1][:200] for e in self._error_history.get(agent_name, [])[-5:]
                ]
                return StuckState(
                    is_stuck=True,
                    error_signature=signature,
                    repetition_count=count,
                    suggested_action=self._suggest_action(agent_name, "", count),
                    error_history=recent_errors,
                )

        return StuckState(is_stuck=False)

    def _fingerprint_error(self, error_text: str) -> str:
        """
        Create a fingerprint for an error to match similar errors.

        Normalizes the error by:
        - Removing line numbers (they change between attempts)
        - Removing file paths (focus on error type)
        - Removing timestamps
        - Lowercasing

        This allows matching "NameError: 'foo' at line 42" with
        "NameError: 'foo' at line 58" as the same underlying issue.
        """
        normalized = error_text.lower()

        # Remove line numbers
        normalized = re.sub(r"line \d+", "line N", normalized)
        normalized = re.sub(r":\d+:\d+", ":N:N", normalized)

        # Remove file paths (keep just filename)
        normalized = re.sub(r"/[\w/.-]+/(\w+\.\w+)", r"\1", normalized)

        # Remove timestamps
        normalized = re.sub(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}", "TIMESTAMP", normalized)

        # Remove hex addresses
        normalized = re.sub(r"0x[0-9a-f]+", "0xHEX", normalized)

        # Extract the core error type/message (first meaningful line)
        lines = [l.strip() for l in normalized.split("\n") if l.strip()]
        core_lines = []
        for line in lines[:5]:
            if any(kw in line for kw in ["error", "fail", "exception", "cannot", "undefined", "not found"]):
                core_lines.append(line)

        if core_lines:
            normalized = " | ".join(core_lines[:3])
        elif lines:
            normalized = lines[0][:200]

        # Generate hash
        return hashlib.md5(normalized.encode()).hexdigest()[:12]

    def _suggest_action(self, agent_name: str, error_text: str, count: int) -> str:
        """
        Suggest an action when an agent is stuck.

        Different suggestions based on how stuck the agent is.
        """
        error_lower = error_text.lower()

        # Identify error category for targeted suggestions
        if any(kw in error_lower for kw in ["import", "module not found", "cannot find"]):
            return (
                f"Agent {agent_name} stuck on import error ({count}x). "
                "Try: check dependency installation, verify module paths, "
                "or use a different import strategy."
            )

        if any(kw in error_lower for kw in ["type", "typescript", "tsc"]):
            return (
                f"Agent {agent_name} stuck on type error ({count}x). "
                "Try: simplify types, use 'unknown' with type guards, "
                "or temporarily broaden types and narrow later."
            )

        if any(kw in error_lower for kw in ["syntax", "unexpected token", "parse"]):
            return (
                f"Agent {agent_name} stuck on syntax error ({count}x). "
                "Try: regenerate the entire file from scratch rather than "
                "patching the existing implementation."
            )

        if any(kw in error_lower for kw in ["test", "assert", "expect"]):
            return (
                f"Agent {agent_name} stuck on test failure ({count}x). "
                "Try: re-read the test expectations, adjust implementation "
                "to match test contracts rather than the reverse."
            )

        if count >= self.threshold + 2:
            return (
                f"Agent {agent_name} severely stuck ({count}x). "
                "ESCALATE: This approach is failing. Consider an entirely "
                "different implementation strategy or decompose the task further."
            )

        return (
            f"Agent {agent_name} stuck on same error ({count}x). "
            "Try a fundamentally different approach to solve this."
        )

    def format_stuck_report(self, agent_name: str) -> str:
        """Format a report about why an agent is stuck, for conductor escalation."""
        state = self.get_state(agent_name)
        if not state.is_stuck:
            return ""

        lines = [
            f"## Stuck Agent Report: {agent_name}",
            f"Error repeated {state.repetition_count} times (threshold: {self.threshold})",
            f"**Suggested action:** {state.suggested_action}",
            "",
            "### Recent Error History",
        ]

        for i, error in enumerate(state.error_history, 1):
            lines.append(f"{i}. {error}")

        return "\n".join(lines)

    def reset(self, agent_name: Optional[str] = None):
        """Reset stuck detection state."""
        if agent_name:
            self._error_history.pop(agent_name, None)
            self._error_counts.pop(agent_name, None)
        else:
            self._error_history.clear()
            self._error_counts.clear()
