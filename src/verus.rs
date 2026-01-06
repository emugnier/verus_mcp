use anyhow::{Context, Result};
use rmcp::{ServerHandler, model::ServerInfo, schemars, tool};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use schemars::JsonSchema;
use std::io::{BufRead, BufReader};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::time::{Duration, Instant};

#[derive(Debug, Clone)]
pub struct VerusRunner {
    verus_path: String,
}

impl VerusRunner {
    pub fn new(verus_path: String) -> Self {
        Self { verus_path }
    }

    /// Find the cargo-verus binary next to the verus binary
    fn find_cargo_verus(&self) -> Result<PathBuf> {
        let verus_exec_path = Path::new(&self.verus_path)
            .canonicalize()
            .with_context(|| format!("Verus binary not found at {}", self.verus_path))?;

        let verus_exec_dir = verus_exec_path
            .parent()
            .unwrap_or_else(|| Path::new("."));
        
        Ok(verus_exec_dir.join("cargo-verus"))
    }

    /// Find the repository root by looking for Cargo.toml
    fn find_repo_root(&self, file_path: &str) -> Option<PathBuf> {
        let file = Path::new(file_path);
        
        for ancestor in file.ancestors() {
            if ancestor.join("Cargo.toml").exists() {
                return Some(if ancestor.as_os_str().is_empty() {
                    PathBuf::from(".")
                } else {
                    ancestor.to_path_buf()
                });
            }
        }
        None
    }

    /// Parse extra arguments from Cargo.toml
    fn parse_extra_args(&self, repo_root: &Path) -> Vec<String> {
        let cargo_toml_path = repo_root.join("Cargo.toml");
        let mut extra_args = Vec::new();
        
        if let Ok(toml_content) = std::fs::read_to_string(cargo_toml_path) {
            let mut found_verus_settings = false;
            
            for line in toml_content.lines() {
                if found_verus_settings {
                    if line.contains("extra_args") {
                        let start = "extra_args".len() + 1;
                        let mut arguments = line[start..line.len() - 1].trim().to_string();
                        if arguments.starts_with("=") {
                            arguments.remove(0);
                            arguments = arguments.trim().to_string();
                        }
                        if arguments.starts_with("\"") {
                            arguments.remove(0);
                        }
                        if arguments.ends_with("\"") {
                            arguments.remove(arguments.len() - 1);
                        }
                        extra_args.extend(
                            arguments
                                .split(" ")
                                .map(|it| it.to_string())
                                .collect::<Vec<_>>()
                        );
                    }
                    break;
                }
                if line.contains("[package.metadata.verus.ide]") {
                    found_verus_settings = true;
                }
            }
        }
        
        extra_args
    }

    /// Run Verus verification on a file or repository
    pub async fn verify(&self, file_path: String) -> Result<VerificationResult> {
        let cargo_verus_exec = self.find_cargo_verus()?;
        let repo_root = self.find_repo_root(&file_path);
        
        let mut cmd = Command::new(&cargo_verus_exec);
        
        // Build arguments
        let mut args = vec![
            "verify".to_string(),
            "--message-format=json".to_string(),
            "--".to_string(),
        ];
        
        // Add extra arguments from Cargo.toml if we found a repo root
        if let Some(ref root) = repo_root {
            let mut extra_args = self.parse_extra_args(root);
            args.append(&mut extra_args);
        }
        
        // Set working directory
        if let Some(root) = repo_root.clone() {
            cmd.current_dir(&root);
        }
        
        cmd.args(&args);
        cmd.stdout(Stdio::piped());
        cmd.stderr(Stdio::piped());
        
        let mut child = cmd.spawn()
            .with_context(|| format!("Failed to spawn cargo-verus process"))?;
        
        let stdout = child.stdout.take()
            .context("Failed to capture stdout from Verus process")?;
        
        let mut all_output = String::new();
        let reader = BufReader::new(stdout);
        
        for line in reader.lines() {
            let line = line?;
            all_output.push_str(&line);
            all_output.push('\n');
        }
        
        let status = child.wait()
            .context("Failed to wait for cargo-verus process")?;
        
        let exit_code = status.code().unwrap_or(-1);
        let success = status.success();
        
        // Parse diagnostics from JSON output
        let diagnostics = self.parse_diagnostics(&all_output);
        
        Ok(VerificationResult {
            success,
            exit_code,
            output: all_output,
            diagnostics,
            file_path: file_path.clone(),
        })
    }

    /// Parse diagnostics from Verus JSON output
    fn parse_diagnostics(&self, output: &str) -> Vec<VerusDiagnostic> {
        let mut diagnostics = Vec::new();
        
        for line in output.lines() {
            if let Ok(json_value) = serde_json::from_str::<Value>(line) {
                if let Some(diagnostic) = self.parse_diagnostic_json(&json_value) {
                    diagnostics.push(diagnostic);
                }
            }
        }
        
        diagnostics
    }

