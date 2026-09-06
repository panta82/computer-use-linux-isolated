#!/usr/bin/python3
# PANTA: persistent browser for X199; never open the primary Chrome profile.
import json,os,pathlib,sys
base=pathlib.Path.home()/'.local/share/computer-use-linux';session=base/'session'
env=json.loads((session/'environment.json').read_text())
assert (session/'ready').exists() and env['DISPLAY']==':199' and env['DBUS_SESSION_BUS_ADDRESS']==f'unix:path={session}/bus'
if any(a.startswith(('--user-data-dir','--profile-directory')) for a in sys.argv[1:]):sys.exit('Profile overrides are not allowed through this launcher')
# Chrome uses its own sandbox. Nesting this browser in the MCP bubblewrap environment failed on this laptop.
os.execve('/usr/bin/google-chrome',['google-chrome',f'--user-data-dir={base}/chrome-profile','--disable-gpu','--no-first-run','--no-default-browser-check','--force-renderer-accessibility',*sys.argv[1:]],env)
