# Knowledge Base

This folder contains learned patterns for fixing Verus verification errors. It grows organically through:

1. **Self-learning**: When a subagent successfully fixes an error with no existing pattern
2. **User help**: When a user provides a fix that works

## Structure

```
knowledge/
├── idiom-converter/      # Patterns for Rust -> Verus idiom conversion
├── assume-spec-gen/      # Patterns for library call specifications
├── verification-fixer/   # Patterns for verification error fixes
└── repair-agent/         # Patterns for repairing broken fixes
```

## Pattern File Format

Each pattern file uses this format:

```markdown
---
triggers:
  - "error message snippet 1"
  - "error message snippet 2"
source: self-learned | user
created: YYYY-MM-DD
success_count: N
last_used: YYYY-MM-DD
---

## Pattern: [Descriptive Name]

### When to use
[Description of the situation/error type]

### Before (fails)
[Code that causes the error]

### After (passes)
[Fixed code]

### Why it works
[Brief explanation]
```

## Searching

Use the `search-knowledge` skill which:
1. Searches by keyword matching in triggers
2. Falls back to LLM semantic search if no match
3. Can search across different agent folders
