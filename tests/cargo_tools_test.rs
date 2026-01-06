use std::fs;
use std::path::PathBuf;
use tempfile::TempDir;
use tokio;

/// Helper to create a dummy Cargo project for testing
fn create_dummy_project() -> (TempDir, PathBuf) {
    let temp_dir = TempDir::new().expect("Failed to create temp dir");
    let project_dir = temp_dir.path().join("dummy_project");
    
    // Create project directory
    fs::create_dir(&project_dir).expect("Failed to create project directory");
    
    // Create Cargo.toml
    let cargo_toml = r#"[package]
name = "dummy_project"
version = "0.1.0"
edition = "2021"

[dependencies]
"#;
    fs::write(project_dir.join("Cargo.toml"), cargo_toml)
        .expect("Failed to write Cargo.toml");
    
    // Create src directory
    let src_dir = project_dir.join("src");
    fs::create_dir(&src_dir).expect("Failed to create src directory");
    
    // Create lib.rs with some tests
    let lib_rs = r#"
/// Add two numbers
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}

/// Subtract two numbers
pub fn subtract(a: i32, b: i32) -> i32 {
    a - b
}

/// Multiply two numbers
pub fn multiply(a: i32, b: i32) -> i32 {
    a * b
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_add() {
        assert_eq!(add(2, 3), 5);
        assert_eq!(add(-1, 1), 0);
    }

    #[test]
    fn test_add_negative() {
        assert_eq!(add(-5, -3), -8);
    }

    #[test]
    fn test_subtract() {
        assert_eq!(subtract(5, 3), 2);
        assert_eq!(subtract(0, 5), -5);
    }

    #[test]
    fn test_multiply() {
        assert_eq!(multiply(3, 4), 12);
        assert_eq!(multiply(-2, 3), -6);
    }
}
"#;
    fs::write(src_dir.join("lib.rs"), lib_rs).expect("Failed to write lib.rs");
    
    (temp_dir, project_dir)
}

#[tokio::test]
async fn test_cargo_build_success() {
    let (_temp_dir, project_dir) = create_dummy_project();
    let project_dir_str = project_dir.to_str().unwrap();
    
    // Call cargo_build via the internal method
    let result = verus_mcp::verus::VerusServer::run_cargo_command(
        project_dir_str,
        "build",
        false,
        None,
        None,
        300,
    )
    .await;
    
    assert!(result.is_ok(), "cargo build should succeed");
    let result = result.unwrap();
    
    assert!(result.success, "Build should be successful");
    assert_eq!(result.exit_code, 0);
    assert!(result.duration_ms > 0);
    assert_eq!(result.command, vec!["cargo", "build"]);
    assert_eq!(result.cwd, project_dir_str);
}

#[tokio::test]
async fn test_cargo_build_release() {
    let (_temp_dir, project_dir) = create_dummy_project();
    let project_dir_str = project_dir.to_str().unwrap();
    
    let result = verus_mcp::verus::VerusServer::run_cargo_command(
        project_dir_str,
        "build",
        true,
        None,
        None,
        300,
    )
    .await;
    
    assert!(result.is_ok(), "cargo build --release should succeed");
    let result = result.unwrap();
    
    assert!(result.success);
    assert!(result.command.contains(&"--release".to_string()));
}

#[tokio::test]
async fn test_cargo_build_invalid_directory() {
    let result = verus_mcp::verus::VerusServer::run_cargo_command(
        "/nonexistent/directory",
        "build",
        false,
        None,
        None,
        300,
    )
    .await;
    
    assert!(result.is_err(), "Should fail with invalid directory");
    let err = result.unwrap_err();
    assert!(err.contains("does not exist"));
}

#[tokio::test]
async fn test_cargo_test_all() {
    let (_temp_dir, project_dir) = create_dummy_project();
    let project_dir_str = project_dir.to_str().unwrap();
    
    let result = verus_mcp::verus::VerusServer::run_cargo_command(
        project_dir_str,
        "test",
        false,
        Some("all".to_string()),
        None,
        300,
    )
    .await;
    
    assert!(result.is_ok(), "cargo test should succeed");
    let result = result.unwrap();
    
    assert!(result.success, "All tests should pass");
    assert_eq!(result.exit_code, 0);
    
    // Check that output contains test results
    let combined_output = format!("{}{}", result.stdout, result.stderr);
    assert!(combined_output.contains("test_add"));
    assert!(combined_output.contains("test_subtract"));
    assert!(combined_output.contains("test_multiply"));
}

