# GSD ↔ OpenCodeKit Agent Alignment

## Executive Summary

GSD has **11 specialized agents** (~12,000 total lines) vs OpenCodeKit's **8 general agents** (~1,200 total lines). GSD's depth enables rigorous execution; OpenCodeKit's simplicity enables faster adoption. This document maps them and proposes a hybrid architecture.

---

## Agent Mapping Matrix

| GSD Agent                  | Lines | Role                                                                                              | OpenCodeKit Equivalent                                        | Gap Analysis                                                                                                 |
| -------------------------- | ----- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `gsd-planner`              | 1,158 | Creates executable phase plans with goal-backward methodology, dependency graphs, wave assignment | `plan` (225 lines)                                            | **5x depth gap**: GSD has TDD detection, discovery levels, scope estimation, gap closure mode, revision mode |
| `gsd-executor`             | 404   | Executes plans atomically with deviation rules, checkpoint protocol, TDD cycles                   | `build` (191 lines)                                           | **2x depth gap**: GSD has 4 deviation rules, auth gates, task commit protocol, self-check                    |
| `gsd-verifier`             | 524   | Goal-backward verification (not task completion) with 3-level artifact checks                     | `review` (104 lines) + `verification-before-completion` skill | **Verifies goals vs code**: GSD checks if phase goal achieved, not just if tasks ran                         |
| `gsd-debugger`             | 1,199 | Systematic debugging with scientific method, hypothesis testing, debug file protocol              | `systematic-debugging` + `root-cause-tracing` skills          | **Structured process**: GSD has debug file protocol, evidence tracking, elimination lists                    |
| `gsd-phase-researcher`     | ~300  | Domain research for specific phases                                                               | `scout` (91 lines)                                            | Similar scope, GSD has more structured output                                                                |
| `gsd-research-synthesizer` | ~200  | Aggregates parallel research findings                                                             | _No equivalent_                                               | **Missing**: Multi-agent research aggregation                                                                |
| `gsd-plan-checker`         | ~400  | Validates plans against requirements before execution                                             | _No equivalent_                                               | **Missing**: Pre-execution plan validation                                                                   |
| `gsd-roadmapper`           | ~300  | Creates ROADMAP.md with phase structure                                                           | _No equivalent_                                               | **Missing**: Dedicated roadmap creation                                                                      |
| `gsd-codebase-mapper`      | ~500  | Analyzes existing codebase architecture                                                           | `explore` (65 lines)                                          | Deeper analysis: stack, conventions, concerns, architecture                                                  |
| `gsd-project-researcher`   | ~250  | Project-level ecosystem research                                                                  | `scout`                                                       | Overlaps with phase-researcher                                                                               |
| `gsd-integration-checker`  | ~200  | Validates integrations work correctly                                                             | _No equivalent_                                               | **Missing**: Integration validation agent                                                                    |

---

## Detailed Alignment

### 1. PLANNER ALIGNMENT

#### GSD gsd-planner (1,158 lines)

```yaml
Core Capabilities:
  - Goal-backward methodology (truths → artifacts → wiring)
  - Discovery levels (0-3) with mandatory protocol
  - TDD detection heuristic
  - Dependency graph construction (needs/creates/has_checkpoint)
  - Wave assignment for parallel execution
  - Scope estimation with context budget rules (~50% target)
  - Gap closure mode (--gaps flag)
  - Revision mode (checker feedback incorporation)
  - Checkpoint protocol (3 types with structured returns)
  - XML task format specification

Key Concepts:
  - Plans ARE prompts (not documents that become prompts)
  - Vertical slices preferred over horizontal layers
  - 2-3 tasks per plan maximum
  - Deviation rules (4 rules for auto-fixing)
```

#### OpenCodeKit plan (225 lines)

```yaml
Core Capabilities:
  - Architecture as ritual philosophy
  - Five-phase ritual (Ground → Calibrate → Transform → Release → Reset)
  - Memory ritual for planning context
  - Delegation to @explore and @scout
  - Basic plan artifact structure

Gaps vs GSD:
  - No goal-backward methodology
  - No discovery levels
  - No TDD detection
  - No dependency graphs or wave assignment
  - No context budget awareness
  - No checkpoint protocol
  - No gap closure or revision modes
```

