"""
Context Builder — Assembles smart, token-efficient context packages for each agent.
Reads AGENTS.md, project index, and specific files — never the full codebase.
Supports RAG-based historical context injection for cross-session learning.
"""

from pathlib import Path
from typing import Optional
from src.config import BRAIN_ROOT, MONTRROASE_ROOT, AGENTS_DIR, CONTEXT_DIR, Config


class ContextBuilder:
    """
    Assembles lean context packages for each agent.
    Each package contains only what that agent needs to do its job.
    Supports historical context injection from RAG for cross-session learning.
    """

    def __init__(self):
        self._agents_md: str | None = None
        self._project_index: str | None = None
        self._design_system: str | None = None
        self._tech_stack: str | None = None

        # RAG components (lazy-loaded)
        self._retriever = None
        self._budget_enforcer = None

    # ─────────────────────────────────────────
    # Base context loaders (cached)
    # ─────────────────────────────────────────

    def agents_md(self) -> str:
        """Load AGENTS.md (the master project constitution)."""
        if self._agents_md is None:
            path = BRAIN_ROOT / "AGENTS.md"
            self._agents_md = path.read_text(encoding="utf-8") if path.exists() else ""
        return self._agents_md

    def project_index(self) -> str:
        """Load the project index (lightweight file lookup)."""
        if self._project_index is None:
            path = CONTEXT_DIR / "project_index.md"
            self._project_index = path.read_text(encoding="utf-8") if path.exists() else ""
        return self._project_index

    def design_system(self) -> str:
        """Load the design system reference (for Creative Brain only)."""
        if self._design_system is None:
            path = CONTEXT_DIR / "design_system.md"
            self._design_system = path.read_text(encoding="utf-8") if path.exists() else ""
        return self._design_system

    def tech_stack(self) -> str:
        """Load the tech stack reference (for Planner / Implementer)."""
        if self._tech_stack is None:
            path = CONTEXT_DIR / "tech_stack.md"
            self._tech_stack = path.read_text(encoding="utf-8") if path.exists() else ""
        return self._tech_stack

    # ─────────────────────────────────────────
    # File content loader
    # ─────────────────────────────────────────

    def read_file(self, relative_path: str) -> str:
        """
        Read a project file by path relative to Montrroase_website root.
        Returns empty string if file doesn't exist or is too large (>50KB).
        """
        full_path = MONTRROASE_ROOT / relative_path
        if not full_path.exists():
            return f"[FILE NOT FOUND: {relative_path}]"

        size = full_path.stat().st_size
        if size > 50_000:  # 50KB limit — very large files get truncated
            content = full_path.read_text(encoding="utf-8", errors="replace")
            return (
                f"[FILE TRUNCATED — {size//1000}KB > 50KB limit. Showing first 40KB]\n\n"
                + content[:40_000]
                + "\n\n[... truncated ...]"
            )

        return full_path.read_text(encoding="utf-8", errors="replace")

    def read_files(self, paths: list[str]) -> str:
        """Read multiple files and concatenate with clear separators."""
        parts = []
        for path in paths:
            content = self.read_file(path)
            parts.append(f"\n\n{'='*60}\n📄 FILE: {path}\n{'='*60}\n{content}")
        return "\n".join(parts)

    # ─────────────────────────────────────────
    # Context package builders
    # ─────────────────────────────────────────

    def for_conductor(self, prompt: str) -> str:
        """Context package for the Conductor (classification only)."""
        return (
            f"# User Request\n{prompt}\n\n"
            f"# Project Constitution\n{self.agents_md()}\n\n"
            f"# File Index\n{self.project_index()}"
        )

    def for_planner(self, prompt: str, classification: dict) -> str:
        """Context package for the Planner agent."""
        domain_tags = classification.get("classification", [])
        needs_backend = any(t in domain_tags for t in ["BACKEND", "FULLSTACK", "DATABASE"])
        needs_frontend = any(t in domain_tags for t in ["FRONTEND", "FULLSTACK", "DESIGN"])

        sections = [
            f"# Task to Plan\n{prompt}",
            f"# Project Constitution\n{self.agents_md()}",
            f"# File Index\n{self.project_index()}",
        ]

        if needs_backend or needs_frontend:
            sections.append(f"# Tech Stack Reference\n{self.tech_stack()}")

        return "\n\n---\n\n".join(sections)

    def for_creative_brain(self, prompt: str, plan_content: str) -> str:
        """Context package for the Creative Brain agent (design specialist)."""
        return (
            f"# Task\n{prompt}\n\n"
            f"---\n\n"
            f"# Plan (from Planner)\n{plan_content}\n\n"
            f"---\n\n"
            f"# Montrroase Design System\n{self.design_system()}\n\n"
            f"---\n\n"
            f"# Project Context\n{self.agents_md()}"
        )

    def for_implementer(
        self,
        prompt: str,
        plan_content: str,
        design_brief: str | None,
        file_paths_to_read: list[str],
        domain: str = "frontend",
    ) -> str:
        """
        Context package for an Implementer agent.
        Reads only the specific files listed in the plan.
        """
        file_contents = self.read_files(file_paths_to_read) if file_paths_to_read else ""

        sections = [
            f"# Task\n{prompt}",
            f"# Architecture Rules (MUST follow)\n{self.agents_md()}",
            f"# Implementation Plan\n{plan_content}",
        ]

        if design_brief:
            sections.append(f"# Design Brief\n{design_brief}")

        if file_contents:
            sections.append(f"# Relevant File Contents\n{file_contents}")

        # Inject domain-specific instruction
        domain_instruction = {
            "frontend": "You are implementing the FRONTEND (TypeScript/React/Next.js) portion.",
            "backend": "You are implementing the BACKEND (Python/Django/DRF) portion.",
            "fullstack": "You are implementing BOTH frontend and backend portions.",
        }.get(domain, "")

        if domain_instruction:
            sections.insert(1, f"# Your Domain\n{domain_instruction}")

        return "\n\n---\n\n".join(sections)

    def load_skill(self, skill_name: str) -> str:
        """Load a skill file from _vibecoding_brain/agents/skills/."""
        skill_path = AGENTS_DIR / "skills" / f"{skill_name}.md"
        return skill_path.read_text(encoding="utf-8") if skill_path.exists() else ""

    def _format_impl_files(self, implementation_files: list[dict]) -> str:
        """Format implementation files for tester/reviewer context."""
        return "\n".join(
            f"\n{'='*60}\n"
            f"📄 {f['operation']}: {f['path']}\n"
            f"{'='*60}\n"
            f"Summary: {f.get('change_summary', 'No summary')}\n\n"
            f"{f.get('content', '[DELETED]')}"
            for f in implementation_files
        )

    def for_ui_ux_tester(
        self,
        plan_content: str,
        design_brief: str | None,
        implementation_files: list[dict],
        retry_count: int = 0,
    ) -> tuple[str, str]:
        """
        Context package + injected skills for the UI/UX Tester agent.

        Returns:
            (context_package, extra_system) where extra_system contains skills to inject.
        """
        impl_section = self._format_impl_files(implementation_files)

        sections = [
            f"# Implementation to Test\n{impl_section}",
            f"# Original Plan (Acceptance Criteria)\n{plan_content}",
            f"# Project Rules (AGENTS.md)\n{self.agents_md()}",
        ]

        if design_brief:
            sections.append(f"# Design Brief (Visual Spec)\n{design_brief}")

        if retry_count > 0:
            sections.insert(
                0,
                f"# Context\nThis is test attempt #{retry_count + 1}. "
                f"Focus on whether the CRITICAL issues from your last report are now resolved.",
            )

        context = "\n\n---\n\n".join(sections)

        # Build skills string — web_accessibility always; playwright if server configured
        skills = [self.load_skill("web_accessibility")]
        if Config.PLAYWRIGHT_SERVER_URL:
            playwright_skill = self.load_skill("playwright_testing").replace(
                "{PLAYWRIGHT_SERVER_URL}", Config.PLAYWRIGHT_SERVER_URL
            )
            skills.append(playwright_skill)

        extra_system = "\n\n---\n\n".join(s for s in skills if s)
        return context, extra_system

    def for_backend_tester(
        self,
        plan_content: str,
        implementation_files: list[dict],
        retry_count: int = 0,
    ) -> tuple[str, str]:
        """
        Context package + injected skills for the Backend Tester agent.

        Returns:
            (context_package, extra_system) where extra_system contains skills to inject.
        """
        impl_section = self._format_impl_files(implementation_files)

        sections = [
            f"# Implementation to Test\n{impl_section}",
            f"# Original Plan (Acceptance Criteria)\n{plan_content}",
            f"# Project Rules (AGENTS.md)\n{self.agents_md()}",
        ]

        if retry_count > 0:
            sections.insert(
                0,
                f"# Context\nThis is test attempt #{retry_count + 1}. "
                f"Focus on whether the CRITICAL issues from your last report are now resolved.",
            )

        context = "\n\n---\n\n".join(sections)
        extra_system = self.load_skill("code_review")
        return context, extra_system

    def for_reviewer(
        self,
        plan_content: str,
        design_brief: str | None,
        implementation_files: list[dict],
        retry_count: int = 0,
    ) -> str:
        """
        Legacy context package for the Reviewer agent (kept for API mode compatibility).
        Prefer for_ui_ux_tester() / for_backend_tester() in new code.
        """
        impl_section = self._format_impl_files(implementation_files)

        sections = [
            f"# Implementation to Review\n{impl_section}",
            f"# Original Plan (Acceptance Criteria)\n{plan_content}",
            f"# Project Rules (AGENTS.md)\n{self.agents_md()}",
        ]

        if design_brief:
            sections.append(f"# Design Brief (Visual Spec)\n{design_brief}")

        if retry_count > 0:
            sections.insert(
                0,
                f"# Context\nThis is review attempt #{retry_count + 1}. "
                f"The implementer has already attempted to fix issues from previous reviews.\n"
                f"Focus on whether the CRITICAL issues from your last review are now resolved.",
            )

        return "\n\n---\n\n".join(sections)

    # ─────────────────────────────────────────
    # File path extraction from plan
    # ─────────────────────────────────────────

    def extract_file_paths_from_plan(self, plan_content: str, section: str = "READ") -> list[str]:
        """
        Extract file paths from plan.md under a given section.
        Looks for backtick-quoted paths in the specified section.
        """
        import re

        # Find the relevant section
        section_pattern = rf"### Files to {section}(.*?)(?=###|##|\Z)"
        section_match = re.search(section_pattern, plan_content, re.DOTALL | re.IGNORECASE)

        if not section_match:
            return []

        # Extract backtick-quoted paths
        paths = re.findall(r"`([^`]+\.[a-zA-Z]{1,6})`", section_match.group(1))
        return paths

    # ─────────────────────────────────────────────────────────────────
    # RAG-based Historical Context
    # ─────────────────────────────────────────────────────────────────

    @property
    def retriever(self):
        """Lazy-load ProgressiveRetriever."""
        if self._retriever is None and self._rag_enabled():
            try:
                from src.rag import ProgressiveRetriever
                self._retriever = ProgressiveRetriever()
            except ImportError:
                pass
        return self._retriever

    @property
    def budget_enforcer(self):
        """Lazy-load BudgetEnforcer."""
        if self._budget_enforcer is None and self._rag_enabled():
            try:
                from src.rag import BudgetEnforcer
                self._budget_enforcer = BudgetEnforcer()
            except ImportError:
                pass
        return self._budget_enforcer

    def _rag_enabled(self) -> bool:
        """Check if RAG is enabled in configuration."""
        return getattr(Config, "ENABLE_HISTORICAL_CONTEXT", False)

    async def with_historical_context(
        self,
        prompt: str,
        base_context: str,
        agent_type: str,
    ) -> str:
        """
        Enhance base context with relevant historical context from RAG.

        Args:
            prompt: The user's task prompt (used for similarity search)
            base_context: The base context package for the agent
            agent_type: Type of agent (planner, implementer, etc.)

        Returns:
            Enhanced context with historical information, or base_context if RAG unavailable
        """
        if not self._rag_enabled() or self.retriever is None:
            return base_context

        try:
            # Retrieve relevant historical context
            retrieved = self.retriever.get_context(
                query=prompt,
                agent_type=agent_type,
                include_lessons=True,
            )

            # Format for context injection
            historical_section = self.retriever.format_for_context(retrieved, agent_type)

            if not historical_section:
                return base_context

            # Inject historical context at appropriate location
            return self._inject_historical_section(base_context, historical_section, agent_type)

        except Exception:
            # Graceful degradation - return base context if RAG fails
            return base_context

    async def with_lesson_injections(
        self,
        context: str,
        issue_types: list[str],
        agent_type: str,
    ) -> str:
        """
        Inject relevant lessons for specific issue types into context.

        Useful when reviewer finds issues - inject lessons about how
        to fix those specific issue types.

        Args:
            context: Current context to enhance
            issue_types: List of issue types to find lessons for
            agent_type: Agent type for budget enforcement

        Returns:
            Context enhanced with relevant lessons
        """
        if not self._rag_enabled() or self.retriever is None:
            return context

        if not issue_types:
            return context

        try:
            from src.rag import get_rag_client

            rag = get_rag_client()
            lessons_parts = []

            for issue_type in issue_types[:3]:  # Limit to 3 issue types
                lessons = rag.search_lessons(issue_type, n=2)
                for lesson in lessons:
                    fix = lesson.get("fix", "")
                    if fix:
                        lessons_parts.append(f"- **{issue_type}**: {fix}")

            if not lessons_parts:
                return context

            # Apply budget enforcement
            lessons_section = "\n".join(lessons_parts)
            if self.budget_enforcer:
                lessons_section = self.budget_enforcer.enforce(agent_type, lessons_section)

            # Inject lessons section
            lessons_md = f"\n\n## Relevant Lessons from Past Tasks\n{lessons_section}"
            return context + lessons_md

        except Exception:
            return context

    def _inject_historical_section(
        self,
        base_context: str,
        historical_section: str,
        agent_type: str,
    ) -> str:
        """
        Inject historical section at appropriate location in context.

        Places historical context after the main task description
        but before detailed instructions.
        """
        # Look for a good injection point (after "# Task" or "# User Request")
        injection_markers = [
            "# Task\n",
            "# User Request\n",
            "---\n",
        ]

        for marker in injection_markers:
            if marker in base_context:
                # Find end of first section after marker
                marker_pos = base_context.find(marker)
                next_section = base_context.find("\n#", marker_pos + len(marker))

                if next_section != -1:
                    # Inject before next section
                    return (
                        base_context[:next_section] +
                        f"\n\n## Historical Context\n{historical_section}\n" +
                        base_context[next_section:]
                    )

        # Fallback: append at end
        return base_context + f"\n\n## Historical Context\n{historical_section}"
