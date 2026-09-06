#!/usr/bin/python3
# PANTA: exercise the deployed stdio MCP with a disposable isolated GTK app.
import json, pathlib, subprocess, select, time, ctypes, threading, re
base=pathlib.Path.home()/'.local/share/computer-use-linux'
log=base/'test-events.jsonl'
class MCP:
    def __init__(self, command=None):
        self.p=subprocess.Popen(command or [str(pathlib.Path.home()/'.local/bin/computer-use-linux-isolated'),'mcp'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=open(base/'mcp-test.stderr','w'),text=True,bufsize=1)
        self.i=0
        self.request('initialize',{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'isolation-verifier','version':'1'}})
        self.p.stdin.write(json.dumps({'jsonrpc':'2.0','method':'notifications/initialized'})+'\n');self.p.stdin.flush()
    def request(self,method,params):
        self.i+=1
        self.p.stdin.write(json.dumps({'jsonrpc':'2.0','id':self.i,'method':method,'params':params})+'\n');self.p.stdin.flush()
        end=time.monotonic()+40
        while time.monotonic()<end:
            ready,_,_=select.select([self.p.stdout],[],[],max(0,end-time.monotonic()))
            if not ready: break
            line=self.p.stdout.readline()
            if not line: raise RuntimeError('MCP exited: '+str(self.p.poll()))
            data=json.loads(line)
            if data.get('id')==self.i:
                if 'error' in data: raise RuntimeError(data['error'])
                return data['result']
        raise TimeoutError(method)
    def tool(self,name,args={}):
        result=self.request('tools/call',{'name':name,'arguments':args})
        if result.get('isError'): raise RuntimeError(result)
        if 'structuredContent' in result: return result['structuredContent']
        texts=[c['text'] for c in result.get('content',[]) if c.get('type')=='text']
        for t in texts:
            try:return json.loads(t)
            except ValueError:pass
        return texts
    def close(self):
        self.p.stdin.close()
        try:self.p.wait(timeout=5)
        except subprocess.TimeoutExpired:self.p.terminate();self.p.wait()
# Read-only host state through Xlib. No event synthesis on :0.
x=ctypes.CDLL('libX11.so.6');x.XOpenDisplay.argtypes=[ctypes.c_char_p];x.XOpenDisplay.restype=ctypes.c_void_p
x.XDefaultRootWindow.argtypes=[ctypes.c_void_p];x.XDefaultRootWindow.restype=ctypes.c_ulong
x.XQueryPointer.argtypes=[ctypes.c_void_p,ctypes.c_ulong,ctypes.POINTER(ctypes.c_ulong),ctypes.POINTER(ctypes.c_ulong),ctypes.POINTER(ctypes.c_int),ctypes.POINTER(ctypes.c_int),ctypes.POINTER(ctypes.c_int),ctypes.POINTER(ctypes.c_int),ctypes.POINTER(ctypes.c_uint)]
x.XGetInputFocus.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_ulong),ctypes.POINTER(ctypes.c_int)]
d=x.XOpenDisplay(b':0');assert d
root=x.XDefaultRootWindow(d)
def host():
    r=ctypes.c_ulong();c=ctypes.c_ulong();rx=ctypes.c_int();ry=ctypes.c_int();wx=ctypes.c_int();wy=ctypes.c_int();m=ctypes.c_uint();f=ctypes.c_ulong();revert=ctypes.c_int()
    x.XQueryPointer(d,root,ctypes.byref(r),ctypes.byref(c),ctypes.byref(rx),ctypes.byref(ry),ctypes.byref(wx),ctypes.byref(wy),ctypes.byref(m));x.XGetInputFocus(d,ctypes.byref(f),ctypes.byref(revert))
    return {'pointer':[rx.value,ry.value],'focus':f.value}
if __name__=='__main__':
    # Count source IDs only. Never retain host keycodes, text, or coordinates from events.
    monitor=subprocess.Popen(['stdbuf','-oL','xinput','test-xi2','--root'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
    counts={}
    def observe():
        for line in monitor.stdout:
            match=re.search(r'device:\s+(\d+)(?:\s+\((\d+)\))?',line)
            if match:
                source=int(match.group(2) or match.group(1)); counts[source]=counts.get(source,0)+1
    watcher=threading.Thread(target=observe,daemon=True);watcher.start()
    m=MCP()
    try:
        tools=m.request('tools/list',{})
        (base/'mcp-tools.json').write_text(json.dumps(tools,indent=2))
        report=m.tool('doctor');print('doctor',json.dumps(report.get('readiness',report)),flush=True)
        windows=m.tool('list_windows');print('windows',json.dumps(windows),flush=True)
        state=m.tool('get_app_state',{'app_name_or_bundle_identifier':'test-app.py','include_screenshot':False})
        (base/'mcp-state.json').write_text(json.dumps(state,indent=2))
        print('state saved',flush=True)
        w=next(w for w in windows['windows'] if w['title']=='Computer Use isolation verification')
        wid=w['window_id']
        def act(name,args):
            before=host(); result=m.tool(name,args); after=host()
            print(json.dumps({'action':name,'result':result,'host_before':before,'host_after':after}),flush=True)
            assert isinstance(result,dict) and result.get('ok',True),result
            assert before['focus']==after['focus'], 'Host focus changed during test; inspect for concurrent user activity'
            if before['pointer']!=after['pointer']: print('Host pointer moved independently during test; checking XTEST sources separately',flush=True)
        nodes=state['accessibility_tree']
        def point(name):
            b=next(n['bounds'] for n in nodes if n['name']==name)
            return {'x':b['x']+b['width']//2,'y':b['y']+b['height']//2}
        act('click',dict(window_id=wid,**point('Isolated text target')))
        act('press_key',{'window_id':wid,'key':'Ctrl+A'})
        act('type_text',{'window_id':wid,'text':'Isolation check _123 žđčćš'})
        act('press_key',{'window_id':wid,'key':'Ctrl+A'})
        act('type_text',{'window_id':wid,'text':'restart-safe-input'})
        act('click',dict(window_id=wid,**point('Verify isolated click')))
        act('scroll',{'window_id':wid,'x':350,'y':350,'direction':'down','pages':1})
        act('drag',{'start_x':300,'start_y':350,'end_x':500,'end_y':400})
        act('activate_window',{'window_id':wid})
        before=host(); shot=m.tool('screenshot',{'window_id':wid}); after=host()
        assert before['focus']==after['focus']
        print('targeted screenshot received; host unchanged',flush=True)
        time.sleep(.2)
        events=[json.loads(line) for line in log.read_text().splitlines()]
        assert any(e.get('value')=='Isolation check _123 žđčćš' for e in events),events
        assert any(e.get('value')=='restart-safe-input' for e in events)
        for kind in ('click','scroll','press','release'): assert any(e['kind']==kind for e in events),kind
        print('PASS: application received Unicode text, chord replacement, click, scroll, and drag; host focus unchanged; see pointer samples and XTEST source monitor',flush=True)
    finally:
        m.close();monitor.terminate();monitor.wait();watcher.join(timeout=1)
        print('Host event counts by source ID:',json.dumps(counts),flush=True)
        assert not counts.get(4) and not counts.get(5), 'Unexpected host XTEST input events'

