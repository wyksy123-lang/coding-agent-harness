# PLAN.md — 实现计划

> 由 Superpowers `writing-plans` 技能驱动，基于人工批准的 `SPEC.md` 生成。
> 每个 task 颗粒度可由一个 subagent 在一次会话内完成，每步 2–5 分钟。
> 严格遵循 TDD：红 → 绿 → 重构。
>
> **TDD 顺序强制**：每个 task 必须先编写失败测试文件，运行并确认红色失败（Red），再编写实现代码使测试通过（Green），最后重构并重新运行全部测试。**禁止先写实现再补测试。** 如果 subagent 先写了实现代码，必须删除后从测试重新开始。

---

## 依赖图

```
T01 (scaffolding + models)
├── T02 (config)
│   ├── T06 (tool base) → T07 (file ops), T08 (shell)
│   ├── T09 (PathGuard)
│   ├── T10 (CommandGuard)
│   ├── T11 (HITLState)
│   └── T17 (credentials)
├── T03 (LLM base)
│   ├── T04 (mock LLM) ─┐
│   └── T05 (DeepSeek)  │
├── T12 (parser)        │
│   ├── T13 (classifier)│
│   │   └── T15 (injector) ← T14 (memory)
│   └── T16 (tracker)   │
└── T14 (memory)         │
                         │
T18 (agent loop) ←───────┘ (depends on T04, T06-T08, T09-T11, T15, T16, T17)
├── T19 (CLI)
├── T20 (FastAPI) → T21 (frontend)
├── T22 (mock integration tests)
└── T23 (mechanism demo)

T24 (GitHub CI) ─┐
T25 (GitLab CI) ─┤ (all depend on T01 only)
T26 (Docker)    ─┘

T27 (README) ← depends on all above
T28 (Render deploy) ← depends on T20, T26
T29 (final acceptance) ← depends on all
```

## 并行计划

| 阶段 | 可并行 tasks | 前置 |
|---|---|---|
| 1 | T01 | — |
| 2 | T02, T03, T12, T14 | T01 |
| 3 | T04, T05, T06, T09, T10, T11, T13, T16, T17 | 阶段 2 对应前置 |
| 4 | T07, T08, T15 | 阶段 3 对应前置 |
| 5 | T18 | T04, T06-T08, T09-T11, T15, T16, T17 |
| 6 | T19, T20, T22, T23, T24, T25, T26 | T18 / T01 |
| 7 | T21, T28 | T20 / T26 |
| 8 | T27 | all above |
| 9 | T29 | all |

## Worktree / PR 映射

| PR | 分支名 | 包含 tasks |
|---|---|---|
| PR1 | `feature/project-setup` | T01 |
| PR2 | `feature/config` | T02 |
| PR3 | `feature/llm` | T03, T04, T05 |
| PR4 | `feature/tools` | T06, T07, T08 |
| PR5 | `feature/governance` | T09, T10, T11 |
| PR6 | `feature/feedback` | T12, T13, T14, T15, T16 |
| PR7 | `feature/credentials` | T17 |
| PR8 | `feature/agent-loop` | T18, T19 |
| PR9 | `feature/webui` | T20, T21 |
| PR10 | `feature/testing-demo` | T22, T23 |
| PR11 | `feature/ci` | T24, T25 |
| PR12 | `feature/distribution` | T26 |
| PR13 | `feature/readme-deploy` | T27, T28, T29 |

---

## T01: 项目脚手架 + 共享数据模型

1. **TASK 编号**: T01
2. **目标**: 创建 Python 项目结构、pyproject.toml、Makefile、conftest.py，以及 `harness/models.py` 定义所有共享数据结构（Config, Action, TestResult, Failure, FailureType, FeedbackMessage, RoundRecord, StopReason, HITLRequest, HITLStatus, GuardResult, MemoryEntry）。
3. **文件路径**:
   - `pyproject.toml`
   - `Makefile`
   - `harness/__init__.py`
   - `harness/models.py`
   - `tests/__init__.py`
   - `tests/conftest.py`
4. **预期实现要点**:
   - `pyproject.toml`: 项目元数据、依赖（httpx, pyyaml, keyring, fastapi, uvicorn, websockets, pytest, pytest-json-report, ruff, mypy）、ruff 和 mypy 配置
   - `Makefile`: `test`, `test-unit`, `test-mock`, `lint`, `typecheck`, `demo`, `build` targets
   - `harness/models.py`: 用 `dataclass` 和 `Enum` 定义 SPEC §6.1 中所有实体，包括：
     - `Config`（13 个字段，见 SPEC §3.6.1 配置表）
     - `Action`（tool_name, args, raw_tool_call）
     - `TestResult`（status, failures, summary）
     - `Failure`（type, test_name, message, file, line, expected, actual）
     - `FailureType`（enum: ASSERTION, SYNTAX, IMPORT, RUNTIME, TIMEOUT, COLLECTION）
     - `FeedbackMessage`（failure_type, details, strategy_hint, relevant_memory）
     - `RoundRecord`（round_number, actions, failure_fingerprint, strategy_used, outcome: RoundOutcome）
     - `RoundOutcome`（enum: PASS, FAIL, NO_TESTS, HITL_DENIED）
     - `StopReason`（enum: PASS, MAX_ROUNDS, STUCK, HITL_DENIED）
     - `HITLRequest`（action, status, timestamp, decision）
     - `HITLStatus`（enum: PENDING, APPROVED, DENIED, TIMEOUT）
     - `GuardResult`（enum: ALLOW, DENY, PENDING）
     - `MemoryEntry`（session_id, round, failure_type, test_name, message, strategy_used, outcome）
   - `tests/conftest.py`: 公共 fixtures（tmp_workspace: 创建临时目标目录并返回路径; mock_config: 返回默认 Config 对象）
5. **需要先编写的失败测试**: `tests/unit/test_models.py` — 具体断言：
   - 测试每个 dataclass（Config, Action, TestResult, Failure, FeedbackMessage, RoundRecord, HITLRequest, MemoryEntry）可正确实例化且字段类型正确
   - 测试每个 enum（FailureType, RoundOutcome, StopReason, HITLStatus, GuardResult）包含 SPEC 中定义的所有值
   - 测试 Config 默认值正确（max_rounds=10, temperature=0.1 等）
   - 测试 RoundRecord.outcome 可设为 RoundOutcome.PASS / FAIL / NO_TESTS / HITL_DENIED
6. **Red 阶段验证命令与预期失败原因**:
   - 命令: `pytest tests/unit/test_models.py -v`
   - 预期失败: `ModuleNotFoundError: No module named 'harness.models'`
7. **Green 阶段验证命令**: `pytest tests/unit/test_models.py -v`（全部通过）
8. **完整测试、lint 和类型检查命令**:
   - `pytest tests/unit/test_models.py -v`
   - `ruff check harness/models.py tests/unit/test_models.py`
   - `mypy harness/models.py`
9. **依赖关系**: 无（首个 task）
10. **是否可并行**: 否（所有后续 task 依赖此 task）
11. **对应 worktree 和 PR 范围**: `feature/project-setup` / PR1
12. **完成状态及 commit hash 记录位置**: 本文件 T01 行的"状态"列；AGENT_LOG.md 对应条目

**状态**: ✅ DONE | **Commit**: 68bd926 (Red), fe41b92 (Green), 79ccece (Refactor)

---

## T02: 配置模块（ConfigLoader）

1. **TASK 编号**: T02
2. **目标**: 实现 `ConfigLoader` 解析 `harness.yaml`，校验必填项，构造 `Config` 对象；创建默认 `harness.yaml.example`。
3. **文件路径**:
   - `harness/config/__init__.py`
   - `harness/config/loader.py`
   - `harness.yaml.example`
   - `tests/unit/test_config.py`
