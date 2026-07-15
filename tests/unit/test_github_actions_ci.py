from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, cast

import yaml

WORKFLOW_PATH = Path(".github/workflows/ci.yml")
PYPROJECT_PATH = Path("pyproject.toml")


def _load_workflow() -> dict[Any, Any]:
    with WORKFLOW_PATH.open(encoding="utf-8") as workflow_file:
        loaded = yaml.safe_load(workflow_file)
    assert isinstance(loaded, dict)
    return loaded


def test_github_actions_workflow_triggers_on_push_and_main_pr() -> None:
    workflow = _load_workflow()

    triggers = cast(dict[str, Any], workflow.get("on", workflow.get(True)))

    assert "push" in triggers
    assert triggers["push"] is None
    assert "pull_request" in triggers
    assert triggers["pull_request"]["branches"] == ["main"]


def test_github_actions_workflow_defines_test_lint_and_typecheck_jobs() -> None:
    workflow = _load_workflow()

    jobs = workflow["jobs"]

    assert {"test", "lint", "typecheck"} <= set(jobs)
    for job_name in ["test", "lint", "typecheck"]:
        job = jobs[job_name]
        assert job["runs-on"] == "${{ matrix.os }}"
        assert job["strategy"]["fail-fast"] is False
        assert job["strategy"]["matrix"]["os"] == ["windows-latest", "ubuntu-latest"]
        assert job["strategy"]["matrix"]["python-version"] == ["3.11"]
        assert any(step.get("uses") == "actions/checkout@v4" for step in job["steps"])
        assert any(
            step.get("uses") == "actions/setup-python@v5"
            and step.get("with", {}).get("python-version") == "${{ matrix.python-version }}"
            and step.get("with", {}).get("cache") == "pip"
            and step.get("with", {}).get("cache-dependency-path") == "pyproject.toml"
            for step in job["steps"]
        )


def test_github_actions_workflow_builds_docker_image_without_publishing() -> None:
    workflow = _load_workflow()

    docker_job = workflow["jobs"]["docker-build"]

    assert docker_job["name"] == "Docker image build"
    assert docker_job["runs-on"] == "ubuntu-latest"
    assert any(step.get("uses") == "actions/checkout@v4" for step in docker_job["steps"])
    build_steps = [
        step for step in docker_job["steps"] if step.get("uses") == "docker/build-push-action@v6"
    ]
    assert len(build_steps) == 1
    build_config = build_steps[0]["with"]
    assert build_config["context"] == "."
    assert build_config["file"] == "./Dockerfile"
    assert build_config["load"] is True
    assert build_config["push"] is False
    assert build_config["tags"] == "coding-agent-harness:ci"

    docker_commands = "\n".join(
        str(step["run"]) for step in docker_job["steps"] if "run" in step
    )
    assert "docker run --rm -d --name coding-agent-harness-ci -p 8000:8000" in docker_commands
    assert "for path in / /static/style.css /static/app.js" in docker_commands
    assert "for attempt in 1 2 3 4 5" in docker_commands
    assert 'curl --fail --silent --show-error "$url"' in docker_commands
    assert "Waiting for $url (attempt $attempt/30)" in docker_commands
    assert "docker ps -a" in docker_commands
    assert "docker logs --tail 50 coding-agent-harness-ci" in docker_commands
    assert "docker inspect coding-agent-harness-ci" in docker_commands
    assert "Docker WebUI did not become ready at $url" in docker_commands
    assert "docker stop coding-agent-harness-ci" in docker_commands


def test_github_actions_workflow_builds_and_uploads_python_distributions() -> None:
    workflow = _load_workflow()

    package_job = workflow["jobs"]["package"]

    assert package_job["name"] == "Build package artifacts"
    assert package_job["runs-on"] == "ubuntu-latest"
    assert any(step.get("uses") == "actions/checkout@v4" for step in package_job["steps"])
    assert any(
        step.get("uses") == "actions/setup-python@v5"
        and step.get("with", {}).get("python-version") == "3.11"
        for step in package_job["steps"]
    )
    package_commands = "\n".join(
        str(step["run"]) for step in package_job["steps"] if "run" in step
    )
    assert "python -m pip install build twine" in package_commands
    assert "python -m build" in package_commands
    assert "python -m twine check dist/*" in package_commands
    upload_steps = [
        step for step in package_job["steps"] if step.get("uses") == "actions/upload-artifact@v4"
    ]
    assert len(upload_steps) == 1
    assert upload_steps[0]["with"]["name"] == "python-distributions"
    assert upload_steps[0]["with"]["path"] == "dist/*"


def test_github_actions_workflow_runs_project_ci_commands() -> None:
    workflow = _load_workflow()
    jobs = workflow["jobs"]

    commands_by_job = {
        job_name: "\n".join(
            str(step["run"]) for step in jobs[job_name]["steps"] if "run" in step
        )
        for job_name in ["test", "lint", "typecheck"]
    }

    for job_name in ["test", "lint", "typecheck"]:
        assert "python -m pip install --upgrade pip" in commands_by_job[job_name]
        assert "python -m pip install -e ." in commands_by_job[job_name]
        assert "python -m pip check" in commands_by_job[job_name]
        assert "make" not in commands_by_job[job_name]
        assert "continue-on-error" not in commands_by_job[job_name]
        assert "|| true" not in commands_by_job[job_name]

    assert "python -m pytest tests/ -q" in commands_by_job["test"]
    assert "python -m ruff check harness/ webui/ demo/ tests/" in commands_by_job["lint"]
    assert "python -m mypy harness/ webui/ demo/" in commands_by_job["typecheck"]


def test_github_actions_workflow_uses_portable_runner_commands() -> None:
    workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")

    forbidden_fragments = [
        "continue-on-error: true",
        "|| true",
        "make test",
        "make lint",
        "make typecheck",
        "python - <<",
        "/bin/sh",
        "bash",
        "cp ",
        "touch ",
        "C:\\Users\\",
        "/home/",
    ]

    for fragment in forbidden_fragments:
        assert fragment not in workflow_text


def test_project_declares_package_discovery_for_editable_ci_install() -> None:
    with PYPROJECT_PATH.open("rb") as pyproject_file:
        pyproject = tomllib.load(pyproject_file)

    package_includes = pyproject["tool"]["setuptools"]["packages"]["find"]["include"]

    assert set(package_includes) == {"harness*", "webui*", "demo*"}
