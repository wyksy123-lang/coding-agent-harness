# REQUIREMENTS_CHECKLIST.md — 穷尽式需求审计清单

> 来源：`docs/assignment/要求1.md`（通用要求）+ `docs/assignment/要求2.md`（Coding Agent Harness 专属要求）。
> 每条需求映射：ID、来源节、义务、计划证据/交付路径、验证方法、状态、PLAN task ID。

## 状态图例

- TODO — 未开始
- BLOCKED — 被依赖阻塞
- DONE — 已完成并验证

---

## A. 过程纪律

| ID | 来源 | 义务 | 计划证据 | 验证方法 | 状态 | PLAN Task |
|---|---|---|---|---|---|---|
| R001 | 要求1 §4 前言 | SPEC + PLAN 完成并通过冷启动验证前，禁止编写任何实现代码 | SPEC_PROCESS.md 记录批准时间线 | git log 首次实现 commit 在 SPEC/PLAN/cold-start 之后 | DONE（首次实现 commit 68bd926 在 Gate C 之后） | T01 |
| R002 | 要求1 §3.6 | 必须使用 Superpowers 框架 + 支持的编码智能体 | .opencode 配置 + AGENT_LOG.md | 检查 Superpowers 安装证据 | TODO | — |
| R003 | 要求1 §3.6 | 必须如实遵循七步工作流，偏离须在 AGENT_LOG.md 记录并解释 | AGENT_LOG.md | 审查偏离记录 | TODO | — |
| R004 | 要求1 §4.1 | brainstorming 主动追问"你想做什么"，分块呈现设计供签字确认 | SPEC_PROCESS.md | 审查含分块确认记录 | TODO | — |
| R005 | 要求1 §4.4 | 至少 3 轮关键迭代的对话节选与处理决策 | SPEC_PROCESS.md | 审查含 ≥3 轮迭代 | TODO | — |
| R006 | 要求1 §4.5 | 冷启动验证：换一个不同类型 agent，新 session，仅给 SPEC+PLAN，选 1-2 task，遇不确定暂停询问 | SPEC_PROCESS.md 冷启动记录 | 审查第二个 agent 暂停点与 spec 缺陷 | DONE（Aider 冷启动完成，Gate C 通过） | — |
| R007 | 要求1 §4.5 | 冷启动记录：暂停点、spec 缺陷、误读、产出差距、SPEC/PLAN 修订 diff | SPEC_PROCESS.md | 审查 before/after diff | DONE（6 个暂停点已记录，5 个缺陷已修复，修订后人工重新批准） | — |
| R008 | 要求1 §4.6 | git worktree 隔离：每个独立功能/大模块一个 worktree，对应一个 PR | git worktree list + PR 链接 | 审查 worktree 与 PR 一一对应 | IN PROGRESS（T01-T21 均在独立/managed task branch 中完成；T21 branch=`codex/task/T21-webui-frontend`） | T01-T29 |
| R009 | 要求1 §4.6 | 每个任务派一个新鲜 subagent 完成 | AGENT_LOG.md | 审查每 task 有独立 subagent 记录 | IN PROGRESS（T01-T21 均记录 fresh subagent/reviewer；T21 prep=Archimedes，Spec Review=Hypatia/Pasteur/Boyle，Quality Review=Dewey） | T01-T29 |
| R010 | 要求1 §4.6 + §3.6 | TDD 强制：红→绿→重构；先写失败测试、得到红色，再写最少代码变绿，再重构。不接受先写实现再补测试 | AGENT_LOG.md + commit 历史 | 审查 commit 顺序：test commit 在 impl commit 之前 | IN PROGRESS（T01-T21 均保持 Red→Green→Review/Refactor；T21: Red 3d17135 → Green 7bd7117 → Review eeefe16） | T01-T29 |
| R011 | 要求1 §4.6 | 两阶段评审：先 spec 合规检查 → 再代码质量检查；Critical issue 必须修复才能进入下一 task | AGENT_LOG.md | 审查每 task 有两阶段评审记录 | IN PROGRESS（T01-T21 均记录两阶段评审；T21 Spec Review 1 Critical/2 Major 已修复；Quality Review 0 Critical/4 Major 已修复或记录） | T01-T29 |
| R012 | 要求1 §4.6 | finishing-a-development-branch 决定 merge/PR/保留/丢弃 | AGENT_LOG.md | 审查分支完成决策记录 | TODO | — |

