# Panta's isolated X11 deployment

Installed on 2026-09-06 from upstream commit `c9ab855` on local branch
`panta/isolated-x11`. This is a dedicated Xvfb desktop at `:199`, with its own
cursor, keyboard focus, authentication cookie, D-Bus session and AT-SPI bus.
It does **not** control existing windows on the main desktop.

## Use

New MCP connections use `/home/panta/.local/bin/computer-use-linux-isolated mcp`.
Reconnect existing clients after installation. Old shared-input MCP processes
were stopped, and their cached executable path redirects to the isolated launcher.

View and interact with the agent desktop. Clipboard sharing remains disabled:

```sh
computer-use-linux-desktop view
```

Launch an app inside it:

```sh
computer-use-linux-desktop run xterm -e bash --noprofile --norc
```

For a browser, use a separate profile to avoid forwarding the launch to an
existing browser instance:

```sh
computer-use-linux-desktop run google-chrome --user-data-dir=/home/panta/.local/share/computer-use-linux/chrome-profile --disable-gpu
```

App launches keep network access and normal read/write access to the user's files,
subject to normal Unix permissions. `/dev`, `/run`, and `/tmp` remain isolated to
keep physical input and host session sockets out of the desktop. Configuration,
cache and data use separate XDG directories. Existing app logins and running
sessions are not automatically reused.
The browser example is a launch recipe, not a verified browser compatibility test.

## Management

```sh
systemctl --user status computer-use-linux-desktop.service
journalctl --user -u computer-use-linux-desktop.service
systemctl --user restart computer-use-linux-desktop.service
computer-use-linux-isolated doctor
```

The service is enabled under the user `default.target`. It starts with the user
manager and is also started on demand by the launcher. It does not require the
main desktop's DISPLAY or temporary Xauthority file. An Xvfb, D-Bus, Openbox or
viewer exit restarts the complete session. Application processes/windows are lost
when the X server restarts; relaunch apps and reconnect MCP after that event.
This does not promise restoration of unsaved application state.

The interactive VNC server listens only on `127.0.0.1:5999`, uses a local password
file with mode 0600, and has clipboard sharing disabled on the server. The view
command opens a viewer only when explicitly invoked. No viewer was opened during
installation.

## Implementation and boundaries

Upstream `src/server.rs` prefers a shared uinput pointer, uses xdotool/ydotool
fallbacks, and activates target windows. `src/diagnostics.rs` also discovers desktop
connection settings from other processes and systemd. Merely changing DISPLAY
would leave those paths available.

The `isolated-x11` Cargo feature makes the deployment binary:

- Reject missing dedicated-session settings, DISPLAY other than `:199`, Wayland,
  and shell-tool enablement before startup.
- Skip host desktop environment discovery.
- Forbid uinput and ydotool, even if installed or explicitly forced.
- Use X11 input only, with no fallback on backend or connection failure.
- Send scrolling and dragging through xdotool, filling upstream's missing X11 paths.
- Capture screenshots directly from its X display with ImageMagick `import`, never
  through desktop portals or GNOME screenshot services.
- Disable GNOME extension installation and the optional shell MCP tool.
- Report the isolated backend in doctor capabilities.
- Delay non-ASCII typing by 25 ms per character so clients receive temporary XKB
  mappings before xdotool removes them. ASCII typing keeps the upstream zero delay.

Bubblewrap gives MCP a private network namespace, hides physical input devices,
`/run`, and host filesystem X sockets, and exposes only the X199 socket. Thus host
abstract X sockets and shared ydotool/session-bus sockets are unavailable too.
The server uses a separate private D-Bus/AT-SPI bus. Apps use the same dedicated
session and hidden devices, but retain network access.

This provides input separation for this configured tool, not a security boundary
against deliberately hostile code running as the same Unix user. The desktop uses
software rendering at 1600x1000; GPU-heavy apps and some toolkits may have limitations.
The pointer is visible in the viewer; upstream screenshot images do not include a
cursor overlay.

