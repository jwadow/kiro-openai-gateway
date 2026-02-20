---
name: v1-run
description: npm package intelligence via MCP. Real-time versions, vulnerability data, health scores, and package comparisons. Use when selecting npm packages, checking for vulnerabilities, or comparing alternatives.
---

# v1.run MCP

Fast, accurate npm package intelligence for AI agents via Model Context Protocol.

## Overview

v1.run is an MCP-first npm registry by Midday.ai that provides:

- **Real-time version data** - No hallucinated packages
- **Security vulnerabilities** - From OSV database
- **Health scores** - Automated 0-100 scoring
- **Package comparisons** - 50+ pre-built categories

## MCP Endpoint

**URL**: `https://api.v1.run/mcp`

**Authentication**: None required (public API)

## Configuration

v1.run MCP is pre-configured as a skill. Load it with:

```typescript
skill({ name: "v1-run" });
```

### Manual Setup (if needed)

```json
{
  "mcpServers": {
    "v1": {
      "url": "https://api.v1.run/mcp"
    }
  }
}
```

## Available Tools

| Tool                    | Description                                                                                                       |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `get_package_health`    | Comprehensive health assessment (primary tool) - version, vulns, score, downloads, TS support, AI recommendations |
| `get_package_version`   | Get latest version of a package                                                                                   |
| `check_deprecated`      | Check if package is deprecated + get alternatives                                                                 |
| `check_types`           | Check TypeScript support (bundled or @types)                                                                      |
| `check_vulnerabilities` | Security vulnerabilities from OSV database                                                                        |
| `find_alternatives`     | Find alternative packages with recommendations                                                                    |
| `compare_packages`      | Side-by-side comparison (2-5 packages)                                                                            |

## Health Score System

Packages are scored 0-100 based on:

| Factor      | Weight | Measures                                |
| ----------- | ------ | --------------------------------------- |
| Downloads   | 20%    | Weekly downloads + trend direction      |
| Bundle Size | 20%    | Smaller gzip = higher score             |
| Freshness   | 25%    | Recent commits and releases             |
| Community   | 10%    | Stars, contributors                     |
| Quality     | 25%    | TypeScript, ESM, security, tree-shaking |

## Usage Examples

### Check Package Health

```typescript
// Get comprehensive health info for a package (primary tool)
skill_mcp({ skill_name: "v1-run", tool_name: "get_package_health", arguments: '{"name": "zod"}' });
```

Response includes:

- Latest version
- Known vulnerabilities (CVEs)
- Health score (0-100) with grade
- Weekly downloads + trend
- TypeScript support
- Maintenance status
- AI recommendation

### Check for Deprecation

```typescript
// Check if package is deprecated and get alternatives
skill_mcp({
  skill_name: "v1-run",
  tool_name: "check_deprecated",
  arguments: '{"name": "request"}',
});
```

### Check Vulnerabilities

```typescript
// Check specific version for security issues
skill_mcp({
  skill_name: "v1-run",
  tool_name: "check_vulnerabilities",
  arguments: '{"name": "lodash", "version": "4.17.20"}',
});
```

### Find Alternatives

```typescript
// Find alternative packages
skill_mcp({
  skill_name: "v1-run",
  tool_name: "find_alternatives",
  arguments: '{"name": "moment"}',
});
```

### Compare Packages

```typescript
// Compare similar packages (2-5 packages)
skill_mcp({
  skill_name: "v1-run",
  tool_name: "compare_packages",
  arguments: '{"packages": ["zod", "yup", "joi", "valibot"]}',
});
```

## Pre-built Categories (50+)

v1.run includes comparisons for popular package categories:

- **HTTP clients**: axios, got, ky, node-fetch
- **Date libraries**: moment, date-fns, dayjs, luxon
- **Validation**: zod, yup, joi, ajv, valibot
- **State management**: redux, zustand, jotai, recoil
- **ORM**: prisma, drizzle, typeorm, sequelize
- **Testing**: vitest, jest, mocha, ava
- **Bundlers**: vite, esbuild, webpack, rollup
- **Logging**: pino, winston, bunyan

## When to Use

Use v1.run MCP when:

1. **Choosing between packages** - Get objective comparisons
2. **Checking for vulnerabilities** - Before adding dependencies
3. **Evaluating maintenance** - Is the package actively maintained?
4. **Finding alternatives** - Discover better options for a package

## Best Practices

1. **Always check health** before adding new dependencies
2. **Compare alternatives** when multiple packages solve the same problem
3. **Verify TypeScript support** for TypeScript projects
4. **Check bundle size** for frontend applications

## Documentation

- [v1.run](https://v1.run)
- [GitHub: midday-ai/v1](https://github.com/midday-ai/v1)
- [MCP Documentation](https://modelcontextprotocol.io)
