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

Python package install, after the package is available from an index:

```powershell
pip install coding-agent-harness
```

Local checkout install for development or release verification:

```powershell
python -m pip install -e .
python -m pip check
```

Docker image install, after an image has been published to your registry:

```powershell
docker pull <registry>/coding-agent-harness
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

Python 3.11 or newer is required. The packaged console script is `harness`.

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

Run the harness against a natural-language requirement:

```powershell
harness run "add a slugify helper with tests"
```

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

Then open `http://127.0.0.1:8000/`.

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

Live deployment pending: this repository contains the Render configuration, but a
public Render service URL has not been verified in this stage.

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

Docker commands require a local Docker runtime. Container image publishing and cloud
deployment are separate release steps.

The README intentionally does not include a Render service URL or final acceptance
results. Those belong to the later deployment and final acceptance tasks.
