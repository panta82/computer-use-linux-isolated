//! PANTA: MPX helper calls fail closed and use fresh device IDs on every action.
use anyhow::{ensure, Context, Result};
use serde::Deserialize;
use std::path::PathBuf;
#[derive(Deserialize)]
pub(crate) struct State {
    pub focus: u64,
}
pub(crate) fn helper_path() -> PathBuf {
    PathBuf::from("/home/panta/.local/share/computer-use-linux/mpx/backend.py")
}
pub(crate) fn query(operation: &str, window: Option<u64>) -> Result<State> {
    let mut cmd = std::process::Command::new("/usr/bin/python3");
    cmd.arg(helper_path()).arg(operation);
    if let Some(id) = window {
        cmd.arg(id.to_string());
    }
    let output = crate::command_runner::output_blocking_with_timeout(
        &mut cmd,
        "MPX device check",
        std::time::Duration::from_secs(5),
    )?;
    ensure!(
        output.status.success(),
        "MPX unavailable; no shared-input fallback: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    serde_json::from_slice(&output.stdout).context("Invalid MPX helper response")
}
