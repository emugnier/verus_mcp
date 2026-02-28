#!/usr/bin/env python3
"""Specification coverage tracker for Verus-wrapped Rust code.

Reports which functions (including external_body and assume_specification blocks)
have requires/ensures specifications and which still need them.

Cross-references veracity-review-module-fn-impls (per-function NoSpec/SpecStr)
with veracity-review-proof-state (aggregate fns_without_spec_count) and greps
assume_specification blocks directly.

Usage:
  # Report spec coverage for a directory
  python3 scripts/verus-spec-status.py --dir fixedbitset/src

  # Report spec coverage for a single file
  python3 scripts/verus-spec-status.py --file fixedbitset/src/lib.rs

  # Save results to JSON
  python3 scripts/verus-spec-status.py --dir fixedbitset/src --save

Requires:
  veracity-review-module-fn-impls  (cargo install --git https://github.com/briangmilnes/veracity)
  veracity-review-proof-state      (same)
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone


VERACITY_FN_BIN = "veracity-review-module-fn-impls"
VERACITY_PROOF_BIN = "veracity-review-proof-state"
ANALYSES_JSON = "analyses/veracity-review-module-fn-impls.json"
ANALYSES_MD = "analyses/veracity-review-module-fn-impls.md"
STATUS_FILE = "spec-status.json"


# ── Helpers ────────────────────────────────────────────────────────────────────

def find_project_root(path):
    """Walk up from path to find the directory containing Cargo.toml."""
    abs_path = os.path.abspath(path)
    current = abs_path if os.path.isdir(abs_path) else os.path.dirname(abs_path)
    while True:
        if os.path.exists(os.path.join(current, "Cargo.toml")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


def run_cmd(cmd, cwd, timeout=120):
    """Run a command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return -1, "", f"ERROR: '{cmd[0]}' not found"
    except subprocess.TimeoutExpired:
        return -2, "", f"ERROR: '{cmd[0]}' timed out"


# ── Veracity: module-fn-impls ──────────────────────────────────────────────────

def run_fn_impls(project_root, target_flag, target_path):
    """Run veracity-review-module-fn-impls and return True if analyses files exist."""
    rc, stdout, stderr = run_cmd(
        [VERACITY_FN_BIN, "-l", "Verus", target_flag, target_path],
        cwd=project_root,
    )
    if rc == -1:
        print(
            f"ERROR: '{VERACITY_FN_BIN}' not found.\n"
            "Install with: cargo install --git https://github.com/briangmilnes/veracity",
            file=sys.stderr,
        )
        sys.exit(1)
    return os.path.exists(os.path.join(project_root, ANALYSES_MD))


def parse_fn_detail_table(md_content):
    """Parse per-function detail table from veracity markdown.

    The detail table header contains: Function, V!, -V!, NoSpec, SpecStr, Lines
    Returns a list of dicts:
      {name, in_verus, is_hole, no_spec, spec_str, lines}
    """
    lines = md_content.split("\n")
    functions = []

    for i, line in enumerate(lines):
        if (
            "Function" in line
            and "V!" in line
            and "-V!" in line
            and "NoSpec" in line
            and "SpecStr" in line
        ):
            headers = [h.strip() for h in line.split("|")]

            def col(name):
                try:
                    return headers.index(name)
                except ValueError:
                    return -1

            col_fn = col("Function")
            col_v = col("V!")
            col_nv = col("-V!")
            col_nospec = col("NoSpec")
            col_spec = col("SpecStr")
            col_lines = col("Lines")

            for row in lines[i + 2 :]:
                if not row.startswith("|"):
                    break
                cells = [c.strip() for c in row.split("|")]

                raw_name = (
                    cells[col_fn].strip("`").split("`")[0].strip()
                    if col_fn >= 0 and col_fn < len(cells)
                    else ""
                )
                in_verus = col_v >= 0 and col_v < len(cells) and cells[col_v] == "Y"
                is_hole = col_spec >= 0 and col_spec < len(cells) and cells[col_spec] == "hole"
                no_spec = col_nospec >= 0 and col_nospec < len(cells) and cells[col_nospec] == "Y"
                spec_str = (
                    cells[col_spec].strip()
                    if col_spec >= 0 and col_spec < len(cells)
                    else ""
                )
                fn_lines = (
                    cells[col_lines].strip().replace("&#8209;", "-")
                    if col_lines >= 0 and col_lines < len(cells)
                    else ""
                )

                if raw_name:
                    functions.append(
                        {
                            "name": raw_name,
                            "in_verus": in_verus,
                            "is_hole": is_hole,
                            "no_spec": no_spec,
                            "spec_str": spec_str,
                            "lines": fn_lines,
                        }
                    )
            break  # Only one detail table per run

    return functions


