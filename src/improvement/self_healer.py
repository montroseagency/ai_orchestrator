"""
Self-Healing Loop — Run tests/lint after implementation, auto-fix failures.

Inspired by: LogicStar's self-healing software pattern and AgentCoder's
test-executor feedback loop. The key insight is that agents produce better
code when they can see their own errors immediately.

Flow:
1. After implementer produces files → run validation commands
2. Capture stdout/stderr from tests, lint, type-check
3. If failures → format errors as fix instructions → re-run implementer
4. Repeat until pass or max healing attempts exhausted
"""

import asyncio
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.config import Config


@dataclass
class ValidationResult:
    """Result of a single validation command."""
    command: str
    passed: bool
    stdout: str
    stderr: str
    return_code: int
    duration_ms: int


@dataclass
class HealingResult:
    """Result of the self-healing loop."""
    healed: bool
    attempts: int
    validations: list[ValidationResult] = field(default_factory=list)
    fix_instructions: list[str] = field(default_factory=list)
    total_duration_ms: int = 0


class SelfHealingLoop:
    """
    Runs validation commands after implementation and feeds errors
    back to the implementer for automatic fixing.

    Supports:
    - Test suites (pytest, jest, npm test)
    - Linters (eslint, flake8, ruff)
    - Type checkers (tsc, mypy, pyright)
    - Build verification (npm run build, python -m py_compile)
    """

    # Default validation commands by project type
    DEFAULT_VALIDATORS = {
        "python": [
            {"cmd": "python3 -m py_compile {file}", "name": "syntax", "blocking": True},
            {"cmd": "python3 -m ruff check {file}", "name": "lint", "blocking": False},
        ],
        "typescript": [
            {"cmd": "npx tsc --noEmit", "name": "typecheck", "blocking": True},
            {"cmd": "npx eslint {file}", "name": "lint", "blocking": False},
        ],
        "frontend": [
            {"cmd": "npm run build", "name": "build", "blocking": True},
            {"cmd": "npx eslint {file}", "name": "lint", "blocking": False},
        ],
        "backend": [
            {"cmd": "python3 -m py_compile {file}", "name": "syntax", "blocking": True},
            {"cmd": "python3 -m ruff check {file}", "name": "lint", "blocking": False},
        ],
    }

    # Max healing attempts before giving up
    MAX_HEALING_ATTEMPTS = 3

    def __init__(
        self,
        project_root: Optional[Path] = None,
        validators: Optional[list[dict]] = None,
        max_attempts: int = 3,
        timeout_per_command: int = 60,
    ):
        """
        Initialize the self-healing loop.

        Args:
            project_root: Root directory for running commands
            validators: Custom validation commands (overrides defaults)
            max_attempts: Max healing attempts before giving up
            timeout_per_command: Timeout per validation command in seconds
        """
        if project_root is None:
            from src.config import PROJECT_ROOT
            project_root = PROJECT_ROOT

        self.project_root = Path(project_root)
        self.custom_validators = validators
        self.max_attempts = max_attempts
        self.timeout = timeout_per_command

    def get_validators(self, domain: str, files: list[dict]) -> list[dict]:
        """
        Get validation commands appropriate for the domain and files.

        Args:
            domain: Implementation domain (frontend, backend, etc.)
            files: List of file dicts from implementer output

        Returns:
            List of validator config dicts
        """
        if self.custom_validators:
            return self.custom_validators

        # Determine project type from domain and files
        validators = []
        file_extensions = set()
        for f in files:
            path = f.get("path", "")
            if "." in path:
                ext = path.rsplit(".", 1)[-1].lower()
                file_extensions.add(ext)

        # Add validators based on file types
        if file_extensions & {"py"}:
            validators.extend(self.DEFAULT_VALIDATORS.get("python", []))

        if file_extensions & {"ts", "tsx", "js", "jsx"}:
            validators.extend(self.DEFAULT_VALIDATORS.get("typescript", []))

        # Add domain-specific validators
        domain_validators = self.DEFAULT_VALIDATORS.get(domain, [])
        for v in domain_validators:
            if v not in validators:
                validators.append(v)

        return validators

    def run_validation(
        self,
        command: str,
        file_path: Optional[str] = None,
    ) -> ValidationResult:
        """
        Run a single validation command.

        Args:
            command: Command template (may contain {file} placeholder)
            file_path: File path to substitute into {file} placeholder

        Returns:
            ValidationResult with pass/fail and output
        """
        # Substitute file path
        if file_path and "{file}" in command:
            command = command.replace("{file}", str(file_path))
        elif "{file}" in command:
            # No file specified, skip file-specific commands
            return ValidationResult(
                command=command,
                passed=True,
                stdout="",
                stderr="skipped (no file specified)",
                return_code=0,
                duration_ms=0,
            )

        start = time.time()

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(self.project_root),
            )

            duration_ms = int((time.time() - start) * 1000)

            return ValidationResult(
                command=command,
                passed=result.returncode == 0,
                stdout=result.stdout[-2000:] if result.stdout else "",  # Truncate
                stderr=result.stderr[-2000:] if result.stderr else "",
                return_code=result.returncode,
                duration_ms=duration_ms,
            )

        except subprocess.TimeoutExpired:
            duration_ms = int((time.time() - start) * 1000)
            return ValidationResult(
                command=command,
                passed=False,
                stdout="",
                stderr=f"Command timed out after {self.timeout}s",
                return_code=-1,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            return ValidationResult(
                command=command,
                passed=False,
                stdout="",
                stderr=str(e),
                return_code=-1,
                duration_ms=duration_ms,
            )

    def validate_files(
        self,
        files: list[dict],
        domain: str = "frontend",
    ) -> tuple[bool, list[ValidationResult]]:
        """
        Run all validators on implementation output.

        Args:
            files: List of file dicts from implementer
            domain: Implementation domain

        Returns:
            Tuple of (all_passed, list of ValidationResults)
        """
        validators = self.get_validators(domain, files)
        results = []
        all_passed = True

        for validator in validators:
            cmd = validator["cmd"]
            name = validator.get("name", cmd)
            blocking = validator.get("blocking", False)

            if "{file}" in cmd:
                # Run per-file
                for f in files:
                    file_path = f.get("path", "")
                    if not file_path:
                        continue

                    # Check file extension matches validator
                    full_path = self.project_root / file_path
                    result = self.run_validation(cmd, str(full_path))
                    results.append(result)

                    if not result.passed:
                        all_passed = False
                        if blocking:
                            return False, results
            else:
                # Run once (project-wide)
                result = self.run_validation(cmd)
                results.append(result)

                if not result.passed:
                    all_passed = False
                    if blocking:
                        return False, results

        return all_passed, results

    def format_errors_as_fix_instructions(
        self,
        results: list[ValidationResult],
    ) -> str:
        """
        Format validation failures as fix instructions for the implementer.

        Args:
            results: List of ValidationResults (only failures included)

        Returns:
            Formatted fix instructions string
        """
        failures = [r for r in results if not r.passed]
        if not failures:
            return ""

        parts = ["## Auto-Healing: Fix These Errors\n"]
        parts.append("The following validation checks failed. Fix ALL errors:\n")

        for i, failure in enumerate(failures, 1):
            parts.append(f"### Error {i}: `{failure.command}`")

            if failure.stderr:
                # Truncate to most relevant portion
                error_text = failure.stderr.strip()
                if len(error_text) > 500:
                    error_text = error_text[:500] + "\n... (truncated)"
                parts.append(f"```\n{error_text}\n```")

            if failure.stdout:
                stdout_text = failure.stdout.strip()
                if len(stdout_text) > 500:
                    stdout_text = stdout_text[:500] + "\n... (truncated)"
                parts.append(f"**Output:**\n```\n{stdout_text}\n```")

            parts.append("")

        parts.append("Fix all errors above. Do NOT introduce new issues.")
        return "\n".join(parts)

    async def heal(
        self,
        files: list[dict],
        domain: str,
        reimplementation_fn=None,
        log_fn=None,
    ) -> HealingResult:
        """
        Run the full self-healing loop.

        Args:
            files: Implementation output files
            domain: Implementation domain
            reimplementation_fn: Async function(fix_instructions) -> new_files
            log_fn: Optional logging function(phase, message)

        Returns:
            HealingResult with healing outcome
        """
        start_time = time.time()
        result = HealingResult(healed=False, attempts=0)
        current_files = files

        for attempt in range(self.max_attempts):
            result.attempts = attempt + 1

            if log_fn:
                log_fn("🔧 Self-Heal", f"Validation attempt {attempt + 1}/{self.max_attempts}")

            # Run validation
            all_passed, validations = self.validate_files(current_files, domain)
            result.validations.extend(validations)

            if all_passed:
                result.healed = True
                if log_fn:
                    log_fn("🔧 Self-Heal", "All validations passed ✓")
                break

            # Format errors as fix instructions
            fix_instructions = self.format_errors_as_fix_instructions(validations)
            result.fix_instructions.append(fix_instructions)

            if log_fn:
                failure_count = sum(1 for v in validations if not v.passed)
                log_fn("🔧 Self-Heal", f"{failure_count} validation(s) failed — sending fixes to implementer")

            # Re-implement with fix instructions
            if reimplementation_fn and attempt < self.max_attempts - 1:
                try:
                    new_files = await reimplementation_fn(fix_instructions)
                    if new_files:
                        current_files = new_files
                except Exception as e:
                    if log_fn:
                        log_fn("🔧 Self-Heal", f"Re-implementation failed: {e}")
                    break
            else:
                break

        result.total_duration_ms = int((time.time() - start_time) * 1000)
        return result