#### Recommended: Enhanced plan Agent

```markdown
## Enhancements to port from GSD:

1. **Add Goal-Backward Section**
   - Derive observable truths from PRD goals
   - Map truths → artifacts → wiring
   - Document must_haves in plan frontmatter

2. **Add Discovery Levels**
   - Level 0: Skip (existing patterns only)
   - Level 1: Quick verification (2-5 min)
   - Level 2: Standard research (15-30 min)
   - Level 3: Deep dive (1+ hour)

3. **Add Dependency Graph Construction**
   - For each task: record needs/creates/has_checkpoint
   - Assign waves based on dependencies
   - Identify parallelization opportunities

4. **Add Context Budget Rules**
   - ~50% context target per plan
   - 2-3 tasks maximum per plan
   - Split signals (>5 files, >3 tasks)

5. **Add Checkpoint Protocol**
   - checkpoint:human-verify (90% of cases)
   - checkpoint:decision (9%)
   - checkpoint:human-action (1%)
```

---

### 2. EXECUTOR ALIGNMENT

#### GSD gsd-executor (404 lines)

```yaml
Core Capabilities:
  - Deviation rules (4 explicit rules)
  - Authentication gates (auth errors as checkpoints)
  - Checkpoint protocol with continuation handling
  - TDD execution (RED → GREEN → REFACTOR)
  - Task commit protocol (per-task commits)
  - Summary creation with frontmatter
  - Self-check before proceeding
  - State updates via gsd-tools

Deviation Rules:
  Rule 1: Auto-fix bugs (no permission needed)
  Rule 2: Auto-add missing critical functionality
  Rule 3: Auto-fix blocking issues
  Rule 4: ASK about architectural changes
```

#### OpenCodeKit build (191 lines)

```yaml
Core Capabilities:
  - Five-phase ritual (Ground → Calibrate → Transform → Release → Reset)
  - Verification as calibration
  - Memory ritual
  - Delegation patterns
  - Skills loading

Gaps vs GSD:
  - No deviation rules
  - No checkpoint protocol
  - No TDD execution flow
  - No per-task commit protocol
  - No self-check requirement
```

#### Recommended: Enhanced build Agent

```markdown
## Enhancements to port from GSD:

1. **Add Deviation Rules Section**
   - Rule 1: Auto-fix bugs (broken behavior, errors)
   - Rule 2: Auto-add missing critical functionality (validation, auth, error handling)
   - Rule 3: Auto-fix blocking issues (missing deps, wrong types)
   - Rule 4: ASK about architectural changes (new tables, library switches)

2. **Add Checkpoint Protocol**
   - Stop at checkpoint:\* tasks
   - Return structured checkpoint message
   - Support continuation agents

3. **Add TDD Execution Flow**
   - RED: Create failing test → commit
   - GREEN: Minimal code to pass → commit
   - REFACTOR: Clean up → commit if changes

4. **Add Task Commit Protocol**
   - Check modified files: git status --short
   - Stage individually (NEVER git add .)
   - Commit format: type(phase-plan): description
   - Record hash for summary

5. **Add Self-Check Requirement**
   - Verify created files exist
   - Verify commits exist
   - Append result to summary
```

---

### 3. VERIFIER ALIGNMENT

#### GSD gsd-verifier (524 lines)

```yaml
Core Philosophy:
  - Task completion ≠ Goal achievement
  - Goal-backward verification (not task-forward)
  - Do NOT trust SUMMARY.md claims
  - Verify what ACTUALLY exists in code

Three-Level Verification:
  Level 1: Exists (file present)
  Level 2: Substantive (not a stub)
  Level 3: Wired (connected/used)

Artifact Verification:
  - Use gsd-tools for automated checks
  - Map to must_haves from PLAN frontmatter
  - Status: VERIFIED | STUB | MISSING | ORPHANED

Key Link Verification:
  - Component → API (fetch + response handling)
  - API → Database (query + result returned)
  - Form → Handler (handler + API call)
  - State → Render (state displayed)
```

#### OpenCodeKit review (104 lines)

```yaml
Core Philosophy:
  - Read-only review agent
  - Quality guardian mindset
  - Severity-ranked findings (P0-P3)

Triage Criteria:
  - Affects correctness, performance, security
  - Introduced or worsened by change
  - Fixable without unrealistic rigor
  - Author would actually want to fix

Gaps vs GSD:
  - Reviews code changes, not goal achievement
  - No three-level artifact verification
  - No key link verification
  - No stub detection patterns
```

