/**
 * GitHub Copilot Auth Plugin
 * Simplified auth provider without token expiration checks
 *
 * Claude Reasoning Support:
 * This plugin adds `thinking_budget` to the request body for Claude models.
 * The Copilot API accepts this parameter and returns reasoning in the response.
 *
 * NOTE: Response parsing for reasoning_text/reasoning_opaque is handled by
 * the custom SDK at .opencode/plugin/sdk/copilot/ which properly converts
 * these fields to AI SDK's reasoning content parts.
 */

import type { Plugin } from "@opencode-ai/plugin";

const CLIENT_ID = "Ov23li8tweQw6odWQebz";

// Logger function that will be set by the plugin
let log: (
	level: "debug" | "info" | "warn" | "error",
	message: string,
	extra?: Record<string, any>,
) => void = () => {};

/**
 * Set the logger function from the plugin context
 */
function setLogger(client: any) {
	log = (level, message, extra) => {
		client.app
			.log({
				service: "copilot-auth",
				level,
				message,
				extra,
			})
			.catch(() => {}); // Fire and forget, don't block on logging
	};
}

// Add a small safety buffer when polling to avoid hitting the server
// slightly too early due to clock skew / timer drift.
const OAUTH_POLLING_SAFETY_MARGIN_MS = 3000; // 3 seconds

const HEADERS = {
	"User-Agent": "GitHubCopilotChat/0.35.0",
	"Editor-Version": "vscode/1.107.0",
	"Editor-Plugin-Version": "copilot-chat/0.35.0",
	"Copilot-Integration-Id": "vscode-chat",
};

const RESPONSES_API_ALTERNATE_INPUT_TYPES = [
	"file_search_call",
	"computer_call",
	"computer_call_output",
	"web_search_call",
	"function_call",
	"function_call_output",
	"image_generation_call",
	"code_interpreter_call",
	"local_shell_call",
	"local_shell_call_output",
	"mcp_list_tools",
	"mcp_approval_request",
	"mcp_approval_response",
	"mcp_call",
	"reasoning",
];

