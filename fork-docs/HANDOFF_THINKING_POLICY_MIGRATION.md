# Handoff Dossier: Thinking Policy Migration (Suffix Rollback -> API-Driven Policy)

> Superseded by canonical docs: `fork-docs/FORK_CHANGELOG.md`, `fork-docs/ARCHITECTURE_AUDIT.md`, `fork-docs/SECURITY_REVIEW.md`, `fork-docs/PR_REVIEW_SUMMARY.md`.
> Kept only as historical migration context.

Status: prepared for transfer to another AI engineer
Scope: `kiro-gateway` codebase + OpenCode integration notes
Authoring context: this document captures what was changed, what was reverted, what was learned, and a production-safe implementation plan

---

## 1) Executive Summary

This handoff document records a two-phase journey:

1. A suffix-based profile implementation was introduced (`-no-thinking`, `-low-thinking`, etc.).
2. That approach was deemed too close to model-hardcoding and less aligned with API standards.
3. The suffix-related code changes were rolled back in gateway source.
4. A new implementation plan is proposed: body/header-driven thinking policy resolution with env-driven budgets and minimal invasive changes.

Primary goal for next engineer:

- Implement a **request-driven** thinking policy resolver that:
  - uses incoming OpenAI/Anthropic fields,
  - falls back to current fake-reasoning defaults when absent,
  - does not alter the existing upstream fake thinking tag transport mechanism,
  - avoids hardcoded model profile aliases.

---

## 2) Explicit User Requirements (Normalized)

The user direction, normalized into engineering requirements:

1. Avoid radical rewrites.
2. Prefer standards-compliant request parsing over model-name suffix parsing.
3. Keep existing fake-reasoning upstream format intact.
4. Make behavior env-driven.
5. If API thinking params are absent, current `FAKE_REASONING_*` defaults should continue to apply.
6. If API thinking params are present, they override defaults.
7. OpenAI request mode should support levels equivalent to: `off|low|medium|high|xhigh`.
8. Anthropic request mode should support levels equivalent to: `off|high|max`.
9. Prepare configuration compatibility for both OpenCode and future OpenClaw flows.
10. Provide a complete transfer plan another AI can execute.

---

## 3) What Was Changed During Session (Historical)

### 3.1 Suffix-based thinking profile implementation (historical)

Implemented earlier (then rolled back):

- model suffix parsing in converters,
- config-level generated model aliases,
- dynamic thinking budget injection based on suffix,
- opencode model expansion into multiple profile models.

Why this was rejected:

- It encoded behavior into model names instead of API semantics.
- It introduced maintenance overhead and model-list clutter.
- It did not center on request-native fields (`reasoning_effort`, `thinking`, etc.).

### 3.2 Rollback actions performed

Rolled back to repository HEAD for the following files:

- `kiro/config.py`
- `kiro/converters_anthropic.py`
- `kiro/converters_core.py`
- `kiro/converters_openai.py`
- `kiro/model_resolver.py`

Rollback command used (record):

```bash
git restore -- "kiro/config.py" "kiro/converters_anthropic.py" "kiro/converters_core.py" "kiro/converters_openai.py" "kiro/model_resolver.py"
```

### 3.3 OpenCode config normalization

The prior custom model explosion for suffix profiles in `~/.config/opencode/opencode.json` was reset to a cleaner base-model set.

Current normalized state includes base models only:

- `claude-opus-4.6`
- `claude-opus-4.5`
- `claude-sonnet-4.5`
- `claude-sonnet-4`
- `claude-haiku-4.5`
- `claude-3.7-sonnet`

---

## 4) Repository State Notes

At the time of this handoff, there are unrelated modified files in working tree:

- `kiro/auth.py`
- `kiro/http_client.py`
- `main.py`

These were intentionally not touched during rollback, because they appear unrelated/user-owned in this session context.

There is also `venv/` tracked as untracked in status output for this environment snapshot.

---

## 5) Research Findings: API Semantics

### 5.1 OpenAI side

Relevant semantics:

- Chat/completions ecosystem commonly uses `reasoning_effort`.
- Responses-style payloads commonly use nested `reasoning.effort`.
- Reasoning effort levels include: `none|minimal|low|medium|high|xhigh`.

Practical mapping for gateway policy layer:

- `none` => off
- `minimal` => near-low (or dedicated minimal env if desired)
- `low|medium|high|xhigh` => mapped token budgets

### 5.2 Anthropic side

Relevant semantics in Messages API:

- `thinking` object with types such as `enabled|disabled|adaptive`.
- When `enabled`, budget can be provided through `thinking.budget_tokens`.
- `output_config.effort` also appears as an effort control signal in newer docs.

Project-specific requirement for this integration:

- expose only `off|high|max` policy levels for Anthropic-mode requests.

### 5.3 Header fallback

There is no universal standard "thinking header" accepted by all SDKs/tools.

Therefore recommended fallback:

- `x-reasoning-effort`
- `x-thinking-budget`
- `x-thinking-mode`

Only use headers when body fields are absent.

---

## 6) Architecture Proposal (Minimal + Professional)

Introduce one small module:

- `kiro/thinking_policy.py`

This module resolves:

- `inject_thinking: bool`
- `thinking_max_tokens: Optional[int]`

Inputs:

- parsed request model (OpenAI or Anthropic)
- raw request headers
- env configuration constants

Core rule:

- if no incoming thinking/reasoning directives, fallback to existing fake reasoning default behavior.

Non-goal:

- do not change fake-reasoning tag payload format or parsing path upstream.

