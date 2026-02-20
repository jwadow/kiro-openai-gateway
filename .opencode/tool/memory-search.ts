import fs from "node:fs/promises";
import path from "node:path";
import { tool } from "@opencode-ai/plugin";
import {
	type ObservationType,
	type SearchIndexResult,
	checkFTS5Available,
	searchObservationsFTS,
} from "../plugin/lib/memory-db";

// Fallback file-based search for non-SQLite content
interface FileSearchResult {
	file: string;
	matches: { line: number; content: string }[];
}

async function searchDirectory(
	dir: string,
	pattern: RegExp,
	results: FileSearchResult[],
	baseDir: string,
): Promise<void> {
	try {
		const entries = await fs.readdir(dir, { withFileTypes: true });

		for (const entry of entries) {
			const fullPath = path.join(dir, entry.name);

			if (entry.isDirectory()) {
				// Skip hidden directories and vector_db
				if (entry.name.startsWith(".") || entry.name === "vector_db") {
					continue;
				}
				await searchDirectory(fullPath, pattern, results, baseDir);
			} else if (entry.name.endsWith(".md")) {
				const content = await fs.readFile(fullPath, "utf-8");
				const lines = content.split("\n");
				const matches: { line: number; content: string }[] = [];

				for (let index = 0; index < lines.length; index++) {
					const line = lines[index];
					if (pattern.test(line)) {
						matches.push({
							line: index + 1,
							content: line.trim().substring(0, 150),
						});
					}
				}

				if (matches.length > 0) {
					const relativePath = path.relative(baseDir, fullPath);
					results.push({ file: relativePath, matches });
				}
			}
		}
	} catch {
		// Directory doesn't exist or not readable
	}
}

async function fallbackKeywordSearch(
	query: string,
	type: string | undefined,
	limit: number,
): Promise<FileSearchResult[]> {
	const memoryDir = path.join(process.cwd(), ".opencode/memory");
	const beadsDir = path.join(process.cwd(), ".beads/artifacts");
	const globalMemoryDir = path.join(
		process.env.HOME || "",
		".config/opencode/memory",
	);

	// Create case-insensitive regex from query
	let pattern: RegExp;
	try {
		pattern = new RegExp(query, "i");
	} catch {
		// Escape special chars if not valid regex
		const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
		pattern = new RegExp(escaped, "i");
	}

	const results: FileSearchResult[] = [];

	// Handle type filtering
	if (type === "beads") {
		await searchDirectory(beadsDir, pattern, results, beadsDir);
	} else if (type && type !== "all" && type !== "observations") {
		const typeMap: Record<string, string> = {
			handoffs: "handoffs",
			research: "research",
			templates: "_templates",
		};
		const subdir = typeMap[type];
		if (subdir) {
			const searchDir = path.join(memoryDir, subdir);
			await searchDirectory(searchDir, pattern, results, memoryDir);
		}
	} else {
		// Search all: memory + beads
		await searchDirectory(memoryDir, pattern, results, memoryDir);
		await searchDirectory(beadsDir, pattern, results, beadsDir);
		await searchDirectory(globalMemoryDir, pattern, results, globalMemoryDir);
	}

	return results.slice(0, limit);
}

const TYPE_ICONS: Record<string, string> = {
	decision: "🎯",
	bugfix: "🐛",
	feature: "✨",
	pattern: "🔄",
	discovery: "💡",
	learning: "📚",
	warning: "⚠️",
};

