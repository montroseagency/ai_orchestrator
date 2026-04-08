#!/usr/bin/env python3
"""
Periodic Claude API caller — executes every 5 hours
"""

import schedule
import time
from datetime import datetime
import anthropic


def call_claude():
    """Call Claude Haiku and print the response."""
    client = anthropic.Anthropic()

    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Calling Claude Haiku...")

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=256,
        messages=[
            {"role": "user", "content": "hello who are you"}
        ]
    )

    # Extract and print the response
    for block in response.content:
        if block.type == "text":
            print(f"Claude: {block.text}")

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Done.")


def main():
    """Schedule and run the periodic task."""
    print("Starting periodic Claude caller (every 5 hours)...")
    print(f"First run at: {datetime.now()}")

    # Schedule the task to run every 5 hours
    schedule.every(5).hours.do(call_claude)

    # Keep the scheduler running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute if a task is due


if __name__ == "__main__":
    main()
