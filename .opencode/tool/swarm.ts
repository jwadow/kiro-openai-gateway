import { execFile } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";
import { promisify } from "node:util";
import { tool } from "@opencode-ai/plugin";

const execFileAsync = promisify(execFile);

/**
 * Unified swarm orchestration tool.
 * Consolidates: swarm-plan, swarm-monitor, swarm-delegate, beads-sync
 */
export default tool({
	description: `Swarm orchestration for parallel task execution.

Operations (choose by op):
- plan: Analyze task for parallel execution
  Examples:
    swarm({ op: "plan", task: "Investigate auth failures", files: "src/auth.ts,src/api.ts" })
    swarm({ op: "plan", task: "Refactor utils" })
- monitor: Track worker progress
  Examples:
    swarm({ op: "monitor", team: "frontend", action: "status" })
    swarm({ op: "monitor", team: "frontend", action: "update", worker_id: "w1", phase: "build", progress: 60, status: "working" })
- delegate: Create delegation packet
  Examples:
    swarm({ op: "delegate", bead_id: "B-123", title: "Add caching", outcome: "Cache layer in place", checks: "lint,typecheck" })
    swarm({ op: "delegate", bead_id: "B-123", outcome: "Bug fixed", must_do: "add test", must_not: "change API" })
- sync: Bridge Beads tasks to OpenCode todos
  Examples:
    swarm({ op: "sync", action: "push", filter: "open" })
    swarm({ op: "sync", action: "pull" })

Tip: Each example only applies when the matching op is used.`,

	args: {
		op: tool.schema
			.enum(["plan", "monitor", "delegate", "sync"])
			.describe("Operation: plan, monitor, delegate, sync"),
		// Plan args
		task: tool.schema.string().optional().describe("Task description (plan)"),
		files: tool.schema
			.string()
			.optional()
			.describe("Comma-separated files (plan)"),
		// Monitor args
		team: tool.schema.string().optional().describe("Team name (monitor)"),
		action: tool.schema
			.enum(["update", "render", "status", "clear", "push", "pull"])
			.optional()
			.describe(
				"Monitor action: update, render, status, clear | Sync action: push, pull",
			),
		worker_id: tool.schema.string().optional().describe("Worker ID (monitor)"),
		phase: tool.schema.string().optional().describe("Phase name (monitor)"),
		progress: tool.schema
			.number()
			.min(0)
			.max(100)
			.optional()
			.describe("Progress 0-100 (monitor)"),
		status: tool.schema.string().optional().describe("Worker status (monitor)"),
		file: tool.schema.string().optional().describe("Current file (monitor)"),
		// Delegate args
		bead_id: tool.schema.string().optional().describe("Bead ID (delegate)"),
		title: tool.schema.string().optional().describe("Task title (delegate)"),
		outcome: tool.schema
			.string()
			.optional()
			.describe("Expected outcome (delegate)"),
		must_do: tool.schema
			.string()
			.optional()
			.describe("Must do list (delegate)"),
		must_not: tool.schema
			.string()
			.optional()
			.describe("Must not do list (delegate)"),
		checks: tool.schema
			.string()
			.optional()
			.describe("Acceptance checks (delegate)"),
		context: tool.schema
			.string()
			.optional()
			.describe("Extra context (delegate)"),
		write: tool.schema
			.boolean()
			.optional()
			.describe("Write to file (delegate)"),
		// Sync args
		filter: tool.schema
			.enum(["open", "in_progress", "all"])
			.optional()
			.describe("Filter: open, in_progress, all (sync)"),
	},

	execute: async (args, ctx) => {
		const worktree = ctx.worktree || process.cwd();

		switch (args.op) {
			case "plan":
				return planOperation(args.task || "", args.files);
			case "monitor":
				return monitorOperation(args, worktree);
			case "delegate":
				return delegateOperation(args, worktree);
			case "sync":
				return syncOperation(args, worktree);
			default:
				return `Error: Unknown operation: ${args.op}`;
		}
	},
});

// ============================================================
// PLAN OPERATION (from swarm-plan.ts)
// ============================================================

interface TaskClassification {
	type: "search" | "batch" | "writing" | "sequential" | "mixed";
	coupling: "high" | "medium" | "low";
	recommended_agents: number;
	reasoning: string;
}