## B. 交付文档

| ID | 来源 | 义务 | 计划证据 | 验证方法 | 状态 | PLAN Task |
|---|---|---|---|---|---|---|
| R013 | 要求1 §4.2 | SPEC.md 含 10 节：问题陈述、≥5 INVEST 用户故事、功能规约（输入/行为/输出/边界/错误）、非功能（性能/安全含凭据威胁模型/可用性/可观测性）、系统架构、数据模型、凭据与分发设计、技术选型理由、验收标准、风险与未决 | SPEC.md | 逐节检查存在性与内容完整性 | TODO（SPEC 已创建，待用户审查） | — |
| R014 | 要求2 A.5 | SPEC 额外「领域与机制设计」节：coding 的反馈信号、危险动作、所需工具、记忆需求；重点维度及理由；机制如何编码 | SPEC.md §9 | 检查该节存在且覆盖四类机制 | TODO（SPEC 已创建，待用户审查） | — |
| R015 | 要求1 §4.2 | 每个功能有客观验收标准 | SPEC.md §10 | 检查每功能有可判定标准 | TODO（SPEC 已创建，待用户审查） | — |
| R016 | 要求1 §4.3 | PLAN.md：每 task 可由一个 subagent 一次会话完成；含目标、涉及文件、实现要点、验证步骤（含将要写的失败测试） | PLAN.md | 审查 task 粒度与字段完整性 | DONE（T01 已验证可由 subagent 完成） | T01 |
| R017 | 要求1 §4.3 | PLAN 显式标出 task 间依赖与可并行部分 | PLAN.md | 检查依赖标注 | DONE（依赖图 + 并行计划已存在） | — |
| R018 | 要求1 §4.7 | PLAN.md 持续更新：每完成一个 task 即标记完成并附 commit hash | PLAN.md + git log | 审查 task 状态与 commit hash | IN PROGRESS（T01-T21 已标记 ✅ DONE + commit hash） | T01-T29 |
| R019 | 要求1 §4.4 | SPEC_PROCESS.md：brainstorming 关键节点、≥3 轮迭代、AI 建议采纳/推翻及理由、brainstorming 反思 | SPEC_PROCESS.md | 逐项检查 | TODO | — |
| R020 | 要求1 §4.9 | AGENT_LOG.md：时间顺序，每条含时间戳、task 编号、Superpowers 技能、关键 prompt/context、subagent 输出/commit hash、人工干预、教训 | AGENT_LOG.md | 逐条检查字段完整性 | TODO | — |
| R021 | 要求1 §五.4 | README.md 含：项目简介、安装、运行、分发命令、目录结构、安全边界说明 | README.md | 逐节检查 | TODO | — |
| R022 | 要求1 §五.8 | REFLECTION.md：1500–2500 字反思报告 | REFLECTION.md | 字数与内容检查 | TODO | — |
| R023 | 要求1 §六 | REFLECTION 必须学生本人撰写，禁止 AI 代写（可 AI 辅助润色但需标注） | REFLECTION.md 内标注 | 审查 AI 辅助标注 | TODO | — |

## C. 凭据安全

