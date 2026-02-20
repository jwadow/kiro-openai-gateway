import { tool } from "@opencode-ai/plugin";
import {
	type SearchIndexResult,
	getTimelineAroundObservation,
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

function formatTimelineResult(
	anchor: {
		id: number;
		type: string;
		title: string;
		created_at: string;
	} | null,
	before: SearchIndexResult[],
	after: SearchIndexResult[],
): string {
	if (!anchor) {
		return "Anchor observation not found.";
	}

	let output = "# Timeline Context\n\n";

	// Before (older observations)
	if (before.length > 0) {
		output += "## Earlier Observations\n\n";
		for (const obs of before) {
			const icon = TYPE_ICONS[obs.type] || "📝";
			const date = obs.created_at.split("T")[0];
			output += `- **#${obs.id}** ${icon} ${obs.title} _(${date})_\n`;
			if (obs.snippet) {
				output += `  ${obs.snippet.substring(0, 80)}...\n`;
			}
		}
		output += "\n";
	}

	// Anchor
	const anchorIcon = TYPE_ICONS[anchor.type] || "📝";
	const anchorDate = anchor.created_at.split("T")[0];
	output += `## ▶ Current: #${anchor.id}\n\n`;
	output += `${anchorIcon} **${anchor.title}** _(${anchorDate})_\n\n`;

	// After (newer observations)
	if (after.length > 0) {
		output += "## Later Observations\n\n";
		for (const obs of after) {
			const icon = TYPE_ICONS[obs.type] || "📝";
			const date = obs.created_at.split("T")[0];
			output += `- **#${obs.id}** ${icon} ${obs.title} _(${date})_\n`;
			if (obs.snippet) {
				output += `  ${obs.snippet.substring(0, 80)}...\n`;
			}
		}
	}

	return output;
}

export default tool({
	description: `Get chronological context around an observation.
	
	Purpose:
	- Progressive disclosure: see what was happening before/after a specific observation
	- Understand decision context over time
	- Navigate memory timeline
	
	Example:
	memory-timeline({ anchor_id: 42, depth_before: 5, depth_after: 5 })`,
	args: {
		anchor_id: tool.schema
			.number()
			.describe("ID of the observation to get context around"),
		depth_before: tool.schema
			.number()
			.optional()
			.describe("Number of earlier observations to include (default: 5)"),
		depth_after: tool.schema
			.number()
			.optional()
			.describe("Number of later observations to include (default: 5)"),
	},
	execute: async (args: {
		anchor_id: number;
		depth_before?: number;
		depth_after?: number;
	}) => {
		const { anchor, before, after } = getTimelineAroundObservation(
			args.anchor_id,
			args.depth_before ?? 5,
			args.depth_after ?? 5,
		);

		return formatTimelineResult(anchor, before, after);
	},
});
