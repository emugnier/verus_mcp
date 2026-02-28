use vstd::prelude::*;

verus! {

use vstd::*;
use core::ops::{BitAnd, BitAndAssign, BitOr, BitOrAssign, BitXor, BitXorAssign, Not};

// Assume specifications for bitwise assignment operators on usize
pub assume_specification[<usize as core::ops::BitAndAssign>::bitand_assign](_0: &mut usize, _1: usize)
    ensures *_0 == *old(_0) & _1;

pub assume_specification[<usize as core::ops::BitOrAssign>::bitor_assign](_0: &mut usize, _1: usize)
    ensures *_0 == *old(_0) | _1;

pub assume_specification[<usize as core::ops::BitXorAssign>::bitxor_assign](_0: &mut usize, _1: usize)
    ensures *_0 == *old(_0) ^ _1;

#[derive(Copy, Clone, PartialEq, Debug)]
#[repr(transparent)]
// Divergence from original (pub(super) -> pub): needed so the Verus spec accessor
// `value()` can be a public open spec fn usable in ensures clauses of public functions.
pub struct Block(pub usize);

impl Block {
    /// Ghost accessor: exposes the underlying usize value for use in specifications.
    pub open spec fn value(self) -> usize {
        self.0
    }

    #[inline]
    pub fn is_empty(self) -> (result: bool)
        ensures result == (self.value() == 0),
    {
        // NONE is defined as Self::from_usize_array([0; Self::USIZE_COUNT])
        // For the default Block(usize) implementation, this is just 0
        self.0 == 0
    }

    #[inline]
    pub fn andnot(self, other: Self) -> (result: Self)
        ensures result.value() == !other.value() & self.value(),
    {
        Self(!other.0 & self.0)
    }
}

impl Not for Block {
    type Output = Block;
    #[inline]
    fn not(self) -> (result: Self::Output)
        ensures result.value() == !self.value(),
    {
        Self(self.0.not())
    }
}

impl BitAnd for Block {
    type Output = Block;
    #[inline]
    fn bitand(self, other: Self) -> (result: Self::Output)
        ensures result.value() == self.value() & other.value(),
    {
        Self(self.0.bitand(other.0))
    }
}

impl BitAndAssign for Block {
    #[inline]
    fn bitand_assign(&mut self, other: Self)
        ensures self.value() == old(self).value() & other.value(),
    {
        self.0.bitand_assign(other.0);
    }
}

impl BitOr for Block {
    type Output = Block;
    #[inline]
    fn bitor(self, other: Self) -> (result: Self::Output)
        ensures result.value() == self.value() | other.value(),
    {
        Self(self.0.bitor(other.0))
    }
}

impl BitOrAssign for Block {
    #[inline]
    fn bitor_assign(&mut self, other: Self)
        ensures self.value() == old(self).value() | other.value(),
    {
        self.0.bitor_assign(other.0)
    }
}

impl BitXor for Block {
    type Output = Block;
    #[inline]
    fn bitxor(self, other: Self) -> (result: Self::Output)
        ensures result.value() == self.value() ^ other.value(),
    {
        Self(self.0.bitxor(other.0))
    }
}

impl BitXorAssign for Block {
    #[inline]
    fn bitxor_assign(&mut self, other: Self)
        ensures self.value() == old(self).value() ^ other.value(),
    {
        self.0.bitxor_assign(other.0)
    }
}

} // verus!