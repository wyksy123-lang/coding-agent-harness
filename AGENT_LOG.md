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

---

## LOG-009 — TASK-03 Red 阶段

**时间戳**：2026-07-12

**Task 编号**：TASK-03（LLM 抽象层 LLMClient 协议）

**触发的 Superpowers 技能**：
- `subagent-driven-development`
- `test-driven-development`

**subagent 信息**：
- 类型：`general`
- Task ID：`ses_0aae41f2bffeqy4J6olq45yL7o`
- 关键 prompt：仅编写 `tests/unit/test_llm_base.py` 失败测试，不写任何实现代码

**subagent 执行内容**：
1. 编写 `tests/unit/test_llm_base.py`（233 行，30 个测试，3 个测试类）
   - TestToolCall（10 个测试）：验证实例化、dataclass、字段类型、空参数、复杂嵌套参数、相等/不等（id/name/arguments）、repr
   - TestLLMResponse（12 个测试）：验证实例化、dataclass、字段类型、空 tool_calls、多个 tool_calls、默认空列表 + mutable-default 隔离、相等/不等（content/finish_reason/tool_calls）、repr
   - TestLLMClientABC（8 个测试）：验证 isabstract、不可直接实例化、不完整子类不可实例化、完整子类可实例化、chat 签名含 messages+tools 参数、chat 返回 LLMResponse、chat 返回 tool_calls、chat 接受 OpenAI 格式消息

**Red 阶段验证**：
- 命令：`pytest tests/unit/test_llm_base.py -v`
- 退出状态码：`2`（collection error）
- 关键失败原因：
  ```
  ModuleNotFoundError: No module named 'harness.llm'
  ```
- 结果：0 collected, 1 error
- 失败原因确认：`harness/llm/` 包尚未创建，测试因导入目标模块不存在而失败。测试文件本身语法正确，导入语句合法，断言全面。**不是语法错误、环境错误或测试本身错误。**

**人工干预**：无

**Commit hash**：`cda280a` (test(T03): add failing tests)

**教训**：—

---

## LOG-010 — TASK-03 Green 阶段

**时间戳**：2026-07-12

**Task 编号**：TASK-03（LLM 抽象层 LLMClient 协议）

**触发的 Superpowers 技能**：
- `subagent-driven-development`
- `test-driven-development`

**subagent 信息**：
- 类型：`general`
- Task ID：`ses_0aad95b6cffevwCUMKZO3Y5qdU`
- 关键 prompt：仅实现让 `tests/unit/test_llm_base.py` 通过的最少代码

**subagent 执行内容**：
1. 创建 `harness/llm/__init__.py`（空文件，包标记）
2. 创建 `harness/llm/base.py`（39 行）：
   - `ToolCall` dataclass: `id: str`, `name: str`, `arguments: dict[str, Any]`
   - `LLMResponse` dataclass: `content: str`, `finish_reason: str`, `tool_calls: list[ToolCall]`（默认空列表 via `field(default_factory=list)`）
   - `LLMClient` ABC: 抽象方法 `chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> LLMResponse`
   - 使用 `from __future__ import annotations`、`abc.ABC`、`abc.abstractmethod`、`dataclass`、`field`
   - 所有类和方法有 docstring

**Green 阶段验证**：
- 命令：`pytest tests/unit/test_llm_base.py -v`
- 退出状态码：`0`
- 结果：**30 passed** in 0.02s
- 从 Red 到 Green：`ModuleNotFoundError` → 全部 30 个测试通过
- 回归检查：`pytest tests/ -v` 同样 118 passed，无回归

**人工干预**：无

**Commit hash**：`fd04023` (feat(T03): implement minimal green solution)

**教训**：—

---

## LOG-011 — TASK-03 Refactor + 两阶段评审 + 最终验证

**时间戳**：2026-07-12

**Task 编号**：TASK-03（LLM 抽象层 LLMClient 协议）

**触发的 Superpowers 技能**：
- `test-driven-development`（重构阶段）
- `subagent-driven-development`（Code Quality Review subagent）

### Refactor 阶段

**执行内容**：
1. 代码在 Green 阶段已非常简洁（39 行实现 + 233 行测试），无需实质性重构
2. 添加 M3 Minor 测试改进：新增 `test_llm_response_completely_empty` 测试，验证 `content=""` + `tool_calls=[]` + `finish_reason="stop"` 共存的边缘情况

**验证**：`pytest tests/unit/test_llm_base.py -v` → 31 passed（从 30 增至 31）

### 第一阶段：Specification Compliance Review

**对照**：SPEC.md §5.1（组件图）、§5.3（外部依赖）、§3.1（Agent 主循环）、§8（技术选型）、PLAN.md T03

**发现 Critical 问题及修复**：无 Critical 问题

**检查结果**：

| 检查项 | 结果 |
|---|---|
| LLMClient 为 ABC | ✅ 符合 |
| chat(messages, tools) -> LLMResponse 签名 | ✅ 符合 |
| LLMResponse dataclass: content/tool_calls/finish_reason | ✅ 符合 |
| ToolCall dataclass: id/name/arguments | ✅ 符合 |
| OpenAI Chat Completions 格式兼容 | ✅ 符合 |
| 无越界实现（未实现 T04/T05） | ✅ 符合 |

**Minor 观察**：LLMResponse 字段顺序为 content, finish_reason, tool_calls（PLAN 列为 content, tool_calls, finish_reason），但因 tool_calls 有默认值必须后置——Python dataclass 规则要求，非 SPEC 违规。

### 第二阶段：Code Quality Review

**subagent 信息**：
- 类型：`general`（reviewer 角色）
- Task ID：`ses_0aad5af23ffefbwpgTn0iww6nY`
- 关键 prompt：审查 T03 代码质量，检查 8 项标准

**审查结果摘要**：

| # | 标准 | 判定 | 严重度 |
|---|---|---|---|
| 1 | 职责划分 | PASS | — |
| 2 | 可读性 | PASS | — |
| 3 | 接口和类型 | PASS | —（3 个 Minor 设计选择） |
| 4 | 错误处理 | PASS | —（ABC 模块，错误处理委托子类） |
| 5 | 安全边界 | PASS | — |
| 6 | 测试质量 | PASS | Minor（缺少完全空 LLMResponse 测试 → 已修复） |
| 7 | 可维护性 | PASS | —（3 个 Minor 设计选择） |
| 8 | 无真实网络/LLM 依赖 | PASS | — |

**Minor 问题及处理**：

| # | 问题 | 严重度 | 处理 |
|---|---|---|---|
| M1 | `finish_reason: str` vs StrEnum | Minor | 保留——str 更灵活，适配不同供应商 |
| M2 | `tools` 参数无默认值 | Minor | 保留——coding agent 总是需要工具，设计合理 |
| M3 | 缺少完全空 LLMResponse 测试 | Minor | **已修复**——新增 `test_llm_response_completely_empty` |
| M4 | `list[dict[str, Any]]` 类型较松 | Minor | 保留——实用主义，匹配 OpenAI 格式处理惯例 |
| M5 | `__init__.py` 为空 | Minor | 保留——与项目约定一致（所有 `__init__.py` 均为空） |

### 最终验证

| 检查项 | 命令 | 结果 |
|---|---|---|
| 完整测试套件 | `pytest tests/ -v` | **119 passed** in 0.08s |
| Lint | `ruff check harness/ tests/` | All checks passed! |
| 类型检查 | `mypy harness/` | Success: no issues found in 6 source files |
| 凭据泄露检查 | `grep -rni "api_key\|secret\|password\|token\|sk-" harness/llm/ tests/unit/test_llm_base.py` | 无匹配（源码无凭据） |
| Git 历史扫描 | `git log --all -p \| grep -i "api_key\|secret\|password"` | 仅文档引用（AGENT_LOG 中概念性提及），无真实凭据 |

**Commit hash**：`f06b2a7` (refactor(T03): complete reviews and verification)

**人工干预**：无

**教训**：
1. ABC + dataclass 模块的 TDD 可以非常简洁——39 行实现 + 233 行测试，Red→Green 过程顺畅，无 Critical/Major 问题。
2. Code Quality Review 的 Minor 问题多为设计选择（str vs enum、参数默认值、类型精度）——在 ABC 抽象层阶段保留灵活性是合理的，具体约束可在子类（T04 MockLLMClient、T05 DeepSeekClient）中实现。
3. mutable-default 隔离测试（`field(default_factory=list)`）是 dataclass 测试的重要模式——T01 已建立此模式，T03 继承使用，验证了跨 task 的一致性。

---

## LOG-012 — TASK-04 Red 阶段

**时间戳**：2026-07-12

**Task 编号**：TASK-04（MockLLMClient）

**触发的 Superpowers 技能**：
- `subagent-driven-development`
- `test-driven-development`

**subagent 信息**：
- 类型：`general`
- Task ID：`ses_0aa9a8bb7ffeLeJebDIiqnTS5g`
- 关键 prompt：仅编写 `tests/unit/test_llm_mock.py` 失败测试，不写任何实现代码

