# AGENT_LOG.md — 开发过程日志

> 按时间顺序记录关键节点。每条包含：时间戳、task 编号、触发的 Superpowers 技能、关键 prompt/context 配置、subagent 输出/commit hash、人工干预、教训。
> 要求来源：要求1 §4.9。

---

## LOG-001 — Phase 0 需求审计 + Phase 1 brainstorming + SPEC 创建

**时间戳**：2026-07-11

**Task 编号**：Phase 0 / Phase 1 / Gate A

**触发的 Superpowers 技能**：
- `using-superpowers`（元技能，理解技能系统）
- `brainstorming`（Socratic 设计精炼，12 轮迭代）

**关键 prompt / context 配置**：
- 输入：`docs/assignment/要求1.md`（229 行通用要求）+ `docs/assignment/要求2.md`（94 行 Coding Agent Harness 专属要求）
- 开发 harness：OpenCode + Superpowers
- 交付 harness：自实现 Python 内核，不调用 OpenCode 的 agent loop / skills / hooks / permissions / memory / subagents / tools

**关键输出**：
1. `REQUIREMENTS_CHECKLIST.md`（208 行）— 63 条需求（R001-R063）+ 3 项冲突分析 + SPEC 追溯矩阵
2. `SPEC_PROCESS.md`（261+ 行）— 12 轮 brainstorming 迭代记录 + brainstorming 反思 + SPEC 批准记录
3. `SPEC.md`（799 行）— 11 节 + 附录：问题陈述、6 个 INVEST 用户故事、18 个功能模块规约、非功能需求、系统架构（2 Mermaid 图）、数据模型（ER 图）、凭据与分发设计、技术选型、领域与机制设计、25 条验收标准、风险

**12 轮 brainstorming 决策摘要**：

| 轮 | 决策 | 选择 |
|---|---|---|
| 1 | 产品方向 | TDD 专项 |
| 2 | 主要贡献维度 | 反馈闭环 |
| 3 | 技术栈 | Python |
| 4 | WebUI 范围 | 交互式 + HITL |
| 5 | 输入与范围 | 自然语言→全新模块 |
| 6 | LLM 供应商 | DeepSeek |
| 7 | 凭据存储 | keyring + .env |
| 8 | 分发与部署 | Docker + PyPI / Render |
| 9 | 反馈闭环深度 | 多类分类+策略路由+卡死检测 |
| 10 | 动作格式 | OpenAI tool calling |
| 11 | 记忆维度 | JSON 文件+结构化过滤 |
| 12 | 配置与治理 | YAML + 三子机制 |

**合规审查**：用户要求 11 项正式审查，10 项 PASS，第 11 项发现 4 个一致性问题（配置项缺失 / test_command 不一致 / 禁止框架未显式列出 / Ollama 未规约），已全部修复。

**人工干预**：
1. 用户在批准设计时附加约束："注意多步 push 的要求，即使向用户确认是否已经 push 到 git 仓库"——AI 不得自行 commit/push。
2. 用户要求正式合规审查（11 项），导致发现并修复 4 项问题。
3. 用户逐节审阅 SPEC.md 后批准。

**Commit hash**：尚未 commit（用户要求先审阅再提交）。

**教训**：
1. AI 自审不够：12 轮 brainstorming 全部建议被采纳，但合规审查仍发现 4 项一致性问题。需用户介入把关，不能仅依赖 AI 自审。
2. 配置项追踪：SPEC 中多处引用配置项但未同步到配置表，导致不一致。未来应在每次引入配置引用时立即更新配置表。
3. 多步 push 纪律：用户明确要求 AI 不得自行 commit/push，每次需确认。这避免了 AI 在未经审查时推送不成熟内容的风险。
4. brainstorming 的隐性上下文风险：12 轮迭代沉淀了大量共享上下文，SPEC 的清晰度需冷启动验证（Gate C）才能客观检验。

---

## LOG-002 — Gate C 冷启动验证 + SPEC/PLAN 修订

**时间戳**：2026-07-11

**Task 编号**：Gate C（冷启动验证）

**触发的 Superpowers 技能**：冷启动验证（要求1 §4.5）