4. **预期实现要点**:
   - `ConfigLoader.load(path: str) -> Config`: 解析 YAML → 校验必填项 → 缺失字段用默认值填充 → 未知字段忽略
   - YAML 解析失败 → 抛 `ConfigError`；必填项缺失 → 抛 `ConfigError`
   - `harness.yaml.example` 包含 SPEC §3.6.1 所有 13 个配置项，使用扁平 snake_case 键（无嵌套），完整示例见 SPEC §3.6.1 `harness.yaml.example` 代码块
   - `dangerous_command_patterns` 为字符串列表（正则模式）；`enabled_tools` 为字符串列表（工具名）
5. **需要先编写的失败测试**: `tests/unit/test_config.py` — 测试加载有效 YAML 返回正确 Config；测试缺失字段用默认值；测试无效 YAML 抛异常；测试未知字段被忽略
6. **Red 阶段验证命令与预期失败原因**:
   - 命令: `pytest tests/unit/test_config.py -v`
   - 预期失败: `ModuleNotFoundError: No module named 'harness.config.loader'`
7. **Green 阶段验证命令**: `pytest tests/unit/test_config.py -v`
8. **完整测试、lint 和类型检查命令**:
   - `pytest tests/unit/test_config.py -v`
   - `ruff check harness/config/ tests/unit/test_config.py`
   - `mypy harness/config/loader.py`
9. **依赖关系**: T01
10. **是否可并行**: 是（与 T03, T12, T14 并行）
11. **对应 worktree 和 PR 范围**: `feature/config` / PR2
12. **完成状态及 commit hash 记录位置**: 本文件 T02 行；AGENT_LOG.md

**状态**: ✅ DONE | **Commit**: e501189 (Red), bfe7750 (Green), c70afe7 (Refactor)

---

## T03: LLM 抽象层（LLMClient 协议）

1. **TASK 编号**: T03
2. **目标**: 实现 `LLMClient` 抽象基类，定义 `chat(messages, tools) -> LLMResponse` 协议；定义 `LLMResponse` 数据结构含 `tool_calls` 字段。
3. **文件路径**:
   - `harness/llm/__init__.py`
   - `harness/llm/base.py`
   - `tests/unit/test_llm_base.py`
4. **预期实现要点**:
   - `LLMClient` 为 ABC，定义 `chat(messages: List[dict], tools: List[dict]) -> LLMResponse`
   - `LLMResponse` dataclass: `content: str`, `tool_calls: List[ToolCall]`, `finish_reason: str`
   - `ToolCall` dataclass: `id: str`, `name: str`, `arguments: dict`
5. **需要先编写的失败测试**: `tests/unit/test_llm_base.py` — 测试 LLMClient 不可直接实例化（ABC）；测试子类必须实现 chat；测试 LLMResponse 和 ToolCall dataclass 可正确构造
6. **Red 阶段验证命令与预期失败原因**:
   - 命令: `pytest tests/unit/test_llm_base.py -v`
   - 预期失败: `ModuleNotFoundError: No module named 'harness.llm.base'`
7. **Green 阶段验证命令**: `pytest tests/unit/test_llm_base.py -v`
8. **完整测试、lint 和类型检查命令**:
   - `pytest tests/unit/test_llm_base.py -v`
   - `ruff check harness/llm/base.py tests/unit/test_llm_base.py`
   - `mypy harness/llm/base.py`
9. **依赖关系**: T01
10. **是否可并行**: 是（与 T02, T12, T14 并行）
11. **对应 worktree 和 PR 范围**: `feature/llm` / PR3
12. **完成状态及 commit hash 记录位置**: 本文件 T03 行；AGENT_LOG.md

**状态**: ✅ DONE | **Commit**: cda280a (Red), fd04023 (Green), f06b2a7 (Refactor)

---

## T04: MockLLMClient

1. **TASK 编号**: T04
2. **目标**: 实现 `MockLLMClient`，按预设响应序列返回 `LLMResponse`，用于离线确定性测试。
3. **文件路径**:
   - `harness/llm/mock.py`
   - `tests/unit/test_llm_mock.py`
4. **预期实现要点**:
   - `MockLLMClient(responses: List[LLMResponse])`: 按顺序返回预设响应，耗尽后抛异常
   - `MockLLMClient.from_tool_calls(tool_call_lists: List[List[ToolCall]])`: 便捷构造
   - 记录每次调用的 messages 和 tools（供测试断言）
5. **需要先编写的失败测试**: `tests/unit/test_llm_mock.py` — 测试按序返回预设响应；测试响应耗尽抛异常；测试记录调用参数
6. **Red 阶段验证命令与预期失败原因**:
   - 命令: `pytest tests/unit/test_llm_mock.py -v`
   - 预期失败: `ModuleNotFoundError: No module named 'harness.llm.mock'`
7. **Green 阶段验证命令**: `pytest tests/unit/test_llm_mock.py -v`
8. **完整测试、lint 和类型检查命令**:
   - `pytest tests/unit/test_llm_mock.py -v`
   - `ruff check harness/llm/mock.py tests/unit/test_llm_mock.py`
   - `mypy harness/llm/mock.py`
9. **依赖关系**: T03
10. **是否可并行**: 是（与 T05 并行）
11. **对应 worktree 和 PR 范围**: `feature/llm` / PR3
12. **完成状态及 commit hash 记录位置**: 本文件 T04 行；AGENT_LOG.md

**状态**: ✅ DONE | **Commit**: db70b60 (Red), cba9cd1 (Green), 8e57cad (Refactor)

---

## T05: DeepSeekClient

1. **TASK 编号**: T05
2. **目标**: 实现 `DeepSeekClient`，通过 httpx 调用 DeepSeek API（OpenAI 兼容 Chat Completions + tool calling），返回 `LLMResponse`。
3. **文件路径**:
   - `harness/llm/deepseek.py`
   - `tests/unit/test_llm_deepseek.py`
4. **预期实现要点**:
   - `DeepSeekClient(api_key: str, model: str, temperature: float, timeout: int, retry_count: int)`
   - `chat(messages, tools) -> LLMResponse`: POST 到 DeepSeek API，解析 response，构造 LLMResponse
   - 重试机制：失败重试 `retry_count` 次后抛异常
   - 超时控制：`timeout` 秒
   - **不硬编码 API key**——通过构造函数注入
5. **需要先编写的失败测试**: `tests/unit/test_llm_deepseek.py` — 用 `httpx.MockTransport` mock HTTP 请求，测试正确构造请求、解析响应、重试逻辑、超时处理。**不发起真实网络请求。**
6. **Red 阶段验证命令与预期失败原因**:
   - 命令: `pytest tests/unit/test_llm_deepseek.py -v`
   - 预期失败: `ModuleNotFoundError: No module named 'harness.llm.deepseek'`
7. **Green 阶段验证命令**: `pytest tests/unit/test_llm_deepseek.py -v`
8. **完整测试、lint 和类型检查命令**:
   - `pytest tests/unit/test_llm_deepseek.py -v`
   - `ruff check harness/llm/deepseek.py tests/unit/test_llm_deepseek.py`
   - `mypy harness/llm/deepseek.py`
9. **依赖关系**: T03
10. **是否可并行**: 是（与 T04 并行）
11. **对应 worktree 和 PR 范围**: `feature/llm` / PR3
12. **完成状态及 commit hash 记录位置**: 本文件 T05 行；AGENT_LOG.md

**状态**: ✅ DONE | **Commit**: 9bd284c (Red), 97a8632 (Green), 8b46398 (Refactor)

---

## T06: 工具基类 + ToolRegistry

1. **TASK 编号**: T06
2. **目标**: 实现 `Tool` 抽象基类和 `ToolRegistry`，支持工具注册、schema 声明、按名分发。
3. **文件路径**:
   - `harness/tools/__init__.py`
   - `harness/tools/base.py`
   - `tests/unit/test_tool_registry.py`
