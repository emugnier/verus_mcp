use vstd::prelude::*;

verus! {

use vstd::*;
use core::ops::{Range, RangeFrom, RangeFull, RangeTo};

// External type specifications for range types not in vstd
#[verifier::reject_recursive_types(Idx)]
#[verifier::external_type_specification]
pub struct ExRangeTo<Idx>(core::ops::RangeTo<Idx>);

#[verifier::external_type_specification]
pub struct ExRangeFull(core::ops::RangeFull);

#[verifier::reject_recursive_types(Idx)]
#[verifier::external_type_specification]
pub struct ExRangeFrom<Idx>(core::ops::RangeFrom<Idx>);

// Taken from https://github.com/bluss/odds/blob/master/src/range.rs.

/// **IndexRange** is implemented by Rust's built-in range types, produced
/// by range syntax like `..`, `a..`, `..b` or `c..d`.
pub trait IndexRange<T = usize> {
    #[inline]
    /// Start index (inclusive). Default returns None (no lower bound).
    // No ensures on the default: concrete impls may override and return Some.
    fn start(&self) -> Option<T> {
        None
    }
    #[inline]
    /// End index (exclusive). Default returns None (no upper bound).
    // No ensures on the default: concrete impls may override and return Some.
    fn end(&self) -> Option<T> {
        None
    }
}

impl<T> IndexRange<T> for RangeFull {}

impl<T: Copy> IndexRange<T> for RangeFrom<T> {
    #[inline]
    fn start(&self) -> (result: Option<T>)
        ensures result == Some(self.start),
    {
        Some(self.start)
    }
}

impl<T: Copy> IndexRange<T> for RangeTo<T> {
    #[inline]
    fn end(&self) -> (result: Option<T>)
        ensures result == Some(self.end),
    {
        Some(self.end)
    }
}

impl<T: Copy> IndexRange<T> for Range<T> {
    #[inline]
    fn start(&self) -> (result: Option<T>)
        ensures result == Some(self.start),
    {
        Some(self.start)
    }
    #[inline]
    fn end(&self) -> (result: Option<T>)
        ensures result == Some(self.end),
    {
        Some(self.end)
    }
}

} // verus!
