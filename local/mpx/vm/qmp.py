#!/usr/bin/python3
# PANTA: guest virtual input only, no host X connection.
import json,socket,pathlib,sys
path=pathlib.Path.home()/'.local/share/computer-use-linux/mpx-vm/qmp.sock'
s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);s.settimeout(10);s.connect(str(path));f=s.makefile('rwb',buffering=0)
def call(cmd,args=None):
 f.write((json.dumps({'execute':cmd,'arguments':args or {}})+'\n').encode())
 while True:
  r=json.loads(f.readline())
  if 'error' in r:raise RuntimeError(r)
  if 'return' in r:return r['return']
json.loads(f.readline());call('qmp_capabilities')
print(json.dumps(call(sys.argv[1],json.loads(sys.argv[2]) if len(sys.argv)>2 else {})))
