from probe import *
import subprocess,time
D=X.XOpenDisplay(None);root=X.XDefaultRootWindow(D)
rows=devices(D);p=next(a['id'] for a in rows if a['name']=='MPX Lab pointer');k=next(a['id'] for a in rows if a['name']=='MPX Lab keyboard')
window=int(subprocess.check_output(['xdotool','search','--name','^Computer Use isolation verification$'],text=True).strip())
# Give primary keyboard to an unrelated existing window, only in :199 lab.
other=int(subprocess.check_output(['xdotool','search','--class','xterm'],text=True).splitlines()[0]);subprocess.run(['xdotool','windowfocus',str(other)],check=True)
def focus(id):
 v=ul();XI.XIGetFocus(D,id,C.byref(v));return v.value
print('before',focus(3),focus(k),flush=True)
XI.XISetClientPointer(D,0,p);XI.XISetFocus(D,k,window,0);X.XSync(D,0)
XI.XIWarpPointer(D,p,0,root,0,0,0,0,450,147);X.XSync(D,0);time.sleep(.2)
XT.XTestFakeButtonEvent(D,1,1,0);XT.XTestFakeButtonEvent(D,1,0,80);X.XSync(D,0);time.sleep(.2)
for char in 'mpxlab':
 code=X.XKeysymToKeycode(D,X.XStringToKeysym(char.encode()));XT.XTestFakeKeyEvent(D,code,1,0);XT.XTestFakeKeyEvent(D,code,0,30)
X.XSync(D,0);time.sleep(.3)
print('after',focus(3),focus(k),flush=True)
