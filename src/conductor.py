"""
Conductor — Master orchestrator of the Vibe Coding Team.
Routes tasks to the right agents, manages parallel execution, coordinates handoffs.
"""

import asyncio
import json
from src.agents.base import BaseAgent
from src.agents.planner_agent import PlannerAgent
from src.agents.creative_agent import CreativeAgent
from src.agents.implementer_agent import ImplementerAgent
from src.agents.reviewer_agent import ReviewerAgent
from src.context_builder import ContextBuilder
from src.file_ops import FileApplicator
from src.session import Session, make_session_id
from src.config import AGENTS_DIR, Config


class ConductorAgent(BaseAgent):
    """Low-cost routing agent that classifies tasks and builds context packages."""

    def __init__(self):
        super().__init__(
            name="Conductor",
            system_prompt_path=AGENTS_DIR / "conductor.md",
            model=Config.CONDUCTOR_MODEL,
        )

    async def classify(self, context_package: str) -> dict:
        """Classify the task and determine which agents to activate."""
        user_message = (
            f"{context_package}\n\n"
            f"---\n\n"
            f"Classify this task and output the routing JSON object as specified in your system prompt. "
            f"Output ONLY the JSON — no prose."
        )
        response = await self.call(user_message=user_message, temperature=0.1, max_tokens=1024)
        return self.extract_json(response)


