"""
Vibe CLI — Beautiful Rich terminal interface for the Vibe Coding Team.
Manages argument parsing, progress display, and user interaction.
"""

import sys
import asyncio
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text
from rich import print as rprint
from rich.rule import Rule
from rich.markup import escape
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.live import Live
from rich.columns import Columns
from rich.padding import Padding

from src.conductor import Conductor
from src.config import Config, SESSIONS_DIR

console = Console()

# ─────────────────────────────────────────────────────────────────
# Brand / Theme
# ─────────────────────────────────────────────────────────────────

BRAND_GRADIENT = "bold bright_white on #1a1a2e"
AGENT_COLORS = {
    "🎯 Conductor":   "#6366f1",   # indigo
    "📋 Planner":     "#06b6d4",   # cyan
    "🎨 Creative":    "#f59e0b",   # amber
    "🎨 Creative Brain": "#f59e0b",
    "⚙️  Implementer": "#10b981",  # emerald
    "🔍 Reviewer":    "#f43f5e",   # rose
    "💾 Writing Files": "#8b5cf6", # violet
    "📝 Walkthrough": "#64748b",   # slate
    "⚠️  Warning":    "#f97316",   # orange
    "❌ Implementer": "#ef4444",   # red
}
DEFAULT_AGENT_COLOR = "#94a3b8"


def get_agent_color(phase: str) -> str:
    for key, color in AGENT_COLORS.items():
        if key in phase or phase in key:
            return color
    return DEFAULT_AGENT_COLOR


# ─────────────────────────────────────────────────────────────────
# CLI App
# ─────────────────────────────────────────────────────────────────

