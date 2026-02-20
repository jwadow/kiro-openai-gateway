---
name: tool-priority
description: Use when choosing between tools or need tool reference - covers LSP, search, swarm, memory, and research tools with correct syntax
---

# Tool Priority Skill

## Priority Order

**LSP → Search → Swarm → Memory → File Operations**

1. **LSP** - Semantic code intelligence (9 operations via unified tool)
2. **grep** - Fast text search (logs, config, code patterns)
3. **glob** - File discovery by name pattern
4. **skill** - Load skills for specialized knowledge
5. **task** - Parallel subagent execution
6. **Swarm tool** - swarm (plan, monitor, delegate, sync operations)
7. **Memory tools** - memory-search, memory-read, memory-update, memory-admin
8. **Research tools** - context7, websearch, codesearch, grepsearch
9. **read/edit/write** - File operations (always read before edit)

**Golden Rule**: Always `read` before `edit` to verify content.

## Choosing the Right Tool

Ask: **"Am I looking for semantic understanding or just text?"**

### Code Understanding (Use LSP)

The `lsp` tool provides 9 operations via a unified interface:

| Need                 | Operation              | Example                                                                                                       |
| -------------------- | ---------------------- | ------------------------------------------------------------------------------------------------------------- |
| Type info at cursor  | `hover`                | `lsp({ operation: "hover", filePath: "src/file.ts", line: 42, character: 10 })`                               |
| Jump to definition   | `goToDefinition`       | `lsp({ operation: "goToDefinition", filePath: "src/file.ts", line: 42, character: 10 })`                      |
| Find all usages      | `findReferences`       | `lsp({ operation: "findReferences", filePath: "src/file.ts", line: 42, character: 10 })`                      |
| File structure       | `documentSymbol`       | `lsp({ operation: "documentSymbol", filePath: "src/file.ts", line: 1, character: 1 })`                        |
| Workspace search     | `workspaceSymbol`      | `lsp({ operation: "workspaceSymbol", filePath: "src/file.ts", line: 1, character: 1, query: "UserService" })` |
| Find implementations | `goToImplementation`   | `lsp({ operation: "goToImplementation", filePath: "src/file.ts", line: 42, character: 10 })`                  |
| Call hierarchy       | `prepareCallHierarchy` | `lsp({ operation: "prepareCallHierarchy", filePath: "src/file.ts", line: 42, character: 10 })`                |
| Incoming calls       | `incomingCalls`        | `lsp({ operation: "incomingCalls", filePath: "src/file.ts", line: 42, character: 10 })`                       |
| Outgoing calls       | `outgoingCalls`        | `lsp({ operation: "outgoingCalls", filePath: "src/file.ts", line: 42, character: 10 })`                       |

**Critical**: Run ALL 9 LSP operations before editing. See AGENTS.md for the full checklist.

### Text Search (Use grep)

| Need              | Pattern          | Example                                    |
| ----------------- | ---------------- | ------------------------------------------ |
| Function calls    | `functionName\(` | `grep({ pattern: "fetchUser\(" })`         |
| Import statements | `import.*from`   | `grep({ pattern: "import.*from.*react" })` |
| Error messages    | `FATAL\|ERROR`   | `grep({ pattern: "ERROR\|FATAL" })`        |
| TODO comments     | `TODO\|FIXME`    | `grep({ pattern: "TODO\|FIXME" })`         |
| Hook usage        | `useState\(`     | `grep({ pattern: "useState\(" })`          |
| Debug logs        | `console\.log`   | `grep({ pattern: "console\.log" })`        |

### Load Skills (Use skill tool)

Load specialized knowledge before starting work:

```typescript
// Essential skills for most work
skill({ name: "verification-before-completion" });
skill({ name: "test-driven-development" });

// Domain-specific skills
skill({ name: "beads" }); // Task tracking
skill({ name: "beads-bridge" }); // Swarm coordination
skill({ name: "swarm-coordination" }); // Parallel execution
skill({ name: "frontend-design" }); // UI implementation
skill({ name: "prd" }); // Requirements documents
```

### Parallel Execution (Use Task tool)

Launch multiple subagents simultaneously:

```typescript
// Workers run in parallel when multiple Task calls in one message
Task({
  subagent_type: "explore",
  description: "Find patterns",
  prompt: `Find auth patterns in codebase...`,
});

Task({
  subagent_type: "scout",
  description: "Research docs",
  prompt: `Research best practices for...`,
});
// Results return when both complete
```

**Subagent types**: `general`, `explore`, `scout`, `review`, `plan`

### Swarm Coordination Tools

| Tool      | Purpose                    | Key Operations                        |
| --------- | -------------------------- | ------------------------------------- |
| **swarm** | Unified swarm coordination | `plan`, `monitor`, `delegate`, `sync` |

**swarm operations:**

- `plan`: Task analysis (actions: analyze, classify, check, allocate)
- `monitor`: Progress tracking (actions: progress_update, render_block, status, clear)
- `delegate`: Create delegation packets for workers
- `sync`: Beads ↔ OpenCode sync (actions: push, pull, create_shared, update_shared)

### Memory Tools

| Tool              | Purpose                   | When to Use                         |
| ----------------- | ------------------------- | ----------------------------------- |
| **memory-search** | Find past learnings       | "Have we solved this before?"       |
| **memory-read**   | Load specific memory file | "What did we decide about X?"       |
| **memory-update** | Save context              | "Document this for future sessions" |
| **observation**   | Record decisions/patterns | "This is worth remembering"         |

