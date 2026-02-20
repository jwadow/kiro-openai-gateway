---
name: stitch
description: Google Stitch MCP for AI-powered UI design. Extract design context, generate code from designs, and create screens from descriptions. Use when working with Stitch designs and UI generation.
---

# Google Stitch MCP

Access Google Stitch UI designs directly through the Model Context Protocol.

## Overview

Stitch MCP is Google's official Model Context Protocol server for interacting with Google Stitch designs. It allows AI agents to extract design context (colors, typography, spacing), generate production-ready code from designs, and create new designs from text descriptions.

## Endpoint

**MCP Server URL**: `https://stitch.googleapis.com/mcp`

**Authentication**: Google Cloud credentials with Bearer token and project ID header

## Prerequisites

1. **Google Cloud Project** with Stitch API enabled
2. **Google Cloud CLI** (`gcloud`) installed and initialized
3. **Required IAM Roles**:
   - `roles/serviceusage.serviceUsageAdmin` (to enable the service)
   - `roles/mcp.toolUser` (to call MCP tools)

## Setup Steps

### 1. Enable Stitch API in Google Cloud

```bash
# Set your Google Cloud project
gcloud config set project PROJECT_ID

# Enable the Stitch MCP service
gcloud beta services mcp enable stitch.googleapis.com --project=PROJECT_ID
```

### 2. Get Your Access Token

```bash
# Authenticate with Google Cloud
gcloud auth login

# Get your access token
gcloud auth print-access-token
```

### 3. Set Environment Variables

```bash
# Set your Google Cloud project ID
export GOOGLE_CLOUD_PROJECT="your-project-id"

# Get and set your access token
export STITCH_ACCESS_TOKEN=$(gcloud auth print-access-token)
```

### 4. Configuration

Stitch MCP is pre-configured in `opencode.json` as a default MCP server. Once environment variables are set, restart OpenCode and the tools will be available.

## Available Tools

Once configured, the Stitch MCP exposes the following tools:

| Tool                               | Description                       |
| ---------------------------------- | --------------------------------- |
| `stitch_list_projects`             | List all your Stitch projects     |
| `stitch_create_project`            | Create a new UI design project    |
| `stitch_get_project`               | Get project details               |
| `stitch_list_screens`              | List screens in a project         |
| `stitch_get_screen`                | Get screen details with HTML code |
| `stitch_generate_screen_from_text` | Generate UI from text prompt      |

## Usage Examples

### List Projects

```typescript
stitch_list_projects({});
```

### Create a Project

```typescript
stitch_create_project({
  title: "My E-commerce App",
});
```

### Generate Screen from Text

```typescript
stitch_generate_screen_from_text({
  projectId: "my-project-123",
  prompt:
    "Create a modern login page with email and password fields, social login buttons, and a forgot password link",
  deviceType: "MOBILE",
});
```

## Troubleshooting

### "Stitch API not enabled"

```bash
gcloud beta services mcp enable stitch.googleapis.com --project=YOUR_PROJECT_ID
```

### "Authentication failed"

```bash
# Refresh your access token (expires after ~1 hour)
export STITCH_ACCESS_TOKEN=$(gcloud auth print-access-token)
# Restart OpenCode
```

### "Project not set"

```bash
gcloud config set project YOUR_PROJECT_ID
export GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
```

## Documentation

- [Google Stitch](https://stitch.withgoogle.com)
- [Stitch MCP Setup](https://stitch.withgoogle.com/docs/mcp/setup)
- [Google Cloud MCP Overview](https://docs.cloud.google.com/mcp/overview)

## Tips

- Access tokens expire after ~1 hour, refresh with `gcloud auth print-access-token`
- Use descriptive prompts for better UI generation results
- Test generated code in your target framework before production use
