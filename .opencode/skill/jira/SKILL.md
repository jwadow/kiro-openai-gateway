---
name: jira
description: Jira and Confluence integration via official Atlassian MCP. Search issues, create tickets, update status, and access Confluence docs. Uses OAuth 2.1 authorization with Rovo Search.
---

# Jira & Confluence Integration (MCP)

Official Atlassian MCP Server integration via `atlassian/atlassian-mcp-server`.

## Key Features

- **OAuth 2.1 Authorization** - Secure browser-based authentication
- **Rovo Search** - Unified search across Jira and Confluence
- **Real-time Data** - Direct connection to Atlassian Cloud
- **Permission-aware** - Respects existing user access controls

## Available Tools

### Universal Search (Recommended)

- `search` - **Rovo Search** - Search Jira and Confluence content (use this by default)
- `fetch` - Get details by ARI (Atlassian Resource Identifier) from search results

### Jira

- `getJiraIssue` - Get issue details by key or ID
- `createJiraIssue` - Create new issues
- `editJiraIssue` - Update existing issues
- `transitionJiraIssue` - Change issue status
- `addCommentToJiraIssue` - Add comments to issues
- `addWorklogToJiraIssue` - Log work time
- `searchJiraIssuesUsingJql` - Search with JQL queries
- `getTransitionsForJiraIssue` - Get available status transitions
- `getVisibleJiraProjects` - List accessible projects
- `getJiraProjectIssueTypesMetadata` - Get issue types for a project
- `getJiraIssueTypeMetaWithFields` - Get field metadata for issue type
- `getJiraIssueRemoteIssueLinks` - Get remote links
- `lookupJiraAccountId` - Find user account IDs

### Confluence

- `getConfluencePage` - Get page content by ID
- `createConfluencePage` - Create new pages
- `updateConfluencePage` - Update existing pages
- `searchConfluenceUsingCql` - Search with CQL queries
- `getConfluenceSpaces` - List spaces
- `getPagesInConfluenceSpace` - List pages in a space
- `getConfluencePageDescendants` - Get child pages
- `getConfluencePageFooterComments` - Get footer comments
- `getConfluencePageInlineComments` - Get inline comments
- `createConfluenceFooterComment` - Add footer comment
- `createConfluenceInlineComment` - Add inline comment on specific text

### Utility

- `atlassianUserInfo` - Get current user info
- `getAccessibleAtlassianResources` - Get cloudId for API calls

## Quick Start

### 1. Configuration

The MCP server uses OAuth 2.1 - no API tokens needed. Configuration in `mcp.json`:

```json
{
  "jira": {
    "command": "npx",
    "args": ["-y", "mcp-remote", "https://mcp.atlassian.com/v1/sse"]
  }
}
```

### 2. Get Cloud ID

Most tools require a `cloudId`. Get it from your site URL or use the utility:

```typescript
// Get accessible resources and cloudId
skill_mcp(
  (skill_name = "jira"),
  (tool_name = "getAccessibleAtlassianResources"),
  (arguments = "{}"),
);
```

Or use your site URL directly as cloudId (e.g., `"ibet.atlassian.net"`).

### 3. Use MCP Tools

```typescript
// Universal search (recommended for discovery)
skill_mcp(
  (skill_name = "jira"),
  (tool_name = "search"),
  (arguments = '{"query": "authentication bug"}'),
);

// Get issue details
skill_mcp(
  (skill_name = "jira"),
  (tool_name = "getJiraIssue"),
  (arguments = '{"cloudId": "your-site.atlassian.net", "issueIdOrKey": "PROJ-123"}'),
);

// Search with JQL
skill_mcp(
  (skill_name = "jira"),
  (tool_name = "searchJiraIssuesUsingJql"),
  (arguments = '{"cloudId": "your-site.atlassian.net", "jql": "project = PROJ AND status = Open"}'),
);

// Create issue
skill_mcp(
  (skill_name = "jira"),
  (tool_name = "createJiraIssue"),
  (arguments =
    '{"cloudId": "your-site.atlassian.net", "projectKey": "PROJ", "issueTypeName": "Bug", "summary": "Login fails on mobile"}'),
);

// Transition issue status
skill_mcp(
  (skill_name = "jira"),
  (tool_name = "transitionJiraIssue"),
  (arguments =
    '{"cloudId": "your-site.atlassian.net", "issueIdOrKey": "PROJ-123", "transition": {"id": "21"}}'),
);

// Get Confluence page
skill_mcp(
  (skill_name = "jira"),
  (tool_name = "getConfluencePage"),
  (arguments = '{"cloudId": "your-site.atlassian.net", "pageId": "123456789"}'),
);

// Search Confluence with CQL
skill_mcp(
  (skill_name = "jira"),
  (tool_name = "searchConfluenceUsingCql"),
  (arguments = '{"cloudId": "your-site.atlassian.net", "cql": "title ~ \"Onboarding\""}'),
);
```

