"""Tests for manuscript assembly."""

from pathlib import Path

from research_infra.manuscript import _assemble_combined_md, _demote_headings, build_manuscript
from research_infra.discover import discover_and_sort, load_project_config
from research_infra.schemas import Category


class TestDemoteHeadings:
    def test_single_hash(self):
        assert _demote_headings("# Title") == "## Title"

    def test_double_hash(self):
        assert _demote_headings("## Subtitle") == "### Subtitle"

    def test_multiline(self):
        text = "# First\nSome text\n## Second"
        result = _demote_headings(text)
        assert "## First" in result
        assert "### Second" in result

    def test_no_headings(self):
        text = "Just regular text."
        assert _demote_headings(text) == text


class TestAssembleCombinedMd:
    def test_produces_yaml_header(self, tmp_project: Path):
        config = load_project_config(tmp_project)
        files = discover_and_sort(tmp_project, category=Category.research, config=config)
        md = _assemble_combined_md(files, config)
        assert "title:" in md
        assert "Test Project Title" in md
        assert "Test Author" in md

    def test_sections_in_order(self, tmp_project: Path):
        config = load_project_config(tmp_project)
        files = discover_and_sort(tmp_project, category=Category.research, config=config)
        md = _assemble_combined_md(files, config)
        intro_pos = md.index("Introduction")
        methods_pos = md.index("Methodology")
        results_pos = md.index("Results")
        assert intro_pos < methods_pos < results_pos


class TestBuildManuscript:
    def test_dry_run(self, tmp_project: Path, capsys):
        result = build_manuscript(tmp_project, dry_run=True)
        assert result is None
        captured = capsys.readouterr()
        assert "intro.md" in captured.out
        assert "methods.md" in captured.out
        assert "results.md" in captured.out

    def test_writes_combined_md(self, tmp_project: Path):
        # Build will write combined.md even if pandoc is missing.
        result = build_manuscript(tmp_project)
        combined = tmp_project / "manuscript" / "output" / "combined.md"
        assert combined.exists()
        content = combined.read_text()
        assert "Test Project Title" in content
        assert "introduction" in content.lower()

    def test_no_files_message(self, tmp_path: Path, capsys):
        # Empty project with config but no tagged .md files.
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        import yaml
        config = {
            "project": {"name": "empty", "title": "Empty", "short_title": "empty"},
            "authors": [],
            "scan_paths": ["."],
            "exclude_paths": [".git"],
            "output_dir": "manuscript/output",
        }
        with open(manuscript_dir / "config.yaml", "w") as f:
            yaml.dump(config, f)
        result = build_manuscript(tmp_path)
        assert result is None
        captured = capsys.readouterr()
        assert "No research .md files found" in captured.out
