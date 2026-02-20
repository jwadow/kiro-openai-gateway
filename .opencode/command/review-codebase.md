---
description: Review code for quality, security, and compliance
argument-hint: "[path|bead-id|pr-number|'all'] [--quick|--thorough]"
agent: review
---

# Review: $ARGUMENTS

## Load Skills

```typescript
skill({ name: "beads" });
skill({ name: "requesting-code-review" });
```

## Determine Input Type

| Input Type            | Detection                    | Action                     |
| --------------------- | ---------------------------- | -------------------------- |
| No arguments          | Default                      | Review uncommitted changes |
| Commit hash (40-char) | SHA pattern                  | `git show <hash>`          |
| Branch name           | String, not matching above   | `git diff main...HEAD`     |
| PR URL/number         | Contains "github.com" or "#" | `gh pr diff`               |

## Before You Review

- **Be certain**: Only flag issues you can verify with tools
- **Don't invent problems**: If an edge case isn't specified, don't flag it
- **Don't be a zealot about style**: Unless it violates project conventions, don't flag
- **Review the changes**: Don't review pre-existing code that wasn't modified
- **Investigate first**: If unsure, use explore/scout agents before flagging

## Available Tools

| Tool         | Use When                                |
| ------------ | --------------------------------------- |
| `explore`    | Finding patterns in codebase, prior art |
| `scout`      | External research, best practices       |
| `lsp`        | Finding symbol definitions, references  |
| `grep`       | Finding code patterns                   |
| `codesearch` | Real-world usage examples               |

## Phase 1: Gather Context

```bash
git status --short
git diff --cached  # staged
git diff           # unstaged
```

For each changed file:

- Read the full file to understand context
- Don't rely on diff alone — code that looks wrong in isolation may be correct

If bead provided, read `.beads/artifacts/$ID/prd.md` to review against spec.

## Phase 2: Determine Scope

| Input                    | Scope                 | How to Get Code           |
| ------------------------ | --------------------- | ------------------------- |
| File/directory path      | That path only        | `read` or `glob` + `read` |
| Bead ID (e.g., `br-123`) | Implementation vs PRD | `br show` then `git diff` |
| PR number (e.g., `#45`)  | PR changes            | `gh pr diff 45`           |
| `all` or empty           | Recent changes        | `git diff main...HEAD`    |

If bead provided, read `.beads/artifacts/$ID/prd.md` to review against spec.

## Phase 2: Automated Checks

Detect project type and run the appropriate checks in parallel:

| Project Type    | Detect Via                    | Build            | Test            | Lint                          | Typecheck                             |
| --------------- | ----------------------------- | ---------------- | --------------- | ----------------------------- | ------------------------------------- |
| Node/TypeScript | `package.json`                | `npm run build`  | `npm test`      | `npm run lint`                | `npm run typecheck` or `tsc --noEmit` |
| Rust            | `Cargo.toml`                  | `cargo build`    | `cargo test`    | `cargo clippy -- -D warnings` | (included in build)                   |
| Python          | `pyproject.toml` / `setup.py` | —                | `pytest`        | `ruff check .`                | `mypy .`                              |
| Go              | `go.mod`                      | `go build ./...` | `go test ./...` | `golangci-lint run`           | (included in build)                   |

Check `package.json` scripts, `Makefile`, or `justfile` for project-specific commands first — prefer those over generic defaults.

Also scan for common issues appropriate to the detected language:

- Debug statements (`console.log`, `print()`, `println!`, `fmt.Println`)
- Loose typing (`any` in TypeScript, `type: ignore` in Python)
- `TODO|FIXME|HACK` markers
- Hardcoded secrets patterns

## Phase 3: Manual Review

Review each category:

| Category            | Focus                                                                   |
| ------------------- | ----------------------------------------------------------------------- |
| **Security**        | Auth checks, input validation, no secrets in code, injection prevention |
| **Performance**     | N+1 queries, unbounded loops, missing pagination, hot path ops          |
| **Maintainability** | Complexity, DRY violations, dead code, naming clarity                   |
| **Error Handling**  | Async error handling, error context, sanitized user errors              |
| **Testing**         | Coverage on changed code, behavior tests, edge cases                    |
| **Type Safety**     | No unjustified `any`, null handling, explicit return types              |

**Depth levels:**

- `--quick`: Automated checks + skim, critical issues only
- Default: Full automated + manual review
- `--thorough`: Deep analysis of all categories

## Phase 4: Report

Group findings by severity:

- **Critical** (must fix before merge): with file:line, issue, fix
- **Important** (should fix): with file:line, issue, fix
- **Minor** (nice to have): with file:line, suggestion

Include:

1. Summary metrics (files reviewed, issues by severity)
2. Strengths (what's done well, with file:line)
3. Verdict: Ready to merge / With fixes / No
4. Reasoning (1-2 sentences)

Record significant findings with `observation()`.

## Related Commands

| Need                | Command        |
| ------------------- | -------------- |
| Ship after review   | `/ship <id>`   |
| Verify completeness | `/verify <id>` |
| Check status        | `/status`      |