    fn parse_diagnostic_json(&self, json: &Value) -> Option<VerusDiagnostic> {
        let message = json.get("message")?.as_str()?.to_string();
        let level = json.get("level")?.as_str()?.to_string();
        
        let spans = json.get("spans")?
            .as_array()?
            .iter()
            .filter_map(|span| self.parse_span_json(span))
            .collect();
        
        Some(VerusDiagnostic {
            message,
            level,
            spans,
        })
    }
    
    fn parse_span_json(&self, span_json: &Value) -> Option<DiagnosticSpan> {
        let file_name = span_json.get("file_name")?.as_str()?.to_string();
        let line_start = span_json.get("line_start")?.as_u64()? as u32;
        let line_end = span_json.get("line_end")?.as_u64()? as u32;
        let column_start = span_json.get("column_start")?.as_u64()? as u32;
        let column_end = span_json.get("column_end")?.as_u64()? as u32;
        
        Some(DiagnosticSpan {
            file_name,
            line_start,
            line_end,
            column_start,
            column_end,
        })
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
pub struct VerificationResult {
    pub success: bool,
    pub exit_code: i32,
    pub output: String,
    pub diagnostics: Vec<VerusDiagnostic>,
    pub file_path: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
pub struct VerusDiagnostic {
    pub message: String,
    pub level: String,
    pub spans: Vec<DiagnosticSpan>,
}

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
pub struct DiagnosticSpan {
    pub file_name: String,
    pub line_start: u32,
    pub line_end: u32,
    pub column_start: u32,
    pub column_end: u32,
}

/// Result from running a cargo command
#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
pub struct CargoCommandResult {
    pub success: bool,
    pub exit_code: i32,
    pub stdout: String,
    pub stderr: String,
    pub duration_ms: u64,
    pub command: Vec<String>,
    pub cwd: String,
}

/// Server implementation with Verus tools
#[derive(Debug, Clone)]
pub struct VerusServer {
    pub runner: VerusRunner,
}

impl VerusServer {
    pub fn new(verus_path: String) -> Self {
        Self {
            runner: VerusRunner::new(verus_path),
        }
    }

    /// Helper function to run cargo commands with timeout
    pub async fn run_cargo_command(
        project_dir: &str,
        subcommand: &str,
        release: bool,
        test_mode: Option<String>,
        test_name: Option<String>,
        timeout_seconds: u64,
    ) -> Result<CargoCommandResult, String> {
        // Validate project directory
        let project_path = Path::new(project_dir);
        if !project_path.exists() {
            return Err(format!("Project directory does not exist: {}", project_dir));
        }

        let cargo_toml = project_path.join("Cargo.toml");
        if !cargo_toml.exists() {
            return Err(format!(
                "Cargo.toml not found in directory: {}",
                project_dir
            ));
        }

        // Build command
        let mut cmd = Command::new("cargo");
        cmd.current_dir(project_path);
        cmd.arg(subcommand);

        let mut command_args = vec!["cargo".to_string(), subcommand.to_string()];

        if release {
            cmd.arg("--release");
            command_args.push("--release".to_string());
        }

        // Handle test-specific arguments
        if subcommand == "test" {
            if let Some(mode) = test_mode {
                match mode.as_str() {
                    "all" => {
                        // No additional args for running all tests
                    }
                    "filter" => {
                        if let Some(name) = test_name {
                            cmd.arg(&name);
                            command_args.push(name);
                        }
                    }
                    "exact" => {
                        if let Some(name) = test_name {
                            cmd.arg("--");
                            cmd.arg("--exact");
                            cmd.arg(&name);
                            command_args.push("--".to_string());
                            command_args.push("--exact".to_string());
                            command_args.push(name);
                        }
                    }
                    _ => {}
                }
            }
        }

        cmd.stdout(Stdio::piped());
        cmd.stderr(Stdio::piped());

        let start = Instant::now();
        let output = tokio::time::timeout(
            Duration::from_secs(timeout_seconds),
            tokio::task::spawn_blocking(move || cmd.output()),
        )
        .await
        .map_err(|_| format!("Command timed out after {} seconds", timeout_seconds))?
        .map_err(|e| format!("Failed to spawn cargo process: {}", e))?
        .map_err(|e| format!("Failed to execute cargo: {}", e))?;

        let duration_ms = start.elapsed().as_millis() as u64;

        let stdout = String::from_utf8_lossy(&output.stdout).to_string();
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();
        let exit_code = output.status.code().unwrap_or(-1);
        let success = output.status.success();

        Ok(CargoCommandResult {
            success,
            exit_code,
            stdout,
            stderr,
            duration_ms,
            command: command_args,
            cwd: project_dir.to_string(),
        })
    }
}

// Tool implementations using rmcp macros
#[tool(tool_box)]
impl VerusServer {
    /// Run Verus verification on a Rust file or project
    #[tool(
        name = "verus_verify",
        description = "Run Verus verification on a Rust file or project"
    )]
    async fn verify(
        &self,
        #[tool(param)]
        #[schemars(description = "Path to the Rust file or project directory to verify")]
        file_path: String,
    ) -> Result<String, String> {
        match self.runner.verify(file_path).await {
            Ok(result) => {
                serde_json::to_string_pretty(&result)
                    .map_err(|e| format!("Failed to serialize result: {}", e))
            }
            Err(e) => Err(e.to_string()),
        }
    }

    /// Check Verus syntax without running full verification
    #[tool(
        name = "verus_check_syntax",
        description = "Check Verus syntax without running full verification"
    )]
    async fn check_syntax(
        &self,
        #[tool(param)]
        #[schemars(description = "Path to the Rust file to syntax check")]
        file_path: String,
    ) -> Result<String, String> {
        match self.runner.verify(file_path).await {
            Ok(result) => {
                let syntax_errors: Vec<_> = result
                    .diagnostics
                    .iter()
                    .filter(|d| d.level == "error")
                    .collect();
                Ok(serde_json::to_string_pretty(&json!({
                    "message": "Syntax check completed",
                    "syntax_errors": syntax_errors
                }))
                .unwrap_or_else(|_| "Syntax check completed".to_string()))
            }
            Err(e) => Err(e.to_string()),
        }
    }

    /// Get detailed diagnostics from Verus verification results
    #[tool(
        name = "verus_get_diagnostics",
        description = "Get detailed diagnostics from Verus verification results"
    )]
    async fn get_diagnostics(
        &self,
        #[tool(param)]
        #[schemars(description = "Path to the file to get diagnostics for")]
        file_path: String,
        #[tool(param)]
        #[schemars(description = "Filter diagnostics by level (error, warning, note)")]
        level_filter: Option<String>,
    ) -> Result<String, String> {
        match self.runner.verify(file_path).await {
            Ok(result) => {
                let mut diagnostics = result.diagnostics;

                if let Some(filter) = level_filter {
                    diagnostics.retain(|d| d.level == filter);
                }

                Ok(serde_json::to_string_pretty(&json!({
                    "diagnostics": diagnostics,
                    "total_count": diagnostics.len(),
                    "file_path": result.file_path
                }))
                .unwrap_or_else(|_| "Diagnostics retrieved".to_string()))
            }
            Err(e) => Err(e.to_string()),
        }
    }

    /// Run cargo build on a Rust project
    #[tool(
        name = "cargo_build",
        description = "Run cargo build on a Rust project"
    )]
    async fn cargo_build(
        &self,
        #[tool(param)]
        #[schemars(description = "Directory containing Cargo.toml")]
        project_dir: String,
        #[tool(param)]
        #[schemars(description = "Build in release mode")]
        release: Option<bool>,
        #[tool(param)]
        #[schemars(description = "Timeout in seconds (default: 300)")]
        timeout_seconds: Option<u64>,
    ) -> Result<String, String> {
        let result = Self::run_cargo_command(
            &project_dir,
            "build",
            release.unwrap_or(false),
            None,
            None,
            timeout_seconds.unwrap_or(300),
        )
        .await?;

        serde_json::to_string_pretty(&result)
            .map_err(|e| format!("Failed to serialize result: {}", e))
    }

    /// Run cargo test on a Rust project
    #[tool(
        name = "cargo_test",
        description = "Run cargo test on a Rust project with flexible test selection"
    )]
    async fn cargo_test(
        &self,
        #[tool(param)]
        #[schemars(description = "Directory containing Cargo.toml")]
        project_dir: String,
        #[tool(param)]
        #[schemars(description = "Test mode: 'all' (run all tests), 'filter' (substring match), or 'exact' (exact test name)")]
        test_mode: String,
        #[tool(param)]
        #[schemars(description = "Test name or filter (required for 'filter' and 'exact' modes)")]
        test_name: Option<String>,
        #[tool(param)]
        #[schemars(description = "Timeout in seconds (default: 300)")]
        timeout_seconds: Option<u64>,
    ) -> Result<String, String> {
        // Validate test_mode
        if !["all", "filter", "exact"].contains(&test_mode.as_str()) {
            return Err(format!(
                "Invalid test_mode '{}'. Must be 'all', 'filter', or 'exact'",
                test_mode
            ));
        }

        // Validate test_name is provided when required
        if (test_mode == "filter" || test_mode == "exact") && test_name.is_none() {
            return Err(format!(
                "test_name is required when test_mode is '{}'",
                test_mode
            ));
        }

        let result = Self::run_cargo_command(
            &project_dir,
            "test",
            false,
            Some(test_mode),
            test_name,
            timeout_seconds.unwrap_or(300),
        )
        .await?;

        serde_json::to_string_pretty(&result)
            .map_err(|e| format!("Failed to serialize result: {}", e))
    }
}

// Implement ServerHandler trait for VerusServer
#[tool(tool_box)]
impl ServerHandler for VerusServer {
    fn get_info(&self) -> ServerInfo {
        ServerInfo {
            instructions: Some("MCP server for Verus verification".into()),
            ..Default::default()
        }
    }
}