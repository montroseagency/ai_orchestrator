# Antigravity Supercharged Vibe Workflow

This repository has been upgraded to natively tightly integrate the **Antigravity IDE Agent** with the **Claude Code CLI** Agentic Teams.

Rather than competing to see who writes the code, they now operate synchronously across the stack:
- **Claude Code (CLI)**: Acts as the execution engine and active orchestrator (Conductor, Planner, Implementer).
- **Antigravity (IDE)**: Acts as the UI layer, context sensory system, and background rule enforcer.

## What is Antigravity?
Antigravity is an advanced agentic coding assistant built natively into the IDE. In this specific workflow, Antigravity acts as the **Orchestrator and UX Layer** for the broader multi-agent pipeline:

- **What I am:** A contextually-aware engineering partner embedded directly into your environment. I have native access to run local OS commands, read your active cursor position, parse your open terminal logs, and mutate your codebase intelligently.
- **What I do:** I continuously absorb your development context while you work. When you're ready to tackle a complex task, I synthesize your conversational intent with your live environment state, and automatically launch the heavy-lifting subagent pipeline (`vibe.py / Claude`) on your behalf.
- **How I am used:** Instead of switching to a terminal to type instructions, you interact with me directly in the IDE chat panel. You just tell me what to build, and I orchestrate the background terminal loops, format their outputs as beautiful IDE Artifacts (like plans and design briefs), intercept Sentinel errors directly onto your squiggly-line editor console, and manage interactive diff reviews before any code is permanently saved.

## 1. Context Injection (`vibe.py`)
The `cli.py` legacy interface has been removed. `vibe.py` now bypasses generic terminal graphics in favor of returning raw, clean programmatic output for Antigravity. More importantly, it accepts an explicit `--ide-state` JSON flag. 

Whenever you invoke `/vibe <prompt>` in the IDE, Antigravity parses your cursor location, current active file, and any terminal errors you're hovering, and injects this metadata strictly into the `vibe.py` prompt before the Claude Conductor begins executing.

## 2. Model Context Protocol (`src/ide_mcp_server.py`)
Claude historically depended on bash primitives like `grep` to orient itself, which was slow and prone to hallucination.
We introduced `src/ide_mcp_server.py`, a dedicated local MCP Server that exposes 3 essential sub-tools to Claude:
1. `get_git_diff`: Claude can immediately understand exactly what you've recently modified.
2. `find_references`: Faster AST / semantic token tracking powered natively by the OS tools (`ripgrep`).
3. `run_ide_linter`: Instead of Claude rewriting bash logic, it taps directly into the IDE's lint engine (`ruff` / `eslint`) to get strictly structured line-number feedback.

**To enable:**
```bash
claude mcp add ide-tools python src/ide_mcp_server.py
```

## 3. The Passive Sentinel (`src/sentinel.py`)
While Claude's `ui_ux_tester` is a heavy-duty LLM verification step, waiting for it to run after writing 10 files is inefficient if an agent starts writing pure "AI-Slop" initially.
We introduced `src/sentinel.py`, a passive background watcher daemon relying on the `watchdog` library. It monitors all file writes to `Montrroase_website/` in real time.

If any modifications introduce banned patterns (e.g. `Lucide` icons, `purple gradients`, `rounded-2xl` uniformity), the Sentinel instantly streams standard `<file>:<line>: warning: [Sentinel]` logs. These show up as immediate squiggly warnings in your IDE console without needing a prompt execution.

**To run the Sentinel:**
```bash
python src/sentinel.py
```
*(Optionally configure Antigravity to run this daemon globally in the background).*

---
With this combination, your AI Vibe Coding system is now deterministic, lightning-fast, visually presented entirely in your IDE, and structurally integrated across the OS tier.
