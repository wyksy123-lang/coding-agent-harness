# T31 DeepSeek Contract And WebUI Errors Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development to implement this plan. The repository task remains T31 only; the sections below are internal TDD slices for one task branch.

**Goal:** Make real DeepSeek tool calling conform to Chat Completions, handle malformed/provider errors as structured failures, and show failed runs clearly in the local WebUI timeline.

**Architecture:** Keep tool parameter schemas on each `Tool`, add a centralized Chat Completions serializer at the registry boundary, and have `AgentLoop` persist assistant `tool_calls` plus `role=tool` results before the next model request. `DeepSeekClient` owns provider request/response classification; `AgentLoop` converts terminal LLM exceptions into `model_error` and one `run_finished`. WebUI state remains event-driven and the frontend renders localized Chinese labels from safe snapshot/timeline payloads.

**Tech Stack:** Python 3.11, httpx MockTransport tests, pytest, FastAPI TestClient, vanilla HTML/CSS/JS WebUI.

## Global Constraints

- Work only on T31 on branch `codex/task/T31-deepseek-contract-webui-errors`.
- Do not modify `REFLECTION.md`.
- Do not request, print, store, or commit real API keys.
- Deterministic tests must use mock/stub LLMs and mocked transports.
- Stop before push or PR creation.

---

### Slice 1: Tool Schema Contract

**Files:**
- Modify: `harness/tools/base.py`
- Test: `tests/unit/test_tool_registry.py`
- Related: `harness/cli.py`

**Steps:**
- [ ] Add failing tests that `ToolRegistry.get_llm_schemas()` returns six Chat Completions function tools with non-empty names/descriptions, object parameters, JSON-serializable bodies, and enabled-tools filtering.
- [ ] Run: `& $PY -m pytest tests/unit/test_tool_registry.py tests/unit/test_cli.py -q`
- [ ] Implement `Tool.description` defaults and `tool_to_chat_completion_schema(tool)`.
- [ ] Keep `get_schemas()` as the parameter-schema API for existing tests, and use `get_llm_schemas()` for model requests.

### Slice 2: Message Protocol

**Files:**
- Modify: `harness/agent_loop.py`
- Test: `tests/unit/test_agent_loop.py`

**Steps:**
- [ ] Add failing tests proving the second LLM request includes the assistant message with original `tool_calls` followed by `role=tool` result messages with matching `tool_call_id`.
- [ ] Include unknown-tool and tool-error feedback as structured tool results instead of plain user feedback.
- [ ] Run: `& $PY -m pytest tests/unit/test_agent_loop.py -q`
- [ ] Implement helper serializers for assistant tool-call messages and JSON tool-result content.

### Slice 3: DeepSeek Response And HTTP Errors

**Files:**
- Modify: `harness/llm/base.py`
- Modify: `harness/llm/deepseek.py`
- Test: `tests/unit/test_llm_deepseek.py`

**Steps:**
- [ ] Add failing tests for malformed JSON, missing choices/message/tool fields, invalid arguments JSON, null content, multiple tool calls, non-object JSON, and unknown finish reason.
- [ ] Add failing tests for 400/401/402/403/422 single-attempt errors and 408/429/500/502/503/504/timeout retries.
- [ ] Run: `& $PY -m pytest tests/unit/test_llm_deepseek.py -q`
- [ ] Implement `LLMError`, `LLMRequestError`, and `LLMResponseError` with `kind`, `safe_message`, `status_code`, `retryable`, and `provider`.

### Slice 4: AgentLoop Failure Boundary

**Files:**
- Modify: `harness/models.py`
- Modify: `harness/run_events.py`
- Modify: `harness/agent_loop.py`
- Modify: `harness/cli.py`
- Test: `tests/unit/test_run_events.py`
- Test: `tests/unit/test_agent_loop.py`
- Test: `tests/unit/test_cli.py`

**Steps:**
- [ ] Add failing tests for event order `task_started`, `round_started`, `model_requested`, `model_error`, `run_finished` on an LLM API error.
- [ ] Assert final result is `StopReason.LLM_ERROR`, phase/status failed, `failure_type` is `LLM_API_ERROR` or `LLM_RESPONSE_ERROR`, and CLI returns non-zero without traceback.
- [ ] Run: `& $PY -m pytest tests/unit/test_agent_loop.py tests/unit/test_run_events.py tests/unit/test_cli.py -q`
- [ ] Implement one terminal failure path that emits exactly one `run_finished`.

