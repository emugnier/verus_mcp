# Verus MCP Server

A Model Context Protocol (MCP) server for [Verus](https://github.com/verus-lang/verus), a tool for verifying the correctness of Rust programs.

## Design notes

We will use stdio for now as it is the easiest to setup:
- https://docs.cursor.com/en/context/mcp
- https://docs.anthropic.com/en/docs/claude-code/mcp#option-1%3A-add-a-local-stdio-server

It will have multiple 

## Features

This MCP server provides the following tools:

### Verus Tools
- **verus_verify**: Run Verus verification on a Rust file or project
- **verus_check_syntax**: Check Verus syntax without running full verification  
- **verus_get_diagnostics**: Get detailed diagnostics from Verus verification results

### Cargo Tools
- **cargo_build**: Run `cargo build` on a Rust project with optional release mode
- **cargo_test**: Run `cargo test` with flexible test selection (all tests, filtered by substring, or exact test name)

## Installation

1. Make sure you have [Verus installed](https://github.com/verus-lang/verus/blob/main/INSTALL.md)
2. Clone this repository:
   ```bash
   git clone <repository-url>
   cd verus_mcp
   ```
3. Build the project:
   ```bash
   cargo build --release
   ```

## Usage

### Running the MCP Server

```bash
# Use default verus path
./target/release/verus_mcp

# Specify custom verus path
./target/release/verus_mcp --verus-path /path/to/verus

# Specify custom port
./target/release/verus_mcp --port 3001
```

### Tool Usage

#### verus_verify

Runs Verus verification on a file or project:

```json
{
  "tool": "verus_verify",
  "arguments": {
    "file_path": "/path/to/your/rust/file.rs"
  }
}
```

Returns:
```json
{
  "message": "Verus verification completed successfully",
  "result": {
    "success": true,
    "exit_code": 0,
    "output": "...",
    "diagnostics": [...],
    "file_path": "/path/to/your/rust/file.rs"
  }
}
```

#### verus_check_syntax

Checks syntax without full verification:

```json
{
  "tool": "verus_check_syntax", 
  "arguments": {
    "file_path": "/path/to/your/rust/file.rs"
  }
}
```

#### verus_get_diagnostics

Gets detailed diagnostics, optionally filtered by level:

```json
{
  "tool": "verus_get_diagnostics",
  "arguments": {
    "file_path": "/path/to/your/rust/file.rs",
    "level_filter": "error"
  }
}
```

#### cargo_build

Runs `cargo build` on a Rust project:

```json
{
  "tool": "cargo_build",
  "arguments": {
    "project_dir": "/path/to/your/rust/project",
    "release": false,
    "timeout_seconds": 300
  }
}
```

Returns:
```json
{
  "success": true,
  "exit_code": 0,
  "stdout": "...",
  "stderr": "...",
  "duration_ms": 1234,
  "command": ["cargo", "build"],
  "cwd": "/path/to/your/rust/project"
}
```

#### cargo_test

Runs `cargo test` with flexible test selection:

**Run all tests:**
```json
{
  "tool": "cargo_test",
  "arguments": {
    "project_dir": "/path/to/your/rust/project",
    "test_mode": "all",
    "timeout_seconds": 300
  }
}
```

**Run tests matching a substring (e.g., all tests related to "add"):**
```json
{
  "tool": "cargo_test",
  "arguments": {
    "project_dir": "/path/to/your/rust/project",
    "test_mode": "filter",
    "test_name": "add",
    "timeout_seconds": 300
  }
}
```

**Run exactly one test by full name:**
```json
{
  "tool": "cargo_test",
  "arguments": {
    "project_dir": "/path/to/your/rust/project",
    "test_mode": "exact",
    "test_name": "tests::test_multiply",
    "timeout_seconds": 300
  }
}
```

Returns the same structure as `cargo_build`.

## Configuration

The server automatically detects Verus configuration from `Cargo.toml` files, including:

- Extra arguments from `[package.metadata.verus.ide]` sections
- Project root directory detection
- Automatic cargo-verus binary location

## Integration with MCP Clients

This server can be integrated with any MCP-compatible client. Configure your client to connect to this server using the appropriate host and port.

## Development

### Running Tests

```bash
cargo test
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Related Projects

- [Verus](https://github.com/verus-lang/verus) - The verification tool this MCP server wraps
- [RMCP](https://github.com/jxdp/rmcp) - Rust Model Context Protocol implementation used by this server
