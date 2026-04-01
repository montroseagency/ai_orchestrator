"""
CliTeamRunner — Runs the full agent team via a single Claude CLI session.

Uses CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 so the conductor spawns real
subagents (planner, creative_brain, implementer, reviewer) via the Agent tool.
Agents communicate through Claude's native mechanism — not Python text-passing.

How it works:
  1. Python builds --agents JSON from the system prompt files
  2. Python launches one `claude --print` session as the conductor
  3. The conductor uses its Read/Write tools + spawns subagents internally
  4. Conductor writes implementation files to disk itself
  5. Returns a structured JSON summary to Python
"""

import asyncio
import json
import os
import re
import subprocess
from pathlib import Path

from src.config import Config, AGENTS_DIR, PROJECT_ROOT, MONTRROASE_ROOT

# Conductor prompt for team mode (different from API mode conductor)
_CONDUCTOR_TEAM_PROMPT = AGENTS_DIR / "conductor_team.md"

# Subagent definitions — name → (description, system_prompt_path)
_SUBAGENTS: dict[str, tuple[str, Path]] = {
    "planner": (
        "Decomposes tasks into detailed plan.md files. Never writes code.",
        AGENTS_DIR / "planner.md",
    ),
    "creative_brain": (
        "Produces design_brief.md with precise UI/UX specs for frontend tasks.",
        AGENTS_DIR / "creative_brain.md",
    ),
    "implementer": (
        "Writes production-quality code. Returns a JSON object with all file operations.",
        AGENTS_DIR / "implementer.md",
    ),
    "ui_ux_tester": (
        "Frontend quality gate: design system compliance, TypeScript, accessibility, interaction quality. "
        "Returns PASS or FAIL with specific fix instructions.",
        AGENTS_DIR / "ui_ux_tester.md",
    ),
    "backend_tester": (
        "Backend quality gate: logic correctness, security, Django/DRF patterns, data integrity. "
        "Returns PASS or FAIL with specific fix instructions.",
        AGENTS_DIR / "backend_tester.md",
    ),
}

# CLI model name aliases
_MODEL_ALIASES = {
    "claude-haiku-4-5-20251001": "haiku",
    "claude-haiku-4-5": "haiku",
    "claude-sonnet-4-5": "sonnet",
    "claude-opus-4-5": "opus",
    "claude-opus-4-6": "opus",
}


