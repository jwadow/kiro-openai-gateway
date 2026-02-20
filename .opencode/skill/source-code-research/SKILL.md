---
name: source-code-research
description: >
  Use when researching library implementation details beyond API docs. Fetches package source code
  using opensrc to understand internals, edge cases, and implementation patterns. Complements
  documentation-based research with actual code inspection.
version: "1.0.0"
license: MIT
---

# Source Code Research - Deep Library Investigation

Fetch and analyze package source code when documentation is insufficient.

## When to Use This Skill

Use source code research when:

- **Documentation gaps**: API docs don't explain behavior clearly
- **Edge cases**: Need to understand how library handles corner cases
- **Implementation details**: Need to see actual code, not just interfaces
- **Debugging**: Library behaving unexpectedly, need to trace internals
- **Evaluation**: Deciding if library fits requirements, need to assess quality
- **Type definitions**: TypeScript types exist but implementation unclear

**Don't use when:**

- Official docs answer your question (check Context7 first)
- You only need API syntax (codesearch is faster)
- Library is too large to analyze in session (>50k LOC)

## Prerequisites

OpenSrc must be available:

```bash
npx opensrc --help
```

If not installed, it will be fetched via npx automatically.

## Workflow

### Step 1: Identify What to Fetch

Determine the minimal package/repo needed:

```typescript
// If researching a specific npm package
const target = "zod"; // Just the package name

// If researching Python library
const target = "pypi:requests";

// If researching Rust crate
const target = "crates:serde";

// If researching GitHub repo directly
const target = "vercel/ai"; // or "github:vercel/ai@v3.0.0"
```

### Step 2: Fetch Source Code

Run opensrc to clone the repository:

```bash
npx opensrc <package>
```

**Examples:**

```bash
npx opensrc zod                    # Fetch latest zod from npm
npx opensrc zod@3.22.0             # Fetch specific version
npx opensrc pypi:requests          # Fetch Python package
npx opensrc vercel/ai              # Fetch GitHub repo
npx opensrc vercel/ai@v3.0.0       # Fetch specific tag
```

**What happens:**

- Clones source to `opensrc/repos/<host>/<owner>/<repo>/`
- Auto-detects version from lockfiles if no version specified
- Updates `opensrc/sources.json` with metadata
- Adds `opensrc/` to `.gitignore` automatically (asks once)

### Step 3: Locate Relevant Code

Use search tools to find code you need:

```typescript
// Find all TypeScript source files
glob({ pattern: "opensrc/**/src/**/*.ts" });

// Search for specific function/class
grep({
  pattern: "class ValidationError",
  path: "opensrc/",
  include: "*.ts",
});

// Search for function pattern
grep({
  pattern: "export function parse",
  path: "opensrc/",
  include: "*.ts",
});
```

### Step 4: Read and Analyze

Read the implementation:

```typescript
// Read the file
read({ filePath: "opensrc/repos/github.com/colinhacks/zod/src/types.ts" });

// Use LSP for navigation (if available)
lsp_lsp_goto_definition({
  filePath: "opensrc/.../file.ts",
  line: 42,
  character: 10,
});

// Find all references
lsp_lsp_find_references({
  filePath: "opensrc/.../file.ts",
  line: 42,
  character: 10,
});
```

### Step 5: Document Findings

Write research findings to bead artifact:

````markdown
# Research: [Library Name] Implementation

**Package:** [name@version]
**Source:** opensrc/repos/[path]
**Focus:** [What you were investigating]

## Key Findings

### [Topic 1]: [Function/Pattern Name]

**Location:** `opensrc/repos/.../file.ts:42`

**Implementation:**

```typescript
// Paste relevant code snippet
```
````

**Insights:**

- [What you learned]
- [Edge cases discovered]
- [Performance implications]

**Confidence:** High (direct source code)

---

### [Topic 2]: [Another Discovery]

[Same structure]

## Answers to Original Questions

1. **Q:** [Original question]
   **A:** [Answer based on source code]
   **Evidence:** `file.ts:123-145`

2. **Q:** [Another question]
   **A:** [Answer]

## Recommendations

Based on source analysis:

- [Recommendation 1]
- [Recommendation 2]

## Caveats

- Version analyzed: [version]
- Code may have changed in newer versions
- Private APIs discovered may change without notice