### Slice 5: WebUI State Semantics

**Files:**
- Modify: `webui/state.py`
- Modify: `harness/run_events.py`
- Test: `tests/unit/test_webui_state.py`
- Test: `tests/unit/test_webui_app.py`

**Steps:**
- [ ] Add failing tests for initial `test_status=not_started`, passed/failed counts as absent until tests run, failed snapshot fields, and WebSocket reconnect retaining full timeline.
- [ ] Run: `& $PY -m pytest tests/unit/test_webui_state.py tests/unit/test_webui_app.py -q`
- [ ] Update snapshot reducer/payload to carry failure type/details safely.

### Slice 6: Chinese Frontend And Grouped Timeline

**Files:**
- Modify: `webui/static/index.html`
- Modify: `webui/static/app.js`
- Modify: `webui/static/style.css`
- Test: `tests/unit/test_webui_app.py`

**Steps:**
- [ ] Add failing static tests for `<html lang="zh-CN">`, required Chinese labels, no hard-coded English placeholders, `textContent` rendering, round dividers, task-end divider, event type mappings, all-event rendering, and latest-event highlight.
- [ ] Run: `& $PY -m pytest tests/unit/test_webui_app.py -q`
- [ ] Implement a full timeline renderer using DOM APIs only, with symbols plus text and left-side connector styling.

### Slice 7: Documentation And Evidence

**Files:**
- Modify: `README.md`
- Modify: `PLAN.md`
- Modify: `REQUIREMENTS_CHECKLIST.md`
- Modify: `AGENT_LOG.md`
- Test: `tests/unit/test_readme.py`

**Steps:**
- [ ] Add or update README tests for DeepSeek function tools, LLM_ERROR, HTTP error display, timeline semantics, and real API smoke warning.
- [ ] Record real commands and outputs only after they have run.
- [ ] Do not mark real DeepSeek smoke as passed unless it actually succeeds.

### Slice 8: Verification

**Commands:**
- `& $PY -m pip install -e .`
- `& $PY -m pip check`
- `& $PY -m pytest tests/unit/test_deepseek*.py -q`
- `& $PY -m pytest tests/unit/test_agent_loop*.py -q`
- `& $PY -m pytest tests/unit/test_run_events*.py -q`
- `& $PY -m pytest tests/unit/test_webui*.py -q`
- `& $PY -m pytest tests/ -q`
- `& $PY -m ruff check harness/ webui/ demo/ tests/`
- `& $PY -m mypy harness/ webui/ demo/`
- `& $PY -m demo.run_demo`
- `& $PY -m build`
- `& $PY -m twine check dist/*`
- `git diff --check`
- Current-tree and full-history credential scans.
- Controlled real DeepSeek smoke only after deterministic tests pass.

---

## Completion Evidence

**Branch:** `codex/task/T31-deepseek-contract-webui-errors`

**Commits:**
- Red: `6cd429d`
- Green: `6d942b8`
- Refactor/Review: `793553c`
- Docs/evidence: pending

**Subagents:**
- Prep: Anscombe (`019f659b-a2f4-7772-934a-b9b3f92658eb`)
- Specification review: Linnaeus (`019f65ab-ff2f-7841-b3aa-92b2e7bd02e4`)
- Code quality review: Laplace (`019f65ac-3002-75c3-8211-4a45404cbb79`)

**Verification actually run:**
- Red target suite: 29 failed, 152 passed, 1 warning.
- Green target suite: 181 passed, 1 warning.
- Review target suite including `test_models`: 242 passed, 1 warning.
- Full tests: 884 passed, 5 skipped, 1 warning.
- Mock regressions: 9 passed.
- Ruff full check: passed.
- Mypy full source check: passed, with the existing unused `tests.*` override note.
- `pip install -e .`: sandbox run blocked by PyPI access; approved rerun passed.
- `pip check`: passed.
- `demo.run_demo`: `HITL_DENIED`, `PASS`, `STUCK`.
- `python -m build`: sandbox run blocked by isolated build dependency install; approved rerun built sdist and wheel.
- `twine check dist\*`: sandbox read of elevated artifacts failed with permission error; approved rerun passed.
- `git diff --check`: passed.
- Credential scans: only explicit fake fixture/log strings were found.
- Controlled real DeepSeek smoke: skipped because `harness key status` returned `not configured`; no real key was read or used.