class Conductor:
    """
    Master orchestrator — runs the full Vibe Coding Team pipeline.

    Pipeline:
        1. Conductor classifies → asks user if uncertain
        2. Planner runs → produces plan.md
        3. Creative Brain + Implementer(s) run in parallel (if needed)
        4. Reviewer loops until PASS or max retries
        5. File changes applied to disk
        6. Walkthrough written
    """

    def __init__(self, ui=None, dry_run: bool = False):
        """
        Args:
            ui: VibeCliApp instance for live progress updates (optional)
            dry_run: Don't write files — just show what would be done
        """
        self.ui = ui
        self.dry_run = dry_run
        self.ctx = ContextBuilder()
        self.conductor_agent = ConductorAgent()
        self.planner = PlannerAgent()
        self.creative = CreativeAgent()
        self.reviewer = ReviewerAgent()
        self.file_ops = FileApplicator(dry_run=dry_run)

    def _log(self, phase: str, message: str, style: str = "info"):
        """Send a log message to the UI (if available)."""
        if self.ui:
            self.ui.log(phase, message, style)
        else:
            print(f"[{phase}] {message}")

    # ─────────────────────────────────────────────────────────────────
    # Main pipeline entrypoint
    # ─────────────────────────────────────────────────────────────────

    async def run(self, prompt: str, ask_user_fn=None) -> dict:
        """
        Run the full pipeline for a given prompt.

        Args:
            prompt: The user's task description
            ask_user_fn: Async function(question: str) -> str for uncertainty resolution

        Returns:
            Result dict with session_id, status, files_applied, walkthrough_path
        """
        Config.validate()

        # Create session
        session_id = make_session_id(prompt)
        session = Session(session_id)
        session.set("prompt", prompt)

        self._log("🎯 Conductor", f"Starting session: {session_id}")

        # ── Phase 0: Classification ─────────────────────────────────
        self._log("🎯 Conductor", "Classifying task...")
        classification = await self._classify(prompt, session)

        # Handle uncertainty
        if classification.get("confidence", 1.0) < Config.UNCERTAINTY_THRESHOLD:
            question = classification.get("uncertainty_question")
            if question and ask_user_fn:
                self._log("🎯 Conductor", f"Low confidence ({classification['confidence']:.0%}). Asking user...")
                user_answer = await ask_user_fn(question)
                # Re-classify with the clarification
                prompt = f"{prompt}\n\nClarification: {user_answer}"
                classification = await self._classify(prompt, session)

        team = classification.get("team", ["planner", "implementer_frontend", "reviewer"])
        self._log("🎯 Conductor", f"Team selected: {', '.join(team)}")
        session.set("classification", classification)
        session.mark_phase_complete("classification")

        # ── Phase 1: Planning ───────────────────────────────────────
        plan_content = None
        if "planner" in team:
            plan_content = await self._run_planner(prompt, classification, session)
        else:
            # Trivial task — generate minimal plan from prompt
            plan_content = self._minimal_plan(prompt, session.session_id)
            session.write_artifact("plan.md", plan_content)

        # ── Phase 2: Creative Brain + Implementer (parallel) ────────
        design_brief = None
        impl_result = None

        implementer_domains = self._extract_implementer_domains(team)

        if "creative_brain" in team and implementer_domains:
            # Run Creative Brain and Implementer(s) in parallel
            creative_context = self.ctx.for_creative_brain(prompt, plan_content)
            impl_context = self._build_implementer_context(
                prompt, plan_content, None, implementer_domains[0]
            )

            self._log("🎨 Creative Brain", "Designing... (parallel with implementer)")
            self._log("⚙️  Implementer", f"Implementing {implementer_domains[0]}... (parallel)")

            design_task = self.creative.design(creative_context, session.session_id)
            impl_task = self._run_implementers(
                prompt, plan_content, None, implementer_domains, session
            )
            design_brief, impl_results = await asyncio.gather(design_task, impl_task)

            session.write_artifact("design_brief.md", design_brief)
            session.mark_phase_complete("creative_brain")
            self._log("🎨 Creative Brain", "Design brief complete ✓")

            # If we got a design brief, run a second implementation pass using it
            if design_brief and "creative_brain" in team:
                self._log("⚙️  Implementer", "Re-implementing with design brief...")
                impl_results = await self._run_implementers(
                    prompt, plan_content, design_brief, implementer_domains, session
                )

        elif implementer_domains:
            # No creative brain — straight to implementation
            impl_results = await self._run_implementers(
                prompt, plan_content, None, implementer_domains, session
            )
        else:
            impl_results = []

        # Merge all file operations from all implementer domains
        all_files = []
        for result in impl_results:
            all_files.extend(result.get("files", []))

        impl_notes = []
        for result in impl_results:
            impl_notes.extend(result.get("notes", []))

        # Save implementation log
        impl_log = self._format_impl_log(impl_results)
        session.write_artifact("implementation_log.md", impl_log)

        if not all_files:
            self._log("⚠️  Warning", "No files were produced by the implementer.")
            return {"session_id": session_id, "status": "no_output", "files_applied": []}

        # ── Phase 3: Review Loop ────────────────────────────────────
        passed, review_content, walkthrough = await self._review_loop(
            prompt=prompt,
            plan_content=plan_content,
            design_brief=design_brief,
            all_files=all_files,
            impl_results=impl_results,
            session=session,
            team=team,
            implementer_domains=implementer_domains,
        )

        # ── Phase 4: Apply Files ────────────────────────────────────
        self._log("💾 Writing Files", f"Applying {len(all_files)} file(s) to disk...")
        apply_results = self.file_ops.apply_all(all_files)
        session.set("apply_results", apply_results)

        applied_ok = [r for r in apply_results if r.get("status") == "ok"]
        applied_err = [r for r in apply_results if r.get("status") == "error"]

        if applied_err:
            self._log("⚠️  Warning", f"{len(applied_err)} file(s) had errors during write.")
        self._log("💾 Writing Files", f"Applied {len(applied_ok)} file(s) successfully.")

        # ── Phase 5: Walkthrough ────────────────────────────────────
        walkthrough_path = None
        if walkthrough:
            walkthrough_path = session.write_artifact("walkthrough.md", walkthrough)
            self._log("📝 Walkthrough", f"Written to {walkthrough_path}")

        session.mark_phase_complete("done")

        return {
            "session_id": session_id,
            "status": "pass" if passed else "fail_max_retries",
            "files_applied": apply_results,
            "walkthrough_path": str(walkthrough_path) if walkthrough_path else None,
            "session_dir": str(session.session_dir),
            "notes": impl_notes,
        }

    # ─────────────────────────────────────────────────────────────────
    # Private pipeline steps
    # ─────────────────────────────────────────────────────────────────

    async def _classify(self, prompt: str, session: Session) -> dict:
        """Run the Conductor agent classification."""
        context = self.ctx.for_conductor(prompt)
        try:
            result = await self.conductor_agent.classify(context)
            # Ensure session_id is set
            result.setdefault("session_id", session.session_id)
            return result
        except (ValueError, json.JSONDecodeError):
            # Fallback: default full-stack team
            self._log("🎯 Conductor", "Classification failed — defaulting to full-stack team")
            return {
                "session_id": session.session_id,
                "classification": ["FULLSTACK"],
                "confidence": 0.5,
                "team": ["planner", "creative_brain", "implementer_frontend",
                         "implementer_backend", "reviewer"],
            }

    async def _run_planner(self, prompt: str, classification: dict, session: Session) -> str:
        """Run the Planner agent and save plan.md."""
        self._log("📋 Planner", "Decomposing task...")
        context = self.ctx.for_planner(prompt, classification)
        plan_content = await self.planner.plan(context, session.session_id)
        session.write_artifact("plan.md", plan_content)
        session.mark_phase_complete("planner")
        self._log("📋 Planner", "plan.md complete ✓")
        return plan_content

    async def _run_implementers(
        self,
        prompt: str,
        plan_content: str,
        design_brief: str | None,
        domains: list[str],
        session: Session,
        retry_count: int = 0,
        fix_instructions: str | None = None,
    ) -> list[dict]:
        """
        Run implementer agents in parallel across all domains.
        Returns list of implementation result dicts.
        """
        tasks = []
        for domain in domains:
            file_paths = self.ctx.extract_file_paths_from_plan(plan_content, "READ") + \
                         self.ctx.extract_file_paths_from_plan(plan_content, "MODIFY")

            context = self.ctx.for_implementer(
                prompt=prompt,
                plan_content=plan_content,
                design_brief=design_brief,
                file_paths_to_read=file_paths,
                domain=domain,
            )
            impl = ImplementerAgent(domain=domain)
            tasks.append(impl.implement(
                context_package=context,
                session_id=session.session_id,
                retry_count=retry_count,
                fix_instructions=fix_instructions,
            ))

        if len(tasks) == 1:
            results = [await tasks[0]]
        else:
            self._log("⚙️  Implementer", f"Running {len(tasks)} domain(s) in parallel...")
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        clean_results = []
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                self._log("❌ Implementer", f"Domain {domains[i]} failed: {r}")
                clean_results.append({"files": [], "notes": [f"FAILED: {r}"]})
            else:
                clean_results.append(r)

        session.mark_phase_complete(f"implementation_{retry_count}")
        return clean_results

    async def _review_loop(
        self,
        prompt: str,
        plan_content: str,
        design_brief: str | None,
        all_files: list[dict],
        impl_results: list[dict],
        session: Session,
        team: list[str],
        implementer_domains: list[str],
    ) -> tuple[bool, str, str | None]:
        """
        Run the Reviewer in a loop until PASS or max retries.
        Returns (passed, review_content, walkthrough).
        """
        if "reviewer" not in team:
            return True, "Reviewer skipped (trivial task)", None

        current_files = list(all_files)
        review_content = ""
        passed = False

        for attempt in range(Config.MAX_REVIEW_RETRIES + 1):
            self._log("🔍 Reviewer", f"Reviewing... (attempt {attempt + 1}/{Config.MAX_REVIEW_RETRIES + 1})")
            review_context = self.ctx.for_reviewer(
                plan_content=plan_content,
                design_brief=design_brief,
                implementation_files=current_files,
                retry_count=attempt,
            )

            passed, review_content, fix_instructions = await self.reviewer.review(
                context_package=review_context,
                session_id=session.session_id,
                retry_count=attempt,
            )
            session.write_artifact(f"review_attempt_{attempt + 1}.md", review_content)

            if passed:
                self._log("🔍 Reviewer", "✅ PASS")
                session.mark_phase_complete("reviewer_pass")
                break
            else:
                self._log("🔍 Reviewer", f"❌ FAIL — sending fix instructions to implementer")

                if attempt >= Config.MAX_REVIEW_RETRIES:
                    self._log("⚠️  Warning", f"Max retries ({Config.MAX_REVIEW_RETRIES}) reached. Using last implementation.")
                    break

                session.increment_iteration()
                # Re-run implementers with fix instructions
                fix_results = await self._run_implementers(
                    prompt=prompt,
                    plan_content=plan_content,
                    design_brief=design_brief,
                    domains=implementer_domains,
                    session=session,
                    retry_count=attempt + 1,
                    fix_instructions=fix_instructions,
                )
                current_files = []
                for r in fix_results:
                    current_files.extend(r.get("files", []))

        # Write final review
        session.write_artifact("review.md", review_content)

        # Generate walkthrough on pass
        walkthrough = None
        if passed:
            self._log("📝 Walkthrough", "Writing walkthrough...")
            walkthrough = await self.reviewer.write_walkthrough(
                prompt=prompt,
                plan_content=plan_content,
                implementation_files=current_files,
                review_content=review_content,
                session_id=session.session_id,
            )

        return passed, review_content, walkthrough

    # ─────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────

    def _extract_implementer_domains(self, team: list[str]) -> list[str]:
        """Extract implementer domain names from team list."""
        domains = []
        for member in team:
            if member.startswith("implementer_"):
                domain = member.replace("implementer_", "")
                domains.append(domain)
        return domains or ["frontend"]

    def _build_implementer_context(
        self, prompt: str, plan_content: str, design_brief: str | None, domain: str
    ) -> str:
        """Build implementer context package."""
        file_paths = (
            self.ctx.extract_file_paths_from_plan(plan_content, "READ") +
            self.ctx.extract_file_paths_from_plan(plan_content, "MODIFY")
        )
        return self.ctx.for_implementer(
            prompt=prompt,
            plan_content=plan_content,
            design_brief=design_brief,
            file_paths_to_read=file_paths,
            domain=domain,
        )

    def _minimal_plan(self, prompt: str, session_id: str) -> str:
        """Create a minimal plan for trivial tasks that skip the Planner."""
        return (
            f"# Plan: {prompt[:60]}\n"
            f"> Session: {session_id}\n"
            f"> Estimated complexity: LOW\n\n"
            f"## Acceptance Criteria\n- [ ] Task completed as described\n\n"
            f"## Scope\n### Files to MODIFY\n- [Implementer to determine]\n\n"
            f"## Task Breakdown\n### Phase 1: Implementation\n"
            f"1. {prompt}\n"
        )

    def _format_impl_log(self, impl_results: list[dict]) -> str:
        """Format implementation results as a markdown log."""
        lines = ["# Implementation Log\n"]
        for i, result in enumerate(impl_results, 1):
            lines.append(f"## Domain {i}\n")
            lines.append(f"**Summary:** {result.get('implementation_summary', 'No summary')}\n")
            files = result.get("files", [])
            if files:
                lines.append(f"**Files ({len(files)}):**")
                for f in files:
                    lines.append(f"- `{f['path']}` — {f.get('change_summary', f['operation'])}")
            notes = result.get("notes", [])
            if notes:
                lines.append("\n**Notes:**")
                for note in notes:
                    lines.append(f"- {note}")
            lines.append("")
        return "\n".join(lines)