---

## 7) Required Code Touchpoints (Planned)

### 7.1 `kiro/config.py`

Add only env knobs needed for policy resolver.

Keep existing:

- `FAKE_REASONING_ENABLED`
- `FAKE_REASONING_MAX_TOKENS`

Add env-driven mapping constants, example:

- OpenAI-style:
  - `THINKING_OPENAI_LOW_TOKENS`
  - `THINKING_OPENAI_MEDIUM_TOKENS`
  - `THINKING_OPENAI_HIGH_TOKENS`
  - `THINKING_OPENAI_XHIGH_TOKENS`
  - optional `THINKING_OPENAI_MINIMAL_TOKENS`
- Anthropic-style:
  - `THINKING_ANTHROPIC_HIGH_TOKENS`
  - `THINKING_ANTHROPIC_MAX_TOKENS`
- clamp:
  - `THINKING_MIN_TOKENS`
  - `THINKING_MAX_TOKENS`

### 7.2 `kiro/thinking_policy.py` (new)

Functions suggested:

- `resolve_openai_policy(request_data, headers) -> ThinkingPolicy`
- `resolve_anthropic_policy(request_data, headers) -> ThinkingPolicy`
- internal helpers:
  - parse effort
  - parse numeric budget
  - normalize synonyms
  - clamp budget
  - precedence resolver

Data structure:

```python
@dataclass
class ThinkingPolicy:
    inject_thinking: bool
    thinking_max_tokens: Optional[int]
    source: str  # for debug logs
```

### 7.3 `kiro/routes_openai.py`

Pass request headers into converter function (or directly resolver) with minimal signature change.

### 7.4 `kiro/routes_anthropic.py`

Same as above.

### 7.5 `kiro/converters_openai.py`

Remove any model-suffix dependency (already rolled back).

Add policy resolution call and pipe into core builder:

- `inject_thinking=policy.inject_thinking`
- `thinking_max_tokens=policy.thinking_max_tokens`

### 7.6 `kiro/converters_anthropic.py`

Same as OpenAI path.

### 7.7 `kiro/converters_core.py`

Do not alter tag format logic.

Only ensure it accepts per-request values from converter path (if not already present in target branch).

---

## 8) Precedence Rules (Normative)

Recommended precedence:

1. Explicit numeric budget from request body
2. Effort/mode from request body
3. Header fallback fields
4. Existing fake-reasoning defaults (env)

Body-over-header principle is mandatory.

---

## 9) Mapping Rules (Normative)

### 9.1 OpenAI route mapping

Accepted normalized levels:

- `off`, `low`, `medium`, `high`, `xhigh`

Alias normalization:

- `none` -> `off`
- `minimal` -> `low` (unless dedicated minimal env exists)

Unsupported value behavior:

- ignore invalid value and fallback to next source in precedence.

### 9.2 Anthropic route mapping

Accepted normalized levels:

- `off`, `high`, `max`

Body interpretation:

- `thinking.type == disabled` -> off
- `thinking.type == enabled` with `budget_tokens` -> numeric budget override
- `thinking.type == adaptive` -> map to high or env default (documented behavior)
- `output_config.effort`:
  - `low|medium|high|max` -> normalize to `high|max` according to project policy

### 9.3 Numeric budget rules

- parse integer
- clamp into `[THINKING_MIN_TOKENS, THINKING_MAX_TOKENS]`
- if parse fails, ignore and continue precedence chain

---

## 10) Logging Contract

For debuggability (without leaking secrets), log:

- resolved policy source
- normalized mode
- budget after clamp
- whether fallback default was used

Do not log API keys, auth headers, refresh tokens, raw confidential payloads.

---

## 11) Backward Compatibility

Hard constraints:

1. No change to existing fake-reasoning transport format.
2. No model alias hardcoding for thinking behavior.
3. Existing clients sending no reasoning fields should observe same default behavior.

---

## 12) Risk Register

R-01: ambiguous client payloads sending contradictory fields.

- Mitigation: strict precedence + deterministic normalization + tests.

R-02: Anthropics mode mismatch between SDK versions.

- Mitigation: parse `thinking` and `output_config.effort`; tolerant fallback.

R-03: invalid/bogus headers from proxies.

- Mitigation: headers are fallback only; body wins.

R-04: over-aggressive budgets increasing latency.

- Mitigation: env caps and clamp.

R-05: regression in routes due to signature changes.

- Mitigation: minimal route changes + unit/integration tests.

---

## 13) Testing Strategy

### 13.1 Unit tests

Create new tests for policy resolver:

- openai effort mapping
- openai nested reasoning mapping
- anthropic thinking type mapping
- anthropic output_config.effort mapping
- numeric budget parse and clamp
- precedence checks
- invalid value fallback

### 13.2 Converter tests

OpenAI converter tests:

- no policy input -> defaults
- `reasoning_effort=off` -> inject false
- `reasoning_effort=high` -> inject true with high budget

Anthropic converter tests:

- no policy input -> defaults
- `thinking.type=disabled` -> inject false
- `thinking.budget_tokens=...` -> inject true with exact/clamped budget

### 13.3 Route tests

- verify header fallback is consumed only when body fields absent.

### 13.4 Runtime smoke tests

- `/health`
- `/v1/models`
- `/v1/chat/completions` openai payload matrix
- `/v1/messages` anthropic payload matrix

---

## 14) OpenCode Integration Plan (Post-Implementation)

### 14.1 Why variants over duplicate models

OpenCode docs support provider/model variants and per-model options.

