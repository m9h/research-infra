"""Autoresearch infrastructure: per-project autonomous research loops and scheduling."""

from __future__ import annotations

import datetime
import json
from pathlib import Path

import click
import yaml


# Default research questions per project type (keyed by project name).
# These are starting points — users should customize.
RESEARCH_TEMPLATES: dict[str, dict] = {
    "alf": {
        "goal": "Discover parameter regimes and generative model structures where active inference agents exhibit qualitatively different behavior from RL baselines (e.g., information-seeking, risk-sensitivity, habit formation).",
        "metric": "behavioral_divergence = KL(policy_AIF || policy_RL) weighted by task-relevant outcomes",
        "parameters": [
            "Generative model structure: A/B/C/D matrix sparsity and rank",
            "Environment: T-maze depth, reward volatility, observation noise",
            "Agent: EFE horizon (1-8), precision (gamma), learning rate",
            "Baselines: Q-learning, SARSA, actor-critic from neuro-nav",
        ],
    },
    "hgx": {
        "goal": "Identify hypergraph neural network architectures and datasets where higher-order structure provides measurable advantage over pairwise GNN baselines.",
        "metric": "ho_advantage = (accuracy_hgx - accuracy_gnn) / accuracy_gnn on held-out test set",
        "parameters": [
            "Convolution layer: UniGCN, HGNN, AllSet, AllDeepSets, HyperGCN, SheafDiffusion",
            "Dataset: Cora cocitation, Citeseer, Pubmed, organoid GRN, synthetic planted partition",
            "Architecture: depth (1-8), hidden dim (16-256), dropout, batch norm",
            "Hypergraph construction: k-nearest, Delaunay, clique expansion, co-occurrence",
        ],
    },
    "setae": {
        "goal": "Optimize bio-inspired surface designs using differentiable contact mechanics — find structures that maximize adhesion-to-weight ratio or drag reduction beyond known biological solutions.",
        "metric": "design_score = adhesion_force / (weight * contact_area) relative to flat baseline",
        "parameters": [
            "Contact model: JKR, DMT, Maugis-Dugdale",
            "Geometry: pillar radius, height, spacing, hierarchy levels (1-4)",
            "Material: elastic modulus, surface energy, Poisson ratio",
            "Bio-template: gecko, tree frog, lotus, shark, nacre",
        ],
    },
    "jaxctrl": {
        "goal": "Benchmark differentiable control solvers against classical baselines on nonlinear systems — find regimes where autodiff through control provides faster convergence or better solutions.",
        "metric": "control_advantage = (cost_classical - cost_jaxctrl) / cost_classical with matched wall time",
        "parameters": [
            "System: Van der Pol, Lorenz, pendulum, cartpole, coupled oscillators",
            "Controller: LQR, MPC, Lyapunov-based, neural, tensor decomposition",
            "Dimension: state dim (2-20), input dim (1-5)",
            "Hypergraph controllability: random hypergraph ensembles, controllability fraction",
        ],
    },
    "qcccm": {
        "goal": "Find sociophysics models and parameter regimes where quantum methods outperform classical methods for finding ground states (social equilibria) of disordered multi-agent systems.",
        "metric": "quantum_advantage = (E_classical - E_quantum) / |E_exact|",
        "parameters": [
            "Topology: complete, square lattice, chain, ring, star, random, scale-free",
            "Disorder: SK (Gaussian J_ij), EA bimodal, EA Gaussian, uniform",
            "System size: N = 4 to 20",
            "Method: Metropolis MC vs PIMC vs VQE vs QAOA",
        ],
    },
    "organoid-hgx-benchmark": {
        "goal": "Systematically benchmark hypergraph neural networks on gene regulatory network inference from organoid scRNA-seq data — identify which HNN architectures best capture higher-order regulatory interactions.",
        "metric": "grn_score = AUROC on held-out regulatory edges + biological validation score (regulon coherence, fate probability, pseudotime correlation)",
        "parameters": [
            "GRN construction: Pando, SCENIC, correlation-based, mutual information",
            "HNN architecture: UniGCN, HGNN, AllSet, SheafDiffusion from hgx",
            "Data split: random, temporal (pseudotime), cell-type stratified",
            "Feature: raw counts, imputed, velocity, regulon activity scores",
        ],
    },
    "spinning-up-alf": {
        "goal": "Validate the RL↔AIF equivalence claims empirically — find environments where the theoretical equivalences break down or where one framework offers practical advantages.",
        "metric": "equivalence_gap = |V_RL(s) - (-G_AIF(s))| averaged over states, plus learning curve comparison (area under reward curve)",
        "parameters": [
            "Environment: GridEnv topologies from neuro-nav (open field, barriers, multiple goals)",
            "RL agent: Q-learning, SARSA, successor representation, actor-critic",
            "AIF agent: AnalyticAgent, BatchAgent from alf with matched parameters",
            "Equivalence condition: observation model A = identity vs partial observability",
        ],
    },
}


