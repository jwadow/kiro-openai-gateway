# Architecture Audit

## Scope

- Repository: `kiro-gateway`
- Baseline: `upstream/main` (`6ada76c`) vs current branch head (`bac2e28`)
- Method: static code audit + test validation (`pytest -q`)

## Current architecture snapshot

- Route layer parses OpenAI/Anthropic input and resolves request-level thinking policy (`kiro/routes_openai.py:258`, `kiro/routes_anthropic.py:297`).
- Converter core applies middleware, normalization, and payload shaping before upstream call (`kiro/converters_core.py:1971`, `kiro/converters_core.py:2032`).
- Middleware pipeline isolates malformed-request repairs and size guards (`kiro/middleware/pipeline.py:44`).
- Payload envelope guards enforce byte/history caps after payload assembly (`kiro/converters_core.py:2178`, `kiro/payload_guards.py:52`).

## Findings

### P0 (production/security risk)

1. Default proxy key is still a known static secret.
   - Evidence: `PROXY_API_KEY` default is `"my-super-secret-password-123"` (`kiro/config.py:100`).
   - Risk: accidental deployment with default key allows trivial unauthorized access.
   - Recommended fix: fail startup when `PROXY_API_KEY` equals default literal unless explicit dev override flag is set.

2. Upstream auth bypass flag can disable bearer forwarding globally.
   - Evidence: `SKIP_AUTH` config (`kiro/config.py:501`), startup early-return in validation (`main.py:225`), header stripping in HTTP client (`kiro/http_client.py:220`).
   - Risk: if enabled unintentionally, requests run without upstream auth controls.
   - Recommended fix: require explicit `SKIP_AUTH_ACKNOWLEDGED=true` handshake and emit high-severity startup banner.

### P1 (reliability/behavior risk)

1. Transparent-proxy behavior is opt-out; mutation guards are opt-in by default.
   - Evidence: default-enabled validators/guards (`kiro/config.py:332`, `kiro/config.py:348`, `kiro/config.py:405`, `kiro/config.py:448`).
   - Effect: payload may be rewritten unless operators disable multiple toggles.
   - Recommended fix: add a single `STRICT_TRANSPARENT_MODE=true` profile that disables all mutating guards atomically.

2. Reactive retry exists only in Anthropic route.
   - Evidence: Anthropic 400 reactive retry loop (`kiro/routes_anthropic.py:372`), no equivalent block in OpenAI route error path (`kiro/routes_openai.py:309`).
   - Effect: inconsistent recovery behavior between `/v1/messages` and `/v1/chat/completions`.
   - Recommended fix: extract shared retry policy module and apply from both routes.

3. Tool schema behavior can diverge due dual name policies.
   - Evidence: hard-fail for long names (`kiro/converters_core.py:528`) and separate truncation behavior (`kiro/middleware/schema_sanitizer.py:116`).
   - Effect: ambiguous operator expectations (fail-fast vs silent mutation).
   - Recommended fix: keep one policy only (prefer fail-fast by default, optional truncation mode behind explicit flag).

### P2 (maintainability/tech debt)

1. Guard logic remains duplicated across legacy core and middleware modules.
   - Evidence: legacy guard path in core (`kiro/converters_core.py:916`) and extracted middleware equivalent (`kiro/middleware/payload_size_guard.py:81`).
   - Effect: future edits can drift between implementations.
   - Recommended fix: remove legacy guard helpers once migration confidence is complete.

2. Documentation sprawl created parallel handoff narratives.
   - Evidence: overlapping docs (`fork-docs/CHANGES_CONTEXT_FULL.md:1`, `fork-docs/HANDOFF_THINKING_POLICY_MIGRATION.md:1`, `fork-docs/PROMPT_KIRO_GATEWAY_DEEP_AUDIT_TR.md:1`).
   - Recommended fix: treat this audit set as canonical and mark prior handoff docs as superseded.

## Applied refactor status in this branch

- Added request-driven thinking policy resolver (`kiro/thinking_policy.py:1`).
- Introduced middleware package and pipeline orchestration (`kiro/middleware/pipeline.py:1`).
- Isolated payload envelope guards into dedicated module (`kiro/payload_guards.py:1`).
- Added dedicated tests for thinking policy and payload guards (`tests/unit/test_thinking_policy.py:1`, `tests/unit/test_payload_guards.py:1`).

## Test status

- Full suite passes: `1489 passed` from `pytest -q`.
