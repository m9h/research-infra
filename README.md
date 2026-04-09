# research-infra

Manuscript assembly, Beamer slides, project validation, and autonomous research
scheduling for a multi-repo research lab — with first-class support for agentic
AI coding workflows.

## Install

```bash
uv sync --group dev
```

## Quick start

```bash
rinf discover                          # list frontmatter-tagged .md files
rinf validate                          # validate project structure
rinf build manuscript                  # build PDF from tagged .md files
rinf build slides                      # build Beamer slide deck
rinf scaffold all                      # generate AGENTS.md, config.yaml, pre-commit, CI
rinf autoresearch schedule             # show autonomous research rotation
rinf autoresearch next                 # advance round-robin to next project
```

## Agentic research infrastructure

research-infra serves as the backbone for agentic AI workflows across a
JAX-based computational neuroscience ecosystem. It coordinates autonomous
research agents, enforces project conventions, and connects the full research
lifecycle — from literature review through manuscript assembly.

### Agent-ready codebases

Every project in the ecosystem includes a `CLAUDE.md` that tells AI agents how
to navigate the codebase: module maps, testing commands, dependency conventions,
and anti-patterns. This follows the pattern described in
[Agentic Research Workflows](https://neuromechanist.github.io/blog/010-agentic-research-workflows/)
— encoding domain knowledge into reusable, machine-readable specifications so
agents understand project structure without repeated explanation.

### Research-skills plugins

Six plugins from the
[neuromechanist/research-skills](https://github.com/neuromechanist/research-skills)
marketplace extend Claude Code with research-specific capabilities:

| Plugin | Commands | Purpose |
|--------|----------|---------|
| **project** | `/init-project`, `/epic-dev`, `/setup-ci`, `/release-prep`, `/doc-process` | Project scaffolding, CI/CD, Docker, security audits |
| **grant** | `/grant-write`, `/grant-review` | NIH/NSF proposal drafting (R01, R21, K99, CAREER) with simulated study section scoring |
| **manuscript** | `/paper-review`, `/manuscript-prep` | IMRAD structuring, journal formatting (Nature, IEEE, PNAS, Elsevier), peer review calibration |
| **opencite** | `/opencite` | Literature search across Semantic Scholar, OpenAlex, PubMed, arXiv, bioRxiv; BibTeX export |
| **scientific-figures** | *(implicit)* | Matplotlib/seaborn/plotly figure creation, icon generation, visual QA feedback loops |
| **neuroinformatics** | `/convert-bids`, `/validate-bids`, `/design-experiment` | EEG/EMG to BIDS conversion, PsychoPy experiment scaffolding with LSL integration |

Install them:

```bash
claude plugin marketplace add neuromechanist/research-skills
for p in project grant manuscript opencite scientific-figures neuroinformatics; do
  claude plugin install "$p@research-skills"
done
```

### Cross-project workflows

**Literature review to implementation:**

1. `/opencite` to search, build citation graphs, and organize references
2. Implement in the relevant project repo
3. Tag research `.md` files with frontmatter for manuscript assembly

**Manuscript assembly:**

1. Write sections as `.md` files with `category: research` frontmatter
2. `rinf build manuscript` to compile a PDF via pandoc + XeLaTeX
3. `/paper-review` for peer review calibration against target journal

**Autonomous research loops:**

1. `rinf scaffold autoresearch` to generate `program.md`, `experiment.py`, and `results.tsv`
2. Edit `autoresearch/program.md` with project-specific goals and metrics
3. `rinf autoresearch next` to coordinate round-robin scheduling across all projects

## Commands

### Discovery and validation

```bash
rinf discover [-p PROJECT] [-c CATEGORY] [-s SECTION]
```

List all `.md` files with valid frontmatter. Filter by category
(`research` / `infrastructure` / `pedagogy`) or section
(`abstract` / `introduction` / `background` / `methodology` / `results` /
`discussion` / `conclusion` / `appendix` / `supplementary`).

```bash
rinf validate [-p PROJECT] [--check frontmatter|no-mock|all]
```

Validate project structure:

- **frontmatter** — checks YAML metadata in `.md` files against the
  `MdFrontmatter` schema (category, section, weight, status)
- **no-mock** — enforces that tests never use `unittest.mock`, `MagicMock`,
  `@patch`, or `mocker.` — real implementations only

### Build

```bash
rinf build manuscript [-p PROJECT] [--dry-run] [--exclude-drafts]
```

Assemble a research PDF from frontmatter-tagged `.md` files. Discovers all
`category: research` files, sorts by section order then weight, demotes headings,
strips remote images, and compiles via pandoc + XeLaTeX with citation support.

```bash
rinf build slides [-p PROJECT] [--dry-run]
```

Build a Beamer presentation from `slide_summary` fields in frontmatter. Each
tagged file becomes one frame, grouped by section, with the first local figure
extracted automatically.

### Scaffold

```bash
rinf scaffold agents-md [-p PROJECT]    # AGENTS.md from pyproject.toml + source tree
rinf scaffold manuscript [-p PROJECT]   # manuscript/config.yaml + references.bib
rinf scaffold pre-commit [-p PROJECT]   # .pre-commit-config.yaml (ruff + no-mock)
rinf scaffold ci [-p PROJECT]           # .github/workflows/ci.yml
rinf scaffold autoresearch [-p PROJECT] # autoresearch/program.md + experiment.py
rinf scaffold all [-p PROJECT]          # all of the above
```

### Autoresearch scheduling

The autoresearch system coordinates autonomous experiment loops across a
portfolio of projects. Each project defines a research goal, a quantitative
metric, and a parameter space in `autoresearch/program.md`. An autonomous agent
runs the loop: modify `experiment.py`, commit, run, extract results, keep
improvements, discard regressions, repeat.

```bash
rinf autoresearch schedule [-d PROJECTS_DIR]    # show project roster and rotation
rinf autoresearch next [-d PROJECTS_DIR]        # print next project, advance pointer
rinf autoresearch scaffold-all [-d PROJECTS_DIR] # scaffold all projects with pyproject.toml
```

By default, the scheduler scans both `~/dev/` and `~/Workspace/` for projects
containing `autoresearch/program.md`, deduplicating by project name.

**Built-in research templates** provide domain-specific goals, metrics, and
parameter spaces for:

| Project | Research goal |
|---------|---------------|
| alf | AIF vs RL behavioral divergence across generative model structures |
| hgx | Higher-order advantage of hypergraph NNs over pairwise GNN baselines |
| jaxctrl | Autodiff-through-control vs classical solver benchmarks |
| neurojax | Differentiable source imaging vs classical inverse methods |
| devograph | Hypergraph models for developmental trajectory and GRN inference |
| ephys-tokenizer-jax | MEG/EEG tokenization strategy optimization |
| organoid-hgx-benchmark | HNN architectures for organoid GRN inference |
| spinning-up-alf | Empirical validation of RL-AIF equivalence claims |
| setae | Bio-inspired surface design via differentiable contact mechanics |
| qcccm | Quantum vs classical ground-state methods for social equilibria |

## Pre-commit hooks

Two hooks are available for use in any project's `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: no-mock
      name: no-mock
      entry: research-infra-no-mock
      language: system
      types: [python]
      files: ^tests?/
    - id: validate-frontmatter
      name: validate-frontmatter
      entry: research-infra-validate-frontmatter
      language: system
      types: [markdown]
```

## Frontmatter schema

Tag `.md` files with YAML frontmatter for discovery, manuscript assembly, and
slide generation:

```yaml
---
category: research          # research | infrastructure | pedagogy
section: methodology        # abstract | introduction | background | methodology |
                            # results | discussion | conclusion | appendix | supplementary
weight: 20                  # 0-999, controls order within section
title: "Methods"
status: draft               # any string; use --exclude-drafts to skip
slide_summary: "One-liner for Beamer frame content."
tags: [jax, simulation]
exclude: false              # true to skip in all builds
---
```

## Project ecosystem

research-infra manages a JAX-based computational neuroscience ecosystem:

```
hgx ──────────┬── devograph
              ├── organoid-hgx-benchmark
              └── jaxctrl (optional)

alf ──────────── spinning-up-alf

neurojax          (standalone, 120+ tests)
ephys-tokenizer-jax  (optional neurojax integration)
Thinking-Higher      (TypeScript/Next.js, planned JAX via Modal)
```

All Python projects share: `uv` for packaging, `hatchling` builds, `ruff` for
linting, `pytest` + `beartype` for testing, no-mock policy, and the Kidger stack
(Equinox, Diffrax, Optax, Lineax).

## License

Apache-2.0