| ID | 来源 | 义务 | 计划证据 | 验证方法 | 状态 | PLAN Task |
|---|---|---|---|---|---|---|
| R024 | 要求1 §3.1 | key 绝不硬编码进源码 | 源码扫描 | grep/secret scan | DONE（T17 touched-file 高置信扫描无匹配；全仓仅既有 fake key 占位符） | T17 |
| R025 | 要求1 §3.1 | key 绝不提交进 Git（含历史） | git log 扫描 | git log -p 全历史扫描 | IN PROGRESS（T17 未新增真实 key；最终全历史扫描留待收尾） | T17 |
| R026 | 要求1 §3.1 | key 绝不写入日志/终端 history/明文配置文件 | 代码审查 | 检查无明文 key 输出 | DONE（T17 status/log tests 验证明文 key 不出现在状态或 warning 日志） | T17 |
| R027 | 要求1 §3.1 | 至少实现一种安全存储：OS 钥匙串/KMS/带主密码加密文件 | 源码实现 | 单测验证存储机制 | DONE（T17 CredentialManager 默认使用 OS keyring，单测用 mock backend 验证） | T17 |
| R028 | 要求1 §3.1 | 环境变量通过 .env 加载而非命令行 export；须说明明文风险 | SPEC + README | 审查说明 | IN PROGRESS（T17 实现 .env 降级并在 SPEC 标注明文风险；README 待 T27） | T17,T27 |
| R029 | 要求1 §3.1 | 首次运行引导用户安全录入 key（隐藏输入） | 源码实现 | 单测/手动验证 | DONE（T17 setup/update 使用 getpass.getpass，单测 monkeypatch 验证路径） | T17 |
| R030 | 要求1 §3.1 | 可查看/更新/清除 key（查看状态时不回显明文） | 源码实现 | 单测验证 | DONE（T17 覆盖 setup/status/update/clear/get_key、掩码和 stale keyring fallback） | T17 |
| R031 | 要求1 §3.1 + §4.2 | SPEC 安全节明确凭据威胁模型与对策 | SPEC.md | 审查威胁模型节 | DONE（SPEC §4.2 已含 T1-T7 凭据威胁模型，T17 reviewer 复核） | T17 |

## D. 分发与部署

| ID | 来源 | 义务 | 计划证据 | 验证方法 | 状态 | PLAN Task |
|---|---|---|---|---|---|---|
| R032 | 要求1 §3.2 | 选容器/二进制/包管理器一种或多种分发 | Dockerfile + PyPI 打包配置 | 检查分发产物存在 | TODO | — |
| R033 | 要求1 §3.2 | README 写清：获取方式、运行命令、key 在目标机安全配置、已知限制 | README.md | 逐项检查 | TODO | — |
| R034 | 要求1 §3.4 | 凭据与分发经得起"全新机器从零运行"检验 | 安装文档 + 测试记录 | fresh-machine 测试 | TODO | — |
| R035 | 要求1 §4.8 | 若选容器分发，CI 须构建镜像 | CI 配置 | 审查 CI build step | TODO | — |
| R036 | 要求1 §4.11 | 可选云部署：提供截止前可访问公网地址；README 说明部署架构与 CI/CD；控制成本 | 部署 URL + README | 访问 URL 验证 | TODO | — |
| R037 | 要求1 §五.9 | 线上部署 URL，必须提供应用可访问的 WebUI 接口 | 部署 URL | 访问验证 | TODO | — |

## E. Harness 内核（要求2 专属）

