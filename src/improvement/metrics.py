"""
Metrics Tracker — Track and persist quality metrics across sessions.

Creates a data flywheel: metrics from each session feed back into
the system to identify trends, regressions, and improvement opportunities.

Tracks:
- Token usage per agent per session
- Pass/fail rates and retry counts
- Quality scores over time
- Self-healing effectiveness
- Time per pipeline phase
"""

import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.config import BRAIN_ROOT


@dataclass
class PhaseMetrics:
    """Metrics for a single pipeline phase."""
    phase: str
    start_time: float = 0.0
    end_time: float = 0.0
    duration_ms: int = 0
    tokens_used: int = 0
    success: bool = True
    error: str = ""


@dataclass
class SessionMetrics:
    """Complete metrics for a pipeline session."""
    session_id: str
    prompt: str = ""
    status: str = ""  # pass, fail, no_output
    created_at: str = ""

    # Phase timing
    phases: list[PhaseMetrics] = field(default_factory=list)
    total_duration_ms: int = 0

    # Token usage
    total_tokens: int = 0
    tokens_by_agent: dict[str, int] = field(default_factory=dict)

    # Quality
    quality_score: float = 0.0
    review_pass: bool = False
    retry_count: int = 0

    # Self-healing
    healing_attempted: bool = False
    healing_success: bool = False
    healing_attempts: int = 0
    validation_failures: int = 0

    # Files
    files_modified: int = 0
    domains: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to serializable dict."""
        data = asdict(self)
        # Convert PhaseMetrics to dicts
        data["phases"] = [asdict(p) for p in self.phases]
        return data

    def summary_line(self) -> str:
        """One-line summary for metrics log."""
        return (
            f"{self.session_id} | {self.status} | "
            f"quality={self.quality_score:.0%} | "
            f"retries={self.retry_count} | "
            f"heals={self.healing_attempts} | "
            f"tokens={self.total_tokens} | "
            f"files={self.files_modified} | "
            f"{self.total_duration_ms}ms"
        )


class MetricsTracker:
    """
    Tracks and persists pipeline metrics across sessions.

    Metrics are stored as JSONL (one JSON object per line) for
    efficient append-only logging and easy analysis.
    """

    def __init__(self, metrics_dir: Optional[Path] = None):
        """
        Initialize metrics tracker.

        Args:
            metrics_dir: Directory for metrics files (defaults to _vibecoding_brain/metrics/)
        """
        self.metrics_dir = metrics_dir or BRAIN_ROOT / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

        self._current: Optional[SessionMetrics] = None
        self._phase_start: Optional[float] = None
        self._session_start: Optional[float] = None

    @property
    def metrics_file(self) -> Path:
        """Path to the metrics JSONL file."""
        return self.metrics_dir / "sessions.jsonl"

    @property
    def summary_file(self) -> Path:
        """Path to the human-readable summary."""
        return self.metrics_dir / "summary.md"

    def start_session(self, session_id: str, prompt: str = ""):
        """Start tracking a new session."""
        self._current = SessionMetrics(
            session_id=session_id,
            prompt=prompt[:200],
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._session_start = time.time()

    def start_phase(self, phase: str):
        """Start timing a pipeline phase."""
        self._phase_start = time.time()
        if self._current:
            self._current.phases.append(PhaseMetrics(
                phase=phase,
                start_time=self._phase_start,
            ))

    def end_phase(self, phase: str, success: bool = True, tokens: int = 0, error: str = ""):
        """End timing a pipeline phase."""
        if not self._current:
            return

        end_time = time.time()

        # Find the phase in the list
        for p in reversed(self._current.phases):
            if p.phase == phase and p.end_time == 0:
                p.end_time = end_time
                p.duration_ms = int((end_time - p.start_time) * 1000)
                p.success = success
                p.tokens_used = tokens
                p.error = error
                break

    def record_tokens(self, agent_name: str, tokens: int):
        """Record token usage for an agent."""
        if not self._current:
            return

        self._current.total_tokens += tokens
        agent_key = agent_name.lower()
        self._current.tokens_by_agent[agent_key] = (
            self._current.tokens_by_agent.get(agent_key, 0) + tokens
        )

    def record_quality_score(self, score: float):
        """Record quality score."""
        if self._current:
            self._current.quality_score = score

    def record_healing(self, attempted: bool, success: bool, attempts: int, failures: int):
        """Record self-healing metrics."""
        if self._current:
            self._current.healing_attempted = attempted
            self._current.healing_success = success
            self._current.healing_attempts = attempts
            self._current.validation_failures = failures

    def record_review(self, passed: bool, retry_count: int):
        """Record review outcome."""
        if self._current:
            self._current.review_pass = passed
            self._current.retry_count = retry_count

    def record_files(self, file_count: int, domains: list[str]):
        """Record implementation output."""
        if self._current:
            self._current.files_modified = file_count
            self._current.domains = domains

    def end_session(self, status: str) -> Optional[SessionMetrics]:
        """
        End session tracking and persist metrics.

        Args:
            status: Final session status

        Returns:
            SessionMetrics for the completed session
        """
        if not self._current:
            return None

        self._current.status = status
        if self._session_start:
            self._current.total_duration_ms = int((time.time() - self._session_start) * 1000)

        # Persist
        self._append_metrics(self._current)
        self._update_summary()

        metrics = self._current
        self._current = None
        self._session_start = None
        return metrics

    def _append_metrics(self, metrics: SessionMetrics):
        """Append metrics to JSONL file."""
        try:
            with open(self.metrics_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(metrics.to_dict()) + "\n")
        except Exception:
            pass

    def _update_summary(self):
        """Update the human-readable summary file."""
        try:
            recent = self.get_recent_metrics(limit=50)
            if not recent:
                return

            total = len(recent)
            passes = sum(1 for m in recent if m.get("status") == "pass")
            avg_quality = sum(m.get("quality_score", 0) for m in recent) / total
            avg_retries = sum(m.get("retry_count", 0) for m in recent) / total
            total_tokens = sum(m.get("total_tokens", 0) for m in recent)
            heals = sum(1 for m in recent if m.get("healing_attempted"))
            heal_successes = sum(1 for m in recent if m.get("healing_success"))

            lines = [
                "# Pipeline Quality Metrics",
                f"> Last updated: {datetime.now(timezone.utc).isoformat()}",
                f"> Sessions analyzed: {total}",
                "",
                "## Overview",
                f"- **Pass rate:** {passes}/{total} ({passes/total:.0%})",
                f"- **Avg quality score:** {avg_quality:.0%}",
                f"- **Avg retries per session:** {avg_retries:.1f}",
                f"- **Total tokens used:** {total_tokens:,}",
                "",
                "## Self-Healing",
                f"- **Sessions with healing:** {heals}/{total}",
                f"- **Healing success rate:** {heal_successes}/{heals if heals else 1} ({heal_successes/(heals or 1):.0%})",
                "",
                "## Recent Sessions",
                "| Session | Status | Quality | Retries | Tokens |",
                "|---------|--------|---------|---------|--------|",
            ]

            for m in recent[-10:]:
                sid = m.get("session_id", "?")[:30]
                status = m.get("status", "?")
                quality = m.get("quality_score", 0)
                retries = m.get("retry_count", 0)
                tokens = m.get("total_tokens", 0)
                lines.append(f"| {sid} | {status} | {quality:.0%} | {retries} | {tokens:,} |")

            self.summary_file.write_text("\n".join(lines), encoding="utf-8")

        except Exception:
            pass

    def get_recent_metrics(self, limit: int = 50) -> list[dict]:
        """Load recent metrics from JSONL file."""
        if not self.metrics_file.exists():
            return []

        try:
            lines = self.metrics_file.read_text(encoding="utf-8").strip().split("\n")
            recent_lines = lines[-limit:] if len(lines) > limit else lines
            return [json.loads(line) for line in recent_lines if line.strip()]
        except Exception:
            return []

    def get_pass_rate(self, last_n: int = 20) -> float:
        """Get pass rate for last N sessions."""
        recent = self.get_recent_metrics(limit=last_n)
        if not recent:
            return 0.0
        passes = sum(1 for m in recent if m.get("status") == "pass")
        return passes / len(recent)

    def get_trend(self, metric_key: str, last_n: int = 10) -> list[float]:
        """Get trend values for a metric over last N sessions."""
        recent = self.get_recent_metrics(limit=last_n)
        return [m.get(metric_key, 0) for m in recent]