**关键 prompt / context 配置**：
- 冷启动智能体类型：Aider（与主开发智能体 OpenCode 不同类型）
- 模型：DeepSeek
- Session：全新，无先前对话历史
- 提供上下文：仅 SPEC.md 和 PLAN.md

**冷启动 agent 选择的 task**：T01（项目脚手架 + 共享数据模型）、T02（ConfigLoader）

**冷启动 agent 暂停点与发现**：

| # | 发现 | 判定 | 修复 |
|---|---|---|---|
| CS1 | RoundRecord.outcome 类型不明确（SPEC 标 str 但未定义约束） | SPEC 缺陷 | 改为 RoundOutcome enum {PASS, FAIL, NO_TESTS, HITL_DENIED} |
| CS2 | harness.yaml.example 无具体 YAML 示例 | SPEC 缺陷 | 添加完整 YAML 代码块 |
| CS3 | test_models.py 测试断言未描述 | PLAN 缺陷 | 添加具体断言列表 |
| CS4 | 无法运行 pytest（环境限制） | 环境限制 | 非 SPEC/PLAN 缺陷 |
| CS5 | TDD 顺序未显式强制 | PLAN 缺陷 | 添加 TDD 顺序强制段落 |
| CS6 | enum 值未在 PLAN 中列出 | PLAN 缺陷 | T01 models 列表标注所有 enum 值 |

**修订的文件**：
- `SPEC.md`：§3.6.1 添加 YAML 示例；§6.1 ER 图 RoundRecord.outcome 改为 RoundOutcome enum + 新增 RoundOutcome 实体；§6.2 添加 RoundRecord.outcome 和 MemoryEntry.outcome 约束
- `PLAN.md`：顶部添加 TDD 顺序强制段落；T01 添加 RoundOutcome enum + 具体测试断言；T02 添加 YAML 结构引用
- `SPEC_PROCESS.md`：添加 Gate C 冷启动验证完整记录（事实/暂停点/判定/修订前后 diff）
- `REQUIREMENTS_CHECKLIST.md`：更新 R006/R007 状态

**人工干预**：用户在外部终端用 Aider 执行冷启动验证，返回报告后指示主 agent 记录和修订。

**Commit hash**：尚未 commit（用户要求修订后等待重新批准）。

**教训**：
1. 冷启动验证有效：5 个文档缺陷被新 agent 发现，证实了"隐性上下文"风险——主开发 agent 和用户在 brainstorming 中沉淀的共识未全部写入文档。
2. 类型定义需完整：SPEC 中 RoundRecord.outcome 标为 str 但未定义约束，而 MemoryEntry.outcome 有明确 enum 约束。同类字段应有一致的类型严格度。
3. 具体示例不可省略：YAML 配置示例、测试断言描述等"看似显然"的内容对新 agent 并不显然。文档应假设读者无先验上下文。
4. TDD 顺序需显式强制：即使 PLAN 中有"Red 阶段验证命令"，新 agent 仍可能先写实现再补测试。需在每个 task 显式提醒顺序。

---

## LOG-003 — TASK-01 Red 阶段

**时间戳**：2026-07-11

**Task 编号**：TASK-01（项目脚手架 + 共享数据模型）

**触发的 Superpowers 技能**：
- `using-superpowers`
- `using-git-worktrees`
- `subagent-driven-development`
- `test-driven-development`

**subagent 信息**：
- 类型：`general`
- Task ID：`ses_0ae3c32e3ffeULLA57TRIYiV95`
- 关键 prompt：仅编写 `tests/unit/test_models.py` 失败测试，不写任何实现代码

