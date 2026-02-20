import { tool } from "@opencode-ai/plugin";
import {
	type ObservationRow,
	getObservationsByIds,
} from "../plugin/lib/memory-db";

const TYPE_ICONS: Record<string, string> = {
	decision: "🎯",
	bugfix: "🐛",
	feature: "✨",
	pattern: "🔄",
	discovery: "💡",
	learning: "📚",
	warning: "⚠️",
};

const CONFIDENCE_ICONS: Record<string, string> = {
	high: "🟢",
	medium: "🟡",
	low: "🔴",
};

function parseJsonArray(jsonStr: string | null): string[] {
	if (!jsonStr) return [];
	try {
		return JSON.parse(jsonStr);
	} catch {
		return [];
	}
}

function formatFullObservation(obs: ObservationRow): string {
	const icon = TYPE_ICONS[obs.type] || "📝";
	const confIcon = CONFIDENCE_ICONS[obs.confidence] || "🟢";
	const date = obs.created_at.split("T")[0];

	let output = `# ${icon} #${obs.id}: ${obs.title}\n\n`;

	// Metadata
	output += `**Type**: ${obs.type} | **Confidence**: ${confIcon} ${obs.confidence} | **Created**: ${date}\n\n`;

	if (obs.subtitle) {
		output += `*${obs.subtitle}*\n\n`;
	}

	// Concepts
	const concepts = parseJsonArray(obs.concepts);
	if (concepts.length > 0) {
		output += `**Concepts**: ${concepts.join(", ")}\n\n`;
	}

	// Files
	const filesRead = parseJsonArray(obs.files_read);
	const filesModified = parseJsonArray(obs.files_modified);
	if (filesRead.length > 0) {
		output += `**Files Read**: ${filesRead.join(", ")}\n`;
	}
	if (filesModified.length > 0) {
		output += `**Files Modified**: ${filesModified.join(", ")}\n`;
	}
	if (filesRead.length > 0 || filesModified.length > 0) {
		output += "\n";
	}

	// Facts
	const facts = parseJsonArray(obs.facts);
	if (facts.length > 0) {
		output += "## Key Facts\n\n";
		for (const fact of facts) {
			output += `- ${fact}\n`;
		}
		output += "\n";
	}

	// Narrative
	if (obs.narrative) {
		output += "## Content\n\n";
		output += obs.narrative;
		output += "\n\n";
	}

	// Relationships
	if (obs.bead_id) {
		output += `**Linked Bead**: ${obs.bead_id}\n`;
	}
	if (obs.supersedes) {
		output += `**Supersedes**: #${obs.supersedes}\n`;
	}
	if (obs.superseded_by) {
		output += `⚠️ **Superseded by**: #${obs.superseded_by}\n`;
	}
	if (obs.valid_until) {
		output += `**Valid until**: ${obs.valid_until}\n`;
	}
	if (obs.markdown_file) {
		output += `**Source file**: ${obs.markdown_file}\n`;
	}

	return output;
}

export default tool({
	description: `Get full observation details by ID.
	
	Purpose:
	- Progressive disclosure: fetch full details after identifying relevant observations via search
	- Get complete narrative, facts, and metadata
	- Supports multiple IDs for batch retrieval
	
	Example:
	memory-get({ ids: "42" })           // Single observation
	memory-get({ ids: "1,5,10" })       // Multiple observations`,
	args: {
		ids: tool.schema
			.string()
			.describe("Comma-separated observation IDs to retrieve"),
	},
	execute: async (args: { ids: string }) => {
		const ids = args.ids
			.split(",")
			.map((id) => Number.parseInt(id.trim(), 10))
			.filter((id) => !Number.isNaN(id));

		if (ids.length === 0) {
			return "No valid observation IDs provided.";
		}

		const observations = getObservationsByIds(ids);

		if (observations.length === 0) {
			return `No observations found for IDs: ${args.ids}`;
		}

		let output = `# Retrieved ${observations.length} Observation(s)\n\n`;

		for (const obs of observations) {
			output += formatFullObservation(obs);
			output += "\n---\n\n";
		}

		return output;
	},
});
