#!/usr/bin/python3
# PANTA: explicit MPX devices only. Never inject into the primary master devices.
from probe import *
import sys,time,fcntl,pathlib,contextlib,hashlib
sig(X,'XGrabServer',[ptr]);sig(X,'XUngrabServer',[ptr]);sig(X,'XDisplayKeycodes',[ptr,C.POINTER(i),C.POINTER(i)])
sig(X,'XGetKeyboardMapping',[ptr,C.c_ubyte,i,C.POINTER(i)],C.POINTER(ul));sig(X,'XFree',[ptr])
sig(X,'XQueryPointer',[ptr,ul,C.POINTER(ul),C.POINTER(ul),C.POINTER(i),C.POINTER(i),C.POINTER(i),C.POINTER(i),C.POINTER(C.c_uint)])
sig(X,'XkbLockGroup',[ptr,C.c_uint,C.c_uint]);sig(X,'XkbLockModifiers',[ptr,C.c_uint,C.c_uint,C.c_uint])
sig(XI,'XIQueryPointer',[ptr,i,ul,C.POINTER(ul),C.POINTER(ul),C.POINTER(C.c_double),C.POINTER(C.c_double),C.POINTER(C.c_double),C.POINTER(C.c_double),ptr,ptr,ptr])
class Backend:
 def __init__(self):
  self.name=os.environ.get('COMPUTER_USE_MPX_NAME','Computer Use Agent')
  self.d=X.XOpenDisplay(None)
  if not self.d:raise RuntimeError('MPX display unavailable; no fallback')
  self.root=X.XDefaultRootWindow(self.d)
  self.p,self.k=self.validate()
  with self.guard():
   XI.XISetClientPointer(self.d,0,self.p)
  self.held=[]
 def validate(self):
  rows=devices(self.d)
  def one(name,use):
   matches=[r for r in rows if r['name']==name and r['use']==use and r['enabled']]
   if len(matches)!=1:raise RuntimeError('Required MPX device missing/ambiguous/disabled; no fallback: '+name)
   return matches[0]
  p=one(self.name+' pointer',1);k=one(self.name+' keyboard',2)
  if p['id']==2 or k['id']==3 or p['attachment']!=k['id'] or k['attachment']!=p['id']:
   raise RuntimeError('Unsafe MPX master attachment; no fallback')
  for master,suffix,use in [(p,'pointer',3),(k,'keyboard',4)]:
   slaves=[r for r in rows if r['attachment']==master['id'] and r['use']==use]
   if len(slaves)!=1 or slaves[0]['name']!=self.name+' XTEST '+suffix or not slaves[0]['enabled']:
    raise RuntimeError('MPX must contain exactly its own XTEST slave and no physical input')
  return p['id'],k['id']
 @contextlib.contextmanager
 def guard(self):
  # The short server grab closes the validate-to-inject race if devices are removed.
  X.XGrabServer(self.d)
  try:
   p,k=self.validate()
   if hasattr(self,'p') and (p,k)!=(self.p,self.k):raise RuntimeError('MPX devices changed during action; no replay')
   XI.XISetClientPointer(self.d,0,p)
   yield
   X.XSync(self.d,0)
  finally:X.XUngrabServer(self.d);X.XSync(self.d,0)
 def focus(self,window):
  if window in (0,1):raise RuntimeError('An explicit application window is required for MPX focus')
  with self.guard():XI.XISetFocus(self.d,self.k,window,0)
  actual=ul();XI.XIGetFocus(self.d,self.k,C.byref(actual));X.XSync(self.d,0)
  if actual.value!=window:raise RuntimeError('MPX keyboard focus was not accepted')
 def position(self):
  r=ul();c=ul();rx=i();ry=i();wx=i();wy=i();mask=C.c_uint()
  with self.guard():X.XQueryPointer(self.d,self.root,C.byref(r),C.byref(c),C.byref(rx),C.byref(ry),C.byref(wx),C.byref(wy),C.byref(mask))
  return [rx.value,ry.value]
 def state(self):
  f=ul();primary=ul();XI.XIGetFocus(self.d,self.k,C.byref(f));XI.XIGetFocus(self.d,3,C.byref(primary))
  return dict(pointer_id=self.p,keyboard_id=self.k,focus=f.value,primary_focus=primary.value,position=self.position(),backend='MPX XI2; no shared-input fallback')
 def move(self,x,y):
  with self.guard():XI.XIWarpPointer(self.d,self.p,0,self.root,0,0,0,0,x,y)
  time.sleep(.04)
 def button(self,button,down):
  if button not in range(1,8):raise RuntimeError('Only standard MPX buttons/wheel supported')
  with self.guard():XT.XTestFakeButtonEvent(self.d,button,int(down),0)
  token=('button',button)
  if down:self.held.append(token)
  elif token in self.held:self.held.remove(token)
  time.sleep(.04)
 def key(self,code,down):
  with self.guard():
   focus=ul();XI.XIGetFocus(self.d,self.k,C.byref(focus))
   if down and focus.value in (0,1):raise RuntimeError('Agent keyboard has no explicit window focus; refusing input')
   XT.XTestFakeKeyEvent(self.d,code,int(down),0)
  token=('key',code)
  if down:self.held.append(token)
  elif token in self.held:self.held.remove(token)
  time.sleep(.015)
 def mapping(self):
  lo=i();hi=i();n=i()
  with self.guard():
   X.XDisplayKeycodes(self.d,C.byref(lo),C.byref(hi));data=X.XGetKeyboardMapping(self.d,lo.value,hi.value-lo.value+1,C.byref(n))
   if not data:raise RuntimeError('MPX keyboard map unavailable')
   rows=[(lo.value+j,[data[j*n.value+l] for l in range(n.value)]) for j in range(hi.value-lo.value+1)];X.XFree(data)
  return rows
 def lookup(self,name,rows):
  symbol=X.XStringToKeysym(name.encode())
  if not symbol and len(name)==1:symbol=ord(name) if ord(name)<256 else 0x01000000+ord(name)
  for code,row in rows:
   if symbol and row[0]==symbol:return code,False
  for code,row in rows:
   if len(row)>1 and symbol and row[1]==symbol:return code,True
  raise RuntimeError('Key not mapped in the agent US keyboard: '+repr(name)+'; no keymap/clipboard fallback')
 def chord(self,spec):
  rows=self.mapping();parts=spec.split('+');mods=[]
  aliases={'ctrl':'Control_L','control':'Control_L','shift':'Shift_L','alt':'Alt_L','super':'Super_L','meta':'Super_L'}
  for part in parts[:-1]:mods.append(self.lookup(aliases.get(part.lower(),part),rows)[0])
  code,shift=self.lookup(aliases.get(parts[-1].lower(),parts[-1]),rows)
  if shift:mods.append(self.lookup('Shift_L',rows)[0])
  # Do not route global desktop shortcuts through this experimental backend.
  if any(p.lower() in ('alt','super','meta') for p in parts[:-1]):raise RuntimeError('Global Alt/Super shortcuts are disabled in MPX trial')
  for mod in mods:self.key(mod,True)
  self.key(code,True);self.key(code,False)
  for mod in reversed(mods):self.key(mod,False)
 def text(self,text):
  rows=self.mapping();shift=self.lookup('Shift_L',rows)[0]
  # Validate the complete string before emitting anything, avoiding partial Unicode input.
  keys=[self.lookup({'\n':'Return','\t':'Tab'}.get(c,c),rows) for c in text]
  for code,needshift in keys:
   if needshift:self.key(shift,True)
   self.key(code,True);self.key(code,False)
   if needshift:self.key(shift,False)
 def cleanup(self):
  for kind,code in list(reversed(self.held)):
   try:(self.key if kind=='key' else self.button)(code,False)
   except Exception:pass
  X.XCloseDisplay(self.d)