class VibeCliApp:
    """Main CLI application for the Vibe Coding Team."""

    def __init__(self):
        self._log_lines: list[tuple[str, str, str]] = []
        self._current_phase: str = ""

    def log(self, phase: str, message: str, style: str = "info"):
        """Record a log line and print it to the console."""
        color = get_agent_color(phase)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._log_lines.append((phase, message, style))
        phase_text = Text(f" {phase} ", style=f"bold {color}")
        msg_text = Text(f" {message}", style="bright_white")
        ts_text = Text(f" {timestamp} ", style="dim")
        console.print(ts_text, phase_text, msg_text)

    # ─────────────────────────────────────────
    # Run entry
    # ─────────────────────────────────────────

    async def run(self, args: list[str]):
        """Parse args and run the pipeline."""
        parsed = self._parse_args(args)

        if parsed.get("help"):
            self._print_help()
            return

        if not parsed.get("prompt"):
            console.print("[red]Error:[/red] No prompt provided. Use --help for usage.")
            sys.exit(1)

        self._print_banner()

        try:
            Config.validate()
        except ValueError as e:
            console.print(f"\n[bold red]Configuration Error[/bold red]\n{e}\n")
            sys.exit(1)

        prompt = parsed["prompt"]
        dry_run = parsed.get("dry_run", False)

        # Show the task
        console.print()
        console.print(Panel(
            f"[bold bright_white]{escape(prompt)}[/bold bright_white]",
            title="[bold #6366f1]🚀 Task[/bold #6366f1]",
            border_style="#6366f1",
            padding=(1, 2),
        ))

        if dry_run:
            console.print("[bold #f97316]DRY RUN MODE — no files will be written[/bold #f97316]\n")

        console.print(Rule(style="dim"))
        console.print()

        # Run the pipeline — multi-terminal, CLI team, or API mode
        try:
            if Config.MULTI_TERMINAL:
                from src.multi_terminal_runner import MultiTerminalRunner
                runner = MultiTerminalRunner(log_fn=self.log)
                result = await runner.run(prompt)
            elif Config.USE_CLAUDE_CLI:
                from src.team_runner import CliTeamRunner
                runner = CliTeamRunner(log_fn=self.log)
                result = await runner.run(prompt)
            else:
                conductor = Conductor(ui=self, dry_run=dry_run)
                result = await conductor.run(
                    prompt=prompt,
                    ask_user_fn=self._ask_user,
                )
            self._print_result(result)
        except KeyboardInterrupt:
            console.print("\n\n[bold red]Interrupted.[/bold red] Session state saved.")
            sys.exit(130)
        except Exception as e:
            console.print(f"\n[bold red]Pipeline Error:[/bold red] {escape(str(e))}")
            import traceback
            console.print_exception()
            sys.exit(1)

    # ─────────────────────────────────────────
    # User interaction
    # ─────────────────────────────────────────

    async def _ask_user(self, question: str) -> str:
        """Ask the user a clarification question and return their answer."""
        console.print()
        console.print(Panel(
            f"[bold #f59e0b]🤔 Clarification Needed[/bold #f59e0b]\n\n"
            f"[bright_white]{escape(question)}[/bright_white]",
            border_style="#f59e0b",
            padding=(1, 2),
        ))
        answer = Prompt.ask("[bold #f59e0b]Your answer[/bold #f59e0b]")
        console.print()
        return answer

    # ─────────────────────────────────────────
    # Result display
    # ─────────────────────────────────────────

    def _print_result(self, result: dict):
        """Print a rich summary of the pipeline result."""
        console.print()
        console.print(Rule(style="dim"))
        console.print()

        status = result.get("status", "unknown")
        session_id = result.get("session_id", "unknown")
        files_applied = result.get("files_applied", [])
        walkthrough_path = result.get("walkthrough_path")
        notes = result.get("notes", [])
        session_dir = result.get("session_dir", "")

        # Status badge
        if status == "pass":
            status_text = "[bold #10b981]✅ PASS[/bold #10b981]"
        elif status == "fail_max_retries":
            status_text = "[bold #f97316]⚠️  FAIL (max retries)[/bold #f97316]"
        elif status == "no_output":
            status_text = "[bold #ef4444]❌ No output produced[/bold #ef4444]"
        else:
            status_text = f"[dim]{escape(status)}[/dim]"

        # Files table
        files_table = Table(
            show_header=True,
            header_style="bold #6366f1",
            border_style="dim",
            expand=True,
        )
        files_table.add_column("Operation", style="bold", width=10)
        files_table.add_column("File", style="bright_white")
        files_table.add_column("Status", width=10)

        for f in files_applied:
            op = f.get("operation", "?")
            path = f.get("path", "?")
            f_status = f.get("status", "?")
            op_color = {"CREATE": "#10b981", "MODIFY": "#06b6d4", "DELETE": "#f43f5e"}.get(op, "white")
            status_color = "#10b981" if f_status == "ok" else "#ef4444"
            files_table.add_row(
                f"[{op_color}]{op}[/{op_color}]",
                escape(path),
                f"[{status_color}]{f_status}[/{status_color}]",
            )

        # Summary panel content
        summary_lines = [
            f"[dim]Status:[/dim]     {status_text}",
            f"[dim]Session:[/dim]    [bold]{escape(session_id)}[/bold]",
            f"[dim]Session dir:[/dim] [dim]{escape(session_dir)}[/dim]",
        ]
        if walkthrough_path:
            summary_lines.append(
                f"[dim]Walkthrough:[/dim] [link={walkthrough_path}]{escape(walkthrough_path)}[/link]"
            )

        console.print(Panel(
            "\n".join(summary_lines),
            title="[bold bright_white]🏁 Pipeline Complete[/bold bright_white]",
            border_style="#10b981" if status == "pass" else "#f97316",
            padding=(1, 2),
        ))

        if files_applied:
            console.print()
            console.print(files_table)

        if notes:
            console.print()
            console.print("[bold #64748b]📌 Notes from Implementer:[/bold #64748b]")
            for note in notes:
                console.print(f"  [dim]•[/dim] {escape(note)}")

        # Walkthrough preview
        if walkthrough_path and Path(walkthrough_path).exists():
            console.print()
            walkthrough = Path(walkthrough_path).read_text(encoding="utf-8")
            console.print(Panel(
                escape(walkthrough[:1200]) + ("..." if len(walkthrough) > 1200 else ""),
                title="[bold #64748b]📝 Walkthrough[/bold #64748b]",
                border_style="dim",
                padding=(1, 2),
            ))

    # ─────────────────────────────────────────
    # Banner & Help
    # ─────────────────────────────────────────

    def _print_banner(self):
        """Print the Vibe Coding Team banner."""
        console.print()
        console.print(Panel(
            "[bold bright_white]  🤖  Vibe Coding Team  [/bold bright_white]\n"
            "[dim]  Planner · Creative Brain · Implementer · Reviewer  [/dim]",
            style="#1a1a2e",
            border_style="#6366f1",
            padding=(0, 4),
        ))
        console.print()

    def _print_help(self):
        """Print usage help."""
        self._print_banner()
        console.print(Panel(
            "[bold]Usage:[/bold]\n"
            "  [cyan]python vibe.py[/cyan] [bold]\"<your task>\"[/bold] [dim][options][/dim]\n\n"
            "[bold]Examples:[/bold]\n"
            "  [cyan]python vibe.py[/cyan] \"Add a dark mode toggle to the sidebar\"\n"
            "  [cyan]python vibe.py[/cyan] \"Add bulk delete endpoint for tasks\" --domain backend\n"
            "  [cyan]python vibe.py[/cyan] \"Refactor the client detail hub\" --dry-run\n\n"
            "[bold]Options:[/bold]\n"
            "  [dim]--dry-run[/dim]         Show what would be done, don't write files\n"
            "  [dim]--help[/dim]            Show this help message\n\n"
            "[bold]Configuration:[/bold]\n"
            "  Create [bold].env[/bold] in the agentic_workflow directory:\n"
            "  [dim]ANTHROPIC_API_KEY=sk-ant-...[/dim]\n"
            "  [dim]VIBE_IMPLEMENTER_MODEL=claude-opus-4-5  (optional)[/dim]\n\n"
            "[bold]Session Artifacts:[/bold]\n"
            f"  Saved to [dim]{SESSIONS_DIR}/<session-id>/[/dim]\n"
            "  [dim]plan.md  design_brief.md  implementation_log.md  review.md  walkthrough.md[/dim]",
            title="[bold #6366f1]📖 Help[/bold #6366f1]",
            border_style="#6366f1",
            padding=(1, 2),
        ))

    # ─────────────────────────────────────────
    # Argument parsing (no external deps)
    # ─────────────────────────────────────────

    def _parse_args(self, args: list[str]) -> dict:
        """Simple argument parser without argparse dependency."""
        result = {
            "prompt": None,
            "dry_run": False,
            "help": False,
        }

        i = 0
        while i < len(args):
            arg = args[i]
            if arg in ("--help", "-h"):
                result["help"] = True
            elif arg in ("--dry-run", "--dry_run"):
                result["dry_run"] = True
            elif not arg.startswith("--"):
                # Positional — the prompt
                if result["prompt"] is None:
                    result["prompt"] = arg
            i += 1

        return result
