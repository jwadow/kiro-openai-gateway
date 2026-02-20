---
name: session-management
description: Use when context is growing large, switching tasks, or needing previous session context - covers thresholds, session tools, and workflow patterns
---

# Session Management

**Philosophy**: Short sessions (<150k tokens) beat long bloated ones. Agents get worse with too much context. Cost is exponential.

## Context Thresholds

The environment monitors context usage and warns at these thresholds:

| Threshold | Action                                                     |
| --------- | ---------------------------------------------------------- |
| **70%**   | Consolidate work; consider pruning irrelevant tool outputs |
| **85%**   | Summarize findings and consider starting a new session     |
| **95%**   | Critical: prune context immediately or restart session     |

## Session Tools

### list_sessions

Discover available sessions before reading:

```typescript
list_sessions({ limit: 10, project: "current" }); // Current project
list_sessions({ since: "today" }); // Today's sessions
list_sessions({ project: "all", since: "yesterday" }); // Cross-project
```

### read_session

Pull context from previous session:

```typescript
read_session("last"); // Most recent
read_session("2 ago", { project: "current" }); // 2nd most recent
read_session("today"); // Today's first session
read_session("ses_abc123", { focus: "file changes" }); // Specific aspect
```

### search_session

Full-text search across sessions:

```typescript
search_session({ query: "auth bug" }); // Search all sessions
search_session({ query: "OAuth", session_id: "ses_abc" }); // Specific session
search_session({ query: "error", limit: 10 }); // Limit results
```

Use to find past discussions, decisions, or work on a topic before starting new work.

### summarize_session

Generate AI summary of a session:

```typescript
summarize_session("ses_abc123"); // Trigger AI summarization
```

Use before `read_session` to get a quick overview of what happened in a past session without loading full context.

## When to Start New Session

- Completing distinct task from `br ready`
- Token usage approaching 150k
- Switching phases (implementation → review → testing)
- After handoff (`/handoff <bead-id>`)

## Session Workflow Pattern

```
Session 1: Implement feature X (80k tokens)
  ↓ close, update memory
Session 2: list_sessions() → read_session("last") → Refactor (60k tokens)
  ↓
Session 3: read_session("previous") → Add tests (90k tokens)
  ↓
Session 4: read_session refs → Final review (100k tokens)
```

**Result**: 4 fresh contexts vs 1 degraded 330k context. Better performance, lower cost.

## Context Transfer

Use all available sources:

1. `read_session("last")` - Previous session work
2. Git state - `git diff`, `git log` - Code changes
3. Memory files - `.opencode/memory/*` - Persistent context
4. Beads - `br show <id>` - Task specs

**Don't**: Carry everything forward. Extract what's needed, discard the rest.

## Pruning Strategy

When context grows large:

1. **Discard** completed task outputs (read files you won't edit again)
2. **Extract** key findings before discarding research
3. **Summarize** complex investigations into memory files
4. **Restart** session if above 85% and work is at a natural break

## Anti-Patterns

- ❌ Running until context limit forces restart
- ❌ Carrying all previous reads forward "just in case"
- ❌ Not using memory files for cross-session persistence
- ❌ Re-reading the same files every session instead of extracting key info
