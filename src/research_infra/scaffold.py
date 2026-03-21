"""Generate boilerplate files for a project: AGENTS.md, config.yaml, pre-commit, CI."""

from __future__ import annotations

import ast
import datetime
from pathlib import Path

import click
import yaml
from jinja2 import Environment, FileSystemLoader


_TEMPLATE_DIR = Path(__file__).parent / "templates"
_ENV = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), keep_trailing_newline=True)


def _read_pyproject(root: Path) -> dict:
    """Read pyproject.toml and return the [project] table as a dict."""
    toml_path = root / "pyproject.toml"
    if not toml_path.exists():
        return {}
    # Use tomllib (stdlib 3.11+).
    import tomllib

    with open(toml_path, "rb") as f:
        data = tomllib.load(f)
    return data.get("project", {})


def _read_package_json(root: Path) -> dict:
    """Read package.json if it exists."""
    pkg_path = root / "package.json"
    if not pkg_path.exists():
        return {}
    import json

    with open(pkg_path) as f:
        return json.load(f)


def _detect_language(root: Path) -> str:
    """Detect primary language from project files."""
    if (root / "pyproject.toml").exists():
        return "Python"
    if (root / "package.json").exists():
        return "TypeScript"
    if (root / "Cargo.toml").exists():
        return "Rust"
    return "Python"


def _detect_build_system(root: Path) -> str:
    """Detect build system."""
    if (root / "pyproject.toml").exists():
        import tomllib

        with open(root / "pyproject.toml", "rb") as f:
            data = tomllib.load(f)
        backend = data.get("build-system", {}).get("build-backend", "")
        if "hatchling" in backend:
            return "hatchling"
        if "uv_build" in backend:
            return "uv_build"
        return backend or "setuptools"
    if (root / "package.json").exists():
        return "pnpm" if (root / "pnpm-lock.yaml").exists() else "npm"
    return "unknown"


def _scan_python_modules(root: Path) -> list[dict]:
    """Scan for Python modules and extract docstrings."""
    modules = []
    # Look for source directories.
    src_dirs = []
    for candidate in [root / "src", root]:
        if not candidate.is_dir():
            continue
        for d in candidate.iterdir():
            if d.is_dir() and (d / "__init__.py").exists():
                src_dirs.append(d)
                break

    # Also check top-level package matching project name.
    pyproject = _read_pyproject(root)
    pkg_name = pyproject.get("name", root.name).replace("-", "_")
    pkg_dir = root / pkg_name
    if pkg_dir.is_dir() and pkg_dir not in src_dirs:
        src_dirs.append(pkg_dir)

    for src_dir in src_dirs:
        for py_file in sorted(src_dir.rglob("*.py")):
            if py_file.name.startswith("_") and py_file.name != "__init__.py":
                continue
            rel = py_file.relative_to(root)
            try:
                tree = ast.parse(py_file.read_text())
                docstring = ast.get_docstring(tree) or ""
                first_line = docstring.split("\n")[0] if docstring else ""
            except Exception:
                first_line = ""

            # Extract public names.
            public = []
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if not node.name.startswith("_"):
                        public.append(node.name)

            modules.append({
                "path": str(rel),
                "purpose": first_line[:80] if first_line else "",
                "api": ", ".join(public[:5]) + ("..." if len(public) > 5 else ""),
            })

    return modules[:30]  # Cap to avoid huge AGENTS.md.


def _detect_test_path(root: Path) -> str:
    """Find the test directory."""
    for candidate in ["tests", "test"]:
        if (root / candidate).is_dir():
            return candidate
    return "tests"


def scaffold_agents_md(root: Path) -> None:
    """Generate AGENTS.md from pyproject.toml and source tree."""
    pyproject = _read_pyproject(root)
    pkg_json = _read_package_json(root)

    name = pyproject.get("name", pkg_json.get("name", root.name))
    description = pyproject.get("description", pkg_json.get("description", ""))
    language = _detect_language(root)
    build_system = _detect_build_system(root)
    license_val = pyproject.get("license", {})
    if isinstance(license_val, dict):
        license_text = license_val.get("text", "")
    else:
        license_text = str(license_val)

    urls = pyproject.get("urls", {})
    repo_url = urls.get("repository", urls.get("Repository", ""))

    modules = _scan_python_modules(root) if language == "Python" else []
    test_path = _detect_test_path(root)

    deps = pyproject.get("dependencies", [])
    external_deps = [{"name": d.split(">")[0].split("<")[0].split("=")[0].split("[")[0].strip(), "version": ""} for d in deps[:10]]

    template = _ENV.get_template("agents_md.jinja2")
    content = template.render(
        project_name=name,
        description=description,
        language=language,
        build_system=build_system,
        license=license_text,
        repo_url=repo_url,
        project_path=str(root),
        modules=modules,
        key_functions=[],
        key_classes=[],
        naming_conventions=["snake_case for functions and variables", "PascalCase for classes"],
        test_path=test_path,
        internal_deps=[],
        external_deps=external_deps,
        file_conventions=["Tests mirror source structure"],
        invariants=["No unittest.mock usage in tests"],
        date=datetime.date.today().isoformat(),
    )

    out = root / "AGENTS.md"
    out.write_text(content)
    click.echo(f"Wrote {out}")


