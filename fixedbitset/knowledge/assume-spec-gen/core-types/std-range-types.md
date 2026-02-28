---
triggers:
  - "core::ops::range::RangeTo is not supported"
  - "core::ops::range::RangeFull is not supported"
  - "core::ops::range::RangeFrom is not supported"
  - "core::ops::range:: is not supported"
source: self-learned
created: 2026-02-26
success_count: 1
last_used: 2026-02-26
---

## Pattern: External Type Specifications for std Range Types

### When to use
When Verus reports that standard library range types (`RangeTo`, `RangeFull`, `RangeFrom`) are not supported. Note that `Range<T>` is already supported by vstd, but the other range variants are not.

### Error Example
```
error: `core::ops::range::RangeTo` is not supported (note: you may be able to add a Verus specification to this type with the `external_type_specification` attribute)
error: `core::ops::range::RangeFull` is not supported
error: `core::ops::range::RangeFrom` is not supported
```

### Before (fails)
```rust
verus! {

use vstd::*;
use core::ops::{Range, RangeFrom, RangeFull, RangeTo};

// Using these types directly fails
pub trait IndexRange<T = usize> {
    fn start(&self) -> Option<T> { None }
    fn end(&self) -> Option<T> { None }
}

impl<T> IndexRange<T> for RangeFull {}
impl<T: Copy> IndexRange<T> for RangeFrom<T> { /* ... */ }
impl<T: Copy> IndexRange<T> for RangeTo<T> { /* ... */ }

} // verus!
```

### After (passes)
```rust
verus! {

use vstd::*;
use core::ops::{Range, RangeFrom, RangeFull, RangeTo};

// Add external type specifications at the top of verus! block
#[verifier::reject_recursive_types(Idx)]
#[verifier::external_type_specification]
pub struct ExRangeTo<Idx>(core::ops::RangeTo<Idx>);

#[verifier::external_type_specification]
pub struct ExRangeFull(core::ops::RangeFull);

#[verifier::reject_recursive_types(Idx)]
#[verifier::external_type_specification]
pub struct ExRangeFrom<Idx>(core::ops::RangeFrom<Idx>);

// Now the types can be used in trait implementations
pub trait IndexRange<T = usize> {
    fn start(&self) -> Option<T> { None }
    fn end(&self) -> Option<T> { None }
}

impl<T> IndexRange<T> for RangeFull {}
impl<T: Copy> IndexRange<T> for RangeFrom<T> { /* ... */ }
impl<T: Copy> IndexRange<T> for RangeTo<T> { /* ... */ }

} // verus!
```

### Why it works
- `#[verifier::external_type_specification]` tells Verus to accept these std types in specifications
- For generic types (`RangeTo<Idx>`, `RangeFrom<Idx>`), the `#[verifier::reject_recursive_types(Idx)]` attribute is required to prevent recursive type issues
- `RangeFull` has no generics, so only needs `external_type_specification`
- These are SPECIFY-style specs (see assume-spec-gen agent docs), not WRAP-style, because the types have no view function and are used directly

### Notes
- `Range<T>` is already supported by vstd and does NOT need an external type specification
- The suggested specs from Verus error messages include the exact syntax needed
- The structs will generate "dead_code" warnings from cargo, which is expected and harmless
- No `external_body` is needed for these types (unlike ArrayString/CapacityError with private fields)
