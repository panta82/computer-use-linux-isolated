#!/usr/bin/python3
# PANTA: remove the optional panel and restore pre-UI launch/window configuration; retain profiles and user data.
import pathlib,subprocess,shutil,json
b=pathlib.Path.home()/'.local/share/computer-use-linux';backup=b/'backup/ui-before'
assert all((backup/n).exists() for n in ['openbox.xml','session.py','launcher.py'])
subprocess.run(['systemctl','--user','disable','--now','computer-use-linux-ui.service'],check=True)
for n in ['openbox.xml','session.py','launcher.py']:shutil.copy2(backup/n,b/n)
for path in [pathlib.Path.home()/'.local/share/applications/computer-use-linux-desktop.desktop',b/'data/applications/google-chrome.desktop',b/'data/applications/agent-files.desktop',b/'data/applications/agent-terminal.desktop']:
 if path.exists() and path.read_text().startswith('# PANTA:'):path.unlink()
for path in [b/'config/mimeapps.list',b/'config/gtk-3.0/settings.ini']:
 if path.exists() and path.read_text().startswith('# PANTA:'):path.unlink()
if (b/'session/ready').exists():
 env=json.loads((b/'session/environment.json').read_text());assert env['DISPLAY']==':199'
 subprocess.run([str(b/'runtime/usr/bin/openbox'),'--reconfigure'],env=env,check=True)
print('Panel disabled; pre-UI configuration restored. Profiles and existing apps retained. Session environment changes apply on its next restart.')
