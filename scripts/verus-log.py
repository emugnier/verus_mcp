#!/usr/bin/env python3
"""Session/event logging CLI for Verus verification sessions.

Usage:
  python3 scripts/verus-log.py session create --target <file-or-dir>
  python3 scripts/verus-log.py session end [--status completed|failed]
  python3 scripts/verus-log.py event --type <type> --data '<json>'

Log path: .claude/verus-history/session-log.json
"""

import argparse
import json
import os
import random
import string
import sys
import time
from datetime import datetime, timezone

LOG_PATH = ".claude/verus-history/session-log.json"


def get_timestamp():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def generate_session_id():
    ts = int(time.time() * 1000)
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=9))
    return f"{ts}-{suffix}"


def read_log():
    if not os.path.exists(LOG_PATH):
        return {"schema_version": "1.0", "sessions": []}
    with open(LOG_PATH, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            import shutil
            bak = LOG_PATH + ".bak"
            shutil.copy(LOG_PATH, bak)
            print(f"WARNING: Corrupted log backed up to {bak}", file=sys.stderr)
            return {"schema_version": "1.0", "sessions": []}


def write_log(log):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)


def find_active_session(log):
    for session in log["sessions"]:
        if session.get("status") == "in_progress":
            return session
    return None


def cmd_session_create(args):
    log = read_log()
    active = find_active_session(log)
    if active:
        print(
            f"ERROR: Active session already exists: {active['session_id']}",
            file=sys.stderr,
        )
        sys.exit(1)
    session_id = generate_session_id()
    session = {
        "session_id": session_id,
        "started_at": get_timestamp(),
        "ended_at": None,
        "target_file": args.target,
        "initial_error_count": 0,
        "final_error_count": 0,
        "status": "in_progress",
        "events": [],
    }
    log["sessions"].append(session)
    write_log(log)
    print(session_id)


def cmd_session_end(args):
    log = read_log()
    active = find_active_session(log)
    if not active:
        print("ERROR: No active session found", file=sys.stderr)
        sys.exit(1)
    active["ended_at"] = get_timestamp()
    active["status"] = args.status
    write_log(log)


def cmd_event(args):
    log = read_log()
    active = find_active_session(log)
    if not active:
        print("ERROR: No active session found", file=sys.stderr)
        sys.exit(1)
    try:
        data = json.loads(args.data)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in --data: {e}", file=sys.stderr)
        sys.exit(1)
    event = {"type": args.type, "timestamp": get_timestamp(), **data}
    active["events"].append(event)
    write_log(log)


def main():
    parser = argparse.ArgumentParser(
        description="Verus session/event logging CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command")

    # session subcommand
    session_parser = subparsers.add_parser("session", help="Manage sessions")
    session_sub = session_parser.add_subparsers(dest="subcommand")

    create_parser = session_sub.add_parser("create", help="Start a new session")
    create_parser.add_argument(
        "--target", required=True, help="Target file or directory being worked on"
    )

    end_parser = session_sub.add_parser("end", help="End the active session")
    end_parser.add_argument(
        "--status",
        choices=["completed", "failed"],
        default="completed",
        help="Session outcome (default: completed)",
    )

    # event subcommand
    event_parser = subparsers.add_parser("event", help="Log an event to active session")
    event_parser.add_argument(
        "--type",
        required=True,
        help="Event type (verus_run, change_applied, subagent_dispatch, self_learned, ...)",
    )
    event_parser.add_argument(
        "--data",
        required=True,
        help="JSON object with event-specific fields",
    )

    args = parser.parse_args()

    if args.command == "session":
        if args.subcommand == "create":
            cmd_session_create(args)
        elif args.subcommand == "end":
            cmd_session_end(args)
        else:
            session_parser.print_help()
            sys.exit(1)
    elif args.command == "event":
        cmd_event(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
