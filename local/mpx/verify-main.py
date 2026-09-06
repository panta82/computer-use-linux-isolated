#!/usr/bin/python3
# PANTA: exercise only the disposable MPX target and record primary-device state.
import importlib.util,pathlib,json,subprocess,time,threading,re
root=pathlib.Path('/home/panta/dev/contrib/computer-use-linux')
spec=importlib.util.spec_from_file_location('original',root/'local/deployment/mcp-check.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m=c.MCP([str(pathlib.Path.home()/'.local/bin/computer-use-linux-mpx'),'mcp'])
counts={}
monitor=subprocess.Popen(['stdbuf','-oL','xinput','test-xi2','--root'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
def observe():
 for line in monitor.stdout:
  found=re.search(r'device:\s+(\d+)(?:\s+\((\d+)\))?',line)
  if found:
   source=int(found.group(2) or found.group(1));counts[source]=counts.get(source,0)+1
watcher=threading.Thread(target=observe,daemon=True);watcher.start()
try:
 state=m.tool('get_app_state',{'app_name_or_bundle_identifier':'test-app.py','include_screenshot':False,'max_nodes':100})
 nodes=state['accessibility_tree'];windows=m.tool('list_windows')['windows']
 wid=next(w['window_id'] for w in windows if w.get('title','').startswith('Agent MPX test'))
 def point(name):
  b=next(n['bounds'] for n in nodes if (n['name']==name or (name=='Test second cursor click' and n['role']=='button')));return {'x':b['x']+b['width']//2,'y':b['y']+b['height']//2}
 def act(name,args):
  before=c.host();r=m.tool(name,args);after=c.host()
  print(json.dumps({'action':name,'ok':r.get('ok'),'message':r.get('message'),'primary_before':before,'primary_after':after}),flush=True)
  assert (r.get('ok') if name not in ('scroll','drag') else not r.get('ok') and 'disabled' in r.get('message','')),r
  if before['focus']!=after['focus']: print('Primary focus changed during physical activity; focus-isolation sample is inconclusive',flush=True)
 act('click',dict(window_id=wid,**point('MPX test input')))
 act('type_text',{'window_id':wid,'text':'MPX _123'})
 act('press_key',{'window_id':wid,'key':'Ctrl+A'})
 act('type_text',{'window_id':wid,'text':'MPX ready'})
 act('click',dict(window_id=wid,**point('Test second cursor click')))
 b=next(n['bounds'] for n in nodes if n['name']=='MPX drawing area')
 act('scroll',{'window_id':wid,'x':b['x']+100,'y':b['y']+40,'direction':'down','pages':1})
 act('drag',{'start_x':b['x']+100,'start_y':b['y']+40,'end_x':b['x']+200,'end_y':b['y']+60})
 events=[json.loads(line) for line in (pathlib.Path.home()/'.local/share/computer-use-linux/mpx/main-test.jsonl').read_text().splitlines()]
 assert any(e.get('value')=='MPX ready' for e in events)
 for kind in ('click',):assert any(e['kind']==kind for e in events),kind
 print('PASS: application received click, text, Ctrl+A; scroll and drag refuse input; see primary-focus samples')
finally:
 m.close();monitor.terminate();monitor.wait();watcher.join(timeout=1)
 print('Host XI2 source counts, no keycodes recorded:',counts)
 assert not counts.get(4) and not counts.get(5),'Primary XTEST activity detected'
