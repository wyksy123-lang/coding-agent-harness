---
description: 自动完成 PLAN 中下一个未完成模块，停在 push 前
agent: ai4se-orchestrator
---

完整读取并遵循：

@SPEC.md
@PLAN.md
@SPEC_PROCESS.md
@REQUIREMENTS_CHECKLIST.md
@AGENT_LOG.md

本次任务是自动完成 PLAN.md 中下一个未完成的实现范围。

## 1. 启动检查

首先检查：

1. 当前主仓库分支必须是 main；
2. 主仓库工作区必须干净；
3. main 必须与 origin/main 指向同一提交；
4. SPEC、PLAN、冷启动和 Implementation Readiness Gate 已完成；
5. 不得在主仓库直接编写实现代码；
6. 不得读取或输出任何凭据。

任一检查失败时立即停止，只说明需要人工处理的问题。

## 2. 选择本次实现范围

读取 PLAN.md：

1. 找到第一个未完成且依赖已满足的顶层实现模块；
2. 如果 PLAN 明确标注多个小 task 属于同一个 worktree/PR，
   则本次处理该完整分组；
3. 否则把第一个未完成的顶层 TASK 作为一个 worktree/PR；
4. 不得提前实现不属于本次范围的后续 TASK。

确定：

- TASK 或模块编号；
- 英文短名称 slug；
- branch 名称：task/<TASK-ID>-<slug>；
- worktree 路径：
  ~/projects/coding-agent-harness-worktrees/<TASK-ID>-<slug>。

## 3. 创建 worktree

从当前最新 main 创建：

- 独立 task 分支；
- 独立 worktree。

创建前确认同名分支和目录不存在。

后续所有文件修改、测试和 commit 都必须在该 worktree 内完成。
所有 subagent 必须获得 worktree 的绝对路径，并且只能操作该路径。

## 4. 逐个执行 task

按照 PLAN 中依赖顺序处理本 worktree 范围内的每个 task。

每个 task 必须使用一个新鲜 subagent。

### 4.1 Red

1. 提取 task 的目标、文件路径、失败测试、验证命令和验收标准；
2. 先写失败测试；
3. 禁止先写实现；
4. 实际运行测试；
5. 确认失败是因为目标功能缺失，而不是语法、环境或依赖错误；
6. 把命令、退出状态和关键失败原因写入 AGENT_LOG.md；
7. 创建 commit：

   test(<TASK-ID>): add failing tests
   [subagent: <类型>; human: pending review]

### 4.2 Green

1. 只编写使当前失败测试通过的最少代码；
2. 不增加未要求的功能；
3. 运行目标测试；
4. 运行相关回归测试；
5. 把测试结果写入 AGENT_LOG.md；
6. 创建 commit：

   feat(<TASK-ID>): implement minimal green solution
   [subagent: <类型>; human: pending review]

### 4.3 Refactor

1. 在不改变已批准行为的前提下重构；
2. 实质性重构后重新运行测试；
3. 不得扩大 task 范围。

### 4.4 第一阶段评审

执行 Specification Compliance Review：

- 对照 SPEC.md；
- 对照 PLAN.md 中当前 task；
- 对照验收标准；
- 检查缺失实现和越界实现；
- 修复所有 Critical specification issue。

### 4.5 第二阶段评审

使用新的 reviewer subagent 执行 Code Quality Review：

- 职责划分；
- 可读性；
- 接口和类型；
- 错误处理；
- 安全边界；
- 测试质量；
- 可维护性；
- 是否错误依赖真实网络或真实 LLM。

修复所有 Critical code-quality issue。

### 4.6 最终验证

根据项目实际技术栈执行：

- 当前 task 目标测试；
- 完整测试套件；
- lint；
- 类型检查；
- 凭据泄露检查。

harness 核心机制测试不得依赖真实网络或真实 LLM，
必须使用 mock/stub LLM。

创建 commit：

refactor(<TASK-ID>): complete reviews and verification
[subagent: reviewer; human: pending review]

## 5. 完成本次模块

完成本 worktree 范围内全部 task 后：

1. 更新 PLAN.md：
   - 标记 task 已完成；
   - 写入对应 commit hash；
   - 记录 Red、Green、Refactor 和评审状态。

2. 更新 AGENT_LOG.md：
   - 每个新鲜 subagent；
   - 关键 prompt/context；
   - 测试命令及结果；
   - 两阶段评审；
   - 待人工检查的内容。

3. 更新 REQUIREMENTS_CHECKLIST.md。

4. 创建过程证据 commit：

   docs(<MODULE-ID>): record task completion evidence
   [human review pending]

## 6. 强制停止条件

不得执行：

- git push；
- git merge；
- git rebase；
- PR 创建或合并；
- 直接修改 main；
- 任何凭据操作。

如果发生以下情况，立即停止：

- PLAN 含糊，无法确定 task 范围；
- 依赖未满足；
- 测试不能产生有效 Red；
- Critical issue 无法修复；
- 需要真实凭据；
- 需要危险 shell 命令；
- 完整测试无法通过。

## 7. 最终输出

结束时输出：

1. 本次 TASK/模块；
2. branch 名称；
3. worktree 路径；
4. subagent 列表；
5. Red、Green、Refactor commit hash；
6. 两阶段评审结果；
7. 完整测试、lint、类型检查结果；
8. git status；
9. 尚未 push 的 commit 列表；
10. 建议的 push 命令；
11. 建议的 PR 标题；
12. 建议的 PR 描述。

完成后停止，等待人工检查和 push。
