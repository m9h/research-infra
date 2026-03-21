"""Tests for autoresearch module."""

from pathlib import Path

from research_infra.autoresearch import (
    discover_autoresearch_projects,
    generate_experiment_py,
    generate_program_md,
    load_schedule,
    next_project,
    save_schedule,
    scaffold_autoresearch,
    show_schedule,
)


class TestGenerateProgramMd:
    def test_known_project(self):
        md = generate_program_md("hgx", Path("/fake"))
        assert "hypergraph" in md.lower()
        assert "ho_advantage" in md
        assert "NEVER STOP" in md

    def test_unknown_project(self):
        md = generate_program_md("unknown-project", Path("/fake"))
        assert "Autonomous research loop for unknown-project" in md
        assert "NEVER STOP" in md

    def test_custom_goal(self):
        md = generate_program_md("hgx", Path("/fake"), custom_goal="Custom goal here.")
        assert "Custom goal here." in md

    def test_all_known_projects_have_templates(self):
        from research_infra.autoresearch import RESEARCH_TEMPLATES

        for name in RESEARCH_TEMPLATES:
            md = generate_program_md(name, Path("/fake"))
            assert len(md) > 200


class TestGenerateExperimentPy:
    def test_generates_valid_python(self):
        code = generate_experiment_py("test-project")
        compile(code, "<test>", "exec")  # Should not raise SyntaxError.

    def test_contains_result_output(self):
        code = generate_experiment_py("test-project")
        assert "RESULT|" in code


class TestScaffoldAutoresearch:
    def test_creates_files(self, tmp_project: Path):
        scaffold_autoresearch(tmp_project)
        assert (tmp_project / "autoresearch" / "program.md").exists()
        assert (tmp_project / "autoresearch" / "experiment.py").exists()
        assert (tmp_project / "autoresearch" / "results.tsv").exists()

    def test_skips_existing(self, tmp_project: Path):
        scaffold_autoresearch(tmp_project)
        # Write custom content.
        program = tmp_project / "autoresearch" / "program.md"
        program.write_text("Custom program.")
        # Re-scaffold should not overwrite.
        scaffold_autoresearch(tmp_project)
        assert program.read_text() == "Custom program."


class TestScheduler:
    def test_discover_projects(self, tmp_path: Path):
        # Create two projects with autoresearch.
        for name in ["proj_a", "proj_b"]:
            d = tmp_path / name / "autoresearch"
            d.mkdir(parents=True)
            (d / "program.md").write_text("# Test")
        # One without autoresearch.
        (tmp_path / "proj_c").mkdir()

        projects = discover_autoresearch_projects(tmp_path)
        assert len(projects) == 2
        names = {p.name for p in projects}
        assert names == {"proj_a", "proj_b"}

    def test_round_robin(self, tmp_path: Path):
        for name in ["a", "b", "c"]:
            d = tmp_path / name / "autoresearch"
            d.mkdir(parents=True)
            (d / "program.md").write_text("# Test")

        schedule_file = tmp_path / "rr_schedule.json"

        from research_infra import autoresearch

        orig_file = autoresearch.SCHEDULE_FILE
        autoresearch.SCHEDULE_FILE = schedule_file
        try:
            # File doesn't exist yet — load_schedule returns fresh state.
            p1 = next_project(tmp_path)
            p2 = next_project(tmp_path)
            p3 = next_project(tmp_path)
            p4 = next_project(tmp_path)  # Should wrap around.

            names = [p.name for p in [p1, p2, p3, p4]]
            # Should cycle through a, b, c, a in order.
            assert names == ["a", "b", "c", "a"]
        finally:
            autoresearch.SCHEDULE_FILE = orig_file

    def test_load_save_schedule(self, tmp_path: Path):
        schedule_file = tmp_path / "schedule.json"
        state = {"last_index": 2, "history": [{"project": "test", "timestamp": "2026-03-20"}]}
        save_schedule(state, schedule_file)
        loaded = load_schedule(schedule_file)
        assert loaded["last_index"] == 2
        assert len(loaded["history"]) == 1

    def test_show_schedule(self, tmp_path: Path, capsys):
        for name in ["proj_x", "proj_y"]:
            d = tmp_path / name / "autoresearch"
            d.mkdir(parents=True)
            (d / "program.md").write_text("# Test")

        show_schedule(tmp_path)
        captured = capsys.readouterr()
        assert "proj_x" in captured.out
        assert "proj_y" in captured.out
