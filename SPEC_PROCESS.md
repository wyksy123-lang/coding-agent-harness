# SPEC_PROCESS.md — 与 Superpowers 协作生成 SPEC 与 PLAN 的过程文档

> 本文档记录 brainstorming 阶段的关键节点、迭代对话节选、AI 建议采纳/推翻决策、以及冷启动验证结果。
> 要求来源：要求1 §4.4 + §4.5。

---

## 设计决策摘要

| 轮次 | 决策项 | 用户选择 | AI 建议 | 采纳 | 理由 |
|---|---|---|---|---|---|
| 1 | 产品方向 | A. TDD 专项 | A. TDD 专项 | 是 | 反馈信号天然确定，契合"机制是代码"要求 |
| 2 | 主要贡献维度 | 反馈闭环 | 反馈闭环 | 是 | TDD 核心是 red→green 循环，反馈闭环是驱动引擎 |
| 3 | 技术栈 | Python | Python | 是 | LLM 生态丰富，pytest JSON 可解析，mock LLM 零障碍 |
| 4 | WebUI 范围 | B. 交互式 WebUI | B. 交互式 WebUI | 是 | 满足 R037 + HITL 可视化 + 反馈闭环可视化 |
| 5 | 输入与范围 | A. 自然语言→全新模块 | A. 自然语言→全新模块 | 是 | 最自主，最能展示反馈闭环驱动行为 |
| 6 | LLM 供应商 | DeepSeek | OpenAI 兼容接口 + DeepSeek | 是 | 成本低，OpenAI 兼容，抽象层一次设计多供应商可用 |
| 7 | 凭据存储 | D. keyring + .env | D. keyring + .env | 是 | OS 级加密满足安全要求，.env 降级覆盖 CI/容器场景 |
| 8 | 分发与部署 | Docker + PyPI / Render | Docker + PyPI / Render | 是 | 双形态覆盖部署+开发，Render 免费层满足 R037 |
| 9 | 反馈闭环深度 | C. 多类分类+策略路由+卡死检测 | C. 多类分类+策略路由+卡死检测 | 是 | 主要贡献维度需足够深度，全部确定性代码可单测 |
| 10 | 动作格式与工具集 | A. OpenAI tool calling | A. OpenAI tool calling | 是 | 结构化易解析，DeepSeek 原生支持，mock 直接返回 tool_call |
| 11 | 记忆维度 | A. JSON 文件+结构化过滤 | A. JSON 文件+结构化过滤 | 是 | 记忆非主要维度，最低可运行实现即可；检索纯代码可单测 |
| 12 | 配置与治理 | YAML + 三子机制 | YAML + 三子机制 | 是 | 配置由代码强制执行非提示词；治理三子机制全部确定性可单测 |

---

## 迭代记录

### 第 1 轮：产品方向

**AI 提问**：你的 Coding Agent Harness 面向的具体编码场景是什么？提供了四个方向（A. TDD 专项 / B. 代码审查修复 / C. 通用编码助手 / D. 自定义）。

**用户回答**：A

**AI 建议**：A. TDD 专项——agent 接收需求描述，自主走"写失败测试→跑测试（红）→写最少实现→跑测试（绿）→重构→重复"循环。反馈信号天然确定（测试运行结果），契合要求2 A.4-B"反馈信号 = 代码校验器"要求。

**采纳**：是。用户选择 A，AI 确认并阐述其与 A.4-B 的契合。

**设计变更**：确定产品方向为 TDD 专项 Coding Agent Harness。

**后续证据需求**：SPEC 问题陈述需说明"为何有人使用"——TDD harness 可自动化测试驱动开发流程，减少人工编写测试和实现的重复劳动。

---

### 第 2 轮：主要贡献维度

**AI 提问**：哪个维度作为主要贡献（深入实现）？提供三个候选（反馈闭环 / 治理 / 工具分发），各附深入机制描述和 mock-LLM 可测性分析。

**用户回答**：同意选择反馈闭环

