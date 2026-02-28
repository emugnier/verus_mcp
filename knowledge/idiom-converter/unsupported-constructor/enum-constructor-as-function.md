---
triggers:
  - "using a datatype constructor as a function value"
  - "datatype constructor as a function"
  - "The verifier does not yet support the following Rust feature: using a datatype constructor as a function value"
source: self-learned
created: 2026-02-25
success_count: 1
last_used: 2026-02-25
---

## Pattern: Enum Constructor as Function Value to Explicit Closure

### When to use
When Verus reports that using a datatype (enum/struct) constructor as a function value is not supported. This commonly occurs with `.map_err()`, `.map()`, `.ok_or()`, and similar combinator methods where an enum variant constructor is passed directly as a function argument.

### Error Example
```
error: The verifier does not yet support the following Rust feature: using a datatype constructor as a function value
  --> src/client.rs:121:52
   |
121 |     let line = self.read_next_line().map_err(ReadError::ReadIoError)?;
   |                                                ^^^^^^^^^^^^^^^^^^^^^^
```

### Before (fails)
```rust
let line = self.read_next_line().map_err(ReadError::ReadIoError)?;

// Other common patterns that fail:
let result = value.map(SomeEnum::Variant);
let option = result.ok_or(ErrorEnum::SomeError);
```

### After (passes)
```rust
let line = self.read_next_line().map_err(|e| ReadError::ReadIoError(e))?;

// Other patterns converted:
let result = value.map(|v| SomeEnum::Variant(v));
let option = result.ok_or_else(|| ErrorEnum::SomeError);
```

### Why it works
In Rust, enum and struct constructors can be used as first-class functions because they implement `FnOnce`. However, Verus doesn't support this feature yet. By converting the constructor to an explicit closure `|x| Constructor(x)`, we achieve the same semantics in a way that Verus can understand.

For unit variants (no fields), the constructor is just a value, not a function, so this conversion isn't needed:
```rust
// This is fine - unit variant, not a function
result.ok_or(ReadError::WrongRequestLine)
```

### Notes
- This pattern applies to any combinator method: `.map()`, `.map_err()`, `.and_then()`, `.or_else()`, `.ok_or_else()`, etc.
- Only needed for constructors that take arguments (tuple variants or structs with fields)
- Unit variants (no fields) don't need conversion - they're values, not functions
- The semantics are identical - this is purely a syntactic transformation
- Search for patterns like `.map_err(EnumVariant)`, `.map(Constructor)` to find all instances
