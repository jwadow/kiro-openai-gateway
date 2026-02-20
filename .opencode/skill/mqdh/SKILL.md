---
name: mqdh
description: Meta Quest Developer Hub MCP for VR/AR development. Access Meta Horizon OS docs, ADB tools, device management. Use when building Quest apps or need Meta XR documentation.
mcp:
  mqdh:
    command: "${MQDH_MCP_PATH}"
    args: []
---

# Meta Quest Developer Hub MCP

Access Meta Horizon OS development tools via the MQDH MCP server. This MCP is **bundled with the Meta Quest Developer Hub application** (v6.2.1+).

## Prerequisites

### 1. Install MQDH

Download and install Meta Quest Developer Hub v6.2.1 or later:

- **macOS**: [Download MQDH for Mac](https://developers.meta.com/horizon/documentation/android-apps/meta-quest-developer-hub)
- **Windows**: [Download MQDH for Windows](https://developers.meta.com/horizon/documentation/android-apps/meta-quest-developer-hub)

### 2. Set MCP Path Environment Variable

The MCP server is bundled with MQDH. Set the path to the MCP executable:

**macOS:**

```bash
export MQDH_MCP_PATH="/Applications/Meta Quest Developer Hub.app/Contents/Resources/mcp-server"
```

**Windows:**

```powershell
$env:MQDH_MCP_PATH = "C:\Program Files\Meta Quest Developer Hub\resources\mcp-server.exe"
```

> **Note**: Paths may vary based on your installation. Check MQDH's AI Tools settings tab for the exact path.

### 3. Alternative: Use MQDH's Built-in Setup

MQDH v6.2.1+ includes an **AI Tools settings tab** with:

- One-click install for **Cursor** and **VS Code**
- Guided setup for Claude Desktop, Gemini CLI, Android Studio
- Manual configuration export for other tools

## Quick Start

After setting up the environment variable and loading this skill:

```
skill_mcp(skill_name="mqdh", list_tools=true)
```

Then invoke tools:

```
skill_mcp(skill_name="mqdh", tool_name="fetch_meta_quest_doc", arguments='{"query": "hand tracking setup"}')
```

## Available Tools

### fetch_meta_quest_doc

Search and retrieve Meta Horizon OS documentation.

| Parameter | Type   | Required | Description                |
| --------- | ------ | -------- | -------------------------- |
| `query`   | string | Yes      | Documentation search query |

**Example:**

```
skill_mcp(skill_name="mqdh", tool_name="fetch_meta_quest_doc", arguments='{"query": "passthrough API Unity"}')
```

### get_adb_path

Get the path to the bundled ADB executable.

**Example:**

```
skill_mcp(skill_name="mqdh", tool_name="get_adb_path", arguments='{}')
```

### device_list

List connected Quest devices.

**Example:**

```
skill_mcp(skill_name="mqdh", tool_name="device_list", arguments='{}')
```

### install_apk

Install an APK to a connected Quest device.

| Parameter   | Type   | Required | Description      |
| ----------- | ------ | -------- | ---------------- |
| `apk_path`  | string | Yes      | Path to APK file |
| `device_id` | string | No       | Target device ID |

**Example:**

```
skill_mcp(skill_name="mqdh", tool_name="install_apk", arguments='{"apk_path": "/path/to/app.apk"}')
```

## Use Cases

- **Documentation Lookup**: Quickly search Meta Horizon OS docs for APIs, best practices
- **Device Management**: List devices, install APKs, manage Quest headsets
- **Development Workflow**: Integrate ADB operations into AI-assisted development
- **Troubleshooting**: Find solutions in Meta's documentation

## Workflow Examples

### 1. Look Up API Documentation

```
# Search for hand tracking documentation
skill_mcp(skill_name="mqdh", tool_name="fetch_meta_quest_doc", arguments='{"query": "hand tracking gesture detection"}')

# Search for passthrough setup
skill_mcp(skill_name="mqdh", tool_name="fetch_meta_quest_doc", arguments='{"query": "mixed reality passthrough Unity"}')
```

### 2. Device Operations

```
# List connected devices
skill_mcp(skill_name="mqdh", tool_name="device_list", arguments='{}')

# Install a build
skill_mcp(skill_name="mqdh", tool_name="install_apk", arguments='{"apk_path": "/builds/myapp.apk", "device_id": "1234567890"}')
```

## Transport

This MCP uses **STDIO** transport to communicate with the LLM agent.

## Troubleshooting

**"Command not found"**: Verify `MQDH_MCP_PATH` points to the correct executable. Check MQDH's AI Tools settings for the exact path.

**"MQDH not installed"**: Download MQDH v6.2.1+ from [Meta Developer Portal](https://developers.meta.com/horizon/documentation/android-apps/meta-quest-developer-hub).

**"Device not found"**: Ensure your Quest is connected via USB and developer mode is enabled.

**One-click setup preferred**: Use MQDH's built-in AI Tools settings tab for automatic configuration with Cursor or VS Code.

## References

- [MQDH MCP Documentation](https://developers.meta.com/horizon/documentation/unity/ts-mqdh-mcp/)
- [Install MQDH](https://developers.meta.com/horizon/documentation/android-apps/meta-quest-developer-hub)
- [Meta Horizon OS Developer Docs](https://developers.meta.com/horizon/documentation/)