# ── Veracity: proof-state ──────────────────────────────────────────────────────

def run_proof_state(project_root, target_flag, target_path):
    """Run veracity-review-proof-state and return fns_without_spec_count (or None)."""
    rc, stdout, stderr = run_cmd(
        [VERACITY_PROOF_BIN, target_flag, target_path],
        cwd=project_root,
    )
    if rc == -1:
        return None  # Not installed; not fatal

    # Parse fns_without_spec_count from output
    match = re.search(r"fns_without_spec[_\s]*count[:\s]+(\d+)", stdout + stderr)
    if match:
        return int(match.group(1))
    # Fall back: count "without spec" lines
    count = len(re.findall(r"without.*spec|no.*requires.*ensures", stdout + stderr, re.IGNORECASE))
    return count if count else None


# ── assume_specification grep ──────────────────────────────────────────────────

def find_assume_spec_blocks(file_path):
    """Find assume_specification blocks and check whether they have requires/ensures.

    Returns list of dicts: {name, line, has_spec}
    """
    results = []
    try:
        with open(file_path, "r") as f:
            source_lines = f.readlines()
    except OSError:
        return results

    i = 0
    while i < len(source_lines):
        raw = source_lines[i]
        stripped = raw.strip()
        if "assume_specification" in stripped and not stripped.startswith("//"):
            line_no = i + 1
            # Extract external function name from assume_specification[...] or assume_specification<...>[...]
            fn_match = re.search(
                r"assume_specification(?:<[^>]*>)?\s*\[([^\]]+)\]", stripped
            )
            fn_name = fn_match.group(1).strip() if fn_match else stripped[:60].strip()

            # Scan ahead for the closing brace of this block (or semicolon for one-liners)
            block_text = stripped
            depth = stripped.count("{") - stripped.count("}")
            j = i + 1
            # If depth==0 and line doesn't end with ";", scan forward to the
            # semicolon terminator (handles multi-line assume_specification blocks
            # with ensures/requires on subsequent lines before the closing ";")
            if depth == 0 and not stripped.endswith(";"):
                while j < len(source_lines) and j - i <= 50:
                    next_line = source_lines[j]
                    block_text += next_line
                    depth += next_line.count("{") - next_line.count("}")
                    j += 1
                    if next_line.strip().endswith(";") and depth == 0:
                        break
            while j < len(source_lines) and depth > 0:
                next_line = source_lines[j]
                block_text += next_line
                depth += next_line.count("{") - next_line.count("}")
                j += 1
                if j - i > 50:  # Safety limit
                    break

            has_spec = bool(
                re.search(r"\brequires\b|\bensures\b", block_text)
            )
            results.append({"name": fn_name, "line": line_no, "has_spec": has_spec})
        i += 1

    return results


# ── Per-file processing ────────────────────────────────────────────────────────

def process_file(file_path):
    """Process a single Rust file; return spec coverage data dict or None."""
    abs_file = os.path.abspath(file_path)
    if not os.path.exists(abs_file):
        print(f"ERROR: File not found: {file_path}", file=sys.stderr)
        return None

    project_root = find_project_root(abs_file)
    if not project_root:
        print(f"ERROR: No Cargo.toml found above {file_path}", file=sys.stderr)
        return None

    rel_file = os.path.relpath(abs_file, project_root)

    # 1. Run veracity-review-module-fn-impls
    ok = run_fn_impls(project_root, "-f", rel_file)
    if not ok:
        print(f"WARNING: veracity did not produce analyses for {rel_file}", file=sys.stderr)

    # 2. Parse markdown table
    md_path = os.path.join(project_root, ANALYSES_MD)
    functions = []
    if os.path.exists(md_path):
        with open(md_path, "r") as f:
            functions = parse_fn_detail_table(f.read())

    # 3. Cross-check with veracity-review-proof-state
    proof_without_spec = run_proof_state(project_root, "-f", rel_file)

    # 4. Detect assume_specification blocks
    assume_specs = find_assume_spec_blocks(abs_file)

    return {
        "file": rel_file,
        "abs_file": abs_file,
        "project_root": project_root,
        "functions": functions,
        "assume_specs": assume_specs,
        "proof_state_fns_without_spec": proof_without_spec,
    }


