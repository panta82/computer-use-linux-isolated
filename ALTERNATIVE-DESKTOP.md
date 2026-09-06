# PANTA: usable alternative desktop

Open **Agent Desktop** from KDE's application menu, or run `computer-use-linux-desktop view`. The interactive viewer connects to the separate X199 desktop. It has its own pointer and keyboard focus. The main-desktop MPX experiment remains disabled and masked.

The top panel provides **Applications**, **Chrome**, **Files**, **Terminal**, and **Run**. Applications searches system and user desktop entries, including installed app launchers under ~/.local/share/applications. Files opens Dolphin at your normal home directory. The taskbar brings existing alternative-session windows forward. Normal Openbox mouse bindings restore dragging, resizing, closing, minimizing, and maximizing windows. Right-click the background for a menu. Alt-F2 opens Run and Ctrl-Alt-T opens a terminal inside the alternative session; the VNC viewer must receive those keys rather than the main window manager.

## Browser sessions

The Chrome button always uses `~/.local/share/computer-use-linux/chrome-profile`. The command `computer-use-linux-desktop run google-chrome` now uses the same launcher and profile. Chrome uses its own sandbox because nesting it inside the original app bubblewrap wrapper did not work on this laptop. The MCP's input isolation remains unchanged.

Sign into websites in that Chrome window. The profile is persistent across browser and desktop restarts; it is not a disposable guest profile. Chrome may ask you to create a **Default Keyring** password for the alternative session. Choose that password yourself in the viewer. After a fresh desktop session, it may need unlocking again because this session is not unlocked through your normal desktop login. No password was chosen, no main-profile credentials were copied, and no plaintext-password-storage flag was added during setup.

This is a separate browser session. It cannot concurrently open the main Chrome profile or automatically reuse all its live website logins. [Chromium documents that one instance cannot span multiple X displays and simultaneous instances cannot share a user-data directory](https://chromium.googlesource.com/chromium/src/%2Bshow/1482000/docs/user_data_dir.md). Signing into Chrome can make supported account data such as bookmarks and saved passwords available, with history and tabs depending on your sync settings; that is not the same as sharing every site's current login cookie. [Chrome account help](https://support.google.com/chrome/answer/165139?hl=en).

## Files, apps and limits

Your normal files are available with your normal Unix permissions. Application configuration, cache, session bus and application data use separate XDG locations. The same installed program is available, but its already-running main-desktop instance and settings are not automatically transferred. Some apps implement their own singleton or IPC behavior and may need an app-specific separate-instance option. Chrome is explicitly handled. The Applications list is a launch catalog, not a claim that every installed app has been compatibility-tested.

Clipboard sharing between the viewer and host remains disabled. Both sessions can access the same files. The desktop is software-rendered and has a fixed 1600×1000 size. Restarting the whole alternative desktop closes its windows; persistent files and browser profile remain, but unsaved state is not guaranteed. No automatic credential synchronization or app-session restoration was added.

## Verification and management

The MCP accessibility tree exposes the panel buttons and application search. UI clicks launched Chrome and Dolphin on X199, and searching for xterm launched a terminal. Alt-F2 opened the Run dialog. Restarting the UI service preserved the terminal and Dolphin PIDs. Restarting the complete alternative-desktop service restored the panel automatically and left main Plasma/KWin PIDs and restart counts unchanged. The isolated MCP doctor passed afterward. A new full laptop reboot was not performed for this UI change.

The panel uses the existing Python GTK/Gio libraries and its own user service, `computer-use-linux-ui.service`, enabled as a dependency of the existing separate-desktop service. It does not require installing another host desktop environment. `KillMode=process` lets a panel restart preserve apps launched from it; stopping the whole separate desktop closes clients by terminating its X server.

```
systemctl --user status computer-use-linux-ui.service
journalctl --user -u computer-use-linux-ui.service
systemctl --user restart computer-use-linux-ui.service
```

Source is in `local/deployment/desktop-ui.py`, `desktop-menu.py`, `chrome.py`, and `ui-install.py`. The profile and UI state live under ~/.local/share/computer-use-linux. Verification artifacts are in that directory's ui-verification subdirectory.

To disable the optional UI and restore the previous window-manager/launcher configuration while preserving user files, browser profile and existing application processes:

```
~/.local/share/computer-use-linux/ui-rollback.py
```

The pre-UI configuration is backed up in `backup/ui-before/`. This rollback does not re-enable MPX or restore shared-input control. To remove the entire older isolated-desktop installation, first consult its separate rollback instructions; that operation has a different scope.
