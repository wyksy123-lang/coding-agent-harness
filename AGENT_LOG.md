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
