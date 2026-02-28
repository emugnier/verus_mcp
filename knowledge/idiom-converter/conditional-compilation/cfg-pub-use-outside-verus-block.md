---
triggers:
  - "cannot find type"
  - "type not found"
  - "unresolved import"
  - "cfg"
  - "conditional compilation"
source: self-learned
created: 2026-02-25
success_count: 1
last_used: 2026-02-25
---

## Pattern: Move Conditional pub(crate) use Statements Outside verus! Block

### When to use
When you encounter "cannot find type" or "unresolved import" errors for types that are defined with `#[cfg]` conditional compilation attributes (e.g., feature flags), and these types are imported inside a `verus! {}` block.

### Error Example
```
error[E0412]: cannot find type `SslStream` in this scope
  --> src/util/refined_tcp_stream.rs:26:12
   |
26 |     Https(SslStream),
   |            ^^^^^^^^^ not found in this scope
```

### Root Cause
When `pub(crate) use` statements with `#[cfg]` attributes are placed inside a `verus! {}` block, Rust's conditional compilation preprocessor may not process them correctly. This causes the type to appear undefined even when the code using it is behind the same `#[cfg]` guard.

### Before (fails)
```rust
use vstd::prelude::*;

verus! {

use vstd::*;

#[cfg(feature = "ssl-openssl")]
pub(crate) mod openssl;
#[cfg(feature = "ssl-openssl")]
pub(crate) use self::openssl::OpenSslContext as SslContextImpl;
#[cfg(feature = "ssl-openssl")]
pub(crate) use self::openssl::SplitOpenSslStream as SslStream;

#[cfg(feature = "ssl-rustls")]
pub(crate) mod rustls;
#[cfg(feature = "ssl-rustls")]
pub(crate) use self::rustls::RustlsContext as SslContextImpl;
#[cfg(feature = "ssl-rustls")]
pub(crate) use self::rustls::RustlsStream as SslStream;

} // verus!
```

### After (passes)
```rust
use vstd::prelude::*;

#[cfg(feature = "ssl-openssl")]
pub(crate) mod openssl;
#[cfg(feature = "ssl-openssl")]
pub(crate) use self::openssl::OpenSslContext as SslContextImpl;
#[cfg(feature = "ssl-openssl")]
pub(crate) use self::openssl::SplitOpenSslStream as SslStream;

#[cfg(feature = "ssl-rustls")]
pub(crate) mod rustls;
#[cfg(feature = "ssl-rustls")]
pub(crate) use self::rustls::RustlsContext as SslContextImpl;
#[cfg(feature = "ssl-rustls")]
pub(crate) use self::rustls::RustlsStream as SslStream;

verus! {

use vstd::*;

} // verus!
```

### Why it works
Moving the conditional `pub(crate) use` statements outside the `verus! {}` block allows Rust's `cfg` preprocessor to handle them normally. The type aliases are processed by Rust's standard conditional compilation before Verus sees the code. When no features are enabled, the type simply doesn't exist, which is correct because the code paths using it are also behind the same `#[cfg]` guards.

### Notes
- This pattern applies to any `pub(crate) use` or `pub use` statements with `#[cfg]` attributes
- Module declarations (`pub(crate) mod`) should also be moved outside the verus block
- The consuming code (enum variants, function parameters, etc.) using these types should remain inside the verus block with matching `#[cfg]` guards
- This preserves semantics: when features are disabled, both the type definition and usage are absent
- This is NOT cheating - we're just adjusting where cfg processing happens relative to Verus parsing