#### Recommended: New verify Agent OR Enhanced review

````markdown
## Option A: New verify Agent (recommended)

Create `.opencode/agent/verify.md` as goal-backward verifier:

```yaml
---
description: Goal-backward verification agent - checks if goals are achieved, not just tasks completed
mode: subagent
---
Core Responsibilities: 1. Load PRD success criteria
  2. Derive observable truths
  3. Verify artifacts exist and are substantive
  4. Verify key links are wired
  5. Detect stubs and anti-patterns
  6. Report gaps in structured format
```
````

## Option B: Enhanced review Agent

Add section to existing review.md:

- Goal-backward verification mode
- Three-level artifact checking
- Stub detection patterns
- Key link verification

````

---

### 4. DEBUGGER ALIGNMENT

#### GSD gsd-debugger (1,199 lines)
```yaml
Core Philosophy:
  - User = Reporter, Claude = Investigator
  - Meta-debugging: fighting your own mental model
  - Scientific method: falsifiable hypotheses
  - Foundation principles: observable facts only

Cognitive Biases to Avoid:
  - Confirmation bias
  - Anchoring
  - Availability bias
  - Sunk cost fallacy

Investigation Techniques:
  - Binary search / divide and conquer
  - Rubber duck debugging
  - Minimal reproduction
  - Working backwards
  - Differential debugging
  - Observability first
  - Comment out everything
  - Git bisect

Debug File Protocol:
  Location: .planning/debug/{slug}.md
  Sections: Symptoms, Eliminated, Evidence, Resolution
  Update rules: OVERWRITE vs APPEND
  Status transitions: gathering → investigating → fixing → verifying → resolved
````

#### OpenCodeKit Skills

```yaml
Existing:
  - systematic-debugging skill
  - root-cause-tracing skill

Gaps vs GSD:
  - No debug file protocol
  - No persistent debug state
  - No cognitive bias awareness
  - No investigation technique library
```

#### Recommended: Port to New Skill

```markdown
## Create `.opencode/skill/gsd-debugging/SKILL.md`

Port GSD debugger content as skill:

- Scientific method framework
- Hypothesis testing protocol
- Investigation techniques (8 methods)
- Debug file protocol
- Verification patterns
- Research vs reasoning decision tree
```

---

### 5. RESEARCH AGENTS ALIGNMENT

#### GSD Research Agents

```yaml
gsd-phase-researcher:
  - Domain research for specific phases
  - Stack investigation
  - Architecture patterns
  - Pitfall identification

gsd-research-synthesizer:
  - Aggregates parallel research findings
  - Resolves conflicts
  - Produces unified recommendations

gsd-project-researcher:
  - Project-level ecosystem research
  - Similar to phase-researcher but broader
```

#### OpenCodeKit Research Agents

```yaml
scout (91 lines):
  - External research specialist
  - Source quality hierarchy
  - Concise recommendations

explore (65 lines):
  - Read-only codebase cartographer
  - LSP-based symbol lookup
  - Usage pattern discovery
```

#### Gap: Research Synthesizer

```markdown
## Missing: gsd-research-synthesizer equivalent

When multiple scout/explore agents run in parallel,
there's no dedicated agent to:

- Aggregate findings
- Resolve conflicts
- Produce unified recommendations

Recommendation: Add synthesis responsibility to plan agent
or create dedicated research-lead agent.
```

---

### 6. SPECIALIZED GSD AGENTS (No OpenCodeKit Equivalent)

#### gsd-plan-checker (~400 lines)

```markdown
Validates plans against requirements before execution.

Dimensions Checked:

- requirement_coverage: All requirements have tasks
- task_completeness: All tasks have required elements
- dependency_correctness: Dependencies are valid
- key_links_planned: Critical connections planned
- scope_sanity: Plan is achievable
- must_haves_derivation: must_haves exist and are valid

Recommendation: Add as skill or plan agent mode
```

#### gsd-roadmapper (~300 lines)

```markdown
Creates ROADMAP.md with phase structure.

Outputs:

