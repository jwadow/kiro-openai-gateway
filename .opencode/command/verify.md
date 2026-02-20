---
description: Verify implementation completeness, correctness, and coherence
argument-hint: "<bead-id> [--quick] [--fix]"
agent: review
---

# Verify: $ARGUMENTS

Check implementation against PRD before shipping.

## Load Skills

```typescript
skill({ name: "beads" });
skill({ name: "verification-before-completion" });
```

## Parse Arguments

| Argument    | Default  | Description                      |
| ----------- | -------- | -------------------------------- |
| `<bead-id>` | required | The bead to verify               |
| `--quick`   | false    | Gates only, skip coherence check |
| `--fix`     | false    | Auto-fix lint/format issues      |

## Determine Input Type

| Input Type | Detection                   | Action                              |
| ---------- | --------------------------- | ----------------------------------- |
| Bead ID    | Matches `br-xxx` or numeric | Check implementation vs PRD in bead |
| Path       | File/directory path         | Verify that specific path           |
| `all`      | Keyword                     | Verify all in-progress work         |

## Before You Verify

- **Be certain**: Only flag issues you can verify with tools
- **Don't invent problems**: If an edge case isn't in the PRD, don't flag it
- **Run the gates**: Build, test, lint, typecheck are non-negotiable
- **Use project conventions**: Check `package.json` scripts first

## Phase 1: Gather Context

```bash
br show $ARGUMENTS
ls .beads/artifacts/$ARGUMENTS/
```

Read the PRD and any other artifacts (plan.md, research.md, design.md).

**Verify guards:**

- [ ] Bead is `in_progress`
- [ ] `prd.md` exists
- [ ] You have read the full PRD

## Phase 2: Completeness

Extract all requirements/tasks from the PRD and verify each is implemented:

- For each requirement: find evidence in the codebase (file:line reference)
- Mark as: complete, partial, or missing
- Report completeness score (X/Y requirements met)

## Phase 3: Correctness

Detect project type and run the appropriate verification gates:

| Project Type    | Detect Via                    | Build            | Test            | Lint                          | Typecheck                             |
| --------------- | ----------------------------- | ---------------- | --------------- | ----------------------------- | ------------------------------------- |
| Node/TypeScript | `package.json`                | `npm run build`  | `npm test`      | `npm run lint`                | `npm run typecheck` or `tsc --noEmit` |
| Rust            | `Cargo.toml`                  | `cargo build`    | `cargo test`    | `cargo clippy -- -D warnings` | (included in build)                   |
| Python          | `pyproject.toml` / `setup.py` | —                | `pytest`        | `ruff check .`                | `mypy .`                              |
| Go              | `go.mod`                      | `go build ./...` | `go test ./...` | `golangci-lint run`           | (included in build)                   |

Check `package.json` scripts, `Makefile`, or `justfile` for project-specific commands first — prefer those over generic defaults.

If `--fix` flag provided, run the project's auto-fix command (e.g., `npm run lint:fix`, `ruff check --fix`, `cargo clippy --fix`).

Report gate results (pass/warn/fail for each).

## Phase 4: Coherence (skip with --quick)

Cross-reference artifacts for contradictions:

- PRD vs implementation (does code address all PRD requirements?)
- Plan vs implementation (did code follow the plan?)
- Research recommendations vs actual approach (if different, is it justified?)

Flag contradictions with specific file references.

## Phase 5: Report

```bash
br comments add $ARGUMENTS "Verification: [PASS|PARTIAL|FAIL] - [summary]"
```

Output:

1. **Result**: READY TO SHIP / NEEDS WORK / BLOCKED
2. **Completeness**: score and status
3. **Correctness**: gate results
4. **Coherence**: contradictions found (if not --quick)
5. **Blocking issues** to fix before shipping
6. **Next step**: `/ship $ARGUMENTS` if ready, or list fixes needed

Record significant findings with `observation()`.

## Related Commands

| Need              | Command            |
| ----------------- | ------------------ |
| Ship after verify | `/ship <id>`       |
| Review code       | `/review-codebase` |
| Check status      | `/status`          |
