import unittest
import json
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch

from scripts.assess_repository import assess_J
from scripts.create_issues_from_assessment import process_findings
from scripts.finalize_comprehensive_assessment import main as finalize_assessment
from scripts import maintain_workflows
from scripts.generate_assessment_summary import extract_score_from_report


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

    @patch("scripts.create_issues_from_assessment.get_existing_issues", return_value=[])
    @patch("scripts.create_issues_from_assessment.create_issue", return_value=True)
    def test_process_findings_uses_issues_schema_and_processes_all(
        self, mock_create_issue, _mock_existing
    ):
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            summary = tmp_path / "summary.json"
            output_file = tmp_path / "issues.md"

            issues = [
                {
                    "severity": "MAJOR",
                    "description": f"Finding {i}",
                    "source": "Assessment_J_API_Design",
                }
                for i in range(25)
            ]
            summary.write_text(json.dumps({"issues": issues}), encoding="utf-8")

            result = process_findings(summary, ["ALL"], False, True, output_file)

            self.assertEqual(result, 0)
            self.assertEqual(mock_create_issue.call_count, 25)
            self.assertTrue(output_file.exists())
            contents = output_file.read_text(encoding="utf-8")
            self.assertIn("Assessment Issue Staging Report", contents)
            self.assertIn("Finding 24", contents)

    def test_finalize_assessment_uses_current_pragmatic_json(self):
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            summary = tmp_path / "assessment_summary.json"
            review_json = tmp_path / "review.json"
            completist = tmp_path / "COMPLETIST_LATEST.md"
            output_md = tmp_path / "Comprehensive_Assessment.md"

            summary.write_text(
                json.dumps(
                    {
                        "overall_score": 8.0,
                        "category_scores": {"A": {"name": "Code Structure", "score": 8.0}},
                    }
                ),
                encoding="utf-8",
            )
            review_json.write_text(
                json.dumps(
                    {
                        "issues": [
                            {
                                "principle": "DRY",
                                "severity": "MAJOR",
                                "title": "Duplicate code block",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            completist.write_text("**Critical Gaps**: 3\n", encoding="utf-8")

            with patch(
                "scripts.finalize_comprehensive_assessment.SUMMARY_JSON", summary
            ), patch(
                "scripts.finalize_comprehensive_assessment.PRAGMATIC_REPORT",
                review_json,
            ), patch(
                "scripts.finalize_comprehensive_assessment.COMPLETIST_REPORT",
                completist,
            ), patch(
                "scripts.finalize_comprehensive_assessment.OUTPUT_MD", output_md
            ):
                self.assertEqual(finalize_assessment(), 0)

            report = output_md.read_text(encoding="utf-8")
            self.assertIn("Pragmatic Programmer Review", report)
            self.assertIn("Duplicate code block", report)

    def test_maintain_workflows_fails_loudly(self):
        self.assertEqual(maintain_workflows.main(), 1)
        with self.assertRaises(NotImplementedError):
            maintain_workflows.refactor_workflow("dummy.yml")


if __name__ == "__main__":
    unittest.main()
