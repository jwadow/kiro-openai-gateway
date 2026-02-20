# Beads PRD Template

**Bead:** bd-2sl  
**Created:** 2026-02-20  
**Status:** Draft

## Bead Metadata

```yaml
depends_on: []
parallel: true
conflicts_with: []
blocks: []
estimated_hours: 6
```

---

## Problem Statement

### What problem are we solving?

Current auth credential flow is effectively single-account: credentials are loaded from one JSON/env source and runtime token usage revolves around one active account context. This creates throughput and reliability limits when one account is rate-limited, invalid, or exhausted. The requested behavior is to store multiple Kiro auth accounts in DB and rotate usage via round-robin selection.

### Why now?

The current single-account flow blocks scale and resiliency for concurrent gateway traffic. Cost of inaction is elevated failure rate concentration on one account, reduced request distribution fairness, and manual operational work to swap credentials.

### Who is affected?

- **Primary users:** Operators running Kiro Gateway for multiple concurrent clients.
- **Secondary users:** End users of OpenAI-compatible and Anthropic-compatible endpoints who depend on stable latency and reduced auth-related failures.

---

## Scope

### In-Scope

- Define DB-backed multi-account credential storage model for Kiro auth entries.
- Load account pool from DB at startup and/or refresh points.
- Implement deterministic round-robin account selection for request authentication.
- Keep existing token refresh behavior, but target refresh and persistence to the selected account.
- Add failure handling for unusable accounts (temporary skip/quarantine rules).
- Add comprehensive tests for account loading, rotation fairness, concurrency safety, and fallback behavior.
- Keep backward compatibility for existing env/json credential paths during migration.

### Out-of-Scope

- Replacing authentication protocol (Kiro Desktop vs AWS SSO OIDC logic stays intact).
- New API endpoints for account management UI.
- Non-auth routing/load-balancing logic beyond account selection.
- Changes to message conversion, streaming protocols, or model resolution behavior.

---

## Proposed Solution

### Overview

Extend the auth manager from single-active-account state to an account pool abstraction backed by DB records, with atomic round-robin index advancement per request. The selected account drives token retrieval/refresh/persistence for that request. Invalid or repeatedly failing accounts are temporarily skipped, while preserving compatibility with existing env/json flows as bootstrap or fallback.

### User Flow (if user-facing)

1. Operator provisions multiple Kiro credential records in DB.
2. Gateway loads account pool and starts serving traffic.
3. Each incoming request selects the next eligible account by round-robin and performs normal token validation/refresh.

---

## Requirements

### Functional Requirements

#### Multi-Account Credential Pool

Gateway must load and maintain multiple credential records from DB instead of a single in-memory account.

**Scenarios:**

- **WHEN** DB contains N valid accounts **THEN** auth manager exposes an account pool of size N.
- **WHEN** DB contains malformed or expired-only records **THEN** invalid records are skipped with actionable logs.

#### Round-Robin Account Selection

Gateway must assign requests to accounts using deterministic round-robin over eligible accounts.

**Scenarios:**

- **WHEN** sequential requests arrive and all accounts are healthy **THEN** account selection cycles A->B->C->A.
- **WHEN** one account is quarantined **THEN** selection skips quarantined account and continues across remaining accounts.

#### Account-Scoped Token Refresh and Persistence

Refresh and persistence must apply to the selected account source record, not global singleton state.

**Scenarios:**

- **WHEN** selected account token nears expiry **THEN** only that account is refreshed and persisted.
- **WHEN** refresh fails with retriable condition **THEN** fallback/retry follows existing rules without corrupting other accounts.

#### Backward-Compatible Credential Source Handling

Existing env/json source paths must continue to work for users not yet migrated to DB pool mode.

**Scenarios:**

- **WHEN** DB pool is not configured **THEN** gateway behavior matches current single-source behavior.
- **WHEN** DB pool is configured **THEN** pool mode is used without breaking current route integrations.

### Non-Functional Requirements

- **Performance:** Account selection adds O(1) overhead per request and no measurable regression in endpoint p95 latency.
- **Security:** Tokens and secrets must never be logged; failure logs remain actionable but sanitized.
- **Accessibility:** N/A (backend-only change).
- **Compatibility:** Existing OpenAI/Anthropic endpoints and current auth flows (Desktop/OIDC) remain compatible.

---

## Success Criteria

- [ ] Gateway can load multiple auth accounts from DB and expose pool health at runtime logs.
  - Verify: `pytest tests/unit/test_auth_manager.py -k "sqlite or account_pool" -v`
- [ ] Round-robin selection distributes requests across eligible accounts in deterministic order.
  - Verify: `pytest tests/unit/test_auth_manager.py -k "round_robin" -v`
- [ ] Refresh/persist logic updates only selected account, preserving account isolation under concurrency.
  - Verify: `pytest tests/unit/test_auth_manager.py -k "refresh and concurrency" -v`
- [ ] OpenAI and Anthropic routes continue working unchanged while receiving auth tokens from pool mode.
  - Verify: `pytest tests/unit/test_routes_openai.py tests/unit/test_routes_anthropic.py -v`
- [ ] Full test suite remains green with no network access.
  - Verify: `pytest -v`

---

## Technical Context

### Existing Patterns

