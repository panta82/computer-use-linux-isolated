#!/usr/bin/python3
# PANTA: self-contained app launcher/taskbar on X199; never connects to the host display.
import json,os,pathlib,subprocess,sys,shlex,time
base=pathlib.Path.home()/'.local/share/computer-use-linux';session=base/'session'
for _ in range(100):
 if (session/'ready').exists():break
 time.sleep(.1)
else:sys.exit('Separate desktop is not ready')
env=json.loads((session/'environment.json').read_text())
assert env['DISPLAY']==':199' and env['XAUTHORITY']==str(session/'Xauthority')
env['XDG_DATA_DIRS']=f'{base}/runtime/usr/share:{pathlib.Path.home()}/.local/share:/usr/local/share:/usr/share:/var/lib/snapd/desktop:/var/lib/flatpak/exports/share'
os.environ.clear();os.environ.update(env)
import gi
gi.require_version('Gtk','3.0');gi.require_version('GdkX11','3.0')
from gi.repository import Gtk,Gdk,GdkX11,Gio,GLib
wmctrl=str(base/'runtime/usr/bin/wmctrl')
def error(message):
 d=Gtk.MessageDialog(message_type=Gtk.MessageType.ERROR,buttons=Gtk.ButtonsType.CLOSE,text='Could not launch application');d.format_secondary_text(str(message));d.run();d.destroy()
def launch(argv):
 try:
  if pathlib.Path(argv[0]).name in ('google-chrome','google-chrome-stable','chrome'):argv=[str(base/'chrome.py'),*argv[1:]]
  subprocess.Popen(argv,env=env,start_new_session=True)
 except Exception as e:error(e)
def run_dialog(*args):
 d=Gtk.Dialog(title='Run command',buttons=('Cancel',Gtk.ResponseType.CANCEL,'Run',Gtk.ResponseType.OK));d.set_default_size(550,100)
 e=Gtk.Entry();e.set_placeholder_text('Application command, for example: gimp');e.set_activates_default(True);d.set_default_response(Gtk.ResponseType.OK);d.get_content_area().pack_start(e,True,True,12);d.show_all()
 if d.run()==Gtk.ResponseType.OK:
  try:
   argv=shlex.split(e.get_text())
   if argv:launch(argv)
  except ValueError as ex:error(ex)
 d.destroy()
app_window=None
def applications(*args):
 global app_window
 if app_window is not None:
  app_window.present();return
 w=Gtk.Window(title='Applications');app_window=w
 def closed(*args):
  global app_window
  app_window=None
 w.connect('destroy',closed)
 w.set_default_size(650,650);box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=10);box.set_border_width(14);w.add(box)
 entry=Gtk.SearchEntry();entry.set_placeholder_text('Find an installed application');box.pack_start(entry,False,False,0)
 scroll=Gtk.ScrolledWindow();box.pack_start(scroll,True,True,0);items=Gtk.ListBox();items.set_selection_mode(Gtk.SelectionMode.SINGLE);scroll.add(items)
 for app in sorted(Gio.AppInfo.get_all(),key=lambda a:a.get_display_name().lower()):
  if not isinstance(app,Gio.DesktopAppInfo) or app.get_nodisplay() or app.get_is_hidden() or app.get_id()=='computer-use-linux-desktop.desktop':continue
  row=Gtk.ListBoxRow();row.app=app;row.search=(app.get_display_name()+' '+(app.get_description() or '')+' '+(app.get_executable() or '')).lower()
  line=Gtk.Box(spacing=12);line.set_border_width(8);row.add(line)
  icon=app.get_icon();pic=Gtk.Image.new_from_gicon(icon,Gtk.IconSize.LARGE_TOOLBAR) if icon else Gtk.Image.new_from_icon_name('application-x-executable',Gtk.IconSize.LARGE_TOOLBAR)
  line.pack_start(pic,False,False,0);label=Gtk.Label(label=app.get_display_name(),xalign=0);line.pack_start(label,True,True,0);items.add(row)
 items.set_filter_func(lambda row:entry.get_text().lower() in row.search)
 entry.connect('search-changed',lambda e:items.invalidate_filter())
 def activate(_,row):
  if not row:return
  try:
   executable=pathlib.Path(row.app.get_executable() or '').name
   if executable in ('google-chrome','google-chrome-stable','chrome'):
    command=row.app.get_commandline() or ''
    if '--app-id=' in command:raise RuntimeError('This Chrome app belongs to another profile. Open or install it in this desktop’s Chrome first.')
    launch([str(base/'chrome.py')])
   else:row.app.launch([],Gdk.Display.get_default().get_app_launch_context())
   w.destroy()
  except Exception as ex:error(ex)
 items.connect('row-activated',activate)
 entry.connect('activate',lambda e:activate(items,next((r for r in items.get_children() if r.get_child_visible()),None)))
 w.show_all();entry.grab_focus()
