---
purpose: PARA-organized memory system with SQLite backing
updated: 2026-02-04
---

# Project Memory

Multi-layer memory system combining PARA organization with SQLite + FTS5 search.

## Directory Structure

```
memory/
├── project/           # Tacit knowledge (always-injected context)
│   ├── user.md        # User preferences, identity
│   ├── tech-stack.md  # Framework, dependencies, constraints
│   └── gotchas.md     # Footguns, edge cases, warnings
├── knowledge/         # PARA-organized reference (curated)
│   ├── projects/      # Active work with deadlines
│   ├── areas/         # Ongoing responsibilities
│   ├── resources/     # Reference material
│   └── archives/      # Completed/inactive items
├── daily/             # Chronological session logs
├── research/          # Deep-dive analysis documents
├── handoffs/          # Session handoff context
└── _templates/        # File templates
```

## Memory Layers (3-Layer Architecture)

| Layer               | Location      | Purpose                 | Access                             |
| ------------------- | ------------- | ----------------------- | ---------------------------------- |
| **Knowledge Graph** | SQLite + FTS5 | Searchable observations | `memory-search()`, `observation()` |
| **Daily Notes**     | `daily/`      | Chronological narrative | Manual review                      |
| **Tacit Knowledge** | `project/`    | Always-present context  | Auto-injected                      |

## SQLite Memory Tools

| Tool                | Purpose                                       |
| ------------------- | --------------------------------------------- |
| `observation()`     | Write structured observations to SQLite       |
| `memory-search()`   | FTS5 full-text search (returns compact index) |
| `memory-get()`      | Fetch full observation details by ID          |
| `memory-timeline()` | Get chronological context around anchor       |
| `memory-update()`   | Update markdown files in memory               |

## PARA Categories

- **Projects**: Active work with deadlines → `knowledge/projects/`
- **Areas**: Ongoing responsibilities → `knowledge/areas/`
- **Resources**: Reference material → `knowledge/resources/`
- **Archives**: Completed/inactive → `knowledge/archives/`

## Memory Tiers (Decay-based)

| Tier     | Access Pattern | Location                   |
| -------- | -------------- | -------------------------- |
| **Hot**  | Daily/Weekly   | Active SQLite + `project/` |
| **Warm** | Monthly        | `knowledge/` directories   |
| **Cold** | Rarely         | `knowledge/archives/`      |

## Workflow

### Session Start

1. `memory-search()` - Find relevant context
2. Read `project/` files (auto-injected)
3. Check `daily/` for recent sessions if needed

### During Work

1. Use `observation()` for decisions, patterns, gotchas
2. Update `project/gotchas.md` for footguns
3. Add to `knowledge/` for curated reference

### Session End

1. Summary appended to `daily/YYYY-MM-DD.md`
2. Sync beads: `br sync --flush-only`

## Philosophy

**Three-layer memory beats single-layer:**

- SQLite for searchability (Knowledge Graph)
- Daily notes for context (Chronological)
- Project files for presence (Tacit Knowledge)

Each layer serves a different retrieval pattern.
