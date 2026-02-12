# Security Review

## Scope and method

- Reviewed auth, transport, request mutation, and error-handling controls.
- Cross-checked implementation defaults in runtime config and route wiring.

## Threat model

- Internet-exposed gateway endpoints protected by shared secret (`PROXY_API_KEY`).
- Upstream AWS/Kiro access token lifecycle and proxy/TLS traversal.
- Untrusted client payloads (tool results, tool args, long histories).

## Findings

### Critical

1. Static default gateway API key is insecure-by-default.
   - Evidence: `PROXY_API_KEY` fallback literal (`kiro/config.py:100`).
   - Impact: if operator forgets `.env`, endpoint auth is predictable.
   - Mitigation: enforce startup failure on default secret in non-dev mode.

### High

1. `SKIP_AUTH` can disable upstream bearer auth entirely.
   - Evidence: flag parsing (`kiro/config.py:501`), warning-only validation path (`main.py:225`), Authorization header removal (`kiro/http_client.py:222`).
   - Impact: policy bypass if misconfigured or leaked env.
   - Mitigation: add explicit double-confirm env and startup hard warning with process exit unless acknowledged.

2. TLS verification can be disabled globally.
   - Evidence: `ALLOW_UNTRUSTED_TLS` toggle (`kiro/config.py:134`), usage in shared client and auth refresh clients (`main.py:347`, `kiro/auth.py:654`, `kiro/auth.py:780`).
   - Impact: MITM exposure on upstream traffic when enabled.
   - Mitigation: keep default off (already done), add certificate pinning/trust-store docs and startup warning banner (currently warning exists at `main.py:350`).

### Medium

1. Auth behavior differs across API surfaces.
   - Evidence: Anthropic accepts key aliases and multiple headers (`kiro/routes_anthropic.py:98`), OpenAI route accepts only exact bearer for primary key (`kiro/routes_openai.py:85`).
   - Impact: migration confusion and uneven access control expectations.
   - Mitigation: either harmonize both routes or document deliberate asymmetry.

2. Synthetic mutation guards may alter user-visible semantics.
   - Evidence: placeholder tool_result injection (`kiro/middleware/tool_pairing_validator.py:71`), queued announce compaction (`kiro/middleware/queued_announce_compactor.py:85`).
   - Impact: content integrity concerns for strict proxy users.
   - Mitigation: provide one-shot strict profile to disable all mutating middleware.

## Positive controls

- Token refresh flow uses lock-protected concurrency (`kiro/auth.py:858`).
- Retry logic classifies network failures with user-safe messages (`kiro/http_client.py:300`).
- Oversized payload controls reduce opaque upstream 400 loops (`kiro/payload_guards.py:128`).

## Security verdict

- Overall: **acceptable with hardening required before broad public deployment**.
- Must-fix before production-by-default posture:
  1. Block static default `PROXY_API_KEY`.
  2. Add explicit acknowledgement guard for `SKIP_AUTH`.
