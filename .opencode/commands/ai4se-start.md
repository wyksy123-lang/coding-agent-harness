---
description: Audit all AI4SE harness requirements and begin spec-driven brainstorming only
agent: plan
---

You are the primary development agent for my individual AI4SE final project. I am building a Coding Agent Harness with OpenCode and Superpowers. Treat the following two files together as the complete, authoritative assignment specification:

@docs/assignment/要求1.md
@docs/assignment/要求2.md

Before doing anything else:

1. Use the Superpowers skill system. Load and follow `using-superpowers`, then load and follow `brainstorming`.
2. Confirm that both assignment files were actually read. Do not merely summarize their headings.
3. Do not write implementation code, create implementation scaffolding, install project dependencies, select a final technology stack, or run destructive commands at this stage.
4. You may create or update documentation-only files needed for requirement tracking and brainstorming.
5. Never request, print, log, copy, or commit any real API key, GitHub token, password, or other credential. The API/provider configuration used by OpenCode is development tooling and must not be copied into the delivered harness.
6. Do not treat OpenCode's own agent loop, skills, hooks, permissions, memory, subagents, or tools as part of the harness being delivered. They may help develop the project, but the delivered harness kernel must be our own code.

## Phase 0 — exhaustive requirement audit

Create `REQUIREMENTS_CHECKLIST.md`. It must map every mandatory statement from both assignment files to:

- requirement ID and source section;
- exact obligation;
- planned evidence or deliverable path;
- verification method;
- current status: TODO / BLOCKED / DONE;
- related PLAN task ID when available.

The checklist must explicitly cover, at minimum:

- no implementation before SPEC + PLAN approval and cold-start validation;
- Superpowers workflow and required skills;
- at least three recorded brainstorming iterations;
- SPEC, PLAN, SPEC_PROCESS, AGENT_LOG, README and REFLECTION obligations;
- REFLECTION must remain human-authored; AI may only provide an outline or clearly marked proofreading assistance;
- five or more INVEST user stories;
- credential threat model and secure key input/status/update/clear behavior;
- distribution, fresh-machine installation, known limits and secure target-machine key configuration;
- at least three clear functional modules and one-command tests;
- self-written agent loop;
- injectable LLM abstraction and offline mock/stub LLM;
- no LangChain AgentExecutor, AutoGen, CrewAI, LlamaIndex agent, coding-agent runner, or other high-level agent loop in the delivered kernel;
- six minimum harness dimensions: decision, tools, memory, governance, feedback and configuration;
- one mechanism-dense dimension developed deeply as the main contribution;
- deterministic code-based guardrails and validators, not prompt-only rules;
- deterministic mock-LLM unit tests for tool dispatch, governance, feedback, memory and stopping;
- mechanism demo containing all three required behaviors;
- worktree per independent feature or large module and PR per worktree;
- fresh subagent per task;
- strict red → green → refactor TDD evidence;
- two-stage review: spec compliance first, code quality second;
- PLAN completion marks with commit hashes;
- commit and PR descriptions naming the subagent contribution and human modifications;
- GitHub Actions on push;
- `.gitlab-ci.yml` containing a job named exactly `unit-test`;
- final passing CI/CD run;
- GitHub public repository or documented TA collaboration if private;
- NJU Git/GitLab final submission requirement;
- mandatory accessible WebUI URL under the final checklist;
- README mandatory sections: introduction, installation, running, distribution commands, directory structure and security boundaries;
- third-party licenses and attribution;
- no real credentials anywhere in current files or Git history.

Identify contradictions and ambiguities instead of silently choosing one interpretation. At minimum, analyze:

1. GitHub repository and GitHub Actions versus NJU Git repository and `.gitlab-ci.yml`.
2. Conditional cloud deployment versus the final mandatory WebUI URL.
3. Pure CLI/backend exemption language versus the final mandatory WebUI.

For each conflict, state the safest compliance strategy. Unless I explicitly override it, use this conservative strategy:

- develop in a public GitHub repository with full branches, worktrees, PRs and GitHub Actions;
- also maintain an NJU Git/GitLab remote, commit `.gitlab-ci.yml`, push all required code and run the required `unit-test` job there;
- record both repository links and CI evidence;
- provide an accessible WebUI and deployment URL because the final checklist says it is mandatory;
- never claim that GitHub PR objects are mirrored automatically to GitLab; record GitHub PR links in AGENT_LOG and README, and create GitLab merge requests too when feasible.

Output an initial compliance report before starting design. The report must separate:

- confirmed hard requirements;
- conflicts and conservative resolutions;
- decisions that still require my approval;
- actions prohibited before the next gate.

## Phase 1 — brainstorming and SPEC process

After the audit, run the Superpowers `brainstorming` workflow interactively.

Rules:

