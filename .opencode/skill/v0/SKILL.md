---
name: v0
description: AI-powered UI generation via v0 MCP. Create chats, generate React components, get design assistance. Use when building UI components, dashboards, or need AI design help.
mcp:
  v0:
    command: npx
    args: ["mcp-remote", "https://mcp.v0.dev", "--header", "Authorization: Bearer ${V0_API_KEY}"]
    env:
      V0_API_KEY: "${V0_API_KEY}"
---

# v0 AI Code Generation (MCP)

Access v0's AI-powered code generation via MCP. When this skill is loaded, the `v0` MCP server auto-starts and exposes tools for creating and managing v0 chats.

## Prerequisites

Set your v0 API key as an environment variable:

```bash
export V0_API_KEY="your-v0-api-key"
```

To get your v0 API key:

1. Go to [v0 account settings](https://v0.app/chat/settings/keys)
2. Create a new API key
3. Copy and set as environment variable

## Quick Start

After loading this skill, list available tools:

```
skill_mcp(skill_name="v0", list_tools=true)
```

Then invoke tools:

```
skill_mcp(skill_name="v0", tool_name="create_chat", arguments='{"prompt": "Create a React dashboard component with a sidebar"}')
```

## Available Tools

### create_chat

Create a new v0 chat with a prompt.

| Parameter | Type   | Required | Description                        |
| --------- | ------ | -------- | ---------------------------------- |
| `prompt`  | string | Yes      | The prompt for v0 to generate code |

**Example:**

```
skill_mcp(skill_name="v0", tool_name="create_chat", arguments='{"prompt": "Build a responsive navbar with dark mode toggle"}')
```

### get_chat

Get details about an existing chat.

| Parameter | Type   | Required | Description    |
| --------- | ------ | -------- | -------------- |
| `chatId`  | string | Yes      | The v0 chat ID |

**Example:**

```
skill_mcp(skill_name="v0", tool_name="get_chat", arguments='{"chatId": "abc123"}')
```

### find_chats

Search through your v0 chats.

| Parameter | Type   | Required | Description  |
| --------- | ------ | -------- | ------------ |
| `query`   | string | No       | Search query |

**Example:**

```
skill_mcp(skill_name="v0", tool_name="find_chats", arguments='{"query": "React components"}')
```

### send_message

Continue a conversation in an existing chat.

| Parameter | Type   | Required | Description     |
| --------- | ------ | -------- | --------------- |
| `chatId`  | string | Yes      | The v0 chat ID  |
| `message` | string | Yes      | Message to send |

**Example:**

```
skill_mcp(skill_name="v0", tool_name="send_message", arguments='{"chatId": "abc123", "message": "Add dark mode support"}')
```

## Workflow

### 1. Generate a New Component

```
# Create a new chat with your requirements
skill_mcp(skill_name="v0", tool_name="create_chat", arguments='{"prompt": "Create a modern pricing table with 3 tiers using Tailwind CSS"}')

# The response includes a chat ID and generated code
```

### 2. Iterate on Design

```
# Send follow-up messages to refine
skill_mcp(skill_name="v0", tool_name="send_message", arguments='{"chatId": "chat-id-here", "message": "Make the recommended tier more prominent with a gradient border"}')
```

### 3. Search Previous Work

```
# Find relevant previous chats
skill_mcp(skill_name="v0", tool_name="find_chats", arguments='{"query": "dashboard"}')
```

## Use Cases

- **Component Generation**: Create React/Next.js components from descriptions
- **UI Prototyping**: Rapidly prototype UI ideas
- **Design Iteration**: Refine designs through conversation
- **Code Assistance**: Get help with Tailwind CSS, responsive design, etc.

## Tips

- **Be specific** in prompts - include framework (React, Next.js), styling (Tailwind, CSS), and functionality details
- **Iterate** using `send_message` rather than creating new chats for refinements
- **Search first** with `find_chats` to reuse previous work
- **Include context** about your existing design system or component patterns

## Troubleshooting

**"Invalid API key"**: Ensure `V0_API_KEY` environment variable is set correctly.

**"Rate limit exceeded"**: v0 has usage limits. Wait a few minutes or check your plan.

**"Chat not found"**: Verify the chat ID is correct. Use `find_chats` to list available chats.
