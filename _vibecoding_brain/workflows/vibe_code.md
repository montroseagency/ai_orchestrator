---
description: Run the full Vibe Coding Team pipeline — Planner, Creative Brain, Implementer, and Reviewer — on a given task
---

# /vibe — Vibe Coding Team

This workflow orchestrates the full multi-agent pipeline inside Antigravity.
Use it by typing `/vibe` followed by your task description in the chat.

**Example:** `/vibe Add a dark mode toggle to the sidebar with smooth transitions`

---

## Usage

When the user types `/vibe <task>`, extract the task description (everything after `/vibe`) and execute the following steps in order.

---

## Step 1: Load Project Context

Read these files to understand the project:
1. Read `c:\Users\User\Documents\GitHub\agentic_workflow\_vibecoding_brain\AGENTS.md` — project constitution
2. Read `c:\Users\User\Documents\GitHub\agentic_workflow\_vibecoding_brain\context\project_index.md` — file index

Summarize the project context in <100 words internally. Do not show this to the user.

---

## Step 2: Classify the Task

Using the loaded context, internally classify the task:
- **Domain tags:** FRONTEND | BACKEND | FULLSTACK | TRIVIAL | DESIGN | DATABASE | REFACTOR
- **Confidence:** 0.0–1.0
- **Team needed:** Which agents to activate

If confidence < 0.65, ask the user ONE focused clarifying question before proceeding.

---

## Step 3: Planning (skip if TRIVIAL)

Read the Planner system prompt:
- Read `c:\Users\User\Documents\GitHub\agentic_workflow\_vibecoding_brain\agents\planner.md`

Act as the Planner. Produce a `plan.md` following the exact format in the planner prompt.
Be specific about file paths relative to `Montrroase_website/` root.

Show the plan to the user with a "📋 Plan ready — proceeding to implementation" message.

---

## Step 4: Creative Brief (FRONTEND/DESIGN tasks only)

If the task involves frontend UI changes:

Read the Creative Brain system prompt:
- Read `c:\Users\User\Documents\GitHub\agentic_workflow\_vibecoding_brain\agents\creative_brain.md`
- Read `c:\Users\User\Documents\GitHub\agentic_workflow\_vibecoding_brain\context\design_system.md`

Act as the Creative Brain. Produce a `design_brief.md` following the exact format.
Show a "🎨 Design brief ready" message.

---

## Step 5: Implementation

Read the Implementer system prompt:
- Read `c:\Users\User\Documents\GitHub\agentic_workflow\_vibecoding_brain\agents\implementer.md`
- Read `c:\Users\User\Documents\GitHub\agentic_workflow\_vibecoding_brain\context\tech_stack.md`

Read all files listed in plan.md under "Files to READ" and "Files to MODIFY".

Act as the Implementer. Produce complete, production-quality code for all files.
Output code directly using the write_to_file / multi_replace_file_content tools — apply changes to the actual project files.

Show a "⚙️ Implementation complete — {N} files modified" message.

---

## Step 6: Review

Read the Reviewer system prompt:
- Read `c:\Users\User\Documents\GitHub\agentic_workflow\_vibecoding_brain\agents\reviewer.md`

Act as the Reviewer. Review all changes made in Step 5.
Produce a `review.md` following the exact format.

**If PASS:** Write a brief walkthrough and show "✅ Done — task complete."
**If FAIL:** List specific issues and fix them immediately (acting as Implementer again), then re-review. Maximum 3 fix cycles.

---

## Step 7: Session Artifacts

Save all artifacts to `_vibecoding_brain/sessions/<task-slug>/`:
- `plan.md`
- `design_brief.md` (if applicable)
- `review.md`
- `walkthrough.md`

Show the user a final summary with:
- Files changed (list)
- Review verdict
- Link to session dir
