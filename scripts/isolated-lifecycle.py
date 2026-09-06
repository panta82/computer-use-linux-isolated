#!/usr/bin/python3
"""Destructive session checks for a disposable VM, never a working desktop."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

if sys.argv[1:] != ['--disposable-desktop']:
    sys.exit('Run only in a disposable VM with --disposable-desktop. This closes all isolated apps.')
exe = str(Path.home()/'.local/bin/computer-use-linux-isolated')
unit = 'computer-use-linux-isolated.service'
base = Path.home()/'.local/share/computer-use-linux-isolated'
def ctl(*args):
    return subprocess.run(['systemctl', '--user', *args], check=True, capture_output=True)
def run(*args, **kwargs):
    return subprocess.run([exe, *args], check=True, capture_output=True, text=True, **kwargs)
def primary():
    return subprocess.check_output(['xdotool', 'getmouselocation', '--shell'], env={**os.environ,'DISPLAY':':0'})

before = primary()
run('desktop','start')
marker = base/'persistence-test.txt'
marker.write_text('persistent settings and profile storage')
ready = (base/'session/ready').read_text()
ctl('restart',unit)
report = json.loads(run('doctor').stdout)
assert report['platform']['display'] == ':199'
assert (base/'session/ready').read_text() != ready
assert marker.read_text() == 'persistent settings and profile storage'
for _ in range(3):
    subprocess.run(['python3', str(Path(__file__).with_name('isolated-smoke.py')), '--disposable-desktop'], check=True)
assert primary() == before, 'Primary display pointer changed'

# An occupied X199 must not be adopted, even though it accepts X11 connections.
ctl('stop',unit)
fixture = subprocess.Popen(['Xvfb', ':199', '-screen', '0', '1600x1000x24', '-nolisten', 'tcp', '-ac'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for _ in range(100):
        if Path('/tmp/.X11-unix/X199').exists(): break
        time.sleep(.05)
    result = subprocess.run([exe,'doctor'], capture_output=True, text=True, timeout=25)
    assert result.returncode != 0, result.stdout
    assert not (base/'session/ready').exists()
    assert fixture.poll() is None
    assert primary() == before
finally:
    ctl('stop',unit)
    fixture.terminate();fixture.wait(timeout=5)
    ctl('reset-failed',unit)
run('desktop','start')
assert marker.read_text() == 'persistent settings and profile storage'
print('PASS: restart persistence, three MCP reconnects, unchanged primary display pointer, occupied-display refusal and recovery')
