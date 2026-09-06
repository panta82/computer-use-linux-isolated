#!/usr/bin/python3
# PANTA: disposable MPX target that does not request the user's focus when mapped.
import gi,json,pathlib
gi.require_version('Gtk','3.0')
from gi.repository import Gtk,Gdk
base=pathlib.Path.home()/'.local/share/computer-use-linux/mpx'
def record(kind,**data):
 with (base/'main-test.jsonl').open('a') as f:f.write(json.dumps(dict(kind=kind,**data))+'\n')
w=Gtk.Window(title='Agent MPX test - your keyboard stays with your app')
w.set_focus_on_map(False);w.set_accept_focus(False);w.set_default_size(560,280);w.move(60,100)
box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12);box.set_border_width(16);w.add(box)
box.pack_start(Gtk.Label(label='Second-cursor test. Safe to close this window.'),False,False,0)
e=Gtk.Entry();e.set_placeholder_text('The agent types here');e.get_accessible().set_name('MPX test input')
e.connect('changed',lambda e:record('text',value=e.get_text()));box.pack_start(e,False,False,0)
b=Gtk.Button(label='Test second cursor click');b.connect('clicked',lambda b:(record('click'),b.set_label('Second cursor click received')));box.pack_start(b,False,False,0)
a=Gtk.DrawingArea();a.get_accessible().set_name('MPX drawing area');a.set_size_request(480,110);a.add_events(Gdk.EventMask.BUTTON_PRESS_MASK|Gdk.EventMask.BUTTON_RELEASE_MASK|Gdk.EventMask.SCROLL_MASK)
a.connect('button-press-event',lambda _,ev:record('press'));a.connect('button-release-event',lambda _,ev:record('release'));a.connect('scroll-event',lambda _,ev:record('scroll'));box.pack_start(a,True,True,0)
w.connect('destroy',Gtk.main_quit);w.show_all();Gtk.main()
