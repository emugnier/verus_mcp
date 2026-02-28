---
name: log-event
description: Log events to the session history file. Use to track verification runs, subagent dispatches, changes applied, and other significant events during the retrofit process.
allowed-tools: Bash
---

# Log Event Skill

Use the `verus-log.py` CLI to append structured events to `.claude/verus-history/session-log.json`.

## Session Commands

### Start a new session
```bash
SESSION_ID=$(python3 scripts/verus-log.py session create --target <file-or-dir>)
echo "Session: $SESSION_ID"
```
Prints the new session ID to stdout. Fails if a session is already active.

### End the active session
```bash
python3 scripts/verus-log.py session end --status completed
# or
python3 scripts/verus-log.py session end --status failed
```

## Event Commands

All events are logged to the currently active session.

### Verification run
```bash
python3 scripts/verus-log.py event --type verus_run --data '{
  "verified_count": 12,
  "error_count": 3,
  "syntax_errors": 0,
  "unsupported_errors": 2,
  "verification_failures": 1,
  "errors": [{"location": "file.rs:45", "category": "unsupported", "message": "..."}]
}'
```

### Subagent dispatch
```bash
python3 scripts/verus-log.py event --type subagent_dispatch --data '{
  "agent": "idiom-converter",
  "reason": "? operator not supported",
  "error_targeted": "error: Verus does not support the ? operator at file.rs:32"
}'
```

### Change applied (logged by subagents, not orchestrator)
```bash
python3 scripts/verus-log.py event --type change_applied --data '{
  "agent": "idiom-converter",
  "acceptance": "accepted",
  "reason": "Converted ? to match, error resolved",
  "error_count_before": 5,
  "error_count_after": 4,
  "files_modified": ["src/lib.rs"]
}'
```

### Pattern learned
```bash
python3 scripts/verus-log.py event --type self_learned --data '{
  "agent": "idiom-converter",
  "pattern_id": "knowledge/idiom-converter/unsupported/question-mark.md",
  "trigger": "Verus does not support the ? operator",
  "success_count": 1
}'
```

### Verification failure (non-blocking, log only)
```bash
python3 scripts/verus-log.py event --type verification_failure_logged --data '{
  "error": "precondition might not hold",
  "location": "file.rs:67",
  "note": "Expected during retrofit - not blocking"
}'
```

### User help requested
```bash
python3 scripts/verus-log.py event --type user_help_requested --data '{
  "reason": "3 failed attempts on same error",
  "error": "the error message",
  "attempts": ["attempt 1", "attempt 2", "attempt 3"]
}'
```

## Event Ownership

| Event type | Logged by |
|-----------|-----------|
| `verus_run` | Orchestrator |
| `subagent_dispatch` | Orchestrator |
| `verification_failure_logged` | Orchestrator |
| `change_applied` | Subagent that made the change |
| `self_learned` | Subagent that learned the pattern |
| `user_help_requested` | Subagent |
| `user_help_received` | Orchestrator |

## Error Handling

- Exits with code 1 and prints to stderr on error
- Backs up corrupted log files to `.bak` before resetting
- Only one active session at a time (`session create` will fail if one exists)
