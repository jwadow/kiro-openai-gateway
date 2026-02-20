# Swarm Protocol (Beads-as-Board)

## Goal

Use `.beads/` as the single source of truth for task state + dependencies, while agents coordinate through structured artifacts (not freeform chatter) and verification gates.

## Roles (Strict)

- Lead: Owns scope, prioritization, and all Beads state transitions.
- Planner: Turns intent into Beads tasks + dependency DAG; no code changes.
- Worker: Executes exactly one claimed task; posts a structured report.
- Verifier: Independently validates acceptance checks; blocks close on missing evidence.

## Board = Beads

Canonical state lives in `.beads/issues.jsonl` (tasks) and `.beads/artifacts/<id>/` (task artifacts).

- Create tasks: `br create "Title" -p <1-3>`
- See unblocked work: `br ready`
- Inspect context: `br show <id>`
- Claim work: `br update <id> --status=in_progress`
- Close work: `br close <id> --reason="..."` then `br sync --flush-only`

## Task Artifact Contract

Every task MUST have `.beads/artifacts/<id>/spec.md`.

Optional supporting files:

- `.beads/artifacts/<id>/plan.md`: multi-step implementation plan, files touched, and gates
- `.beads/artifacts/<id>/review.md`: verifier notes + evidence summary

### spec.md (Minimum Template)

- Context: why this exists
- Scope: in / out
- Constraints: MUST / MUST NOT (security, deps, dist/, etc.)
- Acceptance Criteria: checkboxes, each with a verification method
- Evidence Required: exact commands and expected signals (e.g. "typecheck command passes")

#### Verification Defaults (Language-Agnostic)

Do NOT assume npm/bun/pytest/etc. Prefer this pattern:

- `typecheck`: `<command>`
- `lint`: `<command>`
- `test`: `<command>`
- `build` (optional): `<command>`

If the repository has a canonical list of commands, reference it (e.g. `.opencode/memory/project/commands.md`).

Common stacks (examples only):

| Stack   | typecheck                                  | lint                         | test                     |
| ------- | ------------------------------------------ | ---------------------------- | ------------------------ |
| Node/TS | `npm run typecheck` or `bun run typecheck` | `npm run lint`               | `bun test` or `npm test` |
| Python  | `python -m mypy .`                         | `ruff check .`               | `pytest`                 |
| Go      | `go test ./...` (compile+test)             | `golangci-lint run`          | `go test ./...`          |
| Rust    | `cargo check`                              | `cargo fmt --check` (format) | `cargo test`             |

## Delegation Packet (Worker Input)

Every delegated task MUST include the following envelope:

- TASK: `<id> - <title>`
- EXPECTED OUTCOME: measurable end state
- REQUIRED TOOLS: e.g. `read`, `grep`, `lsp`, `bash`
- MUST DO: e.g. LSP-before-edits, run typecheck, run lint
- MUST NOT DO: e.g. no new deps, no dist/ edits, no git push
- ACCEPTANCE CHECKS: list of commands + pass criteria
- CONTEXT: links to `.beads/artifacts/<id>/spec.md` + relevant files

### Helper Tool

If available, use the custom tool `swarm-delegate` to generate (and optionally write) a delegation packet:

```ts
swarm -
  delegate({
    bead_id: "opencodekit-template-xyz",
    expected_outcome: "<measurable end state>",
    required_tools: "read, grep, lsp, bash",
    must_do: "LSP before edits, run project verification commands",
    must_not_do: "no new deps, don't edit dist/",
    acceptance_checks: "typecheck: <command>, lint: <command>, test: <command>",
    context: "See .beads/artifacts/<id>/spec.md",
    write: true,
  });
```

## Worker Report (Worker Output)

Workers MUST respond with a structured report:

- Result: done / blocked / needs replan
- Changes: file list + what changed (with file references)
- Verification: commands run + pass/fail summary
- Risks/Notes: edge cases, follow-ups
- Confidence: high / medium / low

## Gates (Non-Negotiable)

- Planning gate: `.beads/artifacts/<id>/spec.md` exists with acceptance criteria BEFORE implementation starts
- Execution gate: worker provides verification evidence BEFORE close
- Review gate (risk-based): verifier signs off in `review.md` BEFORE close

## Replan Triggers

Immediately stop execution and return to planning if:

- Scope expands to 4+ files unexpectedly
- Requirement ambiguity changes implementation choice
- Two-strike tool failures
- New dependency or `.opencode/` structure change would be needed

## Lead Checklist

1. `br ready` -> pick task -> `br show <id>`
2. Ensure `.beads/artifacts/<id>/spec.md` has acceptance checks
3. `br update <id> --status=in_progress`
4. Delegate with the packet format
5. Require worker report + evidence
6. `br close <id> --reason="..."` + `br sync --flush-only`
