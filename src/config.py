"""
Configuration for the Vibe Coding Team.
Reads from environment variables + .env file.
"""

import os
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
MONTRROASE_ROOT = PROJECT_ROOT / "Montrroase_website"
SESSIONS_DIR = BRAIN_ROOT / "sessions"
AGENTS_DIR = BRAIN_ROOT / "agents"
CONTEXT_DIR = BRAIN_ROOT / "context"


class Config:
    """Central configuration."""

    # API Keys
    ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")

    # Models (route by capability tier)
    CONDUCTOR_MODEL: str = os.environ.get("VIBE_CONDUCTOR_MODEL", "claude-haiku-4-5")
    PLANNER_MODEL: str = os.environ.get("VIBE_PLANNER_MODEL", "claude-sonnet-4-5")
    CREATIVE_MODEL: str = os.environ.get("VIBE_CREATIVE_MODEL", "claude-sonnet-4-5")
    IMPLEMENTER_MODEL: str = os.environ.get("VIBE_IMPLEMENTER_MODEL", "claude-sonnet-4-5")
    REVIEWER_MODEL: str = os.environ.get("VIBE_REVIEWER_MODEL", "claude-sonnet-4-5")

    # Default / fallback
    DEFAULT_MODEL: str = "claude-sonnet-4-5"

    # Execution limits
    MAX_REVIEW_RETRIES: int = int(os.environ.get("VIBE_MAX_RETRIES", "3"))
    MAX_ITERATIONS: int = int(os.environ.get("VIBE_MAX_ITERATIONS", "8"))

    # Confidence threshold — below this, Conductor asks user for clarification
    UNCERTAINTY_THRESHOLD: float = float(os.environ.get("VIBE_UNCERTAINTY_THRESHOLD", "0.65"))

    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY is not set. "
                "Add it to .env file in the agentic_workflow directory:\n"
                "  ANTHROPIC_API_KEY=sk-ant-..."
            )