| ID | 来源 | 义务 | 计划证据 | 验证方法 | 状态 | PLAN Task |
|---|---|---|---|---|---|---|
| R038 | 要求2 A.4-A | 必须自己实现 agent 主循环（组织上下文→调用 LLM→解析动作→分发执行→回灌结果→停机判断） | 源码 | 代码审查 + 单测 | DONE（T18 AgentLoop 自实现，覆盖 LLM→工具→反馈→停机） | T18 |
| R039 | 要求2 A.4-A | 必须有可注入 mock 的 LLM 抽象层（可替换 mock 离线测试，也可接真实供应商） | 源码 | mock-LLM 单测通过 | DONE（T03 LLMClient ABC + T04 MockLLMClient + T05 DeepSeekClient 均已实现） | T03-T05 |
| R040 | 要求2 A.4-A | 允许使用底层零件（LLM 供应商单次对话 API、HTTP 库、向量库、解析库） | SPEC 说明 | 审查选型 | TODO | — |
| R041 | 要求2 A.4-A | 不允许建在现成 agent 编排框架高层循环之上（LangChain AgentExecutor、AutoGen、CrewAI、LlamaIndex agent、编码智能体 SDK agent runner） | 源码 + SPEC | 依赖审查无禁止框架 | TODO | — |
| R042 | 要求2 A.4-B | 反馈信号 = 代码校验器/传感器（解析产物→客观判定→回灌），不是提示词 | 源码 | 单测验证确定性 | DONE（T12 TestResultParser、T13 FailureClassifier、T15 FeedbackInjector、T16 RoundTracker 均已完成） | T12-T16 |
| R043 | 要求2 A.4-B | 危险动作拦截 = 代码护栏（识别→拦截→要求人工确认），不是提示词 | 源码 | 单测验证确定性 | DONE（T09 PathGuard + T10 CommandGuard + T11 HITLState 均已实现） | T09-T11 |
| R044 | 要求2 A.4-C | 每个核心机制（工具分发、治理拦截、反馈回灌、记忆读写、停机）替换 mock LLM 后仍能用确定性单测验证 | mock-LLM 单测 | 离线运行测试通过 | DONE（T18 用 SequencedLLM/stub tools 离线覆盖 AgentLoop；T22 用 MockLLMClient 集成测试覆盖 TDD 工具分发、治理 HITL PENDING、反馈修正、记忆检索、PASS/MAX_ROUNDS/STUCK 停机） | T18,T22 |
| R045 | 要求2 A.4-C | 配置文件/规则文件/技能/提示词文件属"内容物"，不计入 harness 实现 | SPEC 说明 | 审查不以此充数 | TODO | — |
| R046 | 要求2 A.4-D | 六维度（决策/工具/记忆/治理/反馈/配置）都有可运行的最低实现 | 源码 | 各维度可运行验证 | DONE（决策 T18、工具 T06-T08、治理 T09-T11、配置 T02/T17、反馈 T12-T13/T15-T16、记忆 T14 均有最低可运行实现） | T01-T18 |
| R047 | 要求2 A.4-D | 选择一个机制密集维度深入实现作为主要贡献 | SPEC + 源码 | 深度审查 | DONE（反馈闭环：T12 TestResultParser + T13 FailureClassifier + T14 MemoryRetriever/Recorder + T15 FeedbackInjector + T16 RoundTracker 已完成） | T12-T16 |
| R048 | 要求2 A.4-D | 若以记忆为重点，存储与检索必须自己实现，不得直接接用框架 memory | 源码 | 代码审查 | DONE（T14 JSON memory store/retriever/recorder 自实现，未接入框架 memory） | T14 |
| R049 | 要求2 A.3 | 必须设计四类机制：动作/工具、客观反馈信号、危险动作、记忆 | SPEC「领域与机制设计」 | 逐类检查 | TODO | — |

## F. 测试与机制演示

| ID | 来源 | 义务 | 计划证据 | 验证方法 | 状态 | PLAN Task |
|---|---|---|---|---|---|---|
| R050 | 要求1 §3.4 | 至少 3 个职责清晰的功能模块 | 源码 + SPEC | 模块审查 | IN PROGRESS（配置/凭据 T02/T17、LLM 抽象 T03-T05、工具 T06-T08、治理 T09-T11、反馈 T12-T16、记忆 T14、AgentLoop T18、CLI T19、WebUI 后端 T20、WebUI 前端 T21 — 已实现 11 个模块） | T01-T21 |
| R051 | 要求1 §3.4 + §4.8 | 可一键运行的测试命令（make test 或等价），覆盖核心功能 | Makefile/等价 | 执行测试命令 | DONE（Makefile `make test` 已创建，150 tests pass） | T01 |
| R052 | 要求1 §4.8 | CI（GitHub Actions）必须配置：每次 push 自动运行测试 | .github/workflows/ | push 后 CI 自动触发 | TODO | — |
| R053 | 要求2 A.6 | harness 核心机制必须有用 mock/stub LLM 驱动的确定性单元测试，不依赖网络与真实 LLM | 单测代码 | 离线运行 mock-LLM 测试 | DONE（T22 `tests/mock/test_agent_loop_mock.py` 使用 MockLLMClient/条件式 fake LLM 离线确定性验证主循环核心机制，无网络和真实 LLM） | T18,T22 |
| R054 | 要求2 A.6 | 机制演示：mock LLM 下确定性地复现 ① 治理护栏拦截危险动作 ② 注入失败→反馈闭环使 agent 改变下一步 ③ 重点维度的一个确定性行为 | 演示脚本/测试 | 运行演示 | DONE（T23 `demo/run_demo.py` 与 `tests/mock/test_mechanism_demo.py` 确定性复现治理 HITL PENDING、反馈修正、STUCK 停机；`python -m demo.run_demo` 通过） | T23 |

