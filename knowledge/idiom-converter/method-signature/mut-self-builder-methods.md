---
triggers:
  - "Verus does not support `mut self`"
  - "mut self not supported"
  - "mut self in method signature"
  - "builder pattern mut self"
source: self-learned
created: 2026-02-25
success_count: 2
last_used: 2026-02-25
---

## Pattern: Mark Builder Pattern Methods with mut self as External

### When to use
When Verus reports "Verus does not support `mut self`" or "mut self not supported" for builder pattern methods (consuming methods) that take `mut self` as a parameter and return `Self`. These are typically simple field update methods that don't contain complex logic requiring verification.

### Error Example
```
error: Verus does not support `mut self` in method signatures
  --> src/response.rs:246:39
   |
246 |     pub fn with_chunked_threshold(mut self, length: usize) -> Response<R> {
   |                                       ^^^^
```

### Before (fails)
```rust
impl<R> Response<R>
where
    R: Read,
{
    /// Builder pattern method
    pub fn with_chunked_threshold(mut self, length: usize) -> Response<R> {
        self.chunked_threshold = Some(length);
        self
    }

    pub fn with_header<H>(mut self, header: H) -> Response<R>
    where
        H: Into<Header>,
    {
        self.add_header(header.into());
        self
    }

    pub fn with_status_code<S>(mut self, code: S) -> Response<R>
    where
        S: Into<StatusCode>,
    {
        self.status_code = code.into();
        self
    }
}
```

### After (passes)
```rust
impl<R> Response<R>
where
    R: Read,
{
    /// Builder pattern method
    // VERUS-EXTERNAL: mut self not supported in method signatures
    #[verifier::external]
    pub fn with_chunked_threshold(mut self, length: usize) -> Response<R> {
        self.chunked_threshold = Some(length);
        self
    }

    // VERUS-EXTERNAL: mut self not supported in method signatures
    #[verifier::external]
    pub fn with_header<H>(mut self, header: H) -> Response<R>
    where
        H: Into<Header>,
    {
        self.add_header(header.into());
        self
    }

    // VERUS-EXTERNAL: mut self not supported in method signatures
    #[verifier::external]
    pub fn with_status_code<S>(mut self, code: S) -> Response<R>
    where
        S: Into<StatusCode>,
    {
        self.status_code = code.into();
        self
    }
}
```

### Why it works
Verus does not support `mut self` receiver parameters in method signatures. This is a fundamental limitation of Verus's type system. Builder pattern methods typically:

1. Take ownership of `self` (consume it)
2. Modify fields
3. Return the modified instance

These are simple field updates that don't contain complex verification logic, making them good candidates for marking as `#[verifier::external]`. The semantic behavior is straightforward and can be trusted without verification.

### When to apply this pattern

Use `#[verifier::external]` for builder methods when:
- The method takes `mut self` as a parameter
- The method is a simple field update (builder pattern)
- The method returns `Self` or similar
- No complex logic or invariants need verification
- The error specifically mentions "mut self not supported"

For methods with `mut self` that also contain complex I/O or other unsupported operations, mention both reasons in the comment:
```rust
// VERUS-EXTERNAL: mut self not supported, and contains complex I/O operations
#[verifier::external]
pub fn raw_print<W: Write>(mut self, mut writer: W, ...) -> IoResult<()> {
    // complex I/O logic
}
```

### Notes
- This is appropriate for builder pattern methods that are simple field updates
- The `#[verifier::external]` attribute tells Verus to trust the Rust compiler's type checking without attempting verification
- Document the reason with a `// VERUS-EXTERNAL:` comment above the attribute
- This preserves the API exactly - no signature changes needed
- The semantics are identical - just bypassing Verus verification for these methods
- All changes should remain inside the `verus! { }` block

### Related patterns
- `closure-with-sort-to-external-fn.md` - extracting complex operations to external functions
- For non-builder methods with `mut self`, consider if they can be refactored to use `&mut self` instead
