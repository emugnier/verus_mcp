---
triggers:
  - "The verifier does not yet support the following Rust feature: &mut types"
  - ".iter_mut().find()"
  - "mutable iterator with find"
source: self-learned
created: 2026-02-25
success_count: 1
last_used: 2026-02-25
---

## Pattern: Mark Method Using iter_mut().find() as External

### When to use
When Verus reports "&mut types not supported" for code using `.iter_mut().find()` to locate and modify an element in a collection. This typically occurs in methods that need to find and update a specific item.

### Error Example
```
error: The verifier does not yet support the following Rust feature: &mut types, except in special cases
   --> src/response.rs:294:48
    |
294 |               if let Some(content_type_header) = self
    |  ________________________________________________^
295 | |                 .headers
296 | |                 .iter_mut()
297 | |                 .find(|h| h.field.equiv("Content-Type"))
    | |________________________________________________________^
```

### Before (fails)
```rust
pub fn add_header<H>(&mut self, header: H)
where
    H: Into<Header>,
{
    let header = header.into();

    // ... other logic ...

    // if the header is Content-Type and it's already set, overwrite it
    if header.field.equiv("Content-Type") {
        if let Some(content_type_header) = self
            .headers
            .iter_mut()
            .find(|h| h.field.equiv("Content-Type"))
        {
            content_type_header.value = header.value;
            return;
        }
    }

    self.headers.push(header);
}
```

### After (passes)
```rust
// VERUS-EXTERNAL: Uses iter_mut() which is not supported, and contains HTTP header manipulation logic
#[verifier::external]
pub fn add_header<H>(&mut self, header: H)
where
    H: Into<Header>,
{
    let header = header.into();

    // ... other logic ...

    // if the header is Content-Type and it's already set, overwrite it
    if header.field.equiv("Content-Type") {
        if let Some(content_type_header) = self
            .headers
            .iter_mut()
            .find(|h| h.field.equiv("Content-Type"))
        {
            content_type_header.value = header.value;
            return;
        }
    }

    self.headers.push(header);
}
```

### Why it works
1. **Eliminates verification of unsupported feature**: `.iter_mut()` returns mutable references which Verus has limited support for
2. **Preserves functionality**: The method still works exactly the same at runtime
3. **Appropriate for utility methods**: Methods that manipulate collections based on custom logic (like HTTP header management) are good candidates for `#[verifier::external]` since they:
   - Don't contain complex verification-worthy invariants
   - Rely on standard library collection operations
   - Have straightforward semantics that Rust's type system already validates

### When to apply this pattern

Use `#[verifier::external]` for methods with `.iter_mut().find()` when:
- The method performs simple collection manipulation (find, update, or remove)
- The logic is straightforward string/field comparison
- No complex invariants or mathematical properties need verification
- The method is a utility function (e.g., header management, config updates)

### Alternative approaches

If the method contains critical logic that MUST be verified:
1. **Refactor to avoid iter_mut()**: Use index-based loops with manual search
2. **Extract only the iter_mut part**: Mark a small helper as external, verify the rest
3. **Use Vec indexing**: If you know the position, access by index instead

For this specific case (HTTP header manipulation), marking the entire method as external is appropriate since it's standard collection management logic.

### Notes
- This pattern applies to any `.iter_mut()` usage, not just `.find()`
- Other iterator methods like `.filter()`, `.map()` on `.iter_mut()` will have the same issue
- The `// VERUS-EXTERNAL:` comment should explain BOTH that iter_mut is unsupported AND what the method does (e.g., "HTTP header manipulation")
- All changes remain inside the `verus! { }` block
- Cargo build and cargo test should pass after this conversion

### Related patterns
- `by-ref-bytes-to-read.md` - another &mut types pattern for `.by_ref().bytes()`
- `mut-self-builder-methods.md` - marking builder methods as external