function planOperation(task: string, files?: string): string {
	const fileList = files?.split(",").filter(Boolean) || [];
	const fileCount = Number.parseInt(files || "0") || fileList.length;

	const classification = classifyTask(task, fileList);
	const collapseCheck = detectSerialCollapse(
		task,
		fileCount,
		classification.recommended_agents,
	);

	let recommendation: string;
	if (collapseCheck.is_collapse) {
		recommendation = `Swarm: ${Math.min(fileCount, 5)} agents (serial collapse detected)`;
	} else if (classification.recommended_agents > 1) {
		recommendation = `Swarm: ${classification.recommended_agents} agents`;
	} else {
		recommendation = "Single agent sufficient";
	}

	return JSON.stringify(
		{
			task: task.slice(0, 100),
			file_count: fileCount,
			classification,
			serial_collapse: collapseCheck,
			recommendation,
		},
		null,
		2,
	);
}

function classifyTask(task: string, files: string[]): TaskClassification {
	const searchPatterns = /research|find|search|explore|investigate/i;
	const batchPatterns = /refactor|update|migrate|convert.*all|batch/i;
	const sequentialPatterns = /debug|fix.*issue|optimize|complex/i;

	const coupling = analyzeCoupling(files);

	if (searchPatterns.test(task)) {
		return {
			type: "search",
			coupling: "low",
			recommended_agents: Math.min(Math.max(files.length, 3), 5),
			reasoning: "Search tasks benefit from parallel exploration",
		};
	}

	if ((batchPatterns.test(task) || files.length > 3) && files.length > 0) {
		return {
			type: "batch",
			coupling,
			recommended_agents: Math.min(files.length, 8),
			reasoning: `Batch processing ${files.length} files`,
		};
	}

	if (
		sequentialPatterns.test(task) ||
		coupling === "high" ||
		files.length <= 2
	) {
		return {
			type: "sequential",
			coupling: "high",
			recommended_agents: 1,
			reasoning: "High coupling requires sequential execution",
		};
	}

	return {
		type: "mixed",
		coupling,
		recommended_agents: Math.min(files.length || 2, 4),
		reasoning: "Mixed approach with verification",
	};
}

function analyzeCoupling(files: string[]): "high" | "medium" | "low" {
	if (files.length <= 1) return "high";
	if (files.length <= 3) return "medium";
	const dirs = files.map((f) => path.dirname(f));
	const uniqueDirs = new Set(dirs);
	if (uniqueDirs.size === 1) return "high";
	if (uniqueDirs.size <= files.length / 2) return "medium";
	return "low";
}

function detectSerialCollapse(
	task: string,
	fileCount: number,
	agents: number,
): { is_collapse: boolean; warnings: string[] } {
	const warnings: string[] = [];
	if (fileCount >= 5 && agents === 1) warnings.push("Many files, single agent");
	if (/research|search/i.test(task) && agents === 1)
		warnings.push("Search with single agent");
	if (/refactor.*all|update.*all/i.test(task) && agents === 1)
		warnings.push("Batch with single agent");

	return {
		is_collapse:
			warnings.length >= 2 || (warnings.length === 1 && fileCount > 8),
		warnings,
	};
}

// ============================================================
// MONITOR OPERATION (from swarm-monitor.ts)
// ============================================================

const PROGRESS_FILE = ".beads/swarm-progress.jsonl";

interface ProgressEntry {
	timestamp: string;
	team_name: string;
	worker_id: string;
	phase: string;
	progress: number;
	status: string;
	file?: string;
}

type MonitorAction = "update" | "render" | "status" | "clear";
type SyncAction = "push" | "pull";
type SyncFilter = "open" | "in_progress" | "all";

const MONITOR_ACTIONS = new Set<MonitorAction>([
	"update",
	"render",
	"status",
	"clear",
]);

async function monitorOperation(
	args: {
		team?: string;
		action?: MonitorAction | SyncAction;
		worker_id?: string;
		phase?: string;
		progress?: number;
		status?: string;
		file?: string;
	},
	worktree: string,
): Promise<string> {
	const team = args.team || "default";
	if (args.action && !MONITOR_ACTIONS.has(args.action as MonitorAction)) {
		return `Invalid monitor action: ${args.action}`;
	}
	const action: MonitorAction = (args.action as MonitorAction) || "status";

	switch (action) {
		case "update":
			return updateProgress(
				{
					timestamp: new Date().toISOString(),
					team_name: team,
					worker_id: args.worker_id || "unknown",
					phase: args.phase || "unknown",
					progress: args.progress || 0,
					status: args.status || "idle",
					file: args.file,
				},
				worktree,
			);
		case "render":
			return renderProgress(team, worktree);
		case "status":
			return getFullStatus(team, worktree);
		case "clear":
			return clearTeam(team, worktree);
		default:
			return `Unknown action: ${action}`;
	}
}