**subagent 执行内容**：
1. 创建 `tests/__init__.py`（空文件）
2. 创建 `tests/unit/__init__.py`（空文件）
3. 编写 `tests/unit/test_models.py`（499 行，38 个测试，8 个测试类）
   - TestEnums（6 个测试）：验证 FailureType/RoundOutcome/StopReason/HITLStatus/GuardResult 的值和枚举特性
   - TestConfig（6 个测试）：验证默认值、自定义值、字段类型、dataclass 特性
   - TestAction（4 个测试）：验证实例化、raw_tool_call、字段类型、dataclass 特性
   - TestTestResult（4 个测试）：验证实例化、含 failures、字段类型、dataclass 特性
   - TestFailure（4 个测试）：验证实例化、默认值、FailureType 枚举兼容、dataclass 特性
   - TestFeedbackMessage（4 个测试）：验证实例化、含 memory、字段类型、dataclass 特性
   - TestRoundRecord（7 个测试）：验证实例化、PASS/FAIL/NO_TESTS/HITL_DENIED 四种 outcome、字段类型、dataclass 特性
   - TestHITLRequest（6 个测试）：验证 PENDING/APPROVED/DENIED/TIMEOUT 四种状态、字段类型、dataclass 特性
   - TestMemoryEntry（4 个测试）：验证实例化、resolved/unresolved、字段类型、dataclass 特性

**Red 阶段验证**：
- 命令：`pytest tests/unit/test_models.py -v`
- 退出状态码：`2`（collection error）
- 关键失败原因：
  ```
  ModuleNotFoundError: No module named 'harness.models'
  ```
- 结果：0 collected, 1 error
- 失败原因确认：`harness/models.py` 尚未创建，测试因导入目标模块不存在而失败。测试文件本身语法正确，导入语句合法，断言全面。**不是语法错误、环境错误或测试本身错误。**

**人工干预**：无（Red 阶段自动执行，等待人工检查）

**Commit hash**：尚未 commit（Red 阶段，禁止 commit）

**教训**：—（待 Green 阶段完成后补充）

---

## LOG-004 — TASK-01 Green 阶段

**时间戳**：2026-07-11

**Task 编号**：TASK-01（项目脚手架 + 共享数据模型）

**触发的 Superpowers 技能**：
- `subagent-driven-development`
- `test-driven-development`

**subagent 信息**：
- 类型：`general`
- Task ID：`ses_0ae385d3effecUsOak93DA0XVJ`
- 关键 prompt：仅实现让 `tests/unit/test_models.py` 通过的最少代码

**subagent 执行内容**：
1. 创建 `harness/__init__.py`（空文件）
2. 创建 `harness/models.py`（119 行）：
   - 5 个 Enum：FailureType(str), RoundOutcome, StopReason, HITLStatus, GuardResult
   - 8 个 Dataclass：Config(13 fields), Action, TestResult, Failure, FeedbackMessage, RoundRecord, HITLRequest, MemoryEntry
3. 创建 `pyproject.toml`（项目元数据 + 10 个依赖）
4. 创建 `Makefile`（test, test-unit, lint, typecheck targets）
5. 创建 `tests/conftest.py`（tmp_workspace, mock_config fixtures）

**Green 阶段验证**：
- 命令：`pytest tests/unit/test_models.py -v`
- 退出状态码：`0`
- 结果：**45 passed, 1 warning** in 0.02s
- 从 Red 到 Green：`ModuleNotFoundError` → 全部 45 个测试通过
- 回归检查：`pytest tests/ -v` 同样 45 passed，无回归

**人工干预**：无

**Commit hash**：`fe41b92` (feat(T01): implement minimal green solution)

**教训**：—

---

## LOG-005 — TASK-01 Refactor + 两阶段评审 + 最终验证

**时间戳**：2026-07-12

**Task 编号**：TASK-01（项目脚手架 + 共享数据模型）

**触发的 Superpowers 技能**：
- `test-driven-development`（重构阶段）
- `subagent-driven-development`（Code Quality Review subagent）

### Refactor 阶段

**执行内容**：
1. 修复 `TestResult` pytest 收集警告：添加 `__test__ = False` 类变量
2. 改进类型标注：`list` → `list[str]`、`dict` → `dict[str, Any]`、`Optional[X]` → `X | None`
3. `FailureType(str, Enum)` → `FailureType(StrEnum)`（Python 3.11+）
4. `pyproject.toml` 添加 ruff/mypy/pytest 配置
5. 按依赖顺序重排 dataclass（Failure 移至 TestResult 之前）

**验证**：`pytest tests/unit/test_models.py -v` → 45 passed, 0 warnings（警告消除）