def generate_program_md(
    project_name: str,
    project_root: Path,
    custom_goal: str | None = None,
) -> str:
    """Generate an autoresearch program.md for a project."""
    template = RESEARCH_TEMPLATES.get(project_name, {})
    goal = custom_goal or template.get("goal", f"Autonomous research loop for {project_name}.")
    metric = template.get("metric", "improvement = (new_score - baseline_score) / baseline_score")
    parameters = template.get("parameters", ["Parameter space to be defined"])

    param_list = "\n".join(f"- {p}" for p in parameters)
    date = datetime.date.today().isoformat()

    return f"""# {project_name} Autoresearch Program

> Generated by research-infra on {date}. Customize this file for your project.

## Goal

{goal}

## The Loop

You are an autonomous research agent. Run this loop indefinitely:

1. **Read** `results.tsv` to understand what has been tried and what worked
2. **Modify** `experiment.py` with a new experimental idea
3. **Commit** with a short description: `git commit -am "experiment: <description>"`
4. **Run**: `uv run python autoresearch/experiment.py > autoresearch/run.log 2>&1`
5. **Extract results**: `grep "^RESULT|" autoresearch/run.log`
6. If empty → crash → `tail -n 50 autoresearch/run.log` → attempt fix
7. **Log** to `autoresearch/results.tsv` (append, untracked)
8. If metric improves → **KEEP** (advance branch)
9. If no improvement → **DISCARD** (`git checkout -- autoresearch/experiment.py`)
10. **NEVER STOP.** Do not ask the human. Run indefinitely.

## Metric

```
{metric}
```

## What You Can Change

Everything in `experiment.py` is fair game:

{param_list}

## What You Cannot Change

- The infrastructure imports and solver wrappers
- The metric definition
- The 10-minute wall-clock timeout per experiment
- The requirement to report all metrics

## Results Format

Each experiment appends one line to `results.tsv`:

```
commit\\tmetric_value\\tparameters_json\\tstatus\\tdescription
```

## Strategy Guidance

1. Start with the simplest configuration. Establish a baseline.
2. Vary one parameter at a time to understand sensitivity.
3. Combine insights from previous runs to find promising regimes.
4. If stuck, try a radically different configuration.
5. Re-read results.tsv periodically to spot patterns.

## If You Get Stuck

- Re-read results.tsv for patterns
- Try combining two previous near-misses
- Try a radically different parameter setting
- Check run.log for subtle errors or warnings
"""


def generate_experiment_py(project_name: str) -> str:
    """Generate a starter experiment.py for a project."""
    return f'''"""Autoresearch experiment for {project_name}.

This file is modified by the autonomous research agent.
The agent changes parameters, models, and configurations here.
Infrastructure (imports, metric computation, output format) is fixed.
"""

import json
import sys
import time

# === EXPERIMENT CONFIGURATION (agent modifies this section) ===

EXPERIMENT = {{
    "description": "baseline configuration",
    "parameters": {{
        # Fill in project-specific parameters
    }},
}}

# === INFRASTRUCTURE (do not modify below this line) ===


def run_experiment(config: dict) -> dict:
    """Run a single experiment and return results."""
    start = time.time()

    # TODO: Import project-specific code and run experiment.
    # This is a placeholder — customize for {project_name}.
    result = {{
        "metric_value": 0.0,
        "parameters": config["parameters"],
        "wall_time": time.time() - start,
        "status": "placeholder",
    }}

    return result


def main():
    result = run_experiment(EXPERIMENT)

    # Output in parseable format.
    print(f"RESULT|{{result[\'metric_value\']}}|{{json.dumps(result[\'parameters\'])}}|{{result[\'status\']}}|{{EXPERIMENT[\'description\']}}")


if __name__ == "__main__":
    main()
'''


