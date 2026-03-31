"""
Session Manager — Creates and manages session state for each vibe task.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from src.config import SESSIONS_DIR


class Session:
    """Manages the state and artifacts for a single vibe coding session."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.session_dir = SESSIONS_DIR / session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.session_dir / "state.json"
        self._state: dict = self._load_state()

    def _load_state(self) -> dict:
        """Load existing state or create fresh."""
        if self.state_file.exists():
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        return {
            "session_id": self.session_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "started",
            "phases_completed": [],
            "iterations": 0,
        }

    def save_state(self):
        """Persist state to disk."""
        self._state["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.state_file.write_text(
            json.dumps(self._state, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def write_artifact(self, name: str, content: str) -> Path:
        """Write a session artifact (plan.md, design_brief.md, etc.)."""
        path = self.session_dir / name
        path.write_text(content, encoding="utf-8")
        return path

    def read_artifact(self, name: str) -> str | None:
        """Read a session artifact if it exists."""
        path = self.session_dir / name
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None

    def mark_phase_complete(self, phase: str):
        """Mark a pipeline phase as completed."""
        if phase not in self._state["phases_completed"]:
            self._state["phases_completed"].append(phase)
        self._state["status"] = f"completed_{phase}"
        self.save_state()

    def increment_iteration(self) -> int:
        """Increment and return the iteration counter."""
        self._state["iterations"] += 1
        self.save_state()
        return self._state["iterations"]

    @property
    def iterations(self) -> int:
        return self._state.get("iterations", 0)

    @property
    def phases_completed(self) -> list[str]:
        return self._state.get("phases_completed", [])

    def set(self, key: str, value):
        """Store arbitrary state."""
        self._state[key] = value
        self.save_state()

    def get(self, key: str, default=None):
        """Retrieve arbitrary state."""
        return self._state.get(key, default)


def make_session_id(prompt: str) -> str:
    """
    Create a URL-safe session ID from a prompt.
    e.g. "Add dark mode toggle" → "add-dark-mode-toggle-20260331"
    """
    # Extract first 5 words
    words = re.sub(r"[^\w\s]", "", prompt.lower()).split()[:5]
    slug = "-".join(words)
    date = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    return f"{slug}-{date}"