### Research Tools

| Tool              | Purpose                      | When to Use             |
| ----------------- | ---------------------------- | ----------------------- |
| **context7**      | Library documentation lookup | API reference, examples |
| **websearch**     | Recent info, troubleshooting | Docs not in Context7    |
| **codesearch**    | Real implementation patterns | GitHub code examples    |
| **grepsearch**    | Cross-repo patterns          | grep.app search         |
| **webfetch**      | Specific URL content         | User-provided links     |
| **review (Task)** | Second opinion               | Validate approach       |

**context7 operations:**

- `resolve`: Find library ID from name (e.g., "react" → "/reactjs/react.dev")
- `query`: Get documentation for a library topic

## Workflow Pattern

```typescript
// Step 1: Load skills
skill({ name: "verification-before-completion" });
skill({ name: "beads" });

// Step 2: Find it (text search)
grep({ pattern: "functionName", path: "src/" });

// Step 3: Understand it (LSP - ALL 9 operations)
lsp({ operation: "documentSymbol", filePath: "src/file.ts", line: 1, character: 1 });
lsp({ operation: "goToDefinition", filePath: "src/file.ts", line: 42, character: 10 });
lsp({ operation: "findReferences", filePath: "src/file.ts", line: 42, character: 10 });
lsp({ operation: "hover", filePath: "src/file.ts", line: 42, character: 10 });
// ... remaining 5 operations

// Step 4: Check memory
memory_search({ query: "auth patterns" });

// Step 5: Read before edit
read({ filePath: "/absolute/path/to/file.ts" });

// Step 6: Modify
edit({ filePath: "/absolute/path/to/file.ts", oldString: "...", newString: "..." });

// Step 7: Verify
bash({ command: "npm run typecheck && npm run lint" });
```

## Tool Comparison

### grep vs LSP

| Scenario           | Use                         | Why                                         |
| ------------------ | --------------------------- | ------------------------------------------- |
| "Find all X"       | `grep`                      | Fast text search, includes comments/strings |
| "Where is X used?" | `lsp` with `findReferences` | Semantic, tracks actual code dependencies   |
| "What type is X?"  | `lsp` with `hover`          | Type system intelligence                    |
| "Find TODOs"       | `grep`                      | Text search across all files                |

### When to Use What

**Start with LSP when:**

- Understanding code structure
- Before any edit (ALL 9 operations)
- Tracing dependencies
- Getting type information

**Start with grep when:**

- Quick exploration ("are there any X?")
- Finding error patterns, logs, configs
- Searching across file types (JSON, YAML, etc.)

**Use skill when:**

- Starting any significant work
- Need specialized knowledge
- Following established patterns

**Use Task when:**

- Multiple independent research questions
- Parallel implementation tasks
- 3+ files need simultaneous work

## Common Mistakes

❌ **Wrong**: Edit without LSP

```typescript
// DON'T: Edit without understanding structure
edit({ filePath: "src/file.ts", oldString: "...", newString: "..." });
```

✅ **Right**: LSP before edit

```typescript
// DO: Run all 9 LSP operations first
lsp({ operation: "documentSymbol", filePath: "src/file.ts", line: 1, character: 1 });
lsp({ operation: "goToDefinition", filePath: "src/file.ts", line: 10, character: 5 });
// ... 7 more operations
read({ filePath: "src/file.ts" });
edit({ filePath: "src/file.ts", oldString: "...", newString: "..." });
```

❌ **Wrong**: Old LSP syntax

```typescript
// DON'T: This syntax doesn't exist
lsp_lsp_hover((filePath = "src/file.ts"), (line = 42), (character = 10));
```

✅ **Right**: Correct LSP syntax

```typescript
// DO: Use operation parameter
lsp({ operation: "hover", filePath: "src/file.ts", line: 42, character: 10 });
```

## Quick Reference

```
BEFORE EDITING:
  lsp({ operation: "documentSymbol", ... })     → File structure
  lsp({ operation: "goToDefinition", ... })     → Where defined
  lsp({ operation: "findReferences", ... })     → All usages
  lsp({ operation: "hover", ... })              → Type info
  lsp({ operation: "goToImplementation", ... }) → Implementations
  lsp({ operation: "prepareCallHierarchy", ... }) → Call hierarchy
  lsp({ operation: "incomingCalls", ... })      → What calls this
  lsp({ operation: "outgoingCalls", ... })      → What this calls
  lsp({ operation: "workspaceSymbol", ... })    → Workspace search

SEARCHING:
  grep({ pattern: "...", path: "src/" })        → Text search
  glob({ pattern: "**/*.ts" })                  → File discovery

PARALLEL WORK:
  Task({ subagent_type: "explore", ... })       → Parallel subagent
  swarm({ operation: "sync", action: "push" }) → Sync to todos
  swarm({ operation: "monitor", action: "progress_update" }) → Track progress

RESEARCH:
  context7({ operation: "resolve", libraryName: "..." })
  context7({ operation: "query", libraryId: "...", topic: "..." })
  websearch({ query: "..." })
  Task({ subagent_type: "review", description: "Second opinion", prompt: "Review the approach." })

MEMORY:
  memory_search({ query: "..." })               → Find past learnings
  observation({ type: "learning", ... })        → Record for future
```
