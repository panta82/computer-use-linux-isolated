#!/usr/bin/python3
# PANTA: verify absence refuses input and service restart preserves physical attachments.
import os,json,pathlib,subprocess,sys,time
base=pathlib.Path.home()/'.local/share/computer-use-linux'
runtime=pathlib.Path('/run/user')/str(os.getuid())/'computer-use-mpx'
env=json.loads((runtime/'environment.json').read_text());os.environ.update(env)
sys.path.insert(0,str(base/'mpx'))
from probe import *
def snapshot():
 d=X.XOpenDisplay(None)
 try:return [r for r in devices(d) if not r['name'].startswith('Computer Use Agent ')]
 finally:X.XCloseDisplay(d)
def state():return subprocess.run(['/usr/bin/python3',str(base/'mpx/backend.py'),'state'],env=env,capture_output=True,text=True)
before=snapshot()
try:
 subprocess.run(['systemctl','--user','stop','computer-use-linux-mpx.service'],check=True)
 r=subprocess.run(['/usr/bin/python3',str(base/'mpx/backend.py'),'mousemove','100','100'],env=env,capture_output=True,text=True)
 assert r.returncode!=0 and 'no fallback' in r.stderr,r
 assert before==snapshot(),'Non-agent hierarchy changed'
 print('PASS: missing devices refuse pointer input; physical hierarchy unchanged')
finally:subprocess.run(['systemctl','--user','start','computer-use-linux-mpx.service'],check=True)
for _ in range(100):
 r=state()
 if r.returncode==0:break
 time.sleep(.1)
assert r.returncode==0,r.stderr
assert before==snapshot(),'Non-agent hierarchy changed after restart'
print('PASS: service stop/start recreates valid pair; physical hierarchy unchanged')
subprocess.run(['systemctl','--user','kill','--signal=SIGKILL','--kill-whom=main','computer-use-linux-mpx.service'],check=True)
time.sleep(3)
r=state();assert r.returncode==0,r.stderr
assert before==snapshot()
print('PASS: crash recovery restores valid agent devices and preserves physical hierarchy')