This is superior to creating many duplicate model IDs for thinking levels.

### 14.2 OpenAI-compatible provider config idea

Use `kiro-gateway` provider with base models; define variants that set:

- `reasoningEffort: low|medium|high|xhigh|none`

### 14.3 Anthropic provider-through-gateway option

If using gateway Anthropic route:

- set provider `npm` appropriately (`@ai-sdk/anthropic` when desired)
- `options.baseURL` to gateway
- variants for anthropic models with
  - `thinking.type: disabled` (off)
  - `thinking.type: enabled` + budget for high/max

---

## 15) OpenClaw Compatibility Notes

Observed concern:

- OpenClaw tracks thinking level internally but may not always serialize into same OpenAI field.

Design response:

- parse multiple body forms + header fallback.

Pragmatic expectation:

- this approach is resilient even if OpenClaw serialization evolves.

---

## 16) Migration Runbook (Step-by-Step)

1. Confirm clean branch baseline.
2. Add env constants in `config.py`.
3. Add `thinking_policy.py`.
4. Wire routes to pass headers.
5. Wire converters to apply resolver result.
6. Keep core fake-tag formatter unchanged.
7. Add unit tests.
8. Add integration tests.
9. Run full targeted test subset.
10. Manual smoke through curl + opencode.
11. Optional openclaw manual pass.
12. Document envs in `.env.example` and README.

---

## 17) Acceptance Criteria (Definition of Done)

Functional:

- openai body reasoning overrides default
- anthropic body thinking overrides default
- no body fields -> old default behavior preserved
- header fallback works when body absent

Non-functional:

- no model-suffix logic
- no changes to upstream fake tag format
- tests pass

---

## 18) Known Files and Paths (Operational Index)

Core:

- `kiro/config.py`
- `kiro/converters_core.py`
- `kiro/converters_openai.py`
- `kiro/converters_anthropic.py`
- `kiro/routes_openai.py`
- `kiro/routes_anthropic.py`

Tests:

- `tests/unit/test_converters_openai.py`
- `tests/unit/test_converters_anthropic.py`
- `tests/unit/test_converters_core.py`

Docs:

- `README.md`
- `.env.example`

---

## 19) Proposed Env Contract Draft

Draft envs to add (names can be revised):

```env
# OpenAI mapping budgets
THINKING_OPENAI_LOW_TOKENS=600
THINKING_OPENAI_MEDIUM_TOKENS=1800
THINKING_OPENAI_HIGH_TOKENS=3000
THINKING_OPENAI_XHIGH_TOKENS=4000

# Anthropic mapping budgets
THINKING_ANTHROPIC_HIGH_TOKENS=3000
THINKING_ANTHROPIC_MAX_TOKENS=4000

# Global clamp
THINKING_MIN_TOKENS=256
THINKING_MAX_TOKENS=120000
```

Fallback contract:

- if none of above triggered by request, continue using:
  - `FAKE_REASONING_ENABLED`
  - `FAKE_REASONING_MAX_TOKENS`

---

## 20) Detailed Implementation Blueprint

### 20.1 `ThinkingPolicy` dataclass

Fields:

- `inject_thinking: bool`
- `thinking_max_tokens: Optional[int]`
- `normalized_level: Optional[str]`
- `source: str`

### 20.2 Parsing helper contract

- `parse_openai_effort(...)`
- `parse_openai_nested_effort(...)`
- `parse_anthropic_thinking(...)`
- `parse_anthropic_output_effort(...)`
- `parse_header_effort(...)`
- `parse_header_budget(...)`

### 20.3 Edge case policy

- Empty strings -> ignored
- non-int budgets -> ignored
- negative budgets -> ignored
- out-of-range -> clamped

---

## 21) Example Payload Mapping Matrix

### OpenAI examples

1. `reasoning_effort: "none"` -> inject false
2. `reasoning_effort: "low"` -> inject true + low budget
3. `reasoning: { effort: "xhigh" }` -> inject true + xhigh budget
4. no reasoning fields -> default behavior

### Anthropic examples

1. `thinking: { type: "disabled" }` -> inject false
2. `thinking: { type: "enabled", budget_tokens: 9000 }` -> inject true + 9000(clamped)
3. `output_config: { effort: "max" }` -> inject true + anthropic max budget
4. no thinking fields -> default behavior

---

## 22) Security and Safety Considerations

- treat all header values as untrusted
- do not allow headers to force invalid/unsafe budgets beyond caps
- do not log secret tokens
- keep auth flow untouched

---

## 23) Performance Considerations

- policy resolver is lightweight parse-only logic
- avoid deep serialization and repeated parsing
- perform at converter boundary once per request

---

## 24) Observability Checklist

- add debug line with source + normalized level + budget
- add warning for malformed incoming effort/budget values
- preserve current error formatting behavior

---

## 25) Suggested Commit Strategy (for future implementation)

1. `feat(policy): add request-driven thinking policy resolver`
2. `feat(openai): wire reasoning_effort and header fallback`
3. `feat(anthropic): wire thinking/output_config and header fallback`
4. `test(policy): add precedence and mapping coverage`
5. `docs(config): add env mapping for thinking policy`

---

## 26) Handoff Quickstart for Next AI

If another AI picks this up, first actions:

1. confirm rollback done in source files listed in section 3.2
2. read section 8 and section 9 thoroughly
3. implement only new `thinking_policy.py` and minimal route/converter wiring
4. avoid touching core fake-tag semantics
5. run tests from section 13

---

## 27) Validation Commands (Reference)