4. **预期实现要点**:
   - `Tool` ABC: `name`, `schema` (JSON Schema dict), `execute(args: dict) -> ToolResult`
   - `ToolResult` dataclass: `success: bool`, `output: dict`, `error: Optional[str]`
   - `ToolRegistry`: `register(tool)`, `dispatch(action: Action) -> ToolResult`, `get_schemas() -> List[dict]`, `is_enabled(tool_name) -> bool`（受 Config.enabled_tools 控制）
5. **需要先编写的失败测试**: `tests/unit/test_tool_registry.py` — 测试注册工具后可按名分发；测试未注册工具抛异常；测试 enabled_tools 白名单过滤；测试 get_schemas 返回正确 schema
6. **Red 阶段验证命令与预期失败原因**:
   - 命令: `pytest tests/unit/test_tool_registry.py -v`
   - 预期失败: `ModuleNotFoundError: No module named 'harness.tools.base'`
7. **Green 阶段验证命令**: `pytest tests/unit/test_tool_registry.py -v`
8. **完整测试、lint 和类型检查命令**:
   - `pytest tests/unit/test_tool_registry.py -v`
   - `ruff check harness/tools/base.py tests/unit/test_tool_registry.py`
   - `mypy harness/tools/base.py`
9. **依赖关系**: T01, T02
10. **是否可并行**: 是（与 T09, T10, T11, T17 并行）
11. **对应 worktree 和 PR 范围**: `feature/tools` / PR4
12. **完成状态及 commit hash 记录位置**: 本文件 T06 行；AGENT_LOG.md

**状态**: ✅ DONE | **Commit**: cdbfdd6 (Red), c9431a2 (Green), 5636470 (Refactor)

1. **TASK 编号**: T07
2. **目标**: 实现三个文件操作工具，经 PathGuard 检查后执行文件读写。
3. **文件路径**:
   - `harness/tools/file_ops.py`
   - `tests/unit/test_file_ops.py`
4. **预期实现要点**:
   - `WriteFileTool`: 接收 path + content → PathGuard 检查 → 写文件 → 返回 ToolResult
   - `ReadFileTool`: 接收 path → PathGuard 检查 → 读文件 → 返回 ToolResult
   - `ListFilesTool`: 接收 path → PathGuard 检查 → 列目录 → 返回 ToolResult
   - 目录不存在 → 自动创建（write_file）；文件不存在 → 返回错误（read_file）
5. **需要先编写的失败测试**: `tests/unit/test_file_ops.py` — 测试写入并读取文件；测试越界路径被拦截；测试目录自动创建；测试文件不存在返回错误
6. **Red 阶段验证命令与预期失败原因**:
   - 命令: `pytest tests/unit/test_file_ops.py -v`
   - 预期失败: `ModuleNotFoundError: No module named 'harness.tools.file_ops'`
7. **Green 阶段验证命令**: `pytest tests/unit/test_file_ops.py -v`
8. **完整测试、lint 和类型检查命令**:
   - `pytest tests/unit/test_file_ops.py -v`
   - `ruff check harness/tools/file_ops.py tests/unit/test_file_ops.py`
   - `mypy harness/tools/file_ops.py`
9. **依赖关系**: T06, T09（PathGuard）
10. **是否可并行**: 是（与 T08 并行）
11. **对应 worktree 和 PR 范围**: `feature/tools` / PR4
12. **完成状态及 commit hash 记录位置**: 本文件 T07 行；AGENT_LOG.md

**状态**: ✅ DONE | **Commit**: 945b468 (Red), b7edbc1 (Green), a47072a (Refactor)

---

## T08: Shell 工具（run_command / run_tests）

1. **TASK 编号**: T08
2. **目标**: 实现 `run_command` 和 `run_tests` 工具。run_command 经 CommandGuard 检查后执行 shell；run_tests 运行 pytest 并返回 JSON 报告路径。
3. **文件路径**:
   - `harness/tools/shell.py`
   - `tests/unit/test_shell.py`
4. **预期实现要点**:
   - `RunCommandTool`: 接收 cmd → CommandGuard 检查 → ALLOW 直接执行 / PENDING 返回待审批 → 执行 → 返回 stdout/stderr/exit_code
   - `RunTestsTool`: 运行 Config.test_command → 返回 report.json 路径
   - 超时控制：Config.pytest_timeout
5. **需要先编写的失败测试**: `tests/unit/test_shell.py` — 测试安全命令执行；测试危险命令返回 PENDING；测试 run_tests 返回报告路径；测试超时处理
6. **Red 阶段验证命令与预期失败原因**:
   - 命令: `pytest tests/unit/test_shell.py -v`
   - 预期失败: `ModuleNotFoundError: No module named 'harness.tools.shell'`
7. **Green 阶段验证命令**: `pytest tests/unit/test_shell.py -v`
8. **完整测试、lint 和类型检查命令**:
   - `pytest tests/unit/test_shell.py -v`
   - `ruff check harness/tools/shell.py tests/unit/test_shell.py`
   - `mypy harness/tools/shell.py`
9. **依赖关系**: T06, T10（CommandGuard）
10. **是否可并行**: 是（与 T07 并行）
11. **对应 worktree 和 PR 范围**: `feature/tools` / PR4
12. **完成状态及 commit hash 记录位置**: 本文件 T08 行；AGENT_LOG.md

**状态**: ✅ DONE | **Commit**: 330befa (Red), 7650e9d (Green), 7d4d9f4 (Refactor)

---

## T09: PathGuard（路径围栏）

1. **TASK 编号**: T09
2. **目标**: 实现 `PathGuard.check(path, target_directory) -> GuardResult`，拦截越界路径和 `..` 穿越。
3. **文件路径**:
   - `harness/governance/__init__.py`
   - `harness/governance/path_guard.py`
   - `tests/unit/test_path_guard.py`
4. **预期实现要点**:
   - `PathGuard.check(path: str, target_directory: str) -> GuardResult`
   - 解析路径为绝对路径 → 检查是否在 target_directory 子树内 → 检查 `..` 穿越
   - 越界 → `GuardResult.DENY`；合法 → `GuardResult.ALLOW`；解析失败 → `DENY`
5. **需要先编写的失败测试**: `tests/unit/test_path_guard.py` — 测试合法路径 ALLOW；测试越界路径 DENY；测试 `..` 穿越 DENY；测试绝对路径 DENY；测试符号链接处理
6. **Red 阶段验证命令与预期失败原因**:
   - 命令: `pytest tests/unit/test_path_guard.py -v`
   - 预期失败: `ModuleNotFoundError: No module named 'harness.governance.path_guard'`
7. **Green 阶段验证命令**: `pytest tests/unit/test_path_guard.py -v`
8. **完整测试、lint 和类型检查命令**:
   - `pytest tests/unit/test_path_guard.py -v`
   - `ruff check harness/governance/path_guard.py tests/unit/test_path_guard.py`
   - `mypy harness/governance/path_guard.py`
9. **依赖关系**: T01, T02
10. **是否可并行**: 是（与 T06, T10, T11, T17 并行）
11. **对应 worktree 和 PR 范围**: `feature/governance` / PR5
12. **完成状态及 commit hash 记录位置**: 本文件 T09 行；AGENT_LOG.md

**状态**: ✅ DONE | **Commit**: 26ac727 (Red), 9915a30 (Green), 7e6babd (Refactor)

---

## T10: CommandGuard（危险命令检测）

1. **TASK 编号**: T10
2. **目标**: 实现 `CommandGuard.check(cmd, patterns) -> GuardResult`，正则匹配危险命令模式。
3. **文件路径**:
   - `harness/governance/command_guard.py`
   - `tests/unit/test_command_guard.py`
4. **预期实现要点**:
   - `CommandGuard.check(cmd: str, patterns: List[str]) -> GuardResult`
   - 逐条正则匹配 → 命中任一 → `PENDING`；全部不命中 → `ALLOW`
   - 正则编译失败 → 跳过该条并记录警告