**AI 建议**：反馈闭环作为主要贡献维度，治理作为第二优先（范围围栏+危险拦截做最低可运行实现）。深入机制链：测试运行→结果解析→失败分类→结构化反馈回灌→多轮修正追踪→停机判断。

**采纳**：是。用户同意反馈闭环。

**设计变更**：确定主要贡献维度为反馈闭环。六维度中反馈为深度，治理为必要护栏（最低可运行），其余四维度（决策/工具/记忆/配置）也需最低可运行实现。

**后续证据需求**：SPEC「领域与机制设计」节需说明重点维度选择理由；机制演示（R054）第三条需与反馈闭环对齐。

---

### 第 3 轮：技术栈

**AI 提问**：harness 本身用什么语言构建？TDD agent 写什么语言的测试和代码？提供 Python / TypeScript / Go 三个候选。

**用户回答**：python

**AI 建议**：Python。理由：LLM 抽象层用抽象基类天然适合；pytest --json-report 输出结构化结果可确定性解析；FastAPI 提供 WebUI 后端 + WebSocket；mock LLM 就是一个返回预设响应的 Python 类；分发用 Docker + PyPI 双形态。

**采纳**：是。用户选择 Python。

**设计变更**：确定技术栈为 Python。harness 与 TDD 目标同语言。测试 runner 为 pytest，WebUI 后端为 FastAPI + WebSocket。

**后续证据需求**：SPEC 技术选型节需说明 Python 选型理由；PLAN 需包含 Python 项目初始化 task。

---

### 第 4 轮：WebUI 范围

**AI 提问**：WebUI 的范围与定位？提供三个候选（A. 状态仪表盘 / B. 交互式 WebUI / C. 完整编码界面）。

**用户回答**：B

**AI 建议**：方案 B。FastAPI + WebSocket 实时推送 agent 状态，WebUI 内审批/拒绝危险动作（HITL），反馈闭环全过程可视化。不强制使用 Open Design（§3.6 豁免）。

**采纳**：是。用户选择 B。

**设计变更**：确定 WebUI 为交互式，含 HITL 审批功能。WebSocket 实时推送 agent 运行状态、测试结果、失败分类、修正轮次、停机决策。

**后续证据需求**：SPEC 系统架构需含 WebUI 组件；PLAN 需含 WebUI task（FastAPI + WebSocket + 前端）。

---

### 第 5 轮：输入与工作范围

**AI 提问**：harness 接收什么输入、作用在什么范围？提供三个候选（A. 自然语言需求→全新模块 / B. 函数签名+docstring / C. 给定测试骨架）。

**用户回答**：A

**AI 建议**：方案 A。最能展示反馈闭环的价值——agent 自主决定测试策略，测试失败驱动修正。治理围栏天然清晰：目标目录边界。评价问题通过验收标准解决：不评价"测试是否完美"，而评价"agent 是否走了红→绿→重构循环""是否在测试全绿后停机""是否在越界时被拦截"。

**采纳**：是。用户选择 A。

**设计变更**：确定输入为自然语言需求，作用范围为指定目标目录。agent 在目标目录内自主创建测试文件和实现文件。

**后续证据需求**：SPEC 功能规约需描述输入格式、输出产物、目录结构；验收标准需聚焦过程行为而非测试质量。

---

### 第 6 轮：LLM 供应商

**AI 提问**：交付 harness 的 LLM 抽象层需要指定一个主供应商。提供 OpenAI / Anthropic / DeepSeek / Ollama / 多供应商候选。

**用户回答**：主供应商选择 deepseek

**AI 建议**：OpenAI 兼容接口作为抽象层标准协议，DeepSeek 为真实实现，mock 为离线测试实现，Ollama 可作为本地备选。DeepSeek 兼容 OpenAI Chat Completions 格式，抽象层一次设计多供应商可用。

**采纳**：是。用户选择 DeepSeek。

**设计变更**：确定 LLM 抽象层协议为 OpenAI Chat Completions 格式，主供应商为 DeepSeek。LLMClient 协议 + DeepSeekClient 实现 + MockLLMClient 实现。