Run from repo root:

```bash
"/home/anonim/kiro-gateway/venv/bin/python" -m pytest tests/unit/test_converters_openai.py -q
"/home/anonim/kiro-gateway/venv/bin/python" -m pytest tests/unit/test_converters_anthropic.py -q
"/home/anonim/kiro-gateway/venv/bin/python" -m pytest tests/unit/test_converters_core.py -q
```

Runtime checks:

```bash
curl -sS http://127.0.0.1:8000/health
curl -sS -H "Authorization: Bearer <PROXY_API_KEY>" http://127.0.0.1:8000/v1/models
```

---

## 28) Open Questions for Final Implementation

1. Should OpenAI `minimal` map to dedicated minimal budget or low?
2. For Anthropic `adaptive`, should mapping default to high or max?
3. Should budget clamp max be tied to model max output settings or remain independent?
4. Should invalid incoming values trigger warning or debug log only?

---

## 29) Transfer Checklist

- [x] rollback executed on suffix-related files
- [x] opencode local model explosion removed and normalized
- [x] detailed migration design captured
- [x] file index captured
- [x] test strategy captured
- [x] risks and mitigations captured

---

## 30) Appendix A — Decision Log (Detailed)

Format: `ID | Decision | Rationale | Outcome`

001 | Avoid model suffix control | non-standard coupling | accepted
002 | Keep fake tag protocol unchanged | protect existing pipeline | accepted
003 | Body fields have priority over headers | standards alignment | accepted
004 | Header fallback retained | client variability | accepted
005 | Do not mutate auth/session logic | scope control | accepted
006 | Keep env-driven budgets | operational flexibility | accepted
007 | Avoid hardcoded model maps | maintainability | accepted
008 | Introduce dedicated policy module | isolate complexity | accepted
009 | Preserve default behavior | backward compatibility | accepted
010 | Add explicit precedence rules | deterministic behavior | accepted
011 | Normalize OpenAI none->off | naming consistency | accepted
012 | Normalize OpenAI minimal->low | project preference | provisional
013 | Restrict anthropic levels to off/high/max | user requirement | accepted
014 | Parse output_config.effort | newer anthropic semantics | accepted
015 | Parse thinking.budget_tokens | explicit budget wins | accepted
016 | Clamp token budgets | abuse prevention | accepted
017 | Route passes headers into converter | minimal impact | accepted
018 | Converter resolves policy once | perf and clarity | accepted
019 | Avoid route-level business branching | clean layering | accepted
020 | Add resolver unit tests first | reduce regression | accepted
021 | Add converter wiring tests | verify integration | accepted
022 | Add runtime smoke matrix | practical verification | accepted
023 | Keep log details non-sensitive | security baseline | accepted
024 | Use debug-level source reporting | troubleshooting | accepted
025 | Ignore malformed hints gracefully | robustness | accepted
026 | Prefer stable defaults if ambiguous | safety | accepted
027 | Keep anthropic adaptive deterministic | avoid unpredictable behavior | accepted
028 | Avoid touching stream parsers | scope minimization | accepted
029 | Avoid touching model resolver | remove suffix complexity | accepted
030 | Track rollback as explicit step | auditability | accepted
031 | Keep unrelated dirty files untouched | user ownership respect | accepted
032 | Preserve venv execution path | environment consistency | accepted
033 | Keep docs update in same PR | operational clarity | accepted
034 | Add `.env.example` entries | discoverability | accepted
035 | Mention openclaw uncertainty | realistic interoperability | accepted
036 | Add fallback headers list | compatibility safety net | accepted
037 | Body value precedence hard requirement | prevent proxy side-effects | accepted
038 | Unknown effort values ignored | graceful degradation | accepted
039 | Numeric budget parse strict int | avoid accidental parsing | accepted
040 | Negative budget invalid | semantic correctness | accepted
041 | Zero budget means off | explicit disabling semantics | accepted
042 | If off then budget cleared | avoid contradictory state | accepted
043 | Add source enum string | troubleshooting traceability | accepted
044 | Avoid mutable globals | thread safety | accepted
045 | Keep resolver pure/stateless | testability | accepted
046 | Minimize converter signature changes | maintainability | accepted
047 | Use Optional for budget | clear absent semantics | accepted
048 | Keep policy logic shared not duplicated | DRY | accepted
049 | OpenAI nested `reasoning.effort` support | responses compatibility | accepted
050 | Anthropic `thinking.type=disabled` immediate off | explicit command | accepted
051 | Anthropic budget overrides effort | explicit numeric priority | accepted
052 | Header budget below min -> clamp | robustness | accepted
053 | Header budget above max -> clamp | cost protection | accepted
054 | Include policy docs for transfer | handoff quality | accepted
055 | Keep plan language implementation-oriented | execution ease | accepted
056 | Keep examples concrete | reduce ambiguity | accepted
057 | Keep TODO list sequenced | implementation flow | accepted
058 | Suggest atomic commit boundaries | reviewability | accepted
059 | Preserve backward behavior baseline tests | confidence | accepted
060 | Avoid adding new API endpoints | scope control | accepted
061 | Avoid changing auth headers | compatibility | accepted
062 | Prefer converter-level injection settings | architecture fit | accepted
063 | Keep fake reasoning parser untouched | stability | accepted
064 | Use normalized internal levels | simplification | accepted
065 | Distinguish openai/anthropic maps | policy clarity | accepted
066 | Ensure openai off available | user requirement | accepted
067 | Ensure anthropic max available | user requirement | accepted
068 | allow anthropic high as default mapped level | user requirement | accepted
069 | unknown anthropic effort fallback | resilience | accepted
070 | centralize constants in config | observability | accepted
071 | no runtime writes to env | deterministic startup | accepted
072 | avoid broad refactor | minimal change request | accepted
073 | prioritize testable deterministic logic | maintainability | accepted
074 | preserve external API shape | compatibility | accepted
075 | avoid model alias generation | rejection of prior approach | accepted
076 | remove suffix docs from future output | consistency | accepted
077 | keep this handoff exhaustive | transfer completeness | accepted
078 | include risk register | operations readiness | accepted
079 | include smoke commands | practical execution | accepted
080 | include rollback provenance | audit trail | accepted
081 | include unresolved questions | transparent transfer | accepted
082 | include openclaw note as uncertain | avoid false certainty | accepted
083 | prioritize body over custom headers | standards-first | accepted
084 | avoid route duplication for policy parse | maintainability | accepted
085 | typed dataclass output from resolver | clarity | accepted
086 | keep decision logs in appendix | searchable history | accepted
087 | keep doc path inside repo docs | discoverable | accepted
088 | include env draft values not mandates | flexibility | accepted
089 | include migration runbook | execution predictability | accepted
090 | include DoD checklist | completion clarity | accepted
091 | avoid forcing one SDK provider for opencode | user flexibility | accepted
092 | prefer variants in opencode config | cleanliness | accepted
093 | keep headers optional fallback | interop | accepted
094 | avoid hard fail on unknown reason values | robustness | accepted
095 | clamp before injection | safety | accepted
096 | no fallback to suffix after rollback | consistency | accepted
097 | policy source string should be stable | telemetry utility | accepted
098 | unit tests should cover precedence matrix | correctness | accepted
099 | integration tests should check both routes | completeness | accepted
100 | document all known touched files | traceability | accepted
101 | ensure no sensitive values in docs | security | accepted
102 | avoid mention of force push/amend flows | irrelevant | accepted
103 | preserve project coding style | maintainability | accepted
104 | keep comments minimal in code | style alignment | accepted
105 | ensure env defaults conservative | cost control | accepted
106 | keep fallback with FAKE_REASONING_ENABLED | user requirement | accepted
107 | parse anthropic output_config.effort | compatibility | accepted
108 | parse openai nested reasoning.effort | compatibility | accepted
109 | explicit off should disable injection regardless of defaults | expected behavior | accepted
110 | explicit budget should imply injection enabled unless zero | intuitive semantics | accepted
111 | budget=0 should disable injection | explicit off semantics | accepted
112 | avoid overfitting to one client serializer | future-proofing | accepted
113 | maintain route auth behavior unchanged | scope safety | accepted
114 | prefer single resolver module over scattered helpers | maintainability | accepted
115 | plan for doc updates near implementation | developer UX | accepted
116 | keep manual curl checks in handoff | practical use | accepted
117 | avoid changing default model list endpoint | scope | accepted
118 | avoid touching model_cache behavior | scope | accepted
119 | avoid touching retry/http client behavior | scope | accepted
120 | avoid touching truncation recovery | scope | accepted
121 | design for deterministic same-input same-output policy | reliability | accepted
122 | keep test naming explicit for policy source | readability | accepted
123 | convert minimal->low unless env override exists | pragmatic | provisional
124 | adaptive->high by default | pragmatic | provisional
125 | annotate provisional decisions in docs | transparency | accepted
126 | preserve old behavior when no hints | strict compatibility | accepted
127 | keep parser tolerant to case variations | robustness | accepted
128 | trim whitespace in incoming effort values | resilience | accepted
129 | allow synonyms for off in headers | usability | accepted
130 | avoid throwing 400 on bad hint fields | resilience | accepted
131 | collect malformed-hint metrics via logs | observability | accepted
132 | avoid adding DB/state dependencies | simplicity | accepted
133 | keep policy config purely env/static | deployment simplicity | accepted
134 | avoid introducing hidden global toggles | predictability | accepted
135 | include transfer checklist complete | handoff quality | accepted
136 | include runbook with order | implementation safety | accepted
137 | mention unrelated dirty files intentionally untouched | transparency | accepted
138 | avoid editing user secrets in repo docs | security | accepted
139 | keep opencode config normalized | practical reset | accepted
140 | avoid keeping invalid JSON in local config | stability | accepted
141 | include command references for tests | usability | accepted
142 | recommend small iterative PRs | reviewability | accepted
143 | emphasize no fake-tag transport change | core requirement | accepted
144 | emphasize env-driven tunability | operations requirement | accepted
145 | include matrix for openai levels | clarity | accepted
146 | include matrix for anthropic levels | clarity | accepted
147 | include clamping policy details | safety | accepted
148 | include precedence details | correctness | accepted
149 | include source attribution in resolved policy | debugging | accepted
150 | complete dossier ready for transfer | objective met | accepted

