#!/usr/bin/python3
# PANTA: show UI on the private desktop through its own D-Bus connection.
import json,os,pathlib,sys
b=pathlib.Path.home()/'.local/share/computer-use-linux';env=json.loads((b/'session/environment.json').read_text());assert env['DISPLAY']==':199'
os.environ.clear();os.environ.update(env)
from gi.repository import Gio
app=Gio.Application(application_id='pw.pantas.AgentDesktopLauncher',flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
app.register(None)
if not app.get_is_remote():sys.exit('Agent desktop panel is not running')
sys.exit(app.run(['agent-desktop',*(sys.argv[1:] or ['menu'])]))
