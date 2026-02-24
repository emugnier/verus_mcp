---
name: check-cheating
description: Check that fixes don't bypass Verus verification through cheating patterns. Use to validate code changes.
allowed-tools: mcp__verus-mcp, Read, Grep, Glob
---

# Check Cheating Skill

Verify that a fix doesn't cheat by bypassing Verus verification.

## MCP Tool Available

Use the `mcp__verus-mcp__check_cheat` tool for automated detection:

```
mcp__verus-mcp__check_cheat(path: "path/to/file_or_directory")
```

This tool automatically scans for:
- `assume` statements without proof
- `admit()` calls
- `#[verifier::external_body]` attributes
- `#[verifier::external]` attributes
- `exec` blocks that bypass verification

Returns a report of all cheating patterns found.

## Manual Verification (if needed)

If the MCP tool is unavailable, you can manually check:

### Automatic Rejection Patterns
```rust
assume(...)      // Assumes without proof
admit()          // Admits without proof
#[verifier::external_body]  // Skips body verification
#[verifier::external]       // Marks as external
exec { ... }     // Exec blocks that bypass verification
```

### Search Commands (fallback)
```bash
# Search for assume statements
grep -n "assume(" <file>

# Search for admit calls
grep -n "admit()" <file>

# Search for external_body
grep -n "external_body" <file>

# Search for external attribute
grep -n "verifier::external" <file>

# Search for exec blocks
grep -n "exec" <file>
```

## Check 2: Code Still in Verus Block

Verify that code that was previously inside a `verus! { }` block is still inside a verus block after the fix.

### What to Check
1. Locate all `verus! {` and matching `}` in the file
2. Ensure functions/code that were inside verus blocks before the change are still inside verus blocks
3. Code should NOT be moved outside verus blocks to avoid verification

### Detection
```bash
# Find verus block boundaries
grep -n "verus!" <file>
```

### Red Flags
- Function moved from inside `verus! { }` to outside
- Code extracted to a non-verified helper outside the block
- Entire verus block removed or commented out

## Verdict Format

```
cheating_detected: true/false
explicit_cheats: pass/fail
verus_block_integrity: pass/fail
violations: [list of specific issues found]
recommendation: accept/reject
```

## Decision Rules

- If ANY `assume(...)` or `admit()` found: **REJECT**
- If `external_body` added to previously verified function: **REJECT**
- If code moved outside verus block to avoid verification: **REJECT**
- If all checks pass: **ACCEPT**

## Important

A fix that passes verification by cheating is WORSE than no fix at all. Be strict.
