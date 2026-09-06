#!/bin/bash
# PANTA: disposable guest applications only.
set -eu
[ "$(hostname)" = mpx-lab ] || exit 90
screen -dmS chrome-test python3 /home/lab/mpx/vm/guest-env.py /opt/google/chrome/chrome --user-data-dir=/home/lab/chrome-profile --no-first-run --no-default-browser-check --force-renderer-accessibility --disable-dev-shm-usage --remote-debugging-port=9222 --window-position=0,0 --window-size=700,700 file:///home/lab/mpx/vm/test.html
screen -dmS gtk-test python3 /home/lab/mpx/vm/guest-env.py python3 /home/lab/mpx/vm/gtk-target.py
