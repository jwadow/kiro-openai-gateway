/**
 * Swarm Enforcer Plugin
 *
 * Beads is the single source of truth for the swarm board.
 * This plugin provides non-intrusive enforcement:
 * - System prompt injection with active beads state (via experimental.chat.system.transform)
 * - Workflow stage tracking: /create → /start → /ship (enforced order)
 * - Toast warning when code is edited without a claimed task
 * - Toast warning when in-progress tasks are missing prd.md
 * - Toast warning when implementation starts before /start
 * - Session-end reminder to close/sync in-progress tasks
 *
 * This plugin is intentionally non-destructive: it never runs `br update/close/sync`.
 */

import fsPromises from "node:fs/promises";
import path from "node:path";
import type { Plugin } from "@opencode-ai/plugin";

type BeadsIssue = {
	id: string;
	title?: string;
	status?: string;
	priority?: number;
	issue_type?: string;
};

/**
 * Workflow stage for a bead:
 * - "uncreated": No prd.md exists — needs `/create`
 * - "created": Has prd.md but not in_progress — needs `/start`
 * - "started": In progress with prd.md — ready for `/ship`
 * - "started-no-prd": In progress but missing prd.md — needs `/create` first
 */
type WorkflowStage = "uncreated" | "created" | "started" | "started-no-prd";

const BEADS_DIR = ".beads";
const ISSUES_FILE = "issues.jsonl";

const CODE_EXTENSIONS = [
	".ts",
	".tsx",
	".js",
	".jsx",
	".mjs",
	".cjs",
	".py",
	".go",
	".rs",
	".java",
	".c",
	".cpp",
	".h",
	".hpp",
];

function isCodeFile(filePath: string): boolean {
	return CODE_EXTENSIONS.some((ext) => filePath.endsWith(ext));
}

function isIgnoredPath(repoDir: string, filePath: string): boolean {
	const absPath = path.isAbsolute(filePath)
		? filePath
		: path.join(repoDir, filePath);
	const rel = path.relative(repoDir, absPath);

	// Outside repo: ignore
	if (rel.startsWith("..")) return true;

	const normalized = rel.replace(/\\/g, "/");
	return (
		normalized.startsWith("node_modules/") ||
		normalized.startsWith("dist/") ||
		normalized.startsWith(".beads/") ||
		normalized.startsWith(".git/")
	);
}

async function readIssuesJsonl(repoDir: string): Promise<BeadsIssue[]> {
	const issuesPath = path.join(repoDir, BEADS_DIR, ISSUES_FILE);

	let content: string;
	try {
		content = await fsPromises.readFile(issuesPath, "utf-8");
	} catch {
		return [];
	}

	const issues: BeadsIssue[] = [];
	const lines = content.split(/\r?\n/);
	for (const line of lines) {
		const trimmed = line.trim();
		if (!trimmed) continue;
		try {
			const parsed = JSON.parse(trimmed);
			if (parsed && typeof parsed.id === "string") {
				issues.push({
					id: parsed.id,
					title: typeof parsed.title === "string" ? parsed.title : undefined,
					status: typeof parsed.status === "string" ? parsed.status : undefined,
					priority:
						typeof parsed.priority === "number" ? parsed.priority : undefined,
					issue_type:
						typeof parsed.issue_type === "string"
							? parsed.issue_type
							: undefined,
				});
			}
		} catch {
			// Ignore malformed JSONL lines
		}
	}

	return issues;
}

async function artifactExists(
	repoDir: string,
	issueId: string,
	filename: string,
): Promise<boolean> {
	const filePath = path.join(
		repoDir,
		BEADS_DIR,
		"artifacts",
		issueId,
		filename,
	);
	try {
		await fsPromises.access(filePath);
		return true;
	} catch {
		return false;
	}
}

function getWorkflowStage(issue: BeadsIssue, hasPrd: boolean): WorkflowStage {
	const isInProgress = issue.status === "in_progress";

	if (isInProgress && hasPrd) return "started";
	if (isInProgress && !hasPrd) return "started-no-prd";
	if (hasPrd) return "created";
	return "uncreated";
}

type IssueWithStage = BeadsIssue & {
	stage: WorkflowStage;
	hasPrd: boolean;
	hasPlan: boolean;
};

