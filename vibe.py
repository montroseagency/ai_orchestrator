"""
Vibe Coding Team — Main Python Orchestrator
============================================
Multi-agent code implementation pipeline for the Montrroase project.

Usage:
    python vibe.py "Add a dark mode toggle to the dashboard"
    python vibe.py "Add REST endpoint for bulk task deletion" --domain backend
    python vibe.py --review-only "sessions/my-session"
"""

import asyncio
import sys
import os
from pathlib import Path
from src.conductor import Conductor
from src.cli import VibeCliApp


def main():
    """Entry point for the Vibe Coding Team."""
    app = VibeCliApp()
    asyncio.run(app.run(sys.argv[1:]))


if __name__ == "__main__":
    main()
