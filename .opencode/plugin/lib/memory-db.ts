/**
 * Memory Database Module
 *
 * SQLite + FTS5 backend for OpenCodeKit memory system.
 * Provides fast full-text search and structured storage for observations.
 *
 * Features:
 * - WAL mode for better concurrency
 * - FTS5 for full-text search with BM25 ranking
 * - JSON1 extension for concept/file array queries
 * - Automatic schema migrations
 */

import { Database } from "bun:sqlite";
import path from "node:path";

// ============================================================================
// Types
// ============================================================================

export type ObservationType =
	| "decision"
	| "bugfix"
	| "feature"
	| "pattern"
	| "discovery"
	| "learning"
	| "warning";

export type ConfidenceLevel = "high" | "medium" | "low";

export interface ObservationRow {
	id: number;
	type: ObservationType;
	title: string;
	subtitle: string | null;
	facts: string | null; // JSON array
	narrative: string | null;
	concepts: string | null; // JSON array
	files_read: string | null; // JSON array
	files_modified: string | null; // JSON array
	confidence: ConfidenceLevel;
	bead_id: string | null;
	supersedes: number | null;
	superseded_by: number | null;
	valid_until: string | null;
	markdown_file: string | null;
	created_at: string;
	created_at_epoch: number;
	updated_at: string | null;
}

export interface ObservationInput {
	type: ObservationType;
	title: string;
	subtitle?: string;
	facts?: string[];
	narrative?: string;
	concepts?: string[];
	files_read?: string[];
	files_modified?: string[];
	confidence?: ConfidenceLevel;
	bead_id?: string;
	supersedes?: number;
	markdown_file?: string;
}

export interface SearchIndexResult {
	id: number;
	type: ObservationType;
	title: string;
	snippet: string;
	created_at: string;
	relevance_score: number;
}

export interface MemoryFileRow {
	id: number;
	file_path: string;
	content: string;
	mode: "replace" | "append";
	created_at: string;
	created_at_epoch: number;
	updated_at: string | null;
	updated_at_epoch: number | null;
}

export type ActionQueueSource = "approval" | "bead" | "worker";
export type ActionQueueStatus = "pending" | "ready" | "idle";

export interface ActionQueueItemRow {
	id: string;
	source: ActionQueueSource;
	status: ActionQueueStatus;
	title: string;
	owner: string | null;
	payload: string | null;
	created_at: string;
	created_at_epoch: number;
	updated_at: string | null;
	updated_at_epoch: number | null;
}

export interface ActionQueueItemInput {
	id: string;
	source: ActionQueueSource;
	status: ActionQueueStatus;
	title: string;
	owner?: string;
	payload?: Record<string, unknown>;
}

// ============================================================================
// Schema
// ============================================================================

const SCHEMA_VERSION = 1;

