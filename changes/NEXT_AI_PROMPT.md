Use this repository context file first:

- `changes/CHANGES_CONTEXT_FULL.md`

Then continue from there with these exact goals:

1) Validate and finalize default thinking behavior
- Ensure gateway default is no-thinking when request has no hints.
- Preserve request-driven behavior for explicit hints.

2) Anthropic mode policy in OpenCode
- Keep only `high` and `max` thinking variants for Anthropic profile (no `off` variant).
- Confirm local OpenCode profile is consistent with this policy.

3) Built-in OpenCode Anthropic provider compatibility
- Verify built-in `anthropic` provider requests are accepted by gateway auth layer (no 401 mismatch).
- Confirm support for `x-api-key`, `api-key`, and `Authorization: Bearer` where applicable.
- If gateway key mismatch is the reason, ensure migration path via `PROXY_API_KEY_ALIASES` is documented.

4) Runtime verification
- Run focused tests for touched files first.
- Perform smoke runtime checks.
- If upstream SSL/proxy cert issue blocks end-to-end responses, clearly separate infra SSL failure from API compatibility failure.

5) Keep changes minimal
- Avoid broad refactors.
- Touch only files required by the above goals.

6) Final report
- Summarize what was changed, why, and what remains.
- Include exact file paths and key behavior differences before/after.