class CliTeamRunner:
    """
    Runs the Vibe Coding Team as a real multi-agent session.

    The conductor is a full Claude Code session that:
    - Reads project files using its Read tool
    - Spawns specialist subagents using the Agent tool
    - Writes implementation files to disk using its Write tool
    - Loops the reviewer until PASS or max retries

    Agents actually communicate through Claude's native subagent mechanism.
    """

    def __init__(self, log_fn=None):
        self.log_fn = log_fn or (lambda phase, msg, **_: print(f"[{phase}] {msg}"))

    def _load_skill(self, skill_name: str) -> str:
        """Load a skill file from _vibecoding_brain/agents/skills/."""
        skill_path = AGENTS_DIR / "skills" / f"{skill_name}.md"
        return skill_path.read_text(encoding="utf-8") if skill_path.exists() else ""

    def _build_agents_json(self) -> str:
        """
        Build the --agents JSON string from system prompt files.
        For tester agents, skills are baked into their prompt since CLI subagents
        don't receive an extra_system parameter — skills must be part of the prompt.
        """
        agents: dict[str, dict] = {}
        for name, (description, prompt_path) in _SUBAGENTS.items():
            prompt = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else description

            # Inject skills into tester prompts for CLI team mode
            if name == "ui_ux_tester":
                accessibility = self._load_skill("web_accessibility")
                if accessibility:
                    prompt = f"{prompt}\n\n---\n\n{accessibility}"
                if Config.PLAYWRIGHT_SERVER_URL:
                    playwright = self._load_skill("playwright_testing").replace(
                        "{PLAYWRIGHT_SERVER_URL}", Config.PLAYWRIGHT_SERVER_URL
                    )
                    if playwright:
                        prompt = f"{prompt}\n\n---\n\n{playwright}"

            elif name == "backend_tester":
                code_review = self._load_skill("code_review")
                if code_review:
                    prompt = f"{prompt}\n\n---\n\n{code_review}"

            agents[name] = {"description": description, "prompt": prompt}
        return json.dumps(agents)

    def _model_alias(self, model_id: str) -> str:
        return _MODEL_ALIASES.get(model_id, model_id)

    def _handle_stream_event(self, event: dict) -> None:
        """Parse a stream-json event and log meaningful progress to the UI."""
        etype = event.get("type", "")

        if etype == "system" and event.get("subtype") == "init":
            sid = event.get("session_id", "")
            if sid:
                self.log_fn("🤝 Team", f"Session started: {sid[:16]}...")

        elif etype == "assistant":
            content = event.get("message", {}).get("content", [])
            for block in content:
                if block.get("type") == "text":
                    text = block.get("text", "").strip()
                    if not text:
                        continue
                    # Show first meaningful line (skip trivial one-word replies)
                    first_line = text.split("\n")[0].strip()
                    if len(first_line) > 8:
                        self.log_fn("🎯 Conductor", first_line[:120])

                elif block.get("type") == "tool_use":
                    name = block.get("name", "")
                    inp = block.get("input", {})
                    if name == "Agent":
                        desc = inp.get("description", inp.get("subagent_type", "subagent"))
                        self.log_fn("🤖 Agent", f"Spawning → {desc[:80]}")
                    elif name == "Write":
                        path = inp.get("file_path", "")
                        self.log_fn("💾 Write", path)
                    elif name == "Edit":
                        path = inp.get("file_path", "")
                        self.log_fn("✏️  Edit", path)
                    elif name == "Read":
                        path = inp.get("file_path", "")
                        self.log_fn("📖 Read", path)
                    elif name == "Bash":
                        cmd_str = inp.get("command", "")[:80]
                        self.log_fn("⚡ Bash", cmd_str)
                    elif name == "TodoWrite":
                        todos = inp.get("todos", [])
                        in_progress = [t["content"] for t in todos if t.get("status") == "in_progress"]
                        if in_progress:
                            self.log_fn("📋 Task", in_progress[0][:80])

        elif etype == "tool_result":
            # Tool results are noisy — only surface errors
            is_error = event.get("is_error", False)
            if is_error:
                content = event.get("content", "")
                if isinstance(content, list):
                    content = " ".join(b.get("text", "") for b in content if b.get("type") == "text")
                self.log_fn("⚠️  Tool Error", str(content)[:120])

        elif etype == "result":
            subtype = event.get("subtype", "")
            cost = event.get("total_cost_usd")
            cost_str = f" | cost: ${cost:.4f}" if cost else ""
            self.log_fn("🤝 Team", f"Session complete ({subtype}){cost_str}")

    async def run(self, prompt: str) -> dict:
        """
        Run the full team pipeline for a given prompt.

        Streams stream-json output from the Claude CLI so progress is visible
        in real time. Returns a result dict compatible with Conductor.run().
        """
        if not _CONDUCTOR_TEAM_PROMPT.exists():
            raise FileNotFoundError(
                f"Team conductor prompt not found: {_CONDUCTOR_TEAM_PROMPT}"
            )

        agents_json = self._build_agents_json()
        conductor_prompt = _CONDUCTOR_TEAM_PROMPT.read_text(encoding="utf-8")

        model = self._model_alias(Config.PLANNER_MODEL)

        cmd = [
            Config.CLAUDE_CLI_PATH,
            "--print",
            "--verbose",
            "--model", model,
            "--system-prompt", conductor_prompt,
            "--agents", agents_json,
            "--effort", Config.CLAUDE_CLI_EFFORT_HEAVY,
            "--output-format", "stream-json",
            "--no-session-persistence",
            "--dangerously-skip-permissions",
            "--add-dir", str(PROJECT_ROOT),
        ]

        env = {
            **os.environ,
            "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1",
        }

        self.log_fn("🤝 Team", f"Launching agent team | model: {model} | effort: {Config.CLAUDE_CLI_EFFORT_HEAVY}")

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=str(PROJECT_ROOT),
        )

        # Send prompt via stdin then close so the process knows input is done
        proc.stdin.write(prompt.encode())
        await proc.stdin.drain()
        proc.stdin.close()

        raw_result = ""
        all_lines: list[str] = []

        async def _stream():
            async for raw_line in proc.stdout:
                line = raw_line.decode(errors="replace").strip()
                if not line:
                    continue
                all_lines.append(line)
                try:
                    event = json.loads(line)
                    self._handle_stream_event(event)
                    if event.get("type") == "result":
                        nonlocal raw_result
                        raw_result = event.get("result", "")
                except json.JSONDecodeError:
                    if len(line) > 5 and not line.startswith("{"):
                        self.log_fn("🤝 Team", line[:120])

        # Stream with a 60-min timeout; clean up the subprocess on any exit
        try:
            await asyncio.wait_for(_stream(), timeout=3600)
        except asyncio.TimeoutError:
            proc.kill()
            raise RuntimeError("Team session timed out after 60 minutes")
        except asyncio.CancelledError:
            proc.kill()
            raise
        finally:
            try:
                await proc.wait()
            except Exception:
                pass

        if proc.returncode not in (0, None):
            stderr_bytes = await proc.stderr.read()
            stderr = stderr_bytes.decode(errors="replace").strip()
            raise RuntimeError(f"Team session failed (exit {proc.returncode}): {stderr}")

        return self._parse_result(raw_result or "\n".join(all_lines))

    def _parse_result(self, raw: str) -> dict:
        """
        Extract the structured result JSON from the conductor's final output.
        Falls back gracefully if the conductor didn't produce clean JSON.
        """
        # Try JSON code block first
        block_match = re.search(r"```json\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if block_match:
            try:
                data = json.loads(block_match.group(1))
                return self._normalize(data, raw)
            except json.JSONDecodeError:
                pass

        # Try to find outermost JSON object
        start = raw.find("{")
        if start != -1:
            depth = 0
            for i, ch in enumerate(raw[start:], start):
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            data = json.loads(raw[start : i + 1])
                            return self._normalize(data, raw)
                        except json.JSONDecodeError:
                            break

        # No structured output — return graceful fallback
        return {
            "session_id": "unknown",
            "status": "unknown",
            "files_applied": [],
            "walkthrough_path": None,
            "session_dir": None,
            "notes": [f"Conductor output could not be parsed as JSON. Raw output: {raw[:500]}"],
            "quality_score": None,
        }

    def _normalize(self, data: dict, raw: str) -> dict:
        """Normalize conductor output to match Conductor.run() return format."""
        session_id = data.get("session_id", "unknown")
        status = data.get("status", "unknown")
        files_written = data.get("files_written", [])

        # Build files_applied in the same format as FileApplicator
        files_applied = [
            {"path": p, "status": "ok", "operation": "write"}
            for p in files_written
        ]

        return {
            "session_id": session_id,
            "status": status,
            "files_applied": files_applied,
            "walkthrough_path": None,
            "session_dir": str(PROJECT_ROOT / "_vibecoding_brain" / "sessions" / session_id),
            "notes": [data.get("summary", "")],
            "quality_score": None,
            # Extra team-mode fields
            "iterations": data.get("iterations", 0),
            "review_verdict": data.get("review_verdict", ""),
        }
