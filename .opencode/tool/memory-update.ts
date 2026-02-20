import { tool } from "@opencode-ai/plugin";
import { upsertMemoryFile } from "../plugin/lib/memory-db.js";

export default tool({
	description: `Update memory files with new learnings, progress, or context.
	
	Purpose:
	- Write or append to project memory in SQLite
	- Supports subdirectories (e.g., 'research/2024-01-topic')
	- Two modes: 'replace' (overwrite) or 'append' (add to end)
	
	Example:
	memory-update({ file: "research/session-findings", content: "..." })
	memory-update({ file: "handoffs/phase-2", content: "...", mode: "append" })`,
	args: {
		file: tool.schema
			.string()
			.describe(
				"Memory file to update: handoffs/YYYY-MM-DD-phase, research/YYYY-MM-DD-topic",
			),
		content: tool.schema
			.string()
			.describe("Content to write or append to the memory file"),
		mode: tool.schema
			.string()
			.optional()
			.default("replace")
			.describe(
				"Update mode: 'replace' (overwrite file) or 'append' (add to end).",
			),
	},
	execute: async (args: { file: string; content: string; mode?: string }) => {
		// Normalize file path: strip existing .md extension
		const normalizedFile = args.file.replace(/\.md$/i, "");
		const mode = (args.mode || "replace") as "replace" | "append";

		const timestamp = new Date().toISOString();
		let finalContent: string;

		if (mode === "append") {
			finalContent = `\n\n---\n**Updated:** ${timestamp}\n\n${args.content}`;
		} else {
			// Replace mode - update timestamp placeholder if present
			finalContent = args.content.replace(
				/\*\*Last Updated:\*\* \[Timestamp\]/,
				`**Last Updated:** ${timestamp}`,
			);
		}

		try {
			// Store in SQLite (single source of truth)
			upsertMemoryFile(normalizedFile, finalContent, mode);

			const action = mode === "append" ? "Appended to" : "Updated";
			return `✓ ${action} ${normalizedFile}`;
		} catch (error) {
			if (error instanceof Error) {
				return `Error updating memory: ${error.message}`;
			}
			return "Unknown error updating memory file";
		}
	},
});
