# Kiro Gateway Migration Context (Full)

This file is a full handoff/context document for continuing work on thinking policy migration, Anthropic/OpenCode compatibility, and auth behavior.

---

## 1) Original Objective

Main objective was to stop forcing max/default fake thinking and make gateway respect request-level thinking controls coming from clients (OpenCode, Anthropic SDK style, OpenAI SDK style).

Target behavior:

- If request includes thinking/reasoning hints -> use them.
- If no hints are provided -> use gateway default fallback.
- Fallback should now be **thinking OFF by default** unless explicitly enabled.

---

## 2) High-Level Features Implemented

### Feature A: Request-driven thinking policy engine

Added a dedicated resolver module:

- `kiro/thinking_policy.py`

What it does:

- Normalizes and resolves thinking mode for each request.
- Supports body + header hints.
- Supports Anthropic-style request thinking levels with `high` and `max` modes.
- Precedence:
  1. body numeric budget
  2. body effort/mode
  3. header hints
  4. default fallback (`FAKE_REASONING_*`)
- Supports OpenAI-style and Anthropic-style hint formats and aliases.
- Handles explicit disable (`off/none/disabled`) and numeric budgets.
- Applies min/max clamping for explicit numeric budgets.

### Feature B: Converter/route wiring for both APIs

Wired policy resolution into request conversion flow:

- `kiro/converters_openai.py`
- `kiro/converters_anthropic.py`
- `kiro/routes_openai.py`
- `kiro/routes_anthropic.py`
- `kiro/converters_core.py`

Result:

- Injection of `<thinking_mode>` tags is now per-request.
- Max thinking budget is per-request (`thinking_max_tokens`).
- Default fallback can remain no-thinking (`FAKE_REASONING=false`) while still honoring explicit request-level thinking hints.

### Feature C: Social-login token routing stability (SQLite)

Observed real-world issue: `kirocli:social:token` can coexist with OIDC device-registration rows in SQLite.

Without social guard, auth was misdetected as OIDC and refresh failed with `invalid_grant`.

Implemented guard in:

- `kiro/auth.py`

Behavior:

- If token source is social (`kirocli:social:token` or provider marker), route refresh to Kiro Desktop flow.
- Skip loading OIDC device-registration for social token source.

### Feature D: TLS safety as env-driven feature

Replaced hardcoded untrusted TLS behavior with config-based control:

- `ALLOW_UNTRUSTED_TLS` in `kiro/config.py`
- Used in `main.py`, `kiro/http_client.py`, `kiro/auth.py`

Default remains secure (`verify=True` unless opt-in override).

---

## 3) OpenCode / Provider Work and Findings

### What was attempted

- Built custom Anthropic provider profile in local OpenCode config (`~/.config/opencode/opencode.json`), with thinking variants.
- Later simplified to Anthropic-only custom provider and removed off variant per new requirement.

### Key finding about original built-in Anthropic provider auth error

Observed error:

`Invalid or missing API key. Use x-api-key header or Authorization: Bearer.`

Root cause:

- Built-in provider was using a different key than gateway `PROXY_API_KEY`.

Compatibility actions performed:

1. Added `PROXY_API_KEY_ALIASES` (comma-separated) in config.
2. Anthropic auth now accepts:
   - `x-api-key`
   - `api-key`
   - `Authorization: Bearer ...`
3. `.env` local updated with alias containing the test key used by built-in provider.

Validation result:

- With valid alias key, request reaches upstream logic and no longer fails with 401 auth error.
- In this environment, upstream currently fails at SSL verify stage (502), which confirms auth passed.

---

## 4) Thinking Mode Strategy (Current Intent)

New explicit product decision:

- Anthropic side should expose `high` and `max` only (no `off` variant in OpenCode profile).
- Default fallback should be OFF when no thinking hints are sent.

Implemented:

- `FAKE_REASONING` default behavior changed to OFF semantics in `kiro/config.py`.
- Added explicit behavior in core converter so thinking-system prompt addition is only injected when request resolved to inject thinking.

Important nuance:

- Thinking injection is now controlled by request policy decision, not by global default toggle alone.

---

## 5) Why old behavior was problematic

### Problem 1: Over-eager thinking by default

- Previously fake thinking default was effectively enabled unless explicitly disabled.
- This made clients see thinking even when they didn’t request it.

### Problem 2: Mixed auth key assumptions in SDK clients

- Different SDK/provider combinations send different auth headers and keys.
- Gateway only checking one exact form caused avoidable auth mismatches.

### Problem 3: Social token + device-registration coexistence

- Existing auth detection over-relied on presence of client ID/secret.
- Could choose wrong refresh flow for social tokens and break session longevity.

---

## 6) Tests and Runtime Verification Done

### Verified

- Route auth tests for OpenAI + Anthropic API key verification pass after recent auth compatibility updates.
- Payload-level checks confirm:
  - No thinking tags in default (no hints) path.
  - `high` budget maps to 3000 tag.
  - `max` budget maps to 4000 tag.

### Runtime notes

- Gateway starts and handles requests.
- In this environment, upstream requests currently fail with SSL certificate verify error unless untrusted TLS mode is enabled.
- This SSL issue is environment/proxy cert related, not request auth compatibility.

---

## 7) Current Modified Files (working tree at handoff moment)

- `.env.example`
- `kiro/config.py`
- `kiro/converters_core.py`
- `kiro/routes_anthropic.py`

Note: many earlier changes are already committed in previous local commits.

---

## 8) Pending/Follow-up Work (from latest request)

1. Keep Anthropic thinking variants as `high` and `max` (no `off` variant in profile).
2. Keep default no-hint behavior as thinking OFF.
3. Ensure built-in OpenCode Anthropic provider works without auth mismatch by supporting expected header styles and alias keys.
4. If any remaining behavior requires larger API contract changes, reflect that in OpenCode config guidance.

---

## 9) Practical Ops Notes

- If using enterprise/proxy with MITM certs, set `ALLOW_UNTRUSTED_TLS=true` only if trusted.
- For mixed client migration, use:
  - `PROXY_API_KEY` as primary key
  - `PROXY_API_KEY_ALIASES` for temporary compatibility
- For builtin OpenCode provider tests, ensure the configured key is in either primary key or aliases.

---

## 10) Suggested Next Step for Next AI

- Run targeted tests for modified files only.
- Smoke-test built-in Anthropic provider with one known model and verify:
  - no 401 auth error
  - request reaches upstream path
- If SSL blocks runtime, treat it as env infra issue and separately document recommended cert/proxy setup.