def run(args):
 b=Backend()
 try:
  if args==['state']:print(json.dumps(b.state()));return
  if args[0]=='focus':b.focus(int(args[1],0));print(json.dumps(b.state()));return
  j=0
  while j<len(args):
   cmd=args[j];j+=1
   if cmd=='mousemove':
    if args[j]=='--':j+=1
    b.move(int(args[j]),int(args[j+1]));j+=2
   elif cmd=='sleep':time.sleep(min(float(args[j]),2));j+=1
   elif cmd in ('mousedown','mouseup'):b.button(int(args[j]),cmd=='mousedown');j+=1
   elif cmd=='click':
    repeat=1;delay=.08
    while args[j].startswith('--'):
     if args[j]=='--':j+=1;break
     opt=args[j];val=args[j+1];j+=2
     if opt=='--repeat':repeat=int(val)
     elif opt=='--delay':delay=int(val)/1000
     else:raise RuntimeError('Unsupported click option')
    button=int(args[j]);j+=1
    if not 1<=repeat<=100:raise RuntimeError('Invalid MPX repeat count')
    for _ in range(repeat):b.button(button,True);b.button(button,False);time.sleep(delay)
   elif cmd=='key':
    if args[j]=='--clearmodifiers':j+=1
    # Only the fresh agent keyboard is involved; never clear the user's modifiers.
    b.chord(args[j]);j+=1
   elif cmd=='type':
    while j<len(args) and args[j].startswith('--'):
     option=args[j];j+=1
     if option=='--':break
     if option=='--delay':j+=1
     elif option!='--clearmodifiers':raise RuntimeError('Unsupported type option')
    if len(args[j:])!=1:raise RuntimeError('Expected literal text')
    b.text(args[j]);j+=1
   else:raise RuntimeError('Unsupported MPX operation: '+cmd)
  print('Input sent through dedicated MPX devices; no fallback')
 finally:b.cleanup()
if __name__=='__main__':
 try:
  directory=pathlib.Path(os.environ['COMPUTER_USE_MPX_RUNTIME']);directory.mkdir(mode=0o700,parents=True,exist_ok=True)
  with (directory/'actions.lock').open('a') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX);run(sys.argv[1:])
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