## G. CI/CD 与仓库

| ID | 来源 | 义务 | 计划证据 | 验证方法 | 状态 | PLAN Task |
|---|---|---|---|---|---|---|
| R055 | 要求1 §4.7 | 公开 GitHub 仓库（私有仓需将助教加为协作者） | GitHub URL | 访问仓库 | TODO | — |
| R056 | 要求1 §4.7 | 完整 commit 历史与 PR 工作流；拒绝单次 commit 提交全部代码；每个 worktree 对应一个 PR | git log + PR 链接 | 审查 commit/PR 历史 | TODO | — |
| R057 | 要求1 §4.7 | commit message/PR 描述标注由哪个 subagent 完成、人工修改了哪些 | commit/PR | 审查描述 | TODO | — |
| R058 | 要求1 §五.6 | CI 配置（.gitlab-ci.yml），必须包含一个名为 unit-test 的 job | .gitlab-ci.yml | 检查 job 名 | TODO | — |
| R059 | 要求1 §五.7 | CI/CD 执行记录，最后一次必须是 pass 状态 | CI 截屏/日志 | 审查 CI 状态 | TODO | — |
| R060 | 要求1 §五 | 通过同一个 NJU Git 仓库链接提交全部交付物 | NJU Git URL | 访问仓库 | TODO | — |

## H. 学术规范

| ID | 来源 | 义务 | 计划证据 | 验证方法 | 状态 | PLAN Task |
|---|---|---|---|---|---|---|
| R061 | 要求1 §六 | 若有部分代码更适合自己手写（如核心算法），在该文件/函数顶部明确注释 | 源码注释 | 审查注释 | TODO | — |
| R062 | 要求1 §六 | 使用第三方代码必须遵守其许可证，并在 README 中列出 | README | 审查许可证列表 | TODO | — |
| R063 | 要求1 §五 | 仓库内不得出现任何真实凭据（当前文件 + Git 历史） | 全仓库扫描 | secret scan | TODO | — |

---

## 冲突与保守解决方案

### 冲突 1：GitHub 仓库 + GitHub Actions ↔ NJU Git 仓库 + .gitlab-ci.yml

- **要求1 §4.7/§4.8**：公开 GitHub 仓库 + GitHub Actions 每次 push 自动运行
- **要求1 §五/§五.6**：通过 NJU Git 仓库提交 + .gitlab-ci.yml 必须含 unit-test job
- **保守方案**：在公开 GitHub 仓库开发（完整分支/worktree/PR/Actions）；同时维护 NJU Git/GitLab remote，推送全部代码，提交 .gitlab-ci.yml，运行 unit-test job；记录两个仓库链接与两套 CI 证据；GitHub PR 链接记录在 AGENT_LOG.md 和 README；不声称 GitHub PR 自动镜像到 GitLab。

### 冲突 2：条件性云部署（§4.11）↔ 最终必交 WebUI URL（§五.9）

- **要求1 §4.11**："如做带服务端的项目，可选择部署"（条件性）
- **要求1 §五.9**："线上部署 URL，必须提供应用可访问的 WebUI 接口"（无条件）
- **保守方案**：以最终清单为准——提供可访问的 WebUI 和部署 URL，不论项目是否"带服务端"。

### 冲突 3：纯 CLI/纯后端豁免（§3.6）↔ 最终必交 WebUI（§五.9）

- **要求1 §3.6**："纯 CLI / 纯后端项目可豁免"（仅针对 Open Design 设计系统推荐）
- **要求1 §五.9**："必须提供应用可访问的 WebUI 接口"
- **保守方案**：§3.6 豁免仅意味着不强制使用 Open Design，不豁免"有 UI"。最终清单优先——必须提供 WebUI。

---