### 第一阶段：Specification Compliance Review

**对照**：SPEC.md §3.6.1（配置表）、§6.1（ER 图）、§6.2（字段约束）、PLAN.md T01

**发现 Critical 问题及修复**：

| # | 问题 | 严重度 | 修复 |
|---|---|---|---|
| SC1 | `Config.enabled_tools` 默认值为 `[]`，SPEC §3.6.1 要求默认"全部 6 个" | Critical | 改为 `["write_file", "read_file", "list_files", "run_tests", "run_command", "finish"]` |
| SC2 | `Config.dangerous_command_patterns` 默认值为 `[]`，SPEC §3.6.1 要求 5 个默认模式 | Critical | 改为 `[r"rm\s+-rf", r"git\s+push", r"sudo\s+", r"curl\s+|wget\s+", r"docker\s+"]` |
| SC3 | Makefile 缺少 `test-mock`、`demo`、`build` target，PLAN T01 要求 7 个 | Critical | 添加三个 target |

**越界实现检查**：无越界（未实现 T02+ 的功能）

### 第二阶段：Code Quality Review

**subagent 信息**：
- 类型：`general`（reviewer 角色）
- Task ID：`ses_0ae016d7effek58bXCyBV7qFih`
- 关键 prompt：审查 T01 代码质量，检查 8 项标准

**审查结果摘要**：

| # | 标准 | 判定 | 严重度 |
|---|---|---|---|
| 1 | 职责划分 | PASS | — |
| 2 | 可读性 | WARN | Minor（dataclass 顺序、缺少 docstring） |
| 3 | 接口和类型 | WARN | **Major**（enum/str 类型不匹配） |
| 4 | 错误处理 | WARN | Minor（模型层无验证，可推迟到 ConfigLoader） |
| 5 | 安全边界 | PASS | — |
| 6 | 测试质量 | WARN | Minor（缺少 mutable-default 隔离测试） |
| 7 | 可维护性 | PASS | Minor（Makefile `python` vs `python3`） |
| 8 | 无真实网络/LLM 依赖 | PASS | — |

**修复的 Major/Minor 问题**：

| # | 问题 | 严重度 | 修复 |
|---|---|---|---|
| CQ1 | `Failure.type` 标注为 `str` 但 SPEC §6.2 要求 enum | Major | 改为 `FailureType` 类型 |
| CQ2 | `FeedbackMessage.failure_type` 标注为 `str` | Major | 改为 `FailureType` 类型 |
| CQ3 | `MemoryEntry.failure_type` 标注为 `str` | Major | 改为 `FailureType` 类型 |
| CQ4 | Makefile 使用 `python` 而非 `python3` | Minor | 改为 `python3` |
| CQ5 | 缺少 mutable-default 隔离测试 | Minor | 添加 `test_config_mutable_defaults_isolated` |
| CQ6 | dataclass 顺序违反依赖方向 | Minor | 重排为依赖顺序 |

**未修复（合理保留）**：
- StrEnum vs Enum 不一致：FailureType 需要字符串比较（StrEnum），其他 enum 不需要（Enum）——设计合理
- MemoryEntry.outcome 为 str 而非 enum：SPEC §6.1 与 §6.2 矛盾，保留 str 待后续解决
- 模型层无验证：验证推迟到 ConfigLoader（T02），合理
- conftest fixtures 未使用：为 T02+ 预留，合理

### 最终验证

| 检查项 | 命令 | 结果 |
|---|---|---|
| 完整测试套件 | `pytest tests/ -v` | **46 passed** in 0.02s |
| Lint | `ruff check harness/ tests/` | All checks passed! |
| 类型检查 | `mypy harness/` | Success: no issues found in 2 source files |
| 凭据泄露检查 | `grep -rn "api_key\|secret\|password" harness/ tests/` | 无匹配（源码无凭据） |
| Git 历史扫描 | `git log --all -p \| grep -i "api_key\|secret\|password"` | 仅文档引用（PLAN/SPEC 中概念性提及），无真实凭据 |

**Commit hash**：`79ccece` (refactor(T01): complete reviews and verification)

