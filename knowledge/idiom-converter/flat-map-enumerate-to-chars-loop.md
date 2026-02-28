---
triggers:
  - "ForLoopGhostIteratorNew not satisfied"
  - "FlatMap"
  - "Enumerate"
  - "flat_map"
  - "enumerate"
  - "chain"
  - "for loop over iterator"
source: self-learned
created: 2026-02-24
success_count: 1
last_used: 2026-02-24
---

## Pattern: Convert flat_map/enumerate/chain to for-loop over Chars

### When to use
When a `for` loop uses complex iterator combinators like `flat_map`, `enumerate`, or `chain`
and Verus reports "ForLoopGhostIteratorNew not satisfied" for `FlatMap<Enumerate<Chars<'_>>>`.

**Important**: `#[verifier::external]` does NOT suppress this error — it appears during
Verus's type-checking phase, which runs even for external impls. The iterator type
must be replaced with one that implements `ForLoopGhostIteratorNew`.

### Before (fails — even with #[verifier::external])
```rust
#[verifier::external]
impl Display for BaseIban {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        // FlatMap<Enumerate<Chars<'_>>> does NOT implement ForLoopGhostIteratorNew
        for (i, c) in self.s.chars().enumerate().flat_map(|(i, c)| {
            (i != 0 && i % 4 == 0)
                .then_some(' ')
                .into_iter()
                .chain(core::iter::once(c))
        }) {
            // ...
        }
    }
}
```

### After (passes)
```rust
#[verifier::external]
impl Display for BaseIban {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        // Chars<'a> DOES implement ForLoopGhostIteratorNew
        let mut i: usize = 0;
        for c in self.s.chars() {
            if i != 0 && i % 4 == 0 {
                write!(f, " ")?;
            }
            write!(f, "{c}")?;
            i += 1;
        }
        Ok(())
    }
}
```

### Why it works
Verus injects `ForLoopGhostIteratorNew` as a type constraint during its modified rustc
type-checking pass. Only specific iterator types are supported:
- `core::str::Chars<'_>` ✓
- `core::ops::Range<usize>` ✓
- `core::slice::Iter<'_, T>` ✓
- `std::vec::IntoIter<T>` ✓

Complex combinators (`FlatMap`, `Enumerate`+`flat_map`, `Chain`) are NOT supported.
Replacing with a simple `for c in str.chars()` with a manual index counter satisfies
the type constraint.

### Iterator types known to implement ForLoopGhostIteratorNew
- `str::Chars<'_>` (from `.chars()`)
- `Range<usize>` (from `0..n`)
- `slice::Iter<'_, T>` (from `slice.iter()`)
- `vec::IntoIter<T>` (from `vec.into_iter()`)
