/**
 * OpenCode Session Tools
 * Provides session browsing, searching, and context transfer
 */

import type { Plugin } from "@opencode-ai/plugin";
import { tool } from "@opencode-ai/plugin/tool";

export const SessionsPlugin: Plugin = async ({ client }) => {
	const getProjectContext = () =>
		"Project context: OpenCodeKit CLI repo; sessions often mention .opencode/ plugins, commands, memory rules, beads IDs, and Bun/TypeScript constraints.";

	const getBestPractices = () =>
		"Best practices: Prefer recent sessions, keep queries focused, and reference exact file paths or IDs found in the session.";

	return {
		"tool.definition": async (input, output) => {
			const toolID = input.toolID;
			const projectContext = getProjectContext();
			const commonBestPractices = getBestPractices();

			switch (toolID) {
				case "list_sessions": {
					output.description = `${output.description}

${projectContext}
${commonBestPractices}

Recent session examples:
list_sessions({ since: "this week", limit: 5 })
list_sessions({ since: "yesterday", limit: 3 })`;
					break;
				}
				case "read_session": {
					output.description = `${output.description}

${projectContext}
Best practices: Use "last" for most recent context; add a short focus keyword (e.g., "sessions", "plugin", "beads") to reduce noise.

Recent session examples:
read_session({ session_reference: "last" })
read_session({ session_reference: "last", focus: "sessions plugin" })`;
					break;
				}
				case "search_session": {
					output.description = `${output.description}

${projectContext}
Best practices: Start with 1-2 specific keywords, then read the top match for full context.

Recent session examples:
search_session({ query: "sessions plugin", limit: 5 })
search_session({ query: ".opencode", limit: 5 })`;
					break;
				}
				case "summarize_session": {
					output.description = `${output.description}

${projectContext}
Best practices: Summarize long sessions only after confirming the ID from list_sessions; check back later for the generated summary.

Recent session examples:
summarize_session({ session_id: "abc123" }) // from list_sessions
summarize_session({ session_id: "def456" })`;
					break;
				}
				default:
					break;
			}
		},
		tool: {
			list_sessions: tool({
				description: `List OpenCode sessions with metadata.
	
	Purpose:
	- Browse recent sessions by date
	- Returns session ID, title, and creation time
	- Default: last 20 sessions, most recent first
	
	Example:
	list_sessions({ since: "this week", limit: 10 })
	list_sessions({}) // All recent sessions`,
				args: {
					since: tool.schema
						.string()
						.optional()
						.describe(
							"Filter by date (today, yesterday, this week, or ISO date)",
						),
					limit: tool.schema
						.number()
						.optional()
						.describe("Max sessions to return (default: 20)"),
				},
				async execute(args: { since?: string; limit?: number }) {
					const result = await client.session.list();
					if (!result.data) return "No sessions found.";

					let sessions = result.data;

					// Filter by date
					if (args.since) {
						const sinceDate = parseDate(args.since);
						if (sinceDate) {
							sessions = sessions.filter((s) => {
								const created = s.time?.created
									? new Date(s.time.created)
									: null;
								return created && created >= sinceDate;
							});
						}
					}

					// Limit results
					const limited = sessions.slice(0, args.limit || 20);

					if (limited.length === 0)
						return "No sessions found matching criteria.";

					return `# Sessions\n\n${limited
						.map(
							(s) =>
								`**${s.id}** - ${s.title || "Untitled"}\n   Created: ${s.time?.created ? new Date(s.time.created).toLocaleString() : "Unknown"}`,
						)
						.join("\n\n")}`;
				},
			}),

			read_session: tool({
				description: `Read session context for handoff or reference.
	
	Purpose:
	- Retrieve full session details and messages
	- Use "last" to get most recent session
	- Optional focus keyword to filter messages
	
	Example:
	read_session({ session_reference: "last" })
	read_session({ session_reference: "abc123", focus: "auth" })`,
				args: {
					session_reference: tool.schema
						.string()
						.describe("Session ID, or 'last' for most recent session"),
					focus: tool.schema
						.string()
						.optional()
						.describe("Focus on specific topic (filters messages by keyword)"),
				},
				async execute(args: { session_reference: string; focus?: string }) {
					let sessionId = args.session_reference;

					// Handle "last" reference
					if (sessionId === "last") {
						const sessions = await client.session.list();
						if (!sessions.data?.length) return "No sessions found.";
						sessionId = sessions.data[0].id;
					}

					const session = await client.session.get({ path: { id: sessionId } });
					if (!session.data) return `Session ${sessionId} not found.`;

					const messages = await client.session.messages({
						path: { id: sessionId },
					});
					const messageData = messages.data;

					if (!messageData) return `No messages found in session ${sessionId}.`;

					let summary = `# Session: ${session.data.title || "Untitled"}\n\n`;
					summary += `**ID:** ${session.data.id}\n`;
					summary += `**Created:** ${session.data.time?.created ? new Date(session.data.time.created).toLocaleString() : "Unknown"}\n`;
					summary += `**Messages:** ${messageData.length}\n\n`;

					// Focus filtering
					if (args.focus) {
						summary += `**Focus:** ${args.focus}\n\n`;
						const focusLower = args.focus.toLowerCase();

						// Filter messages by keyword
						const relevant = messageData.filter(
							(m) =>
								m.info &&
								JSON.stringify(m.info).toLowerCase().includes(focusLower),
						);
						summary += `Found ${relevant.length} relevant messages.\n\n`;

						relevant.slice(0, 5).forEach((m, i) => {
							summary += `${i + 1}. **${m.info.role}**: `;
							const content = extractContent(m.info);
							summary += `${content.substring(0, 200)}\n\n`;
						});
					} else {
						// Show last 5 user messages
						const userMessages = messageData.filter(
							(m) => m.info?.role === "user",
						);
						summary += "## Recent User Messages\n\n";
						for (let i = 0; i < Math.min(userMessages.length, 5); i++) {
							const m = userMessages[i];
							const content = extractContent(m.info);
							summary += `${i + 1}. ${content.substring(0, 200)}\n`;
						}

						// Show last assistant message
						const assistantMessages = messageData.filter(
							(m) => m.info?.role === "assistant",
						);
						if (assistantMessages.length > 0) {
							const last = assistantMessages[assistantMessages.length - 1];
							const lastContent = extractContent(last.info);
							summary += `\n## Last Assistant Response\n\n${lastContent.substring(0, 500)}\n`;
						}
					}

					return summary;
				},
			}),

			search_session: tool({
				description: `Full-text search across session messages.
	
	Purpose:
	- Find sessions containing specific keywords
	- Searches up to 50 sessions (configurable via limit)
	- Returns match count and excerpt
	
	Example:
	search_session({ query: "authentication", limit: 5 })`,
				args: {
					query: tool.schema.string().describe("Search query text"),
					limit: tool.schema
						.number()
						.optional()
						.describe("Max results (default: 10)"),
				},
				async execute(args: { query: string; limit?: number }) {
					const sessions = await client.session.list();
					const results: string[] = [];
					let searched = 0;
					const searchLimit = args.limit || 10;

					if (!sessions.data) return "No sessions found.";

					// Search sessions until we find enough results
					for (const session of sessions.data) {
						if (results.length >= searchLimit) break;

						try {
							const messages = await client.session.messages({
								path: { id: session.id },
							});
							const messageData = messages.data;

							if (!messageData) continue;

							const matches = messageData.filter(
								(m) =>
									m.info &&
									JSON.stringify(m.info)
										.toLowerCase()
										.includes(args.query.toLowerCase()),
							);

							if (matches.length > 0) {
								const excerpt = extractContent(matches[0].info) || "";
								results.push(
									`**${session.id}** - ${session.title || "Untitled"}\n   Matches: ${matches.length}\n   Excerpt: ${excerpt.substring(0, 150)}...`,
								);
							}

							searched++;
							if (searched >= 50) break; // Don't search too many sessions
						} catch {
							// Skip inaccessible sessions
						}
					}

					if (results.length === 0)
						return `No matches found for "${args.query}" in ${searched} sessions searched.`;

					return `# Search Results: "${args.query}"\n\n${results.join("\n\n")}`;
				},
			}),

			summarize_session: tool({
				description: `Generate AI summary of a session.
	
	Purpose:
	- Request OpenCode to summarize a session
	- Summary is generated asynchronously
	- Check back for the summary result
	
	Example:
	summarize_session({ session_id: "abc123" })`,
				args: {
					session_id: tool.schema.string().describe("Session ID to summarize"),
				},
				async execute(args: { session_id: string }) {
					// Request summary via OpenCode's summarization
					await client.session.summarize({
						path: { id: args.session_id },
						body: { providerID: "proxypal", modelID: "gemini-3-flash-preview" },
					});

					return `Summarizing session ${args.session_id}... Summary will be available shortly.`;
				},
			}),
		},
	};
};

function parseDate(dateStr: string): Date | null {
	const today = new Date();
	today.setHours(0, 0, 0, 0);

	if (dateStr === "today") return today;
	if (dateStr === "yesterday") {
		const yesterday = new Date(today);
		yesterday.setDate(yesterday.getDate() - 1);
		return yesterday;
	}
	if (dateStr === "this week") {
		const weekStart = new Date(today);
		weekStart.setDate(weekStart.getDate() - weekStart.getDay());
		return weekStart;
	}

	const parsed = new Date(dateStr);
	if (!Number.isNaN(parsed.getTime())) return parsed;

	return null;
}

function extractContent(messageInfo: any): string {
	if (!messageInfo) return "[No info]";

	// Check for summary object
	if (typeof messageInfo.summary === "object" && messageInfo.summary !== null) {
		if (messageInfo.summary.title) return messageInfo.summary.title;
		if (messageInfo.summary.body) return messageInfo.summary.body;
	}

	return "[No content]";
}