export const SwarmEnforcer: Plugin = async ({ client, directory }) => {
	const repoDir = directory || process.cwd();
	let lastStateAt = 0;
	let cachedInProgress: IssueWithStage[] = [];
	let cachedAllActive: IssueWithStage[] = [];

	const refreshState = async () => {
		const now = Date.now();
		if (now - lastStateAt < 1500) return;
		lastStateAt = now;

		const issues = await readIssuesJsonl(repoDir);
		const active = issues.filter(
			(i) => i.status === "in_progress" || i.status === "open",
		);

		const enriched: IssueWithStage[] = [];
		for (const issue of active.slice(0, 15)) {
			const hasPrd = await artifactExists(repoDir, issue.id, "prd.md");
			const hasPlan = await artifactExists(repoDir, issue.id, "plan.md");
			const stage = getWorkflowStage(issue, hasPrd);
			enriched.push({ ...issue, stage, hasPrd, hasPlan });
		}

		cachedAllActive = enriched;
		cachedInProgress = enriched.filter((i) => i.status === "in_progress");
	};

	const showToast = async (
		title: string,
		message: string,
		variant: "info" | "warning" = "info",
	) => {
		try {
			await client.tui.showToast({
				body: {
					title,
					message,
					variant,
					duration: variant === "warning" ? 8000 : 5000,
				},
			});
		} catch {
			// If toast is unavailable, fail silently
		}
	};

	return {
		// Inject active beads state + workflow stage into system prompt
		"experimental.chat.system.transform": async (_input, output) => {
			await refreshState();

			if (cachedAllActive.length === 0) return;

			const priorityLabel = (p?: number) => {
				if (p === 0) return "P0-critical";
				if (p === 1) return "P1-high";
				if (p === 2) return "P2-normal";
				if (p === 3) return "P3-low";
				return "P?";
			};

			const stageLabel = (stage: WorkflowStage) => {
				switch (stage) {
					case "uncreated":
						return "⏳needs:/create";
					case "created":
						return "⏳needs:/start";
					case "started":
						return "✅ready:/ship";
					case "started-no-prd":
						return "⚠needs:/create→/start";
				}
			};

			const lines: string[] = [];
			lines.push("<beads-state>");
			lines.push("## Active Beads");
			lines.push("");

			// Show in-progress first, then open
			const sorted = [...cachedAllActive].sort((a, b) => {
				if (a.status === "in_progress" && b.status !== "in_progress") return -1;
				if (a.status !== "in_progress" && b.status === "in_progress") return 1;
				return 0;
			});

			for (const issue of sorted.slice(0, 7)) {
				const typeTag = issue.issue_type || "task";
				const prioTag = priorityLabel(issue.priority);
				const stage = stageLabel(issue.stage);
				const statusTag =
					issue.status === "in_progress" ? "🔧in_progress" : "📋open";
				lines.push(
					`- **${issue.id}** ${issue.title || "(untitled)"} [${typeTag} ${prioTag}] ${statusTag} ${stage}`,
				);
			}

			// Workflow enforcement warnings
			const needsCreate = cachedAllActive.filter(
				(i) => i.stage === "uncreated" || i.stage === "started-no-prd",
			);
			const needsStart = cachedAllActive.filter((i) => i.stage === "created");
			const readyToShip = cachedInProgress.filter((i) => i.stage === "started");

			lines.push("");
			lines.push("**Workflow enforcement (required order):**");
			lines.push(
				"1. `/create <description>` — creates bead + prd.md (specification)",
			);
			lines.push(
				"2. `/start <id>` — claims task, creates branch, sets in_progress",
			);
			lines.push("3. `/ship <id>` — implement, verify, review, close");
			lines.push("");
			lines.push(
				"⛔ **Do NOT implement code until `/start` has been run.** Edit code only for beads marked ✅ready:/ship.",
			);

			if (needsCreate.length > 0) {
				lines.push("");
				lines.push(
					`⚠ ${needsCreate.length} bead(s) need \`/create\`: ${needsCreate.map((i) => i.id).join(", ")}`,
				);
			}

			if (needsStart.length > 0) {
				lines.push("");
				lines.push(
					`⚠ ${needsStart.length} bead(s) have prd.md but need \`/start\`: ${needsStart.map((i) => i.id).join(", ")}`,
				);
			}

			if (readyToShip.length > 0) {
				lines.push("");
				lines.push(
					`✅ ${readyToShip.length} bead(s) ready for \`/ship\`: ${readyToShip.map((i) => i.id).join(", ")}`,
				);
			}

			lines.push("");
			lines.push("**Beads protocol reminders:**");
			lines.push(
				"- Claim before editing: `br update <id> --status in_progress`",
			);
			lines.push(
				'- When done: `br close <id> --reason="..."` → `br sync --flush-only` → git commit',
			);
			lines.push(
				'- Discovered work (>2min): `br create --title "..." --type bug|task`',
			);
			lines.push("</beads-state>");

			output.system.push(lines.join("\n"));
		},

		// Warn if code gets edited while no task is claimed / workflow not followed
		event: async ({ event }) => {
			if (event.type === "file.edited") {
				const filePath = event.properties?.file;
				if (!filePath || typeof filePath !== "string") return;
				if (isIgnoredPath(repoDir, filePath)) return;

				const absPath = path.isAbsolute(filePath)
					? filePath
					: path.join(repoDir, filePath);

				if (!isCodeFile(absPath)) return;

				await refreshState();

				// No tasks claimed at all
				if (cachedInProgress.length === 0) {
					await showToast(
						"Beads: No task claimed",
						"Run /start <id> to claim a task before editing code.",
						"warning",
					);
					return;
				}

				// Tasks in progress but none are ready for /ship
				const readyForShip = cachedInProgress.filter(
					(i) => i.stage === "started",
				);
				if (readyForShip.length === 0) {
					const notReady = cachedInProgress.filter(
						(i) => i.stage !== "started",
					);
					const ids = notReady
						.slice(0, 3)
						.map((i) => i.id)
						.join(", ");
					await showToast(
						"Beads: Workflow incomplete",
						`Task(s) ${ids} need prd.md via /create before implementing.`,
						"warning",
					);
				}
			}
		},

		// Session end reminder: close/sync if tasks still in progress
		"session.idle": async () => {
			await refreshState();
			if (cachedInProgress.length === 0) return;

			const list = cachedInProgress
				.slice(0, 5)
				.map((i) => i.id)
				.join(", ");
			await showToast(
				"Beads: Work still in progress",
				`In-progress: ${list}. Close with br close + br sync when done.`,
			);
		},
	};
};

export default SwarmEnforcer;
