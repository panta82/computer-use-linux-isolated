> DISABLED AFTER SESSION CRASH. See [MPX-INCIDENT.md](MPX-INCIDENT.md). Do not execute the trial or restart tests on the live desktop.

# PANTA: second-cursor trial on the main X11 desktop

This branch adds `--features mpx`, inheriting the isolated build's disabled uinput, ydotool, portals, environment hydration and shell tool. It uses the existing main X11 display and accessibility bus, so existing applications, Chrome profiles, and user files remain available.

`local/mpx/backend.py` resolves a named XI2 master pair and its exclusive XTEST slaves before every event, under a brief server grab. It sets the helper client's pointer and sends events only through that pair. No physical device is attached to it. Missing, disabled, ambiguous, or changed devices cause an error. A per-user file lock serializes helper calls. Keyboard focus is set with XISetFocus for the agent keyboard. Window activation and raising are skipped. The pair is created with sendCore=0, preventing legacy core event delivery.

Installed files live under `~/.local/share/computer-use-linux/mpx/`, with the binary at `../bin/computer-use-linux-mpx`. The wrapper is `~/.local/bin/computer-use-linux-mpx`. The user service `computer-use-linux-mpx.service` starts with graphical-session.target, reads DISPLAY/XAUTHORITY from the user service manager, and restarts on failure. The launcher also starts the service on demand. No guessed display/auth fallback. The Codex MCP command and old npm executable symlink select this wrapper. Reconnect existing MCP clients after switching; already-running clients retain their original process. The separate desktop remains available.

## Limitations

This is an experimental compatibility mode, not a security boundary or a promise that every application preserves the user's focus. Apps can maintain one internal focused widget, activate new windows, grab devices, or show modal dialogs. Two people typing in the same app can interfere. Legacy core-only apps may ignore the agent entirely. Apps can replace the cyan root cursor. Coordinate input still hits the visible window at that position; moving or covering a target during an action can change what receives the click. Screenshots do not raise windows and cannot reveal covered contents reliably.

Scrolling and dragging are explicitly disabled because application delivery was not verified. AT-SPI mutations, window move/resize, and Alt/Super chords are disabled. Text is limited to symbols already mapped in keyboard group 0; unsupported text fails before typing, without changing the keymap or clipboard. The `focused` window field refers to the agent keyboard. Action success means events were sent, so agents must verify the application result afterward.

All normal user files are accessible, including sensitive ones. The bubblewrap wrapper hides device nodes and other runtime sockets, but grants access to the main X server and session bus. The implementation enforces routing; the X11 connection itself has broader authority and is not a security sandbox.

## Verification

GTK scratch app received text, Ctrl+A, and button clicks through the named agent XTEST sources. No primary XTEST source events appeared in the observed intervals. Physical user input was active, so changing primary-focus snapshots are inconclusive. The scratch app did not confirm scroll/drag delivery; those operations are disabled rather than falling back.

`local/mpx/verify-lifecycle.py` verified missing-device refusal, stop/start recovery, crash recovery, and unchanged non-agent device attachments. A full logout/reboot was not performed. Login persistence is configured through the enabled graphical-session user unit and will require real-login validation.

## Switch or undo

Return to the separate desktop:

```
~/.local/share/computer-use-linux/mpx/select-backend.py isolated
```

Try MPX again:

```
~/.local/share/computer-use-linux/mpx/select-backend.py mpx
```

Reconnect MCP clients afterward. Switching to isolated disables/stops the MPX service and removes only its pair. To undo the entire installation, first switch to isolated, then use the original `../rollback.py`. That restores the original shared-input backend, so it removes the isolation protection deliberately.

Build with `cargo build --release --features mpx`; atomically replace the MPX binary after building. Python runtime needs libX11, libXi, libXtst, xinput, bubblewrap and systemd. Paths in Rust helper discovery are local to Panta's installation. Preserve the isolated binary when rebuilding this variant.
