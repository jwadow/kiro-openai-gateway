---
name: context-engineering
description: Use when designing AGENTS.md hierarchies, understanding autonomous duration, or writing intent layers - covers principles for extending agent work capacity
---

# Context Engineering

Principles for maximizing agent effectiveness through context design.

**For practical context tools (prune/distill/compress), use `context-management` skill.**

## Core Principle

**Autonomous Duration**: How long can an agent work before losing the plot?

Extend it by:

- Binding tighter to intent (clear specs, constraints, invariants)
- Providing systematic context (AGENTS.md hierarchy, memory files)
- Verification loops (test → iterate → verify)

## Three Context Constraints

1. **Blind spots cause hallucinations** - Agent fills gaps with generic priors
2. **Everything influences everything** - Noise degrades ALL output quality
3. **Window is finite** - Performance degrades BEFORE hard token limits

## Intent Layer Principles

### What Belongs in Each AGENTS.md

- **Purpose & Scope** - What this area does. What it DOESN'T do.
- **Entry Points & Contracts** - Main APIs, invariants
- **Usage Patterns** - Canonical examples
- **Anti-patterns** - What NOT to do
- **Dependencies & Downlinks** - Pointers to related context

### Key Mechanics

| Principle                | Meaning                                                  |
| ------------------------ | -------------------------------------------------------- |
| **Hierarchical loading** | When node loads, all ancestors load too (T-shaped view)  |
| **Compression**          | Good nodes compress code; don't add bloat                |
| **LCA placement**        | Place shared knowledge at shallowest node covering paths |
| **Downlinks**            | Point to related context without loading everything      |

## Practical Implications

| Instead of              | Do This                                 |
| ----------------------- | --------------------------------------- |
| Reading entire files    | Use `lsp documentSymbol` for outline    |
| Loading whole documents | Read specific line ranges               |
| Flat file loading       | Navigate AGENTS.md hierarchy            |
| Keeping completed work  | Prune aggressively (context-management) |

## Anti-Patterns

❌ Loading "everything that might be relevant"
❌ Keeping old file reads after editing complete
❌ Reading entire files when you only need a function
❌ Ignoring AGENTS.md hierarchy