- `kiro/auth.py:82` - `KiroAuthManager` is central auth lifecycle owner; currently models single active credential context.
- `kiro/auth.py:199` - `_load_credentials_from_sqlite` currently loads first matching token key only.
- `kiro/auth.py:760` - `get_access_token` is lock-protected entrypoint for token retrieval/refresh.
- `main.py:338` - App lifespan creates one shared `KiroAuthManager` used by all requests.
- `kiro/routes_openai.py:265` - OpenAI route pulls shared `auth_manager` from `app.state`.
- `kiro/routes_anthropic.py:257` - Anthropic route uses same shared auth manager path.

### Key Files

- `kiro/auth.py` - Core credential loading, token refresh, persistence, and auth-type detection.
- `main.py` - Startup config validation and auth manager initialization.
- `kiro/config.py` - Credential source env vars and refresh/retry constants.
- `kiro/http_client.py` - Request retry and token usage integration point.
- `tests/unit/test_auth_manager.py` - Primary auth behavior coverage and regression test location.
- `tests/unit/test_config.py` - Config/env handling expectations.

### Affected Files

Files this bead will modify (for conflict detection):

```yaml
files:
  - kiro/auth.py # Introduce account pool model and round-robin selector
  - kiro/config.py # Add/adjust DB pool configuration toggles
  - main.py # Update initialization/validation flow for pool mode
  - kiro/http_client.py # Ensure selected account token path integrates safely
  - tests/unit/test_auth_manager.py # Add multi-account/rotation/concurrency tests
  - tests/unit/test_config.py # Add config compatibility tests for pool mode
```

---

## Risks & Mitigations

| Risk                                                 | Likelihood | Impact | Mitigation                                                                                   |
| ---------------------------------------------------- | ---------- | ------ | -------------------------------------------------------------------------------------------- |
| Account state races under concurrent requests        | Medium     | High   | Keep account selection and token mutation lock-scoped; test with concurrent access scenarios |
| Refresh failures repeatedly pick bad account         | Medium     | Medium | Add temporary quarantine/cooldown and retry next eligible account                            |
| Backward compatibility regression for env/json users | Low        | High   | Keep legacy source path intact behind explicit mode detection and regression tests           |
| DB schema mismatch with existing kiro-cli storage    | Medium     | Medium | Define adapter layer and validation; fail fast with clear logs                               |

---

## Open Questions

| Question                                                                                                                 | Owner       | Due Date   | Status |
| ------------------------------------------------------------------------------------------------------------------------ | ----------- | ---------- | ------ |
| Should pool mode reuse existing `auth_kv` key format or introduce a dedicated table/namespace for multi-account records? | Engineering | 2026-02-21 | Open   |

---

## Tasks

Write tasks in a machine-convertible format for `prd-task` skill.

### Define DB account pool model [design]

A validated account record model and DB read path exist that can load multiple auth accounts with health metadata.

**Metadata:**

```yaml
depends_on: []
parallel: false
conflicts_with: []
files:
  - kiro/auth.py
  - kiro/config.py
```

**Verification:**

- `pytest tests/unit/test_auth_manager.py -k "sqlite and load" -v`

### Implement round-robin selector with eligibility filtering [feature]

Auth manager can atomically select next eligible account using deterministic round-robin while skipping quarantined accounts.

**Metadata:**

```yaml
depends_on: ["Define DB account pool model"]
parallel: false
conflicts_with: []
files:
  - kiro/auth.py
```

**Verification:**

- `pytest tests/unit/test_auth_manager.py -k "round_robin or quarantine" -v`

### Apply account-scoped refresh and persistence [feature]

Token refresh and save operations target the selected account record only, preserving isolation between accounts.

**Metadata:**

```yaml
depends_on: ["Implement round-robin selector with eligibility filtering"]
parallel: false
conflicts_with: []
files:
  - kiro/auth.py
  - kiro/http_client.py
```

**Verification:**

- `pytest tests/unit/test_auth_manager.py -k "refresh and retry and sqlite" -v`

### Wire pool mode into app startup and route compatibility paths [integration]

Application startup initializes pool-capable auth manager without breaking existing OpenAI/Anthropic request paths.

**Metadata:**

```yaml
depends_on: ["Apply account-scoped refresh and persistence"]
parallel: false
conflicts_with: []
files:
  - main.py
  - kiro/routes_openai.py
  - kiro/routes_anthropic.py
```

**Verification:**

- `pytest tests/unit/test_routes_openai.py tests/unit/test_routes_anthropic.py -v`

### Add regression and concurrency test coverage for pool mode [test]

Comprehensive tests prove multi-account loading, deterministic rotation, failure skip logic, and backward compatibility.

**Metadata:**

```yaml
depends_on: ["Wire pool mode into app startup and route compatibility paths"]
parallel: false
conflicts_with: []
files:
  - tests/unit/test_auth_manager.py
  - tests/unit/test_config.py
```

**Verification:**

- `pytest tests/unit/test_auth_manager.py tests/unit/test_config.py -v`
- `pytest -v`

---

## Notes

- This PRD specifies requirements and implementation tasks only; no production code changes are part of `/create`.
- Existing singleton auth-manager integration in routes should be preserved while internal account selection becomes pool-based.
