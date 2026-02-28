---
triggers:
  - "assume_specification"
  - "use a named param instead of 'self' argument"
  - "mismatched types: expected &u8, found u8"
  - "is_ascii_uppercase"
  - "is_ascii_digit"
  - "is_ascii_alphanumeric"
  - "to_ascii_uppercase"
source: self-learned
created: 2026-02-24
success_count: 1
last_used: 2026-02-24
---

## Pattern: assume_specification for &self methods — parameter must be &T not T

### When to use
When writing `assume_specification` for methods that take `&self` (not `self`),
e.g., u8 ASCII predicate methods or other `&self` methods.
Verus will error with "use a named param instead of 'self' argument" if you use `self: T`,
and "mismatched types" if you use `c: T` instead of `c: &T`.

### Before (fails)
```rust
// Error: "use a named param instead of 'self' argument"
pub assume_specification[ <u8>::is_ascii_uppercase ](self: u8) -> (result: bool);

// Error: "mismatched types: expected &u8, found u8"
pub assume_specification[ <u8>::is_ascii_uppercase ](c: u8) -> (result: bool);
```

### After (passes)
```rust
// Correct: &self methods get parameter type &T
pub assume_specification[ <u8>::is_ascii_uppercase ](c: &u8) -> (result: bool);
pub assume_specification[ <u8>::is_ascii_digit ](c: &u8) -> (result: bool);
pub assume_specification[ <u8>::is_ascii_alphanumeric ](c: &u8) -> (result: bool);
pub assume_specification[ <u8>::to_ascii_uppercase ](c: &u8) -> (result: u8);
```

### Why it works
`&self` methods in Rust take a reference to self. In `assume_specification` syntax,
you cannot use `self` as a parameter name — Verus requires a named parameter.
The type must match the actual receiver type: `&u8` for `&self` on `u8`.

### Enabling assume_specification
`assume_specification` generates internal unsafe code. If the crate has `#![forbid(unsafe_code)]`
in its root, this lint will block compilation. Remove that lint attribute to enable it.
```rust
// In lib.rs or main.rs — remove this line:
// #![forbid(unsafe_code)]
```
