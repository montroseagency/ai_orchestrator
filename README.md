# Vibe Coding Team — Multi-Agent Orchestration

A multi-agent production system to take a single prompt and route it through a specialized team of AI agents to produce high-quality, production-grade code for the Montrroase project.

## The Team

1. 🎯 **Conductor**: Master orchestrator. Classifies the task and routes it.
2. 📋 **Planner**: Decomposes the task into atomic steps (`plan.md`).
3. 🎨 **Creative Brain**: Design/UX specialist that produces visual specs for frontend tasks (`design_brief.md`).
4. ⚙️ **Implementer(s)**: Writes the actual code based on the plan and design brief. Runs in parallel per domain (frontend/backend).
5. 🔍 **Reviewer**: Adversarial quality gate. Checks diffs and either passes or sends fix instructions back.

## Usage

You can use the system either via the CLI or directly within Antigravity.

### CLI

Ensure you have your `.env` configured with your `ANTHROPIC_API_KEY`.

```bash
# General task
python vibe.py "Add a dark mode toggle to the dashboard"

# Backend specific
python vibe.py "Add REST endpoint for bulk task deletion" --domain backend

# Dry run (don't write to disk)
python vibe.py "Refactor the client detail hub" --dry-run
```

### Antigravity Slash Commands

If you're using this workspace within Antigravity, you can use these shortcuts in chat:

- `/vibe <task>`: Runs the full pipeline inside Antigravity itself, applying changes directly.
- `/review-only <files>`: Runs only the Reviewer agent on specified files for a quick quality check.

## Directory Structure

- `vibe.py` — Main CLI entry point
- `src/` — Python execution engine (orchestrator, context builder, etc.)
- `_vibecoding_brain/` — The brain of the system:
  - `AGENTS.md` — Master project constitution
  - `agents/` — System prompts for each agent
  - `context/` — Reference materials (design system, tech stack, file index)
  - `workflows/` — Antigravity slash commands
  - `sessions/` — Automatically generated task state and artifacts (`plan.md`, `review.md`, etc.)

## Context Management

The system uses intelligent context trimming to minimize token usage and prevent "instruction fog." No agent ever reads the entire codebase. The Conductor assembles specific, need-to-know context packages for each agent based on the Project Constitution and the Planner's exact file lists.