panel=Gtk.Window(title='Agent desktop panel');panel.set_decorated(False);panel.set_type_hint(Gdk.WindowTypeHint.DOCK);panel.set_skip_taskbar_hint(True);panel.set_skip_pager_hint(True);panel.set_keep_above(True)
width=Gdk.Screen.get_default().get_width();panel.set_default_size(width,44);panel.move(0,0)
bar=Gtk.Box(spacing=5);bar.set_border_width(4);panel.add(bar)
def button(label,fn):
 b=Gtk.Button(label=label);b.connect('clicked',fn);bar.pack_start(b,False,False,0)
button('Applications',applications);button('Chrome',lambda _:launch([str(base/'chrome.py')]))
button('Files',lambda _:launch(['/usr/bin/dolphin','--new-window',str(pathlib.Path.home())]))
button('Terminal',lambda _:launch(['xterm']));button('Run…',run_dialog)
tasks=Gtk.Box(spacing=4);bar.pack_start(tasks,True,True,10);clock=Gtk.Label();bar.pack_end(clock,False,False,8)
last=None
def update():
 global last
 clock.set_text(time.strftime('%H:%M'))
 try:
  result=subprocess.run([wmctrl,'-lp'],env=env,capture_output=True,text=True,timeout=2)
  windows=[]
  for line in result.stdout.splitlines():
   p=line.split(None,4)
   if len(p)==5 and int(p[2])!=os.getpid() and p[1]!='-1':windows.append((p[0],p[4]))
  if windows!=last:
   for child in tasks.get_children():tasks.remove(child)
   for wid,title in windows:
    b=Gtk.Button(label=title[:28]);b.set_tooltip_text(title);b.connect('clicked',lambda _,w=wid:subprocess.Popen([wmctrl,'-ia',w],env=env));tasks.pack_start(b,True,True,0)
   tasks.show_all();last=windows
 except Exception as ex:print('Taskbar refresh: '+str(ex),file=sys.stderr)
 return True
def reserve(*args):
 xid=panel.get_window().get_xid()
 subprocess.run(['xprop','-id',str(xid),'-f','_NET_WM_STRUT_PARTIAL','32c','-set','_NET_WM_STRUT_PARTIAL',f'0,0,44,0,0,0,0,0,0,{width-1},0,0'],env=env,check=True)
panel.connect('realize',reserve);panel.connect('destroy',Gtk.main_quit);panel.show_all();update();GLib.timeout_add_seconds(1,update)
# The run/menu command uses the same private D-Bus to request a launcher window.
class Control(Gio.Application):
 def __init__(self):super().__init__(application_id='pw.pantas.AgentDesktopLauncher',flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
 def do_command_line(self,cmd):
  (run_dialog if 'run' in cmd.get_arguments() else applications)();return 0
control=Control();control.register(None)
if control.get_is_remote():sys.exit('Desktop panel already running')
Gtk.main()
