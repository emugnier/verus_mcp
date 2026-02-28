#!/usr/bin/env python3
"""Knowledge base CLI for Verus verification patterns.

Usage:
  # Search for patterns matching an error
  python3 scripts/verus-kb.py retrieve --agent idiom-converter --error "ForLoopGhostIteratorNew"

  # Create a new pattern (content from stdin)
  python3 scripts/verus-kb.py create --agent idiom-converter --category unsupported/iterators --name flat-map-to-chars

  # Increment success_count and update last_used on an existing pattern
  python3 scripts/verus-kb.py update --path knowledge/idiom-converter/unsupported/flat-map-to-chars.md

KB root: knowledge/
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime

KB_ROOT = "knowledge"


def get_today():
    return datetime.now().strftime("%Y-%m-%d")


def parse_frontmatter(content):
    """Parse YAML frontmatter from a markdown file."""
    if not content.startswith("---"):
        return {}
    end = content.find("\n---", 3)
    if end == -1:
        return {}
    fm_text = content[3:end].strip()
    result = {}
    current_list_key = None

    for line in fm_text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- ") and current_list_key:
            item = stripped[2:].strip().strip("\"'")
            if isinstance(result.get(current_list_key), list):
                result[current_list_key].append(item)
        elif ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip()
            if val:
                result[key] = val.strip("\"'")
                current_list_key = None
            else:
                result[key] = []
                current_list_key = key

    return result


def score_pattern(content, frontmatter, keywords):
    """Score a pattern file against a set of keywords. Returns (score, reason)."""
    triggers = frontmatter.get("triggers", [])
    if isinstance(triggers, str):
        triggers = [triggers]

    best_score = 0
    best_reason = ""

    for trigger in triggers:
        trigger_lower = trigger.lower()
        trigger_keywords = set(re.findall(r"\b\w{3,}\b", trigger_lower))
        if not trigger_keywords:
            continue
        overlap = keywords & trigger_keywords
        ratio = len(overlap) / len(trigger_keywords)
        if ratio >= 0.8:
            score = 3
            reason = f"High trigger match ({ratio:.0%}): '{trigger[:60]}'"
        elif ratio >= 0.5:
            score = 2
            reason = f"Partial trigger match ({ratio:.0%}): '{trigger[:60]}'"
        elif len(overlap) >= 1:
            score = 1
            reason = f"Keyword match ({', '.join(overlap)}): '{trigger[:60]}'"
        else:
            score = 0
            reason = ""

        if score > best_score:
            best_score = score
            best_reason = reason

    # Fallback: count keyword occurrences in full content
    if best_score == 0:
        content_lower = content.lower()
        matches = sum(1 for kw in keywords if kw in content_lower)
        if matches >= 3:
            best_score = 1
            best_reason = f"Content keyword matches: {matches}"

    return best_score, best_reason


def cmd_retrieve(args):
    """Search knowledge base for patterns matching the given error."""
    agent = args.agent
    error_lower = args.error.lower()
    keywords = set(re.findall(r"\b\w{3,}\b", error_lower))

    results = []

    # Search agent-specific folder first, then cross-agent folders
    agent_dir = os.path.join(KB_ROOT, agent)
    search_dirs = []
    if os.path.exists(agent_dir):
        search_dirs.append((agent_dir, True))  # (path, is_primary)
    if os.path.exists(KB_ROOT):
        for entry in sorted(os.listdir(KB_ROOT)):
            full = os.path.join(KB_ROOT, entry)
            if os.path.isdir(full) and entry != agent:
                search_dirs.append((full, False))

    for search_dir, is_primary in search_dirs:
        for root, dirs, files in os.walk(search_dir):
            dirs.sort()
            for fname in sorted(files):
                if not fname.endswith(".md"):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "r") as f:
                        content = f.read()
                except OSError:
                    continue

                frontmatter = parse_frontmatter(content)
                score, reason = score_pattern(content, frontmatter, keywords)

                if score > 0:
                    if score >= 3:
                        confidence = "high"
                    elif score >= 2:
                        confidence = "medium"
                    else:
                        confidence = "low"

                    results.append(
                        {
                            "path": fpath,
                            "confidence": confidence,
                            "match_reason": reason,
                            "_score": score + (1 if is_primary else 0),
                        }
                    )

    results.sort(key=lambda x: x["_score"], reverse=True)
    for r in results:
        del r["_score"]

    print(json.dumps(results, indent=2))


def cmd_create(args):
    """Create a new pattern file from stdin."""
    path = os.path.join(KB_ROOT, args.agent, args.category, args.name + ".md")
    os.makedirs(os.path.dirname(path), exist_ok=True)

    if os.path.exists(path):
        print(f"ERROR: Pattern already exists: {path}", file=sys.stderr)
        sys.exit(1)

    content = sys.stdin.read()
    if not content.strip():
        print("ERROR: No content provided on stdin", file=sys.stderr)
        sys.exit(1)

    with open(path, "w") as f:
        f.write(content)

    print(path)


def cmd_update(args):
    """Increment success_count and update last_used on an existing pattern."""
    path = args.path
    if not os.path.exists(path):
        print(f"ERROR: Pattern not found: {path}", file=sys.stderr)
        sys.exit(1)

    with open(path, "r") as f:
        content = f.read()

    today = get_today()

    def increment_success(m):
        return f"success_count: {int(m.group(1)) + 1}"

    new_content = re.sub(r"success_count:\s*(\d+)", increment_success, content)
    new_content = re.sub(r"last_used:\s*\S+", f"last_used: {today}", new_content)

    with open(path, "w") as f:
        f.write(new_content)


def main():
    parser = argparse.ArgumentParser(
        description="Verus knowledge base CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command")

    retrieve_parser = subparsers.add_parser(
        "retrieve", help="Search for patterns matching an error"
    )
    retrieve_parser.add_argument(
        "--agent", required=True, help="Agent type (idiom-converter, assume-spec-gen, ...)"
    )
    retrieve_parser.add_argument(
        "--error", required=True, help="Error message or keywords to search for"
    )

    create_parser = subparsers.add_parser("create", help="Create a new pattern from stdin")
    create_parser.add_argument(
        "--agent", required=True, help="Agent type (idiom-converter, assume-spec-gen, ...)"
    )
    create_parser.add_argument(
        "--category",
        required=True,
        help="Category path within agent folder (e.g. unsupported/iterators)",
    )
    create_parser.add_argument(
        "--name", required=True, help="Pattern filename without .md extension"
    )

    update_parser = subparsers.add_parser(
        "update", help="Increment success_count and update last_used"
    )
    update_parser.add_argument("--path", required=True, help="Path to existing pattern file")

    args = parser.parse_args()

    if args.command == "retrieve":
        cmd_retrieve(args)
    elif args.command == "create":
        cmd_create(args)
    elif args.command == "update":
        cmd_update(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