def scaffold_autoresearch(project_root: Path) -> None:
    """Create autoresearch/ directory with program.md and experiment.py."""
    project_name = project_root.name
    # Try to get name from pyproject.toml.
    toml_path = project_root / "pyproject.toml"
    if toml_path.exists():
        import tomllib

        with open(toml_path, "rb") as f:
            data = tomllib.load(f)
        project_name = data.get("project", {}).get("name", project_name)

    ar_dir = project_root / "autoresearch"
    ar_dir.mkdir(exist_ok=True)

    program_path = ar_dir / "program.md"
    if not program_path.exists():
        program_path.write_text(generate_program_md(project_name, project_root))
        click.echo(f"Wrote {program_path}")
    else:
        click.echo(f"Skipped {program_path} (already exists)")

    experiment_path = ar_dir / "experiment.py"
    if not experiment_path.exists():
        experiment_path.write_text(generate_experiment_py(project_name))
        click.echo(f"Wrote {experiment_path}")
    else:
        click.echo(f"Skipped {experiment_path} (already exists)")

    # Create empty results.tsv with header.
    results_path = ar_dir / "results.tsv"
    if not results_path.exists():
        results_path.write_text("commit\tmetric_value\tparameters\tstatus\tdescription\n")
        click.echo(f"Wrote {results_path}")

    # Add to .gitignore (results.tsv and run.log are untracked).
    gitignore = project_root / ".gitignore"
    lines_to_add = ["autoresearch/results.tsv", "autoresearch/run.log"]
    if gitignore.exists():
        existing = gitignore.read_text()
        for line in lines_to_add:
            if line not in existing:
                with open(gitignore, "a") as f:
                    f.write(f"\n{line}")
    else:
        gitignore.write_text("\n".join(lines_to_add) + "\n")


# ---------- Scheduler ----------


DEFAULT_PROJECTS_DIR = Path.home() / "dev"

SCHEDULE_FILE = DEFAULT_PROJECTS_DIR / "research-infra" / "schedule.json"


def discover_autoresearch_projects(
    projects_dir: Path = DEFAULT_PROJECTS_DIR,
) -> list[Path]:
    """Find all projects with autoresearch/program.md."""
    results = []
    if not projects_dir.is_dir():
        return results
    for d in sorted(projects_dir.iterdir()):
        if d.is_dir() and (d / "autoresearch" / "program.md").exists():
            results.append(d)
    return results


def load_schedule(schedule_file: Path = SCHEDULE_FILE) -> dict:
    """Load the round-robin schedule state."""
    if schedule_file.exists():
        with open(schedule_file) as f:
            return json.load(f)
    return {"last_index": -1, "history": []}


def save_schedule(state: dict, schedule_file: Path = SCHEDULE_FILE) -> None:
    """Save the round-robin schedule state."""
    schedule_file.parent.mkdir(parents=True, exist_ok=True)
    with open(schedule_file, "w") as f:
        json.dump(state, f, indent=2, default=str)


def next_project(projects_dir: Path = DEFAULT_PROJECTS_DIR) -> Path | None:
    """Get the next project in the round-robin schedule."""
    projects = discover_autoresearch_projects(projects_dir)
    if not projects:
        return None

    state = load_schedule()
    idx = (state["last_index"] + 1) % len(projects)
    project = projects[idx]

    state["last_index"] = idx
    state["history"].append({
        "project": str(project),
        "timestamp": datetime.datetime.now().isoformat(),
    })
    # Keep last 100 history entries.
    state["history"] = state["history"][-100:]
    save_schedule(state)

    return project


def show_schedule(projects_dir: Path = DEFAULT_PROJECTS_DIR) -> None:
    """Display the current schedule and project roster."""
    projects = discover_autoresearch_projects(projects_dir)
    state = load_schedule()

    click.echo(f"Autoresearch projects ({len(projects)}):\n")
    for i, p in enumerate(projects):
        marker = " >>>" if i == (state["last_index"] + 1) % len(projects) else "    "
        click.echo(f"  {marker} [{i}] {p.name}")

    if state["history"]:
        click.echo(f"\nLast 5 runs:")
        for entry in state["history"][-5:]:
            click.echo(f"  {entry['timestamp']}  {Path(entry['project']).name}")
    else:
        click.echo("\nNo runs yet.")