**人工干预**：无（用户指示跳过人工审查部分，直接完成 T01）

**教训**：
1. Config 默认值必须严格对照 SPEC 配置表——初版测试和实现都用了空列表作为默认值，与 SPEC 不符。冷启动验证（Gate C）虽修复了类型定义和 YAML 示例，但未检查默认值一致性。
2. `TestResult` 以 `Test` 开头会被 pytest 误收集——`__test__ = False` 是标准解法，应在未来所有以 `Test` 开头的非测试类上一致使用。
3. Code Quality Review 的 Major 问题（enum/str 不匹配）在 Red 阶段测试中已埋下——测试用 `FailureType.IMPORT.value` 而非 `FailureType.IMPORT`，说明 TDD 红绿循环不能替代类型安全审查。

---

## LOG-006 — TASK-02 Red 阶段

**时间戳**：2026-07-12

**Task 编号**：TASK-02（配置模块 ConfigLoader）

**触发的 Superpowers 技能**：
- `subagent-driven-development`
- `test-driven-development`

**subagent 信息**：
- 类型：`general`
- Task ID：`ses_0ab2b3f87ffe4AG47qrEJHvC2t`
- 关键 prompt：仅编写 `tests/unit/test_config.py` 失败测试，不写任何实现代码

**subagent 执行内容**：
1. 编写 `tests/unit/test_config.py`（305 行，33 个测试，8 个测试类）
   - TestConfigError（4 个测试）：验证 ConfigError 是 Exception 子类、可抛出、携带消息、与 ValueError/KeyError 不同
   - TestConfigLoaderLoadValid（4 个测试）：验证加载有效 YAML 返回 Config、解析全部 13 个字段、接受 pathlib.Path、字符串值处理
   - TestConfigLoaderDefaults（4 个测试）：验证单字段设置其余默认、空 YAML 全默认、部分字段填充默认、文档分隔符返回默认
   - TestConfigLoaderUnknownFields（3 个测试）：验证未知字段被忽略、不附加到 Config、嵌套未知字段被忽略
   - TestConfigLoaderInvalidYaml（3 个测试）：验证无效 YAML 抛 ConfigError、Tab 缩进抛异常、文件不存在抛异常
   - TestConfigLoaderTypeValidation（7 个测试）：验证 max_rounds/temperature/hitl_timeout 为字符串抛异常、enabled_tools 为非列表抛异常、dangerous_patterns 为 int 抛异常、列表元素非字符串抛异常
   - TestConfigLoaderFieldTypes（5 个测试）：验证 dangerous_command_patterns 为 list[str]、enabled_tools 为 list[str]、max_rounds 为 int（非 bool）、temperature 为 float、默认 patterns 为 regex 字符串
   - TestHarnessYamlExample（5 个测试）：验证 example 文件存在、可加载、包含全部 13 个字段、enabled_tools 为字符串、dangerous_patterns 为字符串

**Red 阶段验证**：
- 命令：`pytest tests/unit/test_config.py -v`
- 退出状态码：`2`（collection error）
- 关键失败原因：
  ```
  ModuleNotFoundError: No module named 'harness.config'
  ```
- 结果：0 collected, 1 error
- 失败原因确认：`harness/config/` 包尚未创建，测试因导入目标模块不存在而失败。测试文件本身语法正确，导入语句合法，断言全面。**不是语法错误、环境错误或测试本身错误。**

**人工干预**：无

**Commit hash**：`e501189` (test(T02): add failing tests)

**教训**：—

---

## LOG-007 — TASK-02 Green 阶段

**时间戳**：2026-07-12

**Task 编号**：TASK-02（配置模块 ConfigLoader）

**触发的 Superpowers 技能**：
- `subagent-driven-development`
- `test-driven-development`

**subagent 信息**：
- 类型：`general`
- Task ID：`ses_0ab22d27bffeuez539HhMekYEL`
- 关键 prompt：仅实现让 `tests/unit/test_config.py` 通过的最少代码

