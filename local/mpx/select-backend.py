#!/usr/bin/python3
# PANTA: reversible choice between MPX trial and the existing isolated desktop.
import pathlib,re,os,subprocess,sys
mode=sys.argv[1] if len(sys.argv)==2 else ''
if mode not in ('mpx','isolated'):sys.exit('Usage: select-backend.py mpx|isolated')
home=pathlib.Path.home();base=home/'.local/share/computer-use-linux'
config=home/'.codex/config.toml';text=config.read_text()
pattern=r'(?ms)^\[mcp_servers\.computer-use-linux\]\n.*?(?=^\[|\Z)'
m=re.search(pattern,text)
if not m:sys.exit('MCP section missing; configuration left unchanged')
section=m.group();old=re.search(r'^command\s*=\s*"([^"]+)"',section,re.M)
allowed=[str(home/'.local/bin'/('computer-use-linux-'+x)) for x in ('mpx','isolated')]
if not old or old.group(1) not in allowed:sys.exit('Unexpected MCP command; configuration left unchanged')
legacy=home/'.nvm/versions/node/v24.4.1/lib/node_modules/@agent-sh/computer-use-linux/npm/bin/computer-use-linux-linux-x64'
if not legacy.is_symlink():sys.exit('Unexpected legacy executable; configuration left unchanged')
command=home/'.local/bin'/('computer-use-linux-'+mode)
subprocess.run(['systemctl','--user','start','computer-use-linux-'+('mpx' if mode=='mpx' else 'desktop')+'.service'],check=True)
section=section[:old.start()]+f'command = "{command}"'+section[old.end():]
if '# PANTA: MPX' not in section:section+='# PANTA: MPX trial is reversible with select-backend.py isolated.\n'
backup=base/'backup/config.toml.before-mpx'
if not backup.exists():
 backup.touch(mode=0o600);backup.write_text(text)
updated=text[:m.start()]+section+text[m.end():]
temp=config.with_name(config.name+'.mpx-tmp');temp.write_text(updated);temp.chmod(0o600);temp.replace(config)
tmp=legacy.with_name(legacy.name+'.mpx-tmp');tmp.unlink(missing_ok=True);tmp.symlink_to(base/'mpx/launcher.py' if mode=='mpx' else base/'launcher.py');tmp.replace(legacy)
if mode=='mpx':subprocess.run(['systemctl','--user','enable','computer-use-linux-mpx.service'],check=True)
else:subprocess.run(['systemctl','--user','disable','--now','computer-use-linux-mpx.service'],check=True)
print('Selected '+mode+'. Reconnect MCP clients to load the selected backend.')
