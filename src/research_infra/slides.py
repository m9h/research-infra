"""Assemble a Beamer slide deck from slide_summary fields in frontmatter."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

_KNOWN_BEAMER_THEMES = {"default", "AnnArbor", "Antibes", "Bergen", "Berkeley",
    "Berlin", "Boadilla", "CambridgeUS", "Copenhagen", "Darmstadt", "Dresden",
    "EastLansing", "Frankfurt", "Goettingen", "Hannover", "Ilmenau", "JuanLesPins",
    "Luebeck", "Madrid", "Malmoe", "Marburg", "Montpellier", "PaloAlto",
    "Pittsburgh", "Rochester", "Singapore", "Szeged", "Warsaw"}

import click

from .discover import discover_and_sort, load_project_config
from .schemas import Category, DiscoveredFile, ProjectConfig, Section, SECTION_ORDER


def _extract_first_figure(body: str) -> str | None:
    """Extract the first local markdown image reference from body text.

    Skips remote URLs (http/https) since XeLaTeX cannot fetch them.
    """
    for match in re.finditer(r"!\[([^\]]*)\]\(([^)]+)\)", body):
        alt, src = match.group(1), match.group(2)
        if not src.startswith(("http://", "https://")):
            return f"![{alt}]({src})"
    return None


def _section_title(section: Section) -> str:
    return section.value.replace("_", " ").title()


def _assemble_slides_md(
    files: list[DiscoveredFile],
    config: ProjectConfig,
) -> str:
    """Assemble sorted files into Beamer-ready markdown."""
    parts: list[str] = []

    # YAML metadata for pandoc beamer.
    author_lines = "\n".join(f"  - {a.name}" for a in config.authors)
    institute = config.authors[0].affiliation if config.authors and config.authors[0].affiliation else ""
    # Validate theme — fall back to default if not available.
    theme = config.beamer_theme
    if theme not in _KNOWN_BEAMER_THEMES:
        # Check if the theme .sty file exists.
        result = subprocess.run(
            ["kpsewhich", f"beamertheme{theme}.sty"],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            click.echo(f"Theme '{theme}' not found, falling back to 'default'.")
            theme = "default"

    meta = (
        "---\n"
        f"title: \"{config.project.title}\"\n"
        f"author:\n{author_lines}\n"
    )
    if institute:
        meta += f"institute: \"{institute}\"\n"
    meta += (
        f"date: \"{config.date}\"\n"
        f"theme: {theme}\n"
    )
    if config.beamer_colortheme:
        meta += f"colortheme: {config.beamer_colortheme}\n"
    meta += "---\n"
    parts.append(meta)

    # Group slides by section.
    current_section: Section | None = None
    for f in files:
        sec = f.frontmatter.section
        if sec != current_section:
            current_section = sec
            parts.append(f"\n# {_section_title(sec)}\n")

        # Frame title.
        title = f.frontmatter.title or f.path.stem.replace("_", " ").replace("-", " ").title()
        parts.append(f"\n## {title}\n")

        # Slide body from slide_summary.
        parts.append(f.frontmatter.slide_summary or "")

        # Include first figure if available.
        fig = _extract_first_figure(f.body)
        if fig:
            parts.append(f"\n{fig}\n")

        parts.append("")

    return "\n".join(parts)


def build_slides(
    project_root: Path,
    *,
    dry_run: bool = False,
) -> Path | None:
    """Build a Beamer slide deck PDF from slide_summary fields.

    Returns the output PDF path, or None if dry_run.
    """
    config = load_project_config(project_root)

    # Discover research files that have slide_summary.
    all_files = discover_and_sort(
        project_root,
        category=Category.research,
        config=config,
    )
    files = [f for f in all_files if f.frontmatter.slide_summary]

    if not files:
        click.echo(
            "No research .md files with slide_summary found.\n"
            "Add slide_summary to frontmatter to include content in slides."
        )
        return None

    if dry_run:
        click.echo(f"Slides for: {config.project.title}")
        click.echo(f"Frames ({len(files)}):\n")
        current_sec = None
        for f in files:
            sec = f.frontmatter.section
            if sec != current_sec:
                current_sec = sec
                click.echo(f"  [{_section_title(sec)}]")
            rel = f.path.relative_to(project_root)
            title = f.frontmatter.title or f.path.stem
            summary = f.frontmatter.slide_summary[:70] + "..." if len(f.frontmatter.slide_summary) > 70 else f.frontmatter.slide_summary
            click.echo(f"    {rel}  ({title})")
            click.echo(f"      -> {summary}")
        return None

    # Assemble.
    slides_md = _assemble_slides_md(files, config)

    output_dir = project_root / config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    slides_md_path = output_dir / "slides.md"
    slides_md_path.write_text(slides_md)
    click.echo(f"Wrote {slides_md_path}")

    if not shutil.which("pandoc"):
        click.echo(
            "WARNING: pandoc not found. Install with: sudo dnf install pandoc\n"
            "Slides markdown written but PDF not generated."
        )
        return slides_md_path

    pdf_name = f"{config.project.name}_slides.pdf"
    pdf_path = output_dir / pdf_name

    template_dir = Path(__file__).parent / "templates"
    beamer_template = template_dir / "beamer.latex"

    cmd = [
        "pandoc",
        str(slides_md_path),
        "--from", "markdown",
        "--to", "beamer",
        "--pdf-engine=xelatex",
        "--slide-level=2",
        "-V", "aspectratio=169",
        "-o", str(pdf_path),
    ]

    # Use custom template if user specified one in config.
    if config.beamer_template:
        custom = project_root / "manuscript" / config.beamer_template
        if custom.exists():
            cmd.extend(["--template", str(custom)])

    click.echo(f"Building slides: {pdf_path}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        click.echo(f"pandoc failed:\n{result.stderr}")
        raise SystemExit(1)

    click.echo(f"Wrote {pdf_path}")
    return pdf_path
