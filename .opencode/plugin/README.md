# OpenCode Plugins

Plugins in this directory extend OpenCode with project-specific behavior and tools.

## Current Plugin Files

```text
plugin/
├── memory.ts           # Memory DB maintenance + observation toasts
├── sessions.ts         # Session tools (list/read/search/summarize)
├── compaction.ts       # Compaction-time context recovery injection
├── swarm-enforcer.ts   # Beads workflow enforcement and reminders
├── skill-mcp.ts        # Skill-scoped MCP bridge (skill_mcp tools)
├── copilot-auth.ts     # GitHub Copilot provider/auth integration
├── lib/
│   ├── memory-db.ts    # SQLite + FTS5 memory backend
│   └── notify.ts       # Shared notification helpers
└── sdk/                # Copilot SDK adaptation code
```

## Plugin Responsibilities

- `memory.ts`
  - Optimizes FTS5 index on idle sessions
  - Checkpoints WAL when needed
  - Shows toast feedback for observation saves and session errors

- `sessions.ts`
  - Provides custom tools: `list_sessions`, `read_session`, `search_session`, `summarize_session`

- `compaction.ts`
  - Injects session continuity context during compaction
  - Pulls memory/project/handoff context and recovery instructions

- `swarm-enforcer.ts`
  - Injects bead state and stage labels into system context
  - Warns when implementation starts without a properly started bead
  - Reminds to close/sync in-progress work on session idle

- `skill-mcp.ts`
  - Loads MCP configs from skills
  - Exposes `skill_mcp`, `skill_mcp_status`, `skill_mcp_disconnect`
  - Supports tool filtering with `includeTools`

- `copilot-auth.ts`
  - Handles GitHub Copilot OAuth/device flow
  - Adds model/provider request shaping for compatible reasoning behavior

## Notes

- `notification.ts.bak` is a backup file and not part of the active plugin set.
- Keep plugin documentation aligned with actual files in this directory.
- Prefer shared helpers in `lib/` over duplicated utilities across plugins.

## References

- OpenCode plugin docs: https://opencode.ai/docs/plugins/
- OpenCode custom tools docs: https://opencode.ai/docs/custom-tools/
