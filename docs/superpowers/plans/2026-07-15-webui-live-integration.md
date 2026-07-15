# WebUI Live Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect local `harness run --web` to the real same-process AgentLoop with recoverable HITL, while making Docker/Render a read-only public replay demo.

**Architecture:** Add a shared typed run-event model, event-backed thread-safe WebUI state, an AgentLoop event/approval adapter, and a local Uvicorn runner. Keep Render safe by making the module-level app demo-only.

**Tech Stack:** Python 3.11, FastAPI, Uvicorn, plain HTML/CSS/JavaScript, pytest, ruff, mypy.

## Global Constraints

- Use `.\.venv\Scripts\python.exe` via `$PY`; do not use bare `python`, `pytest`, `pip`, `ruff`, or `mypy` locally.
- Do not call a real LLM or request/use/print/commit real API keys.
- Do not modify `REFLECTION.md`.
- Keep `harness run "task"` backward compatible and terminal-only.
- `harness run "task" --web` binds only `127.0.0.1:8000`.
- Docker/Render default to `PUBLIC DEMO MODE`; no live local workspace or real AgentLoop.
- Use TDD for every behavior change: failing test, verify red, minimal implementation, verify green, commit.
- Stop before push.

---

### Task 1: Shared Run Event Semantics

**Files:**
- Create: `harness/run_events.py`
- Test: `tests/unit/test_run_events.py`

**Interfaces:**
- Produces: `RunEvent`, `RunEventType`, `RunPhase`, `TestStatus`, `HITLDecision`, `sanitize_event_metadata`.
- Consumed by: WebUI state, AgentLoop adapter, demo replay.

- [ ] Write failing tests for JSON serialization, timestamp format, deterministic event ordering fields, state transitions, and secret/path redaction.
- [ ] Run: `& $PY -m pytest tests/unit/test_run_events.py -v`
- [ ] Implement typed enums/dataclass and sanitizer.
- [ ] Run: `& $PY -m pytest tests/unit/test_run_events.py -v`
- [ ] Commit: `test/feat(T30): add shared webui run events`.

### Task 2: Event-backed WebUIState

**Files:**
- Create/Modify: `webui/state.py`, `webui/websocket.py`, `webui/app.py`
- Test: `tests/unit/test_webui_state.py`, `tests/unit/test_webui_app.py`

**Interfaces:**
- Consumes `RunEvent`.
- Produces `WebUIState.publish(event)`, `snapshot()`, `subscribe()`, `timeline`.

- [ ] Write failing tests for initial idle/not-started state, transitions, timeline, snapshot-first WebSocket behavior, no raw `unknown/none/null`, and concurrent publish safety.
- [ ] Run targeted WebUI tests.
- [ ] Implement thread-safe state and keep compatibility exports from `webui.app`.
- [ ] Run targeted WebUI tests.
- [ ] Commit: `feat(T30): add event-backed webui state`.

### Task 3: Recoverable Approval Broker

**Files:**
- Create: `harness/approval.py`
- Modify: `webui/app.py`, `webui/state.py`
- Test: `tests/unit/test_approval_broker.py`, `tests/unit/test_webui_app.py`

**Interfaces:**
- Produces `ApprovalBroker.request`, `resolve`, `cancel_all`, `pending`.
- Web live mode maps `/api/hitl/{request_id}` to broker decisions.

- [ ] Write failing tests for approve once, deny feedback, duplicate decision rejection, wrong id rejection, cancellation, and demo mutation 403.
- [ ] Run broker/WebUI targeted tests.
- [ ] Implement broker and app endpoint mode separation.
- [ ] Run broker/WebUI targeted tests.
- [ ] Commit: `feat(T30): add recoverable web hitl broker`.

### Task 4: AgentLoop Event and HITL Adapter

**Files:**
- Modify: `harness/agent_loop.py`
- Test: `tests/unit/test_agent_loop.py`, `tests/mock/test_agent_loop_mock.py`

**Interfaces:**
- Consumes `RunEventSink` and `ApprovalBroker`.
- Publishes task/round/model/tool/test/hitl/finish events.

