// TODO: Remove once MSRV supports undocumented_unsafe_blocks
#![allow(unknown_lints)]
#![allow(clippy::undocumented_unsafe_blocks)]
#![allow(dead_code)]
// TODO: Remove once the transmutes are fixed
#![allow(clippy::missing_transmute_annotations)]
// TODO: Remove once MSRV supports derived_hash_with_manual_eq
#![allow(renamed_and_removed_lints)]
#![allow(clippy::derive_hash_xor_eq)]
#![allow(clippy::derived_hash_with_manual_eq)]

use vstd::prelude::*;

// Conditional compilation stays outside verus! block
#[cfg(all(
    not(all(target_family = "wasm", target_feature = "simd128")),
    not(target_feature = "sse2"),
    not(target_feature = "avx"),
    not(target_feature = "avx2"),
))]
mod default;
#[cfg(all(
    not(all(target_family = "wasm", target_feature = "simd128")),
    not(target_feature = "sse2"),
    not(target_feature = "avx"),
    not(target_feature = "avx2"),
))]
pub use self::default::*;

#[cfg(all(
    any(target_arch = "x86", target_arch = "x86_64"),
    target_feature = "sse2",
    not(target_feature = "avx"),
    not(target_feature = "avx2"),
))]
mod sse2;
#[cfg(all(
    any(target_arch = "x86", target_arch = "x86_64"),
    target_feature = "sse2",
    not(target_feature = "avx"),
    not(target_feature = "avx2"),
))]
pub use self::sse2::*;

#[cfg(all(
    any(target_arch = "x86", target_arch = "x86_64"),
    target_feature = "avx",
    not(target_feature = "avx2")
))]
mod avx;
#[cfg(all(
    any(target_arch = "x86", target_arch = "x86_64"),
    target_feature = "avx",
    not(target_feature = "avx2")
))]
pub use self::avx::*;

#[cfg(all(
    any(target_arch = "x86", target_arch = "x86_64"),
    target_feature = "avx2"
))]
mod avx2;
#[cfg(all(
    any(target_arch = "x86", target_arch = "x86_64"),
    target_feature = "avx2"
))]
pub use self::avx2::*;

#[cfg(all(target_family = "wasm", target_feature = "simd128"))]
mod wasm;
#[cfg(all(target_family = "wasm", target_feature = "simd128"))]
pub use self::wasm::*;

verus! {

use vstd::*;
use core::cmp::Ordering;
use core::hash::{Hash, Hasher};

// Assume specifications for external library calls
pub assume_specification<T, const N: usize> [<[T; N] as core::cmp::Ord>::cmp] (_0: &[T; N], _1: &[T; N]) -> core::cmp::Ordering where T: core::cmp::Ord
    ensures result == core::cmp::Ordering::Equal <==> *_0 == *_1;

pub assume_specification<H> [<usize as core::hash::Hash>::hash_slice] (_0: &[usize], _1: &mut H) where H: core::hash::Hasher
    // Hashes all elements of the slice into the hasher; no formal postcondition on hasher state.
    requires true;

pub assume_specification<Src, Dst> [core::intrinsics::transmute] (_0: Src) -> Dst
    // Reinterprets bytes of Src as Dst; safety requires size_of::<Src>() == size_of::<Dst>()
    // which Rust enforces at compile time. No Verus-expressible postcondition without bit-level specs.
    requires true;

impl Block {
    #[verifier::external_body]
    pub const USIZE_COUNT: usize = core::mem::size_of::<Self>() / core::mem::size_of::<usize>();
    #[verifier::external_body]
    pub const NONE: Self = Self::from_usize_array([0; Self::USIZE_COUNT]);
    #[verifier::external_body]
    pub const ALL: Self = Self::from_usize_array([usize::MAX; Self::USIZE_COUNT]);
    #[verifier::external_body]
    pub const BITS: usize = core::mem::size_of::<Self>() * 8;

    #[inline]
    pub fn into_usize_array(self) -> (result: [usize; Self::USIZE_COUNT])
        ensures result@ == seq![self.value()],
    {
        unsafe { core::mem::transmute(self.0) }
    }

    #[inline]
    pub const fn from_usize_array(array: [usize; Self::USIZE_COUNT]) -> (result: Self)
        ensures result.value() == array@[0],
    {
        Self(unsafe { core::mem::transmute(array) })
    }
}

impl Eq for Block {}

impl PartialOrd for Block {
    #[inline]
    fn partial_cmp(&self, other: &Self) -> (result: Option<Ordering>)
        ensures result is Some,
    {
        Some(self.cmp(other))
    }
}

impl Ord for Block {
    #[inline]
    fn cmp(&self, other: &Self) -> (result: Ordering)
        ensures result == Ordering::Equal <==> *self == *other,
    {
        self.into_usize_array().cmp(&other.into_usize_array())
    }
}

impl Default for Block {
    #[inline]
    fn default() -> (result: Self)
        ensures result == Self::NONE,
    {
        Self::NONE
    }
}

impl Hash for Block {
    #[inline]
    fn hash<H: Hasher>(&self, hasher: &mut H)
        // Hash functions update opaque hasher state; no meaningful postcondition possible.
        requires true,
    {
        Hash::hash_slice(&self.into_usize_array(), hasher);
    }
}

} // verus!

// Contract tests validating requires/ensures specs at runtime.
// Uses direct assertions rather than check_contracts!{} because the value() spec fn
// is defined in default.rs and cannot be co-located in a check_contracts!{} block.
#[cfg(test)]
mod contract_tests {
    use super::Block;

    /// Validates: ensures result@ == seq![self.value()]
    /// Runtime translation: result[0] == self.0  (USIZE_COUNT == 1 for default Block)
    #[test]
    fn contract_into_usize_array_postcondition() {
        let b = Block(42usize);
        let arr = b.into_usize_array();
        assert_eq!(
            arr[0], b.0,
            "into_usize_array: result[0] should equal block's underlying value"
        );
    }

    /// Spec-strength: verify the spec captures the actual value, not just some fixed result.
    #[test]
    fn contract_into_usize_array_strength() {
        let b0 = Block(0usize);
        assert_eq!(b0.into_usize_array()[0], 0);

        let b_max = Block(usize::MAX);
        assert_eq!(b_max.into_usize_array()[0], usize::MAX);

        let b_mid = Block(12345usize);
        assert_eq!(b_mid.into_usize_array()[0], 12345);
    }

    /// Validates: ensures result.value() == array@[0]
    /// Runtime translation: result.0 == array[0]
    #[test]
    fn contract_from_usize_array_postcondition() {
        let arr = [42usize; Block::USIZE_COUNT];
        let b = Block::from_usize_array(arr);
        assert_eq!(
            b.0, arr[0],
            "from_usize_array: result.0 should equal array[0]"
        );
    }

    /// Spec-strength: different input values produce different outputs.
    #[test]
    fn contract_from_usize_array_strength() {
        let b0 = Block::from_usize_array([0usize; Block::USIZE_COUNT]);
        assert_eq!(b0.0, 0);

        let b_max = Block::from_usize_array([usize::MAX; Block::USIZE_COUNT]);
        assert_eq!(b_max.0, usize::MAX);
    }

    /// Round-trip: into_usize_array and from_usize_array are inverses.
    #[test]
    fn contract_round_trip() {
        let original = Block(0xDEAD_BEEFusize);
        let arr = original.into_usize_array();
        let recovered = Block::from_usize_array(arr);
        assert_eq!(original, recovered, "into/from round-trip should be identity");
    }
}