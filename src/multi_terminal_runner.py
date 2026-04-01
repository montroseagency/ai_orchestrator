"""
MultiTerminalRunner — Runs each agent in its own macOS Terminal window.

Each agent (Planner, Creative Brain, Implementer, Tester) gets a dedicated
Terminal window showing its live output. The main terminal shows orchestration
status only. Agents run sequentially; context passes through the session dir.

Usage: set VIBE_MULTI_TERMINAL=true in .env
"""

import asyncio
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

from src.config import AGENTS_DIR, CONTEXT_DIR, SESSIONS_DIR, PROJECT_ROOT, Config
from src.file_ops import FileApplicator
from src.session import make_session_id

# Agent display names and colors (ANSI for the log header)
_AGENT_META = {
    "planner":       {"title": "📋 Planner",       "color": "\033[36m"},   # cyan
    "creative_brain":{"title": "🎨 Creative Brain", "color": "\033[33m"},   # yellow
    "implementer":   {"title": "⚙️  Implementer",   "color": "\033[32m"},   # green
    "ui_ux_tester":  {"title": "🔍 UI/UX Tester",   "color": "\033[35m"},   # magenta
    "backend_tester":{"title": "🔍 Backend Tester", "color": "\033[34m"},   # blue
}

_MODEL_ALIASES = {
    "claude-haiku-4-5-20251001": "haiku",
    "claude-haiku-4-5": "haiku",
    "claude-sonnet-4-5": "sonnet",
    "claude-sonnet-4-6": "sonnet",
    "claude-opus-4-5": "opus",
    "claude-opus-4-6": "opus",
}


