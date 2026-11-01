#!/usr/bin/env python3
"""Verify real focus and post-action capture in a disposable VM."""
from pathlib import Path
import runpy
import subprocess
import sys
import time

if sys.argv[1:] != ['--disposable-desktop']:
    sys.exit('Run only in a disposable VM with --disposable-desktop. This changes focus.')

MCP = runpy.run_path(str(Path(__file__).with_name('isolated-smoke.py')))['MCP']
exe = str(Path.home() / '.local/bin/computer-use-linux-isolated')
fixture = '''
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
windows = []
for title, x in [('Focus regression first', 50), ('Focus regression second', 500)]:
    window = Gtk.Window(title=title)
    window.set_default_size(350, 200)
    window.move(x, 100)
    window.add(Gtk.Entry())
    window.show_all()
    windows.append(window)
Gtk.main()
'''
app = subprocess.Popen([exe, 'desktop', 'run', 'python3', '-c', fixture])
client = MCP()
try:
    report = client.tool('doctor')
    assert report['platform']['display'] == ':199'
    assert report['capabilities']['input'] == ['xdotool-isolated-x11-no-fallback']
    for _ in range(80):
        windows = {w['title']: w for w in client.tool('list_windows')['windows']}
        if all(title in windows for title in ('Focus regression first', 'Focus regression second')):
            break
        time.sleep(.1)
    first = windows['Focus regression first']['window_id']
    second = windows['Focus regression second']['window_id']
    client.tool('activate_window', {'window_id': first})
    # Leave EWMH pointing at the first window while the server focuses the second.
    subprocess.run([exe, 'desktop', 'run', 'xdotool', 'windowfocus', '--sync', str(second)], check=True)
    subprocess.run([exe, 'desktop', 'run', 'xprop', '-root', '-f', '_NET_ACTIVE_WINDOW', '32x',
                    '-set', '_NET_ACTIVE_WINDOW', hex(first)], check=True)
    actual = client.tool('focused_window')
    assert actual['focused_window']['window_id'] == second, actual
    subprocess.run([exe, 'desktop', 'run', 'xprop', '-root', '-remove', '_NET_ACTIVE_WINDOW'], check=True)
    actual = client.tool('focused_window')
    assert actual['focused_window']['window_id'] == second, actual
    result = client.tool('press_key', {'window_id': second, 'key': 'a', 'screenshot_after': True})
    assert result['ok'], result
    assert result['screenshot']['source'] == 'isolated-x11', result
    assert result['screenshot']['width'] > 0, result
    print('PASS: actual X11 focus survives stale/missing EWMH metadata; targeted input returns a native post-action screenshot')
finally:
    client.close()
    app.terminate()
    app.wait(timeout=5)
