---
name: ralph
description: Use when running autonomous agent loops for extended task completion without human intervention - handles PRD-driven development, migration tasks, or batch operations
license: MIT
compatibility: opencode
metadata:
  source: https://ghuntley.com/ralph/
  category: automation
  updated: 2026-01-10
---

# Ralph Wiggum - Autonomous Agent Loop

A workflow pattern for extended autonomous work sessions where the agent iterates through tasks until completion.

## When to Use

- **PRD-driven development**: Work through a product requirements document task by task
- **Migration tasks**: "Migrate all Jest tests to Vitest" - agent works until done
- **Batch operations**: Process multiple files/components with the same pattern
- **Away-from-keyboard work**: Let the agent work autonomously while you're away

## When NOT to Use

- Simple single-step tasks (just do them directly)
- Tasks requiring frequent human decisions
- Exploratory work where the goal isn't clear
- Critical production changes (requires human oversight)

## Quick Start

Invoke the workflow with:

```
/ralph Migrate all Jest tests to Vitest --prd PRD.md
```

Or manually follow the loop pattern below.

## The Loop Pattern

```
┌─────────────────────────────────────────────────┐
│  1. Read PRD/task list + progress.txt           │
│  2. Pick highest-priority incomplete task       │
│  3. Implement ONE feature only                  │
│  4. Run feedback: test → typecheck → lint       │
│  5. If pass → commit + update progress.txt      │
│  6. If all done → output <promise>COMPLETE      │
│  7. Otherwise → repeat from step 1              │
└─────────────────────────────────────────────────┘
```

## Using LSP Tools (Experimental)

OpenCode provides LSP tools for code intelligence.

### Available Operations

```typescript
// Understand file structure before editing
lsp({
  operation: "documentSymbol",
  filePath: "src/auth.ts",
  line: 1,
  character: 1,
});

// Find where a symbol is defined
lsp({
  operation: "goToDefinition",
  filePath: "src/auth.ts",
  line: 42,
  character: 10,
});

// Find all usages of a symbol (impact analysis)
lsp({
  operation: "findReferences",
  filePath: "src/auth.ts",
  line: 42,
  character: 10,
});

// Get type info and documentation
lsp({ operation: "hover", filePath: "src/auth.ts", line: 42, character: 10 });

// Find implementations of interface/abstract
lsp({
  operation: "goToImplementation",
  filePath: "src/types.ts",
  line: 15,
  character: 10,
});

// Search symbols across entire workspace
lsp({
  operation: "workspaceSymbol",
  filePath: "src/index.ts",
  line: 1,
  character: 1,
});

// Call hierarchy analysis
lsp({
  operation: "prepareCallHierarchy",
  filePath: "src/api.ts",
  line: 20,
  character: 5,
});
lsp({
  operation: "incomingCalls",
  filePath: "src/api.ts",
  line: 20,
  character: 5,
});
lsp({
  operation: "outgoingCalls",
  filePath: "src/api.ts",
  line: 20,
  character: 5,
});
```

### LSP-First Workflow

Before editing ANY file in the loop:

```
1. Read the file
2. Use documentSymbol to understand structure
3. Use findReferences to check impact
4. Use hover for type info
5. THEN make edits
```

This prevents breaking changes and ensures you understand the code before modifying it.

## Smart Language Detection

OpenCode auto-detects languages via LSP based on file extensions. Use this to determine the project type:

### Primary Detection (File Extensions)

| Language   | Extensions                    | LSP Server    |
| ---------- | ----------------------------- | ------------- |
| TypeScript | `.ts`, `.tsx`, `.mts`, `.cts` | typescript    |
| JavaScript | `.js`, `.jsx`, `.mjs`, `.cjs` | typescript    |
| Python     | `.py`, `.pyi`                 | pyright       |
| Rust       | `.rs`                         | rust-analyzer |
| Go         | `.go`                         | gopls         |
| C/C++      | `.c`, `.cpp`, `.h`, `.hpp`    | clangd        |
| Java       | `.java`                       | jdtls         |
| C#         | `.cs`                         | csharp        |
| Ruby       | `.rb`, `.rake`                | ruby-lsp      |
| PHP        | `.php`                        | intelephense  |
| Swift      | `.swift`                      | sourcekit-lsp |
| Kotlin     | `.kt`, `.kts`                 | kotlin-ls     |
| Elixir     | `.ex`, `.exs`                 | elixir-ls     |
| Dart       | `.dart`                       | dart          |
| Zig        | `.zig`                        | zls           |
| Gleam      | `.gleam`                      | gleam         |
| Lua        | `.lua`                        | lua-ls        |
| Clojure    | `.clj`, `.cljs`, `.cljc`      | clojure-lsp   |
| OCaml      | `.ml`, `.mli`                 | ocaml-lsp     |
| Svelte     | `.svelte`                     | svelte        |
| Vue        | `.vue`                        | vue           |
| Astro      | `.astro`                      | astro         |

