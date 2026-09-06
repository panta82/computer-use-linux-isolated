#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ ${1:-} == --dependencies ]]; then
    # Native installation is necessary: desktop components use distro resource paths.
    exec sudo apt-get install -y build-essential pkg-config libdbus-1-dev python3 bubblewrap xvfb xauth x11-utils x11-xserver-utils dbus-x11 libglib2.0-bin at-spi2-core xfwm4 xfce4-panel xfdesktop4 xfce4-appfinder thunar xfce4-terminal xfce4-settings exo-utils gnome-keyring x11vnc tigervnc-viewer wmctrl xdotool imagemagick
fi
if [[ $# != 0 ]]; then echo 'Usage: ./install.sh [--dependencies]' >&2; exit 2; fi
command -v cargo >/dev/null || { echo 'Install stable Rust through https://rustup.rs first.' >&2; exit 1; }
cargo build --locked --release --bin computer-use-linux-isolated
mkdir -p "$HOME/.local/bin"
# Replace atomically so already-running MCP processes keep their executable.
install -m755 target/release/computer-use-linux-isolated "$HOME/.local/bin/computer-use-linux-isolated.new"
mv -f "$HOME/.local/bin/computer-use-linux-isolated.new" "$HOME/.local/bin/computer-use-linux-isolated"
"$HOME/.local/bin/computer-use-linux-isolated" desktop install
