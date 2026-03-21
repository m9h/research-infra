"""Tests for validate module."""

from pathlib import Path

from research_infra.validate import check_frontmatter, check_no_mock


class TestCheckNoMock:
    def test_clean_tests_pass(self, tmp_project: Path):
        violations = check_no_mock(tmp_project / "tests")
        assert violations == []

    def test_mock_usage_detected(self, tmp_project_with_mocks: Path):
        violations = check_no_mock(tmp_project_with_mocks / "tests")
        assert len(violations) > 0
        assert any("MagicMock" in v for v in violations)

    def test_comments_ignored(self, tmp_project: Path):
        (tmp_project / "tests" / "test_commented.py").write_text(
            "# Note: we don't use MagicMock here\n"
            "def test_ok():\n"
            "    assert True\n"
        )
        violations = check_no_mock(tmp_project / "tests")
        assert violations == []

    def test_nonexistent_dir(self, tmp_path: Path):
        violations = check_no_mock(tmp_path / "nonexistent")
        assert violations == []


class TestCheckFrontmatter:
    def test_valid_frontmatter_passes(self, tmp_project: Path):
        errors = check_frontmatter(tmp_project)
        assert errors == []

    def test_invalid_frontmatter_detected(self, tmp_project: Path):
        (tmp_project / "bad.md").write_text(
            "---\ncategory: research\nsection: INVALID\n---\nBad section.\n"
        )
        errors = check_frontmatter(tmp_project)
        assert len(errors) == 1
        assert "bad.md" in errors[0]

    def test_no_frontmatter_skipped(self, tmp_project: Path):
        # README.md has no frontmatter — should not produce errors.
        errors = check_frontmatter(tmp_project)
        assert errors == []
