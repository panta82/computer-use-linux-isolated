import ctypes as C, json, os
X=C.CDLL('libX11.so.6');XI=C.CDLL('libXi.so.6');XT=C.CDLL('libXtst.so.6')
class Device(C.Structure):
 _fields_=[('deviceid',C.c_int),('name',C.c_char_p),('use',C.c_int),('attachment',C.c_int),('enabled',C.c_int),('num_classes',C.c_int),('classes',C.c_void_p)]
def sig(lib,name,args,result=C.c_int):
 f=getattr(lib,name);f.argtypes=args;f.restype=result;return f
ptr=C.c_void_p; ul=C.c_ulong; i=C.c_int
sig(X,'XOpenDisplay',[C.c_char_p],ptr);sig(X,'XCloseDisplay',[ptr]);sig(X,'XDefaultRootWindow',[ptr],ul);sig(X,'XSync',[ptr,i]);sig(X,'XGetInputFocus',[ptr,C.POINTER(ul),C.POINTER(i)])
sig(XI,'XIQueryDevice',[ptr,i,C.POINTER(i)],C.POINTER(Device));sig(XI,'XIFreeDeviceInfo',[C.POINTER(Device)],None);sig(XI,'XISetClientPointer',[ptr,ul,i]);sig(XI,'XIGetClientPointer',[ptr,ul,C.POINTER(i)]);sig(XI,'XISetFocus',[ptr,i,ul,ul]);sig(XI,'XIGetFocus',[ptr,i,C.POINTER(ul)]);sig(XI,'XIWarpPointer',[ptr,i,ul,ul,C.c_double,C.c_double,C.c_uint,C.c_uint,C.c_double,C.c_double]);sig(XT,'XTestFakeButtonEvent',[ptr,C.c_uint,i,ul]);sig(XT,'XTestFakeKeyEvent',[ptr,C.c_uint,i,ul]);sig(X,'XKeysymToKeycode',[ptr,ul],C.c_ubyte);sig(X,'XStringToKeysym',[C.c_char_p],ul)
def devices(d):
 n=i();a=XI.XIQueryDevice(d,0,C.byref(n));out=[{'id':a[j].deviceid,'name':a[j].name.decode(),'use':a[j].use,'attachment':a[j].attachment,'enabled':a[j].enabled} for j in range(n.value)];XI.XIFreeDeviceInfo(a);return out
if __name__=='__main__':
 d=X.XOpenDisplay(None);assert d;print(json.dumps(devices(d),indent=2));X.XCloseDisplay(d)
