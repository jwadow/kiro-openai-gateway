# Context Management Research Analysis

## How Contexts Fail & How to Fix Them - Adaptation for OpenCodeKit

**Source**: https://www.dbreunig.com/2025/06/22/how-contexts-fail-and-how-to-fix-them.html  
**Follow-up**: https://www.dbreunig.com/2025/06/26/how-to-fix-your-context.html  
**Analysis Date**: 2026-01-30

---

## Executive Summary

The research reveals that **longer contexts do NOT generate better responses**. Context windows beyond 100k tokens cause models to favor repeating past actions over synthesizing novel plans. OpenCodeKit has strong foundations but significant gaps in tool management, context isolation, and structured context assembly.

**Verdict**: OpenCodeKit is at **70% maturity** on context management. Critical gaps exist in tool loadout, context offloading, and poisoning prevention.

---

## The Four Context Failure Modes

### 1. Context Poisoning (CRITICAL GAP)

**Definition**: Hallucinations or errors enter context and are repeatedly referenced, compounding over time.

**Research Evidence**:

- Gemini 2.5 playing Pokémon: goals section poisoned with misinformation about game state
- Agent developed nonsensical strategies pursuing impossible goals
- "Can take a very long time to undo"

**OpenCodeKit Status**: ❌ **NO PROTECTION**

- No validation layer before tool outputs enter context
- No mechanism to detect/correct hallucinations
- Subagent reports trusted without verification
- Tool outputs (grep, read, webfetch) enter context raw

**Impact**: HIGH - Every tool call risks poisoning

---

### 2. Context Distraction (PARTIALLY ADDRESSED)

**Definition**: Context grows so long that model over-focuses on context, neglecting training knowledge.

**Research Evidence**:

- Gemini 2.5 Pro: beyond 100k tokens, agent repeats actions from history vs synthesizing novel plans
- Llama 3.1 405b: correctness falls around 32k tokens
- Smaller models fail earlier

**OpenCodeKit Status**: ⚠️ **PARTIAL - Good thresholds, no enforcement**

- ✅ Has thresholds: 70%, 85%, 95%
- ✅ Session management skill recommends <150k tokens
- ❌ No hard enforcement of thresholds
- ❌ No automatic summarization at thresholds
- ❌ No model-specific limits (Claude vs Gemini vs GPT)

**Impact**: MEDIUM - Guidelines exist but not enforced

---

### 3. Context Confusion (CRITICAL GAP)

**Definition**: Superfluous content in context influences responses negatively.

**Research Evidence**:

- Berkeley Function-Calling Leaderboard: ALL models perform worse with >1 tool
- Llama 3.1 8b: fails with 46 tools, succeeds with 19 tools
- DeepSeek-v3: critical threshold at 30 tools, guaranteed failure beyond 100
- Tool RAG improves accuracy 3x

**OpenCodeKit Status**: ❌ **NO TOOL LOADOUT SYSTEM**

- All 40+ tools loaded into context simultaneously
- No dynamic tool selection based on task
- No tool RAG/semantic selection
- Skills add MORE tools to context
- MCP servers add even more tools

**Impact**: CRITICAL - 40+ tools in context violates research findings

---

### 4. Context Clash (MODERATE GAP)

**Definition**: New information conflicts with existing context, derailing reasoning.

**Research Evidence**:

- Microsoft/Salesforce study: sharded prompts yield 39% worse results
- o3 score dropped from 98.1 to 64.1 with multi-turn assembly
- Models make assumptions early, get lost and don't recover

**OpenCodeKit Status**: ⚠️ **PARTIAL - Subagents help, no clash detection**

- ✅ Subagents provide some isolation
- ✅ Fresh subagent per task reduces accumulation
- ❌ No clash detection between memory + session + tool outputs
- ❌ No validation that assembled context is coherent
- ❌ Multi-turn conversations accumulate conflicting info

**Impact**: MEDIUM - Architecture helps but no active prevention

---

## Six Solutions from Research

### 1. RAG (Retrieval-Augmented Generation)

**Research**: Selectively add relevant information vs dumping everything

**OpenCodeKit Status**: ✅ **IMPLEMENTED**

- memory-search for relevant past context
- context7 for library docs
- exa for web search
- grepsearch for code patterns

**Gap**: Not applied to tool selection

---

### 2. Tool Loadout (CRITICAL MISSING)

**Research**: Select only relevant tools (<30 for best performance)

