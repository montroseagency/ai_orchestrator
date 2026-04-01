"""
Vibe Coding Team — Main Entry Point
====================================
Multi-agent code implementation pipeline for the Montrroase project.
Uses Claude Code native agent teams (subscription mode — no API key needed).

Usage:
    python vibe.py "Add a dark mode toggle to the dashboard"
    python vibe.py "Add REST endpoint for bulk task deletion"
    python vibe.py "Refactor the client detail hub" --ide-state='{"active_file": "server.py"}'
"""

import asyncio
import argparse
import sys
import json
from src.team_runner import CliTeamRunner

def basic_logger(phase: str, msg: str, **kwargs):
    print(json.dumps({"phase": phase, "msg": msg}))

async def run_pipeline(prompt: str, ide_state: str = None, dry_run: bool = False):
    if dry_run:
        print(json.dumps({"phase": "System", "msg": "Dry run enabled. Exiting."}))
        return

    runner = CliTeamRunner(log_fn=basic_logger)
    try:
        result = await runner.run(prompt, ide_state=ide_state)
        print("\n=== PIPELINE RESULT ===")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"phase": "Error", "msg": str(e)}))
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Vibe Coding Team Pipeline")
    parser.add_argument("prompt", type=str, help="The task description")
    parser.add_argument("--ide-state", type=str, default=None, help="JSON string representing IDE context")
    parser.add_argument("--dry-run", action="store_true", help="Dry run without writing files")
    args = parser.parse_args()

    asyncio.run(run_pipeline(args.prompt, args.ide_state, args.dry_run))

if __name__ == "__main__":
    main()
