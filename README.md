# research-infra

Manuscript assembly, Beamer slides, and project validation for a multi-repo research lab.

## Install

```bash
uv sync --group dev
```

## Usage

```bash
rinf discover                          # List frontmatter-tagged .md files
rinf validate                          # Validate project structure
rinf build manuscript                  # Build PDF from tagged .md files
rinf build slides                      # Build Beamer slide deck
rinf scaffold all                      # Generate AGENTS.md, config.yaml, pre-commit, CI
```
