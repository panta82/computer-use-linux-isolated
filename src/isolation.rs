//! PANTA: the deployment binary fails closed without the dedicated session.
use anyhow::{ensure, Result};

pub(crate) fn validate_environment() -> Result<()> {
    if cfg!(feature = "mpx") {
        ensure!(
            std::env::var("COMPUTER_USE_MPX").as_deref() == Ok("1"),
            "MPX launcher is required; no fallback"
        );
        ensure!(
            std::env::var("XDG_SESSION_TYPE").as_deref() == Ok("x11"),
            "MPX requires native X11"
        );
        ensure!(
            std::env::var("WAYLAND_DISPLAY")
                .unwrap_or_default()
                .is_empty(),
            "MPX refuses Wayland"
        );
        crate::mpx::query("state", None)?;
        return Ok(());
    }
    let runtime = std::env::var("COMPUTER_USE_LINUX_SESSION_DIR")?;
    ensure!(
        runtime.starts_with('/') && runtime.ends_with("/computer-use-linux/session"),
        "Invalid isolated session directory"
    );
    for (key, expected) in [
        ("DISPLAY", ":199".to_owned()),
        ("XAUTHORITY", format!("{runtime}/Xauthority")),
        (
            "DBUS_SESSION_BUS_ADDRESS",
            format!("unix:path={runtime}/bus"),
        ),
        ("XDG_RUNTIME_DIR", runtime.clone()),
        ("XDG_SESSION_TYPE", "x11".to_owned()),
        ("COMPUTER_USE_LINUX_ISOLATED", "1".to_owned()),
    ] {
        ensure!(
            std::env::var(key).ok().as_deref() == Some(expected.as_str()),
            "{key} must identify the isolated session; refusing host fallback"
        );
    }
    ensure!(
        std::env::var("WAYLAND_DISPLAY")
            .unwrap_or_default()
            .is_empty(),
        "Wayland is forbidden in isolated X11 mode"
    );
    ensure!(
        std::path::Path::new(&format!("{runtime}/ready")).is_file(),
        "Isolated desktop is not ready; refusing host fallback"
    );
    ensure!(
        std::env::var("COMPUTER_USE_LINUX_ENABLE_SHELL").unwrap_or_default() != "1",
        "Shell tool forbidden in isolated deployment"
    );
    Ok(())
}
