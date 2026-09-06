#!/usr/bin/python3
# PANTA: execute only in the disposable VM, using its Plasma X11 environment.
import os,subprocess,sys,pathlib,socket
assert socket.gethostname()=='mpx-lab','Guest-only command refused'
raw=subprocess.check_output(['systemctl','--user','show-environment'],text=True)
env=dict(os.environ)
for line in raw.splitlines():
 if '=' in line:
  k,v=line.split('=',1)
  if k in ('DISPLAY','XAUTHORITY','DBUS_SESSION_BUS_ADDRESS','XDG_RUNTIME_DIR','XDG_SESSION_TYPE'):env[k]=v
assert env.get('DISPLAY') and env.get('XAUTHORITY'), 'Guest Plasma not ready'
runtime=pathlib.Path('/run/user')/str(os.getuid())/'mpx-test';runtime.mkdir(exist_ok=True)
env.update(COMPUTER_USE_MPX='1',COMPUTER_USE_MPX_RUNTIME=str(runtime),NO_AT_BRIDGE='0')
os.execvpe(sys.argv[1],sys.argv[1:],env)