**后续证据需求**：SPEC 技术选型需说明 DeepSeek 选型理由；凭据存储需支持 DeepSeek API key。

---

### 第 7 轮：凭据存储

**AI 提问**：凭据存储方案？提供 OS 钥匙串 / 加密文件 / .env / 组合四个候选。

**用户回答**：D

**AI 建议**：方案 D（keyring 为主 + .env 降级）。keyring 满足"至少一种安全存储"硬要求；.env 作为降级方案（CI/容器场景）；首次运行 getpass 隐藏录入；key status 掩码显示；key update/clear 支持。威胁模型覆盖：源码泄露、git 历史泄露、日志泄露、进程环境泄露、终端 history 泄露。

**采纳**：是。用户选择 D。

**设计变更**：确定凭据存储为 keyring（主）+ .env（降级）。CLI 命令：key setup / key status / key update / key clear。SPEC 安全节含完整威胁模型。

**后续证据需求**：SPEC 安全节需含凭据威胁模型表（威胁→对策）；单测需 mock keyring backend 验证存储/读取/清除；README 需说明目标机 key 安全配置方式。

---

### 第 8 轮：分发与部署

**AI 提问**：分发形态与部署平台？提供分发（Docker+PyPI / 仅 Docker / 仅 PyPI）和部署平台（Render / Railway / Fly.io / 阿里云）组合。

**用户回答**：执行你的建议

**AI 建议**：Docker + PyPI 分发，Render 部署。Docker 镜像满足 R032 容器分发要求，CI 构建镜像满足 R035；PyPI 包满足开发者本地安装；Render 免费层支持 Docker 部署，提供公网 URL 满足 R037。

**采纳**：是。用户接受建议。

**设计变更**：确定分发为 Docker + PyPI，部署为 Render。CI 需含 Docker 镜像构建 step。README 需写清两种获取方式 + 目标机 key 安全配置。

**后续证据需求**：Dockerfile + docker build/docker run 验证；PyPI 打包配置；Render 部署 URL 可访问；CI 含镜像构建 step。

---

### 第 9 轮：反馈闭环深度

**AI 提问**：反馈闭环的失败分类粒度？提供三个候选（A. 二元分类 / B. 多类分类+策略路由 / C. 多类分类+策略路由+卡死检测）。

**用户回答**：C

**AI 建议**：方案 C。全部为确定性代码：解析器是纯函数（JSON in → 分类结果 out），策略路由是查表，卡死检测是状态机。机制演示第二条"注入失败→反馈闭环使 agent 改变下一步"天然满足。停机判断自然产生：全绿→成功；超最大轮数→失败；卡死→建议停机。附数据结构设计：TestResult / FeedbackInjector / RoundTracker。

**采纳**：是。用户选择 C。

**设计变更**：确定反馈闭环深度为方案 C。失败分类 taxonomy：ASSERTION / SYNTAX / IMPORT / RUNTIME / TIMEOUT / COLLECTION。核心组件：TestResultParser（纯函数）、FeedbackInjector（分类+格式化+策略路由）、RoundTracker（轮次追踪+失败指纹去重+卡死检测+停机判断）。

**后续证据需求**：SPEC「领域与机制设计」需详述反馈闭环机制链；mock-LLM 单测需覆盖：解析器分类、策略路由、卡死检测、停机判断；机制演示需含"注入失败→agent 改变下一步"的确定性复现。

---

### 第 10 轮：动作格式与工具集

**AI 提问**：agent 动作格式与工具集？提供三个动作格式候选（A. OpenAI tool calling / B. 自定义 JSON / C. ReAct）和六个工具。

**用户回答**：A

**AI 建议**：方案 A（OpenAI tool calling）。DeepSeek 支持 OpenAI 兼容 tool calling，是 chat completion API 原生功能，不违反"不得使用高层 agent 框架"约束。动作解析 = 解析 tool_calls 字段，纯代码确定性操作。工具 schema 用 JSON Schema 声明，工具集由配置驱动。run_command 是治理拦截主入口：正则匹配危险模式→拦截→HITL 审批→执行或拒绝。

