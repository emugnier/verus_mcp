---
name: learn-pattern
description: Save a successful fix pattern to the knowledge base. Use after a fix works (from self-discovery or user help).
allowed-tools: Write, Read, Grep, Glob
---

# Learn Pattern Skill

Save a successful fix to the knowledge base for future reuse.

## Before Saving - Similarity Check

1. Extract key trigger words from the error message
2. Search existing patterns in `knowledge/<agent-type>/` for similar triggers
3. If >80% keyword overlap with existing pattern:
   - Update that pattern's `success_count` instead
   - Update `last_used` date
   - DO NOT create a duplicate

```bash
# Search for similar patterns
grep -r "trigger_keyword" knowledge/<agent-type>/
```

## Pattern File Location

Create file at: `knowledge/<agent-type>/<error-category>/<descriptive-name>.md`

Examples:
- `knowledge/idiom-converter/unsupported-operator/question-mark-to-match.md`
- `knowledge/verification-fixer/not-supported/vec-to-seq.md`
- `knowledge/assume-spec-gen/external-call/string-parse.md`

Create the error-category subdirectory if it doesn't exist.

## Pattern File Format

```markdown
---
triggers:
  - "exact error message snippet 1"
  - "exact error message snippet 2"
source: self-learned | user
created: YYYY-MM-DD
success_count: 1
last_used: YYYY-MM-DD
---

## Pattern: [Descriptive Name]

### When to use
[Describe the situation/error type that this pattern fixes]

### Error Example
```
[The actual error message from Verus]
```

### Before (fails)
```rust
[Code that causes the error]
```

### After (passes)
```rust
[Fixed code that passes verification]
```

### Why it works
[Brief explanation of why this transformation works]

### Notes
[Any caveats, edge cases, or related patterns]
```

## Naming Convention

Use descriptive kebab-case:
- `question-mark-to-match.md`
- `vec-push-to-seq-push.md`
- `iterator-to-while-loop.md`
- `external-call-assume-spec.md`

## Updating Existing Patterns

If a similar pattern exists (>80% keyword overlap):

1. Read the existing pattern file
2. Increment `success_count`
3. Update `last_used` to today's date
4. Optionally add new trigger phrases if the error message was slightly different

## Logging

After saving a pattern, log the event:
- Pattern file path
- Source (self-learned or user)
- Error that triggered it
- Brief description of the fix