### Secondary Detection (Lock Files → Package Manager)

| Lock File           | Package Manager | Runtime |
| ------------------- | --------------- | ------- |
| `bun.lockb`         | Bun             | Bun     |
| `yarn.lock`         | Yarn            | Node    |
| `pnpm-lock.yaml`    | pnpm            | Node    |
| `package-lock.json` | npm             | Node    |
| `deno.json`         | Deno            | Deno    |
| `Cargo.toml`        | Cargo           | Rust    |
| `go.mod`            | Go Modules      | Go      |
| `pyproject.toml`    | Poetry/pip      | Python  |
| `Gemfile.lock`      | Bundler         | Ruby    |
| `composer.lock`     | Composer        | PHP     |
| `Package.swift`     | SwiftPM         | Swift   |
| `mix.lock`          | Mix             | Elixir  |
| `pubspec.lock`      | Pub             | Dart    |

### Validation Commands by Language

```bash
# TypeScript/JavaScript (Bun)
bun test && bun run typecheck && bun run lint

# TypeScript/JavaScript (npm)
npm test && npm run typecheck && npm run lint

# TypeScript/JavaScript (Deno)
deno test && deno check . && deno lint

# Python
pytest && ruff check . && mypy .

# Rust
cargo test && cargo check && cargo clippy --all-targets

# Go
go test ./... && go vet ./... && golangci-lint run

# Ruby
bundle exec rspec && bundle exec rubocop

# PHP
composer test && composer phpstan && composer phpcs

# Swift
swift test && swift build

# Elixir
mix test && mix credo && mix dialyzer

# Dart
dart test && dart analyze

# Java (Maven)
mvn test && mvn compile && mvn checkstyle:check

# Java (Gradle)
./gradlew test && ./gradlew check

# C# (.NET)
dotnet test && dotnet build && dotnet format --verify-no-changes
```

## Required Files

### PRD File (Recommended)

Create a `PRD.md` with clear task list:

```markdown
# Migration PRD

## Tasks

- [ ] Convert test-utils.test.js
- [ ] Convert api.test.js
- [ ] Update CI config
- [ ] Remove Jest dependencies
```

### Progress File (Agent-maintained)

Agent creates/updates `progress.txt`:

```markdown
# Progress Log

## Session Started: 2026-01-10

### Project: TypeScript with Bun

### Commands: bun test | bun run typecheck | bun run lint

### Completed Tasks

- [x] test-utils.test.js - migrated, 12 tests passing
- [x] api.test.js - migrated, 8 tests passing

### Notes for Next Iteration

- CI config needs Vitest runner update
```

## Completion Signal

The loop ends when agent outputs:

```
<promise>COMPLETE</promise>
```

## Best Practices

1. **Use LSP for detection**: Check file extensions, not just lock files
2. **Small steps**: ONE feature per iteration (prevents context rot)
3. **Quality gates**: Test, typecheck, lint MUST pass before commit
4. **Prioritize risk**: Hard tasks first, easy wins last
5. **Track progress**: Update progress.txt every iteration
6. **Explicit scope**: Vague tasks loop forever
7. **Graceful fallbacks**: If a command doesn't exist, skip and note it

## Troubleshooting

| Issue                | Solution                                    |
| -------------------- | ------------------------------------------- |
| Loop not progressing | Break task into smaller pieces              |
| Tests failing        | Fix before continuing, don't skip           |
| Context getting long | Summarize progress, restart session         |
| Stuck on decision    | Note in progress.txt, ask user next session |
| Unknown language     | Check file extensions against LSP table     |