- Ask one high-leverage question at a time.
- Do not invent my product goal when it is unclear.
- Offer alternatives with trade-offs when a design decision is needed.
- Challenge vague answers and request objective acceptance criteria.
- Explicitly distinguish the development harness (OpenCode + Superpowers) from the delivered harness.
- Compare possible main-contribution dimensions, especially governance, feedback loop and tool dispatch/extension.
- Ensure all six dimensions have a runnable minimum design.
- Ensure each proposed mechanism can still be tested after replacing the real LLM with a mock.
- Reject any design whose key behavior is only a prompt instruction.
- Reject any architecture whose delivered agent loop is provided by an existing high-level agent framework.
- Treat credential storage, distribution, WebUI and deployment as first-class design concerns rather than end-stage additions.

Maintain `SPEC_PROCESS.md` during the conversation. For every important round, append:

- my answer or decision;
- the agent suggestion;
- what I accepted, rejected or revised;
- why;
- resulting change to the design;
- any evidence needed later.

There must be at least three meaningful iterations, but do not stop merely after reaching three.

At the end of each design block, present it for explicit approval. Do not create the final `SPEC.md` until I clearly approve the full design.

## Gate A — SPEC approval

Only after I explicitly state that the design is approved:

1. Create `SPEC.md` with every section required by both assignment files.
2. Add the extra `领域与机制设计` section.
3. Include objective acceptance criteria for every feature and every core harness mechanism.
4. Include diagrams in Mermaid where useful, but ensure the text remains understandable without rendering.
5. Run a requirement traceability check from `SPEC.md` back to `REQUIREMENTS_CHECKLIST.md`.
6. Stop and ask me to review the SPEC. Do not create implementation code.

## Gate B — PLAN approval

Only after I explicitly approve `SPEC.md`:

1. Load and follow Superpowers `writing-plans`.
2. Create `PLAN.md` with tasks sized for one fresh subagent session and approximately 2–5 minute implementation steps inside each task.
3. Every task must include goal, dependencies, files, expected implementation details, the failing test to write first, verification commands, review steps, worktree branch name and PR evidence.
4. Mark dependencies and parallelizable tasks explicitly.
5. Include documentation, CI, security, distribution, WebUI, deployment and deterministic mechanism-demo tasks; do not postpone them as unspecified cleanup.
6. Update `REQUIREMENTS_CHECKLIST.md` with PLAN task mappings.
7. Stop for my explicit PLAN approval. Do not implement.

## Gate C — cold-start validation

After PLAN approval, do not implement yet. Produce only a cold-start package and instructions for a different agent type.

The cold-start agent must:

- be a different agent product/type, not merely a different model inside OpenCode;
- start in a new session with no prior chat, memory or hidden context;
- receive only `SPEC.md` and `PLAN.md`;
- select one or two tasks;
- pause and ask when uncertain instead of guessing.

After I return the cold-start findings, help me record questions, misinterpretations, output gaps and before/after SPEC/PLAN diffs in `SPEC_PROCESS.md`. Revise SPEC and PLAN, rerun traceability, then stop for my explicit confirmation that cold-start validation is complete.

## Gate D — implementation

Only after I explicitly confirm that the cold-start validation and revisions are complete may implementation begin.

For each task:

1. Load and follow the relevant Superpowers skills, including `using-git-worktrees`, `subagent-driven-development` or `executing-plans`, `test-driven-development`, `requesting-code-review`, and later `finishing-a-development-branch`.
2. Create or use a dedicated git worktree and branch for that feature/task group.
3. Dispatch a fresh subagent with only the task-specific context it needs.
4. Enforce TDD with saved evidence:
   - write the failing test first;
   - run it and record the expected failure;
   - implement the minimum change;
   - rerun and record the pass;
   - refactor and rerun all relevant checks.
5. Perform two separate reviews:
   - spec-compliance review;
   - code-quality review.
6. Fix every critical issue before proceeding.
7. Run all task verification commands.
8. Commit with a message that names the PLAN task and subagent contribution.
9. Update `PLAN.md` with status and commit hash.
10. Update `AGENT_LOG.md` with timestamp, task, skill, prompt/context, subagent result, tests, commit, human intervention and lesson.
11. Push the branch and prepare a PR whose description states:
    - requirement/task mapping;
    - subagent contribution;
    - human changes;
    - red/green/refactor evidence;
    - verification results;
    - remaining risks.
12. Do not merge until reviews and CI pass.

Never use host-agent permissions, hooks, skills or memory as a substitute for implementing and testing the delivered harness mechanisms in our own source code.

## Completion rules

Before claiming completion:

- load and follow `verification-before-completion` and `finishing-a-development-branch`;
- run the one-command test suite without network access for mock-LLM core tests;
- run lint/type checks and build/distribution checks;
- run the deterministic mechanism demo and show all three required behaviors;
- verify GitHub Actions and GitLab `unit-test` pass;
- scan tracked files and Git history for secrets;
- test fresh-machine installation and secure credential setup instructions;
- verify the deployed WebUI URL;
- update requirement traceability so every hard requirement points to evidence;
- do not draft my REFLECTION prose. You may only provide a question outline or proofread text that I wrote, with AI assistance clearly disclosed.

## What to do in this first invocation

Do only Phase 0 and begin Phase 1. Create/update documentation-only audit files as needed. Then present:

1. the exhaustive compliance report;
2. the conflicts and conservative resolution;
3. the first single brainstorming question.

Do not write any implementation code and do not create PLAN.md yet.
