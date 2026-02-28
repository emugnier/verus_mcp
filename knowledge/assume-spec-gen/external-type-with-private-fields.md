---
triggers:
  - "external_type_specification: private fields not supported for transparent datatypes"
  - "private fields not supported"
  - "ArrayString is not supported"
  - "CapacityError is not supported"
  - "is not supported in Verus"
source: self-learned
created: 2026-02-24
success_count: 1
last_used: 2026-02-24
---

## Pattern: external_type_specification with external_body for 3rd-party types with private fields

### When to use
When Verus reports that a 3rd-party crate type (e.g., `ArrayString`, `CapacityError` from arrayvec) is not supported,
OR when you try to add `external_type_specification` and get "private fields not supported for transparent datatypes".

### Before (fails)
```rust
// Adding this alone causes "private fields not supported for transparent datatypes"
#[verifier::external_type_specification]
pub struct ExArrayString<const CAP: usize>(ArrayString<CAP>);
```

### After (passes)
```rust
// Add both attributes: external_type_specification AND external_body
#[verifier::external_type_specification]
#[verifier::external_body]
pub struct ExArrayString<const CAP: usize>(ArrayString<CAP>);

// For generic types, also add reject_recursive_types on type params
#[verifier::external_type_specification]
#[verifier::external_body]
pub struct ExCapacityError<#[verifier::reject_recursive_types] T>(CapacityError<T>);
```

These structs must be placed inside the `verus! { }` block.

### Why it works
`#[verifier::external_type_specification]` tells Verus to accept the type in specs.
`#[verifier::external_body]` allows the struct definition to have private/opaque fields.
`#[verifier::reject_recursive_types]` on generic params is required for `external_body` datatypes
with type parameters to prevent recursive type issues.
