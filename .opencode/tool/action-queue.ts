import { execFile } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";
import { promisify } from "node:util";
import { tool } from "@opencode-ai/plugin";
import {
	type ActionQueueItemInput,
	clearActionQueueItems,
	listActionQueueItems,
	replaceActionQueueItems,
} from "../plugin/lib/memory-db.js";

const execFileAsync = promisify(execFile);
const SWARM_PROGRESS_FILE = ".beads/swarm-progress.jsonl";

type QueueOperation = "status" | "refresh" | "clear";

interface QueueWorkerEntry {
	timestamp?: string;
	team_name?: string;
	worker_id?: string;
	phase?: string;
	progress?: number;
	status?: string;
	file?: string;
}

interface QueueBeadTask {
	id: string;
	title: string;
	status?: string;
	priority?: number;
}

function parsePayload(payload: string | null): Record<string, unknown> {
	if (!payload) return {};
	try {
		const parsed = JSON.parse(payload) as Record<string, unknown>;
		return parsed;
	} catch {
		return {};
	}
}

function buildSnapshot(
	items: ActionQueueItemInput[] | ReturnType<typeof listActionQueueItems>,
) {
	const normalized = items.map((item) => ({
		id: item.id,
		source: item.source,
		status: item.status,
		title: item.title,
		owner: item.owner ?? null,
		payload:
			"payload" in item && typeof item.payload === "string"
				? parsePayload(item.payload)
				: (item.payload ?? {}),
	}));

	const pendingApprovals = normalized.filter(
		(item) => item.source === "approval" && item.status === "pending",
	);
	const readyTasks = normalized.filter(
		(item) => item.source === "bead" && item.status === "ready",
	);
	const idleWorkers = normalized.filter(
		(item) => item.source === "worker" && item.status === "idle",
	);

	return {
		generated_at: new Date().toISOString(),
		pending_approvals: pendingApprovals,
		ready_tasks: readyTasks,
		idle_workers: idleWorkers,
		counts: {
			pending_approvals: pendingApprovals.length,
			ready_tasks: readyTasks.length,
			idle_workers: idleWorkers.length,
			total: normalized.length,
		},
	};
}

async function readReadyTasks(worktree: string): Promise<QueueBeadTask[]> {
	try {
		const { stdout } = await execFileAsync("br", ["ready", "--json"], {
			cwd: worktree,
			timeout: 15000,
		});
		const parsed = JSON.parse(stdout) as QueueBeadTask[];
		return Array.isArray(parsed) ? parsed : [];
	} catch {
		try {
			const { stdout } = await execFileAsync("br", ["ready"], {
				cwd: worktree,
				timeout: 15000,
			});
			const tasks: QueueBeadTask[] = [];
			for (const line of stdout.split("\n")) {
				const match = line.match(
					/^#?(\S+)\s+\[(\w+)\]\s+(?:\(P(\d)\))?\s*(.+)$/,
				);
				if (!match) continue;
				tasks.push({
					id: match[1],
					status: match[2],
					priority: match[3] ? Number.parseInt(match[3], 10) : 2,
					title: match[4],
				});
			}
			return tasks;
		} catch {
			return [];
		}
	}
}

async function readWorkerEntries(
	worktree: string,
): Promise<QueueWorkerEntry[]> {
	const progressPath = path.join(worktree, SWARM_PROGRESS_FILE);
	try {
		const content = await fs.readFile(progressPath, "utf-8");
		const entries = content
			.trim()
			.split("\n")
			.filter(Boolean)
			.map((line) => JSON.parse(line) as QueueWorkerEntry);

		const latestByWorker = new Map<string, QueueWorkerEntry>();
		for (const entry of entries) {
			if (!entry.worker_id) continue;
			const previous = latestByWorker.get(entry.worker_id);
			if (!previous) {
				latestByWorker.set(entry.worker_id, entry);
				continue;
			}

			const currentEpoch = Date.parse(entry.timestamp || "");
			const previousEpoch = Date.parse(previous.timestamp || "");
			if (Number.isNaN(previousEpoch) || currentEpoch >= previousEpoch) {
				latestByWorker.set(entry.worker_id, entry);
			}
		}

		return Array.from(latestByWorker.values());
	} catch {
		return [];
	}
}

