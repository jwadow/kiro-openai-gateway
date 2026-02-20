/**
 * Memory Plugin — Database Maintenance & UX Notifications
 *
 * Handles infrastructure tasks that the agent shouldn't manage:
 * 1. FTS5 index optimization on session idle
 * 2. WAL checkpoint when file gets large
 * 3. Toast notification when observations are saved
 * 4. Toast warning on session errors
 */

import type { Plugin } from "@opencode-ai/plugin";
import {
	checkFTS5Available,
	checkpointWAL,
	getDatabaseSizes,
	optimizeFTS5,
} from "./lib/memory-db.js";

export const MemoryPlugin: Plugin = async ({ client }) => {
	const log = async (message: string, level: "info" | "warn" = "info") => {
		await client.app
			.log({
				body: { service: "memory", level, message },
			})
			.catch(() => {});
	};

	const showToast = async (
		title: string,
		message: string,
		variant: "info" | "warning" = "info",
	) => {
		try {
			await client.tui.showToast({
				body: {
					title: `Memory: ${title}`,
					message,
					variant,
					duration: variant === "warning" ? 8000 : 5000,
				},
			});
		} catch {
			// Toast API unavailable, continue silently
		}
	};

	return {
		// FTS5 optimization + WAL checkpoint on session idle
		"session.idle": async () => {
			// Optimize FTS5 index for fast search
			try {
				if (checkFTS5Available()) {
					optimizeFTS5();
					await log("FTS5 index optimized");
				}
			} catch (err) {
				const msg = err instanceof Error ? err.message : String(err);
				await log(`FTS5 optimization failed: ${msg}`, "warn");
			}

			// Checkpoint WAL if it's grown past 1MB
			try {
				const sizes = getDatabaseSizes();
				if (sizes.wal > 1024 * 1024) {
					const result = checkpointWAL();
					if (result.checkpointed) {
						await log(
							`WAL checkpointed (was ${Math.round(sizes.wal / 1024)}KB)`,
						);
					}
				}
			} catch (err) {
				const msg = err instanceof Error ? err.message : String(err);
				await log(`WAL checkpoint failed: ${msg}`, "warn");
			}
		},

		// Toast when an observation is saved
		"tool.execute.after": async (input, _output) => {
			if (input.tool === "observation") {
				await showToast("Saved", "Observation added to memory");
			}
		},

		// Warn on session errors
		"session.error": async () => {
			await showToast(
				"Session Error",
				"Consider saving important learnings with observation tool",
				"warning",
			);
		},
	};
};

export default MemoryPlugin;
