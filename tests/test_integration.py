"""Integration tests for the Vibe Coding Team."""

import pytest


class TestConfigValidation:
    """Test configuration validation."""

    def test_config_has_required_attributes(self):
        from src.config import Config
        assert hasattr(Config, "CLAUDE_CLI_PATH")
        assert hasattr(Config, "CLAUDE_CLI_EFFORT")
        assert hasattr(Config, "CLAUDE_CLI_MODEL")
        assert hasattr(Config, "MAX_REVIEW_RETRIES")
        assert hasattr(Config, "MAX_ITERATIONS")

    def test_config_defaults(self):
        from src.config import Config
        assert Config.CLAUDE_CLI_MODEL == "sonnet"
        assert Config.CLAUDE_CLI_EFFORT == "high"
        assert Config.MAX_REVIEW_RETRIES == 3
        assert Config.MAX_ITERATIONS == 8


class TestTeamRunnerParsing:
    """Test CliTeamRunner result parsing."""

    def test_parse_valid_json_result(self):
        from src.team_runner import CliTeamRunner
        runner = CliTeamRunner()

        raw = '''```json
{
  "session_id": "add-dark-mode",
  "status": "pass",
  "files_written": ["client/components/DarkMode.tsx"],
  "iterations": 2,
  "review_verdict": "PASS",
  "summary": "Added dark mode toggle."
}
```'''

        result = runner._parse_result(raw)
        assert result["session_id"] == "add-dark-mode"
        assert result["status"] == "pass"
        assert len(result["files_applied"]) == 1
        assert result["iterations"] == 2

    def test_parse_no_json_fallback(self):
        from src.team_runner import CliTeamRunner
        runner = CliTeamRunner()

        result = runner._parse_result("Just some text with no JSON")
        assert result["session_id"] == "unknown"
        assert result["status"] == "unknown"

    def test_parse_inline_json(self):
        from src.team_runner import CliTeamRunner
        runner = CliTeamRunner()

        raw = 'some prefix {"session_id": "test", "status": "pass", "files_written": []} some suffix'
        result = runner._parse_result(raw)
        assert result["session_id"] == "test"
        assert result["status"] == "pass"
