#!/usr/bin/python3
# PANTA: start MPX on the main display; never fall back to the shared-input binary.
import os,pathlib,subprocess,json,sys,time
base=pathlib.Path.home()/'.local/share/computer-use-linux'
runtime=pathlib.Path('/run/user')/str(os.getuid())/'computer-use-mpx'
subprocess.run(['systemctl','--user','start','computer-use-linux-mpx.service'],check=True)
for _ in range(80):
 if (runtime/'ready').exists():break
 time.sleep(.1)
else:sys.exit('MPX devices unavailable; refusing shared-input fallback')
env=json.loads((runtime/'environment.json').read_text())
# Preserve the chosen X connection and read-only accessibility access, hide physical input.
display=env['DISPLAY'].split(':')[-1].split('.')[0]
if not display.isdigit():sys.exit('Only local native X11 is supported for MPX')
args=['/usr/bin/bwrap','--die-with-parent','--bind','/','/','--dev','/dev','--tmpfs','/run','--tmpfs','/tmp',
 '--bind',str(runtime),str(runtime),'--dir','/tmp/.X11-unix',
 '--ro-bind',f'/tmp/.X11-unix/X{display}',f'/tmp/.X11-unix/X{display}',
 '--ro-bind',env['XAUTHORITY'],env['XAUTHORITY'],
 '--ro-bind',f'/run/user/{os.getuid()}/bus',f'/run/user/{os.getuid()}/bus']
atspi=pathlib.Path(f'/run/user/{os.getuid()}/at-spi')
if atspi.exists():args+=['--ro-bind',str(atspi),str(atspi)]
args+=['--unshare-net','--',str(base/'bin/computer-use-linux-mpx'),*(sys.argv[1:] or ['mcp'])]
os.execve(args[0],args,env)