class MultiTerminalRunner:
    """
    Orchestrates the Vibe Coding Team with each agent in its own Terminal window.
    The Python process handles routing and context-passing; each agent is a
    separate `claude --print` subprocess streaming to its own log file.
    """

    def __init__(self, log_fn=None):
        self.log_fn = log_fn or (lambda phase, msg, **_: print(f"[{phase}] {msg}"))
        self.file_ops = FileApplicator()

    # ─────────────────────────────────────────────────────
    # Terminal window management
    # ─────────────────────────────────────────────────────

    def _open_terminal_window(self, agent: str, launcher_path: Path) -> None:
        """Open a macOS Terminal window running the agent's bash launcher (which runs claude)."""
        meta = _AGENT_META.get(agent, {"title": agent, "color": "\033[0m"})
        safe_title    = meta["title"].replace('"', '\\"')
        safe_launcher = str(launcher_path).replace("'", "'\\''")

        script = f'''
        tell application "Terminal"
            activate
            set newWin to do script "bash '{safe_launcher}'"
            delay 0.3
            set custom title of front window to "{safe_title}"
        end tell
        '''
        subprocess.Popen(
            ["osascript", "-e", script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    # ─────────────────────────────────────────────────────
    # Stream-JSON → human-readable log
    # ─────────────────────────────────────────────────────

    def _event_to_readable(self, event: dict) -> str:
        """Convert a Claude stream-json event to a human-readable log line."""
        ts = datetime.now().strftime("%H:%M:%S")
        etype = event.get("type", "")

        # Session start
        if etype == "system" and event.get("subtype") == "init":
            sid = event.get("session_id", "")
            model = event.get("model", "")
            return f"[{ts}] 🔗 Session: {sid}  model: {model}\n"

        # Claude's messages: full text + every tool use with full inputs
        if etype == "assistant":
            content = event.get("message", {}).get("content", [])
            parts = []
            for block in content:
                if block.get("type") == "text":
                    text = block.get("text", "").strip()
                    if text:
                        parts.append(f"[{ts}] {text}")

                elif block.get("type") == "tool_use":
                    name = block.get("name", "")
                    inp = block.get("input", {})

                    if name == "Write":
                        path = inp.get("file_path", "")
                        content_val = inp.get("content", "")
                        content_preview = content_val[:300]
                        parts.append(
                            f"\n[{ts}] {'─'*50}\n"
                            f"[{ts}] ✍️  WRITE → {path}\n"
                            f"{content_preview}{'…' if len(content_val) > 300 else ''}\n"
                            f"{'─'*50}"
                        )
                    elif name == "Edit":
                        parts.append(
                            f"\n[{ts}] ✏️  EDIT → {inp.get('file_path', '')}\n"
                            f"   old: {str(inp.get('old_string',''))[:120]}\n"
                            f"   new: {str(inp.get('new_string',''))[:120]}"
                        )
                    elif name == "Read":
                        parts.append(f"[{ts}] 📖 READ → {inp.get('file_path', '')}")
                    elif name == "Bash":
                        parts.append(f"[{ts}] ⚡ BASH → {inp.get('command', '')}")
                    elif name == "Glob":
                        parts.append(f"[{ts}] 🔍 GLOB → {inp.get('pattern', '')}  in: {inp.get('path','.')}")
                    elif name == "Grep":
                        parts.append(f"[{ts}] 🔎 GREP → \"{inp.get('pattern','')}\"  in: {inp.get('path','.')}")
                    elif name == "Agent":
                        desc = inp.get("description", inp.get("subagent_type", ""))
                        parts.append(f"\n[{ts}] 🤖 SPAWN AGENT → {desc}")
                    elif name == "TodoWrite":
                        todos = inp.get("todos", [])
                        lines = [f"   {'[x]' if t.get('status')=='completed' else '[ ]'} {t.get('content','')}" for t in todos]
                        parts.append(f"[{ts}] 📋 TODOS:\n" + "\n".join(lines))
                    else:
                        # Any other tool — show name + full input JSON
                        parts.append(f"[{ts}] 🔧 {name} → {json.dumps(inp)[:300]}")

            return "\n".join(parts)

        # Tool results — what the tool returned
        if etype == "tool_result":
            is_error = event.get("is_error", False)
            raw = event.get("content", "")
            if isinstance(raw, list):
                raw = "\n".join(b.get("text", "") for b in raw if b.get("type") == "text")
            raw = str(raw).strip()
            if is_error:
                return f"\n[{ts}] ❌ TOOL ERROR:\n{raw[:600]}\n"
            elif raw:
                preview = raw[:500] + ("…" if len(raw) > 500 else "")
                return f"[{ts}]    ↳ {preview}\n"

        # Final result
        if etype == "result":
            cost = event.get("total_cost_usd")
            turns = event.get("num_turns", "?")
            cost_str = f"  cost: ${cost:.4f}" if cost else ""
            return f"\n[{ts}] {'═'*60}\n[{ts}] ✅ DONE  turns: {turns}{cost_str}\n{'═'*60}\n"

        # Fallback: show unknown events so we can see what Claude CLI emits
        if etype and etype != "user":
            return f"[{ts}] ⚙ {etype}: {json.dumps(event, default=str)[:300]}\n"

        return ""

    # ─────────────────────────────────────────────────────
    # Core agent runner
    # ─────────────────────────────────────────────────────

    def _write_launcher(
        self,
        agent: str,
        session_dir: Path,
        model: str,
        system_prompt: str,
        user_message: str,
    ) -> tuple[Path, Path]:
        """
        Write a bash launcher script for this agent and the config files it reads.

        The launcher opens a real `claude` CLI session directly in the Terminal window
        (no Python subprocess wrapper). claude's stdout goes straight to the TTY so
        output appears live without any buffering delays.

        claude is instructed (via an appended completion protocol in its system prompt)
        to use its Write tool to save results to output_file and write ---VIBE_DONE---
        when done. The orchestrator polls that file to know when to start the next agent.

        Returns (launcher_path, output_file_path).
        """
        meta  = _AGENT_META.get(agent, {"title": agent, "color": "\033[0m"})
        title = meta["title"]
        c     = meta["color"]   # actual ANSI bytes — embed directly into the bash file
        r     = "\033[0m"

        prompt_file   = session_dir / f"{agent}_system_prompt.txt"
        msg_file      = session_dir / f"{agent}_initial_message.txt"
        output_file   = session_dir / f"{agent}_output.txt"
        launcher_file = session_dir / f"{agent}_launch.sh"

        # Append completion protocol so claude signals the orchestrator when done.
        # claude uses its OWN Write tool to write the output file + done marker.
        # This avoids any pipe/tee buffering — output streams live to the terminal TTY.
        completion_protocol = (
            "\n\n---\n\n"
            "## COMPLETION PROTOCOL (mandatory — do not skip)\n\n"
            "When you have completely finished your task, use your Write tool twice:\n\n"
            f"1. Write your complete output to this exact path: `{output_file}`\n"
            "   (your full plan / design brief / review / JSON summary — whatever your task produces)\n\n"
            f"2. Write the single line `---VIBE_DONE---` appended to `{output_file}`.\n\n"
            "The orchestrator is polling that file. If you do not write it, the pipeline hangs forever.\n"
        )
        prompt_file.write_text(system_prompt + completion_protocol, encoding="utf-8")
        msg_file.write_text(user_message, encoding="utf-8")
        output_file.unlink(missing_ok=True)   # clear any previous run

        # Safe single-quoted absolute paths for bash
        def sq(p: str) -> str:
            return p.replace("'", "'\\''")

        # The bash launcher runs `claude` directly in this Terminal window.
        # - claude's stdout → straight to TTY, no buffering, user sees output live
        # - Closing the Terminal sends SIGHUP → bash dies → claude dies immediately
        # - Bash reads prompt/message from files so no shell-escaping issues
        sep = f"{c}{'═' * 62}{r}"
        launcher_src = (
            "#!/bin/bash\n"
            f"# Auto-generated launcher for: {title}\n\n"
            f"printf '\\n{sep}\\n'\n"
            f"printf '{c}  {title}{r}\\n'\n"
            f"printf '{sep}\\n\\n'\n\n"
            f"cd '{sq(str(PROJECT_ROOT))}'\n\n"
            f"SYSTEM_PROMPT=$(cat '{sq(str(prompt_file))}')\n"
            f"INITIAL_MESSAGE=$(cat '{sq(str(msg_file))}')\n\n"
            f"'{sq(Config.CLAUDE_CLI_PATH)}' \\\\\n"
            f"    --print \\\\\n"
            f"    --verbose \\\\\n"
            f"    --model '{model}' \\\\\n"
            f"    --system-prompt \"$SYSTEM_PROMPT\" \\\\\n"
            f"    --dangerously-skip-permissions \\\\\n"
            f"    --no-session-persistence \\\\\n"
            f"    --add-dir '{sq(str(PROJECT_ROOT))}' \\\\\n"
            f"    --output-format text \\\\\n"
            f"    \"$INITIAL_MESSAGE\"\n\n"
            f"printf '\\n{sep}\\n'\n"
            f"printf '{c}  {title}  ✅  complete — close this window when ready.{r}\\n'\n"
            f"printf '{sep}\\n'\n"
            "read\n"
        )
        launcher_file.write_text(launcher_src, encoding="utf-8")
        launcher_file.chmod(0o755)
        return launcher_file, output_file

    async def _run_agent(
        self,
        name: str,
        system_prompt_path: Path,
        user_message: str,
        session_dir: Path,
        model: str | None = None,
        extra_context: str = "",
        use_tools: bool = False,   # kept for API compat; text mode used in terminal
    ) -> str:
        """
        Open a Terminal window running a real `claude --print` session for this agent.
        Waits until the session writes ---VIBE_DONE--- to its output file, then
        returns the captured text so the orchestrator can pass it to the next agent.
        Closing the Terminal window kills claude immediately.
        """
        model = model or _MODEL_ALIASES.get(Config.PLANNER_MODEL, "sonnet")
        system_prompt = system_prompt_path.read_text(encoding="utf-8")
        if extra_context:
            system_prompt = f"{system_prompt}\n\n---\n\n{extra_context}"

        meta  = _AGENT_META.get(name, {"title": name, "color": "\033[0m"})
        title = meta["title"]

        launcher_file, output_file = self._write_launcher(
            name, session_dir, model, system_prompt, user_message
        )

        self._open_terminal_window(name, launcher_file)
        self.log_fn(title, "Claude session opened — switch to that window to watch live")

        result_text = await self._wait_for_output(title, output_file)
        return result_text

    # ─────────────────────────────────────────────────────
    # Output poller  (replaces heartbeat)
    # ─────────────────────────────────────────────────────

    async def _wait_for_output(self, title: str, output_file: Path, timeout_s: int = 2700) -> str:
        """
        Poll output_file until the agent writes ---VIBE_DONE---.
        Logs heartbeat progress to the main terminal every 30 s.
        Returns everything before the done marker on success, empty string on timeout.
        """
        start = asyncio.get_event_loop().time()
        last_hb = start

        while True:
            await asyncio.sleep(2.0)
            now = asyncio.get_event_loop().time()
            elapsed = int(now - start)

            if output_file.exists():
                content = output_file.read_text(encoding="utf-8", errors="replace")
                if "---VIBE_DONE---" in content:
                    result = content.split("---VIBE_DONE---")[0].strip()
                    self.log_fn(title, f"done ✓  ({elapsed}s)")
                    return result

            if now - last_hb >= 30:
                self.log_fn(title, f"still running... ({elapsed}s elapsed)")
                last_hb = now

            if elapsed > timeout_s:
                self.log_fn(title, f"⚠️  timeout after {timeout_s}s")
                if output_file.exists():
                    return output_file.read_text(encoding="utf-8", errors="replace")
                return ""

    # ─────────────────────────────────────────────────────
    # Context builders
    # ─────────────────────────────────────────────────────

    def _read_context_file(self, name: str) -> str:
        path = CONTEXT_DIR / name
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def _build_planner_prompt(self, prompt: str) -> str:
        agents_md = self._read_context_file("AGENTS.md") or self._read_context_file("../AGENTS.md")
        project_index = self._read_context_file("project_index.md")
        tech_stack = self._read_context_file("tech_stack.md")

        parts = [f"# Task\n{prompt}"]
        if agents_md:
            parts.append(f"# Project Rules (AGENTS.md)\n{agents_md}")
        if project_index:
            parts.append(f"# Project File Index\n{project_index}")
        if tech_stack:
            parts.append(f"# Tech Stack\n{tech_stack}")
        parts.append("Produce a complete plan.md. Output ONLY the plan.md content.")
        return "\n\n---\n\n".join(parts)

    def _build_creative_prompt(self, prompt: str, plan: str) -> str:
        design_system = self._read_context_file("design_system.md")
        parts = [
            f"# Task\n{prompt}",
            f"# plan.md\n{plan}",
        ]
        if design_system:
            parts.append(f"# Design System\n{design_system}")
        parts.append(
            "Work through Phase 0 Design Thinking, then produce a complete design_brief.md. "
            "Output ONLY the design_brief.md content."
        )
        return "\n\n---\n\n".join(parts)

    def _build_implementer_prompt(
        self, prompt: str, plan: str, design_brief: str, fix_instructions: str, iteration: int
    ) -> str:
        parts = [f"# Task\n{prompt}", f"# plan.md\n{plan}"]
        if design_brief:
            parts.append(f"# design_brief.md\n{design_brief}")
        if fix_instructions:
            parts.append(
                f"# ⚠️ Retry #{iteration} — Fix EXACTLY these issues, change nothing else\n{fix_instructions}"
            )
        parts.append(
            "Implement the plan by writing all files directly to disk using your Write and Edit tools.\n"
            "When ALL files are written, return ONLY this single-line JSON (no explanation):\n"
            '{"files_written": ["path/to/file1", "path/to/file2"], "summary": "one sentence"}'
        )
        return "\n\n---\n\n".join(parts)

    def _build_tester_prompt(self, prompt: str, plan: str, design_brief: str, files: list[dict]) -> str:
        files_content = "\n\n".join(
            f"## `{f['path']}`\n```\n{f.get('content','')[:3000]}\n```"
            for f in files
        )
        parts = [
            f"# Task\n{prompt}",
            f"# plan.md\n{plan}",
        ]
        if design_brief:
            parts.append(f"# design_brief.md\n{design_brief}")
        parts.append(f"# Implementation Files\n{files_content}")
        parts.append(
            "Produce a complete UI/UX test report. "
            "If FAIL, separate fix instructions with `---FIX_INSTRUCTIONS---` on its own line."
        )
        return "\n\n---\n\n".join(parts)

    # ─────────────────────────────────────────────────────
    # JSON parsing helpers
    # ─────────────────────────────────────────────────────

    def _extract_files_written(self, raw: str) -> list[str]:
        """Extract the files_written list from implementer's end-of-run summary."""
        start = raw.rfind("{")   # last JSON object = the summary (not internal reasoning)
        if start != -1:
            depth = 0
            for i, ch in enumerate(raw[start:], start):
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            data = json.loads(raw[start:i + 1])
                            files = data.get("files_written", [])
                            if isinstance(files, list):
                                return [f for f in files if isinstance(f, str)]
                        except json.JSONDecodeError:
                            break
        return []

    def _extract_json_files(self, raw: str) -> list[dict]:
        """Extract the files array from implementer JSON output."""
        # Try JSON code block
        m = re.search(r"```json\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1)).get("files", [])
            except json.JSONDecodeError:
                pass
        # Try bare JSON object
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
                            return json.loads(raw[start: i + 1]).get("files", [])
                        except json.JSONDecodeError:
                            break
        return []

    def _extract_fix_instructions(self, review: str) -> str:
        if "---FIX_INSTRUCTIONS---" in review:
            return review.split("---FIX_INSTRUCTIONS---", 1)[1].strip()
        return ""

    # ─────────────────────────────────────────────────────
    # Main pipeline
    # ─────────────────────────────────────────────────────

    async def run(self, prompt: str) -> dict:
        """
        Run the full multi-agent pipeline with each agent in its own Terminal window.
        """
        session_id = make_session_id(prompt)
        session_dir = SESSIONS_DIR / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        self.log_fn("🎯 Orchestrator", f"Session: {session_id}")

        # ── Classify task ────────────────────────────────
        domain = await self._classify_task(prompt)
        self.log_fn("🎯 Orchestrator", f"Domain: {domain}")

        needs_creative = domain in ("FRONTEND", "FULLSTACK", "DESIGN")
        needs_ui_test  = domain in ("FRONTEND", "FULLSTACK", "DESIGN")
        needs_be_test  = domain in ("BACKEND", "FULLSTACK", "DATABASE", "REFACTOR")

        pipeline = (
            ["planner"]
            + (["creative_brain"] if needs_creative else [])
            + ["implementer"]
            + (["ui_ux_tester"] if needs_ui_test else [])
            + (["backend_tester"] if needs_be_test else [])
        )
        self.log_fn("🎯 Orchestrator", f"Pipeline: {' → '.join(pipeline)}")

        # ── Step 1: Planner ──────────────────────────────
        plan = await self._run_agent(
            "planner",
            AGENTS_DIR / "planner.md",
            self._build_planner_prompt(prompt),
            session_dir,
            model=_MODEL_ALIASES.get(Config.PLANNER_MODEL, "sonnet"),
        )
        (session_dir / "plan.md").write_text(plan, encoding="utf-8")

        # ── Step 2: Creative Brain (frontend/fullstack only) ──
        design_brief = ""
        if needs_creative:
            design_brief = await self._run_agent(
                "creative_brain",
                AGENTS_DIR / "creative_brain.md",
                self._build_creative_prompt(prompt, plan),
                session_dir,
                model=_MODEL_ALIASES.get(Config.CREATIVE_MODEL, "sonnet"),
            )
            (session_dir / "design_brief.md").write_text(design_brief, encoding="utf-8")

        # ── Steps 3+: Implement → Test loop ──────────────
        all_files: list[dict] = []
        apply_results: list[dict] = []
        passed = False
        fix_instructions = ""

        for iteration in range(Config.MAX_REVIEW_RETRIES + 1):
            iter_label = f"(attempt {iteration + 1})" if iteration > 0 else ""
            self.log_fn("⚙️  Implementer", f"Starting... {iter_label}")

            impl_raw = await self._run_agent(
                "implementer",
                AGENTS_DIR / "implementer.md",
                self._build_implementer_prompt(prompt, plan, design_brief, fix_instructions, iteration),
                session_dir,
                model=_MODEL_ALIASES.get(Config.IMPLEMENTER_MODEL, "sonnet"),
                use_tools=True,
            )

            files_written = self._extract_files_written(impl_raw)
            if files_written:
                self.log_fn("💾 Files", f"Written: {', '.join(files_written[:4])}")
                all_files = [
                    {
                        "path": p,
                        "content": (PROJECT_ROOT / p).read_text(errors="replace")
                        if (PROJECT_ROOT / p).exists() else "",
                        "operation": "CREATE",
                        "change_summary": "Written by implementer",
                    }
                    for p in files_written
                ]
                apply_results = [{"path": p, "status": "ok", "operation": "write"} for p in files_written]
                self._update_project_index(all_files, apply_results)
            else:
                self.log_fn("⚠️  Warning", "Implementer returned no file list")
                all_files = []
                apply_results = []

            # ── Test ──────────────────────────────────────
            if not (needs_ui_test or needs_be_test):
                passed = True
                break

            review_text = ""
            if needs_ui_test:
                self.log_fn("🔍 UI/UX Tester", f"Starting... {iter_label}")

                extra = ""
                skill_path = AGENTS_DIR / "skills" / "web_accessibility.md"
                if skill_path.exists():
                    extra = skill_path.read_text(encoding="utf-8")

                review_text = await self._run_agent(
                    "ui_ux_tester",
                    AGENTS_DIR / "ui_ux_tester.md",
                    self._build_tester_prompt(prompt, plan, design_brief, all_files),
                    session_dir,
                    model=_MODEL_ALIASES.get(Config.UIUX_TESTER_MODEL, "sonnet"),
                    extra_context=extra,
                )

            if needs_be_test and not review_text:
                self.log_fn("🔍 Backend Tester", f"Starting... {iter_label}")
                review_text = await self._run_agent(
                    "backend_tester",
                    AGENTS_DIR / "backend_tester.md",
                    self._build_tester_prompt(prompt, plan, design_brief, all_files),
                    session_dir,
                    model=_MODEL_ALIASES.get(Config.BACKEND_TESTER_MODEL, "sonnet"),
                )

            passed = "✅ PASS" in review_text or ("PASS" in review_text and "FAIL" not in review_text)
            fix_instructions = self._extract_fix_instructions(review_text)

            if passed:
                self.log_fn("✅ Review", "PASS")
                break
            else:
                self.log_fn("❌ Review", f"FAIL — retry {iteration + 1}/{Config.MAX_REVIEW_RETRIES}")
                if iteration >= Config.MAX_REVIEW_RETRIES:
                    self.log_fn("⚠️  Orchestrator", "Max retries reached")
                    break

        # ── Final ─────────────────────────────────────────
        self.log_fn(
            "🎯 Orchestrator",
            f"{'✅ PASS' if passed else '❌ FAIL'} | "
            f"session: {session_id} | "
            f"logs: {session_dir}",
        )

        return {
            "session_id": session_id,
            "status": "pass" if passed else "fail_max_retries",
            "files_applied": apply_results,
            "walkthrough_path": None,
            "session_dir": str(session_dir),
            "notes": [],
            "quality_score": None,
        }

    # ─────────────────────────────────────────────────────
    # Task classification (lightweight)
    # ─────────────────────────────────────────────────────

    async def _classify_task(self, prompt: str) -> str:
        """Quick classification via a short claude call (no separate terminal)."""
        classify_msg = (
            f"Classify this development task into exactly one of: "
            f"FRONTEND | BACKEND | FULLSTACK | TRIVIAL | DESIGN | DATABASE | REFACTOR\n\n"
            f"Task: {prompt}\n\n"
            f"Reply with ONLY the classification word."
        )
        cmd = [
            Config.CLAUDE_CLI_PATH,
            "--print",
            "--model", _MODEL_ALIASES.get(Config.CONDUCTOR_MODEL, "haiku"),
            "--output-format", "text",
            "--no-session-persistence",
            "--dangerously-skip-permissions",
            "--verbose",
        ]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            proc.stdin.write(classify_msg.encode())
            await proc.stdin.drain()
            proc.stdin.close()
            stdout, _ = await proc.communicate()
            result = stdout.decode().strip().upper()
            for cls in ("FRONTEND", "BACKEND", "FULLSTACK", "TRIVIAL", "DESIGN", "DATABASE", "REFACTOR"):
                if cls in result:
                    return cls
        except Exception:
            pass
        return "FRONTEND"   # safe default

    # ─────────────────────────────────────────────────────
    # project_index.md auto-update (mirrors Conductor logic)
    # ─────────────────────────────────────────────────────

    def _update_project_index(self, all_files: list[dict], apply_results: list[dict]) -> None:
        index_path = CONTEXT_DIR / "project_index.md"
        if not index_path.exists():
            return
        summaries = {
            op.get("path", ""): op.get("change_summary", "New file")
            for op in all_files
            if op.get("operation", "").upper() == "CREATE"
        }
        existing = index_path.read_text(encoding="utf-8")
        new_entries = []
        for result in apply_results:
            if result.get("operation", "").upper() == "CREATE" and result.get("status") == "ok":
                rel = result.get("path", "")
                if rel and f"`{rel}`" not in existing:
                    summary = summaries.get(rel, "New file")
                    if len(summary) > 80:
                        summary = summary[:77] + "..."
                    new_entries.append(f"| `{rel}` | {summary} |")
        if not new_entries:
            return
        section = "## Recent Additions"
        if section in existing:
            lines = existing.splitlines()
            idx = len(lines)
            in_sec = False
            for i, line in enumerate(lines):
                if line.strip() == section:
                    in_sec = True
                    continue
                if in_sec and line.startswith("## "):
                    idx = i
                    break
            lines = lines[:idx] + new_entries + lines[idx:]
            index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        else:
            with index_path.open("a", encoding="utf-8") as f:
                f.write(f"\n{section}\n| File | Purpose |\n|------|---------|\n")
                f.write("\n".join(new_entries) + "\n")
        self.log_fn("📋 Index", f"Updated with {len(new_entries)} new file(s)")