## 需要用户批准的决策

1. **重点维度**：反馈闭环 ✅（已确认）
2. **目标场景**：TDD 专项 ✅（已确认）
3. **技术栈**：Python ✅（已确认）
4. **LLM 供应商**：DeepSeek ✅（已确认）
5. **分发形态**：Docker + PyPI ✅（已确认）
6. **WebUI 范围**：交互式 WebUI + HITL ✅（已确认）
7. **部署平台**：Render ✅（已确认）
8. **凭据存储**：keyring 为主 + .env 降级 ✅（已确认）
9. **NJU Git/GitLab remote**：待用户提供 URL
10. **Superpowers 安装**：待确认是否已安装

## 下一关卡前禁止的行动

1. 禁止编写任何实现代码（在 SPEC 批准 Gate A、PLAN 批准 Gate B、冷启动验证 Gate C 之前）
2. 禁止创建 SPEC.md（在头脑风暴设计获明确批准之前）
3. 禁止创建 PLAN.md（在 SPEC.md 获明确批准之前）
4. 禁止安装项目依赖或选择最终技术栈（在 SPEC 批准之前）
5. 禁止运行破坏性命令
6. 禁止请求、打印、记录、复制或提交任何真实 API key / GitHub token / 密码
7. 禁止将 OpenCode 自身的 agent loop / skills / hooks / permissions / memory / subagents / tools 当作交付 harness 的一部分

---

## SPEC 追溯矩阵

> 从 REQUIREMENTS_CHECKLIST.md 追溯到 SPEC.md 章节，确认每条硬性要求在 SPEC 中有对应设计。

| 需求 ID | SPEC 章节 | 覆盖状态 | 备注 |
|---|---|---|---|
| R001 | §1.1 + SPEC_PROCESS.md | ✅ | 过程纪律：禁止提前实现 |
| R004 | SPEC_PROCESS.md | ✅ | brainstorming 分块确认 |
| R005 | SPEC_PROCESS.md | ✅ | 12 轮迭代（≥3） |
| R013 | §1-§11 | ✅ | SPEC 10 节 + 额外节全覆盖 |
| R014 | §9 | ✅ | 领域与机制设计：反馈信号/危险动作/工具/记忆/重点维度/编码方式 |
| R015 | §10 | ✅ | 25 条客观验收标准（AC1-AC25） |
| R024-R026 | §4.2 威胁模型 T1-T3 | ✅ | 凭据三不：不硬编码/不提交/不入日志 |
| R027 | §7.1 | ✅ | keyring 安全存储 |
| R028 | §7.1 | ✅ | .env 降级 + 明文风险标注 |
| R029 | §3.7, §7.1 | ✅ | getpass 隐藏录入 |
| R030 | §3.7 | ✅ | status 掩码 / update / clear |
| R031 | §4.2 威胁模型表 | ✅ | 7 项威胁 + 对策 |
| R032 | §7.2 | ✅ | Docker + PyPI |
| R033 | §7.4 | ✅ | 目标机安全配置流程 |
| R034 | §7.4 | ✅ | fresh-machine 安装步骤 |
| R035 | §7.2 | ✅ | CI 构建镜像 |
| R037 | §3.8, §7.3 | ✅ | WebUI + Render 部署 URL |
| R038 | §3.1 | ✅ | agent 主循环自实现 |
| R039 | §5.1, §5.3, §8 | ✅ | LLMClient 抽象层 + MockLLMClient |
| R040 | §5.3 | ✅ | 底层零件清单 |
| R041 | §5.3, §8 | ✅ | 无高层框架依赖 |
| R042 | §3.3, §9.6 | ✅ | 反馈=代码校验器 |
| R043 | §3.4, §9.6 | ✅ | 治理=代码护栏 |
| R044 | §9.6, §10.2 | ✅ | mock-LLM 确定性单测覆盖 |
| R045 | §5.3 | ✅ | 内容物不计入 harness |
| R046 | §3.1-§3.6 | ✅ | 六维度最低实现 |
| R047 | §3.3, §9.5 | ✅ | 反馈闭环深入 |
| R048 | §3.5 | ✅ | 记忆自实现（非框架 memory） |
| R049 | §9.1-§9.4 | ✅ | 四类机制设计 |
| R050 | §3.1-§3.6 | ✅ | ≥3 功能模块 |
| R054 | §10.3 (AC17-AC19) | ✅ | 机制演示三行为 |

