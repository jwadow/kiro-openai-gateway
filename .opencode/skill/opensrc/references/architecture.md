# opensrc Architecture

## Contents
- Directory structure
- Core flow
- Key modules
- Type definitions
- Extension points

## Directory Structure

```
src/
├── index.ts              # CLI entry, Commander setup
├── types.ts              # Shared type definitions
├── commands/
│   ├── fetch.ts          # Main fetch logic
│   ├── list.ts           # List sources
│   ├── remove.ts         # Remove sources
│   └── clean.ts          # Clean all sources
└── lib/
    ├── git.ts            # Clone, path management
    ├── repo.ts           # Parse/resolve repo specs
    ├── version.ts        # Detect installed versions
    ├── agents.ts         # AGENTS.md/sources.json updates
    ├── gitignore.ts      # .gitignore management
    ├── tsconfig.ts       # tsconfig.json exclude
    ├── settings.ts       # User preferences
    ├── prompt.ts         # Interactive prompts
    └── registries/
        ├── index.ts      # Registry detection/routing
        ├── npm.ts        # npm registry API
        ├── pypi.ts       # PyPI API
        └── crates.ts     # crates.io API
```

## Core Flow

### Fetch Package

1. **Parse input** - Detect registry prefix or repo format
2. **Version detection** (npm only) - Check lockfiles/node_modules
3. **Registry lookup** - Query API for repo URL
4. **Clone** - Shallow clone at matching git tag
5. **Update index** - Write to sources.json, optionally AGENTS.md

### Input Type Detection

```
detectInputType(spec) → "package" | "repo"
```

- Registry prefix (`npm:`, `pypi:`, `crates:`) → package
- Repo pattern (`owner/repo`, URL, `github:`) → repo
- Default → package (npm)

## Key Modules

### registries/index.ts

Routes to correct registry handler:

```typescript
parsePackageSpec(spec): PackageSpec
resolvePackage(spec): ResolvedPackage
detectRegistry(spec): { registry, cleanSpec }
detectInputType(spec): "package" | "repo"
```

### git.ts

Manages cloning and source storage:

```typescript
fetchSource(resolved, cwd): FetchResult
fetchRepoSource(resolved, cwd): FetchResult
listSources(cwd): { packages, repos }
removePackageSource(name, cwd, registry): { removed, repoRemoved }
```

Storage structure: `opensrc/repos/{host}/{owner}/{repo}/`

### version.ts

Detects installed npm versions (priority order):
1. `node_modules/{pkg}/package.json`
2. `package-lock.json`
3. `pnpm-lock.yaml`
4. `yarn.lock`
5. `package.json` (strips range prefixes)

### repo.ts

Parses repo specs, resolves via GitHub/GitLab API:

```typescript
parseRepoSpec(spec): RepoSpec | null
resolveRepo(spec): ResolvedRepo
isRepoSpec(spec): boolean
```

Supports: GitHub, GitLab, Bitbucket (GitHub/GitLab via API).

## Type Definitions

```typescript
type Registry = "npm" | "pypi" | "crates"

interface PackageSpec {
  registry: Registry
  name: string
  version?: string
}

interface ResolvedPackage {
  registry: Registry
  name: string
  version: string
  repoUrl: string
  repoDirectory?: string  // For monorepos
  gitTag: string
}

interface RepoSpec {
  host: string      // github.com, gitlab.com
  owner: string
  repo: string
  ref?: string      // Branch, tag, commit
}

interface FetchResult {
  package: string
  version: string
  path: string
  success: boolean
  error?: string
  registry?: Registry
}
```

## Extension Points

### Adding a Registry

1. Create `registries/{name}.ts`:
   - `parse{Name}Spec(spec)` - Parse name@version
   - `resolve{Name}Package(name, version)` - Query API, return ResolvedPackage

2. Update `registries/index.ts`:
   - Add prefix to `REGISTRY_PREFIXES`
   - Add case to `parsePackageSpec` and `resolvePackage`

3. Add to `Registry` type in `types.ts`

### Registry Implementation Pattern

```typescript
// Parse spec into name/version
export function parseSpec(spec: string): { name: string; version?: string }

// Query registry API, extract repo URL
async function fetchInfo(name: string): Promise<RegistryResponse>

// Normalize git URLs (remove git+, .git suffix)
function extractRepoUrl(info): string | null

// Main resolver
export async function resolve(name: string, version?: string): Promise<ResolvedPackage>
```

### Git Tag Resolution

Clone tries tags in order:
1. `v{version}` (most common)
2. `{version}` (no prefix)
3. Default branch (fallback with warning)