MPX was considered but not used. A second master pointer separates pointer state,
but clients and the window manager still share the X server. X.Org documents
ClientPointer and grab restrictions for applications not designed for multiple
pointers: https://www.x.org/Development/Documentation/MPX/
Those restrictions do not provide the requested strict focus separation on the
existing desktop. Upstream: https://github.com/agent-sh/computer-use-linux

## Verification

- 281 unit tests passed across the suite and the retry of one unrelated wtype
  test that transiently returned ETXTBSY. The standard build also passes
  `cargo check --locked`.
- Real stdio MCP initialize, tool discovery, doctor, AT-SPI tree extraction,
  window targeting and screenshots pass.
- A disposable GTK app received pointer clicks, five scroll events, drag press /
  release, Ctrl+A replacement, ASCII and Serbian Unicode text.
- Host keyboard focus stayed unchanged during tested input actions. Host XI2
  source monitoring recorded physical input while the user worked, with **zero
  events from host XTEST devices 4 and 5**. Independent human pointer movement was
  logged as such, not attributed to the agent.
- The input test passed again after a complete service restart.
- Missing xdotool fails all five input tools. A fake ydotool executable was not
  invoked. Stopping Xvfb makes existing MCP input calls fail without shared input.
- A fresh MCP process starts a stopped desktop and restores readiness. Deliberately
  killing Xvfb caused automatic recovery with a new supervisor PID and all doctor
  readiness checks passing.
- Both the configured command and the old cached executable path reach `:199`.
  An explicit DISPLAY=:0 override is rejected.
- Service enablement and the local-only viewer listener were verified. The laptop
  was **not rebooted** and the real graphical session was not restarted.

Test scripts are in `local/deployment/`. Captured reports are in `local/*.log` and
`local/*doctor.json` in this checkout, excluded from Git. Tests that stop or crash
the service close agent desktop apps; use them only when its windows are disposable.

## Follow-up: file access and interaction

The user requested normal file access and interactive viewing after trying the
initial setup. The launcher now mounts ordinary files read/write and enables
viewer keyboard and pointer events. The VNC server no longer forces view-only mode.
The application PATH includes user and system commands. Separate X11/DBus sessions,
private input devices, and the patched server's no-fallback behavior are unchanged.
A temporary file was successfully written/read/deleted inside `~/dev` from the
app launcher; `/dev/uinput` remained absent. The service was restarted with the
new configuration and its terminal reopened. Reopen the viewer using the view
command, since an existing viewer may retain its old read-only options.
Backups of the previous scripts are under `backup/*.before-full-files`.

## Updating

The deployment is pinned and does not follow npm updates. Runtime programs were
extracted from Ubuntu packages into `~/.local/share/computer-use-linux/runtime`,
without sudo or changing system packages. `local/runtime-packages.txt` records
package versions and `local/runtime-sha256.txt` records archive hashes.

Rebuild the patched binary:

```sh
cd /home/panta/dev/contrib/computer-use-linux
cargo build --locked --features isolated-x11 --bin computer-use-linux
install -m755 target/debug/computer-use-linux /home/panta/.local/share/computer-use-linux/bin/computer-use-linux.new
strip /home/panta/.local/share/computer-use-linux/bin/computer-use-linux.new
mv /home/panta/.local/share/computer-use-linux/bin/computer-use-linux.new /home/panta/.local/share/computer-use-linux/bin/computer-use-linux
```

Reconnect MCP clients to load a new binary. Deployment scripts and the unit have
source copies under `local/deployment/`. Reinstall those copies after editing and
restart the service. Stop the service before replacing runtime executable/library
files. Reapply/review this patch before moving to a newer upstream release.

## Rollback

This command deliberately restores the original **shared-input** behavior:

```sh
/home/panta/.local/share/computer-use-linux/rollback.py
```

It restores only the MCP command, preserving unrelated configuration changes;
restores the original npm executable; disables/removes the service; and removes
the two launcher links. It checks for intervening edits before restoring. Reconnect
MCP clients afterward. Backups and isolated app data are retained at
`~/.local/share/computer-use-linux/backup` and its parent. The checkout remains.
The full original Codex config backup is mode 0600 and may contain credentials;
use the stanza-only `mcp-original.json` for manual restoration where possible.
No AGENTS.md or existing desktop settings were changed.