#[tokio::test]
async fn test_cargo_test_filter() {
    let (_temp_dir, project_dir) = create_dummy_project();
    let project_dir_str = project_dir.to_str().unwrap();
    
    // Test filtering for "add" - should run test_add and test_add_negative
    let result = verus_mcp::verus::VerusServer::run_cargo_command(
        project_dir_str,
        "test",
        false,
        Some("filter".to_string()),
        Some("add".to_string()),
        300,
    )
    .await;
    
    assert!(result.is_ok(), "cargo test with filter should succeed");
    let result = result.unwrap();
    
    assert!(result.success);
    assert!(result.command.contains(&"add".to_string()));
    
    let combined_output = format!("{}{}", result.stdout, result.stderr);
    assert!(combined_output.contains("test_add"));
    // Should run both test_add and test_add_negative
}

#[tokio::test]
async fn test_cargo_test_exact() {
    let (_temp_dir, project_dir) = create_dummy_project();
    let project_dir_str = project_dir.to_str().unwrap();
    
    // Test exact match for a specific test
    // Note: --exact requires the full test path including module
    let result = verus_mcp::verus::VerusServer::run_cargo_command(
        project_dir_str,
        "test",
        false,
        Some("exact".to_string()),
        Some("tests::test_multiply".to_string()),
        300,
    )
    .await;
    
    assert!(result.is_ok(), "cargo test with exact match should succeed");
    let result = result.unwrap();
    
    assert!(result.success);
    assert!(result.command.contains(&"--exact".to_string()));
    assert!(result.command.contains(&"tests::test_multiply".to_string()));
    
    // The test should have run (even if exact match requires full path)
    assert!(result.exit_code == 0, "Test should complete successfully");
}

#[tokio::test]
async fn test_cargo_test_filter_substring() {
    let (_temp_dir, project_dir) = create_dummy_project();
    let project_dir_str = project_dir.to_str().unwrap();
    
    // Test filtering for "subtract" - should run only test_subtract
    let result = verus_mcp::verus::VerusServer::run_cargo_command(
        project_dir_str,
        "test",
        false,
        Some("filter".to_string()),
        Some("subtract".to_string()),
        300,
    )
    .await;
    
    assert!(result.is_ok());
    let result = result.unwrap();
    
    assert!(result.success);
    let combined_output = format!("{}{}", result.stdout, result.stderr);
    assert!(combined_output.contains("test_subtract"));
}

#[tokio::test]
async fn test_cargo_command_result_serialization() {
    let result = verus_mcp::CargoCommandResult {
        success: true,
        exit_code: 0,
        stdout: "test output".to_string(),
        stderr: "".to_string(),
        duration_ms: 1234,
        command: vec!["cargo".to_string(), "test".to_string()],
        cwd: "/tmp/test".to_string(),
    };
    
    let serialized = serde_json::to_string(&result).unwrap();
    let deserialized: verus_mcp::CargoCommandResult = 
        serde_json::from_str(&serialized).unwrap();
    
    assert_eq!(result.success, deserialized.success);
    assert_eq!(result.exit_code, deserialized.exit_code);
    assert_eq!(result.duration_ms, deserialized.duration_ms);
}

#[tokio::test]
async fn test_timeout() {
    let (_temp_dir, project_dir) = create_dummy_project();
    let project_dir_str = project_dir.to_str().unwrap();
    
    // This test uses a very short timeout to test the timeout mechanism
    // Note: This might be flaky on very slow systems
    let result = verus_mcp::verus::VerusServer::run_cargo_command(
        project_dir_str,
        "test",
        false,
        Some("all".to_string()),
        None,
        0, // 0 second timeout - should timeout immediately
    )
    .await;
    
    // Should timeout
    assert!(result.is_err());
    let err = result.unwrap_err();
    assert!(err.contains("timed out") || err.contains("timeout"));
}