async function updateProgress(
	entry: ProgressEntry,
	worktree: string,
): Promise<string> {
	const progressPath = path.join(worktree, PROGRESS_FILE);
	await fs.mkdir(path.dirname(progressPath), { recursive: true });
	await fs.appendFile(progressPath, `${JSON.stringify(entry)}\n`, "utf-8");
	return JSON.stringify({ success: true, record: entry }, null, 2);
}

async function getProgress(
	team: string,
	worktree: string,
): Promise<{ workers: ProgressEntry[] }> {
	const progressPath = path.join(worktree, PROGRESS_FILE);
	try {
		const content = await fs.readFile(progressPath, "utf-8");
		const entries = content
			.trim()
			.split("\n")
			.filter(Boolean)
			.map((l) => JSON.parse(l) as ProgressEntry)
			.filter((e) => e.team_name === team);
		const workerMap = new Map<string, ProgressEntry>();
		for (const e of entries) workerMap.set(e.worker_id, e);
		return { workers: Array.from(workerMap.values()) };
	} catch {
		return { workers: [] };
	}
}

async function renderProgress(team: string, worktree: string): Promise<string> {
	const { workers } = await getProgress(team, worktree);
	if (workers.length === 0) return `No progress for team: ${team}`;

	let output = `## Swarm: ${team}\n\n| Worker | Phase | Progress | Status |\n|---|---|---|---|\n`;
	for (const w of workers) {
		output += `| ${w.worker_id} | ${w.phase} | ${w.progress}% | ${w.status} |\n`;
	}
	return output;
}

async function getFullStatus(team: string, worktree: string): Promise<string> {
	const { workers } = await getProgress(team, worktree);
	return JSON.stringify(
		{
			team,
			workers: workers.length,
			completed: workers.filter((w) => w.status === "completed").length,
			working: workers.filter((w) => w.status === "working").length,
			errors: workers.filter((w) => w.status === "error").length,
			details: workers,
		},
		null,
		2,
	);
}

async function clearTeam(team: string, worktree: string): Promise<string> {
	const progressPath = path.join(worktree, PROGRESS_FILE);
	try {
		const content = await fs.readFile(progressPath, "utf-8");
		const entries = content
			.trim()
			.split("\n")
			.filter(Boolean)
			.map((l) => JSON.parse(l) as ProgressEntry);
		const other = entries.filter((e) => e.team_name !== team);
		await fs.writeFile(
			progressPath,
			other.map((e) => JSON.stringify(e)).join("\n") +
				(other.length ? "\n" : ""),
			"utf-8",
		);
		return JSON.stringify({
			success: true,
			cleared: entries.length - other.length,
		});
	} catch {
		return JSON.stringify({ success: true, cleared: 0 });
	}
}

// ============================================================
// DELEGATE OPERATION (from swarm-delegate.ts)
// ============================================================

async function delegateOperation(
	args: {
		bead_id?: string;
		title?: string;
		outcome?: string;
		must_do?: string;
		must_not?: string;
		checks?: string;
		context?: string;
		write?: boolean;
	},
	worktree: string,
): Promise<string> {
	if (!args.bead_id) return "Error: bead_id required";
	if (!args.outcome) return "Error: outcome required";

	const split = (s?: string) =>
		s
			?.split(/[,\n]/)
			.map((x) => x.trim())
			.filter(Boolean) || [];
	const bullets = (items: string[]) =>
		items.length ? items.map((i) => `- ${i}`).join("\n") : "- (none)";

	const packet = [
		"# Delegation Packet",
		"",
		`- TASK: ${args.bead_id}${args.title ? ` - ${args.title}` : ""}`,
		`- EXPECTED OUTCOME: ${args.outcome}`,
		"- MUST DO:",
		bullets(split(args.must_do)),
		"- MUST NOT DO:",
		bullets(split(args.must_not)),
		"- ACCEPTANCE CHECKS:",
		bullets(split(args.checks)),
		"- CONTEXT:",
		args.context || "(none)",
	].join("\n");

	if (!args.write) return packet;

	const artifactDir = path.join(worktree, ".beads", "artifacts", args.bead_id);
	const outPath = path.join(artifactDir, "delegation.md");

	try {
		await fs.mkdir(artifactDir, { recursive: true });
		await fs.appendFile(
			outPath,
			`\n---\nGenerated: ${new Date().toISOString()}\n---\n\n${packet}\n`,
			"utf-8",
		);
		return `✓ Delegation packet written to ${outPath}\n\n${packet}`;
	} catch (error: unknown) {
		const message = error instanceof Error ? error.message : String(error);
		return `Error writing delegation packet: ${message}`;
	}
}