function normalizeDomain(url: string): string {
	return url.replace(/^https?:\/\//, "").replace(/\/$/, "");
}

function getUrls(domain: string) {
	return {
		DEVICE_CODE_URL: `https://${domain}/login/device/code`,
		ACCESS_TOKEN_URL: `https://${domain}/login/oauth/access_token`,
	};
}

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

// Rate limit handling configuration
const RATE_LIMIT_CONFIG = {
	maxRetries: 3,
	baseDelayMs: 2000, // Start with 2 seconds
	maxDelayMs: 30000, // Cap at 30 seconds
};

/**
 * Calculate delay with exponential backoff and jitter
 * Retries: 2s, 4s, 8s (with jitter)
 */
function calculateRetryDelay(attempt: number): number {
	const exponentialDelay = RATE_LIMIT_CONFIG.baseDelayMs * Math.pow(2, attempt);
	const jitter = Math.random() * 1000; // Add 0-1s random jitter
	const delay = Math.min(
		exponentialDelay + jitter,
		RATE_LIMIT_CONFIG.maxDelayMs,
	);
	return Math.round(delay);
}

export const CopilotAuthPlugin: Plugin = async ({ client: sdk }) => {
	// Initialize logger with the SDK client
	setLogger(sdk);

	return {
		auth: {
			provider: "github-copilot",
			loader: async (getAuth, provider) => {
				const info = await getAuth();
				if (!info || info.type !== "oauth") return {};

				// Enterprise URL support for baseURL
				const enterpriseUrl = (info as any).enterpriseUrl;
				const baseURL = enterpriseUrl
					? `https://copilot-api.${normalizeDomain(enterpriseUrl)}`
					: undefined;

				if (provider && provider.models) {
					for (const [_modelId, model] of Object.entries(provider.models)) {
						model.cost = {
							input: 0,
							output: 0,
							cache: {
								read: 0,
								write: 0,
							},
						};

						// All models use the standard github-copilot SDK
						// Reasoning support for Claude models is handled via:
						// 1. The fetch wrapper adds thinking_budget to request body
						// 2. The fetch wrapper strips invalid thinking blocks from messages
						model.api.npm = "@ai-sdk/github-copilot";
					}
				}

				return {
					baseURL,
					apiKey: "",
					async fetch(input, init) {
						const info = await getAuth();
						if (info.type !== "oauth") return fetch(input, init);

						let isAgentCall = false;
						let isVisionRequest = false;
						let modifiedBody: any = undefined;
						let isClaudeModel = false;

						try {
							const body =
								typeof init?.body === "string"
									? JSON.parse(init.body)
									: init?.body;

							const url = input.toString();

							// Check if this is a Claude model request
							const modelId = body?.model || "";
							isClaudeModel = modelId.toLowerCase().includes("claude");

							// Completions API
							if (body?.messages && url.includes("completions")) {
								// Keep local logic: detect if any message is assistant/tool
								isAgentCall = body.messages.some((msg: any) =>
									["tool", "assistant"].includes(msg.role),
								);
								isVisionRequest = body.messages.some(
									(msg: any) =>
										Array.isArray(msg.content) &&
										msg.content.some((part: any) => part.type === "image_url"),
								);

								// For Claude models, add thinking_budget to enable reasoning
								// The Copilot API accepts this parameter and returns reasoning_text/reasoning_opaque
								if (isClaudeModel) {
									// Use configured thinking_budget from model options, or default to 10000
									const thinkingBudget = body.thinking_budget || 10000;

									// Fix for "Invalid signature in thinking block" error:
									// The Copilot API uses reasoning_text/reasoning_opaque format for thinking
									// When these are passed back without proper signature, it causes errors
									// Solution: Ensure reasoning_opaque is present when reasoning_text exists,
									// or remove reasoning content entirely if signature is invalid/missing
									const cleanedMessages = body.messages.map(
										(msg: any, idx: number) => {
											if (msg.role !== "assistant") return msg;

											// Log message structure for debugging
											log("debug", `Processing assistant message ${idx}`, {
												has_reasoning_text: !!msg.reasoning_text,
												has_reasoning_opaque: !!msg.reasoning_opaque,
												content_type: typeof msg.content,
												content_is_array: Array.isArray(msg.content),
											});

											// If message has reasoning_text but no/invalid reasoning_opaque, remove reasoning
											if (msg.reasoning_text && !msg.reasoning_opaque) {
												log(
													"warn",
													`Removing reasoning_text without reasoning_opaque from message ${idx}`,
												);
												const { reasoning_text: _unused, ...cleanedMsg } = msg;
												return cleanedMsg;
											}

											// If content is an array, check for thinking blocks
											if (Array.isArray(msg.content)) {
												const hasThinkingBlock = msg.content.some(
													(part: any) => part.type === "thinking",
												);
												if (hasThinkingBlock) {
													log(
														"debug",
														`Message ${idx} has thinking blocks in content array`,
													);
													// Filter out thinking blocks without signatures
													const cleanedContent = msg.content.filter(
														(part: any) => {
															if (part.type === "thinking") {
																if (!part.signature) {
																	log(
																		"warn",
																		`Removing thinking block without signature`,
																	);
																	return false;
																}
															}
															return true;
														},
													);
													return {
														...msg,
														content:
															cleanedContent.length > 0 ? cleanedContent : null,
													};
												}
											}

											return msg;
										},
									);

									modifiedBody = {
										...body,
										messages: cleanedMessages,
										thinking_budget: thinkingBudget,
									};
									log("info", `Adding thinking_budget for Claude model`, {
										model: modelId,
										thinking_budget: thinkingBudget,
									});
								}

								// For GPT models (o1, gpt-5, etc.), add reasoning parameter
								const isGptModel =
									modelId.toLowerCase().includes("gpt") ||
									modelId.toLowerCase().includes("o1") ||
									modelId.toLowerCase().includes("o3") ||
									modelId.toLowerCase().includes("o4");

								if (isGptModel && !isClaudeModel) {
									// Get reasoning effort from body options or default to "medium"
									const reasoningEffort =
										body.reasoning?.effort ||
										body.reasoningEffort ||
										body.reasoning_effort ||
										"medium";

									modifiedBody = {
										...(modifiedBody || body),
										reasoning: {
											effort: reasoningEffort,
										},
									};

									// Also pass through other reasoning options if present
									if (body.reasoningSummary || body.reasoning?.summary) {
										modifiedBody.reasoning.summary =
											body.reasoningSummary || body.reasoning?.summary;
									}

									log("info", `Adding reasoning for GPT model`, {
										model: modelId,
										reasoning_effort: reasoningEffort,
									});
								}
							}

							// Responses API
							if (body?.input) {
								isAgentCall = body.input.some(
									(item: any) =>
										item?.role === "assistant" ||
										(item?.type &&
											RESPONSES_API_ALTERNATE_INPUT_TYPES.includes(item.type)),
								);

								isVisionRequest = body.input.some(
									(item: any) =>
										Array.isArray(item?.content) &&
										item.content.some(
											(part: any) => part.type === "input_image",
										),
								);
							}

							// Messages API (Anthropic style)
							if (body?.messages && !url.includes("completions")) {
								isAgentCall = body.messages.some((msg: any) =>
									["tool", "assistant"].includes(msg.role),
								);
								isVisionRequest = body.messages.some(
									(item: any) =>
										Array.isArray(item?.content) &&
										item.content.some(
											(part: any) =>
												part?.type === "image" ||
												(part?.type === "tool_result" &&
													Array.isArray(part?.content) &&
													part.content.some(
														(nested: any) => nested?.type === "image",
													)),
										),
								);
							}
						} catch {}

						const headers: Record<string, string> = {
							"x-initiator": isAgentCall ? "agent" : "user",
							...(init?.headers as Record<string, string>),
							...HEADERS,
							Authorization: `Bearer ${info.refresh}`,
							"Openai-Intent": "conversation-edits",
						};

						if (isVisionRequest) {
							headers["Copilot-Vision-Request"] = "true";
						}

						// Official only deletes lowercase "authorization"
						delete headers["x-api-key"];
						delete headers["authorization"];

						// Prepare the final init object with potentially modified body
						const finalInit = {
							...init,
							headers,
							...(modifiedBody ? { body: JSON.stringify(modifiedBody) } : {}),
						};

						// Retry logic with exponential backoff for rate limiting
						let lastError: Error | undefined;
						for (
							let attempt = 0;
							attempt <= RATE_LIMIT_CONFIG.maxRetries;
							attempt++
						) {
							try {
								const response = await fetch(input, finalInit);

								// If we get a 429, retry with backoff
								if (
									response.status === 429 &&
									attempt < RATE_LIMIT_CONFIG.maxRetries
								) {
									const delay = calculateRetryDelay(attempt);
									log("warn", `Rate limited (429), retrying`, {
										delay_ms: delay,
										attempt: attempt + 1,
										max_retries: RATE_LIMIT_CONFIG.maxRetries,
									});
									await sleep(delay);
									continue;
								}

								// Response transformation is now handled by the custom SDK at
								// .opencode/plugin/sdk/copilot/ which properly parses reasoning_text/reasoning_opaque
								// and converts them to AI SDK's reasoning content parts
								return response;
							} catch (error) {
								lastError = error as Error;

								// Network errors might be transient, retry
								if (attempt < RATE_LIMIT_CONFIG.maxRetries) {
									const delay = calculateRetryDelay(attempt);
									log("warn", `Request failed, retrying`, {
										delay_ms: delay,
										attempt: attempt + 1,
										max_retries: RATE_LIMIT_CONFIG.maxRetries,
										error: lastError.message,
									});
									await sleep(delay);
									continue;
								}
								throw error;
							}
						}

						// If we've exhausted all retries, throw the last error
						if (lastError) {
							throw new Error(
								`[Copilot] Max retries (${RATE_LIMIT_CONFIG.maxRetries}) exceeded. Last error: ${lastError.message}`,
							);
						}

						// This should not be reached, but just in case
						throw new Error(
							`[Copilot] Max retries (${RATE_LIMIT_CONFIG.maxRetries}) exceeded`,
						);
					},
				};
			},
			methods: [
				{
					type: "oauth",
					label: "Login with GitHub Copilot",
					prompts: [
						{
							type: "select",
							key: "deploymentType",
							message: "Select GitHub deployment type",
							options: [
								{
									label: "GitHub.com",
									value: "github.com",
									hint: "Public",
								},
								{
									label: "GitHub Enterprise",
									value: "enterprise",
									hint: "Data residency or self-hosted",
								},
							],
						},
						{
							type: "text",
							key: "enterpriseUrl",
							message: "Enter your GitHub Enterprise URL or domain",
							placeholder: "company.ghe.com or https://company.ghe.com",
							condition: (inputs: any) =>
								inputs.deploymentType === "enterprise",
							validate: (value: string) => {
								if (!value) return "URL or domain is required";
								try {
									const url = value.includes("://")
										? new URL(value)
										: new URL(`https://${value}`);
									if (!url.hostname)
										return "Please enter a valid URL or domain";
									return undefined;
								} catch {
									return "Please enter a valid URL (e.g., company.ghe.com or https://company.ghe.com)";
								}
							},
						},
					],
					async authorize(inputs: any = {}) {
						const deploymentType = inputs.deploymentType || "github.com";

						let domain = "github.com";
						let actualProvider = "github-copilot";

						if (deploymentType === "enterprise") {
							const enterpriseUrl = inputs.enterpriseUrl;
							domain = normalizeDomain(enterpriseUrl);
							actualProvider = "github-copilot-enterprise";
						}

						const urls = getUrls(domain);

						const deviceResponse = await fetch(urls.DEVICE_CODE_URL, {
							method: "POST",
							headers: {
								Accept: "application/json",
								"Content-Type": "application/json",
								"User-Agent": "GitHubCopilotChat/0.35.0",
							},
							body: JSON.stringify({
								client_id: CLIENT_ID,
								scope: "read:user",
							}),
						});

						if (!deviceResponse.ok) {
							throw new Error("Failed to initiate device authorization");
						}

						const deviceData = await deviceResponse.json();

						return {
							url: deviceData.verification_uri,
							instructions: `Enter code: ${deviceData.user_code}`,
							method: "auto",
							callback: async () => {
								while (true) {
									const response = await fetch(urls.ACCESS_TOKEN_URL, {
										method: "POST",
										headers: {
											Accept: "application/json",
											"Content-Type": "application/json",
											"User-Agent": "GitHubCopilotChat/0.35.0",
										},
										body: JSON.stringify({
											client_id: CLIENT_ID,
											device_code: deviceData.device_code,
											grant_type:
												"urn:ietf:params:oauth:grant-type:device_code",
										}),
									});

									if (!response.ok) return { type: "failed" };

									const data = await response.json();

									if (data.access_token) {
										const result: {
											type: "success";
											refresh: string;
											access: string;
											expires: number;
											provider?: string;
											enterpriseUrl?: string;
										} = {
											type: "success",
											refresh: data.access_token,
											access: data.access_token,
											expires: 0,
										};

										if (actualProvider === "github-copilot-enterprise") {
											result.provider = "github-copilot-enterprise";
											result.enterpriseUrl = domain;
										}

										return result;
									}

									if (data.error === "authorization_pending") {
										await sleep(
											deviceData.interval * 1000 +
												OAUTH_POLLING_SAFETY_MARGIN_MS,
										);
										continue;
									}

									if (data.error === "slow_down") {
										// Based on the RFC spec, we must add 5 seconds to our current polling interval.
										let newInterval = (deviceData.interval + 5) * 1000;

										if (
											data.interval &&
											typeof data.interval === "number" &&
											data.interval > 0
										) {
											newInterval = data.interval * 1000;
										}

										await sleep(newInterval + OAUTH_POLLING_SAFETY_MARGIN_MS);
										continue;
									}

									if (data.error) return { type: "failed" };

									await sleep(
										deviceData.interval * 1000 + OAUTH_POLLING_SAFETY_MARGIN_MS,
									);
									continue;
								}
							},
						};
					},
				},
			],
		},
		// Hook to add custom headers for Claude reasoning support
		"chat.headers": async (input: any, output: any) => {
			// Only apply to GitHub Copilot provider
			if (!input.model?.providerID?.includes("github-copilot")) return;

			// Add Anthropic beta header for interleaved thinking (extended reasoning)
			// This is required for Claude models to return thinking blocks
			if (input.model?.api?.npm === "@ai-sdk/anthropic") {
				output.headers["anthropic-beta"] = "interleaved-thinking-2025-05-14";
			}

			// Mark subagent sessions as agent-initiated (matching standard Copilot tools)
			try {
				const session = await sdk.session
					.get({
						path: {
							id: input.sessionID,
						},
						throwOnError: true,
					})
					.catch(() => undefined);
				if (session?.data?.parentID) {
					output.headers["x-initiator"] = "agent";
				}
			} catch {
				// Ignore errors from session lookup
			}
		},
	};
};
