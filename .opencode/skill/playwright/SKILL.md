---
name: playwright
description: Browser automation for testing, screenshots, form validation, and UX verification. Uses Playwright CLI for token-efficient automation, with MCP fallback for complex exploratory workflows.
---

# Playwright Browser Automation

Browser automation via **Playwright CLI** (primary) and **Playwright MCP** (fallback for complex workflows).

## Quick Decision

| Scenario                                            | Use     |
| --------------------------------------------------- | ------- |
| Quick screenshots, simple forms, token efficiency   | **CLI** |
| Complex exploratory testing, self-healing workflows | **MCP** |

---

## CLI Mode (Recommended)

The CLI approach is **token-efficient** - no large schemas or verbose accessibility trees in context. Best for most automation tasks.

### Installation

```bash
npm install -g @playwright/cli@latest
playwright-cli install --skills  # Optional: install for Claude/Copilot
```

### Core Workflow

```
# 1. Open browser and navigate
bash({ command: "playwright-cli open https://example.com" })

# 2. Get element refs (snapshot)
bash({ command: "playwright-cli snapshot" })

# 3. Interact using refs
bash({ command: "playwright-cli fill e12 'test@example.com'" })
bash({ command: "playwright-cli click e34" })

# 4. Screenshot
bash({ command: "playwright-cli screenshot --filename=/tmp/result.png" })
```

### Commands Reference

#### Navigation

| Command      | Description                              |
| ------------ | ---------------------------------------- |
| `open [url]` | Open browser, optionally navigate to URL |
| `goto <url>` | Navigate to URL                          |
| `close`      | Close the page/browser                   |
| `go-back`    | Go back to previous page                 |
| `go-forward` | Go forward to next page                  |
| `reload`     | Reload current page                      |

#### Interaction

| Command                    | Description                               |
| -------------------------- | ----------------------------------------- |
| `snapshot`                 | Capture page snapshot to get element refs |
| `type <text>`              | Type text into focused element            |
| `fill <ref> <text>`        | Fill text into specific element           |
| `click <ref> [button]`     | Click element (left/right/middle)         |
| `dblclick <ref>`           | Double-click element                      |
| `hover <ref>`              | Hover over element                        |
| `drag <startRef> <endRef>` | Drag and drop                             |
| `select <ref> <value>`     | Select dropdown option                    |
| `check <ref>`              | Check checkbox/radio                      |
| `uncheck <ref>`            | Uncheck checkbox                          |
| `upload <file>`            | Upload file(s)                            |

#### Keyboard

| Command         | Description                            |
| --------------- | -------------------------------------- |
| `press <key>`   | Press key (e.g., `Enter`, `ArrowLeft`) |
| `keydown <key>` | Hold key down                          |
| `keyup <key>`   | Release key                            |

#### Screenshots & PDF

| Command                              | Description                |
| ------------------------------------ | -------------------------- |
| `screenshot [ref]`                   | Screenshot page or element |
| `screenshot --filename=/tmp/out.png` | Save to specific path      |
| `pdf`                                | Save page as PDF           |
| `pdf --filename=page.pdf`            | Save PDF to specific path  |

#### Tabs

| Command              | Description    |
| -------------------- | -------------- |
| `tab-list`           | List all tabs  |
| `tab-new [url]`      | Create new tab |
| `tab-close [index]`  | Close tab      |
| `tab-select <index>` | Switch to tab  |

#### Storage

| Command                          | Description                     |
| -------------------------------- | ------------------------------- |
| `cookie-list`                    | List cookies                    |
| `cookie-get <name>`              | Get cookie value                |
| `cookie-set <name> <value>`      | Set cookie                      |
| `cookie-delete <name>`           | Delete cookie                   |
| `cookie-clear`                   | Clear all cookies               |
| `localstorage-list`              | List localStorage               |
| `localstorage-get <key>`         | Get localStorage value          |
| `localstorage-set <key> <value>` | Set localStorage                |
| `sessionstorage-*`               | Same pattern for sessionStorage |

#### Network

| Command             | Description           |
| ------------------- | --------------------- |
| `route <pattern>`   | Mock network requests |
| `route-list`        | List active routes    |
| `unroute [pattern]` | Remove route(s)       |

#### DevTools

| Command                 | Description                         |
| ----------------------- | ----------------------------------- |
| `console [min-level]`   | List console messages               |
| `network`               | List network requests               |
| `eval <func> [ref]`     | Evaluate JavaScript on page/element |
| `run-code <code>`       | Run Playwright code snippet         |
| `tracing-start`         | Start trace recording               |
| `tracing-stop`          | Stop trace recording                |
| `video-start`           | Start video recording               |
| `video-stop [filename]` | Stop video recording                |

### CLI Options

