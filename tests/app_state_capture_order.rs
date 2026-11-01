// SPDX-License-Identifier: MIT
// These fixtures exercise shared-desktop routes absent from this fork.
#![cfg(not(feature = "isolated-x11"))]

#[test]
fn app_state_refuses_unfocused_target_before_capture() {
    let status = std::process::Command::new("/usr/bin/python3")
        .arg(concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/scripts/app_state_capture_order_test.py"
        ))
        .arg(env!("CARGO_BIN_EXE_computer-use-linux"))
        .status()
        .expect("run private capture-order fixture");
    assert!(status.success());
}
