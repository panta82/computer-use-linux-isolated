#!/usr/bin/python3
# PANTA: disposable target for checking isolated MCP input.
import gi, json, pathlib
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
base = pathlib.Path.home() / '.local/share/computer-use-linux-isolated'
log = base / 'test-events.jsonl'
def record(kind, **data):
    with log.open('a') as f: f.write(json.dumps(dict(kind=kind, **data))+'\n')
w = Gtk.Window(title='Computer Use isolation verification')
w.set_default_size(700, 450)
w.move(100, 100)
b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
w.add(b)
e = Gtk.Entry(); e.set_placeholder_text('Isolated text target'); e.get_accessible().set_name('Isolated text target')
e.connect('changed', lambda e: record('text', value=e.get_text()))
b.pack_start(e, False, False, 10)
button = Gtk.Button(label='Verify isolated click')
button.connect('clicked', lambda _: record('click'))
b.pack_start(button, False, False, 10)
a = Gtk.DrawingArea(); a.set_size_request(600, 250)
a.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.SCROLL_MASK)
a.connect('button-press-event', lambda _, ev: record('press', x=ev.x, y=ev.y))
a.connect('button-release-event', lambda _, ev: record('release', x=ev.x, y=ev.y))
a.connect('scroll-event', lambda _, ev: record('scroll', direction=int(ev.direction)))
b.pack_start(a, True, True, 10)
def modal(_):
    dialog=Gtk.MessageDialog(transient_for=w, modal=True, buttons=Gtk.ButtonsType.OK, text='Isolated modal verification')
    dialog.run()
    dialog.destroy()
    record('modal-closed')
modal_button=Gtk.Button(label='Open modal')
modal_button.connect('clicked', modal)
b.pack_start(modal_button, False, False, 0)
w.connect('destroy', Gtk.main_quit)
w.show_all()
Gtk.main()
