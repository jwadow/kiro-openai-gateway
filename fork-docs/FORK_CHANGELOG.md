# Fork Changelog (vs upstream `jwadow/kiro-gateway`)

This file documents how this fork differs from upstream and why each change exists.

## Baseline

- Upstream remote: `https://github.com/jwadow/kiro-gateway.git`
- Compared against: `upstream/main` (`6ada76c`)
- Local HEAD during analysis: `bac2e28`
- Diff commands used:
  - `git diff --name-status upstream/main`
  - `git diff --stat upstream/main`

## High-level goals of this fork

1. Improve client compatibility (OpenClaw/OpenCode/Codex/Anthropic/OpenAI adapters).
2. Make thinking behavior request-driven and predictable.
3. Harden malformed-request handling (`Improperly formed request`) with configurable guards.
4. Keep gateway usable in real-world network/auth setups (social token, TLS/proxy, retry behavior).
5. Back changes with expanded unit-test coverage.

## Tracked differences vs upstream (file-by-file)

### Metadata / Docs / Ops

- `.clabot`
  - Updated CLA bot contributor metadata list.
- `.env.example`
  - Expanded config surface (thinking policy, middleware/guards, payload limits, retry toggles).
  - Added explicit notes for enabling/disabling intervention features.
- `README.md`
  - Added fork-specific "What does this fork do?" context and compatibility notes.
- `fork-docs/CHANGES_CONTEXT_FULL.md` (new)
  - Fork handoff/change context documentation.
- `fork-docs/HANDOFF_THINKING_POLICY_MIGRATION.md` (new)
  - Detailed migration notes for thinking-policy behavior.

### Core Runtime / Bootstrap

- `main.py`
  - Startup/runtime wiring updates for fork behavior (auth/model/runtime path alignment).

### Authentication / Model / Errors / HTTP

- `kiro/auth.py`
  - Auth flow hardening for social-token / Kiro CLI SQLite scenarios.
  - Better token refresh routing and session stability.
- `kiro/model_resolver.py`
  - Model normalization/alias handling improvements.
  - Better compatibility with variant model naming formats.
- `kiro/http_client.py`
  - Retry/network behavior tuning and robustness improvements.
- `kiro/kiro_errors.py`
  - Enhanced user-facing error translation for opaque upstream errors.

### Request conversion pipeline

- `kiro/converters_anthropic.py`
  - Adapter-side compatibility updates for Anthropic-style requests.
- `kiro/converters_openai.py`
  - Adapter-side compatibility updates for OpenAI-style requests.
- `kiro/converters_core.py`
  - Major refactor and feature expansion:
    - Unified message normalization and role-structure handling.
    - Middleware pipeline integration.
    - Tool/payload safety controls.
    - Payload-level guard orchestration (size/tool consistency) via dedicated module.

### Route handlers

- `kiro/routes_anthropic.py`
  - Improved request handling, malformed-request recovery behavior, and compatibility paths.
- `kiro/routes_openai.py`
  - Compatibility and robustness updates for OpenAI endpoint behavior.

### Streaming pipeline

- `kiro/streaming_anthropic.py`
  - Streaming stability/compatibility refinements.
- `kiro/streaming_core.py`
  - Shared streaming behavior updates.
- `kiro/streaming_openai.py`
  - OpenAI stream adaptation updates.

### Thinking policy subsystem

- `kiro/thinking_policy.py` (new)
  - Central request-driven thinking policy engine.
  - Handles precedence between request/body hints, headers, defaults.

### Test suite changes (tracked)

- `tests/unit/test_auth_manager.py`
  - Expanded auth-flow coverage.
- `tests/unit/test_config.py`
  - Expanded config/default/compatibility coverage.
- `tests/unit/test_converters_anthropic.py`
  - Anthropic conversion edge-case coverage updates.
- `tests/unit/test_converters_core.py`
  - Large expansion of converter-core regression and edge-case coverage.
- `tests/unit/test_converters_openai.py`
  - OpenAI conversion edge-case coverage updates.
- `tests/unit/test_http_client.py`
  - Retry/network behavior coverage updates.
- `tests/unit/test_kiro_errors.py`
  - Enhanced error-mapping tests.
- `tests/unit/test_streaming_core.py`
  - Shared streaming behavior tests.
- `tests/unit/test_streaming_openai.py`
  - OpenAI streaming behavior tests.
- `tests/unit/test_thinking_parser.py`
  - Thinking parser compatibility tests.
- `tests/unit/test_thinking_policy.py` (new)
  - Thinking policy test matrix.

## Additional fork modules currently present locally

These are part of the fork work but may be untracked relative to current Git index.

### New middleware package

- `kiro/middleware/__init__.py`
- `kiro/middleware/pipeline.py`
- `kiro/middleware/tool_pairing_validator.py`
- `kiro/middleware/message_structure_validator.py`
- `kiro/middleware/payload_size_guard.py`
- `kiro/middleware/queued_announce_compactor.py`
- `kiro/middleware/schema_sanitizer.py`

Purpose:

- Isolate class-based malformed-request fixes into dedicated stages.
- Keep guard logic modular, configurable, and testable.

### New payload guard module

- `kiro/payload_guards.py`

Purpose:

- Move payload-envelope mutation (size trim, empty toolUses stripping,
  orphaned toolResult repair) out of monolithic converter flow.

### New docs/tests

- `fork-docs/KIRO_API_REVERSE_ENGINEERED.md`
  - Source-backed findings for `Improperly formed request` failure modes.
- `tests/unit/test_payload_guards.py`
  - Dedicated tests for payload-guard behavior.

## Design notes / intent analysis

### Where this fork intentionally diverges from strict transparent mode

- Enables anti-400 guards by default (can be disabled by operators).
- Applies payload-level structural repair after trimming to keep requests valid.
- Adds middleware-level compatibility repairs for malformed client sessions.

### Why this was done

- Real-world clients (especially subagent-heavy flows) frequently emit malformed
  or oversized payloads that upstream rejects with generic 400.
- Practical uptime and reliability were prioritized for this fork.

### Operator control retained

- Intervention toggles are exposed in `.env`.
- History count cap is disabled by default (`KIRO_MAX_HISTORY_ENTRIES=0`).
- Payload limit is configurable (`KIRO_MAX_PAYLOAD_BYTES`).

## Local-only artifacts intentionally excluded from fork analysis

Not part of product behavior:

- `.venv/`, `venv/`
- runtime logs (e.g., `gateway_restart.log`, `gateway_8002.log`)
- `__pycache__/`

## Consolidated audit documents (canonical set)

The following files are the maintained review set for this fork:

- `fork-docs/FORK_CHANGELOG.md`
- `fork-docs/ARCHITECTURE_AUDIT.md`
- `fork-docs/SECURITY_REVIEW.md`
- `fork-docs/PR_REVIEW_SUMMARY.md`

Historical handoff/prompt files remain in the repository but are explicitly marked as superseded:

- `fork-docs/CHANGES_CONTEXT_FULL.md`
- `fork-docs/HANDOFF_THINKING_POLICY_MIGRATION.md`
- `fork-docs/PROMPT_KIRO_GATEWAY_DEEP_AUDIT_TR.md`
