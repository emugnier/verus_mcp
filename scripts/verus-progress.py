#!/usr/bin/env python3
"""Progress tracker for Verus porting using veracity.

Wraps veracity-review-module-fn-impls to report how many functions have been
wrapped in verus! blocks, marked external, or are still unprocessed.

Usage:
  # Show aggregate progress metrics for a file
  python3 scripts/verus-progress.py scan --file tiny-http/src/client.rs

  # Show aggregate progress for a directory
  python3 scripts/verus-progress.py scan --dir tiny-http/src/

  # Show per-function status table and save to porting-status.json
  python3 scripts/verus-progress.py list --file tiny-http/src/client.rs [--save]

Requires: veracity-review-module-fn-impls (cargo install --git https://github.com/briangmilnes/veracity)
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone


VERACITY_BIN = "veracity-review-module-fn-impls"
ANALYSES_JSON = "analyses/veracity-review-module-fn-impls.json"
ANALYSES_MD = "analyses/veracity-review-module-fn-impls.md"
STATUS_FILE = "porting-status.json"


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


def run_veracity(project_root, rel_file):
    """Run veracity on a file relative to project_root. Returns True on success."""
    try:
        result = subprocess.run(
            [VERACITY_BIN, "-l", "Verus", "-f", rel_file],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.returncode == 0 or os.path.exists(
            os.path.join(project_root, ANALYSES_JSON)
        )
    except FileNotFoundError:
        print(
            f"ERROR: '{VERACITY_BIN}' not found. Install with:\n"
            "  cargo install --git https://github.com/briangmilnes/veracity",
            file=sys.stderr,
        )
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print(f"ERROR: veracity timed out on {rel_file}", file=sys.stderr)
        return False


def parse_markdown_table(md_content):
    """Parse the summary table from veracity markdown output.

    Returns dict with keys: v!, -v!, hole, nospec (all integers).
    """
    lines = md_content.split("\n")
    header_idx = None
    for i, line in enumerate(lines):
        # Look for the summary table header: must contain all aggregate columns
        # (avoids matching the abbreviation legend table which also has "| V! |")
        if "V!" in line and "-V!" in line and "Hole" in line and "NoSpec" in line:
            header_idx = i
            break

    if header_idx is None:
        return {}

    # Parse header cells
    headers = [h.strip() for h in lines[header_idx].split("|")]

    def col(name):
        try:
            return headers.index(name)
        except ValueError:
            return -1

    col_v = col("V!")
    col_nv = col("-V!")
    col_hole = col("Hole")
    col_nospec = col("NoSpec")

    totals = {"v!": 0, "-v!": 0, "hole": 0, "nospec": 0}

    # Skip header row and separator row, then parse data rows
    for line in lines[header_idx + 2:]:
        if not line.startswith("|"):
            break
        cells = [c.strip() for c in line.split("|")]
        try:
            if col_v >= 0:
                totals["v!"] += int(cells[col_v])
            if col_nv >= 0:
                totals["-v!"] += int(cells[col_nv])
            if col_hole >= 0:
                totals["hole"] += int(cells[col_hole])
            if col_nospec >= 0:
                totals["nospec"] += int(cells[col_nospec])
        except (ValueError, IndexError):
            continue

    return totals


def count_in_file(file_path, pattern):
    """Count occurrences of a string in a file."""
    try:
        with open(file_path, "r") as f:
            content = f.read()
        return content.count(pattern)
    except OSError:
        return 0


def scan_file(file_path):
    """Scan a single Rust source file and return progress metrics."""
    abs_file = os.path.abspath(file_path)
    if not os.path.exists(abs_file):
        print(f"ERROR: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    project_root = find_project_root(abs_file)
    if not project_root:
        print(f"ERROR: No Cargo.toml found above {file_path}", file=sys.stderr)
        sys.exit(1)

    rel_file = os.path.relpath(abs_file, project_root)

    # Run veracity
    run_veracity(project_root, rel_file)

    # Read JSON output (per-function data)
    json_path = os.path.join(project_root, ANALYSES_JSON)
    if not os.path.exists(json_path):
        print(f"ERROR: veracity did not produce {ANALYSES_JSON}", file=sys.stderr)
        sys.exit(1)

    with open(json_path, "r") as f:
        fn_data = json.load(f)
    total_fns = len(fn_data)

    # Read markdown for aggregate counts
    md_path = os.path.join(project_root, ANALYSES_MD)
    table_counts = {}
    if os.path.exists(md_path):
        with open(md_path, "r") as f:
            table_counts = parse_markdown_table(f.read())

    verus_wrapped = table_counts.get("v!", 0)
    unprocessed = table_counts.get("-v!", 0)
    hole = table_counts.get("hole", 0)  # external_body/assume/admit inside verus!

    # Grep source for explicit external markers and assume_specification
    external = count_in_file(abs_file, "#[verifier::external]")
    assume_specs = count_in_file(abs_file, "assume_specification")

    progress_pct = (verus_wrapped / total_fns * 100) if total_fns > 0 else 0

    return {
        "file": file_path,
        "project_root": project_root,
        "total_fns": total_fns,
        "verus_wrapped": verus_wrapped,
        "external_body": hole,
        "external": external,
        "assume_specs": assume_specs,
        "unprocessed": unprocessed,
        "progress_pct": progress_pct,
    }


def print_report(metrics, label=None):
    """Print a human-readable progress report."""
    total = metrics["total_fns"]
    wrapped = metrics["verus_wrapped"]
    unprocessed = metrics["unprocessed"]
    external = metrics["external"]
    external_body = metrics["external_body"]
    assume_specs = metrics["assume_specs"]
    pct = metrics["progress_pct"]

    target = label or metrics.get("file", "")
    print(f"File: {target}")
    print(f"Total exec fns:    {total}")
    print(f"  verus! wrapped:  {wrapped:3d}  ({wrapped/total*100:.0f}%)" if total else f"  verus! wrapped:  {wrapped}")
    if external_body > 0:
        print(f"    incl. external_body/hole: {external_body}")
    if external > 0:
        print(f"  #[verifier::external]: {external}")
    if assume_specs > 0:
        print(f"  assume_specification:  {assume_specs}")
    print(f"  unprocessed:     {unprocessed:3d}  ({unprocessed/total*100:.0f}%)" if total else f"  unprocessed:     {unprocessed}")
    print(f"Progress: {pct:.0f}%")


def parse_function_detail_table(md_content):
    """Parse the per-function detail table from veracity markdown.

    Returns list of dicts: {name, status, lines}
    status is one of: 'verus-wrapped', 'hole', 'unprocessed'
    """
    lines = md_content.split("\n")
    functions = []

    # Find the per-function detail header row (has Function, V!, -V!, SpecStr columns)
    for i, line in enumerate(lines):
        if "Function" in line and "V!" in line and "-V!" in line and "SpecStr" in line:
            header_idx = i
            headers = [h.strip() for h in line.split("|")]

            def col(name):
                try:
                    return headers.index(name)
                except ValueError:
                    return -1

            col_fn = col("Function")
            col_v = col("V!")
            col_nv = col("-V!")
            col_spec = col("SpecStr")
            col_lines = col("Lines")

            # Parse data rows (skip separator)
            for row in lines[header_idx + 2:]:
                if not row.startswith("|"):
                    break
                cells = [c.strip() for c in row.split("|")]
                if len(cells) < max(col_fn, col_v, col_nv, col_lines) + 1:
                    continue

                # Function name: strip backticks and trailing annotations
                raw_name = cells[col_fn] if col_fn >= 0 else ""
                name = raw_name.strip("`").split("`")[0].strip()

                in_verus = col_v >= 0 and cells[col_v] == "Y"
                outside_verus = col_nv >= 0 and cells[col_nv] == "Y"
                spec_str = cells[col_spec].strip() if col_spec >= 0 else ""
                fn_lines = cells[col_lines].strip() if col_lines >= 0 else ""
                # Replace HTML non-breaking hyphen
                fn_lines = fn_lines.replace("&#8209;", "-")

                if in_verus and spec_str:
                    status = "hole"  # external_body / assume / admit
                elif in_verus:
                    status = "verus-wrapped"
                else:
                    status = "unprocessed"

                if name:
                    functions.append({"name": name, "status": status, "lines": fn_lines})

    return functions


STATUS_SYMBOL = {"verus-wrapped": "[V]", "hole": "[H]", "unprocessed": "[ ]"}


def list_file(file_path):
    """Run veracity on a single file and return its full status data.

    Returns dict: {file, project_root, rel_file, total, verus_wrapped, hole,
                   unprocessed, progress_pct, functions}
    """
    abs_file = os.path.abspath(file_path)
    if not os.path.exists(abs_file):
        print(f"ERROR: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    project_root = find_project_root(abs_file)
    if not project_root:
        print(f"ERROR: No Cargo.toml found above {file_path}", file=sys.stderr)
        sys.exit(1)

    rel_file = os.path.relpath(abs_file, project_root)
    run_veracity(project_root, rel_file)

    json_path = os.path.join(project_root, ANALYSES_JSON)
    md_path = os.path.join(project_root, ANALYSES_MD)

    if not os.path.exists(json_path):
        print(f"ERROR: veracity did not produce {ANALYSES_JSON}", file=sys.stderr)
        sys.exit(1)

    with open(json_path, "r") as f:
        fn_data = json.load(f)
    total_fns = len(fn_data)

    table_counts = {}
    functions = []
    if os.path.exists(md_path):
        with open(md_path, "r") as f:
            md_content = f.read()
        table_counts = parse_markdown_table(md_content)
        functions = parse_function_detail_table(md_content)

    verus_wrapped = table_counts.get("v!", 0)
    unprocessed = table_counts.get("-v!", 0)
    hole = table_counts.get("hole", 0)
    progress_pct = (verus_wrapped / total_fns * 100) if total_fns > 0 else 0

    return {
        "file": rel_file,
        "project_root": project_root,
        "total": total_fns,
        "verus_wrapped": verus_wrapped,
        "hole": hole,
        "unprocessed": unprocessed,
        "progress_pct": round(progress_pct, 1),
        "functions": functions,
    }


def print_file_table(data):
    """Print per-function status table for one file."""
    functions = data["functions"]
    col_w = max((len(f["name"]) for f in functions), default=20)
    print(f"File: {data['file']}")
    print(f"{'Function':<{col_w}}  Status         Lines")
    print("-" * (col_w + 25))
    for fn in functions:
        sym = STATUS_SYMBOL.get(fn["status"], "???")
        print(f"{fn['name']:<{col_w}}  {sym} {fn['status']:<14} {fn['lines']}")
    print(
        f"  => {data['total']} fns  "
        f"[V]={data['verus_wrapped']}  [H]={data['hole']}  [ ]={data['unprocessed']}  "
        f"Progress: {data['progress_pct']:.0f}%"
    )


def cmd_list(args):
    """Show per-function status and optionally save to porting-status.json."""
    if args.file:
        data = list_file(args.file)
        print_file_table(data)
        print()
        print("Legend: [V]=verus-wrapped  [H]=hole(external_body/admit)  [ ]=unprocessed")

        if args.save:
            status_path = os.path.join(data["project_root"], STATUS_FILE)
            status_doc = {
                "project_root": data["project_root"],
                "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "progress_pct": data["progress_pct"],
                "summary": {
                    "total": data["total"],
                    "verus_wrapped": data["verus_wrapped"],
                    "hole": data["hole"],
                    "unprocessed": data["unprocessed"],
                },
                "files": [
                    {
                        "file": data["file"],
                        "progress_pct": data["progress_pct"],
                        "summary": {
                            "total": data["total"],
                            "verus_wrapped": data["verus_wrapped"],
                            "hole": data["hole"],
                            "unprocessed": data["unprocessed"],
                        },
                        "functions": data["functions"],
                    }
                ],
            }
            with open(status_path, "w") as f:
                json.dump(status_doc, f, indent=2)
            print(f"\nStatus saved to: {status_path}")

    elif args.dir:
        abs_dir = os.path.abspath(args.dir)
        rs_files = []
        for root, dirs, files in os.walk(abs_dir):
            dirs.sort()
            for fname in sorted(files):
                if fname.endswith(".rs"):
                    rs_files.append(os.path.join(root, fname))

        if not rs_files:
            print(f"No .rs files found in {args.dir}", file=sys.stderr)
            sys.exit(1)

        project_root = None
        file_entries = []
        totals = {"total": 0, "verus_wrapped": 0, "hole": 0, "unprocessed": 0}

        for rs_file in rs_files:
            try:
                data = list_file(rs_file)
                project_root = project_root or data["project_root"]
                print_file_table(data)
                print()
                for key in totals:
                    totals[key] += data.get(key, 0)
                file_entries.append({
                    "file": data["file"],
                    "progress_pct": data["progress_pct"],
                    "summary": {k: data[k] for k in ("total", "verus_wrapped", "hole", "unprocessed")},
                    "functions": data["functions"],
                })
            except SystemExit:
                continue

        total = totals["total"]
        pct = (totals["verus_wrapped"] / total * 100) if total > 0 else 0
        print("=" * 50)
        print(f"PROJECT TOTAL ({len(file_entries)} files)")
        print(f"  [V]={totals['verus_wrapped']}  [H]={totals['hole']}  [ ]={totals['unprocessed']}  total={total}")
        print(f"  Progress: {pct:.0f}%")
        print()
        print("Legend: [V]=verus-wrapped  [H]=hole(external_body/admit)  [ ]=unprocessed")

        if args.save and project_root:
            status_path = os.path.join(project_root, STATUS_FILE)
            status_doc = {
                "project_root": project_root,
                "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "progress_pct": round(pct, 1),
                "summary": {**totals},
                "files": file_entries,
            }
            with open(status_path, "w") as f:
                json.dump(status_doc, f, indent=2)
            print(f"\nStatus saved to: {status_path}")


def cmd_scan(args):
    if args.file:
        metrics = scan_file(args.file)
        print_report(metrics)
    elif args.dir:
        # Find all .rs files in the directory
        rs_files = []
        for root, dirs, files in os.walk(args.dir):
            dirs.sort()
            for fname in sorted(files):
                if fname.endswith(".rs"):
                    rs_files.append(os.path.join(root, fname))

        if not rs_files:
            print(f"No .rs files found in {args.dir}", file=sys.stderr)
            sys.exit(1)

        # Aggregate metrics across all files
        totals = {
            "total_fns": 0,
            "verus_wrapped": 0,
            "external_body": 0,
            "external": 0,
            "assume_specs": 0,
            "unprocessed": 0,
        }

        for rs_file in rs_files:
            try:
                m = scan_file(rs_file)
                print_report(m)
                print()
                for key in totals:
                    totals[key] += m.get(key, 0)
            except SystemExit:
                print(f"  (skipped: no Cargo.toml found)", file=sys.stderr)
                continue

        # Print aggregate
        total = totals["total_fns"]
        pct = (totals["verus_wrapped"] / total * 100) if total > 0 else 0
        print("=" * 40)
        print(f"TOTAL ({len(rs_files)} files)")
        print(f"Total exec fns:    {total}")
        print(f"  verus! wrapped:  {totals['verus_wrapped']:3d}  ({pct:.0f}%)" if total else f"  verus! wrapped:  {totals['verus_wrapped']}")
        print(f"  unprocessed:     {totals['unprocessed']:3d}  ({totals['unprocessed']/total*100:.0f}%)" if total else f"  unprocessed:     {totals['unprocessed']}")
        print(f"Progress: {pct:.0f}%")


def main():
    parser = argparse.ArgumentParser(
        description="Verus porting progress tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command")

    scan_parser = subparsers.add_parser("scan", help="Aggregate progress metrics for file/directory")
    group = scan_parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", help="Path to a single Rust source file")
    group.add_argument("--dir", help="Path to a directory of Rust source files")

    list_parser = subparsers.add_parser(
        "list", help="Per-function status table (optionally saved to porting-status.json)"
    )
    list_group = list_parser.add_mutually_exclusive_group(required=True)
    list_group.add_argument("--file", help="Path to a single Rust source file")
    list_group.add_argument("--dir", help="Path to a project directory (scans all .rs files)")
    list_parser.add_argument(
        "--save",
        action="store_true",
        help=f"Save status to <project-root>/{STATUS_FILE}",
    )

    args = parser.parse_args()

    if args.command == "scan":
        cmd_scan(args)
    elif args.command == "list":
        cmd_list(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
