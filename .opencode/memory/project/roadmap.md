---
purpose: Project roadmap with phases, milestones, and bead organization
updated: 2026-02-12
---

# Roadmap

## Overview

| Phase  | Goal                                              | Status      | Beads |
| ------ | ------------------------------------------------- | ----------- | ----- |
| MVP    | Core `ock init` command with basic template       | Complete    | [#]   |
| Extend | Additional commands (`/ship`, `/plan`, `/resume`) | Complete    | [#]   |
| Polish | Error handling, docs, validation improvements     | Complete    | [#]   |
| Scale  | Plugin system, custom templates, advanced config  | In Progress | [#]   |

## Phase 1: MVP

**Goal:** Users can run `ock init` to generate a working OpenCode project template.

**Success Criteria:**

- [x] `ock init` command creates project structure
- [x] Generated files include AGENTS.md, skills, commands, memory
- [x] Templates pass typecheck and lint
- [x] Basic CLI prompts for project configuration

**Beads:**

| ID  | Title             | Type    | Status | Depends On |
| --- | ----------------- | ------- | ------ | ---------- |
| -   | Core init command | feature | closed | -          |
| -   | Template bundling | task    | closed | -          |
| -   | CLI prompts       | task    | closed | -          |

**Out of Scope:**

- Advanced customization
- Plugin system
- Multiple template options

---

## Phase 2: Extend

**Goal:** Add essential OpenCode commands for common workflows.

**Success Criteria:**

- [x] `/ship` command for deployment workflows
- [x] `/plan` command for implementation planning
- [x] `/resume` command for continuing work
- [x] `/handoff` command for session handoffs
- [x] `/status` command for project state

**Beads:**

| ID  | Title           | Type    | Status | Depends On |
| --- | --------------- | ------- | ------ | ---------- |
| -   | Ship command    | feature | closed | MVP        |
| -   | Plan command    | feature | closed | MVP        |
| -   | Resume command  | feature | closed | MVP        |
| -   | Handoff command | feature | closed | MVP        |
| -   | Status command  | feature | closed | MVP        |

**Dependencies:**

- Requires MVP completion

---

## Phase 3: Polish

**Goal:** Improve quality, documentation, and error handling.

**Success Criteria:**

- [x] Comprehensive error messages with actionable guidance
- [x] Documentation for all commands
- [x] Validation scripts for template integrity
- [x] Improved CLI UX with progress indicators

**Beads:**

| ID  | Title               | Type | Status | Depends On |
| --- | ------------------- | ---- | ------ | ---------- |
| -   | Error handling      | task | closed | Extend     |
| -   | Documentation       | task | closed | Extend     |
| -   | Validation scripts  | task | closed | Extend     |
| -   | CLI UX improvements | task | closed | Extend     |

**Dependencies:**

- Requires Extend completion

---

## Phase 4: Scale

**Goal:** Add advanced features for power users and customization.

**Success Criteria:**

- [ ] Plugin system for extending CLI functionality
- [ ] Custom template support (user-defined templates)
- [ ] Advanced configuration options
- [ ] Template marketplace or sharing mechanism

**Beads:**

| ID  | Title            | Type    | Status | Depends On    |
| --- | ---------------- | ------- | ------ | ------------- |
| -   | Plugin system    | epic    | open   | Polish        |
| -   | Custom templates | feature | open   | Polish        |
| -   | Advanced config  | task    | open   | Polish        |
| -   | Template sharing | epic    | open   | Plugin system |

**Dependencies:**

- Requires Polish completion

---

## Legend

**Status:**

- `Not Started` - No work begun
- `In Progress` - Active development
- `Complete` - All beads closed

**Type:**

- `task` - Tactical, single-session work
- `feature` - New capability, multi-session
- `epic` - Cross-domain, significant scope
- `bug` - Fix for broken behavior

---

_Update this file when phases complete or roadmap changes._
_Use `/plan` command to create detailed plans for active phases._