5. **需要先编写的失败测试**: `tests/unit/test_command_guard.py` — 测试 `rm -rf` 匹配 PENDING；测试 `git push` 匹配 PENDING；测试 `sudo` 匹配 PENDING；测试安全命令 ALLOW；测试无效正则跳过；测试空模式列表 ALLOW
6. **Red 阶段验证命令与预期失败原因**:
   - 命令: `pytest tests/unit/test_command_guard.py -v`
   - 预期失败: `ModuleNotFoundError: No module named 'harness.governance.command_guard'`
7. **Green 阶段验证命令**: `pytest tests/unit/test_command_guard.py -v`
8. **完整测试、lint 和类型检查命令**:
   - `pytest tests/unit/test_command_guard.py -v`
   - `ruff check harness/governance/command_guard.py tests/unit/test_command_guard.py`
   - `mypy harness/governance/command_guard.py`
9. **依赖关系**: T01, T02
10. **是否可并行**: 是（与 T06, T09, T11, T17 并行）
11. **对应 worktree 和 PR 范围**: `feature/governance` / PR5
12. **完成状态及 commit hash 记录位置**: 本文件 T10 行；AGENT_LOG.md

**状态**: ✅ DONE | **Commit**: 4bdfcfe (Red), 308ed0b (Green), e476d48 (Refactor)

---

## T11: HITLState（人工审批状态机）

1. **TASK 编号**: T11
2. **目标**: 实现 `HITLState` 状态机：PENDING → APPROVED/DENIED/TIMEOUT → 返回结果。
3. **文件路径**:
   - `harness/governance/hitl.py`
   - `tests/unit/test_hitl.py`
4. **预期实现要点**:
   - `HITLState.create(action: Action, timeout: int) -> HITLRequest`: 创建 PENDING 请求
   - `HITLState.approve(request_id: str) -> HITLRequest`: 转为 APPROVED
   - `HITLState.deny(request_id: str) -> HITLRequest`: 转为 DENIED
   - `HITLState.check_timeout(request_id: str) -> HITLRequest`: 超时转为 TIMEOUT
   - `HITLState.get_pending() -> List[HITLRequest]`: 获取所有 PENDING 请求
5. **需要先编写的失败测试**: `tests/unit/test_hitl.py` — 测试创建 PENDING；测试 approve → APPROVED；测试 deny → DENIED；测试超时 → TIMEOUT；测试非法状态转换抛异常
6. **Red 阶段验证命令与预期失败原因**:
   - 命令: `pytest tests/unit/test_hitl.py -v`
   - 预期失败: `ModuleNotFoundError: No module named 'harness.governance.hitl'`
7. **Green 阶段验证命令**: `pytest tests/unit/test_hitl.py -v`
8. **完整测试、lint 和类型检查命令**:
   - `pytest tests/unit/test_hitl.py -v`
   - `ruff check harness/governance/hitl.py tests/unit/test_hitl.py`
   - `mypy harness/governance/hitl.py`
9. **依赖关系**: T01, T02
10. **是否可并行**: 是（与 T06, T09, T10, T17 并行）
11. **对应 worktree 和 PR 范围**: `feature/governance` / PR5
12. **完成状态及 commit hash 记录位置**: 本文件 T11 行；AGENT_LOG.md

**状态**: ✅ DONE | **Commit**: 6142f32 (Red), 1811c19 (Green), 6fe2dd6 (Refactor)

---

## T12: TestResultParser（pytest JSON 解析器）

1. **TASK 编号**: T12
2. **目标**: 实现 `TestResultParser.parse(json_str: str) -> TestResult`，解析 pytest `--json-report` 输出。
3. **文件路径**:
   - `harness/feedback/__init__.py`
   - `harness/feedback/parser.py`
   - `tests/unit/test_parser.py`
   - `tests/fixtures/` (示例 pytest JSON 报告)
4. **预期实现要点**:
   - `TestResultParser.parse(json_str: str) -> TestResult`: 解析 JSON → 提取 status, failures, summary
   - 每个 Failure 含 type, test_name, message, file, line, expected, actual
   - JSON 解析失败 → 返回 `TestResult(status=ERROR, failures=[Failure(type=COLLECTION)])`
   - 字段缺失 → 用默认值填充
5. **需要先编写的失败测试**: `tests/unit/test_parser.py` — 测试解析全绿报告（status=PASS, failures=[]）；测试解析含断言失败的报告；测试解析含语法错误的报告；测试解析含导入错误的报告；测试解析空 JSON 抛异常返回 ERROR
6. **Red 阶段验证命令与预期失败原因**:
   - 命令: `pytest tests/unit/test_parser.py -v`
   - 预期失败: `ModuleNotFoundError: No module named 'harness.feedback.parser'`
7. **Green 阶段验证命令**: `pytest tests/unit/test_parser.py -v`
8. **完整测试、lint 和类型检查命令**:
   - `pytest tests/unit/test_parser.py -v`
   - `ruff check harness/feedback/parser.py tests/unit/test_parser.py`
   - `mypy harness/feedback/parser.py`
9. **依赖关系**: T01
10. **是否可并行**: 是（与 T02, T03, T14 并行）
11. **对应 worktree 和 PR 范围**: `feature/feedback` / PR6
12. **完成状态及 commit hash 记录位置**: 本文件 T12 行；AGENT_LOG.md

**状态**: ✅ DONE | **Commit**: 6f92a03 (Red), 99af4a9 (Green), 030eb64 (Refactor)

---

## T13: FailureClassifier（失败分类器）

1. **TASK 编号**: T13
2. **目标**: 实现 `FailureClassifier.classify(failure: Failure) -> FailureType`，按消息和 traceback 模式匹配分类为 6 种失败类型。
3. **文件路径**:
   - `harness/feedback/classifier.py`
   - `tests/unit/test_classifier.py`
4. **预期实现要点**:
   - `FailureClassifier.classify(failure: Failure) -> FailureType`
   - 匹配规则（SPEC §3.3.2）:
     - ASSERTION: 消息含 "AssertionError" 或 "assert"
     - SYNTAX: 消息含 "SyntaxError" 或 "IndentationError"
     - IMPORT: 消息含 "ModuleNotFoundError" 或 "ImportError"
     - RUNTIME: 消息含 "TypeError"/"ValueError"/"KeyError"/"AttributeError" 等
     - TIMEOUT: pytest 报告超时或进程超时
     - COLLECTION: pytest 收集阶段失败
   - 无法匹配 → 默认 RUNTIME
5. **需要先编写的失败测试**: `tests/unit/test_classifier.py` — 测试每种 FailureType 各至少一个用例；测试默认 RUNTIME；测试空消息返回 RUNTIME
6. **Red 阶段验证命令与预期失败原因**:
   - 命令: `pytest tests/unit/test_classifier.py -v`
   - 预期失败: `ModuleNotFoundError: No module named 'harness.feedback.classifier'`
7. **Green 阶段验证命令**: `pytest tests/unit/test_classifier.py -v`
8. **完整测试、lint 和类型检查命令**:
   - `pytest tests/unit/test_classifier.py -v`
   - `ruff check harness/feedback/classifier.py tests/unit/test_classifier.py`
   - `mypy harness/feedback/classifier.py`
9. **依赖关系**: T01, T12
10. **是否可并行**: 是（与 T16 并行，均依赖 T12）
11. **对应 worktree 和 PR 范围**: `feature/feedback` / PR6
12. **完成状态及 commit hash 记录位置**: 本文件 T13 行；AGENT_LOG.md

**状态**: ✅ DONE | **Commit**: 8753677 (Red), 53c81cc (Green), dad9968 (Refactor)

---

## T14: MemoryRetriever + MemoryRecorder（记忆维度）