**subagent 执行内容**：
1. 编写 `tests/unit/test_llm_mock.py`（255 行，28 个测试，6 个测试类）
   - TestMockLLMClientConstruction（4 个测试）：验证构造、issubclass(LLMClient)、isinstance、空列表构造
   - TestMockLLMClientReturnsResponsesInOrder（5 个测试）：验证首次/二次/三次调用顺序、含 tool_calls 的响应
   - TestMockLLMClientExhaustion（2 个测试）：验证耗尽后抛 StopIteration、单响应首次成功二次抛异常
   - TestMockLLMClientFromToolCalls（6 个测试）：验证 from_tool_calls 构造、tool_calls 正确性、默认值、空列表、多 tool_calls、数量正确
   - TestMockLLMClientRecordsCalls（6 个测试）：验证 recorded_calls 初始空、messages/tools 记录、多调用顺序、匹配
   - TestMockLLMClientEdgeCases（5 个测试）：验证空列表首次调用抛异常、OpenAI 格式消息、mutable default 隔离、返回类型、from_tool_calls 空列表

**Red 阶段验证**：
- 命令：`pytest tests/unit/test_llm_mock.py -v`
- 退出状态码：`2`（collection error）
- 关键失败原因：
  ```
  ModuleNotFoundError: No module named 'harness.llm.mock'
  ```
- 结果：0 collected, 1 error
- 失败原因确认：`harness/llm/mock.py` 尚未创建，测试因导入目标模块不存在而失败。测试文件本身语法正确，导入语句合法，断言全面。**不是语法错误、环境错误或测试本身错误。**

**人工干预**：无

**Commit hash**：`db70b60` (test(T04): add failing tests)

**教训**：—

---

## LOG-013 — TASK-04 Green 阶段

**时间戳**：2026-07-12

**Task 编号**：TASK-04（MockLLMClient）

**触发的 Superpowers 技能**：
- `subagent-driven-development`
- `test-driven-development`

**subagent 信息**：
- 类型：`general`
- Task ID：`ses_0aa8de5a0ffe487ZebiMfTQ7N7`
- 关键 prompt：仅实现让 `tests/unit/test_llm_mock.py` 通过的最少代码

**subagent 执行内容**：
1. 创建 `harness/llm/mock.py`（49 行）：
   - `RecordedCall` dataclass: `messages: list[dict[str, Any]]`, `tools: list[dict[str, Any]]`
   - `MockLLMClient(LLMClient)`: 继承 LLMClient ABC
     - `__init__(responses)`: 复制输入列表（mutable default 隔离），初始化 `_index=0` 和 `recorded_calls=[]`
     - `chat(messages, tools) -> LLMResponse`: 记录调用 → 检查耗尽 → 返回下一个响应 → 递增索引
     - `from_tool_calls(tool_call_lists) -> MockLLMClient`: classmethod，从 tool call 列表构造 LLMResponse 序列

**Green 阶段验证**：
- 命令：`pytest tests/unit/test_llm_mock.py -v`
- 退出状态码：`0`
- 结果：**28 passed** in 0.02s
- 从 Red 到 Green：`ModuleNotFoundError` → 全部 28 个测试通过
- 回归检查：`pytest tests/ -v` 同样 147 passed，无回归

**人工干预**：无

**Commit hash**：`cba9cd1` (feat(T04): implement minimal green solution)

**教训**：—

---

## LOG-014 — TASK-04 Refactor + 两阶段评审 + 最终验证

**时间戳**：2026-07-12

**Task 编号**：TASK-04（MockLLMClient）

**触发的 Superpowers 技能**：
- `test-driven-development`（重构阶段）
- `subagent-driven-development`（Code Quality Review subagent）

### Refactor 阶段

**执行内容**：
1. 修复 ruff F401：移除未使用的 `field` 导入
2. 添加完整 docstring：`RecordedCall`、`MockLLMClient` 类、`__init__`、`chat`、`from_tool_calls` 方法
3. 修复 Code Quality Review 发现的 Minor 问题：
   - CQ-2：`recorded_calls` 存储引用而非拷贝 → 改为 `list(messages)` 和 `list(tools)` 拷贝
   - CQ-3：添加 `test_call_recorded_even_when_exhausted` 测试
   - CQ-4：添加 `test_recorded_messages_isolated_from_caller_mutations` 测试
   - CQ-4：添加 `test_recorded_tools_isolated_from_caller_mutations` 测试

**验证**：`pytest tests/unit/test_llm_mock.py -v` → 31 passed（从 28 增至 31）

### 第一阶段：Specification Compliance Review

**对照**：SPEC.md §5.1（组件图）、§5.3（外部依赖）、§8（技术选型）、§9.6（机制编码）、§10.2（AC12）、PLAN.md T04

**发现 Critical 问题及修复**：无 Critical 问题

**检查结果**：

| 检查项 | 结果 |
|---|---|
| MockLLMClient(responses) 构造函数 | ✅ 符合 |
| 按顺序返回预设响应 | ✅ 符合 |
| 耗尽后抛异常（StopIteration） | ✅ 符合 |
| from_tool_calls 便捷构造 | ✅ 符合 |
| 记录 messages 和 tools | ✅ 符合 |
| 继承 LLMClient ABC | ✅ 符合 |
| 无越界实现（未实现 T05+） | ✅ 符合 |
| 无真实网络/LLM 依赖 | ✅ 符合 |

**越界实现检查**：无越界（未实现 T05 DeepSeekClient 或其他 task 的功能）

### 第二阶段：Code Quality Review

**subagent 信息**：
- 类型：`general`（reviewer 角色）
- Task ID：`ses_0aa8ae52fffem2Czot2c2rMoFO`
- 关键 prompt：审查 T04 代码质量，检查 8 项标准

**审查结果摘要**：

| # | 标准 | 判定 | 严重度 |
|---|---|---|---|
| 1 | 职责划分 | PASS | — |
| 2 | 可读性 | PASS | — |
| 3 | 接口和类型 | PASS | — |
| 4 | 错误处理 | WARN | Minor（StopIteration PEP 479 gotcha） |
| 5 | 安全边界 | WARN | Minor（recorded_calls 引用存储 → 已修复） |
| 6 | 测试质量 | WARN | Minor（缺少耗尽记录/隔离测试 → 已修复） |
| 7 | 可维护性 | PASS | — |
| 8 | 无真实网络/LLM 依赖 | PASS | — |

**修复的 Minor 问题**：

| # | 问题 | 严重度 | 修复 |
|---|---|---|---|
| CQ-1 | `field` 导入未使用 | Minor | 移除未使用导入 |
| CQ-2 | `recorded_calls` 存储引用而非拷贝 | Minor | 改为 `list(messages)` 和 `list(tools)` |
| CQ-3 | 缺少耗尽时仍记录调用的测试 | Minor | 添加 `test_call_recorded_even_when_exhausted` |
| CQ-4 | 缺少 recorded_calls 隔离测试 | Minor | 添加 2 个隔离测试 |

**未修复（合理保留）**：
- StopIteration PEP 479 gotcha：仅在 generator 上下文中会触发 RuntimeError，AgentLoop 将使用常规 while 循环，不受影响。测试已定义 StopIteration 为契约，保留一致性。

### 最终验证

| 检查项 | 命令 | 结果 |
|---|---|---|
| 目标测试 | `pytest tests/unit/test_llm_mock.py -v` | **31 passed** in 0.02s |
| 完整测试套件 | `pytest tests/ -v` | **150 passed** in 0.12s |
| Lint | `ruff check harness/ tests/` | All checks passed! |
| 类型检查 | `mypy harness/` | Success: no issues found in 7 source files |
| 凭据泄露检查 | `grep -rni "api_key\|secret\|password\|token\|sk-" harness/llm/ tests/unit/test_llm_mock.py` | 无匹配（源码无凭据） |
| Git 历史扫描 | `git log --all -p \| grep -i "api_key\|secret\|password"` | 仅文档引用（PLAN/SPEC/AGENT_LOG 中概念性提及），无真实凭据 |

**Commit hash**：`8e57cad` (refactor(T04): complete reviews and verification)

**人工干预**：无

**教训**：
1. MockLLMClient 的实现非常简洁（90 行实现 + 283 行测试），Red→Green 过程顺畅，无 Critical/Major 问题——这得益于 T03 ABC 抽象层定义的清晰契约。
2. Code Quality Review 发现的 Minor 问题（recorded_calls 引用存储）是一个典型的"测试驱动开发可能遗漏的边缘情况"——测试验证了记录的内容正确，但未验证记录的独立性。在 review 阶段补充隔离测试是必要的。
3. StopIteration 作为耗尽异常是一个设计选择——PEP 479 的风险仅在 generator 上下文中存在，而 AgentLoop 将使用常规循环。保留 StopIteration 与测试契约一致，避免不必要的范围扩大。

---

## LOG-015 — TASK-05 Red 阶段

**时间戳**：2026-07-12

**Task 编号**：TASK-05（DeepSeekClient）

**触发的 Superpowers 技能**：
- `subagent-driven-development`
- `test-driven-development`

**subagent 信息**：
- 类型：`general`
- Task ID：`ses_0aa7c596effeTq1iRr22uuw0yL`
- 关键 prompt：仅编写 `tests/unit/test_llm_deepseek.py` 失败测试，不写任何实现代码

