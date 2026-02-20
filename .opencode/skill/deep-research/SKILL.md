---
name: deep-research
description: >
  Use when analyzing unfamiliar code, implementing complex features, or entering thorough research mode.
  Provides structured LSP exploration (all 9 operations), memory-first protocol, and confidence-scored findings.
  Integrates with scout agent deep mode and research command --thorough flag.
version: "1.0.0"
license: MIT
---

# Deep Research - Comprehensive Code Understanding

Systematic methodology for thorough codebase exploration before implementation.

## When to Use This Skill

Use deep research when:

- **Complex implementation**: Feature touches 3+ files or unfamiliar modules
- **Thorough mode**: `/research <topic> --thorough` or scout deep mode
- **Pre-edit understanding**: Before modifying code you don't fully understand
- **Architecture exploration**: Understanding how systems connect
- **Debugging**: Tracing behavior through multiple layers

**Don't use when:**

- Quick syntax lookup (use quick mode instead)
- Well-understood code with obvious changes
- Time-constrained fixes (accept lower confidence)

## Core Protocol

### Phase 1: Memory First (Skip External If Found)

```typescript
// Search past research on this topic
memory_search({ query: "<topic keywords>", limit: 5 });

// Check for related observations
memory_search({ query: "<topic> gotchas patterns", limit: 3 });

// Load relevant project context
memory_read({ file: "project/architecture" });
memory_read({ file: "project/gotchas" });
```

**Stop condition**: If memory returns high-confidence findings on this exact topic, synthesize and skip to documentation. Only proceed to exploration if:

- No relevant memory found
- Memory findings are outdated or incomplete
- Question requires fresh analysis

### Phase 2: LSP Exploration (Delegate to Explore Agent)

**Delegate to explore agent** for comprehensive LSP analysis instead of manual operations:

```typescript
task({
  subagent_type: "explore",
  description: "LSP analysis of <target>",
  prompt: `Very thorough LSP analysis of <symbol/module>.

Target files:
- src/path/to/file.ts
- src/related/module.ts

Questions to answer:
1. What is the type signature of <symbol>?
2. What calls this function? (incoming calls)
3. What does this function call? (outgoing calls)
4. Where is this symbol referenced across the codebase?
5. Are there interface implementations to consider?

Return structured findings with file:line references.`,
});
```

The explore agent will run:

- `documentSymbol` - File structure overview
- `goToDefinition` - Symbol definitions
- `findReferences` - All usages across codebase
- `hover` - Type info and documentation
- `workspaceSymbol` - Workspace-wide search
- Call hierarchy (incoming/outgoing calls)

**When to run LSP manually instead:**

- Single symbol lookup (quick mode)
- Explore agent unavailable
- Need specific operation only

### Phase 3: Pattern Discovery

```typescript
// Find similar patterns in codebase
grep({ pattern: "<relevant pattern>", include: "*.ts" });

// Locate related files
glob({ pattern: "src/**/*<topic>*" });

// Check tests for usage examples
glob({ pattern: "**/*.test.ts" });
grep({ pattern: "<function name>", include: "*.test.ts" });
```

### Phase 4: External Research (If Needed)

Only if internal exploration doesn't answer the question:

```typescript
// Official docs
context7({ operation: "resolve", libraryName: "<lib>" });
context7({ operation: "query", libraryId: "<id>", topic: "<specific question>" });

// Real-world patterns
codesearch({ query: "<API usage pattern>", tokensNum: 5000 });
grepsearch({ query: "<code pattern>", language: "TypeScript" });
```

## Confidence Levels

Score every finding:

| Level      | Criteria                                   | Action               |
| ---------- | ------------------------------------------ | -------------------- |
| **High**   | LSP confirmed + tests exist + docs match   | Proceed confidently  |
| **Medium** | LSP confirmed but untested or undocumented | Proceed with caution |
| **Low**    | Inference only, no LSP/test confirmation   | Verify before using  |
| **None**   | Speculation without evidence               | Discard              |

## Stop Conditions

Stop research when ANY of these are true:

- All questions answered with Medium+ confidence
- Tool budget exhausted (~100 calls for thorough)
- Last 5 tool calls yielded no new insights
- Blocked and need human input

## Tool Budget Guidelines

| Mode     | Tool Calls | Use Case                           |
| -------- | ---------- | ---------------------------------- |
| Quick    | ~10        | Single question, syntax lookup     |
| Default  | ~30        | Moderate exploration               |
| Thorough | ~100+      | Comprehensive analysis, new domain |

Track your tool count and stop at budget.

## Output Template

Document findings in structured format:

