from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

WORKFLOW_PATH = Path(".github/workflows/ci.yml")


def _load_workflow() -> dict[str, Any]:
    with WORKFLOW_PATH.open(encoding="utf-8") as workflow_file:
        loaded = yaml.safe_load(workflow_file)
    assert isinstance(loaded, dict)
    return loaded


def test_github_actions_workflow_triggers_on_push_and_main_pr() -> None:
    workflow = _load_workflow()

    triggers = workflow["on"]

    assert "push" in triggers
    assert "pull_request" in triggers
    assert triggers["pull_request"]["branches"] == ["main"]


def test_github_actions_workflow_defines_test_lint_and_typecheck_jobs() -> None:
    workflow = _load_workflow()

    jobs = workflow["jobs"]

    assert {"test", "lint", "typecheck"} <= set(jobs)
    for job_name in ["test", "lint", "typecheck"]:
        job = jobs[job_name]
        assert job["runs-on"] == "ubuntu-latest"
        assert any(step.get("uses") == "actions/checkout@v4" for step in job["steps"])
        assert any(
            step.get("uses") == "actions/setup-python@v5"
            and step.get("with", {}).get("python-version") == "3.11"
            and step.get("with", {}).get("cache") == "pip"
            for step in job["steps"]
        )


def test_github_actions_workflow_runs_project_ci_commands() -> None:
    workflow = _load_workflow()
    jobs = workflow["jobs"]

    commands_by_job = {
        job_name: "\n".join(
            str(step["run"]) for step in jobs[job_name]["steps"] if "run" in step
        )
        for job_name in ["test", "lint", "typecheck"]
    }

    assert "python -m pytest tests/ -v" in commands_by_job["test"]
    assert "python -m ruff check harness/ tests/" in commands_by_job["lint"]
    assert "python -m mypy harness/" in commands_by_job["typecheck"]
