# PANTA: MPX before Plasma, disposable VM results

Tested on 2026-09-06. Creating the MPX pair before Plasma started avoided a crash in these short tests, including one guest reboot and three MCP reconnects. It did not provide independent input across the existing application stack. The host MPX service remains masked and its launcher remains blocked. The VM was shut down after collecting results.

## Environment and method

Ubuntu 25.10 official cloud image, verified against the published SHA256SUMS. Installed Plasma workspace 4:6.4.5-0ubuntu4 and Qt GUI 6.9.2+dfsg-1ubuntu1, matching the laptop. Copied only /opt/google/chrome program files for Chrome 146.0.7680.164; used a new guest profile. QEMU/KVM had 4 GiB RAM, two vCPUs, no shared folders, no forwarded SSH agent and no host input device passthrough. Primary keyboard and mouse input came from QEMU virtual hardware via its private Unix QMP socket. Agent input came from the MPX helper or the modified MCP inside the guest. All assertions about primary input in this report refer to the VM's primary input, not the laptop's.

SDDM's DisplayCommand created `Computer Use Agent` using `xinput create-master 'Computer Use Agent' 0 1` before starting the Plasma session. The pair stayed alive throughout the session; MCP exits did not remove it. The pair was recreated only when a new guest X server started after reboot. This tests the early-creation hypothesis without repeating live device removal.

## Observations

| Check | Result |
| --- | --- |
| Start Plasma with pair already present | Plasma and KWin active, zero service restarts during checks |
| Primary keyboard in GTK | Application text log confirmed input |
| Primary keyboard in Chrome with MPX present | Click reached input, but no DOM key events or text arrived |
| Agent keyboard in Chrome | DOM key/input events and expected text arrived |
| Agent uses Chrome while primary keyboard types into GTK | Both reached their intended applications |
| Three fresh MCP connections, typing through each | Text appended; agent pair IDs and primary focus unchanged; desktop PIDs unchanged |
| Agent types in Chrome HTML modal, primary types in GTK | Both application readbacks confirmed expected text |
| Agent opens Chrome native select popup, primary types in GTK | Popup observed in screenshot; primary GTK text continued |
| Agent opens GTK modal while primary focus is Chrome | FAILED: primary focus changed from Chrome to GTK's modal |
| Reboot with MPX pair created before Plasma again | Desktop started; primary keyboard still ignored by Chrome |
| Reboot same VM without creating MPX pair | Same virtual primary keyboard successfully typed `baseline` into Chrome |

The GTK modal focus transition was 4194308 to 37750828 while only agent MPX input opened the dialog. This is direct evidence that using separate devices does not stop applications and the window manager from changing the primary focus.

## Chrome mechanism

In [Chromium 146.0.7680.164 touch_factory_x11.cc](https://github.com/chromium/chromium/blob/146.0.7680.164/ui/events/devices/x11/touch_factory_x11.cc#L143), the device enumeration assigns `virtual_core_keyboard_device_` for every master keyboard. The event filter then accepts key events only from that one saved ID. In this guest, the last master keyboard is the added agent keyboard. This explains why the agent keyboard works while the original keyboard is ignored. The same pattern was also present in the main-branch file fetched during this investigation. A primary-only selection fix would still exclude the agent; full multi-keyboard support needs a different filter and further focus/grab testing.

## MCP finding

The guest exposed another MPX integration bug: KWin's internal UUID hashes were being used where XISetFocus requires an actual X11 window ID. The experimental source now forces X11 window enumeration for the MPX feature. A debug build was installed only in the guest. Rust tests passed: 281 library tests, 7 CLI smoke tests and 1 additional integration test. These checks validate the source change, not desktop compatibility.

## Conclusion and limits

Early creation is a promising way to avoid the observed device-removal crash, but this experiment is not a long-term stability guarantee. It does not reproduce the laptop's GPU, user configuration, extensions, workloads, suspend/resume or every modal/grab behavior. The test failed the intended independent-input requirement even without a crash. Deployment on the live laptop is not recommended. Moving forward would require Chromium input handling changes and a solution for application/window-manager focus stealing, followed by more guest testing.

## Artifacts and reversibility

VM disk, downloaded image, isolated SSH key, SHA256SUMS, logs and screenshots are under `~/.local/share/computer-use-linux/mpx-vm/`. Evidence includes `phase2.jsonl`, `phase3.jsonl`, `gtk-modal.json`, `reboot-with-mpx.json`, `baseline-without-mpx.json`, `guest-first-boot.log` and `guest-mpx-reboot.log`. Guest shutdown releases its RAM. It has no autostart entry or libvirt definition. Removing that directory after ensuring its `mpx-vm` screen session is stopped removes the VM.

Provisioning and diagnostic scripts are in `local/mpx/vm/`. Some phase scripts contain window IDs and coordinates observed in the first guest session; they are records of that test, not an unattended regression suite to run against an arbitrary session. Host orchestration uses only the VM SSH endpoint and QMP socket. Guest input helpers check the guest hostname. Do not use the older live-desktop lifecycle test on the laptop.
