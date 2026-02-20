---
name: opensrc
description: Fetch source code for npm, PyPI, or crates.io packages and GitHub/GitLab repos to provide AI agents with implementation context beyond types and docs. Use when needing to understand how a library works internally, debug dependency issues, or explore package implementations.
---

# opensrc

CLI tool to fetch source code for packages/repos, giving AI coding agents deeper implementation context.

## When to Use

- Need to understand how a library/package works internally (not just its interface)
- Debugging issues where types alone are insufficient
- Exploring implementation patterns in dependencies
- Agent needs to reference actual source code of a package

## Quick Start

```bash
# Install globally or use npx
npm install -g opensrc

# Fetch npm package (auto-detects installed version from lockfile)
npx opensrc zod

# Fetch from other registries
npx opensrc pypi:requests       # Python/PyPI
npx opensrc crates:serde        # Rust/crates.io

# Fetch GitHub repo directly
npx opensrc vercel/ai           # owner/repo shorthand
npx opensrc github:owner/repo   # explicit prefix
npx opensrc https://github.com/colinhacks/zod  # full URL

# Fetch specific version/ref
npx opensrc zod@3.22.0
npx opensrc owner/repo@v1.0.0
```

## Commands

| Command | Description |
|---------|-------------|
| `opensrc <packages...>` | Fetch source for packages/repos |
| `opensrc list` | List all fetched sources |
| `opensrc remove <name>` | Remove specific source |
| `opensrc clean` | Remove all sources |

## Output Structure

After fetching, sources stored in `opensrc/` directory:

```
opensrc/
├── settings.json           # User preferences
├── sources.json            # Index of fetched packages/repos
└── repos/
    └── github.com/
        └── owner/
            └── repo/       # Cloned source code
```

## File Modifications

On first run, opensrc prompts to modify:
- `.gitignore` - adds `opensrc/` to ignore list
- `tsconfig.json` - excludes `opensrc/` from compilation
- `AGENTS.md` - adds section pointing agents to source code

Use `--modify` or `--modify=false` to skip prompt.

## Key Behaviors

1. **Version Detection** - For npm, auto-detects installed version from `node_modules`, `package-lock.json`, `pnpm-lock.yaml`, or `yarn.lock`
2. **Repository Resolution** - Resolves package to its git repo via registry API, clones at matching tag
3. **Monorepo Support** - Handles packages in monorepos via `repository.directory` field
4. **Shallow Clone** - Uses `--depth 1` for efficient cloning, removes `.git` after clone
5. **Tag Fallback** - Tries `v{version}`, `{version}`, then default branch if tag not found

## Common Workflows

### Fetching a Package

```bash
# Agent needs to understand zod's implementation
npx opensrc zod
# → Detects version from lockfile
# → Finds repo URL from npm registry
# → Clones at matching git tag
# → Source available at opensrc/repos/github.com/colinhacks/zod/
```

### Updating Sources

```bash
# Re-run same command to update to currently installed version
npx opensrc zod
# → Checks if version changed
# → Re-clones if needed
```

### Multiple Sources

```bash
# Fetch multiple at once
npx opensrc react react-dom next
npx opensrc zod pypi:pydantic vercel/ai
```

## References

For detailed information:
- [CLI Usage & Options](references/cli-usage.md) - Full command reference
- [Architecture](references/architecture.md) - Code structure and extension
- [Registry Support](references/registry-support.md) - npm, PyPI, crates.io details
