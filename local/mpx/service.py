#!/usr/bin/python3
# PANTA: maintain a separate XI2 master pair; physical devices remain on the primary pair.
from probe import *
import pathlib,subprocess,time,signal,sys,fcntl
BASE=pathlib.Path.home()/'.local/share/computer-use-linux'
RUNTIME=pathlib.Path('/run/user')/str(os.getuid())/'computer-use-mpx'
RUNTIME.mkdir(mode=0o700,parents=True,exist_ok=True)
NAME='Computer Use Agent'
def desktop_environment():
 raw=subprocess.check_output(['systemctl','--user','show-environment'],text=True)
 manager=dict(line.split('=',1) for line in raw.splitlines() if '=' in line)
 env={key:os.environ[key] for key in ('HOME','USER','LOGNAME','LANG') if key in os.environ}
 for key in ('DISPLAY','XAUTHORITY','XDG_CURRENT_DESKTOP','DESKTOP_SESSION'):
  if manager.get(key):env[key]=manager[key]
 if not env.get('DISPLAY') or not env.get('XAUTHORITY'):raise RuntimeError('Main X11 session is not ready; no guessed display/auth fallback')
 env.update(PATH=f'{BASE}/runtime/usr/bin:{pathlib.Path.home()}/.local/bin:/usr/local/bin:/usr/bin:/bin',
  XDG_RUNTIME_DIR=f'/run/user/{os.getuid()}',DBUS_SESSION_BUS_ADDRESS=f'unix:path=/run/user/{os.getuid()}/bus',
  XDG_SESSION_TYPE='x11',COMPUTER_USE_MPX='1',COMPUTER_USE_MPX_NAME=NAME,COMPUTER_USE_MPX_RUNTIME=str(RUNTIME))
 return env
# Only these GUI settings are saved; no credential-bearing service environment is copied.
env=desktop_environment();os.environ.clear();os.environ.update(env)
from backend import Backend
D=X.XOpenDisplay(None)
if not D:sys.exit('Cannot open the main X11 display')
(RUNTIME/'ready').unlink(missing_ok=True)
lock=(RUNTIME/'service.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
rows=devices(D)
if any(d['name'].startswith(NAME+' ') for d in rows):
 # Adopt only a valid complete pair; never guess numeric IDs or physical attachments.
 b=Backend();b.cleanup()
else:
 subprocess.run(['xinput','create-master',NAME,'0','1'],env=env,check=True)
b=Backend()
with b.guard():
 XI.XISetFocus(b.d,b.k,0,0)
 X.XkbLockGroup(b.d,b.k,0);X.XkbLockModifiers(b.d,b.k,0xff,0)
# A cyan crosshair distinguishes the agent pointer on the desktop background.
class Color(C.Structure):
 _fields_=[('pixel',ul),('red',C.c_ushort),('green',C.c_ushort),('blue',C.c_ushort),('flags',C.c_char),('pad',C.c_char)]
sig(X,'XCreateFontCursor',[ptr,C.c_uint],ul);sig(X,'XRecolorCursor',[ptr,ul,C.POINTER(Color),C.POINTER(Color)])
sig(XI,'XIDefineCursor',[ptr,i,ul,ul])
cur=X.XCreateFontCursor(D,34);fg=Color(0,0,55000,65535,b'\x07',b'\0');bg=Color(0,0,0,0,b'\x07',b'\0')
X.XRecolorCursor(D,cur,C.byref(fg),C.byref(bg));XI.XIDefineCursor(D,b.p,X.XDefaultRootWindow(D),cur);X.XSync(D,0)
(RUNTIME/'environment.json').write_text(json.dumps(env));(RUNTIME/'ready').write_text(str(os.getpid()))
print(json.dumps({'ready':True,'pointer_id':b.p,'keyboard_id':b.k,'display':env['DISPLAY'],'core_events':False}),flush=True)
def stop(*args):raise KeyboardInterrupt
signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
try:
 while True:
  b.validate();time.sleep(1)
except KeyboardInterrupt:pass
finally:
 (RUNTIME/'ready').unlink(missing_ok=True)
 try:
  p,k=b.validate()
  subprocess.run(['xinput','remove-master',str(p),'Floating'],env=env,check=True)
 except Exception as e:print('Device cleanup skipped: '+str(e),file=sys.stderr)
 b.cleanup();X.XCloseDisplay(D)
