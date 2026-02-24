---
name: search-knowledge
description: RAG-like search of the knowledge base. Finds relevant patterns for the current agent and error type. Use before attempting any fix.
allowed-tools: Read, Grep, Glob
---

# Search Knowledge Skill

Two-phase search: syntactic first, LLM semantic fallback if needed.

## Input

- `agent_type`: Which agent is searching (idiom-converter, assume-spec-gen, verification-fixer, repair-agent)
- `error_message`: The actual error text from Verus

## Phase 1: Syntactic Search

### Step 1: Search agent-specific folder first
```bash
# List all patterns for this agent
ls knowledge/<agent_type>/

# Search for keywords in pattern triggers
grep -r "<keyword>" knowledge/<agent_type>/
```

### Step 2: Extract and match keywords
From the error message, extract key terms:
- "not supported" 
- "unsupported"
- Specific Rust constructs mentioned (?, Vec, Iterator, etc.)
- Function/type names

### Step 3: Score matches
- Exact trigger match: HIGH confidence
- Partial keyword match (>50%): MEDIUM confidence
- Single keyword match: LOW confidence

## Phase 2: LLM Semantic Search (if Phase 1 fails)

If no syntactic matches found:

1. List all pattern files in `knowledge/<agent_type>/`
2. Read the `## Pattern:` and `### When to use` sections of each
3. Use reasoning to find semantically similar patterns:
   - Similar error types even with different wording
   - Similar code constructs
   - Related transformation patterns

4. Also check OTHER agent folders if relevant:
   - A verification-fixer pattern might help idiom-converter
   - Cross-pollination of knowledge is allowed

## Output Format

```yaml
found: true | false
patterns:
  - path: "knowledge/idiom-converter/unsupported/question-mark.md"
    confidence: high | medium | low
    match_reason: "Exact trigger match: 'not supported'"
  - path: "..."
    confidence: "..."
    match_reason: "..."
search_summary: "Found N patterns, best match is X"
```

## If Nothing Found

Return:
```yaml
found: false
patterns: []
search_summary: "No matching patterns. This appears to be a novel error type."
suggestion: "Attempt fix based on error analysis. If successful, save as new pattern."
```

## Example Search

Error: `error: Verus does not support the ? operator`

1. Keywords extracted: "not supported", "?", "operator"
2. Search `knowledge/idiom-converter/` for these terms
3. Find `question-mark-to-match.md` with trigger "does not support the ?"
4. Return HIGH confidence match

## Performance Tips

- Search agent-specific folder first (most likely to have relevant patterns)
- Use grep for fast keyword search before reading full files
- Only read full pattern content for potential matches
- Cache results if searching multiple times for same error
