"""Walk a repository, parse YAML frontmatter from .md files, filter and sort."""

from __future__ import annotations

from pathlib import Path

import frontmatter
from pydantic import ValidationError

from .schemas import (
    Category,
    DiscoveredFile,
    MdFrontmatter,
    ProjectConfig,
    Section,
    SECTION_ORDER,
)


def load_project_config(project_root: Path) -> ProjectConfig:
    """Load and validate manuscript/config.yaml from a project root."""
    config_path = project_root / "manuscript" / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(
            f"No manuscript/config.yaml found at {config_path}. "
            f"Run 'rinf scaffold manuscript' to create one."
        )
    import yaml

    with open(config_path) as f:
        data = yaml.safe_load(f)
    return ProjectConfig(**data)


def discover_md_files(
    project_root: Path,
    config: ProjectConfig | None = None,
) -> list[DiscoveredFile]:
    """Walk project for .md files with valid frontmatter.

    Returns list of DiscoveredFile, unsorted. Files without frontmatter
    or with invalid frontmatter are silently skipped.
    """
    if config is None:
        config = load_project_config(project_root)

    exclude = set(config.exclude_paths)
    results: list[DiscoveredFile] = []

    scan_roots = [project_root / p for p in config.scan_paths]

    for scan_root in scan_roots:
        if not scan_root.exists():
            continue
        for md_path in scan_root.rglob("*.md"):
            # Skip excluded directories.
            rel = md_path.relative_to(project_root)
            if any(part in exclude for part in rel.parts):
                continue

            try:
                post = frontmatter.load(str(md_path))
            except Exception:
                continue

            if not post.metadata:
                continue

            # Must have at least 'category' to be considered.
            if "category" not in post.metadata:
                continue

            try:
                fm = MdFrontmatter(**post.metadata)
            except (ValidationError, ValueError):
                continue

            results.append(
                DiscoveredFile(
                    path=md_path,
                    frontmatter=fm,
                    body=post.content,
                )
            )

    return results


def filter_files(
    files: list[DiscoveredFile],
    *,
    category: Category | None = None,
    section: Section | None = None,
    exclude_drafts: bool = False,
) -> list[DiscoveredFile]:
    """Filter discovered files by category, section, and status."""
    out = []
    for f in files:
        if f.frontmatter.exclude:
            continue
        if category is not None and f.frontmatter.category != category:
            continue
        if section is not None and f.frontmatter.section != section:
            continue
        if exclude_drafts and f.frontmatter.status == "draft":
            continue
        out.append(f)
    return out


def sort_files(files: list[DiscoveredFile]) -> list[DiscoveredFile]:
    """Sort files by canonical section order, then weight, then filename."""
    return sorted(
        files,
        key=lambda f: (
            SECTION_ORDER.get(f.frontmatter.section, 99),
            f.frontmatter.weight,
            f.path.name,
        ),
    )


def discover_and_sort(
    project_root: Path,
    *,
    category: Category | None = None,
    section: Section | None = None,
    exclude_drafts: bool = False,
    config: ProjectConfig | None = None,
) -> list[DiscoveredFile]:
    """Discover, filter, and sort .md files in one call."""
    files = discover_md_files(project_root, config=config)
    files = filter_files(
        files, category=category, section=section, exclude_drafts=exclude_drafts
    )
    return sort_files(files)
