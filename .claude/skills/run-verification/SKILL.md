---
name: run-verification
description: Run Verus verification and interpret results. Use to check syntax errors and verification status.
allowed-tools: mcp__verus-mcp
---

# Run Verification Skill

Run Verus verification on a file or project and interpret the results.

## MCP Tools Available

The `mcp__verus-mcp` server provides these tools:

### 1. `mcp__verus-mcp__get_syntax_errors` - Get syntax errors only
Use this to check for syntax/compile errors before verification:

```
mcp__verus-mcp__get_syntax_errors(repo_path: "path/to/project/", output_format: "Primary")
```

Parameters:
- `repo_path`: Path to the repository or project
- `output_format`: "Full", "Primary", or "SyntaxErrors" (optional)

Returns only syntax errors that prevent compilation.

### 2. `mcp__verus-mcp__verify_repository` - Run full Verus verification
Use this to run verification on a project:

```
mcp__verus-mcp__verify_repository(repo_path: "path/to/project/", output_format: "Primary")
```

Parameters:
- `repo_path`: Path to the repository to verify
- `output_format`: "Full", "Primary", or "SyntaxErrors" (optional, default: "Primary")

Returns verification results including all diagnostics.

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
- These block verification entirely

**2. "Not Supported" Errors (MUST FIX):**
- `"not supported"` - Rust feature Verus cannot handle
- `"unsupported"` - Language construct needs conversion
- These require idiom-converter or assume-spec-gen

**3. Verification Errors (EXPECTED - LOG BUT DON'T TREAT AS FAILURE):**
- Precondition violations
- Postcondition failures
- Assertion failures
- Arithmetic overflow checks

Verification errors are **normal** during the retrofit process. They indicate proofs that need strengthening, not code that won't compile. Log them for tracking but don't treat them as blocking errors.

## Output Format

When reporting results, include:

1. **Status**: SUCCESS (0 errors) or NEEDS_WORK
2. **Verified count**: Number of verified items
3. **Error count**: Number of verification errors (for logging)
4. **Syntax errors**: List any blocking syntax issues
5. **Unsupported features**: List "not supported" errors that need conversion
6. **Verification failures**: Log these but note they're expected during retrofit

## Example Output

```
Status: SUCCESS
Verified: 17
Errors: 0

No syntax errors.
No unsupported features.
No verification failures.
```

Or during retrofit:

```
Status: NEEDS_WORK
Verified: 12
Errors: 3

Syntax errors: 0
Unsupported features: 2
  - Line 45: iterator .fold() not supported
  - Line 89: closure not supported

Verification failures (expected, logged for tracking): 1
  - Line 67: postcondition might not hold
```

## Workflow

1. First call `mcp__verus-mcp__get_syntax_errors` to check for compile issues
2. If syntax is clean, call `mcp__verus-mcp__verify_repository` for full verification
3. Parse output and categorize errors
4. Return structured result distinguishing blocking vs expected errors
