# Validation

## Upstream rebase and desktop fixes, 2026-11-01

Rebased the seven fork commits onto `agent-sh/computer-use-linux` commit `3175c045a68011235bcefb8b60305204c7a14729`, version 0.7.35. The fork's mandatory isolated X11 feature, persistent XFCE service, private XDG settings, Chrome profile and VNC setup remain in place.

Validation completed with the release binary in a disposable Ubuntu 24.04 x86_64 KVM guest:

1. `cargo test --locked` passed, including 631 library tests, the binary unit tests and applicable integration tests. Tests specifically requiring upstream's shared-desktop executable, Pixelflux input or enabled shell execution are gated out of the mandatory isolated build. Isolation tests verify that those routes remain disabled.
2. Release compilation, Rust formatting, Python syntax, shell syntax and Git whitespace checks passed. Six Python tests cover service-bus routing, private runtime directories and X-server ownership. Building with `--no-default-features` still fails with the required isolation error.
3. Stdio MCP discovery, Unicode typing, clicking, modal observation/dismissal and native X11 screenshots passed. Post-action screenshot capture also passed.
4. The native-focus regression passed with `_NET_ACTIVE_WINDOW` deliberately stale and then removed. Targeted input succeeded while preserving the actual X11 focus.
5. Restart persistence, three MCP reconnects, an unchanged pointer on a separate `:0` display, refusal of an occupied `:199`, and recovery after the conflicting server exited all passed.
6. The stock `xfdesktop` 4.18.1 emitted 20 missing-`standard::name` warnings with 20 fixture Trash entries. The privately built upstream backport emitted none with the same entries. All 20 entries remained intact. The running executable was verified under the isolated desktop's private runtime directory.
7. The headless installer accepted the backport and placed it in the private runtime directory. This installer check reused the already-built release artifact through a Cargo stub; Rust compilation was tested separately with the real toolchain.

The guest initially lacked the bubblewrap AppArmor user-namespace allowance already installed on the host. The test guest received the same executable-scoped profile. No host AppArmor or kernel settings changed. The host's running isolated desktop was not restarted or upgraded during validation. This run did not test real Chrome account persistence, GPU applications, snap/Flatpak integration, other distributions or a guest reboot.

## Original packaging, 2026-09-06

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