1. **TASK 编号**: T14
2. **目标**: 实现 `MemoryRetriever` 和 `MemoryRecorder`，基于 JSON 文件按失败类型过滤检索，非全量载入。
3. **文件路径**:
   - `harness/memory/__init__.py`
   - `harness/memory/retriever.py`
   - `tests/unit/test_memory.py`
4. **预期实现要点**:
   - `MemoryRetriever.retrieve_relevant(failure_type: str, limit: int = 3) -> List[MemoryEntry]`: 读 memory.json → 按失败类型过滤 → 返回最相关 N 条
   - `MemoryRetriever.get_conventions() -> dict`: 返回项目约定
   - `MemoryRecorder.record(round_record: RoundRecord) -> None`: 追加条目到 memory.json
   - 文件不存在 → 返回空列表 / 创建新文件；JSON 解析失败 → 返回空列表并警告
5. **需要先编写的失败测试**: `tests/unit/test_memory.py` — 测试按失败类型过滤返回正确条目；测试 limit 截断；测试空文件返回空列表；测试记录后可检索；测试非全量载入（验证返回条目数 < 总条目数）
6. **Red 阶段验证命令与预期失败原因**:
   - 命令: `pytest tests/unit/test_memory.py -v`
   - 预期失败: `ModuleNotFoundError: No module named 'harness.memory.retriever'`
7. **Green 阶段验证命令**: `pytest tests/unit/test_memory.py -v`
8. **完整测试、lint 和类型检查命令**:
   - `pytest tests/unit/test_memory.py -v`
   - `ruff check harness/memory/retriever.py tests/unit/test_memory.py`
   - `mypy harness/memory/retriever.py`
9. **依赖关系**: T01
10. **是否可并行**: 是（与 T02, T03, T12 并行）
11. **对应 worktree 和 PR 范围**: `feature/feedback` / PR6
12. **完成状态及 commit hash 记录位置**: 本文件 T14 行；AGENT_LOG.md

**状态**: ✅ DONE | **Commit**: eba84a6 (Red), fbf6d6c (Green), 24b81b0 (Review), 9a9ab97 (Critical review fix)

---

## T15: FeedbackInjector（反馈回灌 + 策略路由）

1. **TASK 编号**: T15
2. **目标**: 实现 `FeedbackInjector.inject(test_result, failure_type, memory) -> FeedbackMessage`，按失败类型查策略路由表，格式化结构化反馈，检索相关记忆。
3. **文件路径**:
   - `harness/feedback/injector.py`
   - `tests/unit/test_injector.py`
4. **预期实现要点**:
   - `FeedbackInjector.inject(test_result: TestResult, failure_type: FailureType, memory: MemoryRetriever) -> FeedbackMessage`
   - 策略路由表（SPEC §5.3）: 每种 FailureType → 对应 StrategyHint + 反馈模板
   - 格式化: 含 failure_type, details (失败位置/期望/实际), strategy_hint, relevant_memory
   - 反馈消息长度限制（避免上下文爆炸）
   - 记忆检索失败 → 返回空列表，不影响反馈
5. **需要先编写的失败测试**: `tests/unit/test_injector.py` — 测试每种 FailureType 返回对应 strategy_hint；测试 details 含失败位置和期望/实际值；测试 relevant_memory 来自 MemoryRetriever；测试记忆检索失败不影响反馈
6. **Red 阶段验证命令与预期失败原因**:
   - 命令: `pytest tests/unit/test_injector.py -v`
   - 预期失败: `ModuleNotFoundError: No module named 'harness.feedback.injector'`
7. **Green 阶段验证命令**: `pytest tests/unit/test_injector.py -v`
8. **完整测试、lint 和类型检查命令**:
   - `pytest tests/unit/test_injector.py -v`
   - `ruff check harness/feedback/injector.py tests/unit/test_injector.py`
   - `mypy harness/feedback/injector.py`
9. **依赖关系**: T01, T13, T14
10. **是否可并行**: 否（依赖 T13 和 T14）
11. **对应 worktree 和 PR 范围**: `feature/feedback` / PR6
12. **完成状态及 commit hash 记录位置**: 本文件 T15 行；AGENT_LOG.md

**状态**: ✅ DONE | **Commit**: c1c4522 (Red), 7935baa (Green), fb307b6 (Review)

---

## T16: RoundTracker（轮次追踪 + 卡死检测 + 停机判断）

1. **TASK 编号**: T16
2. **目标**: 实现 `RoundTracker`，追踪轮次历史，检测卡死（同一失败指纹连续 N 轮），判断停机。
3. **文件路径**:
   - `harness/feedback/tracker.py`
   - `tests/unit/test_tracker.py`
4. **预期实现要点**:
   - `RoundTracker(max_rounds: int, stuck_threshold: int)`
   - `update(round_record: RoundRecord) -> None`: 追加历史 → 更新失败指纹队列
   - `detect_loop() -> bool`: 同一失败指纹连续 `stuck_threshold` 轮 → True
   - `should_stop() -> Optional[StopReason]`: 全绿→PASS / 超轮次→MAX_ROUNDS / 卡死→STUCK / HITL拒绝→HITL_DENIED / 否则 None
   - `failure_fingerprint`: 失败类型+测试名+消息的哈希
5. **需要先编写的失败测试**: `tests/unit/test_tracker.py` — 测试全绿→PASS；测试超 max_rounds→MAX_ROUNDS；测试同一指纹连续 N 轮→STUCK；测试不同指纹不触发卡死；测试 HITL_DENIED；测试 None（继续）
6. **Red 阶段验证命令与预期失败原因**:
   - 命令: `pytest tests/unit/test_tracker.py -v`
   - 预期失败: `ModuleNotFoundError: No module named 'harness.feedback.tracker'`
7. **Green 阶段验证命令**: `pytest tests/unit/test_tracker.py -v`
8. **完整测试、lint 和类型检查命令**:
   - `pytest tests/unit/test_tracker.py -v`
   - `ruff check harness/feedback/tracker.py tests/unit/test_tracker.py`
   - `mypy harness/feedback/tracker.py`
9. **依赖关系**: T01, T12
10. **是否可并行**: 是（与 T13 并行，均依赖 T12）
11. **对应 worktree 和 PR 范围**: `feature/feedback` / PR6
12. **完成状态及 commit hash 记录位置**: 本文件 T16 行；AGENT_LOG.md

**状态**: ✅ DONE | **Commit**: 46ff206 (Red), 868aeee (Green), 39251c4 (Review)

---

## T17: CredentialManager（凭据管理）

1. **TASK 编号**: T17
2. **目标**: 实现 `CredentialManager`，通过 keyring（主）和 .env（降级）管理 API key 的录入/状态/更新/清除。
3. **文件路径**:
   - `harness/credentials/__init__.py`
   - `harness/credentials/manager.py`
   - `tests/unit/test_credentials.py`
4. **预期实现要点**:
   - `CredentialManager(service_name: str = "coding-agent-harness")`
   - `setup() -> None`: `getpass.getpass()` 隐藏录入 → 存入 keyring
   - `status() -> str`: 返回掩码 `sk-****...****`，不回显明文
   - `update() -> None`: 覆写 keyring 中的 key
   - `clear() -> None`: 删除 keyring 中的 key
   - `get_key() -> Optional[str]`: 供 AgentLoop 使用，优先 keyring，降级 .env
   - keyring 不可用 → 降级到 .env 并警告
5. **需要先编写的失败测试**: `tests/unit/test_credentials.py` — 用 mock keyring backend 测试 setup/status/update/clear；测试 status 返回掩码不回显明文；测试 keyring 不可用降级 .env；测试 key 不存在返回 None
6. **Red 阶段验证命令与预期失败原因**:
   - 命令: `pytest tests/unit/test_credentials.py -v`
   - 预期失败: `ModuleNotFoundError: No module named 'harness.credentials.manager'`