```bash
# Headless mode
playwright-cli open https://example.com --headless

# Choose browser
playwright-cli open https://example.com --browser=firefox

# Emulate device
playwright-cli open https://example.com --device="iPhone 14"

# Named session (isolated browser)
playwright-cli -s=project1 open https://example.com

# See all options
playwright-cli --help
```

### CLI Examples

#### Test Responsive Design

```typescript
// Desktop
bash({ command: "playwright-cli open http://localhost:3000" });
bash({ command: "playwright-cli resize 1920 1080" });
bash({ command: "playwright-cli screenshot --filename=/tmp/desktop.png" });

// Mobile
bash({ command: "playwright-cli resize 390 844" }); // iPhone 14
bash({ command: "playwright-cli screenshot --filename=/tmp/mobile.png" });
```

#### Fill a Form

```typescript
bash({ command: "playwright-cli open http://localhost:3000/contact" });

// Get snapshot to see element refs
bash({ command: "playwright-cli snapshot" });

// Fill using refs from snapshot output
bash({ command: "playwright-cli fill e12 'John Doe'" });
bash({ command: "playwright-cli fill e34 'john@example.com'" });
bash({ command: "playwright-cli click e56" }); // Submit button

// Wait for confirmation
bash({ command: "playwright-cli eval 'document.body.innerText.includes(\"Thank you\")'" });
```

#### Multi-Step Login Flow

```typescript
bash({ command: "playwright-cli open https://app.example.com/login" });
bash({ command: "playwright-cli snapshot" });

bash({ command: "playwright-cli fill e10 'username'" });
bash({ command: "playwright-cli fill e12 'password'" });
bash({ command: "playwright-cli click e15" });

// Verify logged in
bash({ command: "playwright-cli eval 'document.querySelector(\".dashboard\") !== null'" });
bash({ command: "playwright-cli screenshot --filename=/tmp/logged-in.png" });
```

#### Session Management

```typescript
// List all browser sessions
bash({ command: "playwright-cli list" });

// Use named session
bash({ command: "playwright-cli -s=project1 open https://example.com" });

// Close specific session
bash({ command: "playwright-cli -s=project1 close" });

// Close all browsers
bash({ command: "playwright-cli close-all" });
```

---

## MCP Mode (Fallback)

Use MCP for complex exploratory workflows or when you need persistent browser state with rich introspection.

### Tools (8 Essential)

- `browser_navigate` - Navigate to URL
- `browser_snapshot` - Get accessibility snapshot with element refs
- `browser_take_screenshot` - Capture screenshot
- `browser_click` - Click element by ref
- `browser_type` - Type text (appends)
- `browser_fill` - Fill input (clears first, then types)
- `browser_wait_for` - Wait for text or selector
- `browser_resize` - Resize viewport or emulate device

### MCP Workflow

```typescript
// Navigate
skill_mcp(
  (skill_name = "playwright"),
  (tool_name = "browser_navigate"),
  (arguments = '{"url": "https://example.com"}'),
);

// Get element refs
skill_mcp((skill_name = "playwright"), (tool_name = "browser_snapshot"));

// Interact
skill_mcp(
  (skill_name = "playwright"),
  (tool_name = "browser_click"),
  (arguments = '{"element": "Submit", "ref": "e12"}'),
);

// Screenshot
skill_mcp(
  (skill_name = "playwright"),
  (tool_name = "browser_take_screenshot"),
  (arguments = '{"filename": "/tmp/result.png"}'),
);
```

### MCP Configuration

```json
{
  "playwright": {
    "command": "npx",
    "args": ["@playwright/mcp@latest"],
    "includeTools": [
      "browser_navigate",
      "browser_snapshot",
      "browser_take_screenshot",
      "browser_click",
      "browser_type",
      "browser_fill",
      "browser_wait_for",
      "browser_resize"
    ]
  }
}
```

---

## Best Practices

1. **Default to CLI** for token efficiency
2. **Snapshot before interact** - always get element refs first
3. **Use named sessions** (`-s=`) for isolated browser contexts
4. **Save outputs to /tmp** for easy access and cleanup
5. **Check console/network** for debugging: `playwright-cli console error`
6. **Use eval for custom checks** when built-in commands aren't enough

## Troubleshooting

| Issue               | Solution                                         |
| ------------------- | ------------------------------------------------ |
| Element not found   | Re-run snapshot to get fresh refs                |
| Page not loading    | Check network with `playwright-cli network`      |
| Timing issues       | Use `eval` to check conditions before proceeding |
| Session conflicts   | Use named sessions (`-s=project1`)               |
| Browser won't close | `playwright-cli kill-all` as last resort         |

## References

- [Playwright CLI GitHub](https://github.com/microsoft/playwright-cli)
- [Playwright MCP GitHub](https://github.com/microsoft/playwright-mcp)
- [Playwright Docs](https://playwright.dev)