### 追溯结论

- 所有已识别的硬性要求在 SPEC.md 中均有对应章节覆盖；
- SPEC.md 待用户审查通过后，R013/R014/R015 状态更新为 DONE；
- 其余实现类需求（R016-R063）在 PLAN.md 创建后回填 PLAN Task ID。

### PLAN Task 映射

| 需求 ID | PLAN Task | 说明 |
|---|---|---|
| R001 | 全局 | 过程纪律：禁止提前实现 |
| R002-R003 | 全局 | Superpowers 工作流 |
| R004-R005 | SPEC_PROCESS.md | brainstorming 记录 |
| R006-R007 | Gate C | 冷启动验证 |
| R008 | 全局 PR1-PR13 | worktree 隔离 |
| R009 | 全局 T01-T29 | subagent 驱动 |
| R010 | 全局 T01-T29 | TDD 红绿重构 |
| R011 | 全局 T01-T29 | 两阶段评审 |
| R012 | 全局 PR1-PR13 | finishing-a-development-branch |
| R013 | SPEC.md §1-§11 | SPEC 10 节 |
| R014 | SPEC.md §9 | 领域与机制设计 |
| R015 | SPEC.md §10 | 验收标准 |
| R016-R017 | PLAN.md | PLAN task 粒度与依赖 |
| R018 | PLAN.md | PLAN 持续更新 |
| R019 | SPEC_PROCESS.md | 过程文档 |
| R020 | AGENT_LOG.md | 开发日志 |
| R021 | T27 | README |
| R022-R023 | T29 | REFLECTION（人工撰写） |
| R024-R031 | T17 | 凭据安全 |
| R032-R035 | T26 | 分发 |
| R036-R037 | T28 | 部署与 WebUI |
| R038 | T18 | agent 主循环 |
| R039 | T03-T05 | LLM 抽象 + mock |
| R040-R041 | T03, T05 | 底层零件 + 无高层框架 |
| R042 | T12-T16 | 反馈=代码 |
| R043 | T09-T11 | 治理=代码 |
| R044 | T22 | mock-LLM 确定性单测 |
| R045 | SPEC.md §5.3 | 内容物不计入 |
| R046 | T02,T06-T08,T09-T11,T12-T16,T17,T18 | 六维度最低 |
| R047 | T12-T16 | 反馈闭环深入 |
| R048 | T14 | 记忆自实现 |
| R049 | SPEC.md §9 | 四类机制 |
| R050 | T01-T21 | ≥3 功能模块 |
| R051 | T01 (Makefile) | 一键测试 |
| R052 | T24 | GitHub Actions |
| R053 | T22 | mock-LLM 单测 |
| R054 | T23 | 机制演示 |
| R055-R057 | 全局 PR1-PR13 | GitHub 仓库与 PR |
| R058 | T25 | .gitlab-ci.yml unit-test |
| R059 | T29 | CI/CD pass |
| R060 | 全局 | NJU Git 提交 |
| R061 | 全局 | 手写代码注释 |
| R062 | T27 | 第三方许可证 |
| R063 | T29 | 无凭据泄露 |

# FIX-WIN-01 Windows Native Acceptance Addendum

| ID | Source | Obligation | Plan Evidence | Verification Method | Status | PLAN Task |
|---|---|---|---|---|---|---|
| R064 | FIX-WIN-01 | Windows 11 + PowerShell + native Python is the primary supported runtime; Linux and Docker remain compatibility/deployment environments; Windows full pytest/Ruff/mypy must not retain known failed baseline. | PLAN.md FIX-WIN-01; AGENT_LOG.md LOG-048 | `python -m pytest -q`; `python -m ruff check harness webui tests`; `python -m mypy harness webui tests` | DONE (`797 passed, 5 skipped`; Ruff passed; mypy passed) | FIX-WIN-01 |

---
