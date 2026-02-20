/**
 * OpenCode Notification Plugin
 * Sends native notifications when sessions complete
 */

import type { Plugin } from "@opencode-ai/plugin";
import { notify } from "./lib/notify.js";

export const NotificationPlugin: Plugin = async ({ client, $ }) => {
	const notifiedSessions = new Set<string>();

	return {
		event: async ({ event }) => {
			if (event.type === "session.idle") {
				const props = event.properties as Record<string, unknown>;
				const sessionId = props?.sessionID as string | undefined;

				if (!sessionId || notifiedSessions.has(sessionId)) return;
				notifiedSessions.add(sessionId);

				setTimeout(async () => {
					try {
						let summary = "Session completed";

						const messagesResponse = await client.session.messages({
							path: { id: sessionId },
						});

						if (messagesResponse.data && Array.isArray(messagesResponse.data)) {
							const lastUserMessage = messagesResponse.data
								.filter((m) => m.info.role === "user")
								.pop();

							const messageSummary = lastUserMessage?.info?.summary;
							if (
								messageSummary &&
								typeof messageSummary === "object" &&
								messageSummary !== null
							) {
								if ("body" in messageSummary && messageSummary.body) {
									summary = String(messageSummary.body).trim().slice(0, 100);
								} else if ("title" in messageSummary && messageSummary.title) {
									summary = String(messageSummary.title).trim();
								}
							}
						}

						await notify($, "OpenCode", summary);
					} catch (error) {
						client.app
							.log({
								body: {
									service: "notification",
									level: "warn",
									message: `Notification failed: ${(error as Error).message}`,
								},
							})
							.catch(() => {});
					}
				}, 2000);
			}
		},
	};
};
