# Registry Support

## Contents
- npm (Node.js)
- PyPI (Python)
- crates.io (Rust)
- Repository hosts

## npm (Node.js)

**Prefixes:** `npm:` (or none - default)

**API:** `https://registry.npmjs.org/{package}`

### Version Detection

Auto-detects installed version from (in order):
1. `node_modules/{pkg}/package.json`
2. `package-lock.json` (npm v6 and v7+ formats)
3. `pnpm-lock.yaml`
4. `yarn.lock`
5. `package.json` dependencies (strips `^`, `~`, etc.)

### Spec Parsing

```
zod           → name: zod, version: (detected or latest)
zod@3.22.0    → name: zod, version: 3.22.0
@babel/core   → name: @babel/core (scoped)
@babel/core@7.0.0 → name: @babel/core, version: 7.0.0
```

### Repo URL Extraction

From `repository` field, normalizes:
- `git+https://...` → `https://...`
- `git://...` → `https://...`
- `git+ssh://git@...` → `https://...`
- Removes `.git` suffix
- Handles `github:owner/repo` shorthand

### Monorepo Support

Uses `repository.directory` field for packages in monorepos.
Path becomes: `repos/{host}/{owner}/{repo}/{directory}`

## PyPI (Python)

**Prefixes:** `pypi:`, `pip:`, `python:`

**API:** `https://pypi.org/pypi/{package}/json`

### Spec Parsing

```
requests        → name: requests
requests==2.31.0 → name: requests, version: 2.31.0
requests@2.31.0  → name: requests, version: 2.31.0
```

### Repo URL Extraction

Checks `project_urls` in order:
1. `Source`, `Source Code`
2. `Repository`, `GitHub`
3. `Code`, `Homepage`

Falls back to `home_page` if it's a git URL.

## crates.io (Rust)

**Prefixes:** `crates:`, `cargo:`, `rust:`

**API:** `https://crates.io/api/v1/crates/{crate}`

### Spec Parsing

```
serde       → name: serde
serde@1.0.0 → name: serde, version: 1.0.0
```

### Repo URL Extraction

Uses `repository` field, falls back to `homepage` if it's a git URL.

## Repository Hosts

### GitHub

**API:** `https://api.github.com/repos/{owner}/{repo}`

Resolves default branch, constructs clone URL.

**Rate limiting:** 60 req/hour unauthenticated. Error on 403.

### GitLab

**API:** `https://gitlab.com/api/v4/projects/{owner}%2F{repo}`

Resolves default branch, constructs clone URL.

### Bitbucket

Supported for parsing (`bitbucket:owner/repo`), but no API resolution.
Assumes `main` as default branch.

## Repo Spec Formats

| Format | Example | Host |
|--------|---------|------|
| `owner/repo` | `vercel/ai` | github.com |
| `github:owner/repo` | `github:facebook/react` | github.com |
| `gitlab:owner/repo` | `gitlab:inkscape/inkscape` | gitlab.com |
| `bitbucket:owner/repo` | `bitbucket:atlassian/python-bitbucket` | bitbucket.org |
| `host/owner/repo` | `gitlab.com/owner/repo` | (from URL) |
| Full URL | `https://github.com/...` | (from URL) |

## Ref Specifications

Append to repo spec:

| Suffix | Example | Meaning |
|--------|---------|---------|
| `@ref` | `owner/repo@v1.0.0` | Tag, branch, or commit |
| `#ref` | `owner/repo#main` | Branch (alternative syntax) |

URL paths also supported: `https://github.com/owner/repo/tree/branch`

## Git Tag Patterns

When cloning packages, tries tags in order:
1. `v{version}` - Most common (e.g., `v3.22.0`)
2. `{version}` - No prefix (e.g., `3.22.0`)
3. Default branch - Fallback with warning

Uses `--depth 1 --single-branch` for efficient cloning.