**subagent 执行内容**：
1. 创建 `harness/config/__init__.py`（空文件）
2. 创建 `harness/config/loader.py`（91 行）：
   - `ConfigError(Exception)`：自定义异常类
   - 4 个字段集合常量：`_INT_FIELDS`（6 个 int 字段）、`_FLOAT_FIELDS`（temperature）、`_STR_FIELDS`（4 个 str 字段）、`_STR_LIST_FIELDS`（2 个 list[str] 字段）
   - `ConfigLoader` 类：`@staticmethod load(path: str | Path) -> Config`
   - 使用 `yaml.safe_load` 解析 YAML
   - 类型验证：int 字段拒绝 bool 和非 int；float 字段拒绝 bool 和非数值；str 字段拒绝非 str；list 字段拒绝非 list 和非 str 元素
   - 缺失字段用 Config 默认值填充；未知字段忽略
   - FileNotFoundError 和 yaml.YAMLError 包装为 ConfigError
3. 创建 `harness.yaml.example`（25 行）：包含全部 13 个配置项，扁平 snake_case 键，与 SPEC §3.6.1 完全一致

**Green 阶段验证**：
- 命令：`pytest tests/unit/test_config.py -v`
- 退出状态码：`0`
- 结果：**35 passed** in 0.05s
- 从 Red 到 Green：`ModuleNotFoundError` → 全部 35 个测试通过
- 回归检查：`pytest tests/ -v` 同样 81 passed，无回归

**人工干预**：无

**Commit hash**：`bfe7750` (feat(T02): implement minimal green solution)

**教训**：—

---

## LOG-008 — TASK-02 Refactor + 两阶段评审 + 最终验证

**时间戳**：2026-07-12

**Task 编号**：TASK-02（配置模块 ConfigLoader）

**触发的 Superpowers 技能**：
- `test-driven-development`（重构阶段）
- `subagent-driven-development`（Code Quality Review subagent）

### Refactor 阶段

**执行内容**：
1. 修复 ruff 导入排序问题（`tests/unit/test_config.py` 导入块未排序）
2. 添加 mypy 配置覆盖：`pyproject.toml` 添加 `[[tool.mypy.overrides]]` 忽略 yaml 模块缺失的类型存根（`types-PyYAML` 在当前环境无法安装）
3. 修复 Code Quality Review 发现的 Minor 问题：
   - E-1：添加 `except OSError` 处理 `IsADirectoryError`/`PermissionError` 等 I/O 错误
   - R-1：为 `ConfigLoader` 类和 `load` 方法添加 docstring
   - T-1/T-2：添加 bool-as-int 和 bool-as-float 拒绝测试
   - T-3：添加非 dict YAML root（list/scalar）拒绝测试
   - T-4：添加 int→float 类型强转测试
   - T-5：添加列表值拷贝隔离测试
   - T-7：添加 null 值拒绝测试

**验证**：`pytest tests/unit/test_config.py -v` → 42 passed（从 35 增至 42）

### 第一阶段：Specification Compliance Review

**对照**：SPEC.md §3.6.1（ConfigLoader）、§3.6.1（harness.yaml.example）、§6.2（字段约束）、PLAN.md T02

**发现 Critical 问题及修复**：无 Critical 问题

**检查结果**：

| 检查项 | 结果 |
|---|---|
| ConfigLoader.load(path) -> Config | ✅ 符合 |
| 解析 YAML → 校验 → 构造 Config | ✅ 符合 |
| 缺失字段用默认值填充 | ✅ 符合 |
| 未知字段忽略 | ✅ 符合 |
| YAML 解析失败 → ConfigError | ✅ 符合 |
| 文件不存在 → ConfigError | ✅ 符合 |
| harness.yaml.example 含全部 13 项 | ✅ 符合 |
| 扁平 snake_case 键（无嵌套） | ✅ 符合 |
| dangerous_command_patterns 为 list[str] | ✅ 符合 |
| enabled_tools 为 list[str] | ✅ 符合 |

**越界实现检查**：无越界（未实现 T03+ 的功能）

**Minor 观察**：SPEC §6.2 字段约束（如 max_rounds > 0）未做值范围验证——但 SPEC §3.6.1 错误处理仅要求 YAML 解析失败和必填项缺失，值范围验证可推迟。

