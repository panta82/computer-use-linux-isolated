#!/usr/bin/python3
# PANTA: supervise a private X11/DBus desktop; never inherit host session endpoints.
import os, pathlib, secrets, signal, socket, subprocess, time
BASE = pathlib.Path.home() / '.local/share/computer-use-linux-isolated'
SESSION = BASE / 'session'
SESSION.mkdir(parents=True, exist_ok=True, mode=0o700)
os.chmod(SESSION, 0o700)
if pathlib.Path('/tmp/.X199-lock').exists() or pathlib.Path('/tmp/.X11-unix/X199').exists():
    raise SystemExit('Display :199 is already occupied; refusing to attach or fall back')
with socket.socket() as listener_check:
    listener_check.bind(('127.0.0.1', 5999))
for name in ('ready', 'bus', 'Xauthority'):
    (SESSION / name).unlink(missing_ok=True)
env = {key: os.environ[key] for key in ('HOME', 'USER', 'LOGNAME', 'LANG') if key in os.environ}
env.update({
    # PANTA: retain installed user/system application commands in this desktop.
    'PATH': f'{BASE}/launchers:{pathlib.Path.home()}/.local/bin:/usr/local/bin:' + os.environ.get('PATH', '/usr/bin:/bin'),
    
    'DISPLAY': ':199', 'XAUTHORITY': str(SESSION / 'Xauthority'),
    'DBUS_SESSION_BUS_ADDRESS': f'unix:path={SESSION}/bus',
    'XDG_RUNTIME_DIR': str(SESSION), 'XDG_SESSION_TYPE': 'x11',
    'XDG_CURRENT_DESKTOP': 'XFCE', 'DESKTOP_SESSION': 'xfce',
    'XDG_CONFIG_HOME': str(BASE / 'config'), 'XDG_CACHE_HOME': str(BASE / 'cache'),
    'XDG_DATA_HOME': str(BASE / 'data'),
    'XDG_DATA_DIRS': f'{BASE}/runtime/usr/share:/usr/local/share:/usr/share',
    'COMPUTER_USE_LINUX_SESSION_DIR': str(SESSION), 'COMPUTER_USE_LINUX_ISOLATED': '1',
    'NO_AT_BRIDGE': '0', 'GTK_A11Y': 'atspi',
})
children = []
def launch(args):
    child = subprocess.Popen(args, env=env)
    children.append(child)
    return child
def wait_for(args):
    for _ in range(100):
        if any(c.poll() is not None for c in children):
            raise RuntimeError('isolated desktop component exited')
        if subprocess.run(args, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
            return
        time.sleep(.1)
    raise RuntimeError(f'isolated desktop failed readiness: {args}')
def stop(*_):
    raise SystemExit(0)
signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
try:
    (SESSION / 'Xauthority').touch(mode=0o600)
    subprocess.run(['xauth', '-f', str(SESSION / 'Xauthority'), 'add', ':199', '.', secrets.token_hex(16)], env=env, check=True)
    launch(['dbus-daemon', '--session', '--nofork', f'--address={env["DBUS_SESSION_BUS_ADDRESS"]}'])
    launch(['Xvfb', ':199', '-screen', '0', '1600x1000x24', '-auth', str(SESSION / 'Xauthority'), '-nolisten', 'tcp', '-noreset'])
    wait_for(['xdpyinfo'])
    # PANTA: silence agent X11 bells without changing the main desktop's sound settings.
    wait_for(['xset', 'b', 'off'])
    wait_for(['dbus-send', '--session', '--print-reply', '--dest=org.freedesktop.DBus', '/', 'org.freedesktop.DBus.ListNames'])
    launch(['xfsettingsd', '--no-daemon'])
    launch(['xfwm4', '--compositor=off'])
    launch(['xfce4-panel'])
    launch(['xfdesktop'])
    wait_for(['wmctrl', '-m'])
    # Private bus activation does not contact the user's systemd desktop bus.
    wait_for(['gdbus', 'call', '--session', '--dest', 'org.a11y.Bus', '--object-path', '/org/a11y/bus', '--method', 'org.a11y.Bus.GetAddress'])
    wait_for(['busctl', '--user', 'set-property', 'org.a11y.Bus', '/org/a11y/bus', 'org.a11y.Status', 'IsEnabled', 'b', 'true'])
    import json
    (SESSION / 'environment.json').write_text(json.dumps(env))
    password_file = BASE / 'view-password'
    if not password_file.exists():
        subprocess.run(['x11vnc', '-storepasswd', secrets.token_urlsafe(6), str(password_file)], env=env, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        password_file.chmod(0o600)
    launch(['x11vnc', '-display', ':199', '-auth', str(SESSION / 'Xauthority'),
            '-listen', '127.0.0.1', '-no6', '-rfbport', '5999', '-rfbauth', str(password_file),
            '-forever', '-shared', '-nobell', '-noclipboard', '-noxdamage', '-quiet'])
    (SESSION / 'ready').write_text(str(os.getpid()))
    print('Isolated desktop ready on :199', flush=True)
    while all(c.poll() is None for c in children):
        time.sleep(.5)
    raise RuntimeError('isolated desktop component exited; restarting the session')
finally:
    (SESSION / 'ready').unlink(missing_ok=True)
    for child in reversed(children):
        if child.poll() is None:
            child.terminate()
    for child in children:
        try: child.wait(timeout=3)
        except subprocess.TimeoutExpired: child.kill()
