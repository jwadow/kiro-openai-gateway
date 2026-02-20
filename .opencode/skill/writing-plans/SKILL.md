---
name: writing-plans
description: Use when design is complete and you need detailed implementation tasks for engineers with zero codebase context - creates comprehensive implementation plans with exact file paths, complete code examples, and verification steps assuming engineer has minimal domain knowledge
---

# Writing Plans

## Overview

Write comprehensive implementation plans assuming the engineer has zero context for our codebase and questionable taste. Document everything they need to know: which files to touch for each task, code, testing, docs they might need to check, how to test it. Give them the whole plan as bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume they are a skilled developer, but know almost nothing about our toolset or problem domain. Assume they don't know good test design very well.

**Announce at start:** "I'm using the writing-plans skill to create the implementation plan."

**Context:** This should be run in a dedicated worktree (created by brainstorming skill).

**Save plans to:** `docs/plans/YYYY-MM-DD-<feature-name>.md`

## Bite-Sized Task Granularity

**Each step is one action (2-5 minutes):**

- "Write the failing test" - step
- "Run it to make sure it fails" - step
- "Implement the minimal code to make the test pass" - step
- "Run the tests and make sure they pass" - step
- "Commit" - step

## Plan Document Header

**Every plan MUST start with this header:**

```markdown
# [Feature Name] Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use skill({ name: "executing-plans" }) to implement this plan task-by-task.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

### Goal-Backward Section (REQUIRED)

Document the reasoning that produced this plan using goal-backward methodology:

```markdown
## Must-Haves

**Goal:** [Outcome-shaped goal from PRD]

### Observable Truths

(What must be TRUE for the goal to be achieved?)

1. [Truth 1: User can...]
2. [Truth 2: User can...]
3. [Truth 3: User can...]

### Required Artifacts

(What must EXIST for truths to be true?)
| Artifact | Provides | Path |
|----------|----------|------|
| [File/component] | [What it does] | `src/path/to/file.ts` |

### Key Links

(Where is this most likely to break?)
| From | To | Via | Risk |
|------|-----|-----|------|
| [Component] | [API] | `fetch` | [Why it might fail] |
```

### Dependency Graph

```markdown
### Task Dependencies
```

Task A (User model): needs nothing, creates src/models/user.ts
Task B (Product model): needs nothing, creates src/models/product.ts
Task C (User API): needs Task A, creates src/api/users.ts

Wave 1: A, B (parallel)
Wave 2: C (after Wave 1)

```

```

## Context Budget

Target: ~50% context per plan execution
Maximum: 2-3 tasks per plan

| Task Complexity | Max Tasks | Typical Context |
| --------------- | --------- | --------------- |
| Simple (CRUD)   | 3         | ~30-45%         |
| Complex (auth)  | 2         | ~40-50%         |
| Very complex    | 1-2       | ~30-50%         |

**Split signals:**

- More than 3 tasks → Create child plans
- Multiple subsystems → Separate plans
- Any task with >5 file modifications → Split
- Checkpoint + implementation → Split
- Discovery + implementation → Split

## Task Structure

````markdown
### Task N: [Component Name]

**Files:**

- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

**Step 1: Write the failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```
````

**Step 2: Run test to verify it fails**

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

**Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```

```

## Remember
- Exact file paths always
- Complete code in plan (not "add validation")
- Exact commands with expected output
- Reference relevant skills with @ syntax
- DRY, YAGNI, TDD, frequent commits

## Execution Handoff

After saving the plan, offer execution choice:

**"Plan complete and saved to `.beads/artifacts/<bead-id>/plan.md`. Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?"**

**If Subagent-Driven chosen:**
- **REQUIRED SUB-SKILL:** Use skill({ name: "subagent-driven-development" })
- Stay in this session
- Fresh subagent per task + code review

**If Parallel Session chosen:**
- Guide them to open new session in worktree
- **REQUIRED SUB-SKILL:** New session uses skill({ name: "executing-plans" })
```