---

## 31) Appendix B — Test Vector Catalog

Format: `TV-XXX | Route | Input | Expected`

TV-001 | openai | no reasoning fields | fallback defaults
TV-002 | openai | reasoning_effort=none | inject=false
TV-003 | openai | reasoning_effort=low | inject=true,low_budget
TV-004 | openai | reasoning_effort=medium | inject=true,medium_budget
TV-005 | openai | reasoning_effort=high | inject=true,high_budget
TV-006 | openai | reasoning_effort=xhigh | inject=true,xhigh_budget
TV-007 | openai | reasoning_effort=minimal | inject=true,low_or_minimal_budget
TV-008 | openai | reasoning.effort=high | inject=true,high_budget
TV-009 | openai | reasoning.effort=none | inject=false
TV-010 | openai | reasoning_effort=invalid | fallback_defaults
TV-011 | openai | header x-reasoning-effort=high no body | inject=true,high_budget
TV-012 | openai | body low + header high | body_wins_low
TV-013 | openai | header x-thinking-budget=2000 no body | inject=true,2000
TV-014 | openai | header budget=-1 | fallback_or_ignore
TV-015 | openai | header budget=0 | inject=false
TV-016 | openai | header budget=99999999 | inject=true,clamped_max
TV-017 | openai | body effort none + header budget 3000 | off_wins
TV-018 | openai | body effort high + header mode off | body_wins_high
TV-019 | openai | whitespace effort " high " | normalized_high
TV-020 | openai | uppercase effort HIGH | normalized_high
TV-021 | anthropic | no thinking fields | fallback_defaults
TV-022 | anthropic | thinking.type=disabled | inject=false
TV-023 | anthropic | thinking.type=enabled,budget=5000 | inject=true,5000
TV-024 | anthropic | thinking.type=enabled,budget=0 | inject=false
TV-025 | anthropic | thinking.type=enabled,budget=-20 | ignore_budget_fallback
TV-026 | anthropic | thinking.type=enabled,budget=999999 | clamped_max
TV-027 | anthropic | thinking.type=adaptive | inject=true,anthropic_high_or_default
TV-028 | anthropic | output_config.effort=high | inject=true,anthropic_high
TV-029 | anthropic | output_config.effort=max | inject=true,anthropic_max
TV-030 | anthropic | output_config.effort=medium | normalized_high
TV-031 | anthropic | output_config.effort=low | normalized_high_or_off_policy
TV-032 | anthropic | output_config.effort=invalid | fallback_defaults
TV-033 | anthropic | header x-thinking-mode=off no body | inject=false
TV-034 | anthropic | body disabled + header max | body_wins_off
TV-035 | anthropic | body budget 8000 + header off | body_budget_wins
TV-036 | anthropic | header budget 2048 no body | inject=true,2048
TV-037 | anthropic | header effort high + header budget 1024 | budget_wins
TV-038 | anthropic | malformed budget "abc" | ignore_budget
TV-039 | anthropic | budget below min | clamped_min
TV-040 | anthropic | budget above max | clamped_max
TV-041 | openai | none + max_tokens set | none_disables_injection
TV-042 | openai | low + stream true | injection_applies
TV-043 | openai | xhigh + tools present | injection_applies
TV-044 | openai | invalid body + valid header | header_used
TV-045 | openai | valid body + invalid header | body_used
TV-046 | anthropic | disabled + tool use | off_applies
TV-047 | anthropic | high effort + tool use | high_applies
TV-048 | anthropic | max effort + stream | max_applies
TV-049 | anthropic | adaptive + output_config max | precedence_defined
TV-050 | anthropic | budget + output_config high | budget_wins
TV-051 | openai | nested reasoning only | parsed
TV-052 | openai | both reasoning_effort and nested effort | top-level_wins
TV-053 | openai | header mode off + budget 2000 | off_wins
TV-054 | openai | header effort medium + budget 0 | off_via_budget_zero
TV-055 | openai | header effort medium + invalid budget | medium_used
TV-056 | openai | body minimal + env minimal defined | minimal_env_used
TV-057 | openai | body minimal + env minimal absent | low_used
TV-058 | anthropic | output_config max + env max changed | env_reflected
TV-059 | anthropic | output_config high + env high changed | env_reflected
TV-060 | anthropic | no body no header + FAKE_REASONING=false | inject=false
TV-061 | openai | no body no header + FAKE_REASONING=false | inject=false
TV-062 | openai | no body no header + FAKE_REASONING=true | inject=true,default_budget
TV-063 | anthropic | no body no header + FAKE_REASONING=true | inject=true,default_budget
TV-064 | openai | body off while default true | off_overrides
TV-065 | anthropic | body off while default true | off_overrides
TV-066 | openai | body high while default false | on_overrides
TV-067 | anthropic | body high while default false | on_overrides
TV-068 | openai | body xhigh while default false | on_overrides
TV-069 | anthropic | body max while default false | on_overrides
TV-070 | openai | effort mixed case XhIgH | normalized
TV-071 | anthropic | effort mixed case MaX | normalized
TV-072 | openai | header effort unknown | ignored
TV-073 | anthropic | header mode unknown | ignored
TV-074 | openai | header budget with spaces | parsed_trimmed
TV-075 | anthropic | header budget with spaces | parsed_trimmed
TV-076 | openai | effort none + budget positive in body | off_wins
TV-077 | anthropic | thinking disabled + budget positive | off_wins
TV-078 | openai | nested effort none + top-level high | top_level_wins
TV-079 | anthropic | output effort max + thinking disabled | thinking_disabled_wins
TV-080 | anthropic | output effort high + thinking budget 7777 | budget_wins
TV-081 | openai | malformed nested reasoning object | ignored
TV-082 | anthropic | malformed thinking object | ignored
TV-083 | openai | huge body unaffected | policy_resolves_fast
TV-084 | anthropic | huge body unaffected | policy_resolves_fast
TV-085 | openai | header effort low no auth change | no_auth_side_effect
TV-086 | anthropic | header effort high no auth change | no_auth_side_effect
TV-087 | openai | policy source log emitted | yes
TV-088 | anthropic | policy source log emitted | yes
TV-089 | openai | malformed value warning emitted | yes
TV-090 | anthropic | malformed value warning emitted | yes
TV-091 | openai | tools + images + high | unaffected_non_policy_fields
TV-092 | anthropic | tools + images + max | unaffected_non_policy_fields
TV-093 | openai | stream response parsing unchanged | true
TV-094 | anthropic | stream response parsing unchanged | true
TV-095 | openai | fake_reasoning_handling passthrough | unchanged
TV-096 | anthropic | fake_reasoning_handling passthrough | unchanged
TV-097 | openai | no model alias required | true
TV-098 | anthropic | no model alias required | true
TV-099 | openai | policy module import success | true
TV-100 | anthropic | policy module import success | true
TV-101 | openai | budget clamp min boundary exact | exact
TV-102 | openai | budget clamp max boundary exact | exact
TV-103 | anthropic | budget clamp min boundary exact | exact
TV-104 | anthropic | budget clamp max boundary exact | exact
TV-105 | openai | header-only mode off | off
TV-106 | openai | header-only mode high | high
TV-107 | openai | header-only mode xhigh | xhigh
TV-108 | anthropic | header-only mode off | off
TV-109 | anthropic | header-only mode high | high
TV-110 | anthropic | header-only mode max | max
TV-111 | openai | body effort low + header budget high | body_effort_precedence
TV-112 | anthropic | body effort max + header budget low | body_effort_precedence
TV-113 | openai | body budget from compat field if present | parsed
TV-114 | anthropic | body budget from thinking only | parsed
TV-115 | openai | empty string effort | ignored
TV-116 | anthropic | empty string effort | ignored
TV-117 | openai | null effort | ignored
TV-118 | anthropic | null effort | ignored
TV-119 | openai | list effort invalid type | ignored
TV-120 | anthropic | list effort invalid type | ignored
TV-121 | openai | bool budget invalid type | ignored
TV-122 | anthropic | bool budget invalid type | ignored
TV-123 | openai | float budget 1024.7 policy | int_or_ignore_defined
TV-124 | anthropic | float budget 1024.7 policy | int_or_ignore_defined
TV-125 | openai | budget just below min by 1 | clamped_min
TV-126 | anthropic | budget just below min by 1 | clamped_min
TV-127 | openai | budget just above max by 1 | clamped_max
TV-128 | anthropic | budget just above max by 1 | clamped_max
TV-129 | openai | malformed header names absent | fallback_defaults
TV-130 | anthropic | malformed header names absent | fallback_defaults
TV-131 | openai | all hints absent default true max=4000 | true_4000
TV-132 | anthropic | all hints absent default true max=4000 | true_4000
TV-133 | openai | all hints absent default false | off
TV-134 | anthropic | all hints absent default false | off
TV-135 | openai | body none + default false | off
TV-136 | anthropic | body disabled + default false | off
TV-137 | openai | body high + default true low default budget | high_budget
TV-138 | anthropic | body max + default true low default budget | max_budget
TV-139 | openai | body invalid + header invalid + default true | default_used
TV-140 | anthropic | body invalid + header invalid + default true | default_used
TV-141 | openai | policy source reports default | yes
TV-142 | anthropic | policy source reports default | yes
TV-143 | openai | policy source reports body_effort | yes
TV-144 | anthropic | policy source reports body_thinking | yes
TV-145 | openai | policy source reports header_budget | yes
TV-146 | anthropic | policy source reports header_budget | yes
TV-147 | openai | policy source reports nested_effort | yes
TV-148 | anthropic | policy source reports output_effort | yes
TV-149 | openai | serialized payload includes max_thinking tag when enabled | yes
TV-150 | anthropic | serialized payload includes max_thinking tag when enabled | yes
TV-151 | openai | serialized payload excludes thinking tags when off | yes
TV-152 | anthropic | serialized payload excludes thinking tags when off | yes
TV-153 | openai | reasoning handling mode unaffected remove | yes
TV-154 | openai | reasoning handling mode unaffected pass | yes
TV-155 | openai | reasoning handling mode unaffected strip_tags | yes
TV-156 | anthropic | reasoning handling mode unaffected remove | yes
TV-157 | anthropic | reasoning handling mode unaffected pass | yes
TV-158 | anthropic | reasoning handling mode unaffected strip_tags | yes
TV-159 | openai | long prompt unaffected except tags | true
TV-160 | anthropic | long prompt unaffected except tags | true
TV-161 | openai | tool description truncation unaffected | true
TV-162 | anthropic | tool description truncation unaffected | true
TV-163 | openai | truncation recovery unaffected | true
TV-164 | anthropic | truncation recovery unaffected | true
TV-165 | openai | auth type desktop unaffected | true
TV-166 | anthropic | auth type desktop unaffected | true
TV-167 | openai | auth type oidc unaffected | true
TV-168 | anthropic | auth type oidc unaffected | true
TV-169 | openai | vpn proxy path unaffected | true
TV-170 | anthropic | vpn proxy path unaffected | true
TV-171 | openai | retry behavior unaffected | true
TV-172 | anthropic | retry behavior unaffected | true
TV-173 | openai | first-token timeout unaffected | true
TV-174 | anthropic | first-token timeout unaffected | true
TV-175 | openai | streaming timeout unaffected | true
TV-176 | anthropic | streaming timeout unaffected | true
TV-177 | openai | no new endpoint paths | true
TV-178 | anthropic | no new endpoint paths | true
TV-179 | openai | no new auth headers required | true
TV-180 | anthropic | no new auth headers required | true
TV-181 | openai | debug logs redact secrets | true
TV-182 | anthropic | debug logs redact secrets | true
TV-183 | openai | malformed JSON body still validation path | unchanged
TV-184 | anthropic | malformed JSON body still validation path | unchanged
TV-185 | openai | body effort high with model auto | policy independent model
TV-186 | anthropic | effort max with model auto | policy independent model
TV-187 | openai | compare latency low vs xhigh | expected trend
TV-188 | anthropic | compare latency high vs max | expected trend
TV-189 | openai | compare token usage low vs xhigh | expected trend
TV-190 | anthropic | compare token usage high vs max | expected trend
TV-191 | openai | policy with tool-calls chain | stable
TV-192 | anthropic | policy with tool-calls chain | stable
TV-193 | openai | policy with image input | stable
TV-194 | anthropic | policy with image input | stable
TV-195 | openai | policy with empty user content | stable
TV-196 | anthropic | policy with empty user content | stable
TV-197 | openai | policy with only system prompt | stable
TV-198 | anthropic | policy with only system prompt | stable
TV-199 | openai | final acceptance matrix all pass | required
TV-200 | anthropic | final acceptance matrix all pass | required

