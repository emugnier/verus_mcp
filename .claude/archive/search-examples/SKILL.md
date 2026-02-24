---
name: search-examples
description: LAST RESORT - Use veracity-search to find similar verified examples. Use sparingly, only when truly stuck.
allowed-tools: Bash
---

# Search Examples Skill (Last Resort)

Use `veracity-search` CLI to find similar verified Verus code examples.

## When to Use

ONLY use after ALL of these conditions are met:
1. Knowledge base search found nothing relevant
2. Multiple fix attempts failed (3+)
3. No obvious solution from error message alone
4. User help is not immediately available

This is a **last resort** - use sparingly.

## What is veracity-search?

A type-based semantic search tool for Verus code. It searches through verified Verus codebases to find:
- Functions with similar signatures
- Traits and implementations
- Structs and enums
- Type aliases
- Similar proof patterns

## Usage

```bash
# Search for functions with similar types
veracity-search "fn parse(s: &str) -> Option<T>"

# Search for traits
veracity-search "trait Validate"

# Search for specific patterns
veracity-search "Vec<u8> -> Seq<u8>"

# Search for proof patterns
veracity-search "ensures result.len() == input.len()"
```

## Search Strategies

### For Unsupported Features
Search for how others handled similar constructs:
```bash
veracity-search "Result<T, E>"  # How to handle Results
veracity-search "Iterator"       # How to replace iterators
veracity-search "? operator"     # Alternative to ? operator
```

### For Type Conversions
Search for conversion patterns:
```bash
veracity-search "Vec -> Seq"
veracity-search "String -> &str"
veracity-search "HashMap"
```

### For Specification Patterns
Search for how to specify similar functions:
```bash
veracity-search "ensures forall"
veracity-search "requires valid"
veracity-search "decreases"
```

## Output Interpretation

Results will show:
- File paths with matching code
- Function/struct signatures
- Relevant specifications
- Proof patterns used

## After Finding Examples

1. **Understand the pattern** - Don't just copy, understand why it works
2. **Adapt to your context** - Examples may need modification
3. **Verify it works** - Run verification after applying
4. **Save to knowledge base** - If successful, use `learn-pattern` to save

## Important Caveats

- **Expensive operation** - Don't use repeatedly for same error
- **Not always accurate** - Results may not directly apply
- **Context matters** - Example code may have different assumptions
- **Save learnings** - Extract the pattern and save to KB so you don't need this again

## Example Workflow

1. Error: "Verus does not support HashMap"
2. KB search: No patterns found
3. 3 fix attempts: All failed
4. veracity-search: `veracity-search "HashMap alternative"`
5. Found: Example using `Map<K,V>` from vstd
6. Apply similar pattern
7. Verification passes
8. Save pattern to `knowledge/idiom-converter/unsupported-types/hashmap-to-map.md`
