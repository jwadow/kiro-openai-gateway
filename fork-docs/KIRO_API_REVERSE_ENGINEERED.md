# Kiro API Reverse-Engineered Findings

Last updated: 2026-02-11 13:23 UTC

This document records reproducible findings about Kiro upstream failures with:

```
HTTP 400
{"message":"Improperly formed request.","reason":null}
```

It is intended as shared operational knowledge for gateway maintainers.

## 1) External evidence (public sources)

### 1.1 Payload-size failure band (community reproducible)

Source: `jwadow/kiro-gateway` issue #73 + comments

- Issue: https://github.com/jwadow/kiro-gateway/issues/73
- Comment evidence (binary search style):
  - `629,504 bytes (614.75 KB) -> HTTP 200`
  - `629,760 bytes (615.00 KB) -> HTTP 400 Improperly formed request`

Interpretation: upstream request-body acceptance appears to have a hard threshold
around ~615 KB in at least one real environment. Exact value may vary, but
payload-size pressure is real and deterministic enough to guard against.

### 1.2 Complex tool schema can trigger the same 400 class

Source: `kirodotdev/Kiro` issue #3431

- URL: https://github.com/kirodotdev/Kiro/issues/3431
- Pattern: nested/complex MCP JSON schema caused ValidationException with
  "Improperly formed request".

Interpretation: this error class is overloaded; schema complexity issues and
payload/structure issues can produce the same generic 400.

### 1.3 Tool-use contract (reference behavior)

Source: Anthropic Messages + tool-use docs

- Messages API: https://docs.claude.com/en/api/messages
- Tool-use implementation: https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/implement-tool-use

Relevant invariant: each `tool_result` must correspond to a prior `tool_use`
in valid conversational structure. While Kiro is not Anthropic, proxy layers
that emulate Anthropic semantics must preserve this invariant.

## 2) Internal reproduction and verification

Local replay/stress tests were run through gateway endpoint `/v1/messages` and
verified with gateway logs.

Observed in `gateway_restart.log`:

- Oversized request was trimmed and succeeded:
  - `History trimmed: 556 -> 314 entries, payload 905374 -> 589770 bytes`
  - `Removed orphaned toolResults: history=1, current=0`
  - Final status: `HTTP 200`

- Large OpenClaw-like run also succeeded after conservative trim:
  - `History trimmed: 568 -> 564 entries, payload 620487 -> 589803 bytes`
  - Final status: `HTTP 200`

## 3) Confirmed failure causes (high confidence)

### 3.1 Orphaned `toolResults`

If history trimming removes the assistant `toolUse` turn but leaves the
user `toolResult`, the payload becomes structurally invalid for Kiro and can
fail with generic 400.

### 3.2 Empty `toolUses: []` fields

Assistant messages with explicit empty arrays are risky. Omitting the field
entirely is safer than sending `"toolUses": []`.

### 3.3 Oversized serialized payload

Payload-size threshold is upstream-sensitive and undocumented. Community and
local evidence indicates a practical danger zone near ~615 KB.

## 4) Guard strategy currently implemented

### 4.1 Payload size guard (configurable)

- Config key: `KIRO_MAX_PAYLOAD_BYTES`
- Default: `590000` (safety headroom below ~615 KB reports)
- Legacy alias: `KIRO_MAX_PAYLOAD_CHARS` (deprecated, interpreted as bytes)

### 4.2 Optional history-entry cap (disabled by default)

- Config key: `KIRO_MAX_HISTORY_ENTRIES`
- Default: `0` (disabled)

This keeps gateway philosophy intact: do not cut by message count unless
operator explicitly opts in.

### 4.3 Post-trim structural sanitizer

After history trim:

- strip empty `toolUses` arrays
- remove orphaned structured `toolResults`
- preserve orphaned tool-result text in message content (to avoid data loss)

## 5) Gateway philosophy alignment