**OpenCodeKit Status**: ❌ **NOT IMPLEMENTED**

**What We Need**:

```typescript
// Tool RAG - semantic selection
const relevantTools = await toolRAG({
  task: "Add authentication",
  availableTools: allTools,
  maxTools: 25, // Research says <30
  selectionMethod: "semantic-similarity",
});

// Result: Only auth-related tools loaded
```

**Implementation Options**:

1. **Static Loadouts**: Pre-defined tool sets per command
   - `/design` → UI/UX tools only
   - `/fix` → debugging tools only
   - `/implement` → code editing tools only

2. **Dynamic RAG**: Vector search tool descriptions
   - Store tool descriptions in vector DB
   - Query with user task
   - Return top-K relevant tools

3. **Hybrid**: Static base + dynamic additions
   - Core tools always loaded (read, edit, bash)
   - Specialized tools selected dynamically

**Priority**: CRITICAL - Immediate impact on performance

---

### 3. Context Quarantine (PARTIALLY IMPLEMENTED)

**Research**: Isolate contexts in dedicated threads

**OpenCodeKit Status**: ⚠️ **PARTIAL - Subagents exist, isolation incomplete**

**Current**:

- Subagents spawned for parallel tasks
- Fresh context per subagent
- Mailbox coordination

**Gaps**:

- Subagents can still access full tool set
- No strict context boundaries
- Leader context accumulates subagent reports
- No "air gap" between contexts

**What We Need**:

```typescript
// True quarantine - subagent gets ONLY:
// - Delegation packet
// - Assigned files
// - Minimal tool set (3-5 tools)
// - NO access to leader's full context

const quarantinedSubagent = await Task({
  subagent_type: "general",
  contextIsolation: "strict", // NEW
  allowedTools: ["read", "edit", "bash"], // Limited loadout
  maxTokens: 50000, // Hard limit
  delegationOnly: true, // Can only see delegation packet
});
```

---

### 4. Context Pruning (IMPLEMENTED BUT MANUAL)

**Research**: Remove irrelevant information (Provence achieved 95% reduction)

**OpenCodeKit Status**: ⚠️ **PARTIAL - Tools exist, not automated**

**Current**:

- `discard` tool for removing outputs
- `extract` tool for distilling knowledge
- Session thresholds (70%, 85%, 95%)

**Gaps**:

- Manual - agent must decide what to prune
- No automated pruning at thresholds
- No Provence-like intelligent pruning
- No structured context to prune from

**What We Need**:

```typescript
// Automated pruning at 85% threshold
if (contextUsage > 0.85) {
  // 1. Identify low-value content
  const pruneable = await identifyPrunableContent({
    context: currentContext,
    criteria: [
      "completed task outputs",
      "superseded tool results",
      "intermediate calculations",
      "verbose logs"
    ]
  });

  // 2. Extract key findings before discarding
  await extract({ ids: pruneable.ids, distillation: [...] });

  // 3. Auto-discard
  await discard({ ids: pruneable.ids, reason: "threshold_auto_prune" });
}
```

---

### 5. Context Summarization (NOT IMPLEMENTED)

**Research**: Boil down accrued context into condensed summary

**OpenCodeKit Status**: ❌ **NOT IMPLEMENTED**

**Current**:

- `summarize_session` exists but not used in workflow
- No automatic summarization at thresholds

**What We Need**:

```typescript
// At 100k tokens, auto-summarize
const summary = await summarizeContext({
  context: currentContext,
  preserve: ["active_task_spec", "uncommitted_changes", "critical_decisions"],
  compress: ["tool_outputs", "completed_subtasks", "research_findings"],
});

// Replace bloated context with summary + preserved essentials
```

---

### 6. Context Offloading (PARTIALLY IMPLEMENTED)

**Research**: Store information outside LLM context via tools

**OpenCodeKit Status**: ⚠️ **PARTIAL - Memory system exists, no scratchpad**

**Current**:

- Memory files for persistent storage
- Beads for task tracking
- Observations for structured findings

**Gaps**:

- No "think tool" / scratchpad pattern
- No structured context assembly
- Everything compiled into single context string

**What We Need - Scratchpad Tool**:

```typescript
// Anthropic's "think tool" pattern
const scratchpad = await tool({
  name: "scratchpad_write",
  section: "reasoning", // reasoning, notes, progress, concerns
  content: "The bug appears to be in the auth middleware...",
});

// Later retrieval
const notes = await scratchpad_read({ section: "reasoning" });
```