- PROJECT.md (vision)
- REQUIREMENTS.md (scoped v1/v2)
- ROADMAP.md (phases with goals)
- STATE.md (memory)

Recommendation: Add `/roadmap` command
```

#### gsd-codebase-mapper (~500 lines)

```markdown
Analyzes existing codebase before new work.

Produces:

- STACK.md (tech stack)
- ARCHITECTURE.md (patterns)
- CONVENTIONS.md (coding standards)
- CONCERNS.md (tech debt, issues)
- STRUCTURE.md (file organization)
- INTEGRATIONS.md (external deps)
- TESTING.md (test patterns)

Recommendation: Add `/map-codebase` command
```

#### gsd-integration-checker (~200 lines)

```markdown
Validates integrations work correctly.

Checks:

- API contracts
- Database connections
- External service health
- Webhook endpoints
- Auth flows

Recommendation: Add to verify agent or as skill
```

---

## Unified Agent Architecture Proposal

### Primary Agents (Keep Current Structure)

```yaml
build:
  role: Primary execution coordinator
  enhancements:
    - Add deviation rules section
    - Add checkpoint protocol
    - Add TDD execution flow
    - Add task commit protocol

plan:
  role: Blueprint architect
  enhancements:
    - Add goal-backward methodology
    - Add discovery levels
    - Add dependency graph construction
    - Add wave assignment
    - Add context budget rules

explore:
  role: Read-only codebase cartographer
  current: Good alignment with gsd-codebase-mapper

review:
  role: Code review specialist
  enhancements:
    - Add goal-backward verification mode
    - OR create separate verify agent

scout:
  role: External research specialist
  current: Good alignment with gsd-phase-researcher
```

### New Agents to Create

```yaml
verify (NEW):
  description: Goal-backward verification agent
  purpose: Check if goals achieved, not just tasks completed
  ported_from: gsd-verifier

research-lead (NEW - optional):
  description: Research synthesis coordinator
  purpose: Aggregate parallel research, resolve conflicts
  ported_from: gsd-research-synthesizer
```

### New Commands to Create

```yaml
/map-codebase:
  description: Analyze existing codebase
  creates: STACK.md, ARCHITECTURE.md, CONVENTIONS.md, etc.
  ported_from: gsd:map-codebase

/roadmap:
  description: Create project roadmap
  creates: PROJECT.md, REQUIREMENTS.md, ROADMAP.md, STATE.md
  ported_from: gsd:new-project (planning phase only)

/verify:
  description: Verify goal achievement
  purpose: Run verify agent against bead
  ported_from: gsd:verify-work
```

### New Skills to Create

```yaml
gsd-planning:
  description: GSD-style planning methodology
  content: Goal-backward, discovery levels, dependency graphs, wave assignment

gsd-debugging:
  description: Systematic debugging with scientific method
  content: Hypothesis testing, investigation techniques, debug file protocol

gsd-execution:
  description: GSD-style execution discipline
  content: Deviation rules, checkpoint protocol, TDD cycles
```

---

## Implementation Priority

| Priority | Item                               | Effort | Impact |
| -------- | ---------------------------------- | ------ | ------ |
| P0       | Add deviation rules to build agent | 2h     | High   |
| P0       | Add goal-backward to plan agent    | 4h     | High   |
| P1       | Create verify agent                | 6h     | High   |
| P1       | Add checkpoint protocol to build   | 3h     | High   |
| P2       | Create gsd-debugging skill         | 4h     | Medium |
| P2       | Create gsd-planning skill          | 4h     | Medium |
| P2       | Add /map-codebase command          | 4h     | Medium |
| P3       | Create research-lead agent         | 3h     | Low    |
| P3       | Add /roadmap command               | 3h     | Low    |

---

## Summary

**GSD's Strength:** Deep, rigorous methodology with explicit protocols for every phase.

**OpenCodeKit's Strength:** Clean architecture, Beads integration, skills system.

**The Opportunity:** Port GSD's execution discipline (deviation rules, goal-backward verification, checkpoint protocol) into OpenCodeKit's cleaner architecture. Don't adopt GSD's ceremony — adapt its rigor.

**Key Principle:** Plans ARE prompts. Don't create documents that become prompts — create the prompt directly. This is GSD's core insight that OpenCodeKit should adopt.
