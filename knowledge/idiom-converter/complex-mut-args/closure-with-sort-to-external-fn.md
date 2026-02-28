---
triggers:
  - "complex arguments to &mut parameters are currently unsupported"
  - "complex arguments to &mut parameters"
  - "sort_by in closure"
source: self-learned
created: 2026-02-25
success_count: 1
last_used: 2026-02-25
---

## Pattern: Extract Closure with Mutable Operations to External Helper

### When to use
When Verus reports "complex arguments to &mut parameters are currently unsupported" and the error points to a method call like `.sort_by()` or other mutable operations inside a closure (e.g., within `.and_then()`, `.map()`, etc.). This is especially applicable when the closure also contains other unsupported features like for loops over iterators.

### Error Example
```
error: complex arguments to &mut parameters are currently unsupported
   --> src/response.rs:155:13
    |
155 |             parse.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(Ordering::Equal));
    |             ^^^^^
```

### Before (fails)
```rust
let user_request = request_headers_iter
    .find(|h| h.field.equiv("TE"))
    .map(|h| h.value.clone())
    .and_then(|value| {
        let mut parse = util::parse_header_value(value.as_str());

        // Complex mutable operation in closure
        parse.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(Ordering::Equal));

        // Also has unsupported for loop
        for value in parse.iter() {
            if value.1 <= 0.0 {
                continue;
            }
            if let Ok(te) = TransferEncoding::from_str(value.0) {
                return Some(te);
            }
        }
        None
    });
```

### After (passes)
```rust
// Extract to separate helper function marked as external
#[verifier::external]
fn parse_te_header_value(value: AsciiString) -> Option<TransferEncoding> {
    use crate::util;

    let mut parse = util::parse_header_value(value.as_str());

    // Complex mutable operations are now in external function
    parse.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(Ordering::Equal));

    for value in parse.iter() {
        if value.1 <= 0.0 {
            continue;
        }
        if let Ok(te) = TransferEncoding::from_str(value.0) {
            return Some(te);
        }
    }
    None
}

let user_request = request_headers_iter
    .find(|h| h.field.equiv("TE"))
    .map(|h| h.value.clone())
    .and_then(parse_te_header_value);  // Now just a simple function reference
```

### Why it works
When complex mutable operations like `sort_by` appear inside closures, Verus has difficulty with the nested complexity of:
1. The closure context
2. The mutable borrow required by `sort_by`
3. The complex expression as an argument to the `&mut` parameter

By extracting the entire closure body to a separate function marked `#[verifier::external]`, we:
- Remove the nested complexity from Verus's analysis
- Allow the standard Rust compiler to handle the mutable operations
- Keep the main logic flow clean and verifiable
- Preserve the exact semantics (the extracted function does exactly what the closure did)

The `#[verifier::external]` attribute is appropriate here because:
- The code involves complex data structure manipulation (sorting, iteration)
- It's typically parsing/processing external data (HTTP headers)
- The core verification goal is the higher-level logic, not the parsing details

### Notes
- Use this pattern when a closure contains mutable operations that cause "complex arguments" errors
- The extracted function should be marked `#[verifier::external]` to bypass verification
- Document WHY the function is marked external (e.g., "complex sorting and iteration")
- Ensure the function signature matches what the closure expected (parameter types, return type)
- This is semantically equivalent - just moving code to a different location
- The function name should describe what it does (e.g., `parse_te_header_value`)
- Keep the extracted function close to where it's used for code readability

### Related patterns
- `iter-call-to-variable.md` - simpler case where just extracting `.iter()` is sufficient
- For cases where the mutable operation can be converted to supported syntax, prefer that over marking external
- Only use `#[verifier::external]` when the complexity genuinely requires it
