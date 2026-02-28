---
triggers:
  - "The verifier does not yet support the following Rust feature: &mut types"
  - ".iter_mut().any()"
  - "mutable iterator with any"
  - "trait implementation"
source: self-learned
created: 2026-02-25
success_count: 1
last_used: 2026-02-25
---

## Pattern: Mark Trait Impl Using iter_mut().any() as External

### When to use
When Verus reports "&mut types not supported" for code using `.iter_mut().any()` inside a trait implementation (like `From`, `Into`, etc.). This typically occurs in conversion or utility code that needs to check if any element matches a condition while having mutable access.

### Error Example
```
error: The verifier does not yet support the following Rust feature: &mut types, except in special cases
  --> src/test.rs:63:13
   |
63 |           if !mock
   |  _____________^
64 | |             .headers
65 | |             .iter_mut()
66 | |             .any(|h| h.field.equiv("Content-Length"))
   | |_____________________________________________________^
```

### Before (fails)
```rust
impl From<TestRequest> for Request {
    fn from(mut mock: TestRequest) -> Request {
        // if the user didn't set the Content-Length header, then set it for them
        // otherwise, leave it alone (it may be under test)
        if !mock
            .headers
            .iter_mut()
            .any(|h| h.field.equiv("Content-Length"))
        {
            mock.headers.push(Header {
                field: HeaderField::from_str("Content-Length").unwrap(),
                value: AsciiString::from_ascii(mock.body.len().to_string()).unwrap(),
            });
        }
        new_request(
            mock.secure,
            mock.method,
            mock.path,
            mock.http_version,
            mock.headers,
            Some(mock.remote_addr),
            mock.body.as_bytes(),
            std::io::sink(),
        )
        .unwrap()
    }
}
```

### After (passes)
```rust
// VERUS-EXTERNAL: Uses iter_mut().any() which is not supported, and this is test infrastructure
impl From<TestRequest> for Request {
    #[verifier::external_body]
    fn from(mut mock: TestRequest) -> Request {
        // if the user didn't set the Content-Length header, then set it for them
        // otherwise, leave it alone (it may be under test)
        if !mock
            .headers
            .iter_mut()
            .any(|h| h.field.equiv("Content-Length"))
        {
            mock.headers.push(Header {
                field: HeaderField::from_str("Content-Length").unwrap(),
                value: AsciiString::from_ascii(mock.body.len().to_string()).unwrap(),
            });
        }
        new_request(
            mock.secure,
            mock.method,
            mock.path,
            mock.http_version,
            mock.headers,
            Some(mock.remote_addr),
            mock.body.as_bytes(),
            std::io::sink(),
        )
        .unwrap()
    }
}
```

### Why it works
1. **Use external_body on the function**: The `#[verifier::external_body]` attribute tells Verus to skip verification of this specific function body
2. **Attribute placement**: The attribute goes on the function itself, not on the `impl` block
3. **Eliminates verification of unsupported feature**: `.iter_mut()` returns mutable references which Verus has limited support for, and `.any()` is an iterator combinator that's also limited
4. **Preserves functionality**: The trait impl still works exactly the same at runtime
5. **Appropriate for conversion/utility code**: Trait implementations like `From`, `Into`, `TryFrom` often contain glue logic that:
   - Performs simple transformations or checks
   - Uses standard library iterator methods
   - Doesn't contain verification-worthy invariants
   - Is test infrastructure or utility code

### When to apply this pattern

Use `#[verifier::external_body]` on functions in trait impls with `.iter_mut().any()` when:
- The trait impl performs simple collection checks or transformations
- The logic is straightforward comparison or validation
- No complex invariants or mathematical properties need verification
- The impl is for test infrastructure, conversion helpers, or utility code
- The trait is a standard trait like `From`, `Into`, `TryFrom`, etc.

### Difference from marking methods as external

| Scenario | Attribute to Use | Where to Place |
|----------|-----------------|----------------|
| Method on a type | `#[verifier::external_body]` or `#[verifier::external]` | On the method |
| Function in trait impl | `#[verifier::external_body]` | On the function |
| Entire function | `#[verifier::external]` | On the function |

**IMPORTANT:** Do NOT use `#[verifier::external_trait_specification]` for this pattern. That attribute is for defining specifications for external traits (from other crates), not for marking your own trait implementations as unverified.

### Alternative approaches

If the trait impl contains critical logic that MUST be verified:
1. **Refactor to avoid iter_mut()**: Use `.iter()` if you don't actually need mutable access (note: `.any()` doesn't modify elements, so `.iter()` might work)
2. **Use index-based loops**: Replace iterator with manual loop and indexing
3. **Extract only the problematic part**: Create a helper function marked external, verify the rest

In this specific case, note that `.any()` doesn't modify elements, so you could potentially use `.iter().any()` instead of `.iter_mut().any()`. However, if the variable is already `mut` and the rest of the code needs mutability, using `external_body` is simpler.

### Common mistakes

**WRONG:** Using `#[verifier::external_trait_specification]` on the impl block
```rust
#[verifier::external_trait_specification]  // WRONG!
impl From<TestRequest> for Request {
    fn from(mut mock: TestRequest) -> Request { ... }
}
```

This is incorrect because `external_trait_specification` is for creating specifications for external traits (like traits from std or other crates), not for marking your own implementations as unverified. The error will persist if you use this attribute.

### Notes
- This pattern applies to any `.iter_mut()` usage in trait impls, not just `.any()`
- Other iterator methods like `.filter()`, `.map()`, `.find()` on `.iter_mut()` will have the same issue
- The `// VERUS-EXTERNAL:` comment should explain BOTH that iter_mut is unsupported AND what the trait impl does
- All changes remain inside the `verus! { }` block
- Cargo build and cargo test should pass after this conversion
- If you don't need mutability for the iterator, consider using `.iter()` instead

### Related patterns
- `iter-mut-find-to-external.md` - marking methods with `.iter_mut().find()` as external
- `by-ref-bytes-to-read.md` - another &mut types pattern for `.by_ref().bytes()`
- Any pattern dealing with trait implementations in Verus