function formatCompactIndex(
	results: SearchIndexResult[],
	query: string,
): string {
	if (results.length === 0) {
		return `No observations found for "${query}".\n\nTip: Use memory-search without query to see recent observations.`;
	}

	let output = `# Search Results: "${query}"\n\n`;
	output += `Found **${results.length}** observation(s). Use \`memory-get\` for full details.\n\n`;
	output += "| ID | Type | Title | Date |\n";
	output += "|---|---|---|---|\n";

	for (const result of results) {
		const icon = TYPE_ICONS[result.type] || "📝";
		const date = result.created_at.split("T")[0];
		const title =
			result.title.length > 50
				? `${result.title.substring(0, 47)}...`
				: result.title;
		output += `| #${result.id} | ${icon} ${result.type} | ${title} | ${date} |\n`;
	}

	output += "\n## Snippets\n\n";
	for (const result of results) {
		const icon = TYPE_ICONS[result.type] || "📝";
		output += `**#${result.id}** ${icon} ${result.title}\n`;
		if (result.snippet) {
			output += `> ${result.snippet}...\n`;
		}
		output += "\n";
	}

	output += "\n---\n";
	output += `💡 **Next steps:**\n`;
	output += `- \`memory-get({ ids: "${results
		.map((r) => r.id)
		.slice(0, 3)
		.join(",")}" })\` - Get full details\n`;
	output += `- \`memory-timeline({ anchor_id: ${results[0].id} })\` - See chronological context\n`;

	return output;
}

function formatFallbackResults(
	query: string,
	results: FileSearchResult[],
	limit: number,
): string {
	if (results.length === 0) {
		return `No matches found for "${query}" in non-observation files.`;
	}

	let output = `# File Search: "${query}"\n\n`;
	output += `Found ${results.length} file(s) with matches.\n\n`;

	for (const result of results) {
		output += `## ${result.file}\n\n`;
		const matchesToShow = result.matches.slice(0, limit);
		for (const match of matchesToShow) {
			output += `- **Line ${match.line}:** ${match.content}\n`;
		}
		if (result.matches.length > limit) {
			output += `- ... and ${result.matches.length - limit} more matches\n`;
		}
		output += "\n";
	}

	return output;
}

export default tool({
	description: `Search memory across observations and markdown archives.
	
	Purpose:
	- Fast, ranked search across all observations in SQLite (when FTS5 is available)
	- Returns compact index (~50-100 tokens per result) for progressive disclosure
	- Use memory-get for full details after identifying relevant observations
	
	FTS5 availability:
	- Auto-detected at runtime; if unavailable, observation searches fall back to file scan
	
	Search modes and hints:
	- "observations" (default): Best for decisions, bugs, learnings; uses FTS5 ranking when available
	- "handoffs": Use for past session handoffs and summaries
	- "research": Use for research notes and external findings
	- "templates": Use for memory templates and boilerplate references
	- "beads": Use for task artifacts in .beads/artifacts
	- "all": Use when you are unsure where info lives; searches SQLite + markdown + beads
	
	Example:
	memory-search({ query: "authentication" })
	memory-search({ query: "auth", type: "decision", limit: 5 })`,
	args: {
		query: tool.schema.string().describe("Search query: keywords or phrase"),
		type: tool.schema
			.string()
			.optional()
			.describe(
				"Filter by observation type (decision, bugfix, feature, pattern, discovery, learning, warning) or search scope (observations, handoffs, research, templates, beads, all)",
			),
		limit: tool.schema
			.number()
			.optional()
			.describe("Max results (default: 10)"),
	},
	execute: async (args: { query: string; type?: string; limit?: number }) => {
		const limit = args.limit || 10;

		// Determine if we should use SQLite FTS5 or fallback
		const observationTypes = [
			"decision",
			"bugfix",
			"feature",
			"pattern",
			"discovery",
			"learning",
			"warning",
		];
		const isObservationType =
			args.type && observationTypes.includes(args.type.toLowerCase());
		const isObservationsScope =
			!args.type || args.type === "observations" || isObservationType;

		// Try SQLite FTS5 for observations
		if (isObservationsScope && checkFTS5Available()) {
			try {
				const obsType = isObservationType
					? (args.type?.toLowerCase() as ObservationType)
					: undefined;
				const results = searchObservationsFTS(args.query, {
					type: obsType,
					limit,
				});
				return formatCompactIndex(results, args.query);
			} catch {
				// FTS5 failed, fall through to file search
				// Silently fall back to file-based search
			}
		}

		// Fallback to file-based search for non-observation types or FTS5 failure
		const results = await fallbackKeywordSearch(args.query, args.type, limit);
		return formatFallbackResults(args.query, results, limit);
	},
});
