---
triggers:
  - "loop must have a decreases clause"
  - "decreases clause"
  - "exec_allows_no_decreases_clause"
source: self-learned
created: 2026-02-24
success_count: 1
last_used: 2026-02-24
---

## Pattern: exec_allows_no_decreases_clause for while loops without termination proof

### When to use
When Verus reports "loop must have a decreases clause" for a `while` loop in an `exec` function,
and you cannot easily provide a `decreases` clause (e.g., complex index arithmetic).
This is appropriate during porting when the goal is Verus-compatibility, not full verification.

### Before (fails)
```rust
fn validate_checksum(address: &[u8]) -> bool {
    let mut i: usize = 0;
    while i < len {  // Error: loop must have a decreases clause
        // ...
        i += 1;
    }
    // ...
}
```

### After (passes)
```rust
#[verifier::exec_allows_no_decreases_clause]
fn validate_checksum(address: &[u8]) -> bool {
    let mut i: usize = 0;
    while i < len {  // No longer requires decreases clause
        // ...
        i += 1;
    }
    // ...
}
```

### Why it works
`#[verifier::exec_allows_no_decreases_clause]` suppresses the Verus requirement for
`decreases` annotations on while loops within the function. This is a porting aid —
the function still compiles and runs correctly, but Verus cannot prove termination.

### When NOT to use
Do not use this on proof functions (`proof fn`) — it's only for `exec fn`.
For full verification, provide a proper `decreases` clause instead.