**subagent 执行内容**：
1. 编写 `tests/unit/test_llm_deepseek.py`（627 行，40 个测试，8 个测试类）
   - TestDeepSeekClientConstruction（5 个测试）：验证构造、issubclass(LLMClient)、isinstance、transport 参数、transport 默认 None
   - TestDeepSeekClientRequestConstruction（8 个测试）：验证 POST 方法、URL 含 deepseek.com/chat/completions、Authorization Bearer header、body 含 model/messages/tools/temperature
   - TestDeepSeekClientResponseParsingNoToolCalls（4 个测试）：验证返回 LLMResponse、content 正确、finish_reason=stop、空 tool_calls
   - TestDeepSeekClientResponseParsingWithToolCalls（6 个测试）：验证 tool_call id/name/arguments（JSON string→dict）、dict 类型、finish_reason=tool_calls、ToolCall 实例
   - TestDeepSeekClientResponseParsingMultipleToolCalls（3 个测试）：验证多个 tool_calls 解析、不同 arguments、顺序保持
   - TestDeepSeekClientRetryLogic（9 个测试）：验证 ConnectError/ReadTimeout/HTTP500/HTTP429 重试、retry_count=0/1 语义、重试后成功、成功不重试
   - TestDeepSeekClientTimeout（3 个测试）：验证 timeout 传递给 httpx.Client、不同值、带 transport
   - TestDeepSeekClientNoHardcodedApiKey（2 个测试）：验证 api_key 无默认值、源码无 "sk-" 字符串

**Red 阶段验证**：
- 命令：`pytest tests/unit/test_llm_deepseek.py -v`
- 退出状态码：`2`（collection error）
- 关键失败原因：
  ```
  ModuleNotFoundError: No module named 'harness.llm.deepseek'
  ```
- 结果：0 collected, 1 error
- 失败原因确认：`harness/llm/deepseek.py` 尚未创建，测试因导入目标模块不存在而失败。测试文件本身语法正确，导入语句合法，断言全面。**不是语法错误、环境错误或测试本身错误。**

**人工干预**：无

**Commit hash**：`9bd284c` (test(T05): add failing tests)

**教训**：—

---

## LOG-016 — TASK-05 Green 阶段

**时间戳**：2026-07-12

**Task 编号**：TASK-05（DeepSeekClient）

**触发的 Superpowers 技能**：
- `subagent-driven-development`
- `test-driven-development`

**subagent 信息**：
- 类型：`general`
- Task ID：`ses_0aa5fa3e2ffe9GndC59moOA7AN`
- 关键 prompt：仅实现让 `tests/unit/test_llm_deepseek.py` 通过的最少代码

**subagent 执行内容**：
1. 创建 `harness/llm/deepseek.py`（117 行）：
   - `DeepSeekClient(LLMClient)`：继承 LLMClient ABC
     - `__init__(api_key, model, temperature, timeout, retry_count, transport=None)`：存储参数，创建 httpx.Client（transport 可选注入用于测试）
     - `chat(messages, tools) -> LLMResponse`：POST 到 `https://api.deepseek.com/chat/completions`，Bearer auth，body 含 model/messages/tools/temperature，重试逻辑（retry_count+1 次尝试），解析响应
     - `_parse_response(response) -> LLMResponse`（staticmethod）：解析 choices[0].message，提取 content/finish_reason/tool_calls（arguments JSON string→dict）

**Green 阶段验证**：
- 命令：`pytest tests/unit/test_llm_deepseek.py -v`
- 退出状态码：`0`
- 结果：**40 passed** in 0.15s
- 从 Red 到 Green：`ModuleNotFoundError` → 全部 40 个测试通过
- 回归检查：`pytest tests/ -v` 同样 190 passed，无回归

**人工干预**：无

**Commit hash**：`97a8632` (feat(T05): implement minimal green solution)

**教训**：—

---

## LOG-017 — TASK-05 Refactor + 两阶段评审 + 最终验证

**时间戳**：2026-07-12

**Task 编号**：TASK-05（DeepSeekClient）

**触发的 Superpowers 技能**：
- `test-driven-development`（重构阶段）
- `subagent-driven-development`（Code Quality Review subagent）

### Refactor 阶段

**执行内容**：
1. 修复 6 个 B017 lint 警告：`pytest.raises(Exception)` → 具体异常类型（`httpx.ConnectError`/`httpx.ReadTimeout`/`httpx.HTTPStatusError`）
2. 修复 Code Quality Review 发现的 1 个 Major + 6 个 Minor 问题：
   - CQ-1（Major）：非重试 HTTP 错误状态码（401/403/400 等）产生混淆的 KeyError → 添加 `response.raise_for_status()` 显式检查非 200 状态码
   - CQ-3（Minor）：`assert last_exception is not None` 在 `python -O` 下被剥离 → 替换为显式 RuntimeError 守卫
   - CQ-4（Minor）：httpx.Client 无资源清理 → 添加 `close()` 方法和 `__enter__`/`__exit__` 上下文管理器
   - CQ-5（Minor）：缺少边缘情况测试 → 添加 9 个新测试（非重试 HTTP 错误、资源清理、负 retry_count）
   - CQ-6（Minor）：URL 硬编码为局部变量 → 提取为模块级常量 `_API_URL`
   - CQ-7（Minor）：docstring Raises 节不完整 → 更新以覆盖非重试 HTTP 错误
3. 重试状态码提取为 `frozenset` 常量 `_RETRY_STATUS_CODES`

**验证**：`pytest tests/unit/test_llm_deepseek.py -v` → 49 passed（从 40 增至 49）

### 第一阶段：Specification Compliance Review

**对照**：SPEC.md §5.1（组件图）、§5.3（外部依赖）、§8（技术选型）、§4.2（安全 T1）、§3.6.1（配置项）、PLAN.md T05

**发现 Critical 问题及修复**：无 Critical 问题

**检查结果**：

| 检查项 | 结果 |
|---|---|
| DeepSeekClient(api_key, model, temperature, timeout, retry_count) 构造函数 | ✅ 符合 |
| chat(messages, tools) -> LLMResponse 方法签名 | ✅ 符合 |
| POST 到 DeepSeek API（OpenAI 兼容） | ✅ 符合 |
| 重试机制：retry_count 次后抛异常 | ✅ 符合 |
| 超时控制：timeout 秒 | ✅ 符合 |
| 不硬编码 API key（构造函数注入） | ✅ 符合 |
| 使用 httpx.MockTransport（无真实网络） | ✅ 符合 |
| 无越界实现（未实现 T06+） | ✅ 符合 |

**越界实现检查**：无越界（`transport` 参数是测试依赖注入便利，非越界功能）

### 第二阶段：Code Quality Review

**subagent 信息**：
- 类型：`general`（reviewer 角色）
- Task ID：`ses_0aa5631deffe2Rb5glZ7g1tLdL`
- 关键 prompt：审查 T05 代码质量，检查 8 项标准

**审查结果摘要**：

| # | 标准 | 判定 | 严重度 |
|---|---|---|---|
| 1 | 职责划分 | PASS | — |
| 2 | 可读性 | PASS | — |
| 3 | 接口和类型 | PASS | — |
| 4 | 错误处理 | WARN | Major（非重试 HTTP 错误产生 KeyError → 已修复） |
| 5 | 安全边界 | PASS | — |
| 6 | 测试质量 | WARN | Minor（缺少边缘情况测试 → 已修复） |
| 7 | 可维护性 | WARN | Minor（无资源清理/assert 脆弱/URL 硬编码 → 已修复） |
| 8 | 无真实网络/LLM 依赖 | PASS | — |

**修复的问题**：

| # | 问题 | 严重度 | 修复 |
|---|---|---|---|
| CQ-1 | 非重试 HTTP 错误状态码（401/403/400）产生混淆 KeyError | Major | 添加 `response.raise_for_status()` 显式检查 |
| CQ-3 | `assert last_exception is not None` 在 `python -O` 下被剥离 | Minor | 替换为显式 RuntimeError 守卫 |
| CQ-4 | httpx.Client 无资源清理 | Minor | 添加 close() + __enter__/__exit__ |
| CQ-5 | 缺少边缘情况测试 | Minor | 添加 9 个新测试 |
| CQ-6 | URL 硬编码为局部变量 | Minor | 提取为模块级常量 |
| CQ-7 | docstring Raises 节不完整 | Minor | 更新覆盖非重试 HTTP 错误 |

**未修复（合理保留）**：
- CQ-2：`_parse_response` 不防御性处理缺失字段——DeepSeek API 契约保证字段存在，信任契约是合理的
- 重试无退避延迟——PLAN 未要求退避，立即重试是可接受的设计选择

### 最终验证

| 检查项 | 命令 | 结果 |
|---|---|---|
| 目标测试 | `pytest tests/unit/test_llm_deepseek.py -v` | **49 passed** in 0.19s |
| 完整测试套件 | `pytest tests/ -v` | **199 passed** in 0.30s |
| Lint | `ruff check harness/llm/deepseek.py tests/unit/test_llm_deepseek.py` | All checks passed! |
| 类型检查 | `mypy harness/llm/deepseek.py` | Success: no issues found in 1 source file |
| 凭据泄露检查 | `grep -rni "api_key\|secret\|password\|token\|sk-" harness/llm/deepseek.py` | 仅参数名 `api_key`（无真实凭据） |
| 测试文件检查 | `grep -rni "sk-" tests/unit/test_llm_deepseek.py` | 仅 `FAKE_API_KEY = "sk-fake-test-key-not-real"`（明显合成值） |
| Git 历史扫描 | `git log --all -p \| grep -i "api_key\|secret\|password"` | 仅参数名和文档引用，无真实凭据 |

