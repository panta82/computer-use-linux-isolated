#!/usr/bin/python3
# PANTA: exercise the deployed stdio MCP with a disposable isolated GTK app.
import json, pathlib, subprocess, select, time, ctypes, threading, re
base=pathlib.Path.home()/'.local/share/computer-use-linux-isolated'
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

if __name__ == '__main__':
    import sys
    if sys.argv[1:] != ['--disposable-desktop']:
        sys.exit('This test types and clicks. Run only in a disposable VM with --disposable-desktop.')
    exe=str(pathlib.Path.home()/'.local/bin/computer-use-linux-isolated')
    log.unlink(missing_ok=True)
    app=subprocess.Popen([exe,'desktop','run','python3',str(pathlib.Path(__file__).with_name('isolated-test-app.py'))])
    m=MCP()
    try:
        report=m.tool('doctor')
        assert report['platform']['display']==':199'
        assert report['capabilities']['input']==['xdotool-isolated-x11-no-fallback']
        tools=m.request('tools/list',{})
        assert not any(t['name']=='run_shell' for t in tools['tools'])
        for _ in range(40):
            windows=m.tool('list_windows')['windows']
            w=next((w for w in windows if w['title']=='Computer Use isolation verification'),None)
            if w: break
            time.sleep(.25)
        assert w, windows
        state=m.tool('get_app_state',{'app_name_or_bundle_identifier':'isolated-test-app.py','include_screenshot':False})
        nodes=state['accessibility_tree'];wid=w['window_id']
        def click(name):
            b=next(n['bounds'] for n in nodes if n['name']==name)
            m.tool('click',{'window_id':wid,'x':b['x']+b['width']//2,'y':b['y']+b['height']//2})
        click('Isolated text target')
        m.tool('type_text',{'window_id':wid,'text':'Restart-safe input žđčćš'})
        click('Verify isolated click')
        click('Open modal')
        windows=m.tool('list_windows')['windows']
        # Observe the actual modal using the accessibility tree and screenshot before dismissal.
        modal_state=m.tool('get_app_state',{'app_name_or_bundle_identifier':'isolated-test-app.py','include_screenshot':False})
        assert 'Isolated modal verification' in json.dumps(modal_state), modal_state
        m.tool('press_key',{'key':'Return'})
        m.tool('screenshot',{})
        events=[json.loads(line) for line in log.read_text().splitlines()]
        assert any(e.get('value')=='Restart-safe input žđčćš' for e in events),events
        assert any(e['kind']=='click' for e in events),events
        assert any(e['kind']=='modal-closed' for e in events),events
        print('PASS: isolated MCP discovery, Unicode input, click, modal observation/dismissal, screenshot')
    finally:
        m.close()
        app.terminate()
        app.wait(timeout=5)
