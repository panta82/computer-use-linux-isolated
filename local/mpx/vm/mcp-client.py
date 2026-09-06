#!/usr/bin/python3
# PANTA: exercise the deployed stdio MCP with a disposable isolated GTK app.
import json, pathlib, subprocess, select, time, ctypes, threading, re
base=pathlib.Path('/home/lab/mpx');base.mkdir(exist_ok=True)
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

if __name__=='__main__':
 import sys,socket
 assert socket.gethostname()=='mpx-lab'
 m=MCP(['/home/lab/mpx/computer-use-linux','mcp'])
 try:
  for name,args in json.loads(sys.argv[1]):print(json.dumps({'tool':name,'result':m.tool(name,args)}),flush=True)
 finally:m.close()
