---
name: supabase
description: Comprehensive Supabase platform MCP for database operations, edge functions, development tools, debugging, and project management. Use when working with Supabase projects, databases, or APIs.
---

# Supabase Platform (MCP)

Supabase MCP server for database operations, edge functions, project management, and debugging.

## Available Tools

### Account & Projects

- `list_projects` - Lists all Supabase projects
- `get_project` - Gets details for a specific project
- `list_organizations` - Lists all organizations

### Database

- `list_tables` - Lists all tables in specified schemas
- `list_extensions` - Lists PostgreSQL extensions
- `list_migrations` - Lists database migrations
- `execute_sql` - Executes raw SQL queries

### Development

- `get_project_url` - Gets the API URL for a project
- `get_publishable_keys` - Gets anonymous API keys (client-safe)
- `generate_typescript_types` - Generates TypeScript types from schema

### Edge Functions

- `list_edge_functions` - Lists all Edge Functions
- `get_edge_function` - Retrieves Edge Function file contents
- `deploy_edge_function` - Deploys or updates an Edge Function

### Debugging

- `get_logs` - Retrieves logs by service type
- `get_advisors` - Gets security/performance advisory notices

### Documentation

- `search_docs` - Searches Supabase documentation

## Workflow

### Quick Start

```
# List projects
skill_mcp(skill_name="supabase", tool_name="list_projects")

# List tables in database
skill_mcp(skill_name="supabase", tool_name="list_tables")

# Execute SQL query
skill_mcp(skill_name="supabase", tool_name="execute_sql", arguments='{"query": "SELECT * FROM users LIMIT 10"}')

# Generate TypeScript types
skill_mcp(skill_name="supabase", tool_name="generate_typescript_types")

# Search docs
skill_mcp(skill_name="supabase", tool_name="search_docs", arguments='{"query": "auth custom claims"}')
```

### Get Project Credentials

```
# Get API URL and keys for project
skill_mcp(skill_name="supabase", tool_name="get_project_url")
skill_mcp(skill_name="supabase", tool_name="get_publishable_keys")

# List Edge Functions
skill_mcp(skill_name="supabase", tool_name="list_edge_functions")

# Deploy Edge Function
skill_mcp(skill_name="supabase", tool_name="deploy_edge_function", arguments='{"name": "my-function", "import_map": {...}, "entrypoint": "index.ts"}')
```

### Debug Issues

```
# Get logs by service
skill_mcp(skill_name="supabase", tool_name="get_logs", arguments='{"service": "postgres", "limit": 100}')

# Check advisories
skill_mcp(skill_name="supabase", tool_name="get_advisors")
```

## Security Notes

- **Read-only mode**: Set `"read_only": true` in mcp.json to disable write operations
- **Project scoping**: Use `project_ref` to limit access to specific projects
- **Environment variables**: Set `SUPABASE_ACCESS_TOKEN` for authentication

## Server Options

For advanced usage, modify `mcp.json`:

```json
{
  "supabase": {
    "command": "npx",
    "args": ["-y", "@supabase/mcp@latest"],
    "env": {
      "SUPABASE_ACCESS_TOKEN": "your-token-here"
    },
    "includeTools": ["list_tables", "execute_sql", "..."]
  }
}
```

Configuration options:

- `project_ref` - Scope to specific project (recommended)
- `read_only` - Restrict to read-only operations (recommended)
- `features` - Enable specific tool groups

> **Note**: This skill loads 14 essential tools. Excludes experimental (branching) and storage tools that require paid plans.
