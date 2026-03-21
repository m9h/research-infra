"""Tests for Beamer slide assembly."""

from pathlib import Path

from research_infra.slides import _assemble_slides_md, _extract_first_figure, build_slides
from research_infra.discover import discover_and_sort, load_project_config
from research_infra.schemas import Category


class TestExtractFirstFigure:
    def test_finds_figure(self):
        body = "Some text\n![My plot](figures/plot.png)\nMore text"
        assert _extract_first_figure(body) == "![My plot](figures/plot.png)"

    def test_no_figure(self):
        assert _extract_first_figure("No images here.") is None

    def test_multiple_figures_returns_first(self):
        body = "![A](a.png)\n![B](b.png)"
        assert _extract_first_figure(body) == "![A](a.png)"


class TestAssembleSlidesMd:
    def test_produces_beamer_yaml(self, tmp_project: Path):
        config = load_project_config(tmp_project)
        all_files = discover_and_sort(tmp_project, category=Category.research, config=config)
        files = [f for f in all_files if f.frontmatter.slide_summary]
        md = _assemble_slides_md(files, config)
        assert "title:" in md
        assert "theme:" in md
        assert "Test Author" in md

    def test_slide_summaries_included(self, tmp_project: Path):
        config = load_project_config(tmp_project)
        all_files = discover_and_sort(tmp_project, category=Category.research, config=config)
        files = [f for f in all_files if f.frontmatter.slide_summary]
        md = _assemble_slides_md(files, config)
        assert "novel approach" in md
        assert "JAX-based" in md
        assert "95% accuracy" in md

    def test_figure_extracted(self, tmp_project: Path):
        config = load_project_config(tmp_project)
        all_files = discover_and_sort(tmp_project, category=Category.research, config=config)
        files = [f for f in all_files if f.frontmatter.slide_summary]
        md = _assemble_slides_md(files, config)
        assert "figures/results.png" in md


class TestBuildSlides:
    def test_dry_run(self, tmp_project: Path, capsys):
        result = build_slides(tmp_project, dry_run=True)
        assert result is None
        captured = capsys.readouterr()
        assert "intro.md" in captured.out
        assert "novel approach" in captured.out

    def test_writes_slides_md(self, tmp_project: Path):
        result = build_slides(tmp_project)
        slides_md = tmp_project / "manuscript" / "output" / "slides.md"
        assert slides_md.exists()
        content = slides_md.read_text()
        assert "theme:" in content

    def test_no_summaries_message(self, tmp_path: Path, capsys):
        # Project with tagged files but no slide_summary.
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        import yaml
        config = {
            "project": {"name": "no-slides", "title": "No Slides", "short_title": "ns"},
            "authors": [],
            "scan_paths": ["."],
            "exclude_paths": [".git"],
            "output_dir": "manuscript/output",
        }
        with open(manuscript_dir / "config.yaml", "w") as f:
            yaml.dump(config, f)
        (tmp_path / "note.md").write_text(
            "---\ncategory: research\nsection: results\n---\nNo summary.\n"
        )
        result = build_slides(tmp_path)
        assert result is None
        captured = capsys.readouterr()
        assert "No research .md files with slide_summary" in captured.out
