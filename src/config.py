"""
Configuration for the Vibe Coding Team.
Reads from environment variables + .env file.

This system uses Claude Code CLI exclusively (subscription mode).
No API key required.
"""

import os
import shutil
from pathlib import Path

# Load .env from project root if it exists
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
BRAIN_ROOT = PROJECT_ROOT / "_vibecoding_brain"
AGENTS_DIR = BRAIN_ROOT / "agents"


class Config:
    """Central configuration."""

    # ═══════════════════════════════════════════════════════════════
    # Claude CLI (subscription account — no API key needed)
    # ═══════════════════════════════════════════════════════════════
    CLAUDE_CLI_PATH: str = os.environ.get("VIBE_CLAUDE_CLI_PATH", "claude")
    CLAUDE_CLI_EFFORT: str = os.environ.get("VIBE_CLAUDE_CLI_EFFORT", "high")
    CLAUDE_CLI_MODEL: str = os.environ.get("VIBE_CLAUDE_CLI_MODEL", "sonnet")

    # Playwright dev server URL — leave empty to disable Playwright skill injection
    PLAYWRIGHT_SERVER_URL: str = os.environ.get("VIBE_PLAYWRIGHT_SERVER_URL", "")

    # Execution limits (embedded in conductor prompt, also used by Python for display)
    MAX_REVIEW_RETRIES: int = int(os.environ.get("VIBE_MAX_RETRIES", "3"))
    MAX_ITERATIONS: int = int(os.environ.get("VIBE_MAX_ITERATIONS", "8"))

    # ═══════════════════════════════════════════════════════════════
    # RAG Integration (optional cross-session memory)
    # ═══════════════════════════════════════════════════════════════
    ENABLE_HISTORICAL_CONTEXT: bool = os.environ.get("VIBE_ENABLE_HISTORICAL_CONTEXT", "true").lower() == "true"
    MAX_SIMILAR_SESSIONS: int = int(os.environ.get("VIBE_MAX_SIMILAR_SESSIONS", "5"))
    MIN_RELEVANCE_THRESHOLD: float = float(os.environ.get("VIBE_MIN_RELEVANCE_THRESHOLD", "0.50"))

    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not shutil.which(cls.CLAUDE_CLI_PATH):
            raise ValueError(
                f"Claude CLI not found at '{cls.CLAUDE_CLI_PATH}'. "
                "Install it with: npm install -g @anthropic-ai/claude-code\n"
                "Then log in with: claude login"
            )
