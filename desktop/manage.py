"""Session management embedded in the main executable. Never selects the host display."""
import json
import os
import pathlib
import shlex
import shutil
import subprocess
import sys
import time

NAME = 'computer-use-linux-isolated'
BASE = pathlib.Path.home() / '.local/share' / NAME
SESSION = BASE / 'session'
UNIT = NAME + '.service'
EXE = pathlib.Path(sys.argv[1]).resolve()
ARGS = sys.argv[2:]

def systemctl(*args, **kwargs):
    return subprocess.run(['systemctl', '--user', *args], **kwargs)

def install():
    required = ['bwrap', 'Xvfb', 'xauth', 'xdpyinfo', 'xset', 'xsetroot', 'dbus-daemon',
                'gdbus', 'busctl', 'xfwm4', 'xfce4-panel', 'xfdesktop', 'xfce4-appfinder',
                'xfsettingsd', 'exo-open', 'thunar', 'xfce4-terminal', 'x11vnc', 'vncviewer', 'wmctrl', 'xdotool', 'import']
    missing = [x for x in required if not shutil.which(x)]
    if missing:
        sys.exit('Missing native packages for: ' + ', '.join(missing) + '\nRun ./install.sh --dependencies first.')
    BASE.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(BASE, 0o700)
    (BASE/'session.py').write_text(os.environ['CUL_SESSION_SOURCE'])
    unitdir = pathlib.Path.home()/'.config/systemd/user'
    unitdir.mkdir(parents=True, exist_ok=True)
    unit = unitdir/UNIT
    if unit.exists() and '# Managed by computer-use-linux-isolated' not in unit.read_text():
        sys.exit('Refusing to overwrite an unmanaged service: ' + str(unit))
    # systemd quotes are different from shell quoting. Escape specifiers and paths explicitly.
    path = str(BASE/'session.py').replace('\\', '\\\\').replace('"', '\\"').replace('%', '%%')
    unit.write_text('# Managed by computer-use-linux-isolated\n# PANTA: separate X11 desktop, never the primary input session.\n[Unit]\nDescription=Isolated computer-use XFCE desktop\n[Service]\nType=simple\nExecStart=/usr/bin/python3 "'+path+'"\nRestart=on-failure\nRestartSec=3\nTimeoutStopSec=15\n[Install]\nWantedBy=default.target\n')
    launchers=BASE/'launchers';launchers.mkdir(exist_ok=True)
    chrome='''#!/usr/bin/python3
import os,pathlib,sys
base=pathlib.Path.home()/'.local/share/computer-use-linux-isolated'
if os.environ.get('DISPLAY') != ':199' or os.environ.get('XAUTHORITY') != str(base/'session/Xauthority'):
    sys.exit('Chrome launcher requires the isolated session')
if any(a.startswith(('--user-data-dir','--profile-directory')) for a in sys.argv[1:]):
    sys.exit('Browser profile overrides are forbidden')
exe='/usr/bin/google-chrome'
if not pathlib.Path(exe).exists(): sys.exit('Install Google Chrome first')
os.execv(exe,[exe,'--user-data-dir='+str(base/'chrome-profile'),'--no-first-run','--no-default-browser-check','--force-renderer-accessibility',*sys.argv[1:]])
'''
    for name in ('google-chrome','google-chrome-stable','chrome'):
        p=launchers/name;p.write_text(chrome);p.chmod(0o755)
    apps=BASE/'data/applications';apps.mkdir(parents=True,exist_ok=True)
    (apps/'google-chrome.desktop').write_text('[Desktop Entry]\nType=Application\nName=Google Chrome (isolated profile)\nExec="'+str(launchers/'google-chrome')+'" %U\nIcon=google-chrome\nCategories=Network;WebBrowser;\nMimeType=text/html;x-scheme-handler/http;x-scheme-handler/https;\n')
    (BASE/'config').mkdir(exist_ok=True)
    mime=BASE/'config/mimeapps.list'
    if not mime.exists(): mime.write_text('# PANTA: browser links use the separate persistent profile.\n[Default Applications]\nx-scheme-handler/http=google-chrome.desktop\nx-scheme-handler/https=google-chrome.desktop\ntext/html=google-chrome.desktop\n')
    entries=pathlib.Path.home()/'.local/share/applications';entries.mkdir(parents=True,exist_ok=True)
    (entries/(NAME+'.desktop')).write_text('[Desktop Entry]\nType=Application\nName=Isolated desktop\nExec="'+str(EXE)+'" desktop view\nIcon=computer\nCategories=Utility;\n')
    systemctl('daemon-reload',check=True)
    systemctl('enable',UNIT,check=True)
    print('Installed. Run '+NAME+' desktop start, then desktop view.\nMCP command: '+str(EXE)+'\nMCP args: ["mcp"]')

def environment():
    systemctl('start',UNIT,check=True)
    for _ in range(150):
        if (SESSION/'ready').is_file():
            env=json.loads((SESSION/'environment.json').read_text())
            if env.get('DISPLAY') != ':199' or env.get('XAUTHORITY') != str(SESSION/'Xauthority'):
                sys.exit('Invalid session environment; refusing fallback')
            return env
        time.sleep(.1)
    sys.exit('Isolated desktop unavailable; refusing host fallback. Check journalctl --user -u '+UNIT)

if ARGS and ARGS[0]=='desktop':
    cmd=ARGS[1] if len(ARGS)>1 else 'status'
    if cmd=='install': install();sys.exit(0)
    if cmd in ('start','stop','status'):
        if cmd=='start': environment();print('Isolated desktop ready on :199')
        else: sys.exit(systemctl(cmd,UNIT).returncode)
        sys.exit(0)
    if cmd=='uninstall':
        systemctl('disable','--now',UNIT,check=True)
        (pathlib.Path.home()/'.config/systemd/user'/UNIT).unlink(missing_ok=True)
        (pathlib.Path.home()/'.local/share/applications'/(NAME+'.desktop')).unlink(missing_ok=True)
        systemctl('daemon-reload',check=True)
        print('Service and menu entry removed. Files and profiles preserved at '+str(BASE))
        sys.exit(0)
    if cmd=='view':
        environment()
        os.execvp('vncviewer',['vncviewer','-PasswordFile',str(BASE/'view-password'),'-AcceptBell=0','127.0.0.1:99'])
    if cmd!='run' or len(ARGS)<3: sys.exit('Usage: '+NAME+' desktop run PROGRAM [ARGS...]')
    command=ARGS[2:]
    env=environment()
    if pathlib.Path(command[0]).name in ('chrome','google-chrome','google-chrome-stable'):
        os.execve(str(BASE/'launchers/google-chrome'),command,env)
    # Application networking is retained. Private endpoints still replace all inherited session variables.
    os.execvpe(command[0],command,env)
else:
    if not ARGS or ARGS[0] not in ('mcp','doctor','setup','apps','state','windows','screenshot'):
        sys.exit('Unknown command; use --help')
    env=environment()
    env['COMPUTER_USE_LINUX_INTERNAL']='1'
    command=['bwrap','--die-with-parent','--bind','/','/','--dev','/dev','--tmpfs','/run','--tmpfs','/tmp',
             '--dir','/tmp/.X11-unix','--ro-bind','/tmp/.X11-unix/X199','/tmp/.X11-unix/X199',
             '--unshare-net','--',str(EXE),*ARGS]
    os.execvpe('bwrap',command,env)
