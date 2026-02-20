# OpenCode MCP Bug Report

## Title

MCP tool calls fail with `TypeError: undefined is not an object (evaluating 'output.output.includes')` despite successful connection

## Environment

- **OpenCode version**: 1.1.36
- **OS**: macOS (darwin)
- **Node version**: (run `node --version` to fill in)

## MCP Servers Affected

- `context7` (https://mcp.context7.com/mcp)
- `gh_grep` (https://mcp.grep.app)

## Description

MCP tool calls from the AI agent fail with a TypeError, even though the MCP servers connect successfully and respond with HTTP 200 OK.

## Steps to Reproduce

1. Configure MCP servers in `opencode.json`:

```json
{
  "mcp": {
    "context7": {
      "type": "remote",
      "url": "https://mcp.context7.com/mcp",
      "headers": {
        "CONTEXT7_API_KEY": "{env:CONTEXT7_API_KEY}"
      }
    },
    "gh_grep": {
      "type": "remote",
      "url": "https://mcp.grep.app"
    }
  }
}
```

2. Set the `CONTEXT7_API_KEY` environment variable

3. Verify MCP servers are connected:

```bash
$ opencode mcp list
✓ context7 connected - https://mcp.context7.com/mcp
✓ gh_grep connected - https://mcp.grep.app
```

4. Debug shows successful connection:

```bash
$ opencode mcp debug context7
HTTP response: 200 OK
Server info: name=Context7, version=2.0.2

$ opencode mcp debug gh_grep
HTTP response: 200 OK
```

5. Use the AI agent to call a tool:

```
context7_resolve-library-id(query="React hooks", libraryName="react")
```

## Expected Behavior

The tool should return library information from Context7.

## Actual Behavior

```
TypeError: undefined is not an object (evaluating 'output.output.includes')
```

## Analysis

The error `output.output.includes` suggests there's code in OpenCode that does something like:

```javascript
if (output.output.includes(...)) { ... }
```

When `output` is undefined or doesn't have an `output` property, this crashes.

The bug is in **OpenCode's tool response handler**, not the MCP connection layer, because:

1. `opencode mcp list` shows both servers as "connected"
2. `opencode mcp debug` shows HTTP 200 OK responses
3. The error happens only when the AI agent calls the tool

## Resolution

✅ **FIXED** - Replaced MCP tools with native HTTP wrappers:

- `context7_resolve-library-id` - Native HTTP wrapper (works)
- `context7_query-docs` - Native HTTP wrapper (works)
- `grepsearch` - Native HTTP wrapper (works)
- `codesearch` (Exa Code API) - works
- `websearch` (Exa Web Search) - works

## Related Issues

- #6972 - May be related to Accept header issues
- #834 - SSE transport issues

## Additional Context

Log entries show benign errors that don't cause the crash:

```
ERROR service=mcp clientName=context7 error=MCP error -32601: Method not found failed to get prompts
```

This is expected (prompts method not implemented), but the TypeError happens later in the response processing pipeline.

---

## How to File

1. Go to: https://github.com/anomalyco/opencode/issues/new
2. Title: `MCP tool calls fail with TypeError: output.output.includes despite successful connection`
3. Copy the content above
4. Add labels: `bug`, `mcp`
