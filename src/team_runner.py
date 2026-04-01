"""
CliTeamRunner — Runs the full agent team via a single Claude CLI session.

Uses CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 so the conductor spawns real
subagents (planner, creative_brain, implementer, ui_ux_tester, backend_tester)
via the Agent tool. Agents communicate through Claude's native mechanism.

How it works:
  1. Python builds --agents JSON from the system prompt files
  2. Python launches one `claude --print` session as the conductor
  3. The conductor uses its Read/Write/Edit/Bash tools + spawns subagents internally
  4. Subagents write implementation files to disk directly
  5. Returns a structured JSON summary to Python
"""

import asyncio
import json
import os
import re
from pathlib import Path

from src.config import Config, AGENTS_DIR, PROJECT_ROOT

# Sentinel script for real-time AI-slop detection
_SENTINEL_SCRIPT = PROJECT_ROOT / "src" / "sentinel.py"

# Conductor prompt for team mode
_CONDUCTOR_TEAM_PROMPT = AGENTS_DIR / "conductor_team.md"

# Subagent definitions — name -> (description, system_prompt_path)
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
        "Writes production-quality code directly to disk using Write/Edit tools. "
        "Returns a summary of what was written.",
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


class CliTeamRunner:
    """
    Runs the Vibe Coding Team as a real multi-agent session.

    The conductor is a full Claude Code session that:
    - Reads project files using its Read tool
    - Spawns specialist subagents using the Agent tool
    - Implementer writes files to disk directly using Write/Edit tools
    - Loops the tester until PASS or max retries

    Agents communicate through Claude's native subagent mechanism.
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

            # Inject skills into tester prompts
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

    def _handle_stream_event(self, event: dict) -> None:
        """Parse a stream-json event and log meaningful progress to the UI."""
        etype = event.get("type", "")

        if etype == "system" and event.get("subtype") == "init":
            sid = event.get("session_id", "")
            if sid:
                self.log_fn("Team", f"Session started: {sid[:16]}...")

        elif etype == "assistant":
            content = event.get("message", {}).get("content", [])
            for block in content:
                if block.get("type") == "text":
                    text = block.get("text", "").strip()
                    if not text:
                        continue
                    first_line = text.split("\n")[0].strip()
                    if len(first_line) > 8:
                        self.log_fn("Conductor", first_line[:120])

                elif block.get("type") == "tool_use":
                    name = block.get("name", "")
                    inp = block.get("input", {})
                    if name == "Agent":
                        desc = inp.get("description", inp.get("subagent_type", "subagent"))
                        self.log_fn("Agent", f"Spawning -> {desc[:80]}")
                    elif name == "Write":
                        path = inp.get("file_path", "")
                        self.log_fn("Write", path)
                    elif name == "Edit":
                        path = inp.get("file_path", "")
                        self.log_fn("Edit", path)
                    elif name == "Read":
                        path = inp.get("file_path", "")
                        self.log_fn("Read", path)
                    elif name == "Bash":
                        cmd_str = inp.get("command", "")[:80]
                        self.log_fn("Bash", cmd_str)

        elif etype == "tool_result":
            is_error = event.get("is_error", False)
            if is_error:
                content = event.get("content", "")
                if isinstance(content, list):
                    content = " ".join(b.get("text", "") for b in content if b.get("type") == "text")
                self.log_fn("Tool Error", str(content)[:120])

        elif etype == "result":
            subtype = event.get("subtype", "")
            cost = event.get("total_cost_usd")
            cost_str = f" | cost: ${cost:.4f}" if cost else ""
            self.log_fn("Team", f"Session complete ({subtype}){cost_str}")

    async def run(self, prompt: str, ide_state: str = None) -> dict:
        """
        Run the full team pipeline for a given prompt.

        Streams stream-json output from the Claude CLI so progress is visible
        in real time. Returns a result dict.
        """
        if not _CONDUCTOR_TEAM_PROMPT.exists():
            raise FileNotFoundError(
                f"Team conductor prompt not found: {_CONDUCTOR_TEAM_PROMPT}"
            )

        # Optional RAG pre-hook: enrich prompt with historical context
        enriched_prompt = await self._rag_pre_hook(prompt)
        
        # Inject IDE State contextual payload if provided by Antigravity
        if ide_state:
            enriched_prompt = f"## IDE Environment Context (Antigravity)\nThis is the current state of the user's IDE:\n{ide_state}\n\n---\n\n{enriched_prompt}"


        agents_json = self._build_agents_json()
        conductor_prompt = _CONDUCTOR_TEAM_PROMPT.read_text(encoding="utf-8")

        cmd = [
            Config.CLAUDE_CLI_PATH,
            "--print",
            "--verbose",
            "--model", Config.CLAUDE_CLI_MODEL,
            "--system-prompt", conductor_prompt,
            "--agents", agents_json,
            "--effort", Config.CLAUDE_CLI_EFFORT,
            "--output-format", "stream-json",
            "--no-session-persistence",
            "--dangerously-skip-permissions",
            "--add-dir", str(PROJECT_ROOT),
        ]

        env = {
            **os.environ,
            "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1",
        }

        # Start the Sentinel — passive background watcher that catches AI-slop in real time
        sentinel_proc = await self._start_sentinel()

        self.log_fn("Team", f"Launching agent team | model: {Config.CLAUDE_CLI_MODEL} | effort: {Config.CLAUDE_CLI_EFFORT}")

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=str(PROJECT_ROOT),
        )

        # Send prompt via stdin then close so the process knows input is done
        proc.stdin.write(enriched_prompt.encode())
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
                        self.log_fn("Team", line[:120])

        # Stream with a 60-min timeout
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

        # Stop the Sentinel and collect any warnings it caught
        sentinel_warnings = await self._stop_sentinel(sentinel_proc)

        result = self._parse_result(raw_result or "\n".join(all_lines))

        if sentinel_warnings:
            result["sentinel_warnings"] = sentinel_warnings
            self.log_fn("Sentinel", f"{len(sentinel_warnings)} warning(s) detected during execution")

        # Optional RAG post-hook: index the session
        await self._rag_post_hook(result, prompt)

        return result

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
                return self._normalize(data)
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
                            return self._normalize(data)
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

    def _normalize(self, data: dict) -> dict:
        """Normalize conductor output to a consistent result format."""
        session_id = data.get("session_id", "unknown")
        status = data.get("status", "unknown")
        files_written = data.get("files_written", [])

        files_applied = [
            {"path": p, "status": "ok", "operation": "write"}
            for p in files_written
        ]

        session_dir = str(PROJECT_ROOT / "_vibecoding_brain" / "sessions" / session_id)
        walkthrough_path = str(PROJECT_ROOT / "_vibecoding_brain" / "sessions" / session_id / "walkthrough.md")

        return {
            "session_id": session_id,
            "status": status,
            "files_applied": files_applied,
            "walkthrough_path": walkthrough_path if (PROJECT_ROOT / "_vibecoding_brain" / "sessions" / session_id / "walkthrough.md").exists() else None,
            "session_dir": session_dir,
            "notes": [data.get("summary", "")],
            "quality_score": data.get("quality_assessment"),
            "iterations": data.get("iterations", 0),
            "review_verdict": data.get("review_verdict", ""),
        }

    async def _start_sentinel(self) -> asyncio.subprocess.Process | None:
        """Start the Sentinel as a background process to catch AI-slop in real time."""
        if not _SENTINEL_SCRIPT.exists():
            return None
        try:
            proc = await asyncio.create_subprocess_exec(
                "python", str(_SENTINEL_SCRIPT),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
                cwd=str(PROJECT_ROOT),
            )
            self.log_fn("Sentinel", "Background watcher started")
            return proc
        except Exception:
            return None

    async def _stop_sentinel(self, proc: asyncio.subprocess.Process | None) -> list[str]:
        """Stop the Sentinel and return any warnings it emitted."""
        if proc is None:
            return []
        try:
            proc.terminate()
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=3)
            lines = stdout.decode(errors="replace").strip().splitlines()
            return [l for l in lines if "[Sentinel]" in l]
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
            return []

    async def _rag_pre_hook(self, prompt: str) -> str:
        """Enrich prompt with historical context from session memory if enabled."""
        if not Config.ENABLE_HISTORICAL_CONTEXT:
            return prompt

        try:
            from src.rag_mcp.session_memory import search_similar_sessions, format_context

            sessions = search_similar_sessions(
                query=prompt,
                max_results=Config.MAX_SIMILAR_SESSIONS,
                min_relevance=Config.MIN_RELEVANCE_THRESHOLD,
            )

            if not sessions:
                return prompt

            formatted = format_context(sessions, budget_tokens=100)
            if formatted:
                return f"## Historical Context (from similar past tasks)\n{formatted}\n\n---\n\n{prompt}"
        except Exception:
            pass

        return prompt

    async def _rag_post_hook(self, result: dict, prompt: str) -> None:
        """Index the completed session into session memory if enabled."""
        if not Config.ENABLE_HISTORICAL_CONTEXT:
            return

        try:
            from src.rag_mcp.session_memory import index_session

            index_session(
                session_id=result.get("session_id", "unknown"),
                prompt=prompt,
                outcome=result.get("status", "unknown"),
                summary=result.get("notes", [""])[0] if result.get("notes") else "",
                files_touched=[f.get("path", "") for f in result.get("files_applied", []) if f.get("path")],
                iterations=result.get("iterations", 0),
            )
        except Exception:
            pass
