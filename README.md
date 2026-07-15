# Coding Agent Harness

## 项目简介

Coding Agent Harness is a Python 3.11 TDD-focused coding-agent harness. It turns a
natural-language requirement into a guarded red-green-refactor loop: the harness asks an
LLM for tool calls, dispatches those calls through deterministic local tools, parses test
feedback, injects structured failure guidance, records rounds, and stops on PASS,
MAX_ROUNDS, STUCK, or HITL_DENIED.

The core idea is that the important engineering mechanisms are code, not prompts:
tool dispatch, feedback parsing, failure classification, memory lookup, path boundaries,
dangerous command detection, and HITL state transitions are all implemented in this
repository and covered by deterministic tests with mock or stub LLMs.

## 安装

The currently verified Python runtime is Python 3.11. The package metadata and CI
intentionally limit formal support to Python 3.11 until newer versions are tested.

Python package install, after the package is available from an index. Current project
state: the package has not been published to PyPI, so use the source or wheel paths
below for verified installation:

```powershell
pip install coding-agent-harness
```

Path A: install from a GitHub source checkout on Windows PowerShell:

```powershell
git clone https://github.com/wyksy123-lang/coding-agent-harness.git
cd coding-agent-harness
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\harness.exe --help
.\.venv\Scripts\python.exe -m demo.run_demo
```

Path A: install from a GitHub source checkout on Linux or macOS:

```bash
git clone https://github.com/wyksy123-lang/coding-agent-harness.git
cd coding-agent-harness
python3.11 -m venv .venv
./.venv/bin/python -m pip install -e .
./.venv/bin/python -m pip check
./.venv/bin/harness --help
./.venv/bin/python -m demo.run_demo
```

For a source checkout, install the release tooling before building local artifacts:

```powershell
python -m pip install build twine
```

Then build and check the current release artifacts locally:

```powershell
python -m build
python -m twine check dist/*
```

Path B: install a built wheel into a fresh Python 3.11 environment:

```bash
python3.11 -m venv .venv
python -m pip install <wheel>
harness --help
python -m demo.run_demo
```

Docker image install, after an image has been published to your registry. Current project
state: no public Docker image has been published yet:

```powershell
docker pull <registry>/coding-agent-harness
```

The packaged console script is `harness`.

## 运行

Create a project configuration from the example:

```powershell
Copy-Item harness.yaml.example harness.yaml
```

Configure the DeepSeek API key with the credential manager:

```powershell
harness key setup
harness key status
harness key update
harness key clear
```

Installation, package checks, the mock mechanism demo, and the WebUI smoke checks do not
need an API key. A real `harness run` that calls DeepSeek does require the user to
configure their own valid key with `harness key setup`. Do not put API keys in the
repository, command-line arguments, Docker image layers, or shell history.

DeepSeek runs use the OpenAI-compatible Chat Completions tool protocol. Tool schemas
are sent as `type=function` entries, each assistant `tool_calls` response is followed
by matching `role=tool` results before the next model request, and provider or
malformed-response failures stop as `LLM_ERROR` instead of producing a traceback. The
WebUI timeline shows model-request, model-error, tool-request, tool-completed, test,
HITL, and finish events with redacted failure details.

Run the harness against a natural-language requirement:

```powershell
harness run "add a slugify helper with tests"
```

Run the same real AgentLoop with the local WebUI attached:

```powershell
harness run "add a slugify helper with tests" --web
```

The local WebUI binds only to `http://127.0.0.1:8000/`. It streams the live
AgentLoop phase, round, test status, event timeline, and recoverable HITL approval
requests from the same process. This is the recommended review path for a teacher or
reviewer who pulls the repository locally; no public demo service is required for this
mode.

Use a non-default configuration path when needed:

```powershell
harness run "add a slugify helper with tests" --config harness.yaml
```

Run the deterministic mechanism demo:

```powershell
python -m demo.run_demo
```

The WebUI backend is served by FastAPI and Uvicorn:

```powershell
python -m uvicorn webui.app:app --host 127.0.0.1 --port 8000
```

Then open `http://127.0.0.1:8000/`. This direct Uvicorn command serves the WebUI
shell; use `harness run ... --web` when you want the UI attached to a real harness run.

## 分发命令

Build the Python distribution:

```powershell
python -m build
python -m twine check dist/*
```

Install the built wheel into a fresh environment:

```powershell
python -m venv .dist-test-venv
.\.dist-test-venv\Scripts\python.exe -m pip install dist\coding_agent_harness-0.1.0-py3-none-any.whl
.\.dist-test-venv\Scripts\harness.exe --help
```

Build the Docker image:

