---
name: ask-user-help
description: Escalate to user when stuck. Use after multiple failed attempts or when facing unknown patterns.
allowed-tools: Read
---

# Ask User Help Skill

Request help from the user when automated fixes have failed.

## When to Use

Escalate to user after:
1. **3 failed fix attempts** for the same error
2. **Knowledge base search** returned nothing relevant
3. **Error type is completely unfamiliar** (not in KB, no obvious solution)
4. **Conflicting strategies** - unsure which approach is correct

Do NOT escalate for:
- First encounter with an error (try to fix it first)
- Errors with clear solutions in the knowledge base
- Simple syntax errors

## Request Format

Structure your help request clearly:

```markdown
## I Need Help with a Verus Error

### The Error
```
[Paste the exact error message from Verus]
```

### Location
- File: `path/to/file.rs`
- Line: X
- Function: `function_name`

### Code Context
```rust
[Show the relevant code, ~10 lines around the error]
```

### What I Tried

1. **Attempt 1**: [Description of strategy]
   - Result: [What happened]
   - KB pattern used: [yes/no, which one]

2. **Attempt 2**: [Description]
   - Result: [What happened]
   - KB pattern used: [yes/no]

3. **Attempt 3**: [Description]
   - Result: [What happened]
   - KB pattern used: [yes/no]

### Knowledge Base Search
- Patterns found: [List or "None"]
- Why they didn't work: [Explanation]

### My Analysis
[Your understanding of why this is failing and any hypotheses]

### Specific Question
[Clear, focused question about what approach to take]
```

## After User Responds

1. **Apply the user's fix**
2. **Run verification** using `run-verification` skill
3. **Check for cheating** using `check-cheating` skill
4. **If fix works**:
   - Use `learn-pattern` skill to save to knowledge base
   - Mark source as "user"
   - Thank user and continue
5. **If fix doesn't work**:
   - Report back with new error
   - Ask for clarification if needed

## Example Interaction

**Bad request** (too vague):
> "I can't fix this error, please help"

**Good request**:
> ## I Need Help with a Verus Error
> 
> ### The Error
> ```
> error: Verus does not support the `?` operator in this context
> ```
> 
> ### Location
> - File: `src/parser.rs`
> - Line: 45
> - Function: `parse_iban`
> 
> ### What I Tried
> 1. Converting to match expression - still failed with different error
> 2. Using if-let - type mismatch
> 3. Extracting to helper function - same error
> 
> ### Specific Question
> What is the correct pattern for handling Result types in Verus when the standard ? operator isn't supported?

## Important

- Be specific, not vague
- Show your work (what you tried)
- Ask focused questions
- Save ALL successful user fixes to knowledge base
