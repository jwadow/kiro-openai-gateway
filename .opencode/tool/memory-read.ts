import { tool } from "@opencode-ai/plugin";
import { getMemoryFile } from "../plugin/lib/memory-db.js";

export default tool({
	description: `Read memory files for persistent cross-session context.
	
	Purpose:
	- Retrieve project state, learnings, and active tasks
	- Reads from SQLite database
	- Supports subdirectories: handoffs/, research/
	
	Example:
	memory-read({ file: "handoffs/2024-01-20-phase-1" })
	memory-read({ file: "research/2024-01-topic" })`,
	args: {
		file: tool.schema
			.string()
			.optional()
			.describe(
				"Memory file to read: handoffs/YYYY-MM-DD-phase, research/YYYY-MM-DD-topic",
			),
	},
	execute: async (args: { file?: string }) => {
		const fileName = args.file || "memory";

		// Normalize: strip .md extension if present
		const normalizedFile = fileName.replace(/\.md$/i, "");

		try {
			const dbRecord = getMemoryFile(normalizedFile);
			if (dbRecord) {
				const updatedInfo = dbRecord.updated_at
					? ` (updated: ${dbRecord.updated_at})`
					: "";
				return `[${normalizedFile}${updatedInfo}]\n\n${dbRecord.content}`;
			}
		} catch (error) {
			if (error instanceof Error) {
				return `Error reading memory: ${error.message}`;
			}
		}

		return `Memory file '${normalizedFile}' not found.\n\nStructure:\n- handoffs/YYYY-MM-DD-phase (phase transitions)\n- research/YYYY-MM-DD-topic (research findings)`;
	},
});