**采纳**：是。用户选择 A。

**设计变更**：确定动作格式为 OpenAI tool calling。工具集：write_file / read_file / list_files / run_tests / run_command / finish。治理拦截点：write_file/read_file/list_files 路径越界检查；run_command 危险命令模式匹配→HITL。

**后续证据需求**：SPEC 功能规约需描述每个工具的输入/行为/输出/边界/错误处理；mock-LLM 单测需覆盖工具分发（mock LLM 返回 tool_call → 验证分发到正确工具）；治理单测需覆盖路径越界拦截和危险命令拦截。

---

### 第 11 轮：记忆维度

**AI 提问**：长期记忆的存储与检索方案？提供 JSON 文件+结构化过滤 / SQLite+SQL / 向量库+语义检索三个候选。区分了工作记忆（已由 RoundTracker 覆盖）和长期记忆（本轮决策）。

**用户回答**：A

**AI 建议**：方案 A（JSON 文件 + 结构化过滤）。记忆不是主要贡献维度，最低可运行实现即可。检索逻辑是纯代码：retrieve(failure_type, limit) → 读 JSON → 过滤 → 返回。"按需提供给 LLM 而非全量载入"：每次只注入与当前失败类型相关的历史条目。附数据结构：memory.json（project_conventions / failure_history / successful_strategies）+ MemoryRetriever 类。

**采纳**：是。用户选择 A。

**设计变更**：确定记忆维度为 JSON 文件 + 结构化过滤。长期记忆存于 .harness/memory.json。MemoryRetriever：retrieve_relevant（按失败类型过滤）、record（记录当前轮次）、get_conventions（返回项目约定）。

**后续证据需求**：mock-LLM 单测需覆盖记忆读写：构造 memory.json → 验证检索返回正确条目 → 验证注入 LLM 上下文的内容正确。

---

### 第 12 轮：配置与治理

**AI 提问**：配置格式与可声明项 + 治理三子机制（路径围栏 / 危险命令检测 / HITL 状态机）联合设计。

**用户回答**：同意

**AI 建议**：YAML 配置（harness.yaml），可配置项包括 max_rounds / target_directory / test_command / model / enabled_tools / dangerous_command_patterns / hitl_timeout_seconds。治理三子机制：PathGuard（路径越界直接拒绝）、CommandGuard（正则匹配→PENDING）、HITLState（PENDING→APPROVED/DENIED/TIMEOUT→RESUME/STOP）。全部由代码强制执行，不是提示词。

**采纳**：是。用户同意。

**设计变更**：确定配置格式为 YAML，治理三子机制为 PathGuard + CommandGuard + HITLState。配置项由代码读取并强制执行。HITL 通过 WebUI WebSocket 推送审批请求。

**后续证据需求**：mock-LLM 单测需覆盖：PathGuard 路径越界拦截、CommandGuard 危险命令匹配、HITLState 状态转换。机制演示第一条"治理护栏拦截危险动作"由 CommandGuard + HITLState 满足。

---

## 冷启动验证

（待 Gate C 阶段填写）

---

## brainstorming 反思

> 以下为 SPEC_PROCESS.md 过程层面的 brainstorming 技能反思。完整反思报告见 REFLECTION.md（由学生本人撰写）。

### brainstorming 技能做得好的地方

1. **一次一个高杠杆问题**：每轮只问一个设计决策点，避免信息过载。12 轮迭代从产品方向到配置细节逐步收敛，节奏可控。
2. **提供带权衡的选项**：每轮提供 2-4 个候选方案并附优势/劣势对比表，使决策成本降低——用户只需选字母即可推进，同时仍可提出自己的方向。
3. **区分开发工具与交付产物**：从第一轮起明确区分 OpenCode+Superpowers（开发 harness）与交付 harness 内核，避免了将宿主框架功能误计入交付物。
4. **拒绝提示词机制**：每轮设计都检查"移除 LLM 后是否仍可单测"，确保机制是代码而非提示词。这一约束在反馈闭环（第 9 轮）和治理（第 12 轮）中反复验证。
5. **凭据/分发/WebUI 作为一等设计关注**：这三项没有推迟到实现阶段，而是在 brainstorming 阶段就作为设计决策点（第 7、8、4 轮），避免了后期返工。

