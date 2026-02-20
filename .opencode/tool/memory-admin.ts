import fs from "node:fs/promises";
import path from "node:path";
import { tool } from "@opencode-ai/plugin";
import {
	type ConfidenceLevel,
	type ObservationInput,
	type ObservationType,
	archiveOldObservations,
	checkpointWAL,
	getDatabaseSizes,
	getMemoryDB,
	getObservationStats,
	rebuildFTS5,
	runFullMaintenance,
	storeObservation,
	vacuumDatabase,
} from "../plugin/lib/memory-db.js";

/**
 * Consolidated memory administration tool.
 * Operations: status, full, archive, checkpoint, vacuum, migrate
 */
export default tool({
	description: `Memory system administration: maintenance and migration.

Operations:
- "status": Storage stats and recommendations
- "full": Full maintenance cycle (archive + checkpoint + vacuum)
- "archive": Archive old observations (>90 days default)
- "checkpoint": Checkpoint WAL file
- "vacuum": Vacuum database
- "migrate": Import .opencode/memory/observations/*.md into SQLite

Example:
memory-admin({ operation: "status" })
memory-admin({ operation: "migrate", dry_run: true })`,
	args: {
		operation: tool.schema
			.string()
			.optional()
			.default("status")
			.describe(
				"Operation: status, full, archive, checkpoint, vacuum, migrate",
			),
		older_than_days: tool.schema
			.number()
			.optional()
			.default(90)
			.describe("Archive threshold in days (default: 90)"),
		dry_run: tool.schema
			.boolean()
			.optional()
			.default(false)
			.describe("Preview changes without executing"),
		force: tool.schema
			.boolean()
			.optional()
			.describe("Force re-migration of all files"),
	},
	execute: async (args: {
		operation?: string;
		older_than_days?: number;
		dry_run?: boolean;
		force?: boolean;
	}) => {
		const operation = args.operation || "status";
		const olderThanDays = args.older_than_days ?? 90;
		const dryRun = args.dry_run ?? false;

		// Helper to format bytes
		const formatBytes = (bytes: number): string => {
			if (bytes < 1024) return `${bytes} B`;
			if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
			return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
		};

		// ===== MIGRATE =====
		if (operation === "migrate") {
			return await runMigration(args.dry_run, args.force);
		}

		const results: string[] = [];

		// ===== STATUS =====
		if (operation === "status") {
			const sizes = getDatabaseSizes();
			const stats = getObservationStats();

			results.push("## Memory System Status\n");
			results.push("### Database Size");
			results.push(`- Main DB: ${formatBytes(sizes.mainDb)}`);
			results.push(`- WAL file: ${formatBytes(sizes.wal)}`);
			results.push(`- **Total: ${formatBytes(sizes.total)}**\n`);

			results.push("### Observations");
			results.push(`- Total: ${stats.total}`);
			for (const [type, count] of Object.entries(stats)) {
				if (type !== "total") {
					results.push(`- ${type}: ${count}`);
				}
			}

			const archiveCandidates = archiveOldObservations({
				olderThanDays,
				includeSuperseded: true,
				dryRun: true,
			});
			results.push(`\n### Maintenance Recommendations`);
			results.push(
				`- Archive candidates (>${olderThanDays} days): ${archiveCandidates}`,
			);
			if (sizes.wal > 1024 * 1024) {
				results.push(`- WAL checkpoint recommended (WAL > 1MB)`);
			}

			return results.join("\n");
		}

		// ===== FULL MAINTENANCE =====
		if (operation === "full") {
			results.push(
				dryRun ? "## Full Maintenance (DRY RUN)\n" : "## Full Maintenance\n",
			);

			const stats = runFullMaintenance({
				olderThanDays,
				includeSuperseded: true,
				dryRun,
			});

			results.push(`### Results`);
			results.push(`- Archived observations: ${stats.archived}`);
			results.push(`- WAL checkpointed: ${stats.checkpointed ? "Yes" : "No"}`);
			results.push(`- Database vacuumed: ${stats.vacuumed ? "Yes" : "No"}`);
			results.push(`- Space before: ${formatBytes(stats.dbSizeBefore)}`);
			results.push(`- Space after: ${formatBytes(stats.dbSizeAfter)}`);
			results.push(`- **Freed: ${formatBytes(stats.freedBytes)}**`);

			return results.join("\n");
		}

		// ===== ARCHIVE ONLY =====
		if (operation === "archive") {
			const archived = archiveOldObservations({
				olderThanDays,
				includeSuperseded: true,
				dryRun,
			});

			if (dryRun) {
				return `## Archive Preview\n\nWould archive ${archived} observations older than ${olderThanDays} days.\n\nRun without dry_run to execute.`;
			}

			return `## Archive Complete\n\nArchived ${archived} observations to observations_archive table.`;
		}

		// ===== CHECKPOINT ONLY =====
		if (operation === "checkpoint") {
			if (dryRun) {
				const sizes = getDatabaseSizes();
				return `## Checkpoint Preview\n\nWAL size: ${formatBytes(sizes.wal)}\n\nRun without dry_run to checkpoint.`;
			}

			const result = checkpointWAL();
			return `## Checkpoint Complete\n\nCheckpointed: ${result.checkpointed ? "Yes" : "No"}\nWAL pages processed: ${result.walSize}`;
		}

		// ===== VACUUM ONLY =====
		if (operation === "vacuum") {
			if (dryRun) {
				const sizes = getDatabaseSizes();
				return `## Vacuum Preview\n\nCurrent size: ${formatBytes(sizes.total)}\n\nRun without dry_run to vacuum.`;
			}

			const before = getDatabaseSizes();
			const success = vacuumDatabase();
			const after = getDatabaseSizes();

			return `## Vacuum Complete\n\nSuccess: ${success ? "Yes" : "No"}\nBefore: ${formatBytes(before.total)}\nAfter: ${formatBytes(after.total)}\nFreed: ${formatBytes(before.total - after.total)}`;
		}

		return `Unknown operation: ${operation}. Use: status, full, archive, checkpoint, vacuum, migrate`;
	},
});