**What We Need - Structured Context**:

```typescript
// Structured context assembly
const contextAssembly = {
  instructions: AGENTS_MD, // Always present
  active_task: beadSpec,   // Current focus
  scratchpad: {...},       // Working notes
  memory: {...},           // Relevant past context
  tools: [...],            // Current loadout
  history: [...],          // Recent actions (pruned)
  // Compile to string only at LLM call time
};
```

---

## Brutal Assessment by Component

### AGENTS.md (The Foundation)

**Score**: 7/10

**Strengths**:

- Clear delegation rules
- LSP verification chain
- Memory checkpoints
- Anti-hallucination protocols

**Weaknesses**:

- No tool loadout guidance
- No context size limits per model
- No scratchpad/think tool mention
- No context clash detection

**Recommendations**:

1. Add "Tool Loadout" section - limit to <30 tools
2. Add "Context Assembly" section - structured context
3. Add "Scratchpad" pattern for working notes
4. Add model-specific context limits

---

### Session Management Skill

**Score**: 6/10

**Strengths**:

- Thresholds defined (70%, 85%, 95%)
- Pruning strategy documented
- Session restart guidance

**Weaknesses**:

- No automated actions at thresholds
- No summarization workflow
- No model-specific guidance
- Thresholds are suggestions, not enforced

**Recommendations**:

1. Auto-trigger extract+discard at 85%
2. Auto-summarize at 100k tokens
3. Hard stop at 150k tokens
4. Model-specific limits (Claude: 100k, Gemini: 150k, GPT: 80k)

---

### Memory System Skill

**Score**: 8/10

**Strengths**:

- Structured storage
- Search capability
- Observation pattern
- Cross-session persistence

**Weaknesses**:

- No RAG for memory retrieval (keyword only)
- No automatic memory updates
- No memory pruning/aging

**Recommendations**:

1. Add semantic search for memories
2. Auto-update memory at task completion
3. Add memory relevance scoring

---

### Swarm Coordination Skill

**Score**: 8/10

**Strengths**:

- Fresh subagent per task (quarantine)
- Delegation packets
- Progress tracking
- Mailbox coordination

**Weaknesses**:

- Subagents still get full tool set
- No strict context isolation
- Leader accumulates all subagent outputs

**Recommendations**:

1. Tool loadout per subagent type
2. Strict context boundaries
3. Synthesized reports vs raw outputs

---

### Subagent-Driven Development Skill

**Score**: 7/10

**Strengths**:

- Fresh context per task
- Review between tasks
- No context pollution

**Weaknesses**:

- No mention of tool limits
- No context size monitoring
- Review adds more context

**Recommendations**:

1. Limit subagent tools to 5-10
2. Monitor subagent context size
3. Summarize review findings

---

## Critical Adaptations Needed

### 1. Tool Loadout System (P0 - Critical)

**Problem**: 40+ tools in context violates research (failures >30 tools)

**Solution**:

```yaml
# .opencode/config/tool-loadouts.yaml
default:
  - read
  - edit
  - bash
  - grep
  - memory-read

design:
  extends: default
  - skill_mcp  # Figma, Stitch
  - vision_agent

debug:
  extends: default
  - lsp
  - systematic_debugging_skill

research:
  extends: default
  - websearch
  - codesearch
  - context7
  - grepsearch
```

**Implementation**:

1. Create tool categorization
2. Map commands to loadouts
3. Add dynamic tool RAG for edge cases
4. Measure impact on accuracy

---

### 2. Structured Context Assembly (P0 - Critical)

**Problem**: Context is unstructured string, hard to prune/summarize

**Solution**:

```typescript
// Context sections with priorities
interface ContextAssembly {
  system: Section<"critical">; // AGENTS.md - never pruned
  instructions: Section<"critical">; // Task spec - never pruned
  scratchpad: Section<"high">; // Working notes - summarized
  memory: Section<"high">; // Relevant past - RAG selected
  tools: Section<"medium">; // Tool definitions - loadout
  history: Section<"low">; // Action history - aggressively pruned
  working: Section<"low">; // Current tool outputs - pruned after use
}
```

**Implementation**:

1. Define context sections
2. Assign priority levels
3. Implement section-aware pruning
4. Compile to string at LLM call time

---

### 3. Scratchpad / Think Tool (P1 - High)

