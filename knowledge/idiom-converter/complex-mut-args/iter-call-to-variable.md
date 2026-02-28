---
triggers:
  - "complex arguments to &mut parameters are currently unsupported"
  - "complex arguments to &mut parameters"
  - "&mut parameters - method call in argument"
source: self-learned
created: 2026-02-25
success_count: 1
last_used: 2026-02-25
---

## Pattern: Extract Iterator Call to Variable

### When to use
When Verus reports "complex arguments to &mut parameters are currently unsupported" and the error points to a method call like `.iter()` that is part of a larger expression involving methods that take `&mut self` (like `.find()`, `.next()`, etc.).

### Error Example
```
error: complex arguments to &mut parameters are currently unsupported
  --> src/client.rs:254:37
   |
254 |             let connection_header = headers.iter().find(|h| h.field.equiv("Connection")).map(|h| h.value.as_str());
   |                                     ^^^^^^^^^^^^^
```

### Before (fails)
```rust
let headers = rq.headers();
let connection_header = headers.iter().find(|h| h.field.equiv("Connection")).map(|h| h.value.as_str());
```

### After (passes)
```rust
let headers = rq.headers();
let mut headers_iter = headers.iter();
let connection_header = headers_iter.find(|h| h.field.equiv("Connection")).map(|h| h.value.as_str());
```

### Why it works
Methods like `.find()` take `&mut self` on the iterator. Verus doesn't support complex expressions (like method calls) as arguments to `&mut` parameters. By extracting the `.iter()` call into a separate variable, the mutable borrow becomes explicit and simple - just a variable name, not a complex expression.

The iterator variable must be declared as `mut` because subsequent methods like `.find()` will mutate it.

### Notes
- This pattern applies to any iterator method call that's part of a chain where later methods require `&mut self`
- Common methods requiring `&mut self`: `.next()`, `.find()`, `.any()`, `.all()`, etc.
- Always declare the iterator variable as `mut`
- The rest of the method chain can remain unchanged after the extraction
- This is a purely syntactic transformation - program semantics are preserved exactly

### Related patterns
- `by-ref-bytes-to-read.md` - similar issue with `.by_ref()` chains
- `enum-constructor-as-function.md` - another Verus syntactic restriction