// ===== MIGRATION HELPERS =====

interface ParsedObservation {
	type: ObservationType;
	title: string;
	subtitle?: string;
	facts: string[];
	narrative: string;
	concepts: string[];
	files_read: string[];
	files_modified: string[];
	confidence: ConfidenceLevel;
	bead_id?: string;
	supersedes?: string;
	markdown_file: string;
	created_at: string;
	created_at_epoch: number;
}

function parseYAML(yamlContent: string): Record<string, unknown> {
	const result: Record<string, unknown> = {};

	for (const line of yamlContent.split("\n")) {
		const match = line.match(/^(\w+):\s*(.*)$/);
		if (match) {
			const [, key, value] = match;
			if (value.startsWith("[")) {
				try {
					result[key] = JSON.parse(value);
				} catch {
					result[key] = value;
				}
			} else if (value === "null" || value === "") {
				result[key] = null;
			} else if (value.startsWith('"') && value.endsWith('"')) {
				result[key] = value.slice(1, -1);
			} else {
				result[key] = value;
			}
		}
	}

	return result;
}

function extractFacts(narrative: string): string[] {
	const facts: string[] = [];
	const lines = narrative.split("\n");

	for (const line of lines) {
		const bulletMatch = line.match(/^[-*]\s+(.+)$/);
		if (bulletMatch) {
			facts.push(bulletMatch[1].trim());
		}
	}

	return facts;
}