```powershell
docker build -t coding-agent-harness .
```

Run the Docker WebUI container:

```powershell
docker run -p 8000:8000 coding-agent-harness
```

For a workspace-mounted run on Windows PowerShell:

```powershell
docker run -p 8000:8000 -v ${PWD}\workspace:/app/workspace coding-agent-harness
```

For a workspace-mounted run on Linux or macOS shells:

```bash
docker run -p 8000:8000 -v $(pwd)/workspace:/app/workspace coding-agent-harness
```

Docker must be installed and available on `PATH` for the Docker commands.

## Render deployment

`render.yaml` defines a Render Docker Web Service that builds from the repository
root with `./Dockerfile`. The service uses the free plan, checks `/` as its health
check path, and starts deployment only after repository checks pass.

The container runs Uvicorn on `0.0.0.0` and reads Render's `PORT` environment
variable with a local fallback to `8000`. The `/` health check is the WebUI index
route served by FastAPI.

Set `DEEPSEEK_API_KEY` in Render as a secret environment variable. The blueprint
marks it with `sync: false`; no real API key, token, or password is stored in this
repository or baked into the image. Render prompts for `sync: false` values during
initial Blueprint creation; for later syncs or existing services, keep the secret
configured manually in Render.

CI/CD flow: push a task branch, wait for GitHub Actions checks to pass, merge to
`main`, then let Render deploy the checked revision from the Dockerfile. Free Render
services may sleep when idle and need a browser refresh or request to wake.

Live deployment verified:

- URL: https://coding-agent-harness-zq0k.onrender.com/
- checked_at_utc=2026-07-15T03:05:17Z
- GET / -> 200, `text/html`, length 1647
- GET /static/style.css -> 200, `text/css`, length 1453
- GET /static/app.js -> 200, `application/javascript`, length 6538
- The root page contained `Coding Agent Harness`, `HITL`, `/static/style.css`, and
  `/static/app.js`.
- secret_pattern_match=False for the checked response bodies.

## 目录结构

```text
.
|-- harness/
|   |-- agent_loop.py
|   |-- cli.py
|   |-- config/
|   |-- credentials/
|   |-- feedback/
|   |-- governance/
|   |-- llm/
|   |-- memory/
|   `-- tools/
|-- webui/
|   |-- app.py
|   |-- websocket.py
|   `-- static/
|-- demo/
|   `-- run_demo.py
|-- tests/
|   |-- unit/
|   |-- mock/
|   `-- fixtures/
|-- Dockerfile
|-- harness.yaml.example
|-- pyproject.toml
|-- SPEC.md
|-- PLAN.md
|-- REQUIREMENTS_CHECKLIST.md
`-- AGENT_LOG.md
```

## 安全边界

Credential management prefers OS keyring storage. If keyring is unavailable, the
credential manager can fall back to `.env`; that fallback is plaintext and should be used
only with normal local-file precautions. Do not commit `.env`, real API keys, GitHub
tokens, passwords, private keys, or provider-local auth files.

`harness key status` prints a masked value and does not echo the plaintext key.
`harness key setup` and `harness key update` use hidden input.

File operations are checked by `PathGuard`, which keeps read, write, and list operations
inside the configured `target_directory`. Command execution is checked by `CommandGuard`,
which marks dangerous patterns such as `rm -rf`, `git push`, `sudo`, `curl` or `wget`,
and `docker` as pending. Pending actions enter the `HITL` state machine and require an
explicit approve, deny, or timeout decision.

Deterministic tests must use mock or stub LLMs and mocked transports. They must not call a
real LLM, real network service, or real credential during core unit and mock integration
tests.

## 第三方许可证

Direct runtime and development dependencies are declared in `pyproject.toml`.
Check installed package metadata before redistribution, especially for transitive
dependencies. The direct dependencies currently use permissive licenses:

| Package | Typical license |
|---|---|
| httpx | BSD-3-Clause |
| pyyaml | MIT |
| keyring | MIT |
| fastapi | MIT |
| uvicorn | BSD-3-Clause |
| websockets | BSD-3-Clause |
| pytest | MIT |
| pytest-json-report | MIT |
| ruff | MIT |
| mypy | MIT |

## 已知限制

The default real LLM client targets DeepSeek through an OpenAI-compatible chat
completions shape. Real LLM runs require a configured API key and network access.
If `harness key status` reports `not configured`, controlled real DeepSeek smoke
checks are skipped rather than simulated.

Docker commands require a local Docker runtime. Container image publishing and cloud
deployment are separate release steps.

The README includes T28 Render deployment evidence, but final acceptance results
remain separate and belong to the final acceptance task.