const SCHEMA_SQL = `
-- Schema versioning for migrations
CREATE TABLE IF NOT EXISTS schema_versions (
  id INTEGER PRIMARY KEY,
  version INTEGER UNIQUE NOT NULL,
  applied_at TEXT NOT NULL
);

-- Observations table (enhanced schema)
CREATE TABLE IF NOT EXISTS observations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  type TEXT NOT NULL CHECK(type IN ('decision','bugfix','feature','pattern','discovery','learning','warning')),
  title TEXT NOT NULL,
  subtitle TEXT,
  facts TEXT,
  narrative TEXT,
  concepts TEXT,
  files_read TEXT,
  files_modified TEXT,
  confidence TEXT CHECK(confidence IN ('high','medium','low')) DEFAULT 'high',
  bead_id TEXT,
  supersedes INTEGER,
  superseded_by INTEGER,
  valid_until TEXT,
  markdown_file TEXT,
  created_at TEXT NOT NULL,
  created_at_epoch INTEGER NOT NULL,
  updated_at TEXT,
  FOREIGN KEY(supersedes) REFERENCES observations(id) ON DELETE SET NULL,
  FOREIGN KEY(superseded_by) REFERENCES observations(id) ON DELETE SET NULL
);

-- FTS5 virtual table for full-text search
CREATE VIRTUAL TABLE IF NOT EXISTS observations_fts USING fts5(
  title,
  subtitle,
  narrative,
  facts,
  concepts,
  content='observations',
  content_rowid='id'
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_observations_type ON observations(type);
CREATE INDEX IF NOT EXISTS idx_observations_created ON observations(created_at_epoch DESC);
CREATE INDEX IF NOT EXISTS idx_observations_bead_id ON observations(bead_id);
CREATE INDEX IF NOT EXISTS idx_observations_superseded ON observations(superseded_by) WHERE superseded_by IS NOT NULL;

-- Memory files table (for non-observation memory files)
CREATE TABLE IF NOT EXISTS memory_files (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  file_path TEXT UNIQUE NOT NULL,
  content TEXT NOT NULL,
  mode TEXT CHECK(mode IN ('replace', 'append')) DEFAULT 'replace',
  created_at TEXT NOT NULL,
  created_at_epoch INTEGER NOT NULL,
  updated_at TEXT,
  updated_at_epoch INTEGER
);

CREATE INDEX IF NOT EXISTS idx_memory_files_path ON memory_files(file_path);

-- Action queue table for orchestration status snapshots
CREATE TABLE IF NOT EXISTS action_queue_items (
  id TEXT PRIMARY KEY,
  source TEXT NOT NULL CHECK(source IN ('approval','bead','worker')),
  status TEXT NOT NULL CHECK(status IN ('pending','ready','idle')),
  title TEXT NOT NULL,
  owner TEXT,
  payload TEXT,
  created_at TEXT NOT NULL,
  created_at_epoch INTEGER NOT NULL,
  updated_at TEXT,
  updated_at_epoch INTEGER
);

CREATE INDEX IF NOT EXISTS idx_action_queue_status ON action_queue_items(status);
CREATE INDEX IF NOT EXISTS idx_action_queue_source ON action_queue_items(source);
`;

// FTS5 sync triggers (separate because they can't use IF NOT EXISTS)
const FTS_TRIGGERS_SQL = `
-- Sync trigger for INSERT
CREATE TRIGGER IF NOT EXISTS observations_fts_ai AFTER INSERT ON observations BEGIN
  INSERT INTO observations_fts(rowid, title, subtitle, narrative, facts, concepts)
  VALUES (new.id, new.title, new.subtitle, new.narrative, new.facts, new.concepts);
END;

-- Sync trigger for DELETE
CREATE TRIGGER IF NOT EXISTS observations_fts_ad AFTER DELETE ON observations BEGIN
  INSERT INTO observations_fts(observations_fts, rowid, title, subtitle, narrative, facts, concepts)
  VALUES('delete', old.id, old.title, old.subtitle, old.narrative, old.facts, old.concepts);
END;

-- Sync trigger for UPDATE
CREATE TRIGGER IF NOT EXISTS observations_fts_au AFTER UPDATE ON observations BEGIN
  INSERT INTO observations_fts(observations_fts, rowid, title, subtitle, narrative, facts, concepts)
  VALUES('delete', old.id, old.title, old.subtitle, old.narrative, old.facts, old.concepts);
  INSERT INTO observations_fts(rowid, title, subtitle, narrative, facts, concepts)
  VALUES (new.id, new.title, new.subtitle, new.narrative, new.facts, new.concepts);
END;
`;

// ============================================================================
// Database Manager
// ============================================================================

let dbInstance: Database | null = null;

/**
 * Get or create the memory database instance.
 * Uses singleton pattern to reuse connection.
 */
export function getMemoryDB(): Database {
	if (dbInstance) return dbInstance;

	const dbPath = path.join(process.cwd(), ".opencode/memory.db");
	dbInstance = new Database(dbPath, { create: true });

	// Enable WAL mode for better concurrency
	dbInstance.run("PRAGMA journal_mode = WAL");
	dbInstance.run("PRAGMA foreign_keys = ON");

	// Initialize schema
	initializeSchema(dbInstance);

	return dbInstance;
}

/**
 * Close the database connection (for cleanup).
 */
export function closeMemoryDB(): void {
	if (dbInstance) {
		dbInstance.close();
		dbInstance = null;
	}
}

/**
 * Initialize database schema if not exists.
 */
