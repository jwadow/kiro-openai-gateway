# Making Tasks Resumable Across Sessions

## When Resumability Matters

**Use enhanced notes for:**

- Multi-session features with API integration
- Complex algorithms requiring code examples
- Features with specific output format requirements
- Work with undocumented APIs

**Skip for:**

- Simple bug fixes with clear scope
- Well-understood patterns (CRUD, etc.)
- Single-session tasks
- Work with obvious criteria

**The test:** Would a fresh agent (or you after 2 weeks) struggle to resume from the notes alone? If yes, add detail.

## Anatomy of Resumable Notes

### Minimal (Always Include)

```
COMPLETED: What's done
IN PROGRESS: Current state
NEXT: Concrete next step
```

### Enhanced (Complex Work)

````
COMPLETED: Specific deliverables
IN PROGRESS: Current state + what's working
NEXT: Concrete next step (not "continue")
BLOCKERS: What's preventing progress
KEY DECISIONS: Important context with rationale

WORKING CODE:
```python
# Tested code that works
result = api.query(fields='importFormats')
# Returns: {'text/markdown': ['application/vnd.google-apps.document']}
````

DESIRED OUTPUT:

```markdown
# Example of what output should look like

Actual structure, not just "return markdown"
```

````

## Example: Before vs After

### Not Resumable

```
Title: Add dynamic capabilities
Notes: Working on it. Made some progress.
````

**Problem:** Future agent doesn't know:

- Which API endpoints to call
- What responses look like
- What format to return

### Resumable

````
Title: Add dynamic capabilities resources

Notes:
COMPLETED: API connection verified. Query working.
IN PROGRESS: Formatting response as markdown.
NEXT: Add caching for API responses.

WORKING CODE:
```python
service = build('drive', 'v3', credentials=creds)
about = service.about().get(fields='importFormats').execute()
# Returns dict with 49 entries
````

DESIRED OUTPUT:

```markdown
# Drive Import Formats

- **text/markdown** → Google Docs
- text/plain → Google Docs
```

KEY DECISION: Using live API query because text/markdown support (July 2024) not in static docs.

```

**Result:** Fresh agent can:
1. See working API code
2. Understand response structure
3. Know desired output format
4. Implement with context

## When to Add Detail

**During task creation:**
- Already have working code? Include it.
- Clear output format? Show example.

**During work:**
- Got API working? Add to notes.
- Discovered important context? Document it.
- Made key decision? Explain rationale.

**Session end:**
- If resuming will be hard, add implementation guide.
- If obvious, skip it.

## Anti-Patterns

### Over-Documenting Simple Work

```

Title: Fix typo in README
Notes: IMPLEMENTATION GUIDE
WORKING CODE: Open README.md, change "teh" to "the"...

```

**Problem:** Wastes tokens on obvious work.

### Vague Progress

```

Notes: Made progress. Will continue later.

```

**Problem:** No context for resumption.

### Raw Data Dumps

```

API RESPONSE:
{giant unformatted JSON blob spanning 100 lines}

```

**Problem:** Hard to read. Extract relevant parts.

### Right Balance

```

API returns dict with 49 entries. Examples:

- 'text/markdown': ['application/vnd.google-apps.document']
- 'text/plain': ['application/vnd.google-apps.document']

```

## The Principle

Help your future self (or next agent) resume without rediscovering everything.

Write notes as if explaining to someone with:
- Zero conversation context
- No memory of previous sessions
- Only the task description and notes
```
