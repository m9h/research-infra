"""CLI entry point for research-infra (rinf command)."""

from __future__ import annotations

from pathlib import Path

import click


def _resolve_project(project: str | None) -> Path:
    """Resolve project root from --project flag or cwd."""
    if project:
        p = Path(project).resolve()
    else:
        p = Path.cwd()
    if not p.is_dir():
        raise click.BadParameter(f"Not a directory: {p}")
    return p


@click.group()
@click.version_option(package_name="research-infra")
def main() -> None:
    """research-infra: manuscript assembly, slides, and project validation."""


# ---------- discover ----------


@main.command()
@click.option("--project", "-p", default=None, help="Project root directory (default: cwd)")
@click.option("--category", "-c", default=None, help="Filter by category (research/infrastructure/pedagogy)")
@click.option("--section", "-s", default=None, help="Filter by section (abstract/introduction/...)")
def discover(project: str | None, category: str | None, section: str | None) -> None:
    """List .md files with valid frontmatter in a project."""
    from .discover import discover_and_sort, load_project_config
    from .schemas import Category, Section

    root = _resolve_project(project)

    try:
        config = load_project_config(root)
    except FileNotFoundError:
        # Allow discovery even without config.yaml — use defaults.
        from .schemas import ProjectConfig, ProjectIdentity

        config = ProjectConfig(
            project=ProjectIdentity(name=root.name, title=root.name),
            authors=[],
        )

    cat = Category(category) if category else None
    sec = Section(section) if section else None

    files = discover_and_sort(root, category=cat, section=sec, config=config)

    if not files:
        click.echo("No .md files with valid frontmatter found.")
        return

    for f in files:
        rel = f.path.relative_to(root)
        fm = f.frontmatter
        summary = fm.slide_summary[:60] + "..." if fm.slide_summary and len(fm.slide_summary) > 60 else (fm.slide_summary or "")
        click.echo(
            f"  {fm.section.value:14s}  w={fm.weight:3d}  {fm.status:6s}  {rel}"
            + (f"  [{summary}]" if summary else "")
        )


# ---------- validate ----------


@main.command()
@click.option("--project", "-p", default=None, help="Project root directory (default: cwd)")
@click.option(
    "--check",
    type=click.Choice(["frontmatter", "no-mock", "all"]),
    default="all",
    help="Which checks to run",
)
def validate(project: str | None, check: str) -> None:
    """Validate project structure, frontmatter, and no-mock policy."""
    from .validate import check_frontmatter, check_no_mock

    root = _resolve_project(project)
    errors: list[str] = []

    if check in ("frontmatter", "all"):
        click.echo("Checking frontmatter...")
        errors.extend(check_frontmatter(root))

    if check in ("no-mock", "all"):
        click.echo("Checking no-mock policy...")
        # Try common test directory names.
        for test_dir_name in ("tests", "test"):
            test_dir = root / test_dir_name
            if test_dir.exists():
                errors.extend(check_no_mock(test_dir))

    if errors:
        click.echo(f"\n{len(errors)} issue(s) found:")
        for e in errors:
            click.echo(f"  {e}")
        raise SystemExit(1)
    else:
        click.echo("All checks passed.")


# ---------- build ----------


@main.group()
def build() -> None:
    """Build manuscript or slides."""


@build.command()
@click.option("--project", "-p", default=None, help="Project root directory (default: cwd)")
@click.option("--dry-run", is_flag=True, help="Show what would be included without building")
@click.option("--exclude-drafts", is_flag=True, help="Skip files with status: draft")
def manuscript(project: str | None, dry_run: bool, exclude_drafts: bool) -> None:
    """Build research manuscript PDF from frontmatter-tagged .md files."""
    from .manuscript import build_manuscript

    root = _resolve_project(project)
    build_manuscript(root, dry_run=dry_run, exclude_drafts=exclude_drafts)


@build.command()
@click.option("--project", "-p", default=None, help="Project root directory (default: cwd)")
@click.option("--dry-run", is_flag=True, help="Show what would be included without building")
def slides(project: str | None, dry_run: bool) -> None:
    """Build Beamer slide deck PDF from slide_summary fields."""
    from .slides import build_slides

    root = _resolve_project(project)
    build_slides(root, dry_run=dry_run)


