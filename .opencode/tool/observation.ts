import { tool } from "@opencode-ai/plugin";
import {
	type ConfidenceLevel,
	type ObservationInput,
	type ObservationType,
	storeObservation,
} from "../plugin/lib/memory-db.js";

const TYPE_ICONS: Record<ObservationType, string> = {
	decision: "🎯",
	bugfix: "🐛",
	feature: "✨",
	pattern: "🔄",
	discovery: "💡",
	learning: "📚",
	warning: "⚠️",
};

const CONFIDENCE_ICONS: Record<ConfidenceLevel, string> = {
	high: "🟢",
	medium: "🟡",
	low: "🔴",
};

// Patterns to detect file references in observation content
const FILE_PATTERNS = [
	// file:line format (e.g., src/auth.ts:42)
	/(?:^|\s)([a-zA-Z0-9_\-./]+\.[a-zA-Z]{2,4}):(\d+)/g,
	// backtick file paths (e.g., `src/auth.ts`)
	/`([a-zA-Z0-9_\-./]+\.[a-zA-Z]{2,4})`/g,
	// common source paths
	/(?:^|\s)(src\/[a-zA-Z0-9_\-./]+\.[a-zA-Z]{2,4})/g,
	/(?:^|\s)(\.opencode\/[a-zA-Z0-9_\-./]+\.[a-zA-Z]{2,4})/g,
];

interface FileReference {
	file: string;
	line?: number;
}

// Extract file references from observation content
function extractFileReferences(content: string): FileReference[] {
	const refs: FileReference[] = [];
	const seen = new Set<string>();

	for (const pattern of FILE_PATTERNS) {
		// Reset regex state
		pattern.lastIndex = 0;
		let match = pattern.exec(content);

		while (match !== null) {
			const file = match[1];
			const line = match[2] ? Number.parseInt(match[2], 10) : undefined;
			const key = `${file}:${line || ""}`;

			if (!seen.has(key) && !file.includes("node_modules")) {
				seen.add(key);
				refs.push({ file, line });
			}
			match = pattern.exec(content);
		}
	}

	return refs;
}

