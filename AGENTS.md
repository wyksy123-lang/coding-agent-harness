# AI4SE Coding Agent Harness — Codex Project Instructions

## Authoritative sources

Before modifying code, read these files completely:

- `SPEC.md`
- `PLAN.md`
- `SPEC_PROCESS.md`
- `REQUIREMENTS_CHECKLIST.md`
- `AGENT_LOG.md`
- this `AGENTS.md`
- relevant Git history

`SPEC.md` and `PLAN.md` are authoritative. Do not silently change scope.

## Handoff state

Development began in OpenCode and is now continuing in Codex because the
previous model API quota was exhausted.

The current `main` branch records T01–T12 as completed. Determine the exact
next task from the latest `PLAN.md`, `AGENT_LOG.md`, and Git history rather
than trusting conversation memory.

Record the OpenCode → Codex transition honestly in `AGENT_LOG.md`. Do not
describe Codex work as OpenCode work.

## Established task workflow

The repository currently uses one top-level PLAN task per run:

- one managed Codex worktree;
- one task branch;
- one Pull Request;
- one fresh implementation subagent;
- separate Red, Green, Refactor/Review, and Docs evidence;
- stop before push.

Although `PLAN.md` groups tasks into larger logical PR modules, continue the
repository's established one-task-per-run workflow unless the human explicitly
approves a different grouping.

When the Codex desktop app has already created a managed worktree, do not
create a nested Git worktree.

## Select exactly one task

At the start of each run:

1. Verify the task starts from the latest `main`.
2. Read `PLAN.md` and find the first incomplete task whose dependencies are
   satisfied.
3. State the chosen task ID, goal, dependencies, files, Red command, Green
   command, and final verification commands.
4. Complete only that task.
5. Do not begin another task in the same run.

## Mandatory TDD sequence

For the selected task, preserve evidence in separate commits.

### Red

1. Delegate implementation preparation to a fresh subagent.
2. Write the required failing test before implementation.
3. Run the exact Red command from `PLAN.md`.
4. Confirm failure is caused by missing required behavior, not syntax,
   environment, dependency, or test errors.
5. Commit with a message such as:
   `test(TXX): add failing tests [subagent: ...; human: pending review]`

### Green

1. Implement only the minimum behavior needed to pass the Red tests.
2. Run target tests and relevant regression tests.
3. Commit with a message such as:
   `feat(TXX): implement minimal green solution [subagent: ...; human: pending review]`

### Refactor and reviews

1. Refactor without changing approved behavior.
2. Run tests after meaningful changes.
3. Use a fresh reviewer subagent for Specification Compliance Review.
4. Fix all Critical specification issues.
5. Use a reviewer subagent for Code Quality Review.
6. Fix all Critical quality issues.
7. Run target tests, the full suite, lint, type checking, and credential scan.
8. Commit with a message such as:
   `refactor(TXX): complete reviews and verification [subagent: reviewer; human: pending review]`

### Process evidence

Update:

- `PLAN.md`
- `AGENT_LOG.md`
- `REQUIREMENTS_CHECKLIST.md`

Record the real subagents, prompts/context, commands, outputs, human gates, and
commit hashes. Commit with a message such as:

`docs(TXX): record task completion evidence [human review pending]`

## Safety

Never:

- push, merge, force-push, or modify remote branches;
- commit directly to `main`;
- perform a second task in the same run;
- request, read, print, store, or commit real API keys, GitHub PATs, passwords,
  tokens, or credential files;
- use a real network or real LLM for deterministic core unit tests;
- bypass failing tests or falsely report checks as passed;
- replace the project's own harness core with an existing high-level agent
  runner.

Use mock/stub LLMs and mocked transports for deterministic tests.

## Completion gate

At the end of one task:

1. Ensure the worktree is clean.
2. Output the chosen task and branch.
3. List Red, Green, Refactor/Review, and Docs commit hashes.
4. Report target tests, full tests, lint, typecheck, and credential scan.
5. Provide the exact manual push command.
6. Provide a PR title and PR body.
7. Stop and wait for the human to push and merge.

The next task may start only after the human merges the PR, synchronizes
`main`, creates a fresh Codex worktree from `main`, and starts a new task.
