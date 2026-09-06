#!/usr/bin/python3
# PANTA: install only the optional UI and private launchers; do not start or control the host desktop.
import pathlib,shutil,subprocess
source=pathlib.Path(__file__).parent;base=pathlib.Path.home()/'.local/share/computer-use-linux'
for name in ['desktop-ui.py','desktop-menu.py','chrome.py','menu.xml','openbox.xml']:
 shutil.copy2(source/name,base/name)
config=base/'config';apps=base/'data/applications';apps.mkdir(parents=True,exist_ok=True)
for filename,name,cmd,icon,categories in [
 ('google-chrome.desktop','Chrome',str(base/'chrome.py')+' %U','google-chrome','Network;WebBrowser;'),
 ('agent-files.desktop','Files','/usr/bin/dolphin --new-window /home/panta','system-file-manager','System;FileManager;'),
 ('agent-terminal.desktop','Terminal','xterm','utilities-terminal','System;TerminalEmulator;')]:
 text=f'# PANTA: launcher for the alternative desktop.\n[Desktop Entry]\nType=Application\nName={name}\nExec={cmd}\nIcon={icon}\nTerminal=false\nCategories={categories}\n'
 if filename=='google-chrome.desktop':text+='MimeType=text/html;x-scheme-handler/http;x-scheme-handler/https;\n'
 (apps/filename).write_text(text)
(config/'mimeapps.list').write_text('# PANTA: links in the alternative desktop use its own Chrome profile.\n[Default Applications]\ntext/html=google-chrome.desktop\nx-scheme-handler/http=google-chrome.desktop\nx-scheme-handler/https=google-chrome.desktop\ninode/directory=agent-files.desktop\n')
(config/'gtk-3.0').mkdir(exist_ok=True)
(config/'gtk-3.0/settings.ini').write_text('# PANTA: readable GTK controls and silent bells in the alternative session.\n[Settings]\ngtk-theme-name=Adwaita\ngtk-icon-theme-name=Adwaita\ngtk-enable-event-sounds=false\ngtk-enable-input-feedback-sounds=false\n')
main=pathlib.Path.home()/'.local/share/applications/computer-use-linux-desktop.desktop'
main.write_text('# PANTA: open the interactive alternative desktop.\n[Desktop Entry]\nType=Application\nName=Agent Desktop\nComment=Open the separate desktop for apps and browser setup\nExec=/home/panta/.local/bin/computer-use-linux-desktop view\nIcon=preferences-system-windows\nTerminal=false\nCategories=Utility;\nOnlyShowIn=KDE;\n')
unit=pathlib.Path.home()/'.config/systemd/user/computer-use-linux-ui.service';shutil.copy2(source/unit.name,unit)
subprocess.run(['systemctl','--user','daemon-reload'],check=True)
subprocess.run(['systemctl','--user','enable','computer-use-linux-ui.service'],check=True)
