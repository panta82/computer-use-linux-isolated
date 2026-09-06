# PANTA: computer use on this laptop

This machine uses a patched MCP on a persistent alternative X11 desktop. Read this note before desktop actions or installation changes on Panta's laptop. These instructions apply to the installed local deployment; generic upstream setup instructions below do not describe it.

## Everyday use

Use the configured `computer-use-linux` MCP. Its command must be `/home/panta/.local/bin/computer-use-linux-isolated` with argument `mcp`. Begin with `doctor` and `get_app_state`; confirm the reported display is `:199` and the input backend is the isolated X11 build. If it reports another display, shared uinput/ydotool, or MPX, stop desktop input and inspect the configuration. Do not substitute a shared-input backend to get a task done.

The desktop persists between conversations. Inspect existing windows rather than assuming a fresh session or closing/restarting it. Target the intended window before typing and verify application results after input. Do only the work authorized in the current conversation; persistent logins do not authorize additional account actions.

The panel has Applications, Chrome, Files, Terminal and Run. The user can open the interactive viewer using **Agent Desktop** in KDE's app menu or `computer-use-linux-desktop view`. Closing the viewer does not stop the desktop. To launch from a shell, `computer-use-linux-desktop run google-chrome` uses the dedicated persistent browser profile; use the panel or `computer-use-linux-desktop run PROGRAM` for other apps. Do not use the old demo launcher as the supported entrypoint.

Chrome's profile is `/home/panta/.local/share/computer-use-linux/chrome-profile`. It is separate from the user's primary Chrome profile. Do not copy cookies, reuse the main profile directory, or infer that websites are logged in. Keyring setup was cancelled during initial setup; its completion is not established by these notes. If login, MFA, or keyring unlocking is needed, ask the user to do it in the viewer and pause dependent actions. Do not ask them to paste passwords into chat or select blank/basic password storage to bypass a prompt.

Only one agent should operate this desktop at a time, and automation should pause when the user takes over. A whole-task ownership lock and automatic human-takeover detection are NOT implemented. Existing per-action serialization does not make concurrent workflows safe. Coordinate ownership when another operator is known to be active.

Normal user files are accessible. Input separation is not file/account permission isolation. Some apps need separate-instance options; appearing in Applications does not establish compatibility with two sessions.

## Maintenance

Source and local changes: `/home/panta/dev/contrib/computer-use-linux`, branch `panta/alternative-desktop`. Installed runtime: `/home/panta/.local/share/computer-use-linux`. Services: `computer-use-linux-desktop.service` and `computer-use-linux-ui.service`. Restarting just the UI preserves its launched apps; restarting the whole alternative desktop closes its windows and may lose unsaved work. Do not restart it as routine troubleshooting without first inspecting active work and considering current authorization.

The source changes disable shared-input fallbacks and host display discovery. Do not run the generic npm/Cargo reinstall instructions or replace the deployed executable with upstream during routine use. Updates need review and isolation checks before replacement. Keep the clone as the source of these patches and deployment scripts; its compiled runtime is what the MCP executes.

The main-desktop MPX experiment was abandoned after a live-session crash and failed VM compatibility tests. Its service is masked and its launcher blocked. Do not unmask it or run the old live-desktop lifecycle tests as part of normal setup or recovery.

Details, verification and scoped rollback: `/home/panta/dev/contrib/computer-use-linux/ALTERNATIVE-DESKTOP.md`. Isolation implementation: `LOCAL-ISOLATION.md` in the same repository. The full-installation rollback restores the original shared-input backend and is not a safe fallback for an unavailable alternative desktop.
