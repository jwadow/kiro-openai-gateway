---
name: augment-context-engine
description: Semantic codebase search via Augment Context Engine MCP. Use when you need to understand code relationships, find relevant implementations, or explore unfamiliar codebases beyond keyword matching.
---

# Augment Context Engine (MCP)

Semantic code search powered by Augment's Context Engine. Unlike grep (text matching), this understands code meaning, relationships, and cross-file dependencies.

## Available Tools

- `augment_code_search` - Semantic search across indexed GitHub repositories

**Parameters:**

- `repo_owner` (string, required) - GitHub org or username (e.g. `"augmentcode"`)
- `repo_name` (string, required) - Repository name (e.g. `"test-repo"`)
- `query` (string, required) - Natural language description of what you're looking for
- `branch` (string, optional) - Branch to search (defaults to `"main"`)
- `max_results` (integer, optional) - Max code snippets to return (defaults to 5)

## Quick Start

```
# Search a GitHub repo for authentication code
skill_mcp(skill_name="augment-context-engine", tool_name="augment_code_search", arguments='{"repo_owner": "myorg", "repo_name": "myapp", "query": "authentication middleware that validates JWT tokens"}')

# Search a specific branch with more results
skill_mcp(skill_name="augment-context-engine", tool_name="augment_code_search", arguments='{"repo_owner": "myorg", "repo_name": "myapp", "query": "error handling patterns", "branch": "develop", "max_results": 10}')
```

> **Tip:** Get `repo_owner` and `repo_name` from git: `git remote get-url origin`

## Setup

### 1. Install the Augment GitHub App

Install at [github.com/apps/augmentcode](https://github.com/apps/augmentcode/installations/new) and grant access to the repos you want to index.

### 2. Add the remote server

The skill's `mcp.json` uses `mcp-remote` to bridge the remote API via stdio.

For global access, add to `~/.config/opencode/opencode.json`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "auggie": {
      "type": "remote",
      "url": "https://api.augmentcode.com/mcp",
      "enabled": true
    }
  }
}
```

### 3. Authenticate

Sign in at [app.augmentcode.com](https://app.augmentcode.com) when prompted by `mcp-remote` on first use.

## Query Tips

Good queries (natural language, conceptual):

- `"function that handles user authentication"`
- `"database connection setup code"`
- `"tests for the payment processing module"`

Bad queries (use grep instead):

- `"foo_bar"` — exact symbol search
- `"TODO"` — keyword search
- `"code that deals with everything"` — too vague

## When to Use

| Scenario                 | Use This              | Instead Of                 |
| ------------------------ | --------------------- | -------------------------- |
| Find code by meaning     | `augment_code_search` | `grep` (text only)         |
| Understand relationships | `augment_code_search` | `@explore` agent (heavier) |
| Unfamiliar codebase      | `augment_code_search` | Manual file exploration    |
| Cross-repo dependencies  | `augment_code_search` | LSP references (narrower)  |

## When NOT to Use

- **Exact string matching** — Use `grep` instead (faster, free)
- **Known file paths** — Use `read` directly
- **Symbol definitions** — Use LSP `goToDefinition` (precise)
- **Local-only work** — This searches GitHub-indexed repos, not local files

## Tool Priority Integration

```
grep (text) → semantic search (meaning) → read (full file) → LSP (symbols) → edit
```

Use grep first for exact matches. Escalate to semantic search when grep results are noisy or you need conceptual understanding.

## Cost

- ~40-70 credits per query
- Not free — use judiciously
- Prefer grep for simple lookups

## Resources

- Docs: https://docs.augmentcode.com/context-services/mcp/overview
- OpenCode Quickstart: https://docs.augmentcode.com/context-services/mcp/quickstart-open-code
- GitHub App: https://github.com/apps/augmentcode/installations/new
- Product: https://www.augmentcode.com/product/context-engine-mcp
