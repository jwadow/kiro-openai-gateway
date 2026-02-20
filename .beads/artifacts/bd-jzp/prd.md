# Beads PRD

**Bead:** bd-jzp  
**Created:** 2026-02-17  
**Status:** Draft

## Bead Metadata

```yaml
depends_on: []
parallel: true
conflicts_with: []
blocks: []
estimated_hours: 12
```

---

## Problem Statement

### What problem are we solving?

The gateway currently authenticates all clients with one shared `PROXY_API_KEY`, which cannot isolate users or enforce per-user billing. The target behavior is to validate incoming API keys against MongoDB `usersNew.apiKey`, then check and deduct per-user credits from `creditsNew` based on model-specific pricing.

### Why now?

This gateway is used to expose Kiro externally to multiple users. Without user-level API key auth and credit enforcement, cost control and tenant isolation are weak, and abuse or over-usage cannot be controlled per user.

### Who is affected?

- **Primary users:** Gateway operators and API consumers using individual API keys.
- **Secondary users:** Finance/ops stakeholders who need accurate usage-to-credit charging.

---

## Scope

### In-Scope

- Add configurable auth source switch (`env` vs `mongodb`) and MongoDB-based API key validation.
- Validate API key against `usersNew.apiKey` (active users only).
- Check available credits in `creditsNew` before request execution.
- Deduct credits after usage is known, using model pricing from env JSON.
- Support provided pricing for Sonnet 4.5 and Haiku 4.5, including multiplier.
- Handle unknown model policy (`reject`, `free`, `default`).
- Add tests covering auth, sufficient-credit checks, pricing, deduction, and edge cases.

### Out-of-Scope

- Replacing Kiro upstream auth (`KIRO_CREDS_FILE`, refresh token flow).
- New admin UI, analytics dashboard, or invoice generation.
- Multi-database support beyond configured MongoDB instance.
- Changing request/response protocol compatibility with OpenAI/Anthropic APIs.

---

## Proposed Solution

### Overview

Introduce a billing/auth layer in the Python gateway that resolves the caller from MongoDB by API key, evaluates model pricing from environment configuration, performs a preflight sufficient-credit check, then applies atomic credit deduction once final usage is available (stream end or non-stream completion). Preserve legacy mode by keeping `PROXY_API_KEY` when `API_KEY_SOURCE=env`.

### User Flow

1. Client sends OpenAI/Anthropic request with API key.
2. Gateway validates key from selected source (`env` or MongoDB `usersNew.apiKey`).
3. Gateway resolves model pricing and ensures sufficient credits.
4. Gateway forwards request to Kiro and collects final usage.
5. Gateway atomically deducts credits from `creditsNew` and returns normal response.

---

## Requirements

### Functional Requirements

#### API Key Source Selection

Gateway must support two auth modes with explicit runtime config.

**Scenarios:**

- **WHEN** `API_KEY_SOURCE=env` **THEN** existing `PROXY_API_KEY` behavior remains unchanged.
- **WHEN** `API_KEY_SOURCE=mongodb` **THEN** gateway validates against `usersNew.apiKey` and rejects unknown/inactive keys.

#### MongoDB User Lookup

Gateway must map incoming API key to a user identity for billing.

**Scenarios:**

- **WHEN** key exists and user is active **THEN** request can proceed to billing checks.
- **WHEN** key is missing, invalid, or user inactive **THEN** return auth error with actionable message.

#### Preflight Credit Validation

Gateway must enforce sufficient credits before calling upstream when billing is enabled.

**Scenarios:**

- **WHEN** credits are below required threshold **THEN** reject request with insufficient-credit error.
- **WHEN** billing enforcement is disabled **THEN** request proceeds without blocking.

#### Pricing by Model

Gateway must price requests using model-specific configuration and fallback policy.

**Scenarios:**

- **WHEN** model ID is found in `BILLING_MODEL_PRICES_JSON` **THEN** use configured input/output/cache rates and multiplier.
- **WHEN** model ID is not found **THEN** apply `BILLING_UNKNOWN_MODEL_POLICY` (`reject`, `free`, or `default`).

#### Credit Deduction

Gateway must deduct credits safely and exactly once per request processing outcome.