// ============================================================
// SYNC OPERATION (from beads-sync.ts)
// ============================================================

const OPENCODE_TODO_DIR = path.join(
	process.env.HOME || "",
	".local",
	"share",
	"opencode",
	"storage",
	"todo",
);

interface BeadTask {
	id: string;
	title: string;
	status: string;
	priority: number;
}

async function syncOperation(
	args: { action?: MonitorAction | SyncAction; filter?: SyncFilter },
	worktree: string,
): Promise<string> {
	if (args.action && args.action !== "push" && args.action !== "pull") {
		return `Invalid sync action: ${args.action}`;
	}

	const action: SyncAction = (args.action as SyncAction) || "push";

	if (action === "push") {
		return pushBeadsToTodos(worktree, args.filter || "open");
	}
	if (action === "pull") {
		return pullTodosToBeads(worktree);
	}
	return `Unknown sync action: ${action}`;
}

async function pushBeadsToTodos(
	worktree: string,
	filter: SyncFilter,
): Promise<string> {
	try {
		const args = ["list", "--json"];
		if (filter !== "all") {
			args.push("--status", filter);
		}

		const { stdout } = await execFileAsync("br", args, {
			cwd: worktree,
			timeout: 15000,
		});

		let tasks: BeadTask[];
		try {
			tasks = JSON.parse(stdout);
		} catch {
			tasks = parseBeadListOutput(stdout);
		}

		if (tasks.length === 0) {
			return JSON.stringify({
				success: true,
				message: "No tasks to sync",
				synced: 0,
			});
		}

		const todos = tasks.map((t) => ({
			id: t.id,
			content: `[Bead] ${t.title}`,
			status:
				t.status === "closed"
					? "completed"
					: t.status === "in_progress"
						? "in_progress"
						: "pending",
			priority: t.priority <= 1 ? "high" : t.priority <= 2 ? "medium" : "low",
			beadId: t.id,
		}));

		const sessionId = `ses_${Date.now().toString(36)}_${path.basename(worktree).slice(0, 10)}`;
		const todoPath = path.join(OPENCODE_TODO_DIR, `${sessionId}.json`);

		await fs.mkdir(OPENCODE_TODO_DIR, { recursive: true });
		await fs.writeFile(todoPath, JSON.stringify(todos, null, 2), "utf-8");

		return JSON.stringify({
			success: true,
			synced: todos.length,
			session_id: sessionId,
		});
	} catch (error: unknown) {
		const message = error instanceof Error ? error.message : String(error);
		return JSON.stringify({ success: false, error: message });
	}
}

async function pullTodosToBeads(worktree: string): Promise<string> {
	// Simplified: scan todo files and close completed beads
	try {
		const files = await fs.readdir(OPENCODE_TODO_DIR).catch(() => []);
		let updated = 0;

		for (const file of files) {
			if (!file.endsWith(".json")) continue;
			const content = await fs.readFile(
				path.join(OPENCODE_TODO_DIR, file),
				"utf-8",
			);
			const todos = JSON.parse(content);

			for (const todo of todos) {
				if (todo.beadId && todo.status === "completed") {
					try {
						await execFileAsync(
							"br",
							["close", todo.beadId, "--reason", "Completed via todo"],
							{
								cwd: worktree,
								timeout: 15000,
							},
						);
						updated++;
					} catch {
						// Already closed
					}
				}
			}
		}

		return JSON.stringify({ success: true, updated });
	} catch (error: unknown) {
		const message = error instanceof Error ? error.message : String(error);
		return JSON.stringify({ success: false, error: message });
	}
}

function parseBeadListOutput(output: string): BeadTask[] {
	const lines = output.trim().split("\n").filter(Boolean);
	const tasks: BeadTask[] = [];

	for (const line of lines) {
		const match = line.match(/^#?(\S+)\s+\[(\w+)\]\s+(?:\(P(\d)\))?\s*(.+)$/);
		if (match) {
			tasks.push({
				id: match[1],
				status: match[2],
				priority: match[3] ? Number.parseInt(match[3]) : 2,
				title: match[4],
			});
		}
	}
	return tasks;
}
