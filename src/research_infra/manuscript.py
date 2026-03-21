"""Assemble a research manuscript from frontmatter-tagged .md files."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import click

from .discover import discover_and_sort, load_project_config
from .schemas import Category, DiscoveredFile, ProjectConfig, Section, SECTION_ORDER


def _demote_headings(body: str) -> str:
    """Demote all markdown headings by one level (# -> ##, ## -> ###, etc.)."""
    return re.sub(r"^(#+)", r"#\1", body, flags=re.MULTILINE)


def _strip_remote_images(body: str) -> str:
    """Remove markdown image references to remote URLs (http/https).

    XeLaTeX cannot fetch remote images, so we replace them with a text note.
    Local file references are kept.
    """
    return re.sub(
        r"!\[([^\]]*)\]\((https?://[^)]+)\)",
        r"[\1](\2)",  # Convert to plain link.
        body,
    )


def _section_title(section: Section) -> str:
    """Human-readable section title."""
    return section.value.replace("_", " ").title()


def _assemble_combined_md(
    files: list[DiscoveredFile],
    config: ProjectConfig,
) -> str:
    """Assemble sorted files into a single markdown document."""
    parts: list[str] = []

    # YAML metadata block for pandoc.
    author_lines = "\n".join(f"  - {a.name}" for a in config.authors)
    meta = (
        "---\n"
        f"title: \"{config.project.title}\"\n"
        f"author:\n{author_lines}\n"
        f"date: \"{config.date}\"\n"
    )
    if config.keywords:
        kw = ", ".join(config.keywords)
        meta += f"keywords: [{kw}]\n"
    meta += "---\n"
    parts.append(meta)

    # Group files by section.
    current_section: Section | None = None
    for f in files:
        sec = f.frontmatter.section
        if sec != current_section:
            current_section = sec
            if sec != Section.abstract:
                parts.append(f"\n# {_section_title(sec)}\n")

        body = f.body.strip()
        body = _strip_remote_images(body)
        if body.startswith("# "):
            body = _demote_headings(body)

        title = f.frontmatter.title
        if title and sec != Section.abstract:
            parts.append(f"\n## {title}\n")

        parts.append(body)
        parts.append("")  # Blank line separator.

    return "\n".join(parts)


def build_manuscript(
    project_root: Path,
    *,
    dry_run: bool = False,
    exclude_drafts: bool = False,
) -> Path | None:
    """Build a manuscript PDF from frontmatter-tagged .md files.

    Returns the output PDF path, or None if dry_run.
    """
    config = load_project_config(project_root)
    files = discover_and_sort(
        project_root,
        category=Category.research,
        exclude_drafts=exclude_drafts,
        config=config,
    )

    if not files:
        click.echo("No research .md files found. Tag files with frontmatter to include them.")
        return None

    if dry_run:
        click.echo(f"Manuscript for: {config.project.title}")
        click.echo(f"Files ({len(files)}):\n")
        current_sec = None
        for f in files:
            sec = f.frontmatter.section
            if sec != current_sec:
                current_sec = sec
                click.echo(f"  [{_section_title(sec)}]")
            rel = f.path.relative_to(project_root)
            title = f.frontmatter.title or f.path.stem
            click.echo(f"    w={f.frontmatter.weight:3d}  {rel}  ({title})")
        return None

    # Assemble.
    combined = _assemble_combined_md(files, config)

    # Ensure output directory.
    output_dir = project_root / config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write combined.md for inspection.
    combined_path = output_dir / "combined.md"
    combined_path.write_text(combined)
    click.echo(f"Wrote {combined_path}")

    # Check for pandoc.
    if not shutil.which("pandoc"):
        click.echo(
            "WARNING: pandoc not found. Install with: sudo dnf install pandoc\n"
            "Combined markdown written but PDF not generated."
        )
        return combined_path

    # Build PDF.
    pdf_name = f"{config.project.name}.pdf"
    pdf_path = output_dir / pdf_name

    bib_path = project_root / "manuscript" / config.bibliography
    template_dir = Path(__file__).parent / "templates"
    latex_template = template_dir / "manuscript.latex"

    cmd = [
        "pandoc",
        str(combined_path),
        "--from", "markdown+yaml_metadata_block+citations+footnotes+pipe_tables+grid_tables",
        "--to", "pdf",
        "--pdf-engine=xelatex",
        "--number-sections",
        "-V", "geometry:margin=1in",
        "-V", "colorlinks=true",
        "-V", "linkcolor=blue",
        "-V", "urlcolor=blue",
        "-o", str(pdf_path),
    ]

    # Use custom template if available AND user requested it via config.
    if config.latex_template:
        custom = project_root / "manuscript" / config.latex_template
        if custom.exists():
            cmd.extend(["--template", str(custom)])

    if bib_path.exists():
        cmd.extend(["--citeproc", "--bibliography", str(bib_path)])

    csl_path = project_root / "manuscript" / config.csl if config.csl else None
    if csl_path and csl_path.exists():
        cmd.extend(["--csl", str(csl_path)])

    click.echo(f"Building PDF: {pdf_path}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        click.echo(f"pandoc failed:\n{result.stderr}")
        raise SystemExit(1)

    click.echo(f"Wrote {pdf_path}")
    return pdf_path