### brainstorming 技能让你不满的地方

1. **冷启动验证尚未执行**：brainstorming 产出的 SPEC 是否真正清晰，需等冷启动验证（Gate C）才能客观检验。当前 12 轮迭代虽多，但隐性上下文仍可能存在。
2. **用户故事 INVEST 检查偏粗**：每条用户故事的 INVEST 检查仅一句话，缺乏更细致的可估算性（E）和可测试性（T）的展开。PLAN 阶段需进一步细化。
3. **选项设计有引导性**：AI 每轮都给出"我的建议"，用户 12 轮全部接受。这可能是建议确实合理，也可能暗示选项设计存在确认偏误——冷启动验证应特别关注这一风险。

---

## SPEC 批准记录

**人工批准时间**：2026-07-11

### 用户接受的主要建议

| 轮次 | AI 建议 | 用户决策 | 采纳 |
|---|---|---|---|
| 1 | TDD 专项方向 | 选 A | 是 |
| 2 | 反馈闭环为主要贡献维度 | 同意 | 是 |
| 3 | Python 技术栈 | 选 Python | 是 |
| 4 | 交互式 WebUI + HITL | 选 B | 是 |
| 5 | 自然语言需求→全新模块 | 选 A | 是 |
| 6 | OpenAI 兼容接口 + DeepSeek | 选 DeepSeek | 是 |
| 7 | keyring 为主 + .env 降级 | 选 D | 是 |
| 8 | Docker + PyPI / Render | 执行建议 | 是 |
| 9 | 多类分类+策略路由+卡死检测 | 选 C | 是 |
| 10 | OpenAI tool calling + 6 工具 | 选 A | 是 |
| 11 | JSON 文件+结构化过滤记忆 | 选 A | 是 |
| 12 | YAML 配置 + 治理三子机制 | 同意 | 是 |
| 审查 | 4 项一致性问题修复（11-A~D） | 同意修复 | 是 |

### 用户否决/修正的建议

- **无重大否决**：用户在 12 轮 brainstorming 中未否决任何 AI 建议。
- **用户附加约束**：用户在批准设计时附加"注意多步 push 的要求，即使向用户确认是否已经 push 到 git 仓库"——要求 AI 不得自行 commit/push，每次都需向用户确认。
- **用户要求正式审查**：用户在 SPEC 创建后要求执行 11 项正式合规审查，导致发现 4 项一致性问题并修复。这表明 AI 自审不够，需用户介入把关。

### 人工批准 SPEC.md 的结论

用户已逐节审阅 SPEC.md（799 行），确认其设计内容覆盖：
- 问题陈述、6 个 INVEST 用户故事、18 个功能模块规约（含输入/行为/输出/边界/错误处理）；
- 非功能需求（性能/安全含凭据威胁模型/可用性/可观测性）；
- 系统架构（组件图+数据流+外部依赖）、数据模型（ER 图+字段约束）；
- 凭据与分发设计、技术选型与理由；
- 领域与机制设计（四类机制+六维度+重点维度+机制编码方式）；
- 25 条客观验收标准、8 项风险与未决问题；
- 11 项合规审查全部 PASS（4 项问题已修复）。

**结论：SPEC.md 设计已获人工批准。** 进入 Gate B（PLAN）的先决条件已满足，但用户要求暂不创建 PLAN.md，等待用户先提交和推送文档。

---

## 设计批准记录

**时间**：2026-07-11
**事件**：用户明确批准完整设计块
**用户附加要求**：注意多步 push 的要求，即使向用户确认是否已经 push 到 git 仓库
**后续动作**：创建 SPEC.md → 运行需求追溯检查 → 停止等待用户审查 SPEC

---

## SPEC 创建记录