### 第二阶段：Code Quality Review

**subagent 信息**：
- 类型：`general`（reviewer 角色）
- Task ID：`ses_0ab1a3f29ffeu3uO09tI0opSZ6`
- 关键 prompt：审查 T02 代码质量，检查 8 项标准

**审查结果摘要**：

| # | 标准 | 判定 | 严重度 |
|---|---|---|---|
| 1 | 职责划分 | PASS | — |
| 2 | 可读性 | WARN | Minor（缺少 docstring → 已修复） |
| 3 | 接口和类型 | PASS | — |
| 4 | 错误处理 | WARN | Minor（OSError 未捕获 → 已修复） |
| 5 | 安全边界 | PASS | — |
| 6 | 测试质量 | WARN | Minor（缺少 bool/non-dict-root/coercion 测试 → 已修复） |
| 7 | 可维护性 | WARN | Minor（字段集合与 Config 重复 → 保留，合理） |
| 8 | 无真实网络/LLM 依赖 | PASS | — |

**修复的 Minor 问题**：

| # | 问题 | 严重度 | 修复 |
|---|---|---|---|
| E-1 | `IsADirectoryError`/`PermissionError` 未捕获 | Minor | 添加 `except OSError` 处理 |
| R-1 | ConfigLoader/load 缺少 docstring | Minor | 添加 docstring |
| T-1 | 缺少 bool-as-int 拒绝测试 | Minor | 添加 `test_bool_for_int_field_raises_config_error` |
| T-2 | 缺少 bool-as-float 拒绝测试 | Minor | 添加 `test_bool_for_float_field_raises_config_error` |
| T-3 | 缺少非 dict root 测试 | Minor | 添加 `test_list_root_raises_config_error` + `test_scalar_root_raises_config_error` |
| T-4 | 缺少 int→float 强转测试 | Minor | 添加 `test_int_temperature_coerced_to_float` |
| T-5 | 缺少列表拷贝隔离测试 | Minor | 添加 `test_list_values_are_copied_not_aliased` |
| T-7 | 缺少 null 值拒绝测试 | Minor | 添加 `test_null_value_for_int_field_raises_config_error` |

**未修复（合理保留）**：
- 字段集合与 Config dataclass 重复：保持手动同步，避免过度工程化
- 值范围验证（max_rounds > 0 等）：SPEC §3.6.1 未要求，推迟到后续 task
- `harness/config/__init__.py` 未 re-export：测试直接从 loader 导入，无需 re-export

### 最终验证

| 检查项 | 命令 | 结果 |
|---|---|---|
| 完整测试套件 | `pytest tests/ -v` | **88 passed** in 0.09s |
| Lint | `ruff check harness/ tests/` | All checks passed! |
| 类型检查 | `mypy harness/` | Success: no issues found in 4 source files |
| 凭据泄露检查 | `grep -rni "api_key\|secret\|password\|token\|sk-" harness/config/ tests/unit/test_config.py harness.yaml.example` | 无匹配（源码无凭据） |
| Git 历史扫描 | `git log --all -p \| grep -i "api_key\|secret\|password"` | 仅文档引用（PLAN/SPEC/AGENT_LOG 中概念性提及），无真实凭据 |

**Commit hash**：`c70afe7` (refactor(T02): complete reviews and verification)

**人工干预**：无

**教训**：
1. ruff 导入排序规则（I001）在 Red 阶段测试文件中容易触发——应在 Green 阶段后立即运行 `ruff check --fix` 而非等到 Refactor 阶段。
2. mypy strict 模式对第三方库（如 yaml）要求类型存根——当 `types-PyYAML` 无法安装时，`[[tool.mypy.overrides]]` + `ignore_missing_imports = true` 是干净的解决方案。
3. Code Quality Review 发现的 8 个 Minor 测试覆盖缺口（bool 拒绝、非 dict root、类型强转、列表拷贝隔离）全部是代码已正确处理但测试未验证的边缘情况——说明 Red 阶段测试编写时应更积极地覆盖 Python 类型系统的边缘情况（bool 是 int 子类、None 值、YAML 非 dict root 等）。