---

## 32) Appendix C — Work Breakdown Checklist (Granular)

W-001 Define env names
W-002 Add env defaults in config
W-003 Add env docs to .env.example
W-004 Add comments for env meaning
W-005 Create policy dataclass
W-006 Create parse helpers
W-007 Create normalize helpers
W-008 Create clamp helper
W-009 Create openai resolver function
W-010 Create anthropic resolver function
W-011 Add source attribution field
W-012 Add route header extraction openai
W-013 Add route header extraction anthropic
W-014 Wire openai converter policy call
W-015 Wire anthropic converter policy call
W-016 Keep core injection protocol unchanged
W-017 Add unit test file for policy
W-018 Add openai converter test updates
W-019 Add anthropic converter test updates
W-020 Add regression test for default fallback
W-021 Add regression test for off override
W-022 Add regression test for budget override
W-023 Add regression test for invalid values
W-024 Add regression test for header fallback
W-025 Add precedence test body over header
W-026 Add precedence test budget over effort
W-027 Add clamp min test
W-028 Add clamp max test
W-029 Add mixed-case normalization test
W-030 Add whitespace normalization test
W-031 Add no-side-effect tests for auth
W-032 Add no-side-effect tests for streaming parser
W-033 Add docs in README for openai fields
W-034 Add docs in README for anthropic fields
W-035 Add docs in README for fallback headers
W-036 Add warning note no universal header standard
W-037 Add examples openai low/high/xhigh
W-038 Add examples anthropic off/high/max
W-039 Run unit test suite targeted
W-040 Run manual curl openai off
W-041 Run manual curl openai high
W-042 Run manual curl anthropic disabled
W-043 Run manual curl anthropic max
W-044 Run opencode smoke test low
W-045 Run opencode smoke test xhigh
W-046 Capture debug logs sample
W-047 Verify no secrets in logs
W-048 Validate style/lint if configured
W-049 Prepare commit notes
W-050 Prepare PR summary
W-051 Verify backwards compatibility default path
W-052 Verify no model suffix required
W-053 Verify /v1/models unaffected
W-054 Verify /health unaffected
W-055 Verify truncation recovery unaffected
W-056 Verify proxy/vpn unaffected
W-057 Verify retry behavior unaffected
W-058 Verify auth refresh unaffected
W-059 Verify cli-db auth unaffected
W-060 Verify desktop auth unaffected
W-061 Verify no new dependencies
W-062 Verify type hints complete
W-063 Verify resolver module docstring
W-064 Verify tests deterministic
W-065 Verify tests independent
W-066 Verify no flaky time assumptions
W-067 Verify conversion logs concise
W-068 Verify warning logs actionable
W-069 Verify env names stable
W-070 Verify env parsing robust
W-071 Verify invalid env values fallback safe
W-072 Verify zero budget off behavior
W-073 Verify negative budget ignore behavior
W-074 Verify huge budget clamp behavior
W-075 Verify minimal mapping behavior
W-076 Verify adaptive mapping behavior
W-077 Verify output_config.effort mapping
W-078 Verify nested reasoning mapping
W-079 Verify top-level reasoning mapping
W-080 Verify field priority in openai
W-081 Verify field priority in anthropic
W-082 Verify header parse integers only
W-083 Verify header parse trims spaces
W-084 Verify unknown header values ignored
W-085 Verify fallback to default preserved
W-086 Verify off override when default true
W-087 Verify on override when default false
W-088 Verify source label consistency
W-089 Verify telemetry references source labels
W-090 Verify docs mention source precedence
W-091 Verify docs mention no suffix mode
W-092 Verify docs include migration note
W-093 Verify existing clients unaffected
W-094 Verify openclaw path with headers works
W-095 Verify openclaw path with body works
W-096 Verify opencode variants recommendation
W-097 Verify opencode base models still usable
W-098 Verify optional anthropic provider path documented
W-099 Verify no hardcoded model table introduced
W-100 Verify release notes prepared

---

## 33) Final Notes to Receiving AI

This dossier is intentionally exhaustive so transfer can continue with low ambiguity.

If you implement from this plan, prioritize:

1. minimal diffs,
2. deterministic precedence,
3. strict backward compatibility,
4. complete tests before optimization.

End of dossier.