function parseMarkdownObservation(
	content: string,
	filename: string,
): ParsedObservation {
	const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
	if (!frontmatterMatch) {
		throw new Error(`Invalid format: ${filename} - no YAML frontmatter`);
	}

	const yaml = parseYAML(frontmatterMatch[1]);
	const narrative = frontmatterMatch[2].trim();

	const titleMatch = narrative.match(/^#\s+.+?\s+(.+)$/m);
	const title = titleMatch
		? titleMatch[1]
		: (yaml.title as string) || "Untitled";

	const validTypes: ObservationType[] = [
		"decision",
		"bugfix",
		"feature",
		"pattern",
		"discovery",
		"learning",
		"warning",
	];
	const type = (yaml.type as string)?.toLowerCase() as ObservationType;
	if (!validTypes.includes(type)) {
		throw new Error(`Invalid type '${yaml.type}' in ${filename}`);
	}

	const validConfidence: ConfidenceLevel[] = ["high", "medium", "low"];
	const confidence = ((yaml.confidence as string)?.toLowerCase() ||
		"high") as ConfidenceLevel;
	if (!validConfidence.includes(confidence)) {
		throw new Error(`Invalid confidence '${yaml.confidence}' in ${filename}`);
	}

	const createdStr = yaml.created as string;
	if (!createdStr) {
		throw new Error(`Missing created date in ${filename}`);
	}
	const createdAt = new Date(createdStr);
	if (Number.isNaN(createdAt.getTime())) {
		throw new Error(`Invalid created date '${createdStr}' in ${filename}`);
	}

	const facts = extractFacts(narrative);
	const files = (yaml.files as string[]) || [];

	return {
		type,
		title,
		subtitle: yaml.subtitle as string | undefined,
		facts,
		narrative,
		concepts: (yaml.concepts as string[]) || [],
		files_read: files,
		files_modified: files,
		confidence,
		bead_id: yaml.bead_id as string | undefined,
		supersedes: yaml.supersedes as string | undefined,
		markdown_file: filename,
		created_at: createdAt.toISOString(),
		created_at_epoch: createdAt.getTime(),
	};
}

async function runMigration(
	dryRun?: boolean,
	force?: boolean,
): Promise<string> {
	const obsDir = path.join(process.cwd(), ".opencode/memory/observations");
	const migrationMarker = path.join(obsDir, ".migrated");

	if (!force) {
		try {
			await fs.access(migrationMarker);
			const markerContent = await fs.readFile(migrationMarker, "utf-8");
			return `Migration already complete.\n\n${markerContent}\n\nUse force: true to re-migrate.`;
		} catch {
			// No marker, proceed with migration
		}
	}

	let files: string[];
	try {
		const entries = await fs.readdir(obsDir);
		files = entries.filter((f) => f.endsWith(".md") && !f.startsWith("."));
	} catch {
		return "No observations directory found at .opencode/memory/observations/";
	}

	if (files.length === 0) {
		return "No markdown files found to migrate.";
	}

	const db = getMemoryDB();
	const results: {
		migrated: string[];
		skipped: string[];
		errors: { file: string; error: string }[];
	} = {
		migrated: [],
		skipped: [],
		errors: [],
	};

	files.sort();

	for (const file of files) {
		try {
			const content = await fs.readFile(path.join(obsDir, file), "utf-8");
			const parsed = parseMarkdownObservation(content, file);

			if (dryRun) {
				results.migrated.push(
					`${file} → ${parsed.type}: ${parsed.title.substring(0, 50)}`,
				);
				continue;
			}

			const existing = db
				.query("SELECT id FROM observations WHERE markdown_file = ?")
				.get(file);

			if (existing && !force) {
				results.skipped.push(file);
				continue;
			}

			const input: ObservationInput = {
				type: parsed.type,
				title: parsed.title,
				subtitle: parsed.subtitle,
				facts: parsed.facts,
				narrative: parsed.narrative,
				concepts: parsed.concepts,
				files_read: parsed.files_read,
				files_modified: parsed.files_modified,
				confidence: parsed.confidence,
				bead_id: parsed.bead_id,
				markdown_file: file,
			};

			storeObservation(input);
			results.migrated.push(file);
		} catch (e) {
			results.errors.push({
				file,
				error: e instanceof Error ? e.message : String(e),
			});
		}
	}

	if (!dryRun && results.migrated.length > 0) {
		try {
			rebuildFTS5();
		} catch {
			// FTS5 rebuild failed, continue
		}
	}

	if (!dryRun) {
		const markerContent = [
			`Migrated ${results.migrated.length} observations on ${new Date().toISOString()}`,
			`Skipped: ${results.skipped.length}`,
			`Errors: ${results.errors.length}`,
		].join("\n");
		await fs.writeFile(migrationMarker, markerContent, "utf-8");
	}

	let output = dryRun
		? "# Migration Preview (Dry Run)\n\n"
		: "# Migration Complete\n\n";

	output += `**Total files**: ${files.length}\n`;
	output += `**Migrated**: ${results.migrated.length}\n`;
	output += `**Skipped**: ${results.skipped.length}\n`;
	output += `**Errors**: ${results.errors.length}\n\n`;

	if (results.errors.length > 0) {
		output += "## Errors\n\n";
		for (const { file, error } of results.errors) {
			output += `- **${file}**: ${error}\n`;
		}
		output += "\n";
	}

	if (dryRun && results.migrated.length > 0) {
		output += "## Files to migrate\n\n";
		for (const item of results.migrated.slice(0, 20)) {
			output += `- ${item}\n`;
		}
		if (results.migrated.length > 20) {
			output += `- ... and ${results.migrated.length - 20} more\n`;
		}
	}

	return output;
}
