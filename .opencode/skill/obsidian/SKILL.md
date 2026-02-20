---
name: obsidian
description: Use when working with Obsidian vault via MCP - read/write notes, search, tag management, and vault operations
mcp:
  server: @mauricio.wolff/mcp-obsidian
  args: ["{env:OBSIDIAN_VAULT_PATH}"]
---

# Obsidian Vault (MCP)

MCP server for safe Obsidian vault access. Read/write notes, search, manage tags.

## Available Tools

### Read Operations

| Tool                  | Purpose                           | Arguments                                         |
| --------------------- | --------------------------------- | ------------------------------------------------- |
| `read_note`           | Read note with parsed frontmatter | `path`, `prettyPrint`                             |
| `read_multiple_notes` | Batch read (max 10)               | `paths[]`, `includeContent`, `includeFrontmatter` |
| `get_frontmatter`     | Extract only frontmatter          | `path`                                            |
| `get_notes_info`      | Get metadata without content      | `paths[]`                                         |
| `list_directory`      | List files and directories        | `path`                                            |

### Write Operations

| Tool                 | Purpose                               | Arguments                                |
| -------------------- | ------------------------------------- | ---------------------------------------- |
| `write_note`         | Write note (overwrite/append/prepend) | `path`, `content`, `frontmatter`, `mode` |
| `update_frontmatter` | Update frontmatter only               | `path`, `frontmatter`, `merge`           |
| `delete_note`        | Delete note (requires confirmation)   | `path`, `confirmPath`                    |
| `move_note`          | Move/rename note                      | `oldPath`, `newPath`, `overwrite`        |

### Search & Tags

| Tool           | Purpose                       | Arguments                                              |
| -------------- | ----------------------------- | ------------------------------------------------------ |
| `search_notes` | Search by content/frontmatter | `query`, `limit`, `searchContent`, `searchFrontmatter` |
| `manage_tags`  | Add/remove/list tags          | `path`, `operation`, `tags[]`                          |

## Write Modes

| Mode        | Description                           |
| ----------- | ------------------------------------- |
| `overwrite` | Replace entire file content (default) |
| `append`    | Add content to end of file            |
| `prepend`   | Add content to beginning of file      |

## Usage Examples

### Read Notes

```typescript
// Read a single note
skill_mcp({
  skill_name: "obsidian",
  tool_name: "read_note",
  arguments: '{"path": "projects/project-ideas.md"}',
});

// Read multiple notes
skill_mcp({
  skill_name: "obsidian",
  tool_name: "read_multiple_notes",
  arguments: '{"paths": ["note1.md", "note2.md"], "includeContent": true}',
});

// List directory
skill_mcp({
  skill_name: "obsidian",
  tool_name: "list_directory",
  arguments: '{"path": "Projects"}',
});
```

### Write Notes

```typescript
// Create new note (overwrite)
skill_mcp({
  skill_name: "obsidian",
  tool_name: "write_note",
  arguments: `{
    "path": "meeting-notes.md",
    "content": "# Team Meeting\\n\\n## Agenda\\n- Project updates",
    "frontmatter": {"title": "Team Meeting", "date": "2025-02-13", "tags": ["meetings", "team"]},
    "mode": "overwrite"
  }`,
});

// Append to existing note
skill_mcp({
  skill_name: "obsidian",
  tool_name: "write_note",
  arguments:
    '{"path": "daily-log.md", "content": "\\n\\n## 3:00 PM\\n- Completed review", "mode": "append"}',
});
```

### Search & Tags

```typescript
// Search notes
skill_mcp({
  skill_name: "obsidian",
  tool_name: "search_notes",
  arguments: '{"query": "machine learning", "limit": 5, "searchContent": true}',
});

// Add tags
skill_mcp({
  skill_name: "obsidian",
  tool_name: "manage_tags",
  arguments: '{"path": "research-notes.md", "operation": "add", "tags": ["important", "ai"]}',
});

// List tags
skill_mcp({
  skill_name: "obsidian",
  tool_name: "manage_tags",
  arguments: '{"path": "research-notes.md", "operation": "list"}',
});
```

### Delete (Safe)

```typescript
// Delete requires confirmation (both paths must match)
skill_mcp({
  skill_name: "obsidian",
  tool_name: "delete_note",
  arguments: '{"path": "old-draft.md", "confirmPath": "old-draft.md"}',
});
```

## Configuration

### Environment Variable

Set your vault path:

```bash
export OBSIDIAN_VAULT_PATH="/path/to/your/obsidian/vault"
```

Or configure in opencode.json:

```json
{
  "mcp": {
    "obsidian": {
      "command": "npx",
      "args": ["@mauricio.wolff/mcp-obsidian", "/path/to/vault"]
    }
  }
}
```

## Security

- Path traversal protection: prevents access outside vault
- Auto-excludes: `.obsidian`, `.git`, `node_modules`
- Frontmatter validation: blocks dangerous objects
- Confirmation required for deletions

## Common Use Cases

| Task                 | Tool             | Example                                                                       |
| -------------------- | ---------------- | ----------------------------------------------------------------------------- |
| List vault files     | `list_directory` | `list_directory({ path: "" })`                                                |
| Read specific note   | `read_note`      | `read_note({ path: "tasks/project.md" })`                                     |
| Create/update note   | `write_note`     | `write_note({ path: "new.md", content: "...", mode: "overwrite" })`           |
| Search notes         | `search_notes`   | `search_notes({ query: "API", limit: 10 })`                                   |
| Add tags             | `manage_tags`    | `manage_tags({ path: "note.md", operation: "add", tags: ["urgent"] })`        |
| Append to daily note | `write_note`     | `write_note({ path: "daily/2025-02-13.md", content: "...", mode: "append" })` |

## Tips

- Use `prettyPrint: true` for debugging, `false` (default) for production
- Batch reads with `read_multiple_notes` (max 10)
- Search supports content and frontmatter filtering
- Frontmatter is auto-parsed on read
