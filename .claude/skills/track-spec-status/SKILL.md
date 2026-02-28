---
name: track-spec-status
description: Report specification coverage for every verus-wrapped, external_body, and assume_specification function in a directory. Use to know which functions still need requires/ensures.
allowed-tools: Bash
---

# Track Spec Status Skill

Report which functions in a Verus-wrapped crate already have `requires`/`ensures`
specifications and which still need them. Covers:

- `[V]` — verus-wrapped functions (inside `verus! {}`)
- `[H]` — hole functions (`#[verifier::external_body]`, `assume`, or `admit` inside `verus! {}`)
- `[A]` — `assume_specification` blocks (for any external library)

Internally, the skill uses `verus-spec-status.py` which cross-references:
1. `veracity-review-module-fn-impls` — per-function `NoSpec`/`SpecStr` columns
2. `veracity-review-proof-state` — aggregate `fns_without_spec_count` cross-check
3. Direct source grep — detects `assume_specification` blocks and checks for specs

## Command

```bash
# Scan a directory
python3 scripts/verus-spec-status.py --dir <target_dir>

# Scan a single file
python3 scripts/verus-spec-status.py --file <target_file>

# Save results to spec-status.json in the project root
python3 scripts/verus-spec-status.py --dir <target_dir> --save
```

## Example Output

```
SPEC COVERAGE  (target: fixedbitset/src)
======================================================================
Legend: [V]=verus-wrapped  [H]=external_body/hole  [A]=assume_specification

FILE: src/block/default.rs
  [V] is_empty                                  line 22-25      UNSPECIFIED
  [H] andnot                                    line 28-31      UNSPECIFIED  (external_body)
  [A] <usize as BitAndAssign>::bitand_assign     line 70         UNSPECIFIED  (assume_specification)
  [A] <usize as BitOrAssign>::bitor_assign       line 72         SPECIFIED    (assume_specification)
  => total=4  specified=1  remaining=3

FILE: src/lib.rs
  [V] contains                                  line 142-148    UNSPECIFIED
  [V] insert                                    line 156-162    UNSPECIFIED
  [V] len                                       line 110-112    SPECIFIED     spec_strength='unknown'
  => total=3  specified=1  remaining=2

----------------------------------------------------------------------
TOTAL: 7  |  Specified: 2  |  Remaining: 5
```

## Interpretation

| Symbol | Meaning | Needs spec? |
|--------|---------|-------------|
| `[V] UNSPECIFIED` | Inside `verus!`, no requires/ensures | YES |
| `[V] SPECIFIED` | Inside `verus!`, has requires/ensures | No (may need strengthening) |
| `[H] UNSPECIFIED` | external_body/hole, no requires/ensures | YES — add to fn signature |
| `[H] SPECIFIED` | external_body/hole, has requires/ensures | No |
| `[A] UNSPECIFIED` | assume_specification, no requires/ensures | YES — add inside block |
| `[A] SPECIFIED` | assume_specification, has requires/ensures | No |

Functions with `[ ]` status (outside `verus!`) are excluded — they belong to the
porting workflow, not the spec-writing workflow.

## Notes

- `external_body` functions need `requires`/`ensures` on their signature; Verus
  treats these as trusted axioms and uses them in callee verification.
- `assume_specification` blocks for any external library also need
  `requires`/`ensures` to be useful downstream.
- Re-run this skill after adding specs to track progress.
- Use `--save` to persist results for session logging.

## Logging

After running, log the result:

```bash
python3 scripts/verus-log.py event --type verus_run --data '{
  "phase": "spec_tracking",
  "total": <N>,
  "specified": <M>,
  "remaining": <K>,
  "target_dir": "<target_dir>"
}'
```