function initializeSchema(db: Database): void {
	// Check current schema version
	try {
		const versionRow = db
			.query("SELECT MAX(version) as version FROM schema_versions")
			.get() as {
			version: number | null;
		} | null;
		const currentVersion = versionRow?.version ?? 0;

		if (currentVersion >= SCHEMA_VERSION) {
			return; // Schema is up to date
		}
	} catch {
		// schema_versions table doesn't exist, need full init
	}

	// Run schema creation
	db.exec(SCHEMA_SQL);

	// Run FTS triggers (handle if already exists)
	try {
		db.exec(FTS_TRIGGERS_SQL);
	} catch {
		// Triggers may already exist, ignore
	}

	// Record schema version
	db.run(
		"INSERT OR REPLACE INTO schema_versions (id, version, applied_at) VALUES (1, ?, ?)",
		[SCHEMA_VERSION, new Date().toISOString()],
	);
}

// ============================================================================
// Observation Operations
// ============================================================================

/**
 * Store a new observation in the database.
 */
export function storeObservation(input: ObservationInput): number {
	const db = getMemoryDB();
	const now = new Date();

	const result = db
		.query(
			`
    INSERT INTO observations (
      type, title, subtitle, facts, narrative, concepts,
      files_read, files_modified, confidence, bead_id,
      supersedes, markdown_file, created_at, created_at_epoch
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `,
		)
		.run(
			input.type,
			input.title,
			input.subtitle ?? null,
			input.facts ? JSON.stringify(input.facts) : null,
			input.narrative ?? null,
			input.concepts ? JSON.stringify(input.concepts) : null,
			input.files_read ? JSON.stringify(input.files_read) : null,
			input.files_modified ? JSON.stringify(input.files_modified) : null,
			input.confidence ?? "high",
			input.bead_id ?? null,
			input.supersedes ?? null,
			input.markdown_file ?? null,
			now.toISOString(),
			now.getTime(),
		);

	const insertedId = Number(result.lastInsertRowid);

	// Update supersedes relationship
	if (input.supersedes) {
		db.run("UPDATE observations SET superseded_by = ? WHERE id = ?", [
			insertedId,
			input.supersedes,
		]);
	}

	return insertedId;
}

/**
 * Get observation by ID.
 */
export function getObservationById(id: number): ObservationRow | null {
	const db = getMemoryDB();
	return db
		.query("SELECT * FROM observations WHERE id = ?")
		.get(id) as ObservationRow | null;
}

/**
 * Get multiple observations by IDs.
 */
export function getObservationsByIds(ids: number[]): ObservationRow[] {
	if (ids.length === 0) return [];

	const db = getMemoryDB();
	const placeholders = ids.map(() => "?").join(",");
	return db
		.query(`SELECT * FROM observations WHERE id IN (${placeholders})`)
		.all(...ids) as ObservationRow[];
}

/**
 * Search observations using FTS5.
 * Returns compact index results for progressive disclosure.
 */