export default tool({
	description: `Create a structured observation for future reference.
	
	Purpose:
	- Capture decisions, bugs, features, patterns, discoveries, learnings, or warnings
	- Auto-detects file references from content (file:line, \`path\`, src/, .opencode/)
	- Stores in SQLite with FTS5 index for fast search
	- Supports enhanced schema: facts, subtitle, files_read/files_modified
	
	Confidence guidance:
	- high: verified by tests, logs, or direct inspection (default)
	- medium: likely, but not fully verified
	- low: uncertain or speculative
	
	Type-specific examples:
	decision
	observation({
	  type: "decision",
	  title: "Use JWT for auth",
	  narrative: "Chose JWT for stateless auth across services.",
	  facts: "stateless, scalable",
	  concepts: "authentication, jwt",
	  confidence: "high"
	})
	
	bugfix
	observation({
	  type: "bugfix",
	  title: "Fix null pointer on login",
	  narrative: "Guarded optional user in src/auth.ts:42 to prevent crash.",
	  files_modified: "src/auth.ts",
	  concepts: "auth, null-check",
	  confidence: "high"
	})
	
	feature
	observation({
	  type: "feature",
	  title: "Add CLI --dry-run",
	  narrative: "Introduce dry-run mode to show planned changes without writing.",
	  files_modified: "src/commands/init.ts",
	  concepts: "cli, ux",
	  confidence: "medium"
	})
	
	pattern
	observation({
	  type: "pattern",
	  title: "Use zod for input validation",
	  narrative: "All command inputs validated with zod schemas before execute.",
	  concepts: "validation, zod",
	  confidence: "high"
	})
	
	discovery
	observation({
	  type: "discovery",
	  title: "Build copies .opencode/ to dist/template/",
	  narrative: "Found rsync step in build.ts that bundles .opencode/.",
	  files_read: "build.ts",
	  confidence: "high"
	})
	
	learning
	observation({
	  type: "learning",
	  title: "Bun test respects --watch",
	  narrative: "Observed bun test --watch keeps runner active during edits.",
	  confidence: "medium"
	})
	
	warning
	observation({
	  type: "warning",
	  title: "Do not edit dist/ directly",
	  narrative: "dist/ is built output and overwritten on build.",
	  concepts: "build, generated",
	  confidence: "high"
	})`,
	args: {
		type: tool.schema
			.string()
			.describe(
				"Observation type: decision, bugfix, feature, pattern, discovery, learning, warning",
			),
		title: tool.schema.string().describe("Brief title for the observation"),
		subtitle: tool.schema
			.string()
			.optional()
			.describe("Optional subtitle or tagline"),
		facts: tool.schema
			.string()
			.optional()
			.describe("Comma-separated key facts (e.g., 'stateless, scalable')"),
		narrative: tool.schema
			.string()
			.optional()
			.describe("Detailed observation content with context"),
		content: tool.schema
			.string()
			.optional()
			.describe(
				"DEPRECATED: Use 'narrative' instead. Alias for backward compat.",
			),
		concepts: tool.schema
			.string()
			.optional()
			.describe(
				"Comma-separated concept tags (e.g., 'authentication, oauth, security')",
			),
		files_read: tool.schema
			.string()
			.optional()
			.describe("Comma-separated files that were read (e.g., 'src/auth.ts')"),
		files_modified: tool.schema
			.string()
			.optional()
			.describe("Comma-separated files that were modified"),
		files: tool.schema
			.string()
			.optional()
			.describe(
				"DEPRECATED: Use 'files_modified' instead. Alias for backward compat.",
			),
		bead_id: tool.schema
			.string()
			.optional()
			.describe("Related bead ID for traceability"),
		confidence: tool.schema
			.string()
			.optional()
			.describe(
				"Confidence level: high (verified), medium (likely), low (uncertain). Defaults to high.",
			),
		supersedes: tool.schema
			.string()
			.optional()
			.describe(
				"ID or filename of observation this supersedes (for contradiction handling)",
			),
	},
	execute: async (args: {
		type: string;
		title: string;
		subtitle?: string;
		facts?: string;
		narrative?: string;
		content?: string;
		concepts?: string;
		files_read?: string;
		files_modified?: string;
		files?: string;
		bead_id?: string;
		confidence?: string;
		supersedes?: string;
	}) => {
		// Validate type
		const validTypes: ObservationType[] = [
			"decision",
			"bugfix",
			"feature",
			"pattern",
			"discovery",
			"learning",
			"warning",
		];
		const obsType = args.type.toLowerCase() as ObservationType;
		if (!validTypes.includes(obsType)) {
			return `Error: Invalid observation type '${args.type}'.\nValid types: ${validTypes.join(", ")}`;
		}

		// Validate confidence level
		const validConfidence: ConfidenceLevel[] = ["high", "medium", "low"];
		const confidence = (args.confidence?.toLowerCase() ||
			"high") as ConfidenceLevel;
		if (!validConfidence.includes(confidence)) {
			return `Error: Invalid confidence level '${args.confidence}'.\nValid levels: ${validConfidence.join(", ")}`;
		}

		// Handle deprecated fields (backward compat)
		const narrative = args.narrative || args.content || "";
		const filesModifiedRaw = args.files_modified || args.files || "";

		// Parse arrays from comma-separated strings
		const facts = args.facts
			? args.facts
					.split(",")
					.map((f) => f.trim())
					.filter(Boolean)
			: [];
		const concepts = args.concepts
			? args.concepts
					.split(",")
					.map((c) => c.trim())
					.filter(Boolean)
			: [];
		let filesRead = args.files_read
			? args.files_read
					.split(",")
					.map((f) => f.trim())
					.filter(Boolean)
			: [];
		const filesModified = filesModifiedRaw
			? filesModifiedRaw
					.split(",")
					.map((f) => f.trim())
					.filter(Boolean)
			: [];

		// Auto-detect file references from narrative
		const detectedRefs = extractFileReferences(narrative);
		const detectedFiles = detectedRefs.map((r) => r.file);

		// Merge detected files with explicitly provided files
		filesRead = [...new Set([...filesRead, ...detectedFiles])];

		// Parse supersedes (could be numeric ID or filename)
		let supersedesId: number | undefined;
		if (args.supersedes) {
			const parsed = Number.parseInt(args.supersedes, 10);
			if (!Number.isNaN(parsed)) {
				supersedesId = parsed;
			}
		}

		// Prepare observation input
		const input: ObservationInput = {
			type: obsType,
			title: args.title,
			subtitle: args.subtitle,
			facts: facts.length > 0 ? facts : undefined,
			narrative: narrative || undefined,
			concepts: concepts.length > 0 ? concepts : undefined,
			files_read: filesRead.length > 0 ? filesRead : undefined,
			files_modified: filesModified.length > 0 ? filesModified : undefined,
			confidence,
			bead_id: args.bead_id,
			supersedes: supersedesId,
		};

		try {
			// Store in SQLite (single source of truth)
			const sqliteId = storeObservation(input);

			// Update bead notes if bead_id provided
			let beadUpdate = "";
			if (args.bead_id) {
				try {
					const { execSync } = await import("node:child_process");
					const noteContent = `${TYPE_ICONS[obsType]} ${obsType}: ${args.title}`;
					execSync(
						`br edit ${args.bead_id} --note "${noteContent.replace(/"/g, '\\"')}"`,
						{
							cwd: process.cwd(),
							encoding: "utf-8",
							timeout: 5000,
						},
					);
					beadUpdate = `\nBead updated: ${args.bead_id}`;
				} catch {
					beadUpdate = `\nWarning: Could not update bead ${args.bead_id}`;
				}
			}

			// Build output
			const icon = TYPE_ICONS[obsType];
			const confIcon = CONFIDENCE_ICONS[confidence];

			let output = `✓ Observation #${sqliteId} saved\n\n`;
			output += `**Type**: ${icon} ${obsType}\n`;
			output += `**Title**: ${args.title}\n`;
			output += `**Confidence**: ${confIcon} ${confidence}\n`;

			if (concepts.length > 0) {
				output += `**Concepts**: ${concepts.join(", ")}\n`;
			}
			if (facts.length > 0) {
				output += `**Facts**: ${facts.length} extracted\n`;
			}

			output += beadUpdate;

			return output;
		} catch (error) {
			if (error instanceof Error) {
				return `Error saving observation: ${error.message}`;
			}
			return "Unknown error saving observation";
		}
	},
});
