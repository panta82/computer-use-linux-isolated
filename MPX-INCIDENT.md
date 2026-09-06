# PANTA: MPX trial disabled after live-session crash, 2026-09-06

Do not run the MPX service, helpers, or lifecycle tests on the live desktop. The installed user service is masked, with its original unit backed up under ~/.local/share/computer-use-linux/backup/computer-use-linux-mpx.service.disabled-after-crash. MCP configuration and the npm executable symlink still select the separate desktop. The planned switch to MPX was never applied.

At 16:42:22 CEST, the lifecycle test stopped the service, whose cleanup removes the agent master pair, then restarted it. At the same second the kernel logged simultaneous segmentation faults in libQt6XcbQpa.so.6.9.2 for ksmserver, kactivitymanagerd, kwalletd6 and other KDE processes. Plasma and KWin also exited with SIGSEGV. At 16:42:40 the login session closed and SDDM stopped its X server. This strongly implicates the MPX hierarchy change as the trigger; the precise Qt code path has not been established with a stack trace.

The service restarted repeatedly after the X server disappeared and recreated MPX devices at 16:42:54 in the replacement login session. User reported Chrome physical input stopped working before the crash and the new login was unusable. Chrome's exact failure mechanism is not established.

Earlier passing checks only established agent input routing and unchanged physical device attachments. They did not check desktop-process survival or application compatibility. The statement that restart verification passed was therefore wrong as a claim about session safety. No further live-desktop reproduction is authorized by this incident investigation.