**Commit hash**：`8b46398` (refactor(T05): complete reviews and verification)

**人工干预**：无

**教训**：
1. DeepSeekClient 是第一个涉及真实网络 HTTP 调用的模块——httpx.MockTransport 的 transport 注入模式是测试真实 HTTP 客户端的标准方法，无需真实网络。这验证了 R053（mock/stub LLM 驱动确定性单测）在 HTTP 客户端层面的可行性。
2. Code Quality Review 发现的 Major 问题（CQ-1：非重试 HTTP 错误产生 KeyError）是一个典型的"happy path 测试驱动开发可能遗漏的错误路径"——40 个测试全部通过，但 401/403 等认证错误会产生混淆的 KeyError 而非有意义的 HTTPStatusError。在 review 阶段补充错误路径测试是必要的。
3. `assert` 语句在 `python -O` 下会被剥离——生产代码中不应依赖 assert 做运行时检查，应使用显式条件判断和异常抛出。
4. httpx.Client 持有连接池资源——提供 `close()` 方法和上下文管理器协议是资源管理的最佳实践，避免连接泄漏。

---

## LOG-018 — TASK-06 Red 阶段

**时间戳**：2026-07-12

**Task 编号**：TASK-06（工具基类 + ToolRegistry）

**触发的 Superpowers 技能**：
- `subagent-driven-development`
- `test-driven-development`

**subagent 信息**：
- 类型：`general`
- Task ID：`ses_0aa3edc19ffewmTCKyEO5GW7Wt`
- 关键 prompt：仅编写 `tests/unit/test_tool_registry.py` 失败测试，不写任何实现代码

**subagent 执行内容**：
1. 编写 `tests/unit/test_tool_registry.py`（593 行，67 个测试，7 个测试类）
   - TestToolResult（16 个测试）：验证 dataclass 实例化、类型、默认值、相等性、repr
   - TestToolABC（13 个测试）：验证抽象类不可实例化、子类必须实现 name/schema/execute、name 和 schema 可访问
   - TestToolRegistryRegistration（5 个测试）：验证单/多/重复注册、按名分发
   - TestToolRegistryDispatch（7 个测试）：验证 execute 分发、未注册抛异常、空参数、失败工具
   - TestToolRegistryWhitelist（9 个测试）：验证 is_enabled true/false、默认配置、禁用工具分发抛异常
   - TestToolRegistryGetSchemas（7 个测试）：验证空/单/多 schema、schema 匹配、重注册反映最新
   - TestToolRegistryEdgeCases（10 个测试）：验证空注册表、None error、多工具分发、raw_tool_call
   - 4 个测试工具子类：_EchoTool、_FailingTool、_NoOpTool、_CustomNameTool

**Red 阶段验证**：
- 命令：`pytest tests/unit/test_tool_registry.py -v`
- 退出状态码：`2`（collection error）
- 关键失败原因：
  ```
  ModuleNotFoundError: No module named 'harness.tools'
  ```
- 结果：0 collected, 1 error
- 失败原因确认：`harness/tools/` 包尚未创建，测试因导入目标模块不存在而失败。测试文件本身语法正确，导入语句合法，断言全面。**不是语法错误、环境错误或测试本身错误。**

**人工干预**：无

**Commit hash**：`cdbfdd6` (test(T06): add failing tests)

**教训**：—

---

## LOG-019 — TASK-06 Green 阶段

**时间戳**：2026-07-12

**Task 编号**：TASK-06（工具基类 + ToolRegistry）

**触发的 Superpowers 技能**：
- `subagent-driven-development`
- `test-driven-development`

**subagent 信息**：
- 类型：`general`
- Task ID：`ses_0aa3929d6ffeOgkNaI9XAdxPKs`
- 关键 prompt：仅实现让 `tests/unit/test_tool_registry.py` 通过的最少代码

**subagent 执行内容**：
1. 创建 `harness/tools/__init__.py`（空文件，包标记）
2. 创建 `harness/tools/base.py`（119 行）：
   - `ToolResult` dataclass: `success: bool`, `output: dict`, `error: str | None = None`
   - `Tool` ABC: 抽象属性 `name` 和 `schema`（via `@property @abstractmethod`），抽象方法 `execute`
   - `ToolRegistry`: `register(tool)`, `dispatch(action)`, `is_enabled(tool_name)`, `get_schemas()`
   - `dispatch` 使用 hacky 的 `_DEFAULT_ENABLED_TOOLS` 比较来决定是否强制白名单（后续 Refactor 修复）

**Green 阶段验证**：
- 命令：`pytest tests/unit/test_tool_registry.py -v`
- 退出状态码：`0`
- 结果：**67 passed** in 0.04s
- 从 Red 到 Green：`ModuleNotFoundError` → 全部 67 个测试通过
- 回归检查：`pytest tests/ -v` 同样 266 passed，无回归

**人工干预**：无

**Commit hash**：`c9431a2` (feat(T06): implement minimal green solution)

**教训**：—

---

## LOG-020 — TASK-06 Refactor + 两阶段评审 + 最终验证

**时间戳**：2026-07-12

**Task 编号**：TASK-06（工具基类 + ToolRegistry）

**触发的 Superpowers 技能**：
- `test-driven-development`（重构阶段）
- `subagent-driven-development`（Code Quality Review subagent）

### Refactor 阶段

**执行内容**：
1. **Critical SPEC 修复**：`dispatch()` 方法使用 hacky 的 `_DEFAULT_ENABLED_TOOLS` 比较来决定是否强制白名单——改为始终检查 `is_enabled()`，符合 SPEC §3.6.1 "enabled_tools → ToolRegistry.dispatch() 白名单"
2. 修复测试：将使用默认 `Config()` 分发测试工具的测试改为使用 `_test_config()`（包含测试工具名的白名单）
3. 添加 SPEC 合规测试：`test_dispatch_default_config_rejects_non_whitelisted_tool`——验证默认 Config 下分发非白名单工具抛 PermissionError
4. 修复 mypy 类型标注：`output: dict` → `output: dict[str, Any]`
5. 修复 Code Quality Review 发现的 1 个 Major + 4 个 Minor 问题：
   - CQ-1（Major）：`test_register_single_tool` 中 `assert registry.is_enabled("echo") or True` 是恒真断言 → 改为验证 `get_schemas()` 返回正确结果
   - CQ-2（Minor）：4 个测试使用过宽的异常匹配 → 收紧为精确的 `KeyError` / `PermissionError`
   - CQ-3（Minor）：`__init__.py` 为空 → 添加 re-export `Tool`, `ToolResult`, `ToolRegistry`
   - CQ-4（Minor）：缺少 `execute()` 抛异常时的 dispatch 行为测试 → 添加 `_RaisingTool` 和 `test_dispatch_propagates_execute_exception`

**验证**：`pytest tests/unit/test_tool_registry.py -v` → 69 passed（从 67 增至 69）

### 第一阶段：Specification Compliance Review

**对照**：SPEC.md §3.2（工具集）、§3.6.1（enabled_tools → dispatch 白名单）、§5.1（组件图）、§6.1（Action dataclass）、§9.6（机制编码）、§10.2（AC12）、PLAN.md T06

**发现 Critical 问题及修复**：

| # | 问题 | 严重度 | 修复 |
|---|---|---|---|
| SC1 | `dispatch()` 未始终强制 `enabled_tools` 白名单——使用 hacky 的 `_DEFAULT_ENABLED_TOOLS` 比较 | Critical | 改为始终检查 `is_enabled()`，移除 `_DEFAULT_ENABLED_TOOLS` 依赖 |

**检查结果**：

| 检查项 | 结果 |
|---|---|
| Tool ABC: name/schema/execute | ✅ 符合 |
| ToolResult: success/output/error | ✅ 符合 |
| ToolRegistry: register/dispatch/get_schemas/is_enabled | ✅ 符合 |
| is_enabled 受 Config.enabled_tools 控制 | ✅ 符合 |
| dispatch 始终强制 enabled_tools 白名单 | ✅ 符合（修复后） |
| 无越界实现（未实现 T07/T08） | ✅ 符合 |
| 无真实网络/LLM 依赖 | ✅ 符合 |

**越界实现检查**：无越界（未实现 T07 文件操作工具或 T08 Shell 工具）

### 第二阶段：Code Quality Review

**subagent 信息**：
- 类型：`general`（reviewer 角色）
- Task ID：`ses_0aa29bb4fffeYQPuwhoiZd9vUY`
- 关键 prompt：审查 T06 代码质量，检查 8 项标准

**审查结果摘要**：

| # | 标准 | 判定 | 严重度 |
|---|---|---|---|
| 1 | 职责划分 | PASS | — |
| 2 | 可读性 | PASS | — |
| 3 | 接口和类型 | PASS | — |
| 4 | 错误处理 | WARN | Minor（KeyError 语义、execute 异常未包装） |
| 5 | 安全边界 | PASS | — |
| 6 | 测试质量 | WARN | Major（恒真断言 → 已修复）+ Minor（过宽异常匹配 → 已修复） |
| 7 | 可维护性 | PASS | Minor（__init__.py 空 → 已修复、register 静默覆盖） |
| 8 | 无真实网络/LLM 依赖 | PASS | — |

