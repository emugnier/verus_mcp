---
triggers:
  - "Unsupported constant type"
  - "byte string literal"
  - "b\"...\""
source: self-learned
created: 2026-02-25
success_count: 1
last_used: 2026-02-25
---

## Pattern: Byte String Literals to External Method

### When to use
When Verus reports "Unsupported constant type" for byte string literals (`b"..."`). This occurs when using Rust byte string syntax which Verus doesn't support.

### Error Example
```
error: Unsupported constant type
   --> src/response.rs:562:37
    |
562 |                 Header::from_bytes(&b"Content-Type"[..], &b"text/plain; charset=UTF-8"[..])
    |                                     ^^^^^^^^^^^^^^^
```

### Before (fails)
```rust
pub fn from_string<S>(data: S) -> Response<Cursor<Vec<u8>>>
where
    S: Into<String>,
{
    let data = data.into();
    let data_len = data.len();

    Response::new(
        StatusCode(200),
        vec![
            Header::from_bytes(&b"Content-Type"[..], &b"text/plain; charset=UTF-8"[..])
                .unwrap(),
        ],
        Cursor::new(data.into_bytes()),
        Some(data_len),
        None,
    )
}
```

### After (passes)
```rust
// VERUS-EXTERNAL: Uses byte string literals which Verus doesn't support
#[verifier::external]
pub fn from_string<S>(data: S) -> Response<Cursor<Vec<u8>>>
where
    S: Into<String>,
{
    let data = data.into();
    let data_len = data.len();

    Response::new(
        StatusCode(200),
        vec![
            Header::from_bytes(&b"Content-Type"[..], &b"text/plain; charset=UTF-8"[..])
                .unwrap(),
        ],
        Cursor::new(data.into_bytes()),
        Some(data_len),
        None,
    )
}
```

### Why it works
Verus doesn't support the `b"..."` byte string literal syntax. By marking the entire method containing the byte string literal as `#[verifier::external]`, we tell Verus to skip verification of this method body while still type-checking its signature.

This is appropriate when:
1. The method is a simple helper/constructor that doesn't need verification
2. The logic is straightforward and unlikely to have bugs
3. The byte string literals are for constant headers, protocol strings, etc.

### Notes
- Use `#[verifier::external]` for regular methods
- Use `#[verifier::external_body]` for free functions if needed
- Always add a comment explaining why the method is marked external
- If byte string literals appear in already-external methods (like I/O operations), no additional action needed
- This pattern is common in HTTP libraries, serialization code, and protocol implementations