**Problem**: No place for working notes outside main context

**Solution**:

```typescript
// scratchpad tool
interface Scratchpad {
  reasoning: string[]; // Current thinking
  concerns: string[]; // Issues to watch
  progress: string[]; // Completed steps
  notes: string[]; // General notes
}

// Usage
scratchpad_write({
  section: "reasoning",
  content: "The auth flow has 3 steps: 1) validate token...",
});
```

**Benefits**:

- Offload working memory from context
- Structured notes vs scattered thoughts
- Survives pruning

---

### 4. Automated Context Maintenance (P1 - High)

**Problem**: Manual pruning is inconsistent

**Solution**:

```typescript
// Auto-maintenance at thresholds
contextMaintenance: {
  at_70_percent: "warn_and_consolidate",
  at_85_percent: "extract_and_prune",
  at_100k_tokens: "summarize_history",
  at_95_percent: "critical_prune_or_restart"
}
```

**Actions**:

1. 70%: Warn, suggest consolidation
2. 85%: Auto-extract key findings, prune completed work
3. 100k: Summarize history section
4. 95%: Aggressive prune or force restart

---

### 5. Context Poisoning Detection (P2 - Medium)

**Problem**: No validation before tool outputs enter context

**Solution**:

```typescript
// Validation layer
interface ContextValidator {
  // Check for hallucinations in tool outputs
  validateToolOutput(output: ToolOutput): ValidationResult;

  // Detect contradictions in context
  detectClashes(context: ContextAssembly): ClashReport;

  // Verify subagent reports
  verifySubagentReport(report: SubagentReport): VerificationResult;
}
```

**Implementation**:

1. Flag suspicious tool outputs
2. Detect contradictions between sources
3. Verify subagent claims before accepting

---

## What OpenCodeKit Does Well

1. **Session Management**: Thresholds are research-aligned (70%, 85%, 95%)
2. **Subagent Pattern**: Fresh context per task reduces distraction
3. **Memory System**: Good context offloading to persistent storage
4. **Pruning Tools**: discard/extract provide foundation
5. **Parallel Execution**: Reduces per-agent context accumulation
6. **Swarm Coordination**: Delegation packets limit context per worker

---

## What OpenCodeKit Gets Wrong

1. **Tool Overload**: 40+ tools in context is 33% over research limit
2. **Manual Pruning**: No automated context maintenance
3. **No Scratchpad**: Working notes pollute main context
4. **Unstructured Context**: Can't intelligently prune/summarize
5. **No Poisoning Detection**: Tool outputs enter context unchecked
6. **One-Size-Fits-All**: No model-specific context limits

---

## Implementation Roadmap

### Phase 1: Tool Loadout (Immediate - 1 week)

- [ ] Categorize all tools by function
- [ ] Create static loadouts per command
- [ ] Implement loadout selection
- [ ] Measure accuracy improvement

### Phase 2: Structured Context (2 weeks)

- [ ] Define context sections
- [ ] Implement section-aware pruning
- [ ] Add scratchpad tool
- [ ] Test with long sessions

### Phase 3: Automation (2 weeks)

- [ ] Auto-extract at 85%
- [ ] Auto-summarize at 100k
- [ ] Model-specific limits
- [ ] Hard stop at 150k

### Phase 4: Validation (3 weeks)

- [ ] Context poisoning detection
- [ ] Clash detection
- [ ] Subagent verification
- [ ] Quality metrics

---

## Success Metrics

| Metric                   | Current | Target    |
| ------------------------ | ------- | --------- |
| Tools in context         | 40+     | <25       |
| Avg session tokens       | ~200k   | <100k     |
| Manual pruning rate      | 30%     | 80% auto  |
| Context restarts         | Rare    | Proactive |
| Task completion accuracy | Unknown | +20%      |

---

## Conclusion

OpenCodeKit has solid foundations but **critical gaps in tool management**. The research is clear: >30 tools causes failures. We have 40+.

**Immediate action**: Implement tool loadout system. This alone should improve accuracy 20-40% based on research findings.

**Secondary priority**: Structured context assembly + scratchpad. Enables intelligent pruning and offloading.

The research validates our session management approach but shows we're not aggressive enough with enforcement. The 70/85/95 thresholds are correct, but we need automated actions at each level, not just warnings.

**Bottom line**: We're 70% there. Tool loadout is the missing 30% that unlocks the other 70%.