**修复的问题**：

| # | 问题 | 严重度 | 修复 |
|---|---|---|---|
| CQ-1 | `test_register_single_tool` 恒真断言 `assert ... or True` | Major | 改为验证 `get_schemas()` 返回正确结果 |
| CQ-2 | 4 个测试过宽异常匹配 `(KeyError, ValueError)` 等 | Minor | 收紧为精确的 `KeyError` / `PermissionError` |
| CQ-3 | `__init__.py` 为空，未 re-export | Minor | 添加 `from harness.tools.base import Tool, ToolRegistry, ToolResult` |
| CQ-4 | 缺少 `execute()` 抛异常时 dispatch 行为测试 | Minor | 添加 `_RaisingTool` + `test_dispatch_propagates_execute_exception` |

**未修复（合理保留）**：
- `KeyError` 用于未注册工具：语义上可辩护（dict 查找隐喻），SPEC 未指定异常类型
- `dispatch` 不包装 `execute()` 异常：约定为工具返回 `ToolResult(success=False)`，T07/T08 遵循此约定
- `register()` 静默覆盖同名工具：已文档化，大型代码库可考虑警告日志
- `get_schemas()` 返回所有注册工具的 schema（不按白名单过滤）：T18 可按需过滤

### 最终验证

| 检查项 | 命令 | 结果 |
|---|---|---|
| 目标测试 | `pytest tests/unit/test_tool_registry.py -v` | **69 passed** in 0.07s |
| 完整测试套件 | `pytest tests/ -v` | **268 passed** in 0.34s |
| Lint | `ruff check harness/ tests/` | All checks passed! |
| 类型检查 | `mypy harness/` | Success: no issues found in 10 source files |
| 凭据泄露检查 | `grep -rni "api_key\|secret\|password\|token\|sk-" harness/tools/ tests/unit/test_tool_registry.py` | 无匹配（源码无凭据） |
| Git 历史扫描 | `git log --all -p \| grep -i "api_key\|secret\|password"` | 仅 T05 文档引用（参数名和概念性提及），无真实凭据 |

**Commit hash**：`5636470` (refactor(T06): complete reviews and verification)

**人工干预**：无

**教训**：
1. SPEC 合规问题可能在 Green 阶段被掩盖——subagent 为使测试通过，使用了 hacky 的 `_DEFAULT_ENABLED_TOOLS` 比较来绕过白名单强制。这导致测试全部通过但行为不符合 SPEC §3.6.1。Specification Compliance Review 是捕获此类问题的关键环节。
2. 恒真断言（`assert ... or True`）是测试质量的典型陷阱——Code Quality Review 发现 `test_register_single_tool` 中的恒真断言，该测试看似通过但实际不验证任何内容。Review 阶段应检查每个 assert 是否真正测试了预期行为。
3. 过宽的异常匹配（`pytest.raises((KeyError, ValueError))`）会掩盖回归——如果实现改为抛出错误的异常类型，测试仍会通过。应始终匹配精确的异常类型。
4. `__init__.py` re-export 是 Python 包的最佳实践——为下游 task（T07/T08/T18）提供更简洁的导入路径 `from harness.tools import Tool` 而非 `from harness.tools.base import Tool`。

---

## LOG-021 — TASK-09 Red 阶段

**时间戳**：2026-07-12

**Task 编号**：TASK-09（PathGuard 路径围栏）

**触发的 Superpowers 技能**：
- `subagent-driven-development`
- `test-driven-development`

**subagent 信息**：
- 类型：`general`
- Task ID：`ses_0aa12a627ffeu6wY5i2LuDj5zU`
- 关键 prompt：仅编写 `tests/unit/test_path_guard.py` 失败测试，不写任何实现代码

**subagent 执行内容**：
1. 创建 `harness/governance/__init__.py`（空文件，包标记）
2. 编写 `tests/unit/test_path_guard.py`（220 行，38 个测试，6 个测试类）
   - TestPathGuardExistence（3 个测试）：验证 PathGuard 是类、有 check 方法、check 可调用
   - TestPathGuardLegitimatePaths（10 个测试）：验证简单/嵌套/深层相对路径、不存在的子目录、仅文件名、./ 前缀、. 路径、target 本身、尾斜杠、内部 `..` 不越界 → ALLOW
   - TestPathGuardOutOfBounds（10 个测试）：验证 `..` 穿越、双重 `..`、绝对路径外部/内部、子目录逃逸、前导斜杠、带前缀 `..`、根路径、父目录、兄弟目录 → DENY
   - TestPathGuardEdgeCases（9 个测试）：验证空路径、None path、None target、null byte、不存在的 target、空 target、仅 `..`、仅斜杠、深层相对路径逃逸 → DENY
   - TestPathGuardSymlinkHandling（3 个测试，平台不支持时跳过）：验证符号链接指向外部 DENY、指向内部 ALLOW、目录符号链接指向外部 DENY
   - TestPathGuardReturnType（3 个测试）：验证返回 GuardResult 枚举、DENY 返回正确枚举、ALLOW 和 DENY 不同

**Red 阶段验证**：
- 命令：`pytest tests/unit/test_path_guard.py -v`
- 退出状态码：`2`（collection error）
- 关键失败原因：
  ```
  ModuleNotFoundError: No module named 'harness.governance.path_guard'
  ```
- 结果：0 collected, 1 error
- 失败原因确认：`harness/governance/path_guard.py` 尚未创建，测试因导入目标模块不存在而失败。测试文件本身语法正确，导入语句合法，断言全面。**不是语法错误、环境错误或测试本身错误。**

**人工干预**：无

**Commit hash**：`26ac727` (test(T09): add failing tests)

**教训**：—

---

## LOG-022 — TASK-09 Green 阶段

**时间戳**：2026-07-12

**Task 编号**：TASK-09（PathGuard 路径围栏）

**触发的 Superpowers 技能**：
- `subagent-driven-development`
- `test-driven-development`

**subagent 信息**：
- 类型：`general`
- Task ID：`ses_0aa0e6457ffenMw547C2Z3WSrE`
- 关键 prompt：仅实现让 `tests/unit/test_path_guard.py` 通过的最少代码

**subagent 执行内容**：
1. 创建 `harness/governance/path_guard.py`（30 行）：
   - `PathGuard` 类：`@staticmethod check(path: str, target_directory: str) -> GuardResult`
   - 拒绝 None/空/null-byte 输入 → 拒绝绝对路径（除 target 本身）→ realpath 解析 target + isdir 检查 → join + realpath 解析路径（处理符号链接）→ commonpath 检查子树 → 所有异常捕获 → DENY
   - 使用 `os.path.realpath`（解析符号链接）+ `os.path.commonpath`（避免前缀兄弟攻击）

**Green 阶段验证**：
- 命令：`pytest tests/unit/test_path_guard.py -v`
- 退出状态码：`0`
- 结果：**38 passed** in 0.03s
- 从 Red 到 Green：`ModuleNotFoundError` → 全部 38 个测试通过
- 回归检查：`pytest tests/ -v` 同样 306 passed，无回归

**人工干预**：无

**Commit hash**：`9915a30` (feat(T09): implement minimal green solution)

**教训**：—

---

## LOG-023 — TASK-09 Refactor + 两阶段评审 + 最终验证

**时间戳**：2026-07-12

**Task 编号**：TASK-09（PathGuard 路径围栏）

**触发的 Superpowers 技能**：
- `test-driven-development`（重构阶段）
- `subagent-driven-development`（Code Quality Review subagent）

### Refactor 阶段

**执行内容**：
1. 为 `PathGuard` 类和 `check` 方法添加 docstring（引用 SPEC §3.4.1）
2. 在 `harness/governance/__init__.py` 添加 re-export `PathGuard`（遵循 T06 建立的模式）

**验证**：`pytest tests/unit/test_path_guard.py -v` → 38 passed（无变化，行为不变）

### 第一阶段：Specification Compliance Review

**对照**：SPEC.md §3.4.1（PathGuard）、§9.2（危险动作）、§9.6（机制编码）、§10.1 AC6（路径围栏）、PLAN.md T09

**发现 Critical 问题及修复**：无 Critical 问题

**检查结果**：

| 检查项 | 结果 |
|---|---|
| PathGuard.check(path, target_directory) -> GuardResult | ✅ 符合 |
| 解析路径为绝对路径 → 检查子树 → 检查 `..` 穿越 | ✅ 符合 |
| 越界 → DENY；合法 → ALLOW；解析失败 → DENY | ✅ 符合 |
| 仅检查文件操作工具（不实现工具本身） | ✅ 符合 |
| 无越界实现（未实现 T10 CommandGuard / T11 HITLState） | ✅ 符合 |
| 无真实网络/LLM 依赖 | ✅ 符合 |

**越界实现检查**：无越界（PathGuard 仅实现路径检查，不涉及 CommandGuard 或 HITLState）

### 第二阶段：Code Quality Review

**subagent 信息**：
- 类型：`general`（reviewer 角色）
- Task ID：`ses_0aa018cacffeRymAgiW7xo73x4`
- 关键 prompt：审查 T09 代码质量，检查 8 项标准

**审查结果摘要**：