## Common Workflows

### Daily Standup

```typescript
skill_mcp(
  (skill_name = "jira"),
  (tool_name = "searchJiraIssuesUsingJql"),
  (arguments =
    '{"cloudId": "your-site.atlassian.net", "jql": "assignee = currentUser() AND updated >= -1d"}'),
);
```

### Bug Triage

```typescript
skill_mcp(
  (skill_name = "jira"),
  (tool_name = "searchJiraIssuesUsingJql"),
  (arguments =
    '{"cloudId": "your-site.atlassian.net", "jql": "type = Bug AND priority in (High, Critical) AND status != Done"}'),
);
```

### Sprint Planning

```typescript
skill_mcp(
  (skill_name = "jira"),
  (tool_name = "searchJiraIssuesUsingJql"),
  (arguments =
    '{"cloudId": "your-site.atlassian.net", "jql": "project = PROJ AND sprint in openSprints()"}'),
);
```

### Quick Discovery with Rovo Search

```typescript
// Best for finding content when you don't know exact location
skill_mcp(
  (skill_name = "jira"),
  (tool_name = "search"),
  (arguments = '{"query": "authentication implementation"}'),
);

// Then fetch details using ARI from results
skill_mcp(
  (skill_name = "jira"),
  (tool_name = "fetch"),
  (arguments = '{"id": "ari:cloud:jira:cloudId:issue/10107"}'),
);
```

## JQL Examples

```sql
-- My open issues
assignee = currentUser() AND status != Done

-- High priority bugs
project = PROJ AND type = Bug AND priority in (High, Critical)

-- Recently updated
project = PROJ AND updated >= -7d

-- Current sprint
project = PROJ AND sprint in openSprints()

-- Unassigned in backlog
project = PROJ AND assignee is EMPTY AND status = "To Do"
```

## CQL Examples (Confluence)

```sql
-- Pages with title containing "guide"
title ~ "guide"

-- Pages in specific space
space = "TEAM" AND type = page

-- Recently modified
lastModified >= now("-7d")

-- Pages by creator
creator = currentUser()
```

## Content Format Options

For Confluence pages, you can specify content format:

- `"markdown"` - Markdown format (easier to read/write)
- `"adf"` - Atlassian Document Format (native format)

```typescript
skill_mcp(
  (skill_name = "jira"),
  (tool_name = "getConfluencePage"),
  (arguments =
    '{"cloudId": "your-site.atlassian.net", "pageId": "123456", "contentFormat": "markdown"}'),
);
```

## Transition Workflow

To change issue status, first get available transitions:

```typescript
// 1. Get available transitions
skill_mcp(
  (skill_name = "jira"),
  (tool_name = "getTransitionsForJiraIssue"),
  (arguments = '{"cloudId": "your-site.atlassian.net", "issueIdOrKey": "PROJ-123"}'),
);

// 2. Use transition ID to change status
skill_mcp(
  (skill_name = "jira"),
  (tool_name = "transitionJiraIssue"),
  (arguments =
    '{"cloudId": "your-site.atlassian.net", "issueIdOrKey": "PROJ-123", "transition": {"id": "31"}}'),
);
```

## Resources

- GitHub: https://github.com/atlassian/atlassian-mcp-server
- Docs: https://www.atlassian.com/platform/remote-mcp-server
- Admin Guide: https://support.atlassian.com/security-and-access-policies/docs/understand-atlassian-rovo-mcp-server/