- [ ] Write failing tests proving events are emitted in order and web deny continues to the next round without `StopReason.HITL_DENIED`.
- [ ] Write approve test proving dangerous tool executes exactly once after approval.
- [ ] Run AgentLoop targeted tests.
- [ ] Implement minimal event sink and recoverable HITL path.
- [ ] Run AgentLoop targeted tests.
- [ ] Commit: `feat(T30): publish agent loop lifecycle events`.

### Task 5: CLI `--web` and Local Server Lifecycle

**Files:**
- Modify: `harness/cli.py`
- Create: `webui/local_runner.py`
- Test: `tests/unit/test_cli.py`, `tests/unit/test_local_web_runner.py`

**Interfaces:**
- Adds CLI flag `--web`.
- Produces `run_with_local_webui(requirement, config, api_key, make_agent_loop)`.

- [ ] Write failing CLI tests for no regression without `--web`, `--web` parsing, fixed host/port, no public host option, browser opens only after readiness, port conflict failure, browser failure warning, and shutdown behavior with fakes.
- [ ] Run CLI/local runner targeted tests.
- [ ] Implement local runner with injectable server/browser/wait dependencies for tests.
- [ ] Run CLI/local runner targeted tests.
- [ ] Commit: `feat(T30): add harness run web mode`.

### Task 6: Frontend Live Rendering

**Files:**
- Modify: `webui/static/index.html`, `webui/static/app.js`, `webui/static/style.css`
- Test: `tests/unit/test_webui_app.py`

**Interfaces:**
- Consumes snapshot/timeline/incremental event messages.
- Live mode enables HITL decisions only when awaiting approval.

- [ ] Write failing tests for required DOM ids/text, no raw null/none/unknown display, local live badge, timeline/current event rendering hooks, reconnect wording, accessible buttons.
- [ ] Run WebUI frontend tests.
- [ ] Implement rendering while preserving existing style.
- [ ] Run WebUI frontend tests.
- [ ] Commit: `feat(T30): render live agent state in webui`.

### Task 7: Public Demo Replay Mode

**Files:**
- Create: `webui/demo.py`
- Modify: `webui/app.py`, `webui/static/index.html`, `webui/static/app.js`, `webui/static/style.css`, `.github/workflows/ci.yml`, `tests/smoke/fresh_install_smoke.py`
- Test: `tests/unit/test_webui_demo.py`, `tests/unit/test_webui_app.py`, `tests/unit/test_github_actions_ci.py`

**Interfaces:**
- Produces `DEMO_STEP_MS = 900` and deterministic demo event list.
- Module-level `app` is demo mode.

- [ ] Write failing tests for `PUBLIC DEMO MODE`, read-only text, full deterministic sequence, per-client replay start, playback controls, disabled real HITL mutation, no AgentLoop/ToolExecutor use, CI root marker.
- [ ] Run demo/CI targeted tests.
- [ ] Implement demo replay source and frontend playback.
- [ ] Run demo/CI targeted tests.
- [ ] Commit: `feat(T30): add public demo replay mode`.

### Task 8: Docs, Packaging, and Final Verification

**Files:**
- Modify: `README.md`, `PLAN.md`, `REQUIREMENTS_CHECKLIST.md`, `AGENT_LOG.md`, `pyproject.toml` if package data changes.
- Test: `tests/unit/test_distribution.py`, `tests/unit/test_readme.py`, `tests/smoke/fresh_install_smoke.py`

**Interfaces:**
- README documents terminal mode, local `--web`, Render read-only demo, HITL semantics, Ctrl+C lifecycle, and safety boundaries.

- [ ] Write/update failing docs/package tests for new static/demo assets and README claims.
- [ ] Run docs/package targeted tests.
- [ ] Update docs and package data.
- [ ] Run required final commands:
  - `& $PY -m pip install -e .`
  - `& $PY -m pip check`
  - `& $PY -m pytest tests -q`
  - `& $PY -m ruff check harness webui demo tests`
  - `& $PY -m mypy harness webui demo`
  - `& $PY -m demo.run_demo`
  - `& $PY -m build`
  - `& $PY -m twine check dist/*`
- [ ] Run fresh wheel install smoke and demo HTTP smoke.
- [ ] Commit: `docs(T30): record webui live integration evidence`.

