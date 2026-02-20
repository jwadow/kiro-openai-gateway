# opensrc CLI Reference

## Contents
- Fetch command (default)
- List command
- Remove command
- Clean command
- Global options

## Fetch Command (Default)

Fetch source for packages/repos.

```bash
opensrc [packages...] [options]
```

### Package Formats

| Format | Example | Description |
|--------|---------|-------------|
| `<name>` | `zod` | npm package (latest or installed version) |
| `<name>@<version>` | `zod@3.22.0` | npm package at specific version |
| `npm:<name>` | `npm:react` | Explicit npm prefix |
| `pypi:<name>` | `pypi:requests` | Python package from PyPI |
| `pip:<name>` | `pip:flask` | Alias for pypi: |
| `crates:<name>` | `crates:serde` | Rust crate from crates.io |
| `cargo:<name>` | `cargo:tokio` | Alias for crates: |

### Repository Formats

| Format | Example |
|--------|---------|
| `owner/repo` | `vercel/ai` |
| `owner/repo@ref` | `vercel/ai@v1.0.0` |
| `owner/repo#ref` | `vercel/ai#main` |
| `github:owner/repo` | `github:facebook/react` |
| `gitlab:owner/repo` | `gitlab:inkscape/inkscape` |
| `https://github.com/...` | Full URL |

### Options

| Option | Description |
|--------|-------------|
| `--cwd <path>` | Working directory (default: cwd) |
| `--modify` | Allow file modifications (skip prompt) |
| `--modify=false` | Deny file modifications (skip prompt) |

### Examples

```bash
# Single package
opensrc zod

# Multiple packages
opensrc react react-dom next

# Mixed registries
opensrc zod pypi:requests crates:serde

# Specific versions
opensrc zod@3.22.0
opensrc pypi:requests==2.31.0

# GitHub repos
opensrc vercel/ai
opensrc facebook/react@v18.2.0
```

## List Command

List all fetched sources.

```bash
opensrc list [options]
```

### Options

| Option | Description |
|--------|-------------|
| `--json` | Output as JSON |
| `--cwd <path>` | Working directory |

### Output

Groups by registry (npm, PyPI, crates.io) and repos:

```
npm Packages:

  zod@3.22.0
    Path: opensrc/repos/github.com/colinhacks/zod
    Fetched: Jan 10, 2025

Repositories:

  github.com/vercel/ai@main
    Path: opensrc/repos/github.com/vercel/ai
    Fetched: Jan 10, 2025

Total: 1 package(s) (1 npm), 1 repo(s)
```

## Remove Command

Remove specific sources.

```bash
opensrc remove <packages...> [options]
opensrc rm <packages...>  # alias
```

### Options

| Option | Description |
|--------|-------------|
| `--cwd <path>` | Working directory |

### Examples

```bash
opensrc remove zod
opensrc rm pypi:requests
opensrc remove vercel/ai
```

## Clean Command

Remove all sources by category.

```bash
opensrc clean [options]
```

### Options

| Option | Description |
|--------|-------------|
| `--packages` | Only remove packages (all registries) |
| `--repos` | Only remove repos |
| `--npm` | Only remove npm packages |
| `--pypi` | Only remove PyPI packages |
| `--crates` | Only remove crates.io packages |
| `--cwd <path>` | Working directory |

### Examples

```bash
opensrc clean              # Remove everything
opensrc clean --packages   # Remove all packages, keep repos
opensrc clean --npm        # Remove only npm packages
opensrc clean --repos      # Remove only repos
```

## File Modifications

On first run, prompts to modify:

1. **`.gitignore`** - Adds `opensrc/` entry
2. **`tsconfig.json`** - Adds `opensrc/` to exclude array
3. **`AGENTS.md`** - Adds source code reference section

Choice saved to `opensrc/settings.json`.

### AGENTS.md Section

Adds guidance for AI agents:

```markdown
<!-- opensrc:start -->
## Source Code Reference
Source code for dependencies is available in `opensrc/`...
See `opensrc/sources.json` for the list of available packages.
<!-- opensrc:end -->
```