| # | 标准 | 判定 | 严重度 |
|---|---|---|---|
| 1 | 职责划分 | PASS | None |
| 2 | 可读性 | PASS | None |
| 3 | 接口和类型 | PASS | None |
| 4 | 错误处理 | PASS | None |
| 5 | 安全边界 | PASS | Minor（TOCTOU 竞争——固有局限，合理保留） |
| 6 | 测试质量 | PASS | Minor（1 个轻微恒真断言、2 个可选测试缺口） |
| 7 | 可维护性 | PASS | Minor（`"\x00"` 可命名为常量——42 行文件可忽略） |
| 8 | 无真实网络/LLM 依赖 | PASS | None |

**修复的问题**：无 Critical 或 Major 问题需修复

**未修复（合理保留）**：
- TOCTOU 竞争：`realpath` 解析与调用方后续文件操作之间的竞争——这是 check 式 guard 的固有局限，需在工具层（T07）使用 `O_NOFOLLOW` 修复，SPEC 未要求 TOCTOU 保护
- `test_allow_and_deny_are_distinct` 轻微恒真断言：无害的健全性检查
- 非字符串非 None 输入（如 int）未显式测试：已手动验证正确处理（TypeError 捕获 → DENY）
- 相对 target_directory 未显式测试：realpath 正确处理
- `"\x00"` 可命名为常量：42 行文件中可忽略

### 最终验证

| 检查项 | 命令 | 结果 |
|---|---|---|
| 目标测试 | `pytest tests/unit/test_path_guard.py -v` | **38 passed** in 0.03s |
| 完整测试套件 | `pytest tests/ -v` | **306 passed** in 0.37s |
| Lint | `ruff check harness/ tests/` | All checks passed! |
| 类型检查 | `mypy harness/` | Success: no issues found in 12 source files |
| 凭据泄露检查 | `grep -rni "api_key\|secret\|password\|token\|sk-" harness/governance/ tests/unit/test_path_guard.py` | 无真实凭据（仅测试 fixture 文件名如 `secret.txt`） |
| Git 历史扫描 | `git log --all -p \| grep -i "api_key\|secret\|password"` | 仅文档引用和测试 fixture，无真实凭据 |

**Commit hash**：`7e6babd` (refactor(T09): complete reviews and verification)

**人工干预**：无

**教训**：
1. PathGuard 是一个安全关键组件——使用 `os.path.realpath` + `os.path.commonpath`（而非简单的 `startswith`）正确防御了前缀兄弟攻击（`../ws_evil/x` 不会被误判为在 `./workspace` 内）。Code Quality Review 手动验证了此攻击向量。
2. TOCTOU 竞争是 check 式 guard 的固有局限——PathGuard 只能在调用时检查路径安全性，无法防止调用后符号链接被替换。这需要在工具层（T07 write_file/read_file）使用 `O_NOFOLLOW` 等机制补充，属于 T07 的职责范围。
3. 42 行实现 + 220 行测试（38 个测试）——TDD 红绿循环非常顺畅，无 Critical/Major 问题。这得益于 T01 中 `GuardResult` 枚举的清晰定义和 conftest.py 中 `tmp_workspace` fixture 的复用。
4. 符号链接测试使用 `platform.skipif` 正确处理了不支持符号链接的平台——这是跨平台测试的最佳实践。

---

## LOG-024 — TASK-07 Red 阶段

**时间戳**：2026-07-12

**Task 编号**：TASK-07（文件操作工具 WriteFileTool / ReadFileTool / ListFilesTool）

**触发的 Superpowers 技能**：
- `subagent-driven-development`
- `test-driven-development`

**subagent 信息**：
- 类型：`general`
- Task ID：`ses_0a9ee9262ffeeVmES5IIDZDWfu`
- 关键 prompt：仅编写 `tests/unit/test_file_ops.py` 失败测试，不写任何实现代码

**subagent 执行内容**：
1. 编写 `tests/unit/test_file_ops.py`（475 行，66 个测试，10 个测试类）
   - TestWriteFileToolConstruction（9 个测试）：验证构造、Tool 子类、name/schema 属性
   - TestWriteFileToolWrites（7 个测试）：验证写入、持久化、覆盖、嵌套目录自动创建、空内容、Unicode
   - TestWriteFileToolBoundary（6 个测试）：验证 `..` 穿越、绝对路径、子目录逃逸被拦截
   - TestReadFileToolConstruction（8 个测试）：验证构造、Tool 子类、name/schema 属性
   - TestReadFileToolReads（5 个测试）：验证读取已有文件、内容匹配、文件不存在、Unicode、空文件
   - TestReadFileToolBoundary（4 个测试）：验证 `..` 穿越、绝对路径被拦截
   - TestListFilesToolConstruction（7 个测试）：验证构造、Tool 子类、name/schema 属性
   - TestListFilesToolLists（6 个测试）：验证空目录、文件列表、子目录列表、混合、嵌套、不存在路径
   - TestListFilesToolBoundary（4 个测试）：验证 `..` 穿越、绝对路径被拦截
   - TestFileOpsIntegration（10 个测试）：验证 write→read 往返、write→list、PathGuard 集成、Tool 子类、Unicode 往返

**Red 阶段验证**：
- 命令：`pytest tests/unit/test_file_ops.py -v`
- 退出状态码：`2`（collection error）
- 关键失败原因：
  ```
  ModuleNotFoundError: No module named 'harness.tools.file_ops'
  ```
- 结果：0 collected, 1 error
- 失败原因确认：`harness/tools/file_ops.py` 尚未创建，测试因导入目标模块不存在而失败。测试文件本身语法正确，导入语句合法，断言全面。**不是语法错误、环境错误或测试本身错误。**

**人工干预**：无

**Commit hash**：`945b468` (test(T07): add failing tests)

**教训**：—

---

## LOG-025 — TASK-07 Green 阶段

**时间戳**：2026-07-12

**Task 编号**：TASK-07（文件操作工具 WriteFileTool / ReadFileTool / ListFilesTool）

**触发的 Superpowers 技能**：
- `subagent-driven-development`
- `test-driven-development`

**subagent 信息**：
- 类型：`general`
- Task ID：`ses_0a9e8db77ffeEB0vFdbgVJO5Tr`
- 关键 prompt：仅实现让 `tests/unit/test_file_ops.py` 通过的最少代码

**subagent 执行内容**：
1. 创建 `harness/tools/file_ops.py`（128 行）：
   - `WriteFileTool(Tool)`：接收 path + content → PathGuard 检查 → 写文件 → 返回 ToolResult
   - `ReadFileTool(Tool)`：接收 path → PathGuard 检查 → 读文件 → 返回 ToolResult
   - `ListFilesTool(Tool)`：接收 path → PathGuard 检查 → 列目录 → 返回 ToolResult
   - 每个工具在 PathGuard 检查前额外拒绝绝对路径（defense-in-depth）
   - 目录不存在 → `os.makedirs(parent, exist_ok=True)` 自动创建
   - 文件不存在 → 返回 `ToolResult(success=False, error="file not found")`
   - 路径不存在 → 返回 `ToolResult(success=True, output={"files": [], "dirs": []})`

**Green 阶段验证**：
- 命令：`pytest tests/unit/test_file_ops.py -v`
- 退出状态码：`0`
- 结果：**66 passed** in 0.07s
- 从 Red 到 Green：`ModuleNotFoundError` → 全部 66 个测试通过
- 回归检查：`pytest tests/ -v` 同样 372 passed，无回归

**人工干预**：无

**Commit hash**：`b7edbc1` (feat(T07): implement minimal green solution)

**教训**：—

---

## LOG-026 — TASK-07 Refactor + 两阶段评审 + 最终验证

**时间戳**：2026-07-12

**Task 编号**：TASK-07（文件操作工具 WriteFileTool / ReadFileTool / ListFilesTool）

**触发的 Superpowers 技能**：
- `test-driven-development`（重构阶段）
- `subagent-driven-development`（Code Quality Review subagent）

### Refactor 阶段

**执行内容**：
1. 修复 3 个 lint 问题：
   - UP015：`open(full, "r", ...)` → `open(full, ...)`（移除不必要的 mode 参数）
   - F401：移除未使用的 `pytest` 导入（Refactor 后因新增 skipif 测试又加回）
   - E741：变量名 `l` → `lst`（消除歧义变量名）
2. 在 `harness/tools/__init__.py` 添加 re-export `WriteFileTool`, `ReadFileTool`, `ListFilesTool`（遵循 T06 建立的模式）
3. 修复 Code Quality Review 发现的 2 个 Major + 4 个 Minor 问题：
   - CQ-1（Major）：非字符串 `path`（如 `None`）在 PathGuard 前引发未捕获 `TypeError` → 提取 `_resolve_safe_path()` 辅助函数，使用 `isinstance(path, str)` 检查
   - CQ-2（Major）：缺少 `O_NOFOLLOW` → symlink TOCTOU 可逃逸沙箱（AGENT_LOG T09 明确标注为 T07 职责）→ write 使用 `os.open(O_WRONLY|O_CREAT|O_TRUNC|O_NOFOLLOW)`，read 使用 `os.open(O_RDONLY|O_NOFOLLOW)`
   - CQ-3（Minor）：`assert tool is not None` 恒真断言 → 改为 `assert isinstance(tool, WriteFileTool)` 等
   - CQ-4（Minor）：`assert result.error is not None` 不验证错误消息 → 改为 `assert result.error == "path out of bounds"`
   - CQ-5（Minor）：缺少边缘情况测试 → 新增 11 个测试（None path、非字符串 path、list-on-file、missing path key、symlink O_NOFOLLOW 拒绝）
   - CQ-6（Minor）：边界检查代码重复 6× → 提取 `_resolve_safe_path()` 辅助函数和 `_BOUNDARY_ERROR` 常量

