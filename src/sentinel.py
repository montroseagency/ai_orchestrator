#!/usr/bin/env python3
"""
The Sentinel — Passive Background Agent for Montrroase
Monitors file saves in real-time and instantly flags architectural/design rule violations.
"""
import sys
import time
import re
from pathlib import Path

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("Error: watchdog not installed. Run `pip install watchdog`.", file=sys.stderr)
    sys.exit(1)

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
MONTRROASE_DIR = PROJECT_ROOT / "Montrroase_website"

# The 12 AI-Slop Patterns mapped to regexes (simplified for real-time scanning)
RULES = [
    {
        "pattern": r"(bg-gradient-to|from-purple|to-blue)",
        "msg": "Purple-to-blue gradients detected. Ban AI-slop gradients.",
    },
    {
        "pattern": r"rounded-2xl",
        "msg": "Uniform rounded-2xl detected. Use graduated border-radius.",
    },
    {
        "pattern": r"import\s+.*from\s+['\"]lucide-react['\"]",
        "msg": "Lucide icons detected. Use Phosphor icons.",
    },
    {
        "pattern": r"font-bold|font-\[700\]",
        "msg": "Font weight 700+ detected. Max 600 in product UI unless it's a page heading.",
    },
    {
        "pattern": r"bg-white.*<body|bg-white.*<html",
        "msg": "Pure white background on canvas detected. Use gray-50 (#FAFAF8).",
        "flags": re.IGNORECASE,
    },
    {
        "pattern": r"(bg-zinc|text-indigo-\d{3}|bg-gray-\d{3})\b",
        "msg": "Raw tailwind color class detected. Verify it aligns with custom Montrroase tokens.",
    }
]

class SentinelHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return
        
        filepath = Path(event.src_path)
        if filepath.suffix not in [".tsx", ".ts", ".jsx", ".js", ".py", ".css"]:
            return

        # Simple debounce / read safety
        time.sleep(0.1)
        try:
            content = filepath.read_text(encoding="utf-8")
        except Exception:
            return

        lines = content.split('\n')
        for i, line in enumerate(lines):
            # Check emojis heuristically (basic wide range check)
            if re.search(r"[\U00010000-\U0010ffff]", line) and '<' in line and '>' in line:
                self._alert(filepath, i+1, "Emoji might be used as UI element. Ensure it's not structural.")

            for rule in RULES:
                flags = rule.get("flags", 0)
                if re.search(rule["pattern"], line, flags):
                    self._alert(filepath, i+1, rule["msg"])

    def _alert(self, filepath: Path, line: int, msg: str):
        # Format explicitly for IDE Error Matchers
        try:
            rel = filepath.relative_to(PROJECT_ROOT)
        except ValueError:
            rel = filepath
        print(f"{rel}:{line}: warning: [Sentinel] {msg}")

def start_sentinel():
    if not MONTRROASE_DIR.exists():
        print(f"Error: {MONTRROASE_DIR} does not exist. (Is project root correct?)")
        # Proceed anyway on parent dir for testing
        watch_dir = PROJECT_ROOT
    else:
        watch_dir = MONTRROASE_DIR
        
    print(f"🛡️  The Sentinel is active. Watching {watch_dir.name} for architectural violations...")
    event_handler = SentinelHandler()
    observer = Observer()
    observer.schedule(event_handler, str(watch_dir), recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    start_sentinel()
