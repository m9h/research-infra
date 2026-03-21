"""Tests for discover module."""

from pathlib import Path

from research_infra.discover import (
    discover_and_sort,
    discover_md_files,
    filter_files,
    load_project_config,
    sort_files,
)
from research_infra.schemas import Category, Section


class TestLoadProjectConfig:
    def test_loads_valid_config(self, tmp_project: Path):
        config = load_project_config(tmp_project)
        assert config.project.name == "test-project"
        assert config.project.title == "Test Project Title"
        assert len(config.authors) == 1

    def test_missing_config_raises(self, tmp_path: Path):
        import pytest

        with pytest.raises(FileNotFoundError, match="manuscript/config.yaml"):
            load_project_config(tmp_path)


class TestDiscoverMdFiles:
    def test_finds_tagged_files(self, tmp_project: Path):
        files = discover_md_files(tmp_project)
        # Should find intro.md, methods.md, results.md, dev_notes.md
        # Should NOT find README.md (no category in frontmatter)
        assert len(files) == 4
        names = {f.path.name for f in files}
        assert "intro.md" in names
        assert "methods.md" in names
        assert "results.md" in names
        assert "dev_notes.md" in names
        assert "README.md" not in names

    def test_skips_excluded_dirs(self, tmp_project: Path):
        # Create a file in an excluded directory.
        venv_dir = tmp_project / ".venv"
        venv_dir.mkdir()
        (venv_dir / "hidden.md").write_text(
            "---\ncategory: research\nsection: appendix\n---\nHidden.\n"
        )
        files = discover_md_files(tmp_project)
        names = {f.path.name for f in files}
        assert "hidden.md" not in names


class TestFilterFiles:
    def test_filter_by_category(self, tmp_project: Path):
        files = discover_md_files(tmp_project)
        research = filter_files(files, category=Category.research)
        assert len(research) == 3
        assert all(f.frontmatter.category == Category.research for f in research)

    def test_filter_by_section(self, tmp_project: Path):
        files = discover_md_files(tmp_project)
        results = filter_files(files, section=Section.results)
        assert len(results) == 1
        assert results[0].path.name == "results.md"

    def test_filter_excludes_excluded(self, tmp_project: Path):
        # Mark intro.md as excluded.
        (tmp_project / "excluded.md").write_text(
            "---\ncategory: research\nsection: introduction\nexclude: true\n---\nSkip me.\n"
        )
        files = discover_md_files(tmp_project)
        filtered = filter_files(files, category=Category.research)
        names = {f.path.name for f in filtered}
        assert "excluded.md" not in names

    def test_exclude_drafts(self, tmp_project: Path):
        files = discover_md_files(tmp_project)
        research = filter_files(files, category=Category.research, exclude_drafts=True)
        # Only results.md has status: final
        assert len(research) == 1
        assert research[0].path.name == "results.md"


class TestSortFiles:
    def test_sorts_by_section_then_weight(self, tmp_project: Path):
        files = discover_md_files(tmp_project)
        research = filter_files(files, category=Category.research)
        sorted_files = sort_files(research)
        sections = [f.frontmatter.section for f in sorted_files]
        assert sections == [Section.introduction, Section.methodology, Section.results]


class TestDiscoverAndSort:
    def test_combined(self, tmp_project: Path):
        files = discover_and_sort(tmp_project, category=Category.research)
        assert len(files) == 3
        assert files[0].path.name == "intro.md"
        assert files[1].path.name == "methods.md"
        assert files[2].path.name == "results.md"
