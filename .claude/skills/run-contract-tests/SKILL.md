---
name: run-contract-tests
description: Validate requires/ensures specs at runtime using the check_contracts! macro from vstd. Wraps functions with check_contracts! {}, generates #[test] callers, runs cargo test, and validates spec strength. Use after adding or modifying specifications.
allowed-tools: Bash, Read, Write, Edit, Glob
---

# Run Contract Tests Skill

Validate `requires`/`ensures` specifications at runtime using the `check_contracts!`
macro from `vstd::contrib::exec_spec`. The macro wraps function bodies and generates
`check_<fn>()` wrappers that return `Result<T, ContractError>`.

Reference: `verus/source/vstd/contrib/exec_spec/README.md`

## Step 1 — Import `check_contracts!` from vstd

vstd is already a dependency. No extra Cargo feature needed. At the top of the file
being tested, add:

```rust
use vstd::contrib::exec_spec::check_contracts;
```

## Step 2 — Wrap the target function/impl block with `check_contracts! {}`

Move the function (or entire impl block) OUT of any existing `verus! {}` block and
into a **top-level** `check_contracts! {}` block. The macro wraps it in verus internally.

**Critical rules:**
- `check_contracts! {}` must be at the crate top level — **NOT inside `verus! {}`**
- Any `spec fn` referenced in `requires`/`ensures` must live **inside the same
  `check_contracts! {}` block** (they get compiled to `exec_*` versions at runtime)
- Types used with `old()` must derive `Clone`
- Methods generate `obj.check_method(args)`; free functions generate `check_fn(args)`

```rust
// ❌ WRONG — nested inside verus!
verus! { check_contracts! { fn foo() ensures ..., { } } }

// ✅ CORRECT — top level
check_contracts! {
    impl Block {
        spec fn value(self) -> usize { self.0 }  // spec fn referenced in ensures

        pub fn is_empty(self) -> (result: bool)
            ensures result == (self.value() == 0),
        {
            self.0 == 0
        }
    }
}
```

If the function uses `old()`, the struct must derive `Clone`:
```rust
check_contracts! {
    #[derive(Clone)]   // required for old(self) captures
    impl Counter {
        fn increment(&mut self)
            requires old(self).value < old(self).max,
            ensures  self.value == old(self).value + 1,
        { self.value += 1; }
    }
}
```

## Step 3 — Write `#[test]` functions calling the generated wrappers

Place inline as `#[cfg(test)] mod tests { ... }` or in `tests/contract_tests.rs`.
No feature gate needed — `check_contracts!` is always active.

**Postcondition test (happy path):**
```rust
#[test]
fn contract_<fn_name>_postcondition() {
    // Arrange valid state satisfying the precondition
    let obj = ...;
    // Call the check_ wrapper
    match obj.check_<fn_name>(<valid_arg>) {
        Ok(result) => {
            // Assert the postcondition holds
            assert!(<postcondition_expression>, "Postcondition violated: <spec text>");
        }
        Err(e) => panic!("Unexpected contract violation: {:?}", e),
    }
}
```

**Precondition test (boundary / invalid input):**
```rust
#[test]
fn contract_<fn_name>_precondition() {
    let mut obj = ...;
    match obj.check_<fn_name>(<invalid_arg>) {
        Ok(_) => panic!("Expected PreconditionViolated for <reason>"),
        Err(e) => assert!(
            matches!(e, ContractError::PreconditionViolated { .. }),
            "Expected PreconditionViolated, got {:?}", e
        ),
    }
}
```

**Value selection:**
- Boundary values: 0, max allowed index, `len - 1`, `len`, `len + 1`
- For `insert(bit)` with `requires bit < self.len()`: test `bit = 0`, `bit = len-1`
  (valid) and `bit = len`, `bit = len + 100` (invalid)

## Step 4 — Run the tests

```bash
cd <project_root> && cargo test 2>&1
```

No `--features` flag is needed.

## Step 5 — Spec-strength check

After tests pass, verify the spec is **not vacuously satisfied**.
A test that always passes regardless of the postcondition value indicates a weak spec.

**Method A — mutate the test input:**
1. Change the valid input to a boundary value adjacent to the spec boundary
2. Re-run `cargo test`; the `assert!` inside `Ok(_)` should now fail (or a
   different value should be returned)
3. If tests still pass after the mutation → the postcondition is not being exercised;
   strengthen the `ensures` clause

**Method B — negate one ensures clause (temporary):**
1. Temporarily change `ensures result == X` to `ensures result == X + 1` in the source
2. Re-run `cargo test`; expect `PostconditionViolated { condition: "result == X + 1" }`
3. If tests **still pass** → the `check_<fn>` wrapper is not being called or the
   ensures is not constraining enough; investigate and strengthen
4. Revert the negation

## Step 6 — Interpret failures

| Failure | Cause | Fix |
|---------|-------|-----|
| `PreconditionViolated` in happy-path test | `requires` too strict | Relax the clause |
| `PostconditionViolated` | `ensures` wrong or impl doesn't satisfy it | Fix spec or impl |
| Regular `assert!` failure | Expected postcondition expression is wrong | Fix the test assertion |
| Spec-strength mutation passes silently | `ensures` is too weak / not exercised | Strengthen the spec |

Report the failing test name, the error variant, and the condition string.

## Step 7 — Log the run

```bash
python3 scripts/verus-log.py event --type verus_run --data '{
  "phase": "contract_tests",
  "command": "cargo test",
  "result": "pass|fail",
  "failing_tests": [...],
  "spec_strength_confirmed": true,
  "project_root": "<project_root>"
}'
```