7. **Green 阶段验证命令**: `pytest tests/unit/test_credentials.py -v`
8. **完整测试、lint 和类型检查命令**:
   - `pytest tests/unit/test_credentials.py -v`
   - `ruff check harness/credentials/manager.py tests/unit/test_credentials.py`
   - `mypy harness/credentials/manager.py`
9. **依赖关系**: T01, T02
10. **是否可并行**: 是（与 T06, T09, T10, T11 并行）
11. **对应 worktree 和 PR 范围**: `feature/credentials` / PR7
12. **完成状态及 commit hash 记录位置**: 本文件 T17 行；AGENT_LOG.md

**状态**: ✅ DONE | **Commit**: 3d88110 (Red), d21bda2 (Green), e34c611 (Review)

---

## T18: Agent 主循环（AgentLoop）

1. **TASK 编号**: T18
2. **目标**: 实现 `AgentLoop.run(requirement: str) -> AgentResult`，整合 LLM、工具分发、治理、反馈闭环、记忆、配置，完成 TDD 循环。
3. **文件路径**:
   - `harness/agent_loop.py`
   - `tests/unit/test_agent_loop.py`
4. **预期实现要点**:
   - `AgentLoop(config: Config, llm_client: LLMClient, tool_registry: ToolRegistry, ...)`
   - `run(requirement: str) -> AgentResult`: 加载配置 → 初始化上下文 → 循环（组织上下文 → 调用 LLM → 解析 tool_calls → 治理检查 → 分发执行 → 反馈回灌 → 轮次追踪 → 停机判断）→ 返回结果
   - LLM 调用失败 → 重试 `llm_retry_count` 次后报错停机
   - 治理拦截 → HITL 或直接拒绝
   - HITL 拒绝 → 反馈给 agent
   - `AgentResult` dataclass: `status: StopReason`, `rounds: List[RoundRecord]`, `output_files: List[str]`
5. **需要先编写的失败测试**: `tests/unit/test_agent_loop.py` — 用 MockLLMClient 测试完整 TDD 循环（红→绿）；测试停机判断（PASS/MAX_ROUNDS/STUCK）；测试治理拦截；测试 HITL 拒绝反馈。**全部不依赖网络和真实 LLM。**
6. **Red 阶段验证命令与预期失败原因**:
   - 命令: `pytest tests/unit/test_agent_loop.py -v`
   - 预期失败: `ModuleNotFoundError: No module named 'harness.agent_loop'`
7. **Green 阶段验证命令**: `pytest tests/unit/test_agent_loop.py -v`
8. **完整测试、lint 和类型检查命令**:
   - `pytest tests/unit/test_agent_loop.py -v`
   - `ruff check harness/agent_loop.py tests/unit/test_agent_loop.py`
   - `mypy harness/agent_loop.py`
9. **依赖关系**: T04, T06, T07, T08, T09, T10, T11, T15, T16, T17
10. **是否可并行**: 否（核心集成 task）
11. **对应 worktree 和 PR 范围**: `feature/agent-loop` / PR8
12. **完成状态及 commit hash 记录位置**: 本文件 T18 行；AGENT_LOG.md

**状态**: ✅ DONE | **Commit**: ed438bc (Red), 21d9972 (Green), c964704 (Review)

---

## T19: CLI 入口

1. **TASK 编号**: T19
2. **目标**: 实现 CLI 入口 `harness run`、`harness key setup/status/update/clear`，解析参数并调用 AgentLoop 或 CredentialManager。
3. **文件路径**:
   - `harness/cli.py`
   - `tests/unit/test_cli.py`
4. **预期实现要点**:
   - `harness run "需求描述" --config harness.yaml`: 加载配置 → 初始化 AgentLoop → 运行
   - `harness key setup/status/update/clear`: 调用 CredentialManager
   - 使用 `argparse` 或 `click` 解析命令行参数
   - 首次运行无 key → 引导 setup
5. **需要先编写的失败测试**: `tests/unit/test_cli.py` — 测试 `harness run` 参数解析；测试 `harness key status` 输出掩码；测试缺失 key 提示 setup；测试 `--config` 参数
6. **Red 阶段验证命令与预期失败原因**:
   - 命令: `pytest tests/unit/test_cli.py -v`
   - 预期失败: `ModuleNotFoundError: No module named 'harness.cli'`
7. **Green 阶段验证命令**: `pytest tests/unit/test_cli.py -v`
8. **完整测试、lint 和类型检查命令**:
   - `pytest tests/unit/test_cli.py -v`
   - `ruff check harness/cli.py tests/unit/test_cli.py`
   - `mypy harness/cli.py`
9. **依赖关系**: T18
10. **是否可并行**: 是（与 T20, T22, T23 并行）
11. **对应 worktree 和 PR 范围**: `feature/agent-loop` / PR8
12. **完成状态及 commit hash 记录位置**: 本文件 T19 行；AGENT_LOG.md

**状态**: ✅ DONE | **Commit**: fa2daab (Red), 2f84570 (Green), 10869ac (Review)

---

## T20: FastAPI 应用 + WebSocket

1. **TASK 编号**: T20
2. **目标**: 实现 FastAPI 应用，提供 WebSocket 实时推送 agent 状态和 HITL 审批接口。
3. **文件路径**:
   - `webui/__init__.py`
   - `webui/app.py`
   - `webui/websocket.py`
   - `tests/unit/test_webui_app.py`
4. **预期实现要点**:
   - `webui/app.py`: FastAPI 应用，`GET /` 返回前端页面，`GET /api/status` 返回当前状态，`POST /api/hitl/{request_id}` 处理审批
   - `webui/websocket.py`: WebSocket 端点 `/ws`，实时推送 agent 状态（循环阶段、测试结果、失败分类、修正轮次、停机决策）
   - AgentLoop 通过事件回调推送状态到 WebSocket
   - HITL 审批通过 HTTP POST 或 WebSocket 消息
5. **需要先编写的失败测试**: `tests/unit/test_webui_app.py` — 测试 `GET /` 返回 HTML；测试 `GET /api/status` 返回 JSON；测试 WebSocket 连接和消息推送；测试 HITL 审批 POST
6. **Red 阶段验证命令与预期失败原因**:
   - 命令: `pytest tests/unit/test_webui_app.py -v`
   - 预期失败: `ModuleNotFoundError: No module named 'webui.app'`
7. **Green 阶段验证命令**: `pytest tests/unit/test_webui_app.py -v`
8. **完整测试、lint 和类型检查命令**:
   - `pytest tests/unit/test_webui_app.py -v`
   - `ruff check webui/ tests/unit/test_webui_app.py`
   - `mypy webui/app.py`
9. **依赖关系**: T18
10. **是否可并行**: 是（与 T19, T22, T23 并行）
11. **对应 worktree 和 PR 范围**: `feature/webui` / PR9
12. **完成状态及 commit hash 记录位置**: 本文件 T20 行；AGENT_LOG.md

**状态**: ✅ DONE | **Commit**: 5009627 (Red), 5236758 (Green), e8776ea (Review)

---

## T21: WebUI 前端

1. **TASK 编号**: T21
2. **目标**: 实现轻量 HTML/JS 前端，展示 agent 状态、测试结果、失败分类、修正轮次，提供 HITL 审批按钮。
3. **文件路径**:
   - `webui/static/index.html`
   - `webui/static/app.js`
   - `webui/static/style.css`
4. **预期实现要点**:
   - WebSocket 连接 `/ws`，实时显示 agent 状态
   - 显示：当前循环阶段（红/绿/重构）、测试结果（pass/fail 计数）、失败分类（类型+详情）、修正轮次追踪、停机决策
   - HITL 审批界面：显示待审批命令，approve/deny 按钮
   - 不使用 Open Design（§3.6 豁免），轻量 HTML/JS
