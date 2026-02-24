---
name: log-event
description: Log events to the session history file. Use to track verification runs, subagent dispatches, changes applied, and other significant events during the retrofit process.
allowed-tools: Read, Write, Edit
---

# Log Event Skill

Append structured events to the session history log at `.claude/verus-history/session-log.json`.

## Purpose

Track all significant events during the Verus verification retrofit process:
- Verification runs and their results
- Subagent dispatches and outcomes
- Pattern learning events
- User interventions
- Success/failure tracking

## Session Log Format

Location: `.claude/verus-history/session-log.json`

Structure:
```json
{
  "schema_version": "1.0",
  "sessions": [
    {
      "session_id": "uuid-v4",
      "started_at": "ISO-8601 timestamp",
      "ended_at": "ISO-8601 timestamp or null if active",
      "target_file": "path/to/file.rs",
      "initial_error_count": 0,
      "final_error_count": 0,
      "status": "in_progress | completed | failed",
      "events": [...]
    }
  ]
}
```

## Event Types

### 1. Verification Run
```json
{
  "type": "verus_run",
  "timestamp": "ISO-8601",
  "verified_count": 12,
  "error_count": 3,
  "syntax_errors": 0,
  "unsupported_errors": 2,
  "verification_failures": 1,
  "errors": [
    {
      "location": "file.rs:45",
      "category": "unsupported",
      "message": "error text..."
    }
  ]
}
```

### 2. Subagent Dispatch
```json
{
  "type": "subagent_dispatch",
  "timestamp": "ISO-8601",
  "agent": "idiom-converter | assume-spec-gen | repair-agent",
  "reason": "description of why agent was called",
  "error_targeted": "the error message being fixed"
}
```

### 3. Change Applied
```json
{
  "type": "change_applied",
  "timestamp": "ISO-8601",
  "agent": "idiom-converter | assume-spec-gen | repair-agent",
  "acceptance": "accepted | rejected",
  "reason": "why accepted/rejected",
  "error_count_before": 5,
  "error_count_after": 3,
  "files_modified": ["file1.rs", "file2.rs"]
}
```

### 4. Verification Failure Logged
```json
{
  "type": "verification_failure_logged",
  "timestamp": "ISO-8601",
  "error": "precondition might not hold",
  "location": "file.rs:67",
  "note": "Expected during retrofit - not blocking"
}
```

### 5. Self-Learned Pattern
```json
{
  "type": "self_learned",
  "timestamp": "ISO-8601",
  "agent": "idiom-converter | assume-spec-gen | repair-agent",
  "pattern_id": "knowledge/agent/category/name.md",
  "trigger": "error message that triggers this pattern",
  "success_count": 1
}
```

### 6. User Help Requested
```json
{
  "type": "user_help_requested",
  "timestamp": "ISO-8601",
  "reason": "3 failed attempts on same error",
  "error": "the error message",
  "attempts": ["attempt 1 description", "attempt 2 description", "attempt 3 description"]
}
```

### 7. User Help Received
```json
{
  "type": "user_help_received",
  "timestamp": "ISO-8601",
  "solution": "description of user's fix",
  "pattern_saved": true,
  "pattern_id": "knowledge/agent/category/name.md"
}
```

## Usage

### Starting a New Session

```
1. Read the session log file
2. Generate a new UUID for session_id
3. Create new session object with:
   - session_id
   - started_at: current timestamp
   - ended_at: null
   - target_file: the file being worked on
   - status: "in_progress"
   - events: []
4. Append to sessions array
5. Write back to file
```

### Logging an Event

```
1. Read the session log file
2. Find the active session (status: "in_progress")
3. Create event object with appropriate type and fields
4. Append to session's events array
5. Write back to file
```

### Ending a Session

```
1. Read the session log file
2. Find the active session
3. Update:
   - ended_at: current timestamp
   - status: "completed" or "failed"
   - final_error_count: final count from last verification
4. Write back to file
```

## Helper Functions

### Generate UUID
```javascript
// Use this pattern for session IDs
const uuid = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
```

### Get Current Timestamp
```javascript
// ISO-8601 format
const timestamp = new Date().toISOString();
```

### Find Active Session
```javascript
// The active session is the one with status: "in_progress"
const activeSession = sessions.find(s => s.status === "in_progress");
```

## Important Rules

1. **Always use ISO-8601 timestamps** - `new Date().toISOString()`
2. **Only one active session at a time** - end previous session before starting new one
3. **Log all significant events** - don't skip events to save space
4. **Atomic writes** - read, modify, write in single operation
5. **Preserve all previous sessions** - append only, never delete history
6. **Validate JSON structure** - ensure valid JSON before writing

## Error Handling

If the log file doesn't exist:
```json
{
  "schema_version": "1.0",
  "sessions": []
}
```

If JSON is malformed:
- Back up the corrupted file
- Create fresh log file
- Report the issue

## Example Workflow

```
1. User: "Fix iban_validate/src/base_iban.rs"
2. Start session: session_id="123-abc"
3. Log verus_run event: 15 errors found
4. Log subagent_dispatch: idiom-converter for "? operator not supported"
5. Log change_applied: accepted, errors: 15 → 14
6. Log verus_run event: 14 errors remain
7. ... repeat for each fix ...
8. End session: status="completed", final_error_count=0
```

## Performance

- Keep session log file size reasonable (< 1MB)
- Archive old sessions if file grows too large
- Use efficient JSON parsing (stream if needed)
- Avoid reading/writing on every minor event (batch if appropriate)
