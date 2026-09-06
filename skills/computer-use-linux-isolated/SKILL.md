---
name: computer-use-linux-isolated
description: Operate applications in a persistent isolated Linux X11 desktop through MCP, with separate input and a standard XFCE desktop.
metadata:
  upstream-author: agent-sh
  maintainer: panta82
---

# Isolated Linux computer use

Use the configured computer-use-linux-isolated MCP server. Run `computer-use-linux-isolated doctor` before GUI input and confirm DISPLAY is :199 and the input backend is isolated X11. If unavailable, stop and report the error. Never install or start upstream computer-use-linux as a fallback, select the host DISPLAY, create MPX devices, or enable uinput/ydotool.

The user can open `computer-use-linux-isolated desktop view` to interact. Launch applications with `computer-use-linux-isolated desktop run PROGRAM [ARGS...]` or XFCE's Applications menu. Use the provided Chrome launcher so the persistent separate profile is selected. Do not copy a running browser profile, inspect cookies/passwords, bypass a keyring, or handle MFA for the user.

List windows and observe current state before input. Check for modal dialogs, including separate windows, before retrying a click. Refresh state after an action; do not repeat blindly. Only one model should operate this desktop at a time. Coordinate with the human using the viewer; automatic takeover detection and task ownership locks are not implemented.

This desktop shares the user's files and installed applications, but has its own display, D-Bus session, desktop settings, and Chrome profile. It is input separation, not a security sandbox. Files can be modified with normal user permissions. Existing host windows and browser sessions are not transferred. Some single-instance applications, portals, snaps, or flatpaks may not support the second session. Report these limitations rather than redirecting to the host desktop.

Do not stop/restart the desktop while the user has unsaved work. App profiles and files persist across service restarts and reboots, but running windows do not. See the repository README for installation and removal.