5. **需要先编写的失败测试**: 手动验证（前端为 HTML/JS，不写自动化测试）。验证项：WebSocket 连接成功、状态实时更新、HITL 按钮可点击
6. **Red 阶段验证命令与预期失败原因**:
   - 命令: `pytest tests/unit/test_webui_app.py -v`（后端端点测试仍通过）
   - 预期失败: `GET /` 返回 404（index.html 不存在）
7. **Green 阶段验证命令**: `pytest tests/unit/test_webui_app.py -v` + 手动访问 `http://localhost:8000/` 确认前端加载
8. **完整测试、lint 和类型检查命令**:
   - `pytest tests/unit/test_webui_app.py -v`
   - `ruff check webui/`
9. **依赖关系**: T20
10. **是否可并行**: 否（依赖 T20）
11. **对应 worktree 和 PR 范围**: `feature/webui` / PR9
12. **完成状态及 commit hash 记录位置**: 本文件 T21 行；AGENT_LOG.md

**状态**: ⬜ TODO | **Commit**: —

---

## T22: Mock-LLM 集成测试

1. **TASK 编号**: T22
2. **目标**: 编写 mock-LLM 驱动的确定性集成测试，覆盖 agent 主循环端到端行为，不依赖网络和真实 LLM。
3. **文件路径**:
   - `tests/mock/__init__.py`
   - `tests/mock/test_agent_loop_mock.py`
4. **预期实现要点**:
   - 测试完整 TDD 循环：MockLLMClient 返回 write_file(测试) → run_tests(红) → write_file(实现) → run_tests(绿) → finish
   - 测试反馈驱动修正：注入失败 → agent 收到反馈 → 改变下一步动作
   - 测试治理拦截：MockLLMClient 请求 `rm -rf` → 被拦截 → HITL
   - 测试停机：全绿→PASS / 超轮次→MAX_ROUNDS / 卡死→STUCK
   - 测试记忆：记录后可检索
   - 全部确定性，无网络
5. **需要先编写的失败测试**: `tests/mock/test_agent_loop_mock.py` — 先编写所有测试用例，验证当前实现是否通过
6. **Red 阶段验证命令与预期失败原因**:
   - 命令: `pytest tests/mock/test_agent_loop_mock.py -v`
   - 预期失败: 集成测试发现的问题（如 AgentLoop 未正确处理 mock 响应序列）
7. **Green 阶段验证命令**: `pytest tests/mock/test_agent_loop_mock.py -v`
8. **完整测试、lint 和类型检查命令**:
   - `pytest tests/mock/test_agent_loop_mock.py -v`
   - `ruff check tests/mock/test_agent_loop_mock.py`
   - `mypy tests/mock/test_agent_loop_mock.py`
9. **依赖关系**: T18
10. **是否可并行**: 是（与 T19, T20, T23 并行）
11. **对应 worktree 和 PR 范围**: `feature/testing-demo` / PR10
12. **完成状态及 commit hash 记录位置**: 本文件 T22 行；AGENT_LOG.md

**状态**: ⬜ TODO | **Commit**: —

---

## T23: 机制演示（三项行为）

1. **TASK 编号**: T23
2. **目标**: 实现机制演示脚本 `demo/run_demo.py`，在 mock LLM 下确定性地复现三项行为：① 治理护栏拦截危险动作 ② 注入失败→反馈闭环使 agent 改变下一步 ③ 卡死检测→STUCK 停机。
3. **文件路径**:
   - `demo/__init__.py`
   - `demo/run_demo.py`
   - `tests/mock/test_mechanism_demo.py`
4. **预期实现要点**:
   - 演示①: MockLLMClient 请求 `run_command("rm -rf /tmp/test")` → CommandGuard 匹配 → HITL PENDING → 断言被拦截
   - 演示②: MockLLMClient 返回 write_file(测试) → run_tests(红, ASSERTION) → FeedbackInjector 注入 → 下一轮 MockLLMClient 返回 write_file(修正实现) → run_tests(绿) → 断言 agent 改变了动作
   - 演示③: MockLLMClient 连续返回相同失败 → RoundTracker.detect_loop() → STUCK 停机 → 断言 StopReason
   - `make demo` 运行演示
5. **需要先编写的失败测试**: `tests/mock/test_mechanism_demo.py` — 测试三个演示场景各自确定性通过
6. **Red 阶段验证命令与预期失败原因**:
   - 命令: `pytest tests/mock/test_mechanism_demo.py -v`
   - 预期失败: `ModuleNotFoundError: No module named 'demo.run_demo'`
7. **Green 阶段验证命令**: `pytest tests/mock/test_mechanism_demo.py -v` + `python -m demo.run_demo`
8. **完整测试、lint 和类型检查命令**:
   - `pytest tests/mock/test_mechanism_demo.py -v`
   - `ruff check demo/ tests/mock/test_mechanism_demo.py`
   - `mypy demo/run_demo.py`
9. **依赖关系**: T18
10. **是否可并行**: 是（与 T19, T20, T22 并行）
11. **对应 worktree 和 PR 范围**: `feature/testing-demo` / PR10
12. **完成状态及 commit hash 记录位置**: 本文件 T23 行；AGENT_LOG.md

**状态**: ⬜ TODO | **Commit**: —

---

## T24: GitHub Actions CI

1. **TASK 编号**: T24
2. **目标**: 配置 GitHub Actions，每次 push 自动运行测试、lint、类型检查。
3. **文件路径**:
   - `.github/workflows/ci.yml`
4. **预期实现要点**:
   - 触发: push to any branch, PR to main
   - Jobs: `test` (pytest), `lint` (ruff), `typecheck` (mypy)
   - Python 3.11+
   - 缓存 pip 依赖
   - `make test` 运行全部测试
4. **需要先编写的失败测试**: 验证 YAML 语法正确、job 名存在
5. **Red 阶段验证命令与预期失败原因**:
   - 命令: `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"`
   - 预期失败: `FileNotFoundError: '.github/workflows/ci.yml'`
6. **Green 阶段验证命令**: `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` + push 后检查 GitHub Actions 运行
7. **完整测试、lint 和类型检查命令**:
   - `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"`
   - `make test && make lint && make typecheck`
8. **依赖关系**: T01
9. **是否可并行**: 是（与 T25, T26 并行）
10. **对应 worktree 和 PR 范围**: `feature/ci` / PR11
11. **完成状态及 commit hash 记录位置**: 本文件 T24 行；AGENT_LOG.md

**状态**: ⬜ TODO | **Commit**: —

---

## T25: GitLab CI（.gitlab-ci.yml）

1. **TASK 编号**: T25
2. **目标**: 配置 `.gitlab-ci.yml`，包含一个名为 `unit-test` 的 job。
3. **文件路径**:
   - `.gitlab-ci.yml`
4. **预期实现要点**:
   - Job 名: `unit-test`（必须精确匹配）
   - Script: `make test`
   - Python 3.11+ 镜像
   - 缓存 pip 依赖
5. **需要先编写的失败测试**: 验证 YAML 语法正确、`unit-test` job 存在
6. **Red 阶段验证命令与预期失败原因**:
   - 命令: `python -c "import yaml; d=yaml.safe_load(open('.gitlab-ci.yml')); assert 'unit-test' in d"`
   - 预期失败: `FileNotFoundError: '.gitlab-ci.yml'`
7. **Green 阶段验证命令**: `python -c "import yaml; d=yaml.safe_load(open('.gitlab-ci.yml')); assert 'unit-test' in d"`
8. **完整测试、lint 和类型检查命令**:
   - `python -c "import yaml; d=yaml.safe_load(open('.gitlab-ci.yml')); assert 'unit-test' in d"`
   - `make test`
9. **依赖关系**: T01
10. **是否可并行**: 是（与 T24, T26 并行）
11. **对应 worktree 和 PR 范围**: `feature/ci` / PR11
12. **完成状态及 commit hash 记录位置**: 本文件 T25 行；AGENT_LOG.md

