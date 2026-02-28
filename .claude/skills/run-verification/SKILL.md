---
name: run-verification
description: Run Verus verification and interpret results. Use to check syntax errors and verification status.
allowed-tools: Bash
---

# Run Verification Skill

Run `cargo verus verify` and interpret the results.

## Command

```bash
cd <project_dir> && cargo verus verify 2>&1
```

If `cargo verus verify` is not available, stop and resolve the installation — do not fall back to MCP tools.

## Understanding Results

### Success Criteria

**Verus-Compatibility Success (primary goal during porting):**
No syntax errors and no "not supported" errors. The code is Verus-compatible even if verification failures (pre/post conditions) remain. Verification failures are expected and do not block progress.

**Full Verification Success (future goal, not required during porting):**
`verification results:: X verified, 0 errors` — requires proofs and postconditions, out of scope for the porting phase.

### Error Categories

**1. Syntax/Compile Errors (MUST FIX):**
- Missing imports, undefined types
- Invalid Rust syntax
- `error[E...]` — blocking

**2. "Not Supported" Errors (MUST FIX):**
- `error: not supported` — Rust feature Verus cannot handle
- `error: unsupported` — Language construct needs conversion
- These require idiom-converter or assume-spec-gen

**3. Verification Errors (EXPECTED — LOG BUT DON'T FIX):**
- Precondition violations
- Postcondition failures
- Assertion failures
- `error: possible arithmetic underflow/overflow`

Verification errors are **normal** during the retrofit process. Log them with the `log-event` skill but do not treat them as blocking.

## Output Format

When reporting results, include:

1. **Status**: SUCCESS (Verus-compatible) or NEEDS_WORK
2. **Syntax errors**: List any blocking compile issues
3. **Unsupported features**: List "not supported" errors that need conversion
4. **Verification failures**: Log these but note they are expected during retrofit

### Example — success

```
Status: SUCCESS
No syntax errors.
No unsupported features.
Verification failures (non-blocking): 4
  - possible arithmetic underflow/overflow (file.rs:112)
```

### Example — needs work

```
Status: NEEDS_WORK

Syntax errors: 0
Unsupported features: 2
  - Line 45: iterator .fold() not supported
  - Line 89: closure not supported

Verification failures (expected, not blocking): 1
  - Line 67: postcondition might not hold
```

## Workflow

1. Run `cargo verus verify 2>&1` in the project directory
2. Parse output and categorize each error
3. Return structured result distinguishing blocking vs expected errors
4. Log results via `log-event` skill
