# Validation

Validated on 2026-09-06 in a fresh Ubuntu 25.10 x86_64 cloud-image VM with no host directories, devices, or graphical session passed through. Rust stable 1.98.1 built the release binary from Cargo.lock using the documented installer. Native dependencies came from Ubuntu's package repositories.

Checks completed:

- 281 Rust library tests passed.
- Default binary built; `--no-default-features` was rejected with the isolation-required compiler error.
- Python syntax, shell syntax, Rust formatting, and Git whitespace checks passed.
- Native XFCE panel, desktop, window manager, and accessibility bus started successfully.
- Stdio MCP initialization, tool discovery, Unicode typing, clicking, modal observation/dismissal, and screenshots passed.
- A service restart preserved a file in the persistent data directory and produced a new supervisor PID.
- Three separate MCP connections passed the GUI test while another Xvfb display's pointer remained unchanged.
- Starting with an occupied `:199` failed; it did not adopt the existing X server. Normal startup recovered after removing the fixture.
- The VM rebooted with user lingering enabled. The service started automatically, retained the persistence marker, and passed the MCP GUI smoke test again.

The test scripts intentionally require `--disposable-desktop`. Do not run the lifecycle test in a desktop containing real work: it stops the service and creates an X server on the reserved display. It expects a separate test X server on `:0`. GUI fixture dependencies, beyond the normal installer, are `python3-gi` and `gir1.2-gtk-3.0`.

```bash
python3 scripts/isolated-smoke.py --disposable-desktop
python3 scripts/isolated-lifecycle.py --disposable-desktop
```

This validates runtime and installation on the tested distro, not every installed application. Chrome login/keyring persistence, GPU applications, snap/Flatpak integration, other distributions, and ARM builds were not validated in this clean VM. No real browser profile or account credentials were copied into the test machine. The persistence test uses a marker file; it does not claim to have tested an authenticated Chrome session across reboot.