def compute_coverage(data):
    """Return (total, specified, remaining) counts for a processed file."""
    total = specified = 0
    for fn in data["functions"]:
        if not fn["in_verus"]:
            continue  # Skip unprocessed (outside verus!)
        total += 1
        if not fn["no_spec"]:
            specified += 1
    for assume in data["assume_specs"]:
        total += 1
        if assume["has_spec"]:
            specified += 1
    remaining = total - specified
    return total, specified, remaining


# ── Reporting ──────────────────────────────────────────────────────────────────

def print_file_report(data):
    """Print spec coverage table for one file. Returns (total, specified, remaining)."""
    print(f"\nFILE: {data['file']}")

    for fn in data["functions"]:
        if not fn["in_verus"]:
            continue  # Skip unprocessed functions

        status = "UNSPECIFIED" if fn["no_spec"] else "SPECIFIED  "
        sym = "[H]" if fn["is_hole"] else "[V]"
        kind = " (external_body)" if fn["is_hole"] else ""
        spec_note = f"  spec_strength={fn['spec_str']!r}" if fn["spec_str"] else ""
        print(
            f"  {sym} {fn['name']:<45} line {fn['lines']:<12} {status}{spec_note}{kind}"
        )

    for assume in data["assume_specs"]:
        status = "SPECIFIED  " if assume["has_spec"] else "UNSPECIFIED"
        print(
            f"  [A] {assume['name']:<49} line {assume['line']:<12} {status}  (assume_specification)"
        )

    total, specified, remaining = compute_coverage(data)

    # Cross-check with proof-state
    proof_count = data.get("proof_state_fns_without_spec")
    cross_check = ""
    if proof_count is not None:
        cross_check = f"  [proof-state cross-check: {proof_count} fns without spec]"

    print(
        f"  => total={total}  specified={specified}  remaining={remaining}{cross_check}"
    )
    return total, specified, remaining


# ── Commands ───────────────────────────────────────────────────────────────────

def cmd_status(args):
    if args.file:
        rs_files = [args.file]
        label = args.file
    else:
        abs_dir = os.path.abspath(args.dir)
        rs_files = []
        for root, dirs, files in os.walk(abs_dir):
            dirs.sort()
            for fname in sorted(files):
                if fname.endswith(".rs"):
                    rs_files.append(os.path.join(root, fname))
        label = args.dir

    if not rs_files:
        print(f"No .rs files found in {label}", file=sys.stderr)
        sys.exit(1)

    print(f"SPEC COVERAGE  (target: {label})")
    print("=" * 70)
    print("Legend: [V]=verus-wrapped  [H]=external_body/hole  [A]=assume_specification")

    grand_total = grand_specified = grand_remaining = 0
    file_results = []
    project_root = None

    for rs_file in rs_files:
        data = process_file(rs_file)
        if data is None:
            continue
        project_root = project_root or data["project_root"]
        total, specified, remaining = print_file_report(data)
        grand_total += total
        grand_specified += specified
        grand_remaining += remaining
        file_results.append(
            {
                "file": data["file"],
                "total": total,
                "specified": specified,
                "remaining": remaining,
                "functions": [
                    {
                        "name": fn["name"],
                        "lines": fn["lines"],
                        "in_verus": fn["in_verus"],
                        "is_hole": fn["is_hole"],
                        "no_spec": fn["no_spec"],
                        "spec_str": fn["spec_str"],
                    }
                    for fn in data["functions"]
                    if fn["in_verus"]
                ],
                "assume_specs": data["assume_specs"],
            }
        )

    print()
    print("-" * 70)
    print(
        f"TOTAL: {grand_total}  |  Specified: {grand_specified}  |  Remaining: {grand_remaining}"
    )

    if args.save and project_root:
        status_doc = {
            "target": label,
            "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "summary": {
                "total": grand_total,
                "specified": grand_specified,
                "remaining": grand_remaining,
            },
            "files": file_results,
        }
        status_path = os.path.join(project_root, STATUS_FILE)
        with open(status_path, "w") as f:
            json.dump(status_doc, f, indent=2)
        print(f"\nStatus saved to: {status_path}")


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Spec coverage tracker for Verus-wrapped Rust functions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dir", help="Directory to scan (all .rs files)")
    group.add_argument("--file", help="Single Rust file to scan")
    parser.add_argument(
        "--save",
        action="store_true",
        help=f"Save results to <project-root>/{STATUS_FILE}",
    )

    args = parser.parse_args()
    cmd_status(args)


if __name__ == "__main__":
    main()