**状态**: ⬜ TODO | **Commit**: —

---

## T26: Dockerfile + PyPI 打包

1. **TASK 编号**: T26
2. **目标**: 创建 Dockerfile（`docker build` + `docker run` 可启动）和 PyPI 打包配置。
3. **文件路径**:
   - `Dockerfile`
   - `pyproject.toml`（更新，添加 `[project.scripts]` 入口点）
4. **预期实现要点**:
   - Dockerfile: 基于 `python:3.11-slim`，安装依赖，复制源码，暴露 8000 端口，启动 uvicorn
   - `docker build -t coding-agent-harness .` 可成功
   - `docker run -p 8000:8000 coding-agent-harness` 可启动 WebUI
   - PyPI: `pyproject.toml` 添加 `[project.scripts] harness = "harness.cli:main"`
   - 不写入 API key 到镜像层
5. **需要先编写的失败测试**: `docker build` 成功；`docker run` 启动后 `curl localhost:8000/` 返回 200
6. **Red 阶段验证命令与预期失败原因**:
   - 命令: `docker build -t coding-agent-harness . 2>&1 | tail -5`
   - 预期失败: `Error: No Dockerfile found`
7. **Green 阶段验证命令**: `docker build -t coding-agent-harness .` 成功
8. **完整测试、lint 和类型检查命令**:
   - `docker build -t coding-agent-harness .`
   - `make test && make lint && make typecheck`
9. **依赖关系**: T01
10. **是否可并行**: 是（与 T24, T25 并行）
11. **对应 worktree 和 PR 范围**: `feature/distribution` / PR12
12. **完成状态及 commit hash 记录位置**: 本文件 T26 行；AGENT_LOG.md

**状态**: ⬜ TODO | **Commit**: —

---

## T27: README

1. **TASK 编号**: T27
2. **目标**: 编写 README.md，包含 SPEC 要求的 6 个必选章节：项目简介、安装、运行、分发命令、目录结构、安全边界说明。另含第三方许可证列表。
3. **文件路径**:
   - `README.md`
4. **预期实现要点**:
   - 项目简介: 一句话描述 + 核心命题
   - 安装: `pip install coding-agent-harness` / `docker pull`
   - 运行: `harness run "需求描述"` / `docker run`
   - 分发命令: `docker build` / `pip install`
   - 目录结构: 树形图
   - 安全边界: 凭据管理（keyring/.env）、治理围栏、HITL
   - 第三方许可证: httpx, pyyaml, keyring, fastapi, uvicorn, pytest 等（MIT/BSD）
   - 已知限制: 平台/架构/依赖前提
5. **需要先编写的失败测试**: 验证 README 包含所有必选章节标题
6. **Red 阶段验证命令与预期失败原因**:
   - 命令: `grep -c "## " README.md`（检查章节数）
   - 预期失败: `README.md: No such file or directory`
7. **Green 阶段验证命令**: `grep "项目简介\|安装\|运行\|分发命令\|目录结构\|安全边界" README.md`（全部匹配）
8. **完整测试、lint 和类型检查命令**:
   - `grep "项目简介\|安装\|运行\|分发命令\|目录结构\|安全边界" README.md`
   - `make test`
9. **依赖关系**: T01-T26（需所有模块完成后才能准确描述）
10. **是否可并行**: 否（依赖所有前序 task）
11. **对应 worktree 和 PR 范围**: `feature/readme-deploy` / PR13
12. **完成状态及 commit hash 记录位置**: 本文件 T27 行；AGENT_LOG.md

**状态**: ⬜ TODO | **Commit**: —

---

## T28: Render 部署

1. **TASK 编号**: T28
2. **目标**: 将 WebUI 部署到 Render，提供可访问的公网 URL。
3. **文件路径**:
   - `render.yaml`（Render 配置，可选）
4. **预期实现要点**:
   - Render Docker 部署，使用 Dockerfile
   - 环境变量注入 API key（不写入镜像）
   - 提供公网 URL
   - 文档说明部署架构与 CI/CD
5. **需要先编写的失败测试**: 部署后 `curl <URL>/` 返回 200
6. **Red 阶段验证命令与预期失败原因**:
   - 命令: `curl -s -o /dev/null -w "%{http_code}" <URL>`
   - 预期失败: URL 不可访问（未部署）
7. **Green 阶段验证命令**: `curl -s -o /dev/null -w "%{http_code}" <URL>` 返回 200
8. **完整测试、lint 和类型检查命令**:
   - `curl -s -o /dev/null -w "%{http_code}" <URL>`
   - `make test`
9. **依赖关系**: T20, T26
10. **是否可并行**: 否（依赖 T20 和 T26）
11. **对应 worktree 和 PR 范围**: `feature/readme-deploy` / PR13
12. **完成状态及 commit hash 记录位置**: 本文件 T28 行；AGENT_LOG.md

**状态**: ⬜ TODO | **Commit**: —

---

## T29: 最终验收

1. **TASK 编号**: T29
2. **目标**: 执行全部验收标准（AC1-AC25），确认每条通过；更新 REQUIREMENTS_CHECKLIST.md 状态。
3. **文件路径**:
   - `REQUIREMENTS_CHECKLIST.md`（更新状态）
   - `PLAN.md`（更新所有 task 状态）
4. **预期实现要点**:
   - 逐条验证 AC1-AC25
   - 运行 `make test`（无网络，mock-LLM 核心测试通过）
   - 运行 `make lint && make typecheck`
   - 运行 `make demo`（三项行为确定性通过）
   - 验证 GitHub Actions pass
   - 验证 GitLab `unit-test` pass
   - 扫描源码和 Git 历史无真实凭据
   - 验证 Render WebUI URL 可访问
   - 验证 fresh-machine 安装说明
   - 更新 REQUIREMENTS_CHECKLIST.md 所有 R 状态为 DONE
5. **需要先编写的失败测试**: N/A（验收 task，不写新测试）
6. **Red 阶段验证命令与预期失败原因**:
   - 命令: `make test && make lint && make typecheck && make demo`
   - 预期失败: 任何未通过的检查
7. **Green 阶段验证命令**: `make test && make lint && make typecheck && make demo` 全部通过
8. **完整测试、lint 和类型检查命令**:
   - `make test && make lint && make typecheck && make demo`
   - `git log --all -p | grep -i "api_key\|secret\|password" || echo "CLEAN"`
9. **依赖关系**: T01-T28（所有前序 task）
10. **是否可并行**: 否（最终验收）
11. **对应 worktree 和 PR 范围**: `feature/readme-deploy` / PR13
12. **完成状态及 commit hash 记录位置**: 本文件 T29 行；AGENT_LOG.md；REQUIREMENTS_CHECKLIST.md

**状态**: ⬜ TODO | **Commit**: —

---

## 验证命令汇总

| 命令 | 用途 |
|---|---|
| `make test` | 运行全部测试（含 mock-LLM，无网络依赖） |
| `make test-unit` | 仅运行单元测试 |
| `make test-mock` | 仅运行 mock-LLM 集成测试 |
| `make lint` | ruff 代码检查 |
| `make typecheck` | mypy 类型检查 |
| `make demo` | 运行机制演示（三项行为） |
| `make build` | 构建 Docker 镜像 |
| `make ci` | 运行全部 CI 检查（test + lint + typecheck） |

---

## TDD 证据记录要求

每个 task 完成后，在 AGENT_LOG.md 中记录：
1. **Red**: 失败测试的命令输出（证明测试先于实现）
2. **Green**: 通过测试的命令输出（证明实现使测试通过）
3. **Refactor**: 重构后全部测试仍通过的输出

commit message 格式: `feat(TXX): <描述> [subagent: <ID>, human: <修改内容>]`