**时间**：2026-07-11
**事件**：SPEC.md 已创建，包含以下章节：
- §1 问题陈述
- §2 用户故事（6 个 INVEST 故事）
- §3 功能规约（8 个模块：Agent 主循环 / 工具集 / 反馈闭环 / 治理 / 记忆 / 配置 / 凭据管理 / WebUI）
- §4 非功能需求（性能 / 安全含凭据威胁模型 / 可用性 / 可观测性）
- §5 系统架构（组件图 Mermaid + 数据流序列图 Mermaid + 外部依赖表）
- §6 数据模型（ER 图 Mermaid + 字段约束表）
- §7 凭据与分发设计
- §8 技术选型与理由
- §9 领域与机制设计（额外节，要求2 A.5）
- §10 验收标准（25 条 AC）
- §11 风险与未决问题
- 附录：需求追溯矩阵

**需求追溯检查**：已在 REQUIREMENTS_CHECKLIST.md 末尾添加 SPEC 追溯矩阵，所有硬性要求在 SPEC 中均有对应章节覆盖。

**当前状态**：等待用户审查 SPEC.md。用户审查通过后进入 Gate B（PLAN）。

---

## SPEC 合规审查与修复记录

**时间**：2026-07-11
**事件**：用户要求对 SPEC.md 执行正式合规审查（11 项检查）

### 审查结果

| 审查项 | 结果 |
|---|---|
| 1. 问题陈述/目标用户/价值 | PASS |
| 2. ≥5 INVEST 用户故事 | PASS |
| 3. 功能模块五字段 | PASS |
| 4. 非功能需求四项 | PASS |
| 5. 凭据威胁模型+key 流程 | PASS |
| 6. 架构/数据流/依赖/数据模型 | PASS |
| 7. 技术选型/分发/验收标准 | PASS |
| 8. 风险与未决 | PASS |
| 9. 领域与机制设计完整覆盖 | PASS |
| 10. 机制是代码非提示词 | PASS |
| 11. TODO/矛盾/无法验收 | **FAIL** → 已修复 |

### 修复内容（11-A 至 11-D）

1. **11-A**：§3.6.1 配置表补充 4 项缺失配置项：`llm_timeout`(int, 60) / `pytest_timeout`(int, 60) / `stuck_threshold`(int, 3) / `llm_retry_count`(int, 3)。同步更新 §6.1 ER 图 Config 实体和 §6.2 字段约束表。
2. **11-B**：§3.6.1 配置表 `test_command` 默认值统一为 `pytest --json-report --output=.harness/report.json`，与 §3.2.4 一致。
3. **11-C**：§5.3 补充显式声明："交付内核不使用 LangChain AgentExecutor、AutoGen、CrewAI、LlamaIndex agent 或任何编码智能体 SDK 自带的 agent runner。"
4. **11-D**：§11 RK1 补充 Ollama 说明："遵循同一 LLMClient 协议，通过配置 model 和 API base URL 切换，为可选扩展，不在核心交付范围内"。

**当前状态**：4 项问题已修复。等待用户确认是否进入 Gate B（PLAN）。

---

## SPEC 人工批准记录

**时间**：2026-07-11
**事件**：用户逐节审阅 SPEC.md，批准其设计内容。

**用户接受的主要建议**：12 轮 brainstorming 中 AI 的全部设计建议均被采纳（TDD 方向、反馈闭环为主要贡献、Python、交互式 WebUI、自然语言输入、DeepSeek、keyring+.env、Docker+PyPI/Render、多类分类+卡死检测、OpenAI tool calling、JSON 记忆、YAML 配置+治理三子机制）。合规审查的 4 项修复也已采纳。

**用户否决/修正的建议**：无重大否决。用户附加约束：AI 不得自行 commit/push，每次需向用户确认。用户要求 11 项正式合规审查，发现并修复 4 项一致性问题。

**结论**：SPEC.md 已获人工批准。用户要求暂不创建 PLAN.md，等待先提交和推送文档。

详细记录见下方"SPEC 批准记录"节。