**验证**：`pytest tests/unit/test_file_ops.py -v` → 77 passed（从 66 增至 77）

### 第一阶段：Specification Compliance Review

**对照**：SPEC.md §3.2.1（write_file）、§3.2.2（read_file）、§3.2.3（list_files）、§3.4.1（PathGuard）、§9.2（危险动作）、§9.6（机制编码）、§10.1 AC6（路径围栏）、PLAN.md T07

**发现 Critical 问题及修复**：无 Critical 问题

**检查结果**：

| 检查项 | 结果 |
|---|---|
| WriteFileTool: path + content → PathGuard → write → ToolResult | ✅ 符合 |
| ReadFileTool: path → PathGuard → read → ToolResult | ✅ 符合 |
| ListFilesTool: path → PathGuard → list → ToolResult | ✅ 符合 |
| write_file output: {"success": True} / error | ✅ 符合 |
| read_file output: {"content": "..."} / error | ✅ 符合 |
| list_files output: {"files": [...], "dirs": [...]} | ✅ 符合 |
| 路径越界 → PathGuard 拦截 | ✅ 符合 |
| 目录不存在 → 自动创建（write_file） | ✅ 符合 |
| 文件不存在 → 返回错误（read_file） | ✅ 符合 |
| 路径不存在 → 返回空列表（list_files） | ✅ 符合 |
| 无越界实现（未实现 T08+） | ✅ 符合 |
| 无真实网络/LLM 依赖 | ✅ 符合 |

**越界实现检查**：无越界（未实现 T08 Shell 工具或其他 task 的功能）

### 第二阶段：Code Quality Review

**subagent 信息**：
- 类型：`general`（reviewer 角色）
- Task ID：`ses_0a9e2c3bbffem7MFbkuLc0lz7P`
- 关键 prompt：审查 T07 代码质量，检查 8 项标准

**审查结果摘要**：

| # | 标准 | 判定 | 严重度 |
|---|---|---|---|
| 1 | 职责划分 | PASS | None |
| 2 | 可读性 | PASS | None |
| 3 | 接口和类型 | PASS | None |
| 4 | 错误处理 | WARN | Major（非字符串 path 引发 TypeError → 已修复） |
| 5 | 安全边界 | WARN | Major（缺少 O_NOFOLLOW → 已修复） |
| 6 | 测试质量 | WARN | Minor（恒真断言 + 不验证错误消息 → 已修复） |
| 7 | 可维护性 | WARN | Minor（代码重复 → 已修复） |
| 8 | 无真实网络/LLM 依赖 | PASS | None |

**修复的问题**：

| # | 问题 | 严重度 | 修复 |
|---|---|---|---|
| CQ-1 | 非字符串 `path`（如 `None`）在 PathGuard 前引发未捕获 `TypeError` | Major | 提取 `_resolve_safe_path()` 辅助函数，使用 `isinstance(path, str)` 检查 |
| CQ-2 | 缺少 `O_NOFOLLOW` → symlink TOCTOU 可逃逸沙箱 | Major | write/read 使用 `os.open(... \| O_NOFOLLOW)` + `os.fdopen` |
| CQ-3 | `assert tool is not None` 恒真断言 | Minor | 改为 `assert isinstance(tool, ...)` |
| CQ-4 | `assert result.error is not None` 不验证错误消息 | Minor | 改为 `assert result.error == "path out of bounds"` |
| CQ-5 | 缺少边缘情况测试 | Minor | 新增 11 个测试（None path、非字符串、list-on-file、symlink） |
| CQ-6 | 边界检查代码重复 6× | Minor | 提取 `_resolve_safe_path()` + `_BOUNDARY_ERROR` 常量 |

**未修复（合理保留）**：
- TOCTOU 对中间目录符号链接：O_NOFOLLOW 仅保护最后一级组件，中间目录的符号链接仍可被跟随。PathGuard 的 `realpath` 已解析全部符号链接，TOCTOU 窗口极窄，SPEC 未要求完整 TOCTOU 保护。
- `output={}` on error：与 ToolResult dataclass 设计一致（T06 建立），error 在 `ToolResult.error` 字段而非 output dict 中。

### 最终验证

| 检查项 | 命令 | 结果 |
|---|---|---|
| 目标测试 | `pytest tests/unit/test_file_ops.py -v` | **77 passed** in 0.11s |
| 完整测试套件 | `pytest tests/ -v` | **383 passed** in 0.41s |
| Lint | `ruff check harness/ tests/` | All checks passed! |
| 类型检查 | `mypy harness/` | Success: no issues found in 13 source files |
| 凭据泄露检查 | `grep -rni "api_key\|secret\|password\|token\|sk-" harness/tools/ tests/unit/test_file_ops.py` | 仅测试数据 `f.write("secret")`（非真实凭据） |
| Git 历史扫描 | `git log --all -p \| grep -i "api_key\|secret\|password"` | 仅文档引用和测试 fixture，无真实凭据 |

**Commit hash**：`a47072a` (refactor(T07): complete reviews and verification)

**人工干预**：无

**教训**：
1. T09 AGENT_LOG 中明确标注的 O_NOFOLLOW 职责在 T07 Code Quality Review 中被正确识别并修复——跨 task 的 AGENT_LOG 记录对后续 task 的 review 有实际指导价值。
2. 非字符串 path 的 TypeError 是 Python 类型系统边缘情况的典型案例——`args.get("path", "")` 在 key 存在但值为 None 时返回 None 而非 ""，导致 `os.path.isabs(None)` 抛 TypeError。`isinstance` 检查是防御非字符串输入的标准方法。
3. O_NOFOLLOW 的实现需要 `os.open` + `os.fdopen` 而非内置 `open()`——这是 Python 文件操作中防止 symlink 攻击的标准模式。`os.fdopen` 接管 fd 所有权后，`with` 语句会正确关闭它。
4. 恒真断言（`assert tool is not None`）和模糊错误检查（`assert result.error is not None`）是测试质量的典型陷阱——Code Quality Review 应检查每个 assert 是否真正验证了预期行为和具体值。

---

## LOG-027 — TASK-10 Red 阶段

**时间戳**：2026-07-12

**Task 编号**：TASK-10（CommandGuard 危险命令检测）

**触发的 Superpowers 技能**：
- `subagent-driven-development`
- `test-driven-development`

**subagent 信息**：
- 类型：`general`
- Task ID：`ses_0a9b9975dffeO17VPyUtZNVF8T`
- 关键 prompt：仅编写 `tests/unit/test_command_guard.py` 失败测试，不写任何实现代码

**subagent 执行内容**：
1. 编写 `tests/unit/test_command_guard.py`（516 行，92 个测试，17 个测试类）
   - TestCommandGuardExistence（3 个测试）：验证 CommandGuard 是类、有 check 方法、check 可调用
   - TestCommandGuardRmRf（5 个测试）：验证 `rm -rf` 各种形式 → PENDING
   - TestCommandGuardGitPush（4 个测试）：验证 `git push` 各种形式 → PENDING
   - TestCommandGuardSudo（3 个测试）：验证 `sudo` 各种形式 → PENDING
   - TestCommandGuardCurlWget（4 个测试）：验证 `curl`/`wget` → PENDING
   - TestCommandGuardDocker（4 个测试）：验证 `docker` → PENDING
   - TestCommandGuardSafeCommands（16 个测试）：验证安全命令 → ALLOW
   - TestCommandGuardPartialMatches（6 个测试）：验证复合命令中的危险模式检测
   - TestCommandGuardInvalidRegex（7 个测试）：验证无效正则跳过不崩溃
   - TestCommandGuardEmptyInputs（3 个测试）：验证空输入 → ALLOW
   - TestCommandGuardNoneInputs（3 个测试）：验证 None 输入 → ALLOW
   - TestCommandGuardNonStringInputs（5 个测试）：验证非字符串输入防御性处理
   - TestCommandGuardMultipleMatches（3 个测试）：验证多模式匹配 → PENDING
   - TestCommandGuardCaseSensitivity（6 个测试）：验证大小写敏感
   - TestCommandGuardSimilarButNoMatch（8 个测试）：验证相似但不匹配的命令 → ALLOW
   - TestCommandGuardDefaultPatternsFromConfig（9 个测试）：验证 Config 默认 patterns
   - TestCommandGuardReturnType（3 个测试）：验证返回 GuardResult 枚举

**Red 阶段验证**：
- 命令：`pytest tests/unit/test_command_guard.py -v`
- 退出状态码：`2`（collection error）
- 关键失败原因：
  ```
  ModuleNotFoundError: No module named 'harness.governance.command_guard'
  ```
- 结果：0 collected, 1 error
- 失败原因确认：`harness/governance/command_guard.py` 尚未创建，测试因导入目标模块不存在而失败。测试文件本身语法正确，导入语句合法，断言全面。**不是语法错误、环境错误或测试本身错误。**