# ---------- scaffold ----------


@main.group()
def scaffold() -> None:
    """Generate boilerplate files for a project."""


@scaffold.command("agents-md")
@click.option("--project", "-p", default=None, help="Project root directory (default: cwd)")
def scaffold_agents_md(project: str | None) -> None:
    """Generate AGENTS.md from pyproject.toml and source tree."""
    from .scaffold import scaffold_agents_md as _scaffold

    root = _resolve_project(project)
    _scaffold(root)


@scaffold.command("manuscript")
@click.option("--project", "-p", default=None, help="Project root directory (default: cwd)")
def scaffold_manuscript(project: str | None) -> None:
    """Create manuscript/config.yaml and manuscript/references.bib."""
    from .scaffold import scaffold_manuscript as _scaffold

    root = _resolve_project(project)
    _scaffold(root)


@scaffold.command("pre-commit")
@click.option("--project", "-p", default=None, help="Project root directory (default: cwd)")
def scaffold_pre_commit(project: str | None) -> None:
    """Create .pre-commit-config.yaml."""
    from .scaffold import scaffold_pre_commit as _scaffold

    root = _resolve_project(project)
    _scaffold(root)


@scaffold.command("ci")
@click.option("--project", "-p", default=None, help="Project root directory (default: cwd)")
def scaffold_ci(project: str | None) -> None:
    """Create .github/workflows/ci.yml."""
    from .scaffold import scaffold_ci as _scaffold

    root = _resolve_project(project)
    _scaffold(root)


@scaffold.command("autoresearch")
@click.option("--project", "-p", default=None, help="Project root directory (default: cwd)")
def scaffold_autoresearch(project: str | None) -> None:
    """Create autoresearch/program.md and experiment.py."""
    from .autoresearch import scaffold_autoresearch as _scaffold

    root = _resolve_project(project)
    _scaffold(root)


@scaffold.command("all")
@click.option("--project", "-p", default=None, help="Project root directory (default: cwd)")
def scaffold_all(project: str | None) -> None:
    """Run all scaffolding commands."""
    from .scaffold import scaffold_all as _scaffold

    root = _resolve_project(project)
    _scaffold(root)


# ---------- autoresearch ----------


@main.group()
def autoresearch() -> None:
    """Autoresearch scheduling and management."""


@autoresearch.command("schedule")
@click.option("--projects-dir", "-d", default=None, help="Parent directory containing projects (default: ~/dev)")
def ar_schedule(projects_dir: str | None) -> None:
    """Show the autoresearch schedule and project roster."""
    from .autoresearch import show_schedule, DEFAULT_PROJECTS_DIR

    d = Path(projects_dir).resolve() if projects_dir else DEFAULT_PROJECTS_DIR
    show_schedule(d)


@autoresearch.command("next")
@click.option("--projects-dir", "-d", default=None, help="Parent directory containing projects (default: ~/dev)")
def ar_next(projects_dir: str | None) -> None:
    """Print the next project in the round-robin and advance the pointer."""
    from .autoresearch import next_project, DEFAULT_PROJECTS_DIR

    d = Path(projects_dir).resolve() if projects_dir else DEFAULT_PROJECTS_DIR
    project = next_project(d)
    if project:
        click.echo(str(project))
    else:
        click.echo("No projects with autoresearch/program.md found.")
        raise SystemExit(1)


@autoresearch.command("scaffold-all")
@click.option("--projects-dir", "-d", default=None, help="Parent directory containing projects (default: ~/dev)")
def ar_scaffold_all(projects_dir: str | None) -> None:
    """Scaffold autoresearch/ in all projects that have pyproject.toml."""
    from .autoresearch import scaffold_autoresearch as _scaffold, DEFAULT_PROJECTS_DIR

    d = Path(projects_dir).resolve() if projects_dir else DEFAULT_PROJECTS_DIR
    count = 0
    for p in sorted(d.iterdir()):
        if p.is_dir() and (p / "pyproject.toml").exists():
            click.echo(f"\n--- {p.name} ---")
            _scaffold(p)
            count += 1
    click.echo(f"\nScaffolded autoresearch in {count} projects.")
