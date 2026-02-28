---
triggers:
  - "The verifier does not yet support the following Rust feature: &mut types"
  - ".by_ref().bytes().next()"
  - "mutable reference in iterator chain"
source: self-learned
created: 2026-02-25
success_count: 1
last_used: 2026-02-25
---

## Pattern: Convert `.by_ref().bytes().next()` to Direct `Read::read()`

### When to use
When Verus reports "&mut types not supported" for code using `.by_ref()` in an iterator chain, particularly with `.bytes().next()` to read a single byte without consuming the reader.

### Error Example
```
error: The verifier does not yet support the following Rust feature: &mut types, except in special cases
  --> src/client.rs:91
   |
91 |             let byte = self.next_header_source.by_ref().bytes().next();
   |                                                ^^^^^^^^
```

### Before (fails)
```rust
loop {
    let byte = self.next_header_source.by_ref().bytes().next();

    let byte = match byte {
        Some(b) => b?,
        None => return Err(IoError::new(ErrorKind::ConnectionAborted, "Unexpected EOF")),
    };

    // ... use byte ...
}
```

### After (passes)
```rust
loop {
    let mut single_byte_buf = [0u8; 1];
    let result = self.next_header_source.read(&mut single_byte_buf);

    let byte = match result {
        Ok(0) => return Err(IoError::new(ErrorKind::ConnectionAborted, "Unexpected EOF")),
        Ok(_) => single_byte_buf[0],
        Err(e) => return Err(e),
    };

    // ... use byte ...
}
```

### Why it works
1. **Eliminates `.by_ref()`**: Direct method call on `self.next_header_source` avoids creating a mutable reference
2. **Uses `Read::read()` directly**: Since `SequentialReader` (or similar type) implements `Read`, we can call `.read()` directly
3. **Single-byte buffer**: Using `[0u8; 1]` array avoids variable shadowing issues with existing buffers
4. **Preserves semantics**:
   - Reading one byte at a time: ✓
   - EOF detection (read returns 0): ✓
   - Error propagation: ✓
   - Doesn't consume the reader: ✓

### Notes
- This pattern works for any type implementing `std::io::Read`
- Be careful about variable naming - use a distinct name for the single-byte buffer to avoid shadowing existing variables (e.g., if there's already a `buf` Vec, use `single_byte_buf`)
- The conversion is semantically equivalent: both read exactly one byte per iteration
- Cargo build and cargo test should pass after this conversion, confirming behavior is preserved
