---
description: Create and submit pull request with bead traceability
argument-hint: "[bead-id] [--draft]"
agent: build
---

# Pull Request

## Load Skills

```typescript
skill({ name: "beads" });
skill({ name: "verification-before-completion" });
```

## Parse Arguments

| Argument    | Default  | Description        |
| ----------- | -------- | ------------------ |
| `<bead-id>` | optional | Link PR to bead    |
| `--draft`   | false    | Create as draft PR |

## Phase 1: Pre-PR Verification

```bash
git status --porcelain
```

If uncommitted changes exist, ask whether to commit first.

Run verification gates. Detect project type and use the appropriate commands:

| Project Type    | Detect Via                    | Build            | Test            | Lint                          | Typecheck                             |
| --------------- | ----------------------------- | ---------------- | --------------- | ----------------------------- | ------------------------------------- |
| Node/TypeScript | `package.json`                | `npm run build`  | `npm test`      | `npm run lint`                | `npm run typecheck` or `tsc --noEmit` |
| Rust            | `Cargo.toml`                  | `cargo build`    | `cargo test`    | `cargo clippy -- -D warnings` | (included in build)                   |
| Python          | `pyproject.toml` / `setup.py` | —                | `pytest`        | `ruff check .`                | `mypy .`                              |
| Go              | `go.mod`                      | `go build ./...` | `go test ./...` | `golangci-lint run`           | (included in build)                   |

Check `package.json` scripts, `Makefile`, or `justfile` for project-specific commands first — prefer those over generic defaults.

If any gate fails, stop. Fix errors first, then run `/pr` again.

## Phase 2: Gather Context

```bash
git branch --show-current
git log main...HEAD --oneline
git diff main...HEAD --stat
```

If bead ID provided:

```bash
br show $ARGUMENTS
ls .beads/artifacts/$ARGUMENTS/
```

Read the PRD to extract goal and success criteria for the PR description.

## Phase 3: Push and Confirm

Show what will be pushed and ask the user:

```typescript
question({
  questions: [
    {
      header: "Push",
      question: "Ready to push and create PR. Proceed?",
      options: [
        { label: "Push & create PR (Recommended)", description: "Push branch and create PR" },
        { label: "Push & draft PR", description: "Create as draft for review" },
        { label: "Show diff first", description: "Review changes before pushing" },
      ],
    },
  ],
});
```

If confirmed:

```bash
git push -u origin $(git branch --show-current)
```

## Phase 4: Create PR

```bash
gh pr create --title "<title>" --body "$(cat <<'EOF'
## Summary

[1-2 sentences: what this PR does and why]

## Changes

- `file.ts`: [what changed]
- `other.ts`: [what changed]

## Testing

- All tests pass
- Lint and typecheck pass
- Manual verification: [how to test]

## Checklist

- [x] Tests added/updated
- [x] All gates pass
- [ ] Docs updated (if applicable)
EOF
)"
```

If `--draft`, add `--draft` flag.

If bead ID provided, add artifacts section linking to `.beads/artifacts/$ARGUMENTS/prd.md`.

## Output

Report:

1. PR URL
2. Status (Ready for Review / Draft)
3. Branch → main
4. Gate results

## Related Commands

| Need         | Command        |
| ------------ | -------------- |
| Ship first   | `/ship <id>`   |
| Verify first | `/verify <id>` |
