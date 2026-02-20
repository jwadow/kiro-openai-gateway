---
name: brainstorming
description: Use when creating or developing, before writing code or implementation plans - refines rough ideas into fully-formed designs through collaborative questioning, alternative exploration, and incremental validation. Don't use during clear 'mechanical' processes
---

# Brainstorming Ideas Into Designs

## Overview

Help turn ideas into fully formed designs and specs through natural collaborative dialogue.

Start by understanding the current project context, then ask questions one at a time to refine the idea. Once you understand what you're building, present the design in small sections (200-300 words), checking after each section whether it looks right so far.

**Part of:** `development-lifecycle` skill (Phase 1: Ideation)

**Output template:** `.opencode/memory/_templates/design.md`

## The Process

**Understanding the idea:**

- Check out the current project state first (files, docs, recent commits)
- Ask questions one at a time to refine the idea
- Prefer multiple choice questions when possible, but open-ended is fine too
- Only one question per message - if a topic needs more exploration, break it into multiple questions
- Focus on understanding: purpose, constraints, success criteria

**Exploring approaches:**

- Propose 2-3 different approaches with trade-offs
- Present options conversationally with your recommendation and reasoning
- Lead with your recommended option and explain why

**Presenting the design:**

- Once you believe you understand what you're building, present the design
- Break it into sections of 200-300 words
- Ask after each section whether it looks right so far
- Cover: architecture, components, data flow, error handling, testing
- Be ready to go back and clarify if something doesn't make sense

## After the Design

**Documentation:**

- Write the validated design to `.beads/artifacts/<bead-id>/design.md`
- Use template from `.opencode/memory/_templates/design.md`
- Use elements-of-style:writing-clearly-and-concisely skill if available
- Commit the design document to git

**Next Phase (if continuing):**

- Ask: "Ready to create the PRD?"
- Load next skill: `skill({ name: "prd" })`
- This moves to Phase 2: Specification

**Alternative paths:**

- Use `skill({ name: "using-git-worktrees" })` to create isolated workspace first
- Use `skill({ name: "writing-plans" })` if skipping formal PRD

**Full lifecycle reference:**

- Use `skill({ name: "development-lifecycle" })` to see all phases

## Key Principles

- **One question at a time** - Don't overwhelm with multiple questions
- **Multiple choice preferred** - Easier to answer than open-ended when possible
- **YAGNI ruthlessly** - Remove unnecessary features from all designs
- **Explore alternatives** - Always propose 2-3 approaches before settling
- **Incremental validation** - Present design in sections, validate each
- **Be flexible** - Go back and clarify when something doesn't make sense
