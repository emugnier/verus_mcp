---
name: search-knowledge
description: RAG-like search of the knowledge base. Finds relevant patterns for the current agent and error type. Use before attempting any fix.
allowed-tools: Bash
---

# Search Knowledge Skill

Search the knowledge base for patterns matching the current error.

## Command

```bash
python3 scripts/verus-kb.py retrieve --agent <agent_type> --error "<error_message>"
```

Returns a JSON array of matching patterns sorted by confidence:

```json
[
  {
    "path": "knowledge/idiom-converter/unsupported/question-mark.md",
    "confidence": "high",
    "match_reason": "High trigger match (100%): 'Verus does not support the ? operator'"
  }
]
```

Empty array `[]` means no match found.

## Input

- `--agent`: Which agent is searching (`idiom-converter`, `assume-spec-gen`, `repair-agent`)
- `--error`: The actual error text from Verus (quote it)

## Example

```bash
python3 scripts/verus-kb.py retrieve \
  --agent idiom-converter \
  --error "error: Verus does not support the ? operator"
```

## Confidence Levels

| Confidence | Meaning |
|-----------|---------|
| `high` | Trigger phrase matches >= 80% of keywords |
| `medium` | Trigger phrase matches >= 50% of keywords |
| `low` | Single keyword match or content match |

## After Getting Results

1. If `confidence: high` — read the pattern file and apply it directly
2. If `confidence: medium` — read the pattern file, verify it applies, adapt if needed
3. If `confidence: low` — read the pattern file as a hint, may need adaptation
4. If empty array — novel error; attempt fix from scratch, save result as new pattern

## Reading a Pattern

```bash
cat <path-from-results>
```

The pattern file contains: error example, before/after code, and explanation of why the fix works.

## Cross-Agent Search

The `retrieve` command automatically searches the specified agent's folder first,
then cross-searches other agent folders. A pattern from `assume-spec-gen` may be
relevant to `idiom-converter` and vice versa.
