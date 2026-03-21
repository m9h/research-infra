"""Tests for schemas module."""

import pytest
from pydantic import ValidationError

from research_infra.schemas import (
    Category,
    DiscoveredFile,
    MdFrontmatter,
    ProjectConfig,
    ProjectIdentity,
    Section,
    SECTION_ORDER,
)


class TestMdFrontmatter:
    def test_minimal(self):
        fm = MdFrontmatter(category="research", section="results")
        assert fm.category == Category.research
        assert fm.section == Section.results
        assert fm.weight == 50
        assert fm.status == "draft"
        assert fm.exclude is False

    def test_full(self):
        fm = MdFrontmatter(
            category="research",
            section="methodology",
            weight=10,
            slide_summary="A brief summary.",
            title="Methods",
            status="final",
            tags=["jax", "benchmark"],
        )
        assert fm.slide_summary == "A brief summary."
        assert fm.tags == ["jax", "benchmark"]

    def test_invalid_category(self):
        with pytest.raises(ValidationError):
            MdFrontmatter(category="invalid", section="results")

    def test_invalid_section(self):
        with pytest.raises(ValidationError):
            MdFrontmatter(category="research", section="invalid")

    def test_weight_bounds(self):
        with pytest.raises(ValidationError):
            MdFrontmatter(category="research", section="results", weight=-1)
        with pytest.raises(ValidationError):
            MdFrontmatter(category="research", section="results", weight=1000)

    def test_pedagogy_category(self):
        fm = MdFrontmatter(category="pedagogy", section="introduction")
        assert fm.category == Category.pedagogy


class TestProjectConfig:
    def test_defaults(self):
        config = ProjectConfig(
            project=ProjectIdentity(name="test", title="Test"),
            authors=[],
        )
        assert config.exclude_drafts is False
        assert ".git" in config.exclude_paths
        assert config.beamer_theme == "metropolis"
        assert config.output_dir == "manuscript/output"


class TestSectionOrder:
    def test_all_sections_have_order(self):
        for sec in Section:
            assert sec in SECTION_ORDER

    def test_order_is_ascending(self):
        values = list(SECTION_ORDER.values())
        assert values == sorted(values)
