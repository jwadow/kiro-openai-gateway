---
name: structured-edit
description: Use when editing files to reduce str_replace failures - combines LSP location with read-verify-edit pattern for reliable edits
---

# Structured Edit Protocol

## Overview

The `str_replace` edit tool is the #1 source of failures in LLM coding. Models reproduce content with subtle differences (whitespace, encoding, line endings) causing "string not found" errors.

**Core principle:** Don't guess content — locate, read, verify, then edit.

## Why This Exists

`str_replace` failures happen when:

| Cause                | Example                                    |
| -------------------- | ------------------------------------------ |
| Whitespace mismatch  | Tabs vs spaces, trailing spaces            |
| Content changed      | File modified since last read              |
| Multiple matches     | Same string appears twice in file          |
| Encoding differences | Line endings (CRLF vs LF), invisible chars |
| Stale context        | Editing from memory instead of fresh read  |

**Result:** Wasted tokens on retries, frustrated developers, broken workflows.

## The Protocol

### Step 1: LOCATE

Use LSP to find exact positions instead of guessing:

```typescript
// Find where a function is defined
lsp({ operation: "goToDefinition", filePath, line, character });

// Find all references to a symbol
lsp({ operation: "findReferences", filePath, line, character });

// Get all symbols in a file
lsp({ operation: "documentSymbol", filePath, line: 1, character: 1 });

// Search for symbol across workspace
lsp({ operation: "workspaceSymbol", filePath, line: 1, character: 1 });
```

### Step 2: READ

Get fresh file content at the located position:

```typescript
// Read context around target line
read({ filePath, offset: line - 10, limit: 30 });
```

**Always include context** — don't just read the target line.

### Step 3: VERIFY

Confirm expected content exists at the location:

```typescript
// Check that what you expect is actually there
if (!content.includes(expectedSubstring)) {
  // STOP — investigate before proceeding
}
```

### Step 4: EDIT

Apply minimal, scoped change with unique context:

```typescript
// Include enough surrounding lines for uniqueness
edit({
  filePath,
  oldString: "  // unique context before\n  targetLine\n  // unique context after",
  newString: "  // unique context before\n  modifiedLine\n  // unique context after",
});
```

**Guidelines:**

- Include 2-3 lines before/after for uniqueness
- Never use just the target line
- Keep oldString minimal but unique

### Step 5: CONFIRM

Verify the edit succeeded:

```typescript
// Read back the modified section
read({ filePath, offset: line - 5, limit: 15 });

// Confirm content matches intent
```

## Red Flags — STOP

If you catch yourself:

- Editing without reading first
- Assuming content hasn't changed
- Using large multi-line oldString values
- Skipping the verify step
- Guessing line numbers without LSP

**STOP.** Return to Step 1.

## Best Practices

### File Size Matters

From research on the "harness problem":

| File Size     | Strategy                                   |
| ------------- | ------------------------------------------ |
| < 100 lines   | Full rewrite often easier than str_replace |
| 100-400 lines | Structured edit with good context          |
| > 400 lines   | Strongly prefer structured edits           |

**Prefer smaller files** — composition over monoliths.

### Unique Context Selection

```typescript
// BAD: Non-unique, whitespace-sensitive
oldString: "return result;";

// GOOD: Unique with surrounding context
oldString: "  // Calculate final value\n  const result = compute(input);\n  return result;";
```

### When to Use LSP vs Direct

| Scenario                  | Approach              |
| ------------------------- | --------------------- |
| Finding function/class    | LSP goToDefinition    |
| Finding all usages        | LSP findReferences    |
| Modifying specific symbol | LSP + structured edit |
| Large refactoring         | Consider full rewrite |
| Simple one-line change    | Direct edit OK        |

## Integration with Other Skills

**Use with:**

- `verification-before-completion` — Always verify edits succeeded
- `systematic-debugging` — When edit failures indicate deeper issues
- `defense-in-depth` — Add validation after structural changes

## Quick Reference

```
LOCATE  → lsp({ operation: "goToDefinition" | "findReferences", ... })
READ    → read({ filePath, offset: line-10, limit: 30 })
VERIFY  → Check expected content exists
EDIT    → edit({ oldString: "...unique context...", newString: "..." })
CONFIRM → read() again to verify success
```

## The Bottom Line

**Don't trust your memory. Don't guess content. Locate, read, verify, edit, confirm.**

This protocol eliminates the #1 source of LLM coding failures.