```markdown
# Deep Research: [Topic]

**Mode:** thorough
**Tool calls:** [N]
**Duration:** [time]

## Questions Addressed

1. [Q1] → Answered (High confidence)
2. [Q2] → Partial (Medium confidence)
3. [Q3] → Unanswered (needs: [what would resolve])

## LSP Findings

### Symbol: [name]

**Location:** `src/path/file.ts:42`
**Type:** [type signature from hover]

**Callers (incoming):**

- `src/a.ts:10` - [context]
- `src/b.ts:25` - [context]

**Dependencies (outgoing):**

- `src/utils.ts:15` - [what it calls]

**References:** [N] usages across [M] files

---

## Pattern Analysis

### Pattern 1: [Name]

**Files:** `src/a.ts`, `src/b.ts`
**Confidence:** High
**Evidence:** [LSP + grep findings]

[Description of pattern]

---

## Key Findings

### [Finding 1]

**Confidence:** High
**Sources:** LSP goToDefinition, findReferences
**Evidence:** `src/file.ts:42-56`

[Finding with code evidence]

---

## Recommendations

Based on LSP analysis:

1. [Recommendation 1] - because [LSP evidence]
2. [Recommendation 2] - because [pattern found]

## Open Items

- [Remaining question] - needs: [specific tool/info]
```

## Integration Points

### Scout Agent Deep Mode

When scout enters deep mode, load this skill:

```typescript
skill({ name: "deep-research" });
```

Scout then follows the protocol for external + internal analysis.

### Research Command --thorough

When `/research <topic> --thorough` is invoked:

```typescript
skill({ name: "deep-research" });
// Follow full protocol with ~100 tool budget
```

### Pre-Edit Verification

Before any complex edit:

```typescript
skill({ name: "deep-research" });
// Run Phase 2 (LSP) on all symbols being modified
// Proceed only when all 9 operations complete
```

## Workflow Example

**Scenario:** Understanding authentication middleware before adding rate limiting.

```typescript
// Phase 1: Memory check
memory_search({ query: "authentication middleware rate limiting" });
memory_read({ file: "project/architecture" });

// Phase 2: Delegate LSP exploration to explore agent
task({
  subagent_type: "explore",
  description: "Analyze auth middleware",
  prompt: `Very thorough LSP analysis of authentication middleware.

Target: src/middleware/auth.ts

Questions:
1. What functions are exported from auth.ts?
2. What calls the auth middleware? (incoming calls)
3. What does it depend on? (outgoing calls)
4. Are there existing rate limiting patterns?

Return file:line references for all findings.`,
});

// Phase 3: Pattern discovery (parallel with Phase 2)
grep({ pattern: "middleware", include: "*.ts" });
grep({ pattern: "rateLimit", include: "*.ts" });
glob({ pattern: "src/middleware/*.ts" });

// Phase 4: External (if patterns unclear)
context7({ operation: "resolve", libraryName: "express" });
context7({ operation: "query", libraryId: "/expressjs/express", topic: "middleware" });

// Document findings
write({
  filePath: ".beads/artifacts/<id>/research.md",
  content: "# Deep Research: Auth Middleware...",
});
```

## Anti-Patterns

### DON'T: Skip LSP Exploration

```typescript
// Bad: Reading file without LSP analysis
read({ filePath: "src/auth.ts" });
// Then immediately editing...

// Good: Delegate to explore agent first
task({
  subagent_type: "explore",
  description: "Analyze auth.ts",
  prompt: "Very thorough LSP analysis of src/auth.ts...",
});
// Then edit with understanding
```

### DON'T: Ignore Memory

```typescript
// Bad: Jumping straight to exploration
grep({ pattern: "auth", include: "*.ts" });

// Good: Check memory first
memory_search({ query: "authentication patterns" });
// Only explore if memory doesn't answer
```

### DON'T: Mix Confidence Levels

```typescript
// Bad: Treating speculation as fact
"This function definitely handles X"; // Without LSP verification

// Good: Explicit confidence
"Based on LSP findReferences (High confidence): This function is called from...";
"Inference (Low confidence): This might also handle X, needs verification";
```

### DON'T: Exceed Budget Without Stopping

```typescript
// Bad: 150 tool calls on thorough mode
// Keep going indefinitely...

// Good: Track and stop
// Tool call 95: Still finding new insights, continue
// Tool call 100: Stopping at budget, documenting partial findings
```

## Success Criteria

Research is complete when:

- [ ] Memory checked before exploration
- [ ] All 9 LSP operations run on target symbols
- [ ] Confidence scores assigned to all findings
- [ ] Tool budget respected
- [ ] Findings documented with evidence
- [ ] Open items listed with resolution paths

## Quick Reference

```
PROTOCOL:
1. Memory first → skip if found
2. Delegate LSP to @explore (very thorough)
3. Patterns → grep + glob (parallel)
4. External → only if needed

DELEGATION:
task({ subagent_type: "explore", prompt: "Very thorough LSP analysis..." })

CONFIDENCE:
High = LSP + tests + docs
Medium = LSP only
Low = inference
None = discard

BUDGET:
quick ~10 | default ~30 | thorough ~100

STOP WHEN:
- Questions answered (Medium+)
- Budget exhausted
- 5 calls with no new insights
- Blocked on human input
```
