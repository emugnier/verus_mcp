---
triggers:
  - "transmute conversion ensures spec into_usize_array from_usize_array"
  - "inverse function spec array transmute ghost model"
  - "seq! ensures result@ spec for array return"
source: self-learned
created: 2026-02-27
success_count: 1
last_used: 2026-02-27
---

## Pattern: Specifying transmute-based into/from array conversions with seq! and ghost accessor

### When to use
When a struct wraps a primitive (e.g. `Block(usize)`) and has `into_array` / `from_array`
conversion functions implemented via `unsafe { core::mem::transmute(...) }`.
The transmute assume_specification provides no postcondition, so you must express the
contract using the struct's ghost accessor spec fn (e.g. `value()`) and Verus `seq!`.

### Before (fails — no spec)
```rust
pub fn into_usize_array(self) -> [usize; Self::USIZE_COUNT] {
    unsafe { core::mem::transmute(self.0) }
}

pub const fn from_usize_array(array: [usize; Self::USIZE_COUNT]) -> Self {
    Self(unsafe { core::mem::transmute(array) })
}
```

### After (passes contract tests)
```rust
pub fn into_usize_array(self) -> (result: [usize; Self::USIZE_COUNT])
    ensures result@ == seq![self.value()],
{
    unsafe { core::mem::transmute(self.0) }
}

pub const fn from_usize_array(array: [usize; Self::USIZE_COUNT]) -> (result: Self)
    ensures result.value() == array@[0],
{
    Self(unsafe { core::mem::transmute(array) })
}
```

### Runtime contract test (direct assertions)
```rust
#[cfg(test)]
mod contract_tests {
    use super::Block;

    #[test]
    fn contract_into_usize_array_postcondition() {
        let b = Block(42usize);
        let arr = b.into_usize_array();
        assert_eq!(arr[0], b.0, "result[0] == block's underlying value");
    }

    #[test]
    fn contract_from_usize_array_postcondition() {
        let arr = [42usize; Block::USIZE_COUNT];
        let b = Block::from_usize_array(arr);
        assert_eq!(b.0, arr[0], "result.0 == array[0]");
    }

    #[test]
    fn contract_round_trip() {
        let original = Block(0xDEAD_BEEFusize);
        assert_eq!(original, Block::from_usize_array(original.into_usize_array()));
    }
}
```

### Why it works
- `self.value()` is a `pub open spec fn` that exposes the inner field.
- `seq![self.value()]` creates a 1-element `Seq<usize>` matching the array's `@` view.
- `array@[0]` accesses the sequence view of the input array at index 0.
- Verus can't statically verify these (transmute has no ensures), but runtime contract
  tests pass because at execution time `USIZE_COUNT == 1` and the transmute is identity.

### Notes
- Use `check_contracts!{}` only if the ghost accessor spec fn (`value()`) can be
  co-located in the same macro block. If it's defined in a separate file, use direct
  assertion tests instead.
- The `requires true` pattern is appropriate for hash functions and transmute
  assume_specifications where no meaningful postcondition can be expressed in Verus.
- For the spec-status detection script: multi-line `assume_specification` blocks
  (ensures on the next line from the signature) require `endswith(";")` detection,
  not `";" in line`, because type params like `[T; N]` contain semicolons.
