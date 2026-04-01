"""
Conductor — Master orchestrator of the Vibe Coding Team.
Routes tasks to the right agents, manages parallel execution, coordinates handoffs.
Integrates RAG-based memory for cross-session learning and pattern recognition.
"""

import asyncio
import json
from pathlib import Path
from typing import Optional
from src.agents.base import BaseAgent
from src.agents.planner_agent import PlannerAgent
from src.agents.creative_agent import CreativeAgent
from src.agents.implementer_agent import ImplementerAgent
from src.agents.ui_ux_tester_agent import UIUXTesterAgent
from src.agents.backend_tester_agent import BackendTesterAgent
from src.context_builder import ContextBuilder
from src.file_ops import FileApplicator
from src.session import Session, make_session_id
from src.config import AGENTS_DIR, CONTEXT_DIR, Config


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
        self.ui_ux_tester = UIUXTesterAgent()
        self.backend_tester = BackendTesterAgent()
        self.file_ops = FileApplicator(dry_run=dry_run)

        # RAG components (lazy-loaded)
        self._rag = None
        self._session_indexer = None
        self._lesson_extractor = None
        self._router = None

        # Improvement components (lazy-loaded)
        self._self_healer = None
        self._quality_scorer = None
        self._reflection_engine = None
        self._stuck_detector = None
        self._metrics = None

    # ─────────────────────────────────────────────────────────────────
    # RAG Properties (lazy-loaded)
    # ─────────────────────────────────────────────────────────────────

    @property
    def rag(self):
        """Lazy-load RagServer."""
        if self._rag is None and self._rag_enabled():
            try:
                from src.rag import get_rag_client
                self._rag = get_rag_client()
            except ImportError:
                pass
        return self._rag

    @property
    def session_indexer(self):
        """Lazy-load SessionIndexer."""
        if self._session_indexer is None and self._rag_enabled():
            try:
                from src.rag import SessionIndexer
                self._session_indexer = SessionIndexer(rag_client=self.rag)
            except ImportError:
                pass
        return self._session_indexer

    @property
    def lesson_extractor(self):
        """Lazy-load LessonExtractor."""
        if self._lesson_extractor is None and self._rag_enabled():
            try:
                from src.rag import LessonExtractor
                self._lesson_extractor = LessonExtractor(rag_client=self.rag)
            except ImportError:
                pass
        return self._lesson_extractor

    @property
    def router(self):
        """Lazy-load MessageRouter."""
        if self._router is None:
            try:
                from src.coordination import get_router
                self._router = get_router()
            except ImportError:
                pass
        return self._router

    def _rag_enabled(self) -> bool:
        """Check if RAG is enabled in configuration."""
        return getattr(Config, "ENABLE_HISTORICAL_CONTEXT", False)

    # ─────────────────────────────────────────────────────────────────
    # Improvement Properties (lazy-loaded)
    # ─────────────────────────────────────────────────────────────────

    @property
    def self_healer(self):
        """Lazy-load SelfHealingLoop."""
        if self._self_healer is None:
            try:
                from src.improvement import SelfHealingLoop
                self._self_healer = SelfHealingLoop()
            except ImportError:
                pass
        return self._self_healer

    @property
    def quality_scorer(self):
        """Lazy-load QualityScorer."""
        if self._quality_scorer is None:
            try:
                from src.improvement import QualityScorer
                self._quality_scorer = QualityScorer()
            except ImportError:
                pass
        return self._quality_scorer

    @property
    def reflection_engine(self):
        """Lazy-load ReflectionEngine."""
        if self._reflection_engine is None:
            try:
                from src.improvement import ReflectionEngine
                self._reflection_engine = ReflectionEngine()
            except ImportError:
                pass
        return self._reflection_engine

    @property
    def stuck_detector(self):
        """Lazy-load StuckDetector."""
        if self._stuck_detector is None:
            try:
                from src.improvement import StuckDetector
                self._stuck_detector = StuckDetector()
            except ImportError:
                pass
        return self._stuck_detector

    @property
    def metrics(self):
        """Lazy-load MetricsTracker."""
        if self._metrics is None:
            try:
                from src.improvement import MetricsTracker
                self._metrics = MetricsTracker()
            except ImportError:
                pass
        return self._metrics

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

        # ── CLI mode: use real agent teams ──────────────────────────
        if Config.USE_CLAUDE_CLI:
            from src.team_runner import CliTeamRunner
            runner = CliTeamRunner(log_fn=self._log)
            return await runner.run(prompt)

        # Create session
        session_id = make_session_id(prompt)
        session = Session(session_id)
        session.set("prompt", prompt)

        self._log("🎯 Conductor", f"Starting session: {session_id}")

        # Start metrics tracking
        if self.metrics:
            self.metrics.start_session(session_id, prompt)

        # ── Pre-Classification: Historical Context ──────────────────
        historical_hints = None
        if self._rag_enabled():
            historical_hints = await self._get_historical_context(prompt)
            if historical_hints:
                self._log("🧠 RAG", "Found similar past tasks")

        # ── Phase 0: Classification ─────────────────────────────────
        self._log("🎯 Conductor", "Classifying task...")
        classification = await self._classify(prompt, session, historical_hints=historical_hints)

        # Handle uncertainty
        if classification.get("confidence", 1.0) < Config.UNCERTAINTY_THRESHOLD:
            question = classification.get("uncertainty_question")
            if question and ask_user_fn:
                self._log("🎯 Conductor", f"Low confidence ({classification['confidence']:.0%}). Asking user...")
                user_answer = await ask_user_fn(question)
                # Re-classify with the clarification
                prompt = f"{prompt}\n\nClarification: {user_answer}"
                classification = await self._classify(prompt, session, historical_hints=historical_hints)

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
            if self.metrics:
                self.metrics.end_session("no_output")
            return {"session_id": session_id, "status": "no_output", "files_applied": []}

        # ── Phase 2.5: Self-Healing Loop ─────────────────────────────
        healing_result = None
        if self.self_healer and not self.dry_run:
            if self.metrics:
                self.metrics.start_phase("self_healing")

            self._log("🔧 Self-Heal", "Running validation checks...")
            domain = implementer_domains[0] if implementer_domains else "frontend"

            async def _reimpl(fix_instructions):
                results = await self._run_implementers(
                    prompt=prompt, plan_content=plan_content,
                    design_brief=design_brief, domains=implementer_domains,
                    session=session, retry_count=1,
                    fix_instructions=fix_instructions,
                )
                new_files = []
                for r in results:
                    new_files.extend(r.get("files", []))
                return new_files

            healing_result = await self.self_healer.heal(
                files=all_files,
                domain=domain,
                reimplementation_fn=_reimpl,
                log_fn=self._log,
            )

            if healing_result.healed:
                self._log("🔧 Self-Heal", f"Healed in {healing_result.attempts} attempt(s) ✓")
            elif healing_result.attempts > 0:
                self._log("🔧 Self-Heal", f"Could not fully heal after {healing_result.attempts} attempt(s)")

            if self.metrics:
                self.metrics.end_phase("self_healing", success=healing_result.healed)
                self.metrics.record_healing(
                    attempted=True,
                    success=healing_result.healed,
                    attempts=healing_result.attempts,
                    failures=sum(1 for v in healing_result.validations if not v.passed),
                )

        # ── Phase 3: Test Loop ──────────────────────────────────────
        domain = self._classify_domain(implementer_domains)
        passed, review_content, walkthrough = await self._test_loop(
            prompt=prompt,
            plan_content=plan_content,
            design_brief=design_brief,
            all_files=all_files,
            impl_results=impl_results,
            session=session,
            team=team,
            implementer_domains=implementer_domains,
            domain=domain,
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

        # Update project_index.md with any newly created files
        self._update_project_index(all_files, apply_results)

        # ── Phase 5: Walkthrough ────────────────────────────────────
        walkthrough_path = None
        if walkthrough:
            walkthrough_path = session.write_artifact("walkthrough.md", walkthrough)
            self._log("📝 Walkthrough", f"Written to {walkthrough_path}")

        session.mark_phase_complete("done")

        # ── Phase 6: Quality Scoring ─────────────────────────────────
        quality_score = None
        if self.quality_scorer:
            try:
                self._log("📊 Quality", "Scoring implementation...")
                quality_score = await self.quality_scorer.score_implementation(
                    plan_content=plan_content,
                    implementation_files=all_files,
                    review_content=review_content,
                )
                self._log("📊 Quality", quality_score.summary())
                session.set("quality_score", quality_score.to_dict())

                if self.metrics:
                    self.metrics.record_quality_score(quality_score.overall)
            except Exception as e:
                self._log("📊 Quality", f"Scoring failed: {e}")

        # ── Phase 7: Post-Pipeline Hooks (RAG) ──────────────────────
        await self._post_pipeline_hooks(session, passed, session.iterations)

        # ── Phase 8: Reflection ──────────────────────────────────────
        if self.reflection_engine:
            try:
                self._log("🪞 Reflection", "Generating post-task reflection...")
                reflection = await self.reflection_engine.reflect(
                    session_id=session_id,
                    prompt=prompt,
                    plan_content=plan_content,
                    status="pass" if passed else "fail",
                    review_content=review_content,
                    files=all_files,
                    retry_count=session.iterations,
                    quality_score=quality_score.overall if quality_score else 0.0,
                    healing_result=healing_result,
                )
                reflection_path = self.reflection_engine.save_reflection(reflection, session.session_dir)
                self._log("🪞 Reflection", f"Saved to {reflection_path}")

                # Log key learnings
                if reflection.prompt_improvements:
                    self._log("🪞 Reflection", f"Prompt improvement: {reflection.prompt_improvements[0]}")
            except Exception as e:
                self._log("🪞 Reflection", f"Reflection failed: {e}")

        # ── Phase 9: Finalize Metrics ────────────────────────────────
        if self.metrics:
            self.metrics.record_review(passed, session.iterations)
            self.metrics.record_files(len(all_files), implementer_domains)
            session_metrics = self.metrics.end_session("pass" if passed else "fail_max_retries")
            if session_metrics:
                self._log("📊 Metrics", session_metrics.summary_line())

        return {
            "session_id": session_id,
            "status": "pass" if passed else "fail_max_retries",
            "files_applied": apply_results,
            "walkthrough_path": str(walkthrough_path) if walkthrough_path else None,
            "session_dir": str(session.session_dir),
            "notes": impl_notes,
            "quality_score": quality_score.to_dict() if quality_score else None,
        }

    # ─────────────────────────────────────────────────────────────────
    # Private pipeline steps
    # ─────────────────────────────────────────────────────────────────

    async def _classify(
        self,
        prompt: str,
        session: Session,
        historical_hints: Optional[str] = None,
    ) -> dict:
        """Run the Conductor agent classification."""
        context = self.ctx.for_conductor(prompt)

        # Inject historical hints if available
        if historical_hints:
            context = f"{context}\n\n## Historical Context\n{historical_hints}"

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

        # Inject historical context if RAG is enabled
        if self._rag_enabled():
            context = await self.ctx.with_historical_context(prompt, context, "planner")

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
        issue_types: list[str] | None = None,
    ) -> list[dict]:
        """
        Run implementer agents in parallel across all domains.
        Returns list of implementation result dicts.
        """
        file_paths = self.ctx.extract_file_paths_from_plan(plan_content, "READ") + \
                     self.ctx.extract_file_paths_from_plan(plan_content, "MODIFY")

        # Build base contexts for all domains
        base_contexts = [
            self.ctx.for_implementer(
                prompt=prompt,
                plan_content=plan_content,
                design_brief=design_brief,
                file_paths_to_read=file_paths,
                domain=domain,
            )
            for domain in domains
        ]

        # Fetch RAG context for all domains in parallel (was sequential before)
        if self._rag_enabled():
            async def _enrich_context(ctx: str) -> str:
                ctx = await self.ctx.with_historical_context(prompt, ctx, "implementer")
                if issue_types and retry_count > 0:
                    ctx = await self.ctx.with_lesson_injections(ctx, issue_types, "implementer")
                return ctx

            enriched = await asyncio.gather(*[_enrich_context(ctx) for ctx in base_contexts])
        else:
            enriched = base_contexts

        tasks = []
        for domain, context in zip(domains, enriched):
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

    def _classify_domain(self, implementer_domains: list[str]) -> str:
        """Determine testing domain from implementer domains."""
        has_frontend = any(d == "frontend" for d in implementer_domains)
        has_backend = any(d == "backend" for d in implementer_domains)
        if has_frontend and has_backend:
            return "fullstack"
        if has_frontend:
            return "frontend"
        return "backend"

    async def _run_test_attempt(
        self,
        domain: str,
        plan_content: str,
        design_brief: str | None,
        current_files: list[dict],
        session_id: str,
        attempt: int,
    ) -> tuple[bool, str, str | None]:
        """
        Run one test attempt with the appropriate tester(s).
        FULLSTACK: runs both testers in parallel, fails if either fails.
        Returns (passed, combined_content, fix_instructions).
        """
        if domain == "frontend":
            ctx, skills = self.ctx.for_ui_ux_tester(plan_content, design_brief, current_files, attempt)
            self._log("🎨 UI/UX Tester", f"Testing... (attempt {attempt + 1})")
            passed, content, fix = await self.ui_ux_tester.test(ctx, session_id, attempt, skills)
            return passed, content, fix

        if domain == "backend":
            ctx, skills = self.ctx.for_backend_tester(plan_content, current_files, attempt)
            self._log("🔧 Backend Tester", f"Testing... (attempt {attempt + 1})")
            passed, content, fix = await self.backend_tester.test(ctx, session_id, attempt, skills)
            return passed, content, fix

        # fullstack — run both in parallel
        self._log("🎨 UI/UX Tester + 🔧 Backend Tester", f"Testing in parallel... (attempt {attempt + 1})")
        fe_ctx, fe_skills = self.ctx.for_ui_ux_tester(plan_content, design_brief, current_files, attempt)
        be_ctx, be_skills = self.ctx.for_backend_tester(plan_content, current_files, attempt)

        (fe_passed, fe_content, fe_fix), (be_passed, be_content, be_fix) = await asyncio.gather(
            self.ui_ux_tester.test(fe_ctx, session_id, attempt, fe_skills),
            self.backend_tester.test(be_ctx, session_id, attempt, be_skills),
        )

        combined_content = f"## UI/UX Test\n{fe_content}\n\n## Backend Test\n{be_content}"
        combined_fix = "\n\n".join(f for f in [fe_fix, be_fix] if f) or None
        return fe_passed and be_passed, combined_content, combined_fix

    async def _test_loop(
        self,
        prompt: str,
        plan_content: str,
        design_brief: str | None,
        all_files: list[dict],
        impl_results: list[dict],
        session: Session,
        team: list[str],
        implementer_domains: list[str],
        domain: str = "backend",
    ) -> tuple[bool, str, str | None]:
        """
        Run the appropriate tester(s) in a loop until PASS or max retries.
        Routes: FRONTEND → ui_ux_tester | BACKEND → backend_tester | FULLSTACK → both.
        Returns (passed, test_content, walkthrough).
        """
        has_tester = any(t in team for t in ["ui_ux_tester", "backend_tester", "reviewer"])
        if not has_tester:
            return True, "Testing skipped (trivial task)", None

        current_files = list(all_files)
        test_content = ""
        passed = False

        for attempt in range(Config.MAX_REVIEW_RETRIES + 1):
            passed, test_content, fix_instructions = await self._run_test_attempt(
                domain=domain,
                plan_content=plan_content,
                design_brief=design_brief,
                current_files=current_files,
                session_id=session.session_id,
                attempt=attempt,
            )
            session.write_artifact(f"test_attempt_{attempt + 1}.md", test_content)

            if passed:
                self._log("✅ Tests", "PASS")
                session.mark_phase_complete("tester_pass")
                if self.stuck_detector:
                    self.stuck_detector.record_success("implementer")
                break
            else:
                self._log("❌ Tests", "FAIL — sending fix instructions to implementer")

                if self.stuck_detector and fix_instructions:
                    stuck_state = self.stuck_detector.record_error("implementer", fix_instructions)
                    if stuck_state.is_stuck:
                        self._log("🚨 Stuck", stuck_state.suggested_action)
                        session.write_artifact("stuck_report.md", self.stuck_detector.format_stuck_report("implementer"))
                        break

                if attempt >= Config.MAX_REVIEW_RETRIES:
                    self._log("⚠️  Warning", f"Max retries ({Config.MAX_REVIEW_RETRIES}) reached.")
                    break

                session.increment_iteration()
                issue_types = self._extract_issue_types(test_content)

                fix_results = await self._run_implementers(
                    prompt=prompt,
                    plan_content=plan_content,
                    design_brief=design_brief,
                    domains=implementer_domains,
                    session=session,
                    retry_count=attempt + 1,
                    fix_instructions=fix_instructions,
                    issue_types=issue_types,
                )
                current_files = []
                for r in fix_results:
                    current_files.extend(r.get("files", []))

        session.write_artifact("test_report.md", test_content)

        # Generate walkthrough on pass — use the appropriate tester
        walkthrough = None
        if passed:
            self._log("📝 Walkthrough", "Writing walkthrough...")
            tester = self.ui_ux_tester if domain in ("frontend", "fullstack") else self.backend_tester
            walkthrough = await tester.write_walkthrough(
                prompt=prompt,
                plan_content=plan_content,
                implementation_files=current_files,
                review_content=test_content,
                session_id=session.session_id,
            )

        return passed, test_content, walkthrough

    # ─────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────

    def _extract_issue_types(self, review_content: str) -> list[str]:
        """Extract issue types from review content for lesson lookup."""
        import re

        issue_patterns = {
            "typescript_any_type": [r"any\s+type", r"avoid any"],
            "missing_error_handling": [r"error handling", r"try.*catch"],
            "missing_loading_state": [r"loading state", r"isLoading"],
            "missing_validation": [r"validation", r"validate input"],
            "accessibility": [r"accessibility", r"aria-"],
            "security": [r"security", r"xss", r"injection"],
            "performance": [r"performance", r"memoize"],
            "missing_tests": [r"test.*missing", r"add.*test"],
        }

        review_lower = review_content.lower()
        found = []
        for issue_type, patterns in issue_patterns.items():
            for pattern in patterns:
                if re.search(pattern, review_lower):
                    found.append(issue_type)
                    break

        return found

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

    # ─────────────────────────────────────────────────────────────────
    # RAG Integration Methods
    # ─────────────────────────────────────────────────────────────────

    async def _get_historical_context(self, prompt: str) -> Optional[str]:
        """
        Query RAG for similar past sessions to provide context hints.

        Args:
            prompt: User's task prompt

        Returns:
            Formatted historical context string, or None if unavailable
        """
        if not self._rag_enabled() or self.rag is None:
            return None

        try:
            # Search for similar sessions
            similar = self.rag.search_sessions(
                query=prompt,
                n=getattr(Config, "MAX_SIMILAR_SESSIONS", 3),
                min_relevance=getattr(Config, "MIN_RELEVANCE_THRESHOLD", 0.5),
            )

            if not similar:
                return None

            # Format as hints for conductor
            hints = []
            for session in similar[:3]:
                outcome = session.get("outcome", "unknown")
                summary = session.get("summary", "")
                issues = session.get("issues", [])

                hint = f"- {outcome.upper()}: {summary[:100]}"
                if issues and isinstance(issues, list):
                    hint += f" (Issues: {', '.join(issues[:3])})"
                hints.append(hint)

            return "Similar past tasks:\n" + "\n".join(hints)

        except Exception as e:
            self._log("🧠 RAG", f"Historical context lookup failed: {e}")
            return None

    async def _post_pipeline_hooks(
        self,
        session: Session,
        passed: bool,
        retry_count: int,
    ):
        """
        Run post-pipeline hooks for session indexing and lesson extraction.

        Args:
            session: The completed session
            passed: Whether the review passed
            retry_count: Number of review retries that occurred
        """
        if not self._rag_enabled():
            return

        # Index the session
        if self.session_indexer:
            try:
                self._log("🧠 RAG", "Indexing session...")
                result = await self.session_indexer.index_session(session.session_dir)
                if result.get("status") == "ok":
                    self._log("🧠 RAG", "Session indexed successfully")
                else:
                    self._log("🧠 RAG", f"Session indexing failed: {result.get('error', 'unknown')}")
            except Exception as e:
                self._log("🧠 RAG", f"Session indexing error: {e}")

        # Extract lessons if retry succeeded (indicates learning opportunity)
        if passed and retry_count > 0 and self.lesson_extractor:
            try:
                if getattr(Config, "LESSON_EXTRACTION_ENABLED", True):
                    self._log("🧠 RAG", "Extracting lessons from successful retry...")
                    result = self.lesson_extractor.process_session(session.session_dir)
                    if result.get("status") == "ok":
                        self._log("🧠 RAG", f"Extracted {result.get('recorded', 0)} lesson(s)")

                        # Check for recurring patterns and auto-generate prompt patches
                        await self._detect_and_patch_patterns()
            except Exception as e:
                self._log("🧠 RAG", f"Lesson extraction error: {e}")

    async def _detect_and_patch_patterns(self):
        """
        Detect recurring patterns and auto-generate prompt patches.

        When the same issue type appears 3+ times, generate a patch file
        that can be injected into agent system prompts to prevent recurrence.
        """
        try:
            from src.rag import PatternDetector
            from src.config import AGENTS_DIR

            threshold = getattr(Config, "PATCH_GENERATION_THRESHOLD", 3)
            detector = PatternDetector(rag_client=self.rag)
            patterns = detector.find_recurring_patterns(min_occurrences=threshold)

            if not patterns:
                return

            patches_dir = AGENTS_DIR / "patches"
            patches_dir.mkdir(parents=True, exist_ok=True)

            for pattern in patterns:
                issue_type = pattern["issue_type"]
                patch_file = patches_dir / f"patch_{issue_type}.md"

                # Only generate if patch doesn't already exist
                if not patch_file.exists():
                    patch_content = detector.generate_patch_content(pattern)
                    patch_file.write_text(patch_content, encoding="utf-8")
                    self._log("🧠 RAG", f"Generated prompt patch: {issue_type} ({pattern['occurrences']} occurrences)")

        except Exception as e:
            self._log("🧠 RAG", f"Pattern detection error: {e}")

    def _update_project_index(self, all_files: list[dict], apply_results: list[dict]) -> None:
        """
        Append newly created files to project_index.md so future agents know they exist.
        Only processes CREATE operations that succeeded.
        """
        index_path = CONTEXT_DIR / "project_index.md"
        if not index_path.exists():
            return

        # Build lookup: path -> change_summary from original file operations
        summaries: dict[str, str] = {}
        for op in all_files:
            if op.get("operation", "").upper() == "CREATE":
                summaries[op.get("path", "")] = op.get("change_summary", "New file")

        # Find successfully created files not already in the index
        existing_content = index_path.read_text(encoding="utf-8")
        new_entries: list[str] = []

        for result in apply_results:
            if result.get("operation", "").upper() == "CREATE" and result.get("status") == "ok":
                rel_path = result.get("path", "")
                if rel_path and f"`{rel_path}`" not in existing_content:
                    summary = summaries.get(rel_path, "New file")
                    if len(summary) > 80:
                        summary = summary[:77] + "..."
                    new_entries.append(f"| `{rel_path}` | {summary} |")

        if not new_entries:
            return

        section_header = "## Recent Additions"
        if section_header in existing_content:
            # Append rows inside the existing section, before the next ##
            lines = existing_content.splitlines()
            insertion_idx = len(lines)
            in_section = False
            for i, line in enumerate(lines):
                if line.strip() == section_header:
                    in_section = True
                    continue
                if in_section and line.startswith("## "):
                    insertion_idx = i
                    break
            lines = lines[:insertion_idx] + new_entries + lines[insertion_idx:]
            index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        else:
            additions = "\n".join(new_entries)
            section = (
                f"\n{section_header}\n"
                f"| File | Purpose |\n"
                f"|------|---------|\n"
                f"{additions}\n"
            )
            with index_path.open("a", encoding="utf-8") as f:
                f.write(section)

        self._log("📋 Index", f"Updated project_index.md with {len(new_entries)} new file(s)")

    async def _process_agent_messages(self, agent) -> list:
        """
        Process and route messages from an agent's outbox.

        Args:
            agent: Agent instance with outbox

        Returns:
            List of responses received
        """
        if not hasattr(agent, "flush_outbox") or self.router is None:
            return []

        messages = agent.flush_outbox()
        if not messages:
            return []

        responses = []
        for message in messages:
            try:
                response = await self.router.route(message)
                if response:
                    responses.append(response)
            except Exception as e:
                self._log("📨 Router", f"Message routing error: {e}")

        return responses

    async def _inject_pending_messages(self, agent) -> str:
        """
        Get pending messages for an agent formatted for prompt injection.

        Args:
            agent: Agent to get messages for

        Returns:
            Formatted message string, or empty string
        """
        if self.router is None:
            return ""

        agent_name = getattr(agent, "name", "").lower()
        return self.router.format_pending_for_prompt(agent_name)
