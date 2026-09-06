#!/usr/bin/python3
# PANTA: host orchestration targets ONLY the disposable QEMU socket and guest SSH.
import pathlib,subprocess,json,shlex,time,socket
base=pathlib.Path.home()/'.local/share/computer-use-linux/mpx-vm'
def guest(args,env=False):
 argv=(['python3','/home/lab/mpx/vm/guest-env.py'] if env else [])+args
 return subprocess.check_output([str(base/'ssh'),shlex.join(argv)],text=True)
def qmp(cmd,args):
 s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);s.settimeout(10);s.connect(str(base/'qmp.sock'));f=s.makefile('rwb',buffering=0);json.loads(f.readline())
 def call(cmd,args):
  f.write((json.dumps({'execute':cmd,'arguments':args})+'\n').encode())
  while True:
   r=json.loads(f.readline())
   if 'error' in r:raise RuntimeError(r)
   if 'return' in r:return r['return']
 call('qmp_capabilities',{});r=call(cmd,args);f.close();s.close();return r
def human_click(x,y):
 qmp('input-send-event',{'events':[{'type':'abs','data':{'axis':'x','value':round(x/1279*32767)}},{'type':'abs','data':{'axis':'y','value':round(y/799*32767)}}]});time.sleep(.1)
 for down in (True,False):qmp('input-send-event',{'events':[{'type':'btn','data':{'down':down,'button':'left'}}]});time.sleep(.1)
def human_type(text):
 for char in text:
  qmp('send-key',{'keys':[{'type':'qcode','data':char}],'hold-time':35});time.sleep(.09)
def mcp(calls):return [json.loads(l)['result'] for l in guest(['python3','/home/lab/mpx/vm/mcp-client.py',json.dumps(calls)],True).splitlines()]
def browser():return json.loads(guest(['python3','/home/lab/mpx/vm/cdp-read.py']))
def state():return json.loads(guest(['python3','/home/lab/mpx/backend.py','state'],True))
def checkpoint(label):
 s={'label':label,'agent':state(),'chrome':browser(),'gtk':guest(['tail','-8','/home/lab/gtk-events.jsonl']),'desktop':guest(['systemctl','--user','show','plasma-plasmashell.service','plasma-kwin_x11.service','-p','MainPID','-p','NRestarts','-p','ActiveState'])}
 print(json.dumps(s),flush=True);return s
if __name__=='__main__':
 human_click(649,122) # close observed Chrome update bubble
 human_click(280,270);human_type('human')
 checkpoint('primary-browser-baseline')
 r=mcp([['get_app_state',{'app_name_or_bundle_identifier':'gtk-target.py','include_screenshot':False,'max_nodes':50}],['list_windows',{}]])
 nodes=r[0]['accessibility_tree'];w=next(w for w in r[1]['windows'] if w['title']=='MPX guest GTK target');wid=w['window_id'];b=next(n['bounds'] for n in nodes if n['name']=='GTK input')
 print(json.dumps(mcp([['click',{'window_id':wid,'x':b['x']+b['width']//2,'y':b['y']+b['height']//2}],['type_text',{'window_id':wid,'text':'agent'}]])),flush=True)
 human_type('more');checkpoint('primary-chrome-agent-gtk')
