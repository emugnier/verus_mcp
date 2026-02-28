---
triggers:
  - "unsizing operation from `&mut [u8; N]` to `&mut [u8]`"
  - "The verifier does not yet support the following Rust feature: unsizing operation"
  - "array reference to slice reference unsizing"
source: self-learned
created: 2026-02-25
success_count: 1
last_used: 2026-02-25
---

## Pattern: Array Reference to Slice Reference Explicit Conversion

### When to use
When the idiom-converter's fix passes a fixed-size array reference `&mut [T; N]` to a function expecting a slice reference `&mut [T]`, causing an unsizing operation error in Verus.

This commonly occurs when:
- Converting iterator-based byte reading to direct Read::read() calls
- Passing fixed-size buffers to functions expecting slices
- Any situation where Rust would normally perform automatic unsizing coercion

### Error Example
```
error: The verifier does not yet support the following Rust feature: unsizing operation from `&mut [u8; 1]` to `&mut [u8]`
  --> src/client.rs:92
   |
92 |     let result = self.next_header_source.read(&mut single_byte_buf);
   |                                                ^^^^^^^^^^^^^^^^^^^^
```

### Context
The idiom-converter replaced:
```rust
// Original (unsupported by Verus - &mut types pattern)
let byte = self.next_header_source.by_ref().bytes().next();
```

With:
```rust
// First fix attempt (introduced unsizing error)
let mut single_byte_buf = [0u8; 1];
let result = self.next_header_source.read(&mut single_byte_buf);  // ERROR
```

The problem: `.read()` has signature `fn read(&mut self, buf: &mut [u8])` (expects slice), but `single_byte_buf` is `[u8; 1]` (array). Rust normally auto-unsizes `&mut [u8; 1]` to `&mut [u8]`, but Verus doesn't support this coercion.

### Before (fails)
```rust
let mut single_byte_buf = [0u8; 1];
let result = self.next_header_source.read(&mut single_byte_buf);
// Error: unsizing operation not supported
```

### After (passes)
```rust
let mut single_byte_buf = [0u8; 1];
let result = self.next_header_source.read(single_byte_buf.as_mut_slice());
// Explicit conversion using .as_mut_slice()
```

### Why it works
- `.as_mut_slice()` explicitly converts `&mut [T; N]` to `&mut [T]`
- No implicit unsizing coercion needed
- Semantically identical to the automatic coercion
- Works for any array size N and any element type T

### Alternative Methods

For `&mut [T; N]` to `&mut [T]`:
- `array.as_mut_slice()` - explicit method (recommended)
- `&mut array[..]` - slice syntax (also works)

For `&[T; N]` to `&[T]`:
- `array.as_slice()` - explicit method
- `&array[..]` - slice syntax

### Notes
- This is a repair pattern specifically for when idiom-converter introduces the unsizing error
- The original idiom-converter fix was correct in approach (replacing unsupported .by_ref().bytes().next())
- Only the final step (passing the buffer) needed adjustment
- No cheating involved - legitimate syntax conversion
- Always preserve exact semantics (one byte at a time, same error handling)

### Related Patterns
- `knowledge/idiom-converter/unsupported-mut-ref/by-ref-bytes-to-read.md` - the original conversion that led to this repair
