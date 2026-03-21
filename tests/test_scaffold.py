"""Tests for scaffold module."""

from pathlib import Path

from research_infra.scaffold import (
    scaffold_agents_md,
    scaffold_all,
    scaffold_ci,
    scaffold_manuscript,
    scaffold_pre_commit,
)


class TestScaffoldAgentsMd:
    def test_creates_agents_md(self, tmp_project: Path):
        scaffold_agents_md(tmp_project)
        agents = tmp_project / "AGENTS.md"
        assert agents.exists()
        content = agents.read_text()
        assert "test-project" in content
        assert "A test project" in content
        assert "hatchling" in content

    def test_includes_dependencies(self, tmp_project: Path):
        scaffold_agents_md(tmp_project)
        content = (tmp_project / "AGENTS.md").read_text()
        assert "jax" in content


class TestScaffoldManuscript:
    def test_creates_config_and_bib(self, tmp_path: Path):
        # Need a pyproject.toml for metadata.
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "scaffold-test"\n'
            'version = "0.1.0"\ndescription = "Test"\n'
            'authors = [{name = "Author"}]\n'
            '\n[build-system]\nrequires = ["hatchling"]\n'
            'build-backend = "hatchling.build"\n'
        )
        scaffold_manuscript(tmp_path)
        assert (tmp_path / "manuscript" / "config.yaml").exists()
        assert (tmp_path / "manuscript" / "references.bib").exists()

    def test_skips_existing(self, tmp_project: Path):
        # config.yaml already exists from fixture.
        scaffold_manuscript(tmp_project)
        # Should not overwrite.


class TestScaffoldPreCommit:
    def test_creates_config(self, tmp_project: Path):
        # Remove existing if any.
        pc = tmp_project / ".pre-commit-config.yaml"
        if pc.exists():
            pc.unlink()
        scaffold_pre_commit(tmp_project)
        assert pc.exists()
        content = pc.read_text()
        assert "ruff" in content
        assert "no-mock" in content


class TestScaffoldCi:
    def test_creates_workflow(self, tmp_project: Path):
        scaffold_ci(tmp_project)
        ci = tmp_project / ".github" / "workflows" / "ci.yml"
        assert ci.exists()
        content = ci.read_text()
        assert "astral-sh/setup-uv" in content
        assert "pytest" in content


class TestScaffoldAll:
    def test_creates_everything(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "all-test"\nversion = "0.1.0"\n'
            'description = "Full scaffold test"\n'
            'authors = [{name = "Author"}]\ndependencies = []\n'
            '\n[build-system]\nrequires = ["hatchling"]\n'
            'build-backend = "hatchling.build"\n'
        )
        (tmp_path / "tests").mkdir()
        scaffold_all(tmp_path)
        assert (tmp_path / "AGENTS.md").exists()
        assert (tmp_path / "manuscript" / "config.yaml").exists()
        assert (tmp_path / ".pre-commit-config.yaml").exists()
        assert (tmp_path / ".github" / "workflows" / "ci.yml").exists()