````

## Common Patterns

### Pattern 1: Understanding Error Handling

```typescript
// 1. Fetch package
// bash: npx opensrc zod

// 2. Find error classes
grep({ pattern: "class.*Error", path: "opensrc/", include: "*.ts" });

// 3. Read error implementation
read({ filePath: "opensrc/repos/.../errors.ts" });

// 4. Find where errors are thrown
grep({ pattern: "throw new", path: "opensrc/", include: "*.ts" });
````

### Pattern 2: Tracing Function Behavior

```typescript
// 1. Fetch source
// bash: npx opensrc react-hook-form

// 2. Find function definition
grep({
  pattern: "export function useForm",
  path: "opensrc/",
  include: "*.ts",
});

// 3. Read implementation
read({ filePath: "opensrc/.../useForm.ts" });

// 4. Find dependencies
grep({ pattern: "import.*from", path: "opensrc/.../useForm.ts" });
```

### Pattern 3: Evaluating Library Quality

```typescript
// 1. Fetch source
// bash: npx opensrc candidate-library

// 2. Check test coverage
glob({ pattern: "opensrc/**/*.test.ts" });
glob({ pattern: "opensrc/**/*.spec.ts" });

// 3. Read tests for usage patterns
read({ filePath: "opensrc/.../feature.test.ts" });

// 4. Check for TypeScript usage
glob({ pattern: "opensrc/**/tsconfig.json" });

// 5. Review package.json for dependencies
read({ filePath: "opensrc/.../package.json" });
```

## Source Structure Guide

### npm Packages

```
opensrc/
└── repos/
    └── github.com/              # npm packages resolve to GitHub
        └── owner/
            └── repo/
                ├── src/         # Source code (usually)
                ├── dist/        # Built output (ignore)
                ├── test/        # Tests (useful for examples)
                ├── package.json # Dependencies, scripts
                └── README.md    # Often has examples
```

### Python Packages (PyPI)

```
opensrc/
└── repos/
    └── github.com/              # Most PyPI packages on GitHub
        └── owner/
            └── repo/
                ├── src/         # or package_name/
                ├── tests/       # Python tests
                ├── setup.py     # Package config
                └── pyproject.toml
```

### Rust Crates

```
opensrc/
└── repos/
    └── github.com/
        └── owner/
            └── repo/
                ├── src/
                │   └── lib.rs   # Main library file
                ├── tests/
                ├── Cargo.toml   # Dependencies
                └── examples/    # Usage examples
```

## Tips for Efficient Analysis

### 1. Start with Tests

Tests often show real-world usage better than docs:

```typescript
glob({ pattern: "opensrc/**/*.test.{ts,js}" });
read({ filePath: "opensrc/.../feature.test.ts" });
```

### 2. Check Examples Directory

Many repos have `examples/` or `samples/`:

```typescript
glob({ pattern: "opensrc/**/examples/**/*" });
```

### 3. Read CHANGELOG for Context

Understand recent changes:

```typescript
read({ filePath: "opensrc/.../CHANGELOG.md" });
```

### 4. Check TypeScript Definitions

Often more accurate than docs:

```typescript
glob({ pattern: "opensrc/**/*.d.ts" });
read({ filePath: "opensrc/.../index.d.ts" });
```

### 5. Use Blame for History (if needed)

```bash
cd opensrc/repos/github.com/owner/repo
git log --oneline -- src/file.ts
git show <commit>:src/file.ts
```

## Limitations

### When Source Code Won't Help

- **Build-time transforms**: Source may differ from runtime (Babel, webpack)
- **Native modules**: C/C++ code requires different analysis
- **Minified code**: Some packages don't publish source
- **Monorepos**: May need to navigate complex structure

### Alternatives

If opensrc doesn't work:

1. **GitHub web interface**: Browse online at github.com/owner/repo
2. **npm unpacked**: `npm pack <package>` then extract
3. **node_modules**: If already installed, check `node_modules/<package>/`
4. **Source maps**: If debugging, browser DevTools may show original source

## Integration with Other Research Methods

Source code research complements other tools:

| Method         | Best For                   | Source Code Adds               |
| -------------- | -------------------------- | ------------------------------ |
| **Context7**   | API docs, official guides  | Implementation details         |
| **codesearch** | Usage patterns in the wild | Canonical implementation       |
| **grepsearch** | Real-world examples        | How library itself works       |
| **Web search** | Tutorials, blog posts      | Ground truth from source       |
| **Codebase**   | Project-specific patterns  | How dependencies actually work |

**Recommended flow:**

1. Context7 - Check official docs
2. Codebase - Check existing usage
3. **Source code** - If still unclear, fetch source
4. codesearch/grepsearch - See how others use it
5. Web search - Last resort for context

## Cleanup

After research is complete:

```bash
# Remove specific package
npx opensrc remove <package>

