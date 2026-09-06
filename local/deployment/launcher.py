#!/usr/bin/python3
# PANTA: route MCP/app launches only to the dedicated session and hide host input devices.
import json, os, pathlib, subprocess, sys, time
base = pathlib.Path.home() / '.local/share/computer-use-linux'
session = base / 'session'
subprocess.run(['systemctl', '--user', 'start', 'computer-use-linux-desktop.service'], check=True)
for _ in range(100):
    if (session / 'ready').is_file(): break
    time.sleep(.1)
else: sys.exit('Isolated desktop unavailable; refusing host input fallback')
env = json.loads((session / 'environment.json').read_text())
mode = pathlib.Path(sys.argv[0]).name
if mode == 'computer-use-linux-desktop':
    if sys.argv[1:] == ['view']:
        os.execvp('vncviewer', ['vncviewer', '-PasswordFile', str(base / 'view-password'),
                  '-SendKeyEvents=0', '-SendPointerEvents=0', '127.0.0.1:99'])
    if len(sys.argv) < 3 or sys.argv[1] != 'run':
        sys.exit('Usage: computer-use-linux-desktop view | run PROGRAM [ARGS...]')
    command = sys.argv[2:]
else:
    command = [str(base / 'bin/computer-use-linux'), *sys.argv[1:]]
    if not sys.argv[1:]: command.append('mcp')
# Hide physical devices, shared D-Bus/ydotool sockets, and host filesystem X sockets.
# MCP also gets a separate network namespace, blocking abstract host X/DBus sockets.
args = ['/usr/bin/bwrap', '--die-with-parent', '--ro-bind', '/', '/',
        '--bind', str(base), str(base), '--dev', '/dev', '--tmpfs', '/run', '--tmpfs', '/tmp',
        '--dir', '/tmp/.X11-unix', '--ro-bind', '/tmp/.X11-unix/X199', '/tmp/.X11-unix/X199']
if mode != 'computer-use-linux-desktop': args += ['--unshare-net']
args += ['--', *command]
os.execve(args[0], args, env)
