# T30 WebUI Live Integration Design

## Goal

Implement two strictly separated WebUI modes:

- Local live mode for `harness run "task" --web`, connected to the same-process
  `AgentLoop` and a recoverable HITL approval flow.
- Public demo mode for Docker/Render, a read-only deterministic replay that never
  connects to a local workspace, real tools, real HITL broker, real AgentLoop, or
  real LLM.

## Binding Constraints

- Primary local platform: Windows 11, PowerShell, Python 3.11.
- Keep compatibility with Ubuntu GitHub Actions.
- Use the existing FastAPI/Uvicorn/static HTML/CSS/JS stack. Do not add React,
  Vue, a database, accounts, upload flows, remote execution, or a web terminal.
- Do not call real DeepSeek/LLM APIs in tests or demo mode.
- Do not request, print, store, or commit real API keys/tokens/passwords.
- Do not modify `REFLECTION.md`.
- Docker and Render default to public demo mode, not live mode.
- `harness run "task"` remains terminal-only and backward compatible.
- `harness run "task" --web` binds only `127.0.0.1:8000`; no public host option.

## Architecture

### Shared Event Model

Create a typed event model in `harness/run_events.py`:

- `RunEvent`
- `RunPhase`
- `RunEventType`
- `TestStatus`
- `HITLDecision`
- `sanitize_event_metadata`

The event schema is JSON-serializable and covers:

- `task_started`
- `round_started`
- `model_response`
- `tool_requested`
- `tool_completed`
- `tests_started`
- `tests_completed`
- `hitl_requested`
- `hitl_resolved`
- `run_finished`

The state transition rules are centralized in `webui/state.py`. The API uses
`None` for absent fields; the browser renders absent values as "Not available"
or hides them. It must not display raw `unknown`, `none`, `null`, or `undefined`.

### WebUI State and Transport

Replace the legacy string-status `WebUIState` with a thread-safe event-backed
state:

- current snapshot
- full timeline
- pending HITL requests
- subscription queues
- deterministic event order
- sanitized JSON output

WebSocket clients receive a snapshot/timeline message first, then incremental
events. Updates may come from an `AgentLoop` thread while FastAPI serves HTTP and
WebSocket requests.

### AgentLoop Adapter

`AgentLoop` accepts optional lightweight dependencies:

- `event_sink: RunEventSink | None`
- `approval_broker: ApprovalBroker | None`

The loop remains independent of FastAPI. It publishes lifecycle events around
LLM responses, tool requests/results, tests, HITL, and finish. Metadata is
sanitized before WebUI exposure.

### Recoverable HITL

Create `harness/approval.py`:

- `ApprovalBroker.request(action, timeout)` creates a request and blocks until a
  decision or cancellation.
- `resolve(request_id, decision)` permits exactly one decision.
- approve returns a signal that lets `AgentLoop` execute the original dangerous
  tool once.
- deny returns structured feedback:
  - `status = denied_by_user`
  - `executed = false`
  - `message = "The user denied this operation. Choose a safe alternative."`

In web live mode, deny does not produce `StopReason.HITL_DENIED`; the agent sees
feedback and can choose a safe alternative.

### Local Web Runner

Create `webui/local_runner.py` to start Uvicorn in-process for `--web`:

- host fixed to `127.0.0.1`
- port fixed to `8000`
- fail fast with a clear error if port 8000 is occupied
- wait for HTTP readiness before `webbrowser.open`
- browser open failures print a warning and manual URL but do not stop the agent
- after the task finishes, keep WebUI running until Ctrl+C
- Ctrl+C cancels/cleans up the server and broker without leaving the port busy

### Public Demo Mode

The module-level FastAPI app remains safe for Docker/Render:

```python
app = create_app(mode="demo")
```

Demo mode:

- displays `PUBLIC DEMO MODE`
- states it is read-only replay and no live agent/local workspace is connected
- provides deterministic replay events using the same `RunEvent` schema
- has `DEMO_STEP_MS = 900` in one place
- supports browser-local Pause, Resume, Replay, progress, current event, and
  full timeline
- returns 403/404/405 for real HITL mutation attempts

### Frontend

Keep plain HTML/CSS/JS. Render:

- mode badge
- task requirement
- Phase, Status, Round, Tests, Stop reason
- current event details
- timeline
- live HITL panel only when live and awaiting approval
- demo playback controls only in demo mode
- reconnect state without marking the run failed

## Non-goals

- public remote execution
- account system
- database
- cloud task queue
- file editor
- API key entry page
- Render live mode
- real LLM network tests

