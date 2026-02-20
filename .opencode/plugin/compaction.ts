/**
 * Session Continuity Plugin (compaction-time context injection)
 *
 * Purpose:
 * - Provide compact, bounded state needed to resume work after compaction.
 * - Keep injected prompt guidance minimal and deterministic.
 *
 * Non-goals:
 * - Replace DCP policy/rules management.
 * - Inject large free-form manuals into the prompt.
 */

import { Database } from "bun:sqlite";
import { readFile, readdir, stat } from "node:fs/promises";
import path from "node:path";
import type { Plugin } from "@opencode-ai/plugin";

const MAX_SESSION_CONTEXT_CHARS = 3000;
const MAX_PROJECT_FILES = 3;
const MAX_PROJECT_FILE_CHARS = 900;
const MAX_HANDOFF_CHARS = 2500;
const MAX_BEADS = 8;
const MAX_COMBINED_CONTEXT_CHARS = 9000;

interface BeadRow {
	id: string;
	title: string;
}

function truncate(text: string, maxChars: number): string {
	if (text.length <= maxChars) return text;
	return `${text.slice(0, maxChars)}\n...[truncated]`;
}

async function safeReadFile(filePath: string): Promise<string> {
	try {
		return await readFile(filePath, "utf-8");
	} catch {
		return "";
	}
}

function renderSection(title: string, body: string): string {
	if (!body.trim()) return "";
	return `## ${title}\n${body.trim()}`;
}

async function readProjectMemoryContext(memoryDir: string): Promise<string> {
	const projectDir = path.join(memoryDir, "project");
	let names: string[] = [];
	try {
		names = (await readdir(projectDir))
			.filter((name) => name.endsWith(".md"))
			.sort()
			.slice(0, MAX_PROJECT_FILES);
	} catch {
		return "";
	}

	const chunks: string[] = [];
	for (const name of names) {
		const fullPath = path.join(projectDir, name);
		const content = (await safeReadFile(fullPath)).trim();
		if (!content) continue;
		chunks.push(
			`### ${name.replace(/\.md$/, "")}\n${truncate(content, MAX_PROJECT_FILE_CHARS)}`,
		);
	}

	return chunks.join("\n\n");
}

async function readLatestHandoff(handoffDir: string): Promise<string> {
	let names: string[] = [];
	try {
		names = (await readdir(handoffDir)).filter((name) => name.endsWith(".md"));
	} catch {
		return "";
	}

	if (names.length === 0) return "";

	const withMtime = await Promise.all(
		names.map(async (name) => {
			const fullPath = path.join(handoffDir, name);
			try {
				const info = await stat(fullPath);
				return { name, fullPath, mtimeMs: info.mtimeMs };
			} catch {
				return { name, fullPath, mtimeMs: 0 };
			}
		}),
	);

	withMtime.sort((a, b) => b.mtimeMs - a.mtimeMs);
	const latest = withMtime[0];
	const content = (await safeReadFile(latest.fullPath)).trim();
	if (!content) return "";

	return `Source: ${latest.name}\n${truncate(content, MAX_HANDOFF_CHARS)}`;
}

/**
 * Read in-progress beads directly from SQLite database.
 * Cross-platform alternative to shell command execution.
 */
function readInProgressBeads(directory: string): string {
	const dbPath = path.join(directory, ".beads", "beads.db");
	let db: Database | undefined;

	try {
		db = new Database(dbPath, { readonly: true });

		const rows = db
			.query<BeadRow, [number]>(
				"SELECT id, title FROM issues WHERE status = 'in_progress' ORDER BY updated_at DESC LIMIT ?",
			)
			.all(MAX_BEADS);

		if (rows.length === 0) return "";

		return rows.map((row) => `- ${row.id}: ${row.title}`).join("\n");
	} catch {
		// Database may not exist, be locked, or have different schema
		// Return empty string to allow graceful degradation
		return "";
	} finally {
		db?.close();
	}
}

export const CompactionPlugin: Plugin = async ({ directory }) => {
	const memoryDir = path.join(directory, ".opencode", "memory");
	const handoffDir = path.join(memoryDir, "handoffs");

	return {
		"experimental.session.compacting": async (_input, output) => {
			const sessionContext = truncate(
				(await safeReadFile(path.join(memoryDir, "session-context.md"))).trim(),
				MAX_SESSION_CONTEXT_CHARS,
			);

			const [projectContext, handoffContext] = await Promise.all([
				readProjectMemoryContext(memoryDir),
				readLatestHandoff(handoffDir),
			]);

			// Synchronous SQLite query - no async/await needed
			const beadsContext = readInProgressBeads(directory);

			const combined = [
				renderSection("Session Continuity", sessionContext),
				renderSection("Active Beads", beadsContext),
				renderSection("Previous Handoff", handoffContext),
				renderSection("Project Memory", projectContext),
			]
				.filter(Boolean)
				.join("\n\n");

			if (combined) {
				output.context.push(
					`## Session Context\n${truncate(combined, MAX_COMBINED_CONTEXT_CHARS)}\n`,
				);
			}

			output.prompt = `${output.prompt}

<compaction_task>
Summarize conversation state for reliable continuation after compaction.
</compaction_task>

<compaction_rules>
- Preserve exact IDs, file paths, and unresolved constraints.
- Distinguish completed work from current in-progress work.
- Keep summary concise and execution-focused.
- If critical context is missing, state uncertainty explicitly.
</compaction_rules>

<compaction_output>
Include:
- What was done
- What is being worked on now
- Files currently in play
- Next actions
- Persistent user constraints/preferences
</compaction_output>
`;
		},
	};
};
