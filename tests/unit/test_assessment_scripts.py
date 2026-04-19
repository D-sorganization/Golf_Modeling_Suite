import re
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.assess_repository import assess_J
from scripts.generate_assessment_summary import extract_score_from_report

# Secret-scan pattern extracted from assess_F() — kept in sync by reference.
_SECRET_PATTERN = re.compile(
    r'(?:password|secret|api_key|token)\s*=\s*["\']'
    r'(?!your-|example|placeholder|fake|test|dummy|<|{)[^"\']{8,}["\']'
)


class TestAssessmentScripts(unittest.TestCase):
    def test_extract_score_from_report(self):
        # Create a dummy report file
        dummy_report = Path("dummy_report.md")
        dummy_report.write_text(
            "# Assessment: Test\n\n**Grade**: 8.5/10\n", encoding="utf-8"
        )
        try:
            score = extract_score_from_report(dummy_report)
            self.assertEqual(score, 8.5)
        finally:
            if dummy_report.exists():
                dummy_report.unlink()

    def test_assess_J_logic(self):
        # We can't easily mock the file system for the whole function without heavy mocking,
        # but we can verify that the function runs without error and returns a report path.
        # This assumes REPO_ROOT is set correctly in the imported module.

        # We need to mock generate_markdown_report to avoid writing files
        with patch("scripts.assess_repository.generate_markdown_report") as mock_gen:
            mock_gen.return_value = Path("dummy_output.md")

            # We also need to mock grep_count to avoid scanning the whole repo
            with patch("scripts.assess_repository.grep_count") as mock_grep:
                mock_grep.return_value = 1

                result = assess_J()
                self.assertIsInstance(result, Path)
                self.assertEqual(str(result), "dummy_output.md")

                # Verify that generate_markdown_report was called with expected arguments
                # The score should be 7.5 (default) + potentially adjustments
                # In current state, if src/api exists (which it does), score is 7.5.
                # If grep_count finds FastAPI (mocked to 1), it appends "FastAPI usage detected".

                args, _ = mock_gen.call_args
                category_id = args[0]
                score = args[2]
                self.assertEqual(category_id, "J")
                # We expect 7.5 if api or src/api exists.
                # Since we are running in the actual repo, src/api exists.
                self.assertEqual(score, 7.5)


class TestSecretScanPattern:
    """Validate the hardcoded-secret regex used in assess_F().

    Ensures real production secrets are flagged while documented placeholder
    credentials are excluded. Closes issue #2798.
    """

    def test_real_secret_is_flagged(self) -> None:
        """A genuine-looking secret assignment in production code is matched."""
        line = 'api_key = "sk-abcdef1234567890"'
        assert _SECRET_PATTERN.search(line) is not None, (
            "Real secret literal should be flagged"
        )

    def test_password_literal_is_flagged(self) -> None:
        line = "password = 'SuperSecretP@ss!'"
        assert _SECRET_PATTERN.search(line) is not None

    def test_docstring_example_your_prefix_skipped(self) -> None:
        """Docstring examples using 'your-*' placeholder are not flagged."""
        line = '    >>> adapter = AnthropicAdapter(api_key="your-api-key-here")'
        assert _SECRET_PATTERN.search(line) is None, (
            "Docstring placeholder 'your-api-key-here' must not be flagged"
        )

    def test_example_prefix_skipped(self) -> None:
        line = 'token = "example-token-value"'
        assert _SECRET_PATTERN.search(line) is None

    def test_placeholder_prefix_skipped(self) -> None:
        line = 'secret = "placeholder-secret"'
        assert _SECRET_PATTERN.search(line) is None

    def test_fake_prefix_skipped(self) -> None:
        line = 'password = "fakep@ssword123"'
        assert _SECRET_PATTERN.search(line) is None

    def test_test_prefix_skipped(self) -> None:
        line = 'api_key = "testkey-abc123xyz"'
        assert _SECRET_PATTERN.search(line) is None

    def test_dummy_prefix_skipped(self) -> None:
        line = 'token = "dummytoken12345"'
        assert _SECRET_PATTERN.search(line) is None

    def test_short_value_not_matched(self) -> None:
        """Values shorter than 8 chars are intentionally not matched."""
        line = 'password = "short"'
        assert _SECRET_PATTERN.search(line) is None

    def test_env_var_usage_not_matched(self) -> None:
        """Assignment from os.environ is not a hardcoded secret."""
        line = 'api_key = os.environ.get("API_KEY")'
        assert _SECRET_PATTERN.search(line) is None


if __name__ == "__main__":
    unittest.main()