def scaffold_manuscript(root: Path) -> None:
    """Create manuscript/config.yaml and manuscript/references.bib."""
    manuscript_dir = root / "manuscript"
    manuscript_dir.mkdir(exist_ok=True)
    (manuscript_dir / "output").mkdir(exist_ok=True)

    config_path = manuscript_dir / "config.yaml"
    bib_path = manuscript_dir / "references.bib"

    pyproject = _read_pyproject(root)
    name = pyproject.get("name", root.name)
    description = pyproject.get("description", root.name)

    authors_raw = pyproject.get("authors", [])
    authors = []
    for a in authors_raw:
        if isinstance(a, dict):
            authors.append({
                "name": a.get("name", ""),
                "affiliation": "",
                "email": a.get("email", ""),
                "orcid": "",
            })

    if not authors:
        authors = [{"name": "Morgan G Hough", "affiliation": "Independent Researcher", "email": "morgan.g.hough@gmail.com", "orcid": ""}]

    keywords = pyproject.get("keywords", [])

    config_data = {
        "project": {
            "name": name,
            "title": description,
            "short_title": name,
        },
        "authors": authors,
        "date": datetime.date.today().isoformat(),
        "version": pyproject.get("version", "0.1.0"),
        "abstract_source": "auto",
        "keywords": keywords,
        "exclude_drafts": False,
        "bibliography": "references.bib",
        "beamer_theme": "metropolis",
        "scan_paths": ["."],
        "exclude_paths": [".git", ".venv", "node_modules", "__pycache__", "manuscript/output", ".github"],
        "output_dir": "manuscript/output",
    }

    if not config_path.exists():
        with open(config_path, "w") as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
        click.echo(f"Wrote {config_path}")
    else:
        click.echo(f"Skipped {config_path} (already exists)")

    if not bib_path.exists():
        bib_path.write_text(
            "% Bibliography for " + name + "\n"
            "% Add BibTeX entries below.\n\n"
        )
        click.echo(f"Wrote {bib_path}")
    else:
        click.echo(f"Skipped {bib_path} (already exists)")

    # Add output/ to .gitignore if not already there.
    gitignore = root / ".gitignore"
    ignore_line = "manuscript/output/"
    if gitignore.exists():
        existing = gitignore.read_text()
        if ignore_line not in existing:
            with open(gitignore, "a") as f:
                f.write(f"\n{ignore_line}\n")
            click.echo(f"Added {ignore_line} to .gitignore")
    else:
        gitignore.write_text(f"{ignore_line}\n")
        click.echo(f"Wrote {gitignore}")


def scaffold_pre_commit(root: Path) -> None:
    """Create .pre-commit-config.yaml."""
    out = root / ".pre-commit-config.yaml"
    language = _detect_language(root)

    if language == "Python":
        content = """\
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.11.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: end-of-file-fixer
      - id: trailing-whitespace
      - id: check-yaml
      - id: check-toml
      - id: check-added-large-files
        args: ["--maxkb=500"]

  - repo: local
    hooks:
      - id: no-mock
        name: no-mock
        description: "Forbid unittest.mock usage in tests"
        entry: bash -c 'grep -rn "MagicMock\\|unittest\\.mock\\|from mock import\\|@patch" tests/ test/ 2>/dev/null && exit 1 || exit 0'
        language: system
        pass_filenames: false
        always_run: true
"""
    else:
        content = """\
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: end-of-file-fixer
      - id: trailing-whitespace
      - id: check-yaml
      - id: check-added-large-files
        args: ["--maxkb=500"]
"""

    if not out.exists():
        out.write_text(content)
        click.echo(f"Wrote {out}")
    else:
        click.echo(f"Skipped {out} (already exists)")


def scaffold_ci(root: Path) -> None:
    """Create .github/workflows/ci.yml."""
    workflows_dir = root / ".github" / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)
    out = workflows_dir / "ci.yml"

    pyproject = _read_pyproject(root)
    name = pyproject.get("name", root.name)
    language = _detect_language(root)
    test_path = _detect_test_path(root)

    # Detect source directory.
    src_dir = "src/"
    pkg_name = name.replace("-", "_")
    if (root / pkg_name).is_dir():
        src_dir = f"{pkg_name}/"
    elif (root / "src").is_dir():
        src_dir = "src/"

    if language == "Python":
        content = f"""\
name: CI

on:
  push:
    branches: [main]
  pull_request:

env:
  MPLBACKEND: Agg

jobs:
  test:
    name: Test (Python ${{{{ matrix.python-version }}}})
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - name: Install Python
        run: uv python install ${{{{ matrix.python-version }}}}
      - name: Install dependencies
        run: uv sync --group dev 2>/dev/null || uv pip install -e ".[dev]"
      - name: Ruff check
        run: uv run ruff check {src_dir} {test_path}/
      - name: Ruff format check
        run: uv run ruff format --check {src_dir} {test_path}/
      - name: No-mock check
        run: |
          if grep -rn "unittest\\.mock\\|MagicMock\\|from mock import\\|@patch" {test_path}/ --include="*.py" | grep -v "^#"; then
            echo "::error::unittest.mock usage detected in tests"
            exit 1
          fi
      - name: Pytest
        run: uv run pytest {test_path}/ -v --tb=short
"""
    else:
        content = f"""\
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npm test
"""

    if not out.exists():
        out.write_text(content)
        click.echo(f"Wrote {out}")
    else:
        click.echo(f"Skipped {out} (already exists)")


def scaffold_all(root: Path) -> None:
    """Run all scaffolding commands."""
    from .autoresearch import scaffold_autoresearch

    click.echo(f"Scaffolding {root.name}...\n")
    scaffold_agents_md(root)
    scaffold_manuscript(root)
    scaffold_pre_commit(root)
    scaffold_ci(root)
    scaffold_autoresearch(root)
    click.echo(f"\nDone. Review generated files and customize as needed.")
