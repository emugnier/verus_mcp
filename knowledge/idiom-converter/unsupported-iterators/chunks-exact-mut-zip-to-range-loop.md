---
triggers:
  - "ChunksExactMut"
  - "ForLoopGhostIteratorNew not satisfied"
  - "Zip"
  - "chunks_exact_mut"
  - "iter_mut().zip"
source: self-learned
created: 2026-02-26
success_count: 3
last_used: 2026-02-26
---

## Pattern: Convert ChunksExactMut and Zip Iterators to Range-Based Loops

### When to use
When a `for` loop uses `ChunksExactMut`, `Zip`, or other unsupported iterator combinators
and Verus reports "ForLoopGhostIteratorNew not satisfied".

Verus only supports these iterator types in for loops:
- `str::Chars<'_>`
- `Range<usize>`
- `slice::Iter<'_, T>`
- `vec::IntoIter<T>`

Complex combinators like `ChunksExactMut`, `ChunksExact`, `Zip`, etc. are NOT supported.

### Error Example
```
error[E0277]: the trait bound `&mut core::slice::ChunksExactMut<'_, u8>: vstd::pervasive::ForLoopGhostIteratorNew` is not satisfied
error[E0277]: the trait bound `Zip<IterMut<'_, W>, ChunksExact<'_, u8>>: ForLoopGhostIteratorNew` is not satisfied
```

### Case 1: ChunksExactMut

#### Before (fails)
```rust
let mut chunks = dst.chunks_exact_mut(size_of::<W>());
for chunk in &mut chunks {
    let val = next_word()?;
    chunk.copy_from_slice(val.to_le_bytes().as_ref());
}
let rem = chunks.into_remainder();
```

#### After (passes)
```rust
let chunk_size = size_of::<W>();
let num_full_chunks = dst.len() / chunk_size;
for i in 0..num_full_chunks {
    let start = i * chunk_size;
    let end = start + chunk_size;
    let chunk = &mut dst[start..end];
    let val = next_word()?;
    chunk.copy_from_slice(val.to_le_bytes().as_ref());
}
let chunks = dst.chunks_exact_mut(chunk_size);
let rem = chunks.into_remainder();
```

### Case 2: Zip Iterator

#### Before (fails)
```rust
let mut dst = [W::from_usize(0); N];
let chunks = src.chunks_exact(size_of::<W>());
for (out, chunk) in dst.iter_mut().zip(chunks) {
    let mut buf: W::Bytes = Default::default();
    buf.as_mut().copy_from_slice(chunk);
    *out = W::from_le_bytes(buf);
}
```

#### After (passes)
```rust
let mut dst = [W::from_usize(0); N];
let chunk_size = size_of::<W>();
for i in 0..N {
    let start = i * chunk_size;
    let end = start + chunk_size;
    let chunk = &src[start..end];
    let mut buf: W::Bytes = Default::default();
    buf.as_mut().copy_from_slice(chunk);
    dst[i] = W::from_le_bytes(buf);
}
```

### Why it works
Verus requires `for` loop iterators to implement `ForLoopGhostIteratorNew`. Only a small
set of basic iterator types implement this trait. Complex combinators must be replaced
with manual index-based loops using `Range<usize>` (e.g., `0..n`), which does implement
`ForLoopGhostIteratorNew`.

### Important Notes
- **Preserve the ChunksExactMut object** if `into_remainder()` is called after the loop
- **Use manual indexing and slicing** instead of the iterator
- **Keep chunk_size as a variable** to avoid repeated calculations
- **This conversion is semantically equivalent** — behavior and safety are preserved

### Related Patterns
- See `flat-map-enumerate-to-chars-loop.md` for other complex iterator conversions
- All complex iterator combinators require similar conversion to Range-based loops
