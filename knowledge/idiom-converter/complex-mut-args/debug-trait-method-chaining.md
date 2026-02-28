---
triggers:
  - "complex arguments to &mut parameters are currently unsupported"
  - "fmt.debug_struct"
  - "debug_struct builder pattern"
source: self-learned
created: 2026-02-26
success_count: 1
last_used: 2026-02-26
---

## Pattern: Mark Debug Trait Implementation as External Body

### When to use
When Verus reports "complex arguments to &mut parameters are currently unsupported" and the error points to a `fmt::Debug` trait implementation that uses the builder pattern with method chaining (e.g., `fmt.debug_struct().field().finish()`).

### Error Example
```
error: complex arguments to &mut parameters are currently unsupported
   --> src/block.rs:133:9
    |
133 |         fmt.debug_struct("BlockRng")
    |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
```

### Before (fails)
```rust
impl<G> fmt::Debug for BlockRng<G>
where
    G: Generator + fmt::Debug,
{
    fn fmt(&self, fmt: &mut fmt::Formatter) -> fmt::Result {
        fmt.debug_struct("BlockRng")
            .field("core", &self.core)
            .finish_non_exhaustive()
    }
}
```

### After (passes)
```rust
impl<G> fmt::Debug for BlockRng<G>
where
    G: Generator + fmt::Debug,
{
    // VERUS-EXTERNAL: Debug builder pattern with method chaining not supported
    #[verifier::external_body]
    fn fmt(&self, fmt: &mut fmt::Formatter) -> fmt::Result {
        fmt.debug_struct("BlockRng")
            .field("core", &self.core)
            .finish_non_exhaustive()
    }
}
```

### Why it works
The Debug trait's builder pattern (`.debug_struct().field().finish()`) involves method chaining where each method takes `&mut self` and returns `&mut Self`. This creates complex mutable borrows that Verus doesn't support.

Marking the `fmt` method as `#[verifier::external_body]` is appropriate because:
1. Debug implementations are for display/formatting, not core verification targets
2. They rarely contain verification-worthy invariants
3. The builder pattern with method chaining is idiomatic Rust that Verus doesn't fully support
4. The correctness of Debug output is not critical to program correctness

### Notes
- This applies to all Debug trait implementations using the builder pattern
- Also applies to Display trait implementations with similar method chaining
- The `#[verifier::external_body]` should be placed on the `fmt` method, not the entire impl block
- Always add a comment explaining why (e.g., "// VERUS-EXTERNAL: Debug builder pattern...")
- This preserves the Debug implementation for normal Rust compilation while skipping verification

### Related patterns
- `closure-with-sort-to-external-fn.md` - more complex case requiring full function extraction
- `iter-call-to-variable.md` - simpler case where extraction to variable suffices
- For non-trait methods with complex mut args, consider those patterns first
