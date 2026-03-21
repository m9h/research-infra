"""Validation hooks: no-mock enforcement and frontmatter validation."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import frontmatter
from pydantic import ValidationError

from .schemas import MdFrontmatter

# Patterns that indicate mock usage.
MOCK_PATTERNS = [
    r"unittest\.mock",
    r"from\s+mock\s+import",
    r"MagicMock",
    r"@patch",
    r"patch\(",
    r"mock\.patch",
    r"mocker\.",
]
_MOCK_RE = re.compile("|".join(MOCK_PATTERNS))


def check_no_mock(test_dir: Path) -> list[str]:
    """Check for mock usage in test files. Returns list of violation strings."""
    violations = []
    if not test_dir.exists():
        return violations

    for py_file in test_dir.rglob("*.py"):
        with open(py_file) as f:
            for i, line in enumerate(f, 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if _MOCK_RE.search(line):
                    violations.append(f"{py_file}:{i}: {stripped}")
    return violations


def check_frontmatter(project_root: Path, scan_paths: list[str] | None = None) -> list[str]:
    """Validate YAML frontmatter in .md files. Returns list of error strings."""
    errors = []
    roots = [project_root / p for p in (scan_paths or ["."])]

    for root in roots:
        if not root.exists():
            continue
        for md_path in root.rglob("*.md"):
            rel = md_path.relative_to(project_root)
            if any(part in {".git", ".venv", "node_modules", "__pycache__"} for part in rel.parts):
                continue

            try:
                post = frontmatter.load(str(md_path))
            except Exception as e:
                errors.append(f"{md_path}: failed to parse frontmatter: {e}")
                continue

            if not post.metadata or "category" not in post.metadata:
                continue  # No frontmatter or no category — not participating, skip.

            try:
                MdFrontmatter(**post.metadata)
            except (ValidationError, ValueError) as e:
                errors.append(f"{md_path}: invalid frontmatter: {e}")

    return errors


def no_mock_hook() -> None:
    """Pre-commit entry point: check files passed as arguments for mock usage."""
    violations = []
    for filepath in sys.argv[1:]:
        path = Path(filepath)
        if not path.exists():
            continue
        with open(path) as f:
            for i, line in enumerate(f, 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if _MOCK_RE.search(line):
                    violations.append(f"{filepath}:{i}: {stripped}")

    if violations:
        print("ERROR: unittest.mock usage detected. Use real implementations.")
        for v in violations:
            print(f"  {v}")
        sys.exit(1)


def frontmatter_hook() -> None:
    """Pre-commit entry point: validate frontmatter in .md files passed as arguments."""
    errors = []
    for filepath in sys.argv[1:]:
        path = Path(filepath)
        if not path.exists():
            continue
        try:
            post = frontmatter.load(str(path))
        except Exception as e:
            errors.append(f"{filepath}: parse error: {e}")
            continue

        if not post.metadata or "category" not in post.metadata:
            continue

        try:
            MdFrontmatter(**post.metadata)
        except (ValidationError, ValueError) as e:
            errors.append(f"{filepath}: {e}")

    if errors:
        print("ERROR: Invalid frontmatter in .md files:")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)