function toQueueItems(
	readyTasks: QueueBeadTask[],
	workerEntries: QueueWorkerEntry[],
): ActionQueueItemInput[] {
	const items: ActionQueueItemInput[] = [];

	for (const task of readyTasks) {
		items.push({
			id: `bead:${task.id}`,
			source: "bead",
			status: "ready",
			title: task.title,
			owner: task.id,
			payload: {
				bead_id: task.id,
				priority: task.priority ?? null,
				status: task.status ?? "ready",
			},
		});
	}

	for (const worker of workerEntries) {
		const workerId = worker.worker_id || "unknown";
		const status = (worker.status || "").toLowerCase();
		const phase = (worker.phase || "").toLowerCase();
		const needsApproval =
			status.includes("approval") ||
			status === "awaiting_approval" ||
			status === "needs_approval" ||
			phase.includes("approval");

		if (status === "idle") {
			items.push({
				id: `worker:${workerId}`,
				source: "worker",
				status: "idle",
				title: `Worker ${workerId} is idle`,
				owner: workerId,
				payload: {
					phase: worker.phase || null,
					progress: worker.progress ?? null,
					file: worker.file || null,
					timestamp: worker.timestamp || null,
				},
			});
		}

		if (needsApproval) {
			items.push({
				id: `approval:${workerId}`,
				source: "approval",
				status: "pending",
				title: `Approval needed for worker ${workerId}`,
				owner: workerId,
				payload: {
					phase: worker.phase || null,
					status: worker.status || null,
					progress: worker.progress ?? null,
					file: worker.file || null,
					timestamp: worker.timestamp || null,
				},
			});
		}
	}

	return items;
}

async function refreshSnapshot(worktree: string) {
	const [readyTasks, workerEntries] = await Promise.all([
		readReadyTasks(worktree),
		readWorkerEntries(worktree),
	]);

	const items = toQueueItems(readyTasks, workerEntries);
	replaceActionQueueItems(items);

	return buildSnapshot(items);
}

export default tool({
	description: `Unified action queue for operators.

Returns a consumable queue with:
- pending approvals
- ready tasks
- idle workers

Operations with context-aware hints:
- status: Read last stored queue snapshot. Use for quick checks or when you just refreshed and want a stable view without re-scanning.
- refresh: Recompute queue from Beads + swarm progress and store snapshot. Use when work has changed (new beads, workers progressed, approvals resolved) or when status shows stale counts.
- clear: Clear stored queue snapshot. Use when you want to force a clean slate before a fresh refresh or when stale data is confusing the queue view.

Examples:
- You see pending approvals but know they were resolved: run refresh to rebuild from live worker progress.
- You want a quick glance during a long session: run status to reuse the last snapshot.
- You suspect the snapshot is corrupted or out of date: run clear, then refresh to rebuild from scratch.`,
	args: {
		op: tool.schema
			.enum(["status", "refresh", "clear"])
			.optional()
			.default("status")
			.describe("Operation: status, refresh, clear"),
	},
	execute: async (args: { op?: QueueOperation }, ctx) => {
		const op = args.op || "status";
		const worktree = ctx.worktree || process.cwd();

		if (op === "clear") {
			clearActionQueueItems();
			return JSON.stringify(
				{
					op: "clear",
					result: "ok",
					cleared: true,
					queue: buildSnapshot([]),
				},
				null,
				2,
			);
		}

		if (op === "refresh") {
			const queue = await refreshSnapshot(worktree);
			return JSON.stringify(
				{
					op: "refresh",
					result: "ok",
					queue,
				},
				null,
				2,
			);
		}

		const stored = listActionQueueItems();
		if (stored.length === 0) {
			const queue = await refreshSnapshot(worktree);
			return JSON.stringify(
				{
					op: "status",
					result: "ok",
					source: "live-refresh",
					queue,
				},
				null,
				2,
			);
		}

		return JSON.stringify(
			{
				op: "status",
				result: "ok",
				source: "snapshot",
				queue: buildSnapshot(stored),
			},
			null,
			2,
		);
	},
});
