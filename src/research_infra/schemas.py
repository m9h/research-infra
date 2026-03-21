"""Pydantic models for frontmatter and project configuration."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class Category(str, Enum):
    research = "research"
    infrastructure = "infrastructure"
    pedagogy = "pedagogy"


class Section(str, Enum):
    abstract = "abstract"
    introduction = "introduction"
    background = "background"
    methodology = "methodology"
    results = "results"
    discussion = "discussion"
    conclusion = "conclusion"
    appendix = "appendix"
    supplementary = "supplementary"


# Canonical ordering for sections in assembled output.
SECTION_ORDER: dict[Section, int] = {
    Section.abstract: 0,
    Section.introduction: 1,
    Section.background: 2,
    Section.methodology: 3,
    Section.results: 4,
    Section.discussion: 5,
    Section.conclusion: 6,
    Section.appendix: 7,
    Section.supplementary: 8,
}


class MdFrontmatter(BaseModel):
    """YAML frontmatter for a .md file participating in manuscript assembly."""

    category: Category
    section: Section
    weight: int = Field(default=50, ge=0, le=999)
    slide_summary: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    date: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    status: str = "draft"
    exclude: bool = False


class AuthorConfig(BaseModel):
    name: str
    affiliation: str = ""
    email: str = ""
    orcid: str = ""


class ProjectIdentity(BaseModel):
    name: str
    title: str
    short_title: str = ""


class ProjectConfig(BaseModel):
    """Schema for manuscript/config.yaml in each repo."""

    project: ProjectIdentity
    authors: list[AuthorConfig]
    date: str = ""
    version: str = "0.1.0"
    abstract_source: str = "auto"
    abstract: str = ""
    abstract_file: str = ""
    keywords: list[str] = Field(default_factory=list)
    doi: str = ""
    journal: str = ""
    arxiv_id: str = ""
    exclude_drafts: bool = False
    bibliography: str = "references.bib"
    csl: str = ""
    latex_template: str = ""
    beamer_template: str = ""
    beamer_theme: str = "metropolis"
    beamer_colortheme: str = ""
    scan_paths: list[str] = Field(default_factory=lambda: ["."])
    exclude_paths: list[str] = Field(
        default_factory=lambda: [
            ".git",
            ".venv",
            "node_modules",
            "__pycache__",
            "manuscript/output",
            ".github",
        ]
    )
    output_dir: str = "manuscript/output"


class DiscoveredFile(BaseModel):
    """A .md file discovered with valid frontmatter."""

    path: Path
    frontmatter: MdFrontmatter
    body: str

    model_config = {"arbitrary_types_allowed": True}