export function searchObservationsFTS(
	query: string,
	options: {
		type?: ObservationType;
		concepts?: string[];
		limit?: number;
	} = {},
): SearchIndexResult[] {
	const db = getMemoryDB();
	const limit = options.limit ?? 10;

	// Build FTS5 query - escape special characters
	const ftsQuery = query
		.replace(/['"]/g, '""')
		.split(/\s+/)
		.filter((term) => term.length > 0)
		.map((term) => `"${term}"*`)
		.join(" OR ");

	if (!ftsQuery) {
		// Empty query - return recent observations
		return db
			.query(
				`
      SELECT id, type, title, 
             substr(COALESCE(narrative, ''), 1, 100) as snippet,
             created_at,
             0 as relevance_score
      FROM observations
      WHERE superseded_by IS NULL
      ${options.type ? "AND type = ?" : ""}
      ORDER BY created_at_epoch DESC
      LIMIT ?
    `,
			)
			.all(
				...(options.type ? [options.type, limit] : [limit]),
			) as SearchIndexResult[];
	}

	try {
		// Use FTS5 with BM25 ranking
		let sql = `
      SELECT o.id, o.type, o.title,
             substr(COALESCE(o.narrative, ''), 1, 100) as snippet,
             o.created_at,
             bm25(observations_fts) as relevance_score
      FROM observations o
      JOIN observations_fts fts ON fts.rowid = o.id
      WHERE observations_fts MATCH ?
        AND o.superseded_by IS NULL
    `;

		const params: (string | number)[] = [ftsQuery];

		if (options.type) {
			sql += " AND o.type = ?";
			params.push(options.type);
		}

		sql += " ORDER BY relevance_score LIMIT ?";
		params.push(limit);

		return db.query(sql).all(...params) as SearchIndexResult[];
	} catch {
		// FTS5 query failed, fallback to LIKE search
		return fallbackLikeSearch(db, query, options.type, limit);
	}
}

/**
 * Fallback search using LIKE (for when FTS5 fails).
 */
function fallbackLikeSearch(
	db: Database,
	query: string,
	type: ObservationType | undefined,
	limit: number,
): SearchIndexResult[] {
	const likePattern = `%${query}%`;

	let sql = `
    SELECT id, type, title,
           substr(COALESCE(narrative, ''), 1, 100) as snippet,
           created_at,
           0 as relevance_score
    FROM observations
    WHERE superseded_by IS NULL
      AND (title LIKE ? OR narrative LIKE ? OR concepts LIKE ?)
  `;

	const params: (string | number)[] = [likePattern, likePattern, likePattern];

	if (type) {
		sql += " AND type = ?";
		params.push(type);
	}

	sql += " ORDER BY created_at_epoch DESC LIMIT ?";
	params.push(limit);

	return db.query(sql).all(...params) as SearchIndexResult[];
}

/**
 * Get timeline around an anchor observation.
 */
export function getTimelineAroundObservation(
	anchorId: number,
	depthBefore = 5,
	depthAfter = 5,
): {
	anchor: ObservationRow | null;
	before: SearchIndexResult[];
	after: SearchIndexResult[];
} {
	const db = getMemoryDB();

	const anchor = getObservationById(anchorId);
	if (!anchor) {
		return { anchor: null, before: [], after: [] };
	}

	const before = db
		.query(
			`
    SELECT id, type, title,
           substr(COALESCE(narrative, ''), 1, 100) as snippet,
           created_at,
           0 as relevance_score
    FROM observations
    WHERE created_at_epoch < ?
      AND superseded_by IS NULL
    ORDER BY created_at_epoch DESC
    LIMIT ?
  `,
		)
		.all(anchor.created_at_epoch, depthBefore) as SearchIndexResult[];

	const after = db
		.query(
			`
    SELECT id, type, title,
           substr(COALESCE(narrative, ''), 1, 100) as snippet,
           created_at,
           0 as relevance_score
    FROM observations
    WHERE created_at_epoch > ?
      AND superseded_by IS NULL
    ORDER BY created_at_epoch ASC
    LIMIT ?
  `,
		)
		.all(anchor.created_at_epoch, depthAfter) as SearchIndexResult[];

	return {
		anchor,
		before: before.reverse(),
		after,
	};
}

/**
 * Get most recent observation.
 */
export function getMostRecentObservation(): ObservationRow | null {
	const db = getMemoryDB();
	return db
		.query(
			"SELECT * FROM observations WHERE superseded_by IS NULL ORDER BY created_at_epoch DESC LIMIT 1",
		)
		.get() as ObservationRow | null;
}

/**
 * Get observation count by type.
 */
export function getObservationStats(): Record<string, number> {
	const db = getMemoryDB();
	const rows = db
		.query(
			`
    SELECT type, COUNT(*) as count
    FROM observations
    WHERE superseded_by IS NULL
    GROUP BY type
  `,
		)
		.all() as { type: string; count: number }[];

	const stats: Record<string, number> = { total: 0 };
	for (const row of rows) {
		stats[row.type] = row.count;
		stats.total += row.count;
	}
	return stats;
}

// ============================================================================
// Memory File Operations
// ============================================================================

/**
 * Store or update a memory file.
 */
export function upsertMemoryFile(
	filePath: string,
	content: string,
	mode: "replace" | "append" = "replace",
): void {
	const db = getMemoryDB();
	const now = new Date();

	db.run(
		`
    INSERT INTO memory_files (file_path, content, mode, created_at, created_at_epoch)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(file_path) DO UPDATE SET
      content = CASE WHEN excluded.mode = 'append' THEN memory_files.content || '\n\n' || excluded.content ELSE excluded.content END,
      mode = excluded.mode,
      updated_at = ?,
      updated_at_epoch = ?
  `,
		[
			filePath,
			content,
			mode,
			now.toISOString(),
			now.getTime(),
			now.toISOString(),
			now.getTime(),
		],
	);
}

/**
 * Get a memory file by path.
 */
export function getMemoryFile(filePath: string): MemoryFileRow | null {
	const db = getMemoryDB();
	return db
		.query("SELECT * FROM memory_files WHERE file_path = ?")
		.get(filePath) as MemoryFileRow | null;
}

/**
 * Replace action queue snapshot with a new set of items.
 */
export function replaceActionQueueItems(items: ActionQueueItemInput[]): void {
	const db = getMemoryDB();
	const now = new Date();

	const insertStmt = db.query(
		`
			INSERT INTO action_queue_items
			(id, source, status, title, owner, payload, created_at, created_at_epoch)
			VALUES (?, ?, ?, ?, ?, ?, ?, ?)
			ON CONFLICT(id) DO UPDATE SET
				source = excluded.source,
				status = excluded.status,
				title = excluded.title,
				owner = excluded.owner,
				payload = excluded.payload,
				updated_at = excluded.created_at,
				updated_at_epoch = excluded.created_at_epoch
		`,
	);

	db.transaction(() => {
		db.run("DELETE FROM action_queue_items");
		for (const item of items) {
			insertStmt.run(
				item.id,
				item.source,
				item.status,
				item.title,
				item.owner ?? null,
				item.payload ? JSON.stringify(item.payload) : null,
				now.toISOString(),
				now.getTime(),
			);
		}
	})();
}

/**
 * Return action queue items, optionally filtered by status.
 */
export function listActionQueueItems(
	status?: ActionQueueStatus,
): ActionQueueItemRow[] {
	const db = getMemoryDB();
	if (!status) {
		return db
			.query(
				"SELECT * FROM action_queue_items ORDER BY created_at_epoch DESC, id ASC",
			)
			.all() as ActionQueueItemRow[];
	}

	return db
		.query(
			"SELECT * FROM action_queue_items WHERE status = ? ORDER BY created_at_epoch DESC, id ASC",
		)
		.all(status) as ActionQueueItemRow[];
}

/**
 * Clear all action queue items.
 */
export function clearActionQueueItems(): void {
	const db = getMemoryDB();
	db.run("DELETE FROM action_queue_items");
}

// ============================================================================
// FTS5 Maintenance
// ============================================================================

/**
 * Optimize FTS5 index (run periodically).
 */
export function optimizeFTS5(): void {
	const db = getMemoryDB();
	db.run("INSERT INTO observations_fts(observations_fts) VALUES('optimize')");
}

/**
 * Rebuild FTS5 index from scratch.
 */
export function rebuildFTS5(): void {
	const db = getMemoryDB();
	db.run("INSERT INTO observations_fts(observations_fts) VALUES('rebuild')");
}

/**
 * Check if FTS5 is available and working.
 */
export function checkFTS5Available(): boolean {
	try {
		const db = getMemoryDB();
		db.query("SELECT * FROM observations_fts LIMIT 1").get();
		return true;
	} catch {
		return false;
	}
}

// ============================================================================
// Database Maintenance
// ============================================================================

export interface MaintenanceStats {
	archived: number;
	vacuumed: boolean;
	checkpointed: boolean;
	prunedMarkdown: number;
	freedBytes: number;
	dbSizeBefore: number;
	dbSizeAfter: number;
}

export interface ArchiveOptions {
	/** Archive observations older than this many days (default: 90) */
	olderThanDays?: number;
	/** Archive superseded observations regardless of age */
	includeSuperseded?: boolean;
	/** Dry run - don't actually archive, just count */
	dryRun?: boolean;
}

/**
 * Archive old observations to a separate table.
 * Archived observations are removed from main table and FTS index.
 */
export function archiveOldObservations(options: ArchiveOptions = {}): number {
	const db = getMemoryDB();
	const olderThanDays = options.olderThanDays ?? 90;
	const includeSuperseded = options.includeSuperseded ?? true;
	const dryRun = options.dryRun ?? false;

	const cutoffEpoch = Date.now() - olderThanDays * 24 * 60 * 60 * 1000;

	// Create archive table if not exists
	db.run(`
		CREATE TABLE IF NOT EXISTS observations_archive (
			id INTEGER PRIMARY KEY,
			type TEXT NOT NULL,
			title TEXT NOT NULL,
			subtitle TEXT,
			facts TEXT,
			narrative TEXT,
			concepts TEXT,
			files_read TEXT,
			files_modified TEXT,
			confidence TEXT,
			bead_id TEXT,
			supersedes INTEGER,
			superseded_by INTEGER,
			valid_until TEXT,
			markdown_file TEXT,
			created_at TEXT NOT NULL,
			created_at_epoch INTEGER NOT NULL,
			updated_at TEXT,
			archived_at TEXT NOT NULL
		)
	`);

	// Build WHERE clause
	let whereClause = `created_at_epoch < ${cutoffEpoch}`;
	if (includeSuperseded) {
		whereClause = `(${whereClause} OR superseded_by IS NOT NULL)`;
	}

	// Count candidates
	const countResult = db
		.query(`SELECT COUNT(*) as count FROM observations WHERE ${whereClause}`)
		.get() as { count: number };

	if (dryRun || countResult.count === 0) {
		return countResult.count;
	}

	// Move to archive
	const now = new Date().toISOString();
	db.run(`
		INSERT INTO observations_archive
		SELECT *, '${now}' as archived_at FROM observations WHERE ${whereClause}
	`);

	// Delete from main table (triggers will remove from FTS)
	db.run(`DELETE FROM observations WHERE ${whereClause}`);

	return countResult.count;
}

/**
 * Checkpoint WAL file back to main database.
 * This reclaims space and improves read performance.
 */
export function checkpointWAL(): { walSize: number; checkpointed: boolean } {
	const db = getMemoryDB();

	try {
		// TRUNCATE mode: checkpoint and truncate WAL to zero
		const result = db.query("PRAGMA wal_checkpoint(TRUNCATE)").get() as {
			busy: number;
			log: number;
			checkpointed: number;
		};

		return {
			walSize: result.log,
			checkpointed: result.busy === 0,
		};
	} catch {
		return { walSize: 0, checkpointed: false };
	}
}

/**
 * Vacuum database to reclaim space and defragment.
 */
export function vacuumDatabase(): boolean {
	const db = getMemoryDB();
	try {
		db.run("VACUUM");
		return true;
	} catch {
		return false;
	}
}

/**
 * Get database file sizes.
 */
export function getDatabaseSizes(): {
	mainDb: number;
	wal: number;
	shm: number;
	total: number;
} {
	const db = getMemoryDB();

	try {
		const pageCount = db.query("PRAGMA page_count").get() as {
			page_count: number;
		};
		const pageSize = db.query("PRAGMA page_size").get() as {
			page_size: number;
		};
		const mainDb = pageCount.page_count * pageSize.page_size;

		// WAL and SHM sizes from pragma
		const walResult = db.query("PRAGMA wal_checkpoint").get() as {
			busy: number;
			log: number;
			checkpointed: number;
		};
		const wal = walResult.log * pageSize.page_size;

		return {
			mainDb,
			wal,
			shm: 32768, // SHM is typically 32KB
			total: mainDb + wal + 32768,
		};
	} catch {
		return { mainDb: 0, wal: 0, shm: 0, total: 0 };
	}
}

/**
 * Get list of markdown files that exist in SQLite (for pruning).
 */
export function getMarkdownFilesInSqlite(): string[] {
	const db = getMemoryDB();
	const rows = db
		.query(
			"SELECT markdown_file FROM observations WHERE markdown_file IS NOT NULL",
		)
		.all() as { markdown_file: string }[];

	return rows.map((r) => r.markdown_file);
}

/**
 * Run full maintenance cycle.
 */
export function runFullMaintenance(
	options: ArchiveOptions = {},
): MaintenanceStats {
	const sizesBefore = getDatabaseSizes();

	// 1. Archive old observations
	const archived = archiveOldObservations(options);

	// 2. Optimize FTS5
	if (!options.dryRun) {
		optimizeFTS5();
	}

	// 3. Checkpoint WAL
	let checkpointed = false;
	if (!options.dryRun) {
		const walResult = checkpointWAL();
		checkpointed = walResult.checkpointed;
	}

	// 4. Vacuum
	let vacuumed = false;
	if (!options.dryRun) {
		vacuumed = vacuumDatabase();
	}

	const sizesAfter = getDatabaseSizes();

	return {
		archived,
		vacuumed,
		checkpointed,
		prunedMarkdown: 0, // Will be set by the tool after file operations
		freedBytes: sizesBefore.total - sizesAfter.total,
		dbSizeBefore: sizesBefore.total,
		dbSizeAfter: sizesAfter.total,
	};
}