# Remove all sources
npx opensrc clean

# Remove just npm packages
npx opensrc clean --npm

# Keep sources for documentation
# (opensrc/ is gitignored, won't be committed)
```

## Example: Complete Workflow

**Scenario:** Need to understand how zod handles async refinements.

```bash
# 1. Fetch source
npx opensrc zod
```

```typescript
// 2. Find refinement code
grep({
  pattern: "refine.*async",
  path: "opensrc/",
  include: "*.ts",
});

// 3. Locate implementation
ast_grep({
  pattern: "refine($$$) { $$$ }",
  path: "opensrc/repos/github.com/colinhacks/zod/",
});

// 4. Read the implementation
read({
  filePath: "opensrc/repos/github.com/colinhacks/zod/src/types.ts",
  offset: 500,
  limit: 100,
});

// 5. Check tests for usage examples
glob({
  pattern: "opensrc/**/zod/**/*.test.ts",
});

read({
  filePath: "opensrc/repos/.../async.test.ts",
});

// 6. Document findings
write({
  filePath: ".beads/artifacts/br-xxx/research.md",
  content: `# Zod Async Refinements

**Finding:** Async refinements use \`parseAsync()\` not \`parse()\`

**Evidence:** \`src/types.ts:842-856\`

Async refinements return Promise<Output> and require:
- Use \`.parseAsync()\` method
- Refinement function must return Promise<boolean>
- Errors handled via Promise rejection

**Code snippet:**
[paste relevant code]

**Recommendation:** Use \`.refine(async (val) => {...})\` with \`.parseAsync()\`
`,
});
```

## Success Criteria

You've successfully used this skill when:

- [ ] Fetched correct package/version source
- [ ] Located relevant implementation code
- [ ] Understood behavior from reading source
- [ ] Documented findings with file:line references
- [ ] Answered original research question with high confidence
- [ ] Provided code evidence for claims

## Anti-Patterns

### ❌ Don't: Fetch Entire Ecosystem

```bash
# Bad: Fetching everything
npx opensrc react
npx opensrc react-dom
npx opensrc react-router
npx opensrc react-query
# ... (too much code)
```

**Do:** Fetch only what you need to answer specific question.

### ❌ Don't: Read Random Files

```typescript
// Bad: Reading without purpose
read({ filePath: "opensrc/.../index.ts" });
read({ filePath: "opensrc/.../utils.ts" });
read({ filePath: "opensrc/.../helpers.ts" });
// ... (unfocused exploration)
```

**Do:** Use grep to find relevant code first, then read.

### ❌ Don't: Ignore Version Mismatch

```bash
# Bad: Fetching latest when project uses old version
npx opensrc zod  # Fetches 3.23.x
# But project uses zod@3.20.0 (different behavior)
```

**Do:** Specify version matching your lockfile, or let opensrc auto-detect.

## Quick Reference

```bash
# Fetch package source
npx opensrc <package>                    # npm (auto-detect version)
npx opensrc <package>@<version>          # npm (specific version)
npx opensrc pypi:<package>               # Python
npx opensrc crates:<package>             # Rust
npx opensrc <owner>/<repo>               # GitHub
npx opensrc <owner>/<repo>@<tag>         # GitHub (specific tag)

# List fetched sources
npx opensrc list
npx opensrc list --json

# Remove sources
npx opensrc remove <package>
npx opensrc clean
npx opensrc clean --npm --pypi --crates

# Source location
opensrc/repos/<host>/<owner>/<repo>/

# Metadata
opensrc/sources.json
```

## Further Reading

- OpenSrc Docs: https://github.com/vercel-labs/opensrc
- When to read source vs docs: https://danluu.com/read-code/
- Code reading techniques: https://www.codeproject.com/Articles/10/Code-Reading