**Scenarios:**

- **WHEN** usage is finalized **THEN** compute charge and atomically decrement user credits.
- **WHEN** deduction would underflow balance **THEN** fail with consistent error and log context.

### Non-Functional Requirements

- **Performance:** Auth lookup and credit check add minimal overhead and must not block streaming responsiveness.
- **Security:** Do not log raw API keys or secrets; validate headers consistently across OpenAI and Anthropic routes.
- **Reliability:** Deduction path must be race-safe under concurrent requests.
- **Compatibility:** Preserve existing API schemas and success/error envelope conventions.

---

## Success Criteria

- [ ] MongoDB auth mode accepts valid `usersNew.apiKey` and rejects invalid/inactive keys for both route families.
  - Verify: `pytest tests/unit/test_routes_openai.py -v`
  - Verify: `pytest tests/unit/test_routes_anthropic.py -v`
- [ ] Billing logic computes per-model charge with multiplier and unknown-model policy handling.
  - Verify: `pytest tests/unit/test_billing.py -v`
- [ ] Requests with insufficient credits are rejected before upstream call when enforcement is enabled.
  - Verify: `pytest tests/unit/test_routes_openai.py -v`
  - Verify: `pytest tests/unit/test_routes_anthropic.py -v`
- [ ] Credits are deducted atomically for successful requests and reflected in response usage metadata where applicable.
  - Verify: `pytest tests/unit/test_streaming_openai.py -v`
  - Verify: `pytest tests/integration/test_full_flow.py -v`
- [ ] Full regression suite passes with no network violations.
  - Verify: `pytest -v`

---

## Technical Context

### Existing Patterns

- Route-level auth gate for OpenAI: `kiro/routes_openai.py` (`verify_api_key`).
- Route-level auth gate for Anthropic: `kiro/routes_anthropic.py` (`verify_anthropic_api_key`).
- Env-based config parsing and raw `.env` support: `kiro/config.py`.
- Model normalization/resolution in converters/resolver: `kiro/converters_openai.py`, `kiro/converters_anthropic.py`, `kiro/model_resolver.py`.
- Usage event parsing and final usage payload emission: `kiro/parsers.py`, `kiro/streaming_core.py`, `kiro/streaming_openai.py`, `kiro/streaming_anthropic.py`.

### Key Files

- `kiro/config.py` - New billing/auth source flags and pricing config parsing.
- `kiro/routes_openai.py` - OpenAI auth and preflight credit check integration.
- `kiro/routes_anthropic.py` - Anthropic auth and preflight credit check integration.
- `kiro/streaming_openai.py` - Final usage/credits attachment point for billing result.
- `tests/unit/test_routes_openai.py` - Auth and preflight guard coverage.
- `tests/unit/test_routes_anthropic.py` - Anthropic auth mode and guard coverage.
- `tests/unit/test_streaming_openai.py` - Final usage and credits behavior.

### Affected Files

```yaml
files:
  - kiro/config.py # parse API_KEY_SOURCE, MongoDB settings, pricing settings
  - kiro/routes_openai.py # integrate MongoDB auth and credit precheck
  - kiro/routes_anthropic.py # integrate MongoDB auth and credit precheck
  - kiro/streaming_openai.py # carry finalized credit usage in OpenAI responses
  - kiro/parsers.py # confirm usage fields needed for billing calculation
  - kiro/streaming_core.py # ensure usage propagation for deduction inputs
  - kiro/billing.py # new pricing and deduction orchestration module
  - kiro/mongodb_store.py # new MongoDB data access for usersNew/creditsNew
  - tests/unit/test_routes_openai.py # auth source and insufficient credit tests
  - tests/unit/test_routes_anthropic.py # auth source and insufficient credit tests
  - tests/unit/test_billing.py # new pricing math and policy tests
  - tests/integration/test_full_flow.py # end-to-end auth+billing regression
```

---

## Risks & Mitigations

