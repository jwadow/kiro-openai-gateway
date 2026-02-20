import { tool } from "@opencode-ai/plugin";

// Context7 API v2 - https://context7.com/docs/api-guide
const CONTEXT7_API = "https://context7.com/api/v2";

interface LibraryInfo {
	id: string;
	title: string;
	description?: string;
	totalSnippets?: number;
	trustScore?: number;
	benchmarkScore?: number;
	versions?: string[];
}

interface SearchResponse {
	results: LibraryInfo[];
}

/**
 * Consolidated Context7 documentation lookup tool.
 * Operations: resolve (find library ID), query (get docs)
 */
export default tool({
	description: `Context7 documentation lookup: resolve library IDs and query docs.

Operations:
- "resolve": Find library ID from name (e.g., "react" → "/reactjs/react.dev")
- "query": Get documentation for a library topic

Example:
context7({ operation: "resolve", libraryName: "react" })
context7({ operation: "query", libraryId: "/reactjs/react.dev", topic: "hooks" })`,
	args: {
		operation: tool.schema
			.string()
			.optional()
			.default("resolve")
			.describe("Operation: resolve or query"),
		libraryName: tool.schema
			.string()
			.optional()
			.describe("Library name to resolve (for resolve operation)"),
		libraryId: tool.schema
			.string()
			.optional()
			.describe("Library ID from resolve (for query operation)"),
		topic: tool.schema
			.string()
			.optional()
			.describe("Documentation topic (for query operation)"),
	},
	execute: async (args: {
		operation?: string;
		libraryName?: string;
		libraryId?: string;
		topic?: string;
	}) => {
		const operation = args.operation || "resolve";

		// Add API key if available
		const apiKey = process.env.CONTEXT7_API_KEY;
		const headers: HeadersInit = {
			Accept: "application/json",
			"User-Agent": "OpenCode/1.0",
		};

		if (apiKey) {
			headers.Authorization = `Bearer ${apiKey}`;
		}

		// ===== RESOLVE =====
		if (operation === "resolve") {
			const { libraryName } = args;

			if (!libraryName || libraryName.trim() === "") {
				return "Error: libraryName is required for resolve operation";
			}

			try {
				const url = new URL(`${CONTEXT7_API}/libs/search`);
				url.searchParams.set("libraryName", libraryName);
				url.searchParams.set("query", "documentation");

				const response = await fetch(url.toString(), { headers });

				if (!response.ok) {
					if (response.status === 401) {
						return `Error: Invalid CONTEXT7_API_KEY. Get a free key at https://context7.com/dashboard`;
					}
					if (response.status === 429) {
						return `Error: Rate limit exceeded. Get a free API key at https://context7.com/dashboard for higher limits.`;
					}
					return `Error: Context7 API returned ${response.status}`;
				}

				const data = (await response.json()) as SearchResponse;
				const libraries = data.results || [];

				if (!libraries || libraries.length === 0) {
					return `No libraries found matching: ${libraryName}\n\nTry:\n- Different library name\n- Check spelling\n- Use official package name`;
				}

				const formatted = libraries
					.slice(0, 5)
					.map((lib, i) => {
						const desc = lib.description
							? `\n   ${lib.description.slice(0, 100)}...`
							: "";
						const snippets = lib.totalSnippets
							? ` (${lib.totalSnippets} snippets)`
							: "";
						const score = lib.benchmarkScore
							? ` [score: ${lib.benchmarkScore}]`
							: "";
						return `${i + 1}. **${lib.title}** → \`${lib.id}\`${snippets}${score}${desc}`;
					})
					.join("\n\n");

				return `Found ${libraries.length} libraries matching "${libraryName}":

${formatted}

**Next step**: Use \`context7({ operation: "query", libraryId: "${libraries[0].id}", topic: "your topic" })\` to fetch documentation.`;
			} catch (error: unknown) {
				const message = error instanceof Error ? error.message : String(error);
				return `Error resolving library: ${message}`;
			}
		}

		// ===== QUERY =====
		if (operation === "query") {
			const { libraryId, topic } = args;

			if (!libraryId || libraryId.trim() === "") {
				return 'Error: libraryId is required (use operation: "resolve" first)';
			}

			if (!topic || topic.trim() === "") {
				return "Error: topic is required (e.g., 'hooks', 'setup', 'API reference')";
			}

			try {
				const url = new URL(`${CONTEXT7_API}/context`);
				url.searchParams.set("libraryId", libraryId);
				url.searchParams.set("query", topic);

				const queryHeaders = { ...headers, Accept: "text/plain" };
				const response = await fetch(url.toString(), {
					headers: queryHeaders,
				});

				if (!response.ok) {
					if (response.status === 401) {
						return `Error: Invalid CONTEXT7_API_KEY. Get a free key at https://context7.com/dashboard`;
					}
					if (response.status === 404) {
						return `Error: Library not found: ${libraryId}\n\nUse operation: "resolve" first to find the correct ID.`;
					}
					if (response.status === 429) {
						return `Error: Rate limit exceeded. Get a free API key at https://context7.com/dashboard for higher limits.`;
					}
					return `Error: Context7 API returned ${response.status}`;
				}

				const content = await response.text();

				if (!content || content.trim() === "") {
					return `No documentation found for "${topic}" in ${libraryId}.\n\nTry:\n- Simpler terms (e.g., "useState" instead of "state management")\n- Different topic spelling\n- Broader topics like "API reference" or "getting started"`;
				}

				return `# Documentation: ${topic} (${libraryId})

${content}`;
			} catch (error: unknown) {
				const message = error instanceof Error ? error.message : String(error);
				return `Error querying documentation: ${message}`;
			}
		}

		return `Unknown operation: ${operation}. Use: resolve, query`;
	},
});
