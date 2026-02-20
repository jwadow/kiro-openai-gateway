---
name: gemini-large-context
description: Use when analyzing large codebases, comparing multiple files, or researching project-wide patterns that exceed typical context limits - leverages Gemini CLI's 1M token context window for comprehensive analysis
---

# Gemini CLI Large Context Analysis

## Overview

Use Gemini CLI's massive context window (1M tokens) when analysis requires more context than available in current session. Ideal for codebase-wide searches, multi-file comparisons, and pattern discovery across large projects.

## When to Use

- Analyzing entire codebases or large directories (100KB+)
- Comparing multiple large files simultaneously
- Understanding project-wide patterns or architecture
- Context window insufficient for current task
- Verifying feature implementations across codebase
- Research that needs to scan many files at once

## Quick Reference

```bash
# Basic non-interactive analysis
gemini -p "@src/ Summarize architecture"

# Multiple directories
gemini -p "@src/ @tests/ Analyze test coverage"

# All project files
gemini --all-files -p "Project overview"

# Specific model (Pro = 1M context)
gemini -m gemini-2.5-pro -p "@src/ Deep analysis"
```

## File/Directory Inclusion Syntax

```bash
# Single file
gemini -p "@src/main.py Explain this file"

# Multiple files
gemini -p "@package.json @src/index.js Analyze dependencies"

# Entire directory (recursive)
gemini -p "@src/ Summarize architecture"

# Multiple directories
gemini -p "@src/ @tests/ Analyze test coverage"

# Current directory
gemini -p "@./ Project overview"

# Alternative: all files flag
gemini --all-files -p "Analyze project structure"
```

## Research Patterns

### Architecture Analysis

```bash
gemini -p "@src/
Describe:
1. Overall architecture pattern (MVC, Clean, etc.)
2. Key modules and their responsibilities
3. Data flow between components
4. External dependencies and integrations"
```

### Feature Implementation Check

```bash
gemini -p "@src/ @lib/
Has [FEATURE] been implemented?
Show:
- Relevant files and functions
- Implementation approach
- Any gaps or incomplete areas"
```

### Pattern Discovery

```bash
gemini -p "@src/
Find all instances of [PATTERN]:
- File paths
- Implementation variations
- Consistency assessment"
```

### Security Audit

```bash
gemini -p "@src/ @api/
Security review:
- Input validation practices
- Authentication/authorization patterns
- SQL injection protections
- XSS prevention measures"
```

### Test Coverage Analysis

```bash
gemini -p "@src/ @tests/
Assess test coverage:
- Which modules have tests?
- Which are missing tests?
- Test quality (unit vs integration)
- Edge cases covered"
```

## Integration with OpenCode Workflow

### For Task-Constrained Research

When researching within task boundaries:

```bash
# 1. Include bead spec in context
gemini -p "@src/ @.beads/artifacts/br-xxx/spec.md
Research implementations matching spec constraints"

# 2. Save findings to bead artifacts
# Write to .beads/artifacts/br-xxx/research.md
```

### Delegating Large Research to Gemini

In AGENTS.md or prompts, instruct agents:

```markdown
When analysis requires more than 100KB of files:

1. Use Gemini CLI: `gemini -p "@[paths] [question]"`
2. Capture output
3. Synthesize findings in response
```

## Output Options

```bash
# Plain text (default)
gemini -p "query"

# JSON for parsing
gemini -p "query" --output-format json

# Streaming for long ops
gemini -p "query" --output-format stream-json
```

## Common Research Queries

- **Architecture overview:** `gemini -p "@src/ Describe architecture"`
- **Find implementations:** `gemini -p "@src/ Where is [X] implemented?"`
- **Pattern audit:** `gemini -p "@src/ Find all [pattern] usages"`
- **Dependency analysis:** `gemini -p "@package.json @src/ Analyze dependency usage"`
- **Code quality:** `gemini -p "@src/ Identify code smells"`
- **Migration planning:** `gemini -p "@src/ Plan migration from [A] to [B]"`

## Configuration

### Authentication

```bash
# Google login (free tier: 60 req/min, 1000/day)
gemini  # Follow OAuth flow

# Or API key
export GEMINI_API_KEY="your-key"
```

### Model Selection

For most analysis tasks, **`gemini-2.5-pro`** is the best choice—it has a 1M token context window and handles code, text, and image analysis exceptionally well. This is the default model.

Use **`gemini-2.5-flash`** when you need faster responses and don't need the full context window.

**Important:** If you're analyzing images or screenshots, use `gemini-2.5-pro`. Image generation models like `imagen-3.0-generate-002` are for _creating_ new images, not understanding existing ones.

```bash
# Gemini 2.5 Pro (1M context) - default, best for analysis
gemini -p "query"

# Gemini Flash (faster, smaller context)
gemini -m gemini-2.5-flash -p "query"
```

## Best Practices

1. **Scope appropriately** - Include only relevant directories
2. **Be specific** - Ask focused questions, not vague queries
3. **Use for read-only analysis** - Don't ask Gemini to modify files in non-interactive mode
4. **Capture output** - Redirect to file for long analyses: `gemini -p "..." > analysis.md`
5. **Combine with local tools** - Use Gemini for research, local tools for implementation

## Limitations

- Non-interactive mode: no tool approvals (file writes, shell commands)
- `@file` syntax: best in interactive mode
- Network dependency: requires internet connection
- Rate limits: 60 req/min free tier