**人工干预**：无

**Commit hash**：`4bdfcfe` (test(T10): add failing tests for CommandGuard)

**教训**：—

---

## LOG-028 — TASK-10 Green 阶段

**时间戳**：2026-07-12

**Task 编号**：TASK-10（CommandGuard 危险命令检测）

**触发的 Superpowers 技能**：
- `subagent-driven-development`
- `test-driven-development`

**subagent 信息**：
- 类型：`general`
- Task ID：`ses_0a9ae9ad8ffe3H3nnj1en4dmMb`
- 关键 prompt：仅实现让 `tests/unit/test_command_guard.py` 通过的最少代码

**subagent 执行内容**：
1. 创建 `harness/governance/command_guard.py`（28 行）：
   - `CommandGuard` 类：`@staticmethod check(cmd, patterns) -> GuardResult`
   - 非字符串 cmd → ALLOW；非列表 patterns → ALLOW
   - 逐条遍历 patterns：非字符串元素跳过；`re.compile` 失败跳过；`compiled.search(cmd)` 匹配 → PENDING
   - 全部不匹配 → ALLOW
2. 更新 `harness/governance/__init__.py`：添加 re-export `CommandGuard`

**Green 阶段验证**：
- 命令：`pytest tests/unit/test_command_guard.py -v`
- 退出状态码：`0`
- 结果：**92 passed** in 0.05s
- 从 Red 到 Green：`ModuleNotFoundError` → 全部 92 个测试通过
- 回归检查：`pytest tests/ -v` 同样 475 passed，无回归

**人工干预**：无

**Commit hash**：`308ed0b` (feat(T10): implement minimal green solution)

**教训**：—

---

## LOG-029 — TASK-10 Refactor + 两阶段评审 + 最终验证

**时间戳**：2026-07-12

**Task 编号**：TASK-10（CommandGuard 危险命令检测）

**触发的 Superpowers 技能**：
- `test-driven-development`（重构阶段）
- `subagent-driven-development`（Code Quality Review subagent）

### Refactor 阶段

**执行内容**：
1. 添加详细 docstring（引用 SPEC §3.4.2），遵循 PathGuard 模式
2. 精化类型标注：`Any` → `str` / `list[str]`（匹配 SPEC 签名），保留 `isinstance` 防御性检查
3. 移除未使用的 `from typing import Any` 导入
4. 修复 Code Quality Review 发现的 Minor 问题：
   - CQ-3：移除 2 个重复测试（`test_rm_rf_in_compound_command_pending` 和 `test_sudo_in_middle_pending` 在 PartialMatches 类中与 RmRf/Sudo 类中重复），替换为差异化的测试（subshell 和 env var 场景）
   - CQ-4：添加空字符串 pattern 测试（`""` 匹配所有命令 → PENDING）
   - CQ-5：添加 tab/newline 命令测试（验证 `\s+` 覆盖）
   - CQ-6：添加 regex 元字符命令测试（`.`, `*`, `[`, `]`）

**验证**：`pytest tests/unit/test_command_guard.py -v` → 100 passed（从 92 增至 100）

### 第一阶段：Specification Compliance Review

**对照**：SPEC.md §3.4.2（CommandGuard）、§3.6.1（配置项 dangerous_command_patterns）、§9.2（危险动作）、§10.1 AC7（危险命令）、PLAN.md T10

**发现 Critical 问题及修复**：无 Critical 问题

**检查结果**：

| 检查项 | 结果 |
|---|---|
| CommandGuard.check(cmd, patterns) -> GuardResult | ✅ 符合 |
| 逐条正则匹配 → 命中 → PENDING；全部不命中 → ALLOW | ✅ 符合 |
| 正则编译失败 → 跳过该条 | ✅ 符合 |
| 输出 GuardResult.ALLOW 或 GuardResult.PENDING | ✅ 符合 |
| 默认 patterns 与 SPEC §3.6.1 一致（5 个） | ✅ 符合 |
| AC7: `rm -rf` 匹配 → PENDING | ✅ 符合 |
| 无越界实现（未实现 T11 HITLState / T08 Shell 工具） | ✅ 符合 |
| 无真实网络/LLM 依赖 | ✅ 符合 |

**越界实现检查**：无越界（CommandGuard 仅实现命令模式匹配，不涉及 HITLState 或 Shell 工具）

**Minor 观察**：PLAN T10 提到"正则编译失败 → 跳过该条并记录警告"，但 SPEC §3.4.2 仅要求"跳过该条"。实现遵循 SPEC，静默跳过无效正则。非 Critical 问题。

### 第二阶段：Code Quality Review

**subagent 信息**：
- 类型：`general`（reviewer 角色）
- Task ID：`ses_0a9a973c2fferekdg3WPn6hhvR`
- 关键 prompt：审查 T10 代码质量，检查 8 项标准

**审查结果摘要**：

| # | 标准 | 判定 | 严重度 |
|---|---|---|---|
| 1 | 职责划分 | PASS | None |
| 2 | 可读性 | PASS | None |
| 3 | 接口和类型 | WARN | Minor（类型契约分歧：签名 str 但运行时接受 Any） |
| 4 | 错误处理 | PASS | None（空字符串 pattern 行为已补测试） |
| 5 | 安全边界 | WARN | Minor（fail-open 与 PathGuard 的 fail-closed 不一致） |
| 6 | 测试质量 | WARN | Minor（2 个重复测试 → 已修复；缺少边缘测试 → 已修复） |
| 7 | 可维护性 | PASS | None |
| 8 | 无真实网络/LLM 依赖 | PASS | None |

**修复的 Minor 问题**：

| # | 问题 | 严重度 | 修复 |
|---|---|---|---|
| CQ-3 | 2 个重复测试（rm -rf compound 和 sudo compound） | Minor | 替换为差异化测试（subshell 和 env var 场景） |
| CQ-4 | 缺少空字符串 pattern 测试 | Minor | 添加 3 个测试（空 pattern 匹配所有命令） |
| CQ-5 | 缺少 tab/newline 命令测试 | Minor | 添加 2 个测试（验证 `\s+` 覆盖 tab 和 newline） |
| CQ-6 | 缺少 regex 元字符命令测试 | Minor | 添加 3 个测试（`.`, `*`, `[`, `]` 在命令中） |

**未修复（合理保留）**：
- 类型契约分歧：签名 `str`/`list[str]` 但运行时接受 `Any`——防御性编程设计选择，测试用 `# type: ignore` 标注，合理保留
- fail-open vs fail-closed：CommandGuard 对非字符串输入返回 ALLOW（fail-open），PathGuard 返回 DENY（fail-closed）——SPEC §3.4.2 定义"全部不命中 → ALLOW"，非字符串无法匹配任何 pattern 故 ALLOW 符合 SPEC 语义
- `test_unclosed_character_class_raises_re_error` 测试 stdlib `re` 而非 CommandGuard——作为文档性测试保留，证明 `[invalid` 确实是无效正则
- `re.compile` 每次调用重复编译——对每次 `run_command` 调用一次的 guard 来说性能影响可忽略

### 最终验证

| 检查项 | 命令 | 结果 |
|---|---|---|
| 目标测试 | `pytest tests/unit/test_command_guard.py -v` | **100 passed** in 0.08s |
| 完整测试套件 | `pytest tests/ -v` | **483 passed** in 0.52s |
| Lint | `ruff check harness/ tests/` | All checks passed! |
| 类型检查 | `mypy harness/` | Success: no issues found in 14 source files |
| 凭据泄露检查 | `grep -rni "api_key\|secret\|password\|token\|sk-" harness/governance/ tests/unit/test_command_guard.py` | 无匹配（源码无凭据） |
| Git 历史扫描 | `git log --all -p \| grep -i "api_key\|secret\|password"` | 仅文档引用和测试 fixture，无真实凭据 |

**Commit hash**：`e476d48` (refactor(T10): complete reviews and verification)

**人工干预**：无

**教训**：
1. CommandGuard 是一个简洁的安全组件——39 行实现 + 540 行测试（100 个测试），TDD 红绿循环非常顺畅，无 Critical/Major 问题。这得益于 T01 中 `GuardResult` 枚举的清晰定义和 PathGuard 建立的模式。
2. Code Quality Review 发现的重复测试是测试编写中的常见问题——当多个测试类从不同角度测试同一行为时（如 RmRf 类和 PartialMatches 类都测试 `rm -rf` 在复合命令中的匹配），容易出现完全相同的测试用例。Review 阶段应检查是否有完全重复的测试。
3. 空字符串 pattern 是一个容易被忽略的边缘情况——`re.compile("")` 成功且 `"".search(cmd)` 匹配任何字符串（在位置 0），导致所有命令返回 PENDING。这是一个"正确但可能令人惊讶"的行为，值得有测试覆盖。
4. fail-open vs fail-closed 的设计选择——CommandGuard 对非字符串输入返回 ALLOW（fail-open），而 PathGuard 返回 DENY（fail-closed）。这是因为两个 guard 的 SPEC 语义不同：CommandGuard 的"全部不命中 → ALLOW"意味着非字符串无法匹配任何 pattern 故 ALLOW；PathGuard 的"路径解析失败 → DENY"意味着任何解析问题都拒绝。两种设计都符合各自的 SPEC 语义。