| Risk                                                         | Likelihood | Impact | Mitigation                                                                                        |
| ------------------------------------------------------------ | ---------- | ------ | ------------------------------------------------------------------------------------------------- |
| Double charge on retries/stream reconnect                    | Medium     | High   | Use request-level idempotency key and ledger record checks before deduction finalization.         |
| Race condition on concurrent deductions                      | Medium     | High   | Use atomic MongoDB updates with guarded balance checks (`$inc` + sufficient-balance filter).      |
| Model ID mismatch between resolver and pricing config        | Medium     | Medium | Price using canonical normalized model ID and add explicit tests for known aliases/date suffixes. |
| Unknown model leads to free usage or false rejections        | Medium     | Medium | Enforce explicit unknown model policy and audit logs with safe metadata.                          |
| Backward compatibility regression for existing env-key users | Low        | High   | Keep default `env` mode and verify legacy route tests still pass.                                 |

---

## Open Questions

| Question                                                                                                     | Owner               | Due Date       | Status |
| ------------------------------------------------------------------------------------------------------------ | ------------------- | -------------- | ------ |
| Should deduction happen only after final usage, or reserve upfront then settle?                              | Product/Engineering | Before `/ship` | Open   |
| What is the minimum reserve heuristic for preflight check on streaming requests?                             | Engineering         | Before `/ship` | Open   |
| Is `creditsNew.credits` authoritative balance, or should we maintain a separate immutable ledger collection? | Product/DB Owner    | Before `/ship` | Open   |

---

## Tasks

### Implement auth source switch and MongoDB API key validation [backend]

Gateway auth dependencies accept both legacy env mode and MongoDB mode, with active-user validation by `usersNew.apiKey`.

**Metadata:**

```yaml
depends_on: []
parallel: false
conflicts_with: []
files:
  - kiro/config.py
  - kiro/routes_openai.py
  - kiro/routes_anthropic.py
  - kiro/mongodb_store.py
```

**Verification:**

- `pytest tests/unit/test_routes_openai.py -v`
- `pytest tests/unit/test_routes_anthropic.py -v`

### Implement model pricing parser and charge calculator [backend]

Billing module can compute deterministic charges from usage and model pricing JSON, including unknown-model policies.

**Metadata:**

```yaml
depends_on: []
parallel: true
conflicts_with: []
files:
  - kiro/config.py
  - kiro/billing.py
  - tests/unit/test_billing.py
```

**Verification:**

- `pytest tests/unit/test_billing.py -v`

### Add preflight sufficient-credit enforcement [backend]

Routes perform credit sufficiency checks before upstream execution when billing is enabled and enforcement is true.

**Metadata:**

```yaml
depends_on:
  - Implement auth source switch and MongoDB API key validation
  - Implement model pricing parser and charge calculator
parallel: false
conflicts_with: []
files:
  - kiro/routes_openai.py
  - kiro/routes_anthropic.py
  - kiro/billing.py
```

**Verification:**

- `pytest tests/unit/test_routes_openai.py -v`
- `pytest tests/unit/test_routes_anthropic.py -v`

### Add post-usage atomic credit deduction [backend]

Credits are atomically decremented in `creditsNew` from finalized usage for non-streaming and streaming completion paths.

**Metadata:**

```yaml
depends_on:
  - Add preflight sufficient-credit enforcement
parallel: false
conflicts_with: []
files:
  - kiro/billing.py
  - kiro/routes_openai.py
  - kiro/routes_anthropic.py
  - kiro/streaming_openai.py
```

**Verification:**

- `pytest tests/unit/test_streaming_openai.py -v`
- `pytest tests/integration/test_full_flow.py -v`

### Extend test coverage for concurrency and edge cases [test]

Tests cover retry/idempotency, unknown model policies, balance underflow prevention, and legacy env-mode compatibility.

**Metadata:**

```yaml
depends_on:
  - Add post-usage atomic credit deduction
parallel: false
conflicts_with: []
files:
  - tests/unit/test_routes_openai.py
  - tests/unit/test_routes_anthropic.py
  - tests/unit/test_billing.py
  - tests/integration/test_full_flow.py
```

**Verification:**

- `pytest tests/unit/ -v`
- `pytest tests/integration/test_full_flow.py -v`

---

## Notes

- Pricing uses the provided Sonnet/Haiku model rates and multiplier definitions from env.
- PRD intentionally avoids implementation-level code; it defines expected end state and verification only.
