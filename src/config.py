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

    # ═══════════════════════════════════════════════════════════════
    # Claude CLI Mode (subscription account — no API key needed)
    # ═══════════════════════════════════════════════════════════════
    # Set VIBE_USE_CLAUDE_CLI=true in .env to use your Claude Pro/Max
    # subscription instead of paying per-token API credits.
    USE_CLAUDE_CLI: bool = os.environ.get("VIBE_USE_CLAUDE_CLI", "false").lower() == "true"
    MULTI_TERMINAL: bool = os.environ.get("VIBE_MULTI_TERMINAL", "false").lower() == "true"
    CLAUDE_CLI_PATH: str = os.environ.get("VIBE_CLAUDE_CLI_PATH", "claude")
    # Effort level for CLI agents that would otherwise use extended thinking.
    # Maps to Claude's --effort flag: low | medium | high | max
    CLAUDE_CLI_EFFORT_HEAVY: str = os.environ.get("VIBE_CLAUDE_CLI_EFFORT_HEAVY", "high")   # planner, reviewer
    CLAUDE_CLI_EFFORT_NORMAL: str = os.environ.get("VIBE_CLAUDE_CLI_EFFORT_NORMAL", "medium") # implementer, creative
    CLAUDE_CLI_EFFORT_FAST: str = os.environ.get("VIBE_CLAUDE_CLI_EFFORT_FAST", "low")       # conductor

    # Models (route by capability tier)
    CONDUCTOR_MODEL: str = os.environ.get("VIBE_CONDUCTOR_MODEL", "claude-haiku-4-5-20251001")
    PLANNER_MODEL: str = os.environ.get("VIBE_PLANNER_MODEL", "claude-sonnet-4-6")
    CREATIVE_MODEL: str = os.environ.get("VIBE_CREATIVE_MODEL", "claude-sonnet-4-6")
    IMPLEMENTER_MODEL: str = os.environ.get("VIBE_IMPLEMENTER_MODEL", "claude-sonnet-4-6")
    UIUX_TESTER_MODEL: str = os.environ.get("VIBE_UIUX_TESTER_MODEL", "claude-sonnet-4-6")
    BACKEND_TESTER_MODEL: str = os.environ.get("VIBE_BACKEND_TESTER_MODEL", "claude-sonnet-4-6")
    # Playwright dev server URL — leave empty to disable Playwright skill injection
    PLAYWRIGHT_SERVER_URL: str = os.environ.get("VIBE_PLAYWRIGHT_SERVER_URL", "")

    # Default / fallback
    DEFAULT_MODEL: str = "claude-sonnet-4-6"

    # Extended Thinking (token budgets — 0 = disabled)
    # Planner benefits most: complex decomposition = 54% quality improvement
    PLANNER_THINKING_TOKENS: int = int(os.environ.get("VIBE_PLANNER_THINKING_TOKENS", "8000"))
    # Reviewer benefits: catches edge cases, deeper analysis
    REVIEWER_THINKING_TOKENS: int = int(os.environ.get("VIBE_REVIEWER_THINKING_TOKENS", "5000"))

    # Execution limits
    MAX_REVIEW_RETRIES: int = int(os.environ.get("VIBE_MAX_RETRIES", "3"))
    MAX_ITERATIONS: int = int(os.environ.get("VIBE_MAX_ITERATIONS", "8"))

    # Confidence threshold — below this, Conductor asks user for clarification
    UNCERTAINTY_THRESHOLD: float = float(os.environ.get("VIBE_UNCERTAINTY_THRESHOLD", "0.65"))

    # ═══════════════════════════════════════════════════════════════
    # RAG Integration
    # ═══════════════════════════════════════════════════════════════
    ENABLE_HISTORICAL_CONTEXT: bool = os.environ.get("VIBE_ENABLE_HISTORICAL_CONTEXT", "true").lower() == "true"
    MAX_SIMILAR_SESSIONS: int = int(os.environ.get("VIBE_MAX_SIMILAR_SESSIONS", "5"))
    MIN_RELEVANCE_THRESHOLD: float = float(os.environ.get("VIBE_MIN_RELEVANCE_THRESHOLD", "0.50"))
    SIMILARITY_DEDUPE_THRESHOLD: float = float(os.environ.get("VIBE_SIMILARITY_DEDUPE_THRESHOLD", "0.80"))

    # ═══════════════════════════════════════════════════════════════
    # Token Optimization
    # ═══════════════════════════════════════════════════════════════
    ENABLE_PREINDEX_SUMMARIES: bool = os.environ.get("VIBE_ENABLE_PREINDEX_SUMMARIES", "true").lower() == "true"
    PREINDEX_SUMMARY_TOKENS: int = int(os.environ.get("VIBE_PREINDEX_SUMMARY_TOKENS", "150"))
    ENABLE_QUERY_CACHE: bool = os.environ.get("VIBE_ENABLE_QUERY_CACHE", "true").lower() == "true"
    QUERY_CACHE_TTL: int = int(os.environ.get("VIBE_QUERY_CACHE_TTL", "300"))

    # Token budgets per agent (historical context only)
    TOKEN_BUDGETS: dict = {
        "conductor": 100,
        "planner": 300,
        "creative_brain": 400,
        "implementer": 150,
        "ui_ux_tester": 150,
        "backend_tester": 100,
    }

    # ═══════════════════════════════════════════════════════════════
    # Learning
    # ═══════════════════════════════════════════════════════════════
    LESSON_EXTRACTION_ENABLED: bool = os.environ.get("VIBE_LESSON_EXTRACTION_ENABLED", "true").lower() == "true"
    PATCH_GENERATION_THRESHOLD: int = int(os.environ.get("VIBE_PATCH_GENERATION_THRESHOLD", "3"))

    # ═══════════════════════════════════════════════════════════════
    # Coordination
    # ═══════════════════════════════════════════════════════════════
    MAX_NEGOTIATION_ROUNDS: int = int(os.environ.get("VIBE_MAX_NEGOTIATION_ROUNDS", "3"))
    COORDINATION_TIMEOUT: float = float(os.environ.get("VIBE_COORDINATION_TIMEOUT", "30.0"))

    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if cls.USE_CLAUDE_CLI:
            # CLI mode uses your subscription — no API key needed.
            import shutil
            if not shutil.which(cls.CLAUDE_CLI_PATH):
                raise ValueError(
                    f"Claude CLI not found at '{cls.CLAUDE_CLI_PATH}'. "
                    "Install it with: npm install -g @anthropic-ai/claude-code\n"
                    "Then log in with: claude login"
                )
        elif not cls.ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY is not set.\n"
                "Option 1 — API credits: add ANTHROPIC_API_KEY=sk-ant-... to your .env\n"
                "Option 2 — Subscription: add VIBE_USE_CLAUDE_CLI=true to your .env"
            )
