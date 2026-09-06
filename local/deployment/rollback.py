#!/usr/bin/python3
# PANTA: explicitly restore the original shared-input MCP setup; keep data/backups.
import json, os, pathlib, re, shutil, signal, subprocess
base=pathlib.Path.home()/'.local/share/computer-use-linux'
original=json.loads((base/'backup/mcp-original.json').read_text())
config=pathlib.Path.home()/'.codex/config.toml'
s=config.read_text()
new='command = "/home/panta/.local/bin/computer-use-linux-isolated"'
assert new in s, 'MCP config changed since installation; restore its computer-use-linux entry manually from backup/mcp-original.json'
legacy=pathlib.Path(original['command'])
assert legacy.is_symlink() and legacy.resolve()==base/'launcher.py', 'Legacy executable changed; inspect backup before restoring it'
subprocess.run(['systemctl','--user','disable','--now','computer-use-linux-desktop.service'],check=True)
for proc in pathlib.Path('/proc').iterdir():
    if not proc.name.isdigit():continue
    try:
        args=(proc/'cmdline').read_bytes().split(b'\0')
        if args[:2]==[str(base/'bin/computer-use-linux').encode(),b'mcp']:
            os.kill(int(proc.name),signal.SIGTERM)
    except (FileNotFoundError,PermissionError,ProcessLookupError):pass
restore=legacy.with_name(legacy.name+'.restore')
shutil.copy2(base/'backup/computer-use-linux-original',restore);os.replace(restore,legacy)
s=s.replace('# PANTA: dedicated X11/DBus desktop; shared input fallback is forbidden.\n','').replace(new,'command = '+json.dumps(original['command']))
config.write_text(s)
(pathlib.Path.home()/'.config/systemd/user/computer-use-linux-desktop.service').unlink()
subprocess.run(['systemctl','--user','daemon-reload'],check=True)
for name in ('computer-use-linux-isolated','computer-use-linux-desktop'):
    p=pathlib.Path.home()/'.local/bin'/name
    if p.is_symlink() and p.resolve()==base/'launcher.py':p.unlink()
print('Original MCP restored. It controls shared input again. Reconnect MCP clients. Backups and isolated app data retained at '+str(base))
