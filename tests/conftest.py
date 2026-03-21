"""Shared test fixtures for research-infra."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a minimal project structure for testing."""
    # manuscript/config.yaml
    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    (manuscript_dir / "output").mkdir()

    config = {
        "project": {
            "name": "test-project",
            "title": "Test Project Title",
            "short_title": "test",
        },
        "authors": [
            {"name": "Test Author", "affiliation": "Test Lab", "email": "test@example.com", "orcid": ""}
        ],
        "date": "2026-03-20",
        "version": "0.1.0",
        "abstract_source": "auto",
        "keywords": ["testing", "research-infra"],
        "exclude_drafts": False,
        "bibliography": "references.bib",
        "beamer_theme": "metropolis",
        "scan_paths": ["."],
        "exclude_paths": [".git", ".venv", "manuscript/output"],
        "output_dir": "manuscript/output",
    }
    with open(manuscript_dir / "config.yaml", "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    (manuscript_dir / "references.bib").write_text("% Test bibliography\n")

    # A .md file with valid frontmatter.
    (tmp_path / "intro.md").write_text(
        "---\n"
        "category: research\n"
        "section: introduction\n"
        "weight: 10\n"
        "title: Introduction\n"
        "status: draft\n"
        "slide_summary: This project introduces a novel approach.\n"
        "---\n\n"
        "# Introduction\n\n"
        "This is the introduction content.\n"
    )

    (tmp_path / "methods.md").write_text(
        "---\n"
        "category: research\n"
        "section: methodology\n"
        "weight: 20\n"
        "title: Methods\n"
        "status: draft\n"
        "slide_summary: We use JAX-based differentiable simulation.\n"
        "---\n\n"
        "## Simulation Setup\n\n"
        "We implement the algorithm in JAX.\n"
    )

    (tmp_path / "results.md").write_text(
        "---\n"
        "category: research\n"
        "section: results\n"
        "weight: 30\n"
        "title: Results\n"
        "status: final\n"
        "slide_summary: Our method achieves 95% accuracy on the benchmark.\n"
        "---\n\n"
        "## Benchmark Results\n\n"
        "| Model | Accuracy |\n"
        "|-------|----------|\n"
        "| Ours  | 95.0%    |\n"
        "| Baseline | 78.9% |\n\n"
        "![Results plot](figures/results.png)\n"
    )

    # A file without frontmatter (should be ignored).
    (tmp_path / "README.md").write_text("# Test Project\n\nA test project.\n")

    # An infrastructure file (should not appear in research filter).
    (tmp_path / "dev_notes.md").write_text(
        "---\n"
        "category: infrastructure\n"
        "section: appendix\n"
        "weight: 99\n"
        "---\n\n"
        "Dev notes here.\n"
    )

    # A pyproject.toml for scaffold tests.
    (tmp_path / "pyproject.toml").write_text(
        '[project]\n'
        'name = "test-project"\n'
        'version = "0.1.0"\n'
        'description = "A test project for research-infra"\n'
        'authors = [{name = "Test Author", email = "test@example.com"}]\n'
        'license = {text = "Apache-2.0"}\n'
        'requires-python = ">=3.11"\n'
        'dependencies = ["jax>=0.4.30"]\n'
        'keywords = ["testing"]\n'
        '\n'
        '[build-system]\n'
        'requires = ["hatchling"]\n'
        'build-backend = "hatchling.build"\n'
        '\n'
        '[tool.pytest.ini_options]\n'
        'testpaths = ["tests"]\n'
    )

    # Test directory with clean test file.
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_example.py").write_text(
        "def test_addition():\n"
        "    assert 1 + 1 == 2\n"
    )

    return tmp_path


@pytest.fixture
def tmp_project_with_mocks(tmp_project: Path) -> Path:
    """Project with mock usage in tests (for testing no-mock validation)."""
    test_file = tmp_project / "tests" / "test_bad.py"
    test_file.write_text(
        "from unittest.mock import MagicMock\n\n"
        "def test_bad():\n"
        "    m = MagicMock()\n"
        "    assert m is not None\n"
    )
    return tmp_project
