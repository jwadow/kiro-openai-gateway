/**
 * Shared notification utilities for OpenCode plugins
 * Uses Bun's shell API ($) as recommended by official docs
 */

// Cache WSL detection result
let _isWSL: boolean | null = null;

/**
 * Check if running in WSL (cached)
 */
export function isWSL(): boolean {
  if (_isWSL !== null) return _isWSL;
  try {
    const fs = require("node:fs");
    const release = fs.readFileSync("/proc/version", "utf8").toLowerCase();
    _isWSL = release.includes("microsoft") || release.includes("wsl");
  } catch {
    _isWSL = false;
  }
  return _isWSL ?? false;
}

/**
 * Send native notification using Bun shell API
 * @param $ - Bun shell from plugin context
 * @param title - Notification title
 * @param message - Notification body
 */
export async function notify($: any, title: string, message: string): Promise<void> {
  const platform = process.platform;
  const safeTitle = title || "OpenCode";
  const safeMessage = message || "";

  try {
    if (platform === "darwin") {
      await $`osascript -e ${`display notification "${safeMessage}" with title "${safeTitle}"`}`;
    } else if (platform === "linux") {
      if (isWSL()) {
        // WSL: try notify-send, fail silently
        await $`notify-send ${safeTitle} ${safeMessage}`.catch(() => {});
      } else {
        await $`notify-send ${safeTitle} ${safeMessage}`;
      }
    } else if (platform === "win32") {
      // Windows: PowerShell toast (fire and forget)
      await $`powershell -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show('${safeMessage}', '${safeTitle}')"`.catch(
        () => {},
      );
    }
  } catch {
    // Notifications are best-effort, never throw
  }
}

/**
 * Threshold configuration for context monitoring
 */
export const THRESHOLDS = {
  MODERATE: 70,
  URGENT: 85,
  CRITICAL: 95,
} as const;

/**
 * Token statistics from session events
 */
export interface TokenStats {
  used: number;
  limit: number;
  percentage?: number;
}

/**
 * Calculate context percentage from token stats
 */
export function getContextPercentage(stats: TokenStats): number {
  if (stats.percentage) return stats.percentage;
  if (stats.limit > 0) return Math.round((stats.used / stats.limit) * 100);
  return 0;
}
