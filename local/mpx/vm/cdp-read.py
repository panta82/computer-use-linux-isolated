#!/usr/bin/python3
# PANTA: read test-page state inside disposable guest; no browser profile access on host.
import urllib.request,json,websocket,sys,socket
assert socket.gethostname()=='mpx-lab'
pages=json.load(urllib.request.urlopen('http://127.0.0.1:9222/json'))
p=next(p for p in pages if p.get('title')=='MPX Chrome input test')
w=websocket.create_connection(p['webSocketDebuggerUrl'],suppress_origin=True)
expr="JSON.stringify({input:input.value,modalInput:modalInput.value,modal:dialog.open,active:document.activeElement.id,events:events.slice(-30),bounds:Object.fromEntries(['input','modal','modalInput','close','select'].map(id=>{let r=document.getElementById(id).getBoundingClientRect();return [id,{x:screenX+r.x+r.width/2,y:screenY+outerHeight-innerHeight+r.y+r.height/2,width:r.width,height:r.height}]}))})"
w.send(json.dumps({'id':1,'method':'Runtime.evaluate','params':{'expression':expr,'returnByValue':True}}))
while True:
 r=json.loads(w.recv())
 if r.get('id')==1:
  print(r['result']['result']['value']);break
w.close()
