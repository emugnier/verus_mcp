---
triggers:
  - "The verifier does not yet support the following Rust feature: &mut types"
  - "external_trait_specification doesn't fix error"
  - "trait impl still failing after external_trait_specification"
source: self-learned
created: 2026-02-25
success_count: 1
last_used: 2026-02-25
---

## Pattern: external_trait_specification vs external_body - Wrong Attribute Used

### When to use
When a previous fix applied `#[verifier::external_trait_specification]` to a trait implementation, but the "&mut types not supported" error persists. This indicates the wrong attribute was used.

### Original Error
```
error: The verifier does not yet support the following Rust feature: &mut types, except in special cases
  --> src/test.rs:65:13
   |
65 |           if !mock
   |  _____________^
66 | |             .headers
67 | |             .iter_mut()
68 | |             .any(|h| h.field.equiv("Content-Length"))
   | |_____________________________________________________^
```

### Failed Fix (still errors)
```rust
// VERUS-EXTERNAL: Uses iter_mut().any() which is not supported, and this is test infrastructure
#[verifier::external_trait_specification]
impl From<TestRequest> for Request {
    fn from(mut mock: TestRequest) -> Request {
        if !mock
            .headers
            .iter_mut()
            .any(|h| h.field.equiv("Content-Length"))
        {
            // ... body ...
        }
        // ... rest of function ...
    }
}
```

**Why this fails:** `#[verifier::external_trait_specification]` is for creating *specifications* for external traits (like specifying the behavior of a trait from another crate). It is NOT for marking your own trait implementations as unverified.

### Correct Fix (passes)
```rust
// VERUS-EXTERNAL: Uses iter_mut().any() which is not supported, and this is test infrastructure
impl From<TestRequest> for Request {
    #[verifier::external_body]
    fn from(mut mock: TestRequest) -> Request {
        if !mock
            .headers
            .iter_mut()
            .any(|h| h.field.equiv("Content-Length"))
        {
            // ... body ...
        }
        // ... rest of function ...
    }
}
```

### Why it works
1. **Removed external_trait_specification**: This attribute was never appropriate for this use case
2. **Added external_body on the function**: This tells Verus to skip verification of the function body
3. **Attribute placement**: The attribute goes directly on the function, not on the `impl` block

### Key Distinction

| Attribute | Purpose | Where to use |
|-----------|---------|--------------|
| `#[verifier::external_trait_specification]` | Define specs for external traits | When specifying behavior of traits from other crates (like `std::io::Read`) |
| `#[verifier::external_body]` | Skip verification of function body | When marking your own functions as unverified (like functions with unsupported features) |
| `#[verifier::external]` | Mark entire item as external | For functions, but `external_body` is preferred for trait methods |

### When to apply this repair

Apply this repair when:
- A previous fix added `#[verifier::external_trait_specification]` to a trait impl
- The original error still persists after that fix
- The trait being implemented is a standard trait (From, Into, TryFrom, etc.)
- The implementation is YOUR code, not specifying behavior of someone else's trait

### Common mistakes that lead to this

1. **Misunderstanding external_trait_specification**: Seeing "trait" in the attribute name and thinking it's for trait impls
2. **Following incorrect KB patterns**: If an idiom-converter pattern incorrectly suggests external_trait_specification
3. **Confusion about attribute placement**: Not realizing the attribute should go on the function, not the impl

### Repair strategy

1. Remove `#[verifier::external_trait_specification]` from the `impl` line
2. Add `#[verifier::external_body]` on the function inside the trait impl
3. Keep the explanatory comment
4. Verify the fix resolves the error

### Related patterns
- Any pattern dealing with marking functions as external
- Patterns about trait implementations in Verus

### Notes
- The comment should remain to explain WHY the function is marked external
- All changes remain inside the `verus! { }` block
- This is a repair pattern - it fixes an incorrect first attempt
- If you need to mark multiple methods in a trait impl as external, use `#[verifier::external_body]` on each method individually
