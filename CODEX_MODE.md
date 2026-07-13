# CODEX_MODE.md

# Codex Efficient Completion Mode

## Purpose

This repository is currently in completion phase.

Goal:
Finish remaining TASKs with minimum token consumption while maintaining correctness.

Priorities:
1. Complete required TASK implementation.
2. Keep existing architecture stable.
3. Pass necessary tests.
4. Maintain required Git history.
5. Move efficiently to next TASK.

---

## 1. Document Reading Policy

When starting a new TASK, read:

Required:
- AGENTS.md
- Relevant SPEC section

Only read when necessary:
- PLAN.md
- SPEC_PROCESS.md
- REQUIREMENTS_CHECKLIST.md
- AGENT_LOG.md

Do not repeatedly reload all documents for every TASK.

---

## 2. Output Policy

Keep responses concise.

Only report:

TASK:
Branch:
Worktree:

Implementation:
- short summary

Verification:
- tests executed
- result

Next action:

Avoid:
- long explanations
- repeated summaries
- unnecessary file descriptions

---

## 3. Implementation Strategy

Prefer:
- Minimal correct implementation
- Existing repository patterns
- Reuse existing utilities

Avoid:
- Architecture redesign
- Unnecessary dependencies
- Unrelated refactoring
- Modifying completed TASKs

If existing code already satisfies requirements:
verify and continue.

---

## 4. Testing Strategy

Priority:

Required:
- TASK-specific tests
- Related regression tests

Optional:
- Full test suite only when needed

Do not spend excessive tokens on unrelated failures.

---

## 5. Review Strategy

Perform lightweight verification:

Check:
- Import/compile errors
- Logic bugs
- Interface mismatch
- Missing functionality

Avoid:
- Long simulated reviews
- Style discussions
- Excessive refactoring

---

## 6. Git Commit Policy

Maintain TASK history:

test(TASK):
add failing tests

feat(TASK):
implement minimal solution

refactor(TASK):
verification and improvements

docs(TASK):
completion evidence

Docs commit should be minimal.

---

## 7. Worktree Policy

For every TASK:

1. Start from latest main.
2. Create fresh worktree.
3. Create TASK branch.
4. Modify only current TASK.

Do not modify:
- Other TASK branches
- Completed history
- main directly

Before coding report:

Current main commit:
Worktree:
Branch:
TASK:

---

## 8. Error Handling

Continue unless blocked.

Ask human only when:
- Requirements are unclear
- Continuing may break existing functions
- Destructive operation is needed

---

## 9. Completion Policy

After TASK completion report:

TASK completed.

Branch:
Commit list:

Validation:
- tests
- lint
- other checks

Waiting for push/merge.

Do not start next TASK until:
- Current TASK merged
- main synchronized

---

## Final Goal

Complete remaining TASKs successfully.

Optimize for:
- reliable code
- low token usage
- efficient progress

Prefer progress over unnecessary process.
