---
name: learn-pattern
description: Save a successful fix pattern to the knowledge base. Use after a fix works (from self-discovery or user help).
allowed-tools: Bash
---

# Learn Pattern Skill

Save a successful fix to the knowledge base for future reuse.

## Before Saving — Similarity Check

First check if a similar pattern already exists:

```bash
python3 scripts/verus-kb.py retrieve --agent <agent_type> --error "<error_message>"
```

If results include a `high` or `medium` confidence match, update that pattern instead of creating a duplicate:

```bash
python3 scripts/verus-kb.py update --path <path-from-results>
```

## Creating a New Pattern

If no similar pattern exists, create one:

```bash
cat << 'EOF' | python3 scripts/verus-kb.py create \
  --agent <agent_type> \
  --category <error-category> \
  --name <descriptive-name>
---
triggers:
  - "exact error message snippet 1"
  - "exact error message snippet 2"
source: self-learned
created: YYYY-MM-DD
success_count: 1
last_used: YYYY-MM-DD
---

## Pattern: [Descriptive Name]

### When to use
[Describe the situation/error type this pattern fixes]

### Error Example
\`\`\`
[The actual Verus error message]
\`\`\`

### Before (fails)
\`\`\`rust
[Code that causes the error]
\`\`\`

### After (passes)
\`\`\`rust
[Fixed code that passes verification]
\`\`\`

### Why it works
[Brief explanation of why this transformation works]

### Notes
[Caveats, edge cases, or related patterns]
EOF
```

The command prints the path of the created file to stdout.

## File Location Convention

```
knowledge/<agent-type>/<error-category>/<descriptive-name>.md
```

Examples:
- `knowledge/idiom-converter/unsupported-operator/question-mark-to-match.md`
- `knowledge/assume-spec-gen/external-call/string-parse.md`
- `knowledge/repair-agent/incorrect-attribute/external-trait-spec-vs-external-body.md`

## Naming Conventions

Use descriptive kebab-case for both categories and names:
- Category: `unsupported-operator`, `unsupported-iterators`, `method-signature`
- Name: `question-mark-to-match`, `flat-map-to-chars-loop`, `mut-self-builder-methods`

## After Saving

Log the event via `log-event`:

```bash
python3 scripts/verus-log.py event --type self_learned --data '{
  "agent": "<agent_type>",
  "pattern_id": "<path-returned-by-create>",
  "trigger": "<error that triggered it>",
  "success_count": 1
}'
```