The current behavior aims to remain aligned with project philosophy:

- no blanket context truncation by default
- mutate only when needed for upstream validity
- preserve user-visible information where possible
- keep risky thresholds configurable

## 6) Code audit: non-ideal / technical debt areas

These are not immediate blockers, but should be cleaned up.

### A) `build_kiro_payload` is still too monolithic

File: `kiro/converters_core.py`

The function performs conversion, role normalization, legacy compatibility,
payload assembly, size trimming, and structural repair in one place.

Risk: hard to reason about mutation order; easier to regress.

### B) Front-pop trimming loops are O(n)

File: `kiro/converters_core.py`

Repeated `history.pop(0)` loops are acceptable at current scales but not ideal.
Prefer index slicing or deque-based trimming for cleaner complexity.

### C) User-visible marker text is currently hardcoded

File: `kiro/converters_core.py`

The marker `[Orphaned tool result]` is practical but hardcoded and English-only.
Should become a configurable/internalized message template.

### D) Synthetic message insertion remains broad

Files:

- `kiro/converters_core.py`
- `kiro/middleware/tool_pairing_validator.py`

Synthetic repairs are necessary for malformed streams, but should remain tightly
scoped and ideally share one central repair policy to avoid divergent behavior.

## 7) Recommended next cleanup steps (engineering plan)

1. Extract payload-size + orphan sanitizer into dedicated middleware module
   (single mutation stage, easier testing).
2. Replace front-pop trimming loops with index-window trimming helper.
3. Add integration test matrix for payload bytes around threshold
   (e.g., 580KB, 600KB, 620KB synthetic fixtures).
4. Make orphan-preservation marker configurable (or structured metadata only).
5. Keep legacy alias `KIRO_MAX_PAYLOAD_CHARS`, but document deprecation timeline.

## 8) Configuration reference

### New / relevant keys

- `KIRO_MAX_PAYLOAD_BYTES` (default: `590000`)
- `KIRO_MAX_HISTORY_ENTRIES` (default: `0`)
- `TOOL_RESULT_GUARD_ENABLED` (default: `true`)
- `TOOL_CALL_ARGS_GUARD_ENABLED` (default: `true`)
- `QUEUED_ANNOUNCE_GUARD_ENABLED` (default: `true`)
- `TOOL_PAIRING_VALIDATOR_ENABLED` (default: `true`)
- `MESSAGE_STRUCTURE_VALIDATOR_ENABLED` (default: `true`)
- `REACTIVE_RETRY_ENABLED` (default: `true`)
- `REACTIVE_RETRY_MAX_ATTEMPTS` (default: `1`)

### Suggested operator defaults

- Leave `KIRO_MAX_HISTORY_ENTRIES=0`
- Keep `KIRO_MAX_PAYLOAD_BYTES=590000` unless upstream behavior changes
- If strict transparent mode is preferred, disable tool-size guards and validators
  explicitly in `.env`
- Enable validators only for clients with repeatedly malformed tool/message flow
- Tune only after observing real traffic + logs

## 9) Devil's-advocate PR review (against upstream philosophy)

If this branch were reviewed as a PR against `jwadow/kiro-gateway`, strongest
criticisms would likely be:

1. Too much mutation in one place (`build_kiro_payload`) without fully extracting
   all compatibility logic into isolated modules.
2. Synthetic-message repair paths can be seen as content intervention.
3. Historical compatibility code + new middleware can look like overlapping systems.

What was improved to reduce those risks:

- Kept intervention defaults enabled for reliability, while documenting explicit
  operator opt-out toggles in `.env` for stricter transparent mode.
- Removed double-application of old/new guards in payload build flow.
- Kept history-count trimming disabled by default (`KIRO_MAX_HISTORY_ENTRIES=0`).
- Kept payload cap configurable and documented with external evidence.

Remaining PR risk level: **medium** (mostly architectural size/complexity, not correctness).
