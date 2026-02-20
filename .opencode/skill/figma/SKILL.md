---
name: figma
description: Access Figma design data via Framelink MCP. Fetch layout, styles, components from Figma files/frames. Use when implementing UI from Figma designs, extracting design tokens, or downloading assets.
mcp:
  figma:
    command: npx
    args: ["-y", "figma-developer-mcp", "--stdio"]
    env:
      FIGMA_API_KEY: "${FIGMA_API_KEY}"
---

# Figma Design Data (MCP)

Access Figma design data via the Framelink MCP server. When this skill is loaded, the `figma` MCP server auto-starts and exposes tools to fetch design data and download images.

## Prerequisites

Set your Figma API key as an environment variable:

```bash
export FIGMA_API_KEY="your-figma-personal-access-token"
```

To create a Figma Personal Access Token:

1. Go to Figma → Settings → Account → Personal access tokens
2. Create a new token with read access
3. See: https://help.figma.com/hc/en-us/articles/8085703771159-Manage-personal-access-tokens

## Quick Start

After loading this skill, use `skill_mcp` to invoke Figma tools:

```
skill_mcp(skill_name="figma", tool_name="get_figma_data", arguments='{"fileKey": "abc123", "nodeId": "1234:5678"}')
```

## Available Tools

### get_figma_data

Fetch comprehensive Figma file data including layout, content, visuals, and component information.

| Parameter | Type   | Required | Description                                                                                       |
| --------- | ------ | -------- | ------------------------------------------------------------------------------------------------- |
| `fileKey` | string | Yes      | The Figma file key (from URL: `figma.com/file/<fileKey>/...` or `figma.com/design/<fileKey>/...`) |
| `nodeId`  | string | No       | Specific node ID (from URL param `node-id=<nodeId>`). Format: `1234:5678` or `1234-5678`          |
| `depth`   | number | No       | Levels deep to traverse. Only use if explicitly requested by user.                                |

**Returns:** YAML-formatted design data with:

- `metadata` - File/node information
- `nodes` - Simplified node tree with layout, styles, text content
- `globalVars` - Shared styles and variables

### download_figma_images

Download SVG and PNG images/icons from a Figma file.

| Parameter   | Type   | Required | Description                                   |
| ----------- | ------ | -------- | --------------------------------------------- |
| `fileKey`   | string | Yes      | The Figma file key                            |
| `nodes`     | array  | Yes      | Array of node objects to download (see below) |
| `localPath` | string | Yes      | Absolute path to save images                  |
| `pngScale`  | number | No       | Export scale for PNGs (default: 2)            |

**Node object structure:**

```json
{
  "nodeId": "1234:5678",
  "fileName": "icon-name.svg",
  "imageRef": "optional-for-image-fills"
}
```

## Workflow

### 1. Extract File Key and Node ID from Figma URL

Figma URLs follow these patterns:

- `https://www.figma.com/file/<fileKey>/<fileName>?node-id=<nodeId>`
- `https://www.figma.com/design/<fileKey>/<fileName>?node-id=<nodeId>`

Example: `https://www.figma.com/design/abc123xyz/MyDesign?node-id=1234-5678`

- `fileKey`: `abc123xyz`
- `nodeId`: `1234-5678` (or `1234:5678` - both formats work)

### 2. Fetch Design Data

```
# Fetch specific frame/component
skill_mcp(skill_name="figma", tool_name="get_figma_data", arguments='{"fileKey": "abc123xyz", "nodeId": "1234:5678"}')

# Fetch entire file (use sparingly - can be large)
skill_mcp(skill_name="figma", tool_name="get_figma_data", arguments='{"fileKey": "abc123xyz"}')
```

### 3. Download Assets (Optional)

```
skill_mcp(skill_name="figma", tool_name="download_figma_images", arguments='{
  "fileKey": "abc123xyz",
  "nodes": [
    {"nodeId": "1234:5678", "fileName": "hero-image.png"},
    {"nodeId": "5678:9012", "fileName": "icon-arrow.svg"}
  ],
  "localPath": "/absolute/path/to/assets"
}')
```

## Examples

### Implement a Component from Figma

```
# User provides: https://www.figma.com/design/abc123/Dashboard?node-id=100-200

# 1. Fetch the design data
skill_mcp(skill_name="figma", tool_name="get_figma_data", arguments='{"fileKey": "abc123", "nodeId": "100-200"}')

# 2. Review the returned YAML for:
#    - Layout structure (flex, grid, spacing)
#    - Typography (font, size, weight, line-height)
#    - Colors (fills, strokes)
#    - Dimensions and constraints

# 3. Implement the component using the extracted data
```

### Extract Design Tokens

```
# Fetch a design system file
skill_mcp(skill_name="figma", tool_name="get_figma_data", arguments='{"fileKey": "designSystemKey"}')

# The globalVars section contains:
# - Color styles
# - Typography styles
# - Effect styles (shadows, blurs)
```

### Download Icons

```
skill_mcp(skill_name="figma", tool_name="download_figma_images", arguments='{
  "fileKey": "iconLibraryKey",
  "nodes": [
    {"nodeId": "10:20", "fileName": "icon-home.svg"},
    {"nodeId": "10:30", "fileName": "icon-settings.svg"},
    {"nodeId": "10:40", "fileName": "icon-user.svg"}
  ],
  "localPath": "/project/src/assets/icons",
  "pngScale": 2
}')
```

## Data Structure

The `get_figma_data` tool returns simplified, AI-optimized data:

```yaml
metadata:
  name: "Component Name"
  lastModified: "2024-01-15T..."

nodes:
  - id: "1234:5678"
    name: "Button"
    type: "FRAME"
    layout:
      mode: "HORIZONTAL"
      padding: { top: 12, right: 24, bottom: 12, left: 24 }
      gap: 8
    size: { width: 120, height: 48 }
    fills:
      - type: "SOLID"
        color: { r: 0.2, g: 0.4, b: 1, a: 1 }
    cornerRadius: 8
    children:
      - id: "1234:5679"
        name: "Label"
        type: "TEXT"
        content: "Click me"
        textStyle:
          fontFamily: "Inter"
          fontSize: 16
          fontWeight: 600

globalVars:
  styles:
    "S:abc123": { name: "Primary", fills: [...] }
```

## Tips

- **Always use nodeId** when provided - fetching entire files is slow and context-heavy
- **Node IDs with `-` or `:`** both work - the MCP handles conversion
- **Check globalVars** for reusable styles before hardcoding values
- **Use depth parameter sparingly** - only when explicitly needed
- **For images/icons**, identify nodes with `imageRef` in the data for proper downloading
- **SVG vs PNG**: Use `.svg` for icons/vectors, `.png` for photos/complex images

## Troubleshooting

**"Invalid API key"**: Ensure `FIGMA_API_KEY` environment variable is set correctly.

**"File not found"**: Verify the fileKey is correct and you have access to the file.

**"Node not found"**: Check the nodeId format. Try both `1234:5678` and `1234-5678`.

**Large response**: Use `nodeId` to fetch specific frames instead of entire files.
