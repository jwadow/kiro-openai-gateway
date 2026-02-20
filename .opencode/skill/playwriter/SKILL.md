---
name: playwriter
description: Browser automation via Chrome extension. Single execute tool with full Playwright API. Uses your existing browser with extensions, sessions, cookies. 90% less context than traditional browser MCP.
mcp:
  playwriter:
    command: npx
    args: ["playwriter@latest"]
---

# Playwriter Browser Automation (MCP)

Control your actual Chrome browser via extension. Unlike traditional browser MCP tools that spawn isolated instances, Playwriter:

- **Uses your existing browser** - extensions, sessions, cookies all work
- **Single `execute` tool** - send Playwright code snippets directly
- **90% less context** - no tool schema bloat
- **Full Playwright API** - LLMs already know it from training
- **Bypass automation detection** - disconnect extension when needed

## Prerequisites

**You must install the Chrome extension first:**

1. Install [Playwriter Extension](https://chromewebstore.google.com/detail/playwriter-mcp/jfeammnjpkecdekppnclgkkffahnhfhe)
2. Click extension icon on tabs you want to control (icon turns green)
3. Now the skill can interact with those tabs

## Quick Start

After loading this skill:

```
# List available tabs (enabled ones)
skill_mcp(skill_name="playwriter", tool_name="listTabs")

# Execute Playwright code on a tab
skill_mcp(skill_name="playwriter", tool_name="execute", arguments='{"tabId": "tab-id-here", "code": "await page.goto(\"https://example.com\")"}')
```

## Available Tools

| Tool       | Description                      | Arguments                         |
| ---------- | -------------------------------- | --------------------------------- |
| `listTabs` | List tabs with extension enabled | `{}`                              |
| `execute`  | Run Playwright code snippet      | `{"tabId": "...", "code": "..."}` |

That's it. Two tools. The power is in the Playwright code you send.

## The `execute` Pattern

Send any valid Playwright code. The `page` object is already available:

```javascript
// Navigate
await page.goto("https://github.com");

// Click
await page.click("button.sign-in");

// Fill form
await page.fill("#email", "user@example.com");
await page.fill("#password", "secret");
await page.click('button[type="submit"]');

// Wait for element
await page.waitForSelector(".dashboard");

// Get text
const title = await page.title();

// Screenshot
await page.screenshot({ path: "/tmp/screenshot.png" });

// Complex selectors
await page.click("text=Submit");
await page.click('[data-testid="login-btn"]');

// Evaluate JS in page
const links = await page.evaluate(() =>
  Array.from(document.querySelectorAll("a")).map((a) => a.href),
);
```

## Examples

### Navigate and Screenshot

```
skill_mcp(skill_name="playwriter", tool_name="execute", arguments='{"tabId": "abc123", "code": "await page.goto(\"https://example.com\"); await page.screenshot({ path: \"/tmp/example.png\" })"}')
```

### Fill a Form

```
skill_mcp(skill_name="playwriter", tool_name="execute", arguments='{"tabId": "abc123", "code": "await page.fill(\"#name\", \"John Doe\"); await page.fill(\"#email\", \"john@example.com\"); await page.click(\"button[type=submit]\")"}')
```

### Login Flow (Using Your Saved Sessions)

```
# If you're already logged in via browser, just navigate
skill_mcp(skill_name="playwriter", tool_name="execute", arguments='{"tabId": "abc123", "code": "await page.goto(\"https://github.com/settings/profile\")"}')

# Your cookies/session already work - no login needed!
```

### Scrape Data

```
skill_mcp(skill_name="playwriter", tool_name="execute", arguments='{"tabId": "abc123", "code": "const items = await page.$$eval(\".product\", els => els.map(e => ({ name: e.querySelector(\"h2\").textContent, price: e.querySelector(\".price\").textContent }))); return items"}')
```

### Test Responsive

```
skill_mcp(skill_name="playwriter", tool_name="execute", arguments='{"tabId": "abc123", "code": "await page.setViewportSize({ width: 375, height: 667 }); await page.screenshot({ path: \"/tmp/mobile.png\" })"}')
```

## Bypassing Automation Detection

For sites that detect automation (Google login, etc.):

1. **Disconnect the extension** before sensitive actions
2. Perform login manually
3. **Reconnect** after authentication
4. Continue automation with your authenticated session

This works because the browser is real - not a Puppeteer/Playwright-spawned instance.

## vs Traditional Playwright MCP

| Aspect               | `playwright` skill      | `playwriter` skill      |
| -------------------- | ----------------------- | ----------------------- |
| Tools                | 17+                     | 2                       |
| Context usage        | High                    | ~90% less               |
| Browser              | New instance            | Your existing browser   |
| Extensions           | None                    | All yours               |
| Sessions/cookies     | Fresh                   | Your logged-in sessions |
| Automation detection | Always detected         | Can bypass              |
| API knowledge        | Must learn tool schemas | Standard Playwright     |

## Tips

- **List tabs first** to get valid tabId values
- **Chain commands** in single execute for efficiency
- **Use your sessions** - if you're logged into GitHub in Chrome, it just works
- **Return data** from execute to get values back
- **Standard Playwright docs** apply - no special syntax to learn
