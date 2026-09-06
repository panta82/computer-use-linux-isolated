#!/usr/bin/python3
# PANTA: disposable guest target with application-level event logging.
import gi,json,pathlib,socket
gi.require_version('Gtk','3.0')
from gi.repository import Gtk,Gdk
assert socket.gethostname()=='mpx-lab'
log=pathlib.Path('/home/lab/gtk-events.jsonl')
def record(kind,**data):
 with log.open('a') as f:f.write(json.dumps(dict(kind=kind,**data))+'\n')
w=Gtk.Window(title='MPX guest GTK target');w.set_default_size(500,360);w.move(720,60);w.set_focus_on_map(False)
box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12);box.set_border_width(16);w.add(box)
box.pack_start(Gtk.Label(label='Disposable second application'),False,False,0)
e=Gtk.Entry();e.get_accessible().set_name('GTK input');e.connect('changed',lambda e:record('text',value=e.get_text()));box.pack_start(e,False,False,0)
b=Gtk.Button(label='Open GTK modal');box.pack_start(b,False,False,0)
def modal(*args):
 d=Gtk.Dialog(title='GTK modal',transient_for=w,modal=True);d.add_button('Close',Gtk.ResponseType.CLOSE);entry=Gtk.Entry();entry.connect('changed',lambda e:record('modal-text',value=e.get_text()));d.get_content_area().add(entry);d.show_all();d.run();d.destroy()
b.connect('clicked',modal)
a=Gtk.DrawingArea();a.set_size_request(450,150);a.get_accessible().set_name('GTK drawing area');a.add_events(Gdk.EventMask.BUTTON_PRESS_MASK|Gdk.EventMask.BUTTON_RELEASE_MASK|Gdk.EventMask.SCROLL_MASK)
for signal in ('button-press-event','button-release-event','scroll-event'):a.connect(signal,lambda _,ev,s=signal:record(s))
box.pack_start(a,True,True,0);w.connect('destroy',Gtk.main_quit);w.show_all();Gtk.main()
