#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
usage() {
    echo 'Usage: ./install.sh [--rebuild] [--skip-skill] | --dependencies'
}
skip_skill=false
rebuild=false
dependencies=false
for arg in "$@"; do
    case "$arg" in
        --help|-h) usage; exit 0 ;;
        --skip-skill) skip_skill=true ;;
        --rebuild) rebuild=true ;;
        --dependencies) dependencies=true ;;
        *) usage >&2; exit 2 ;;
    esac
done
if [[ "$dependencies" == true && $# != 1 ]]; then usage >&2; exit 2; fi
if [[ "$dependencies" == true ]]; then
    # Native installation is necessary: desktop components use distro resource paths.
    exec sudo apt-get install -y build-essential pkg-config libdbus-1-dev python3 bubblewrap xvfb xauth x11-utils x11-xserver-utils dbus-x11 libglib2.0-bin at-spi2-core xfwm4 xfce4-panel xfdesktop4 xfce4-appfinder thunar xfce4-terminal xfce4-settings exo-utils gnome-keyring x11vnc tigervnc-viewer wmctrl xdotool imagemagick
fi
build=true
if [[ "$rebuild" == false && -x target/release/computer-use-linux-isolated && -t 0 && -t 1 ]]; then
    echo 'Found an existing release binary. Reusing it will not include any newer source changes.'
    answer=''
    if ! read -r -p 'Rebuild before installing? [y/N] ' answer; then
        echo
        exit 0
    fi
    case "$answer" in
        y|Y|yes|YES) ;;
        *) build=false; echo 'Reusing target/release/computer-use-linux-isolated.' ;;
    esac
fi
if [[ "$build" == true ]]; then
    command -v cargo >/dev/null || { echo 'Install stable Rust through https://rustup.rs first.' >&2; exit 1; }
    cargo build --locked --release --bin computer-use-linux-isolated
fi
mkdir -p "$HOME/.local/bin"
# Replace atomically so already-running MCP processes keep their executable.
install -m755 target/release/computer-use-linux-isolated "$HOME/.local/bin/computer-use-linux-isolated.new"
mv -f "$HOME/.local/bin/computer-use-linux-isolated.new" "$HOME/.local/bin/computer-use-linux-isolated"
"$HOME/.local/bin/computer-use-linux-isolated" desktop install

# The application is installed before offering optional, user-level harness integration.
if [[ "$skip_skill" == true ]]; then exit 0; fi
if [[ ! -t 0 || ! -t 1 ]]; then
    echo 'Skipping optional skill installation without an interactive terminal.'
    echo 'To install it later, run from this checkout:'
    echo '  npx skills add . --skill computer-use-linux-isolated --global'
    exit 0
fi
answer=''
if ! read -r -p 'Install the skill for your agents? [Y/n] ' answer; then
    echo
    exit 0
fi
case "$answer" in
    ''|y|Y|yes|YES)
        if ! command -v npx >/dev/null; then
            echo 'The application is installed. Skill installation needs Node.js/npm with npx.' >&2
            echo 'After installing Node.js/npm, run from this checkout:' >&2
            echo '  npx skills add . --skill computer-use-linux-isolated --global' >&2
            exit 1
        fi
        # Delegate harness selection and symlink placement to the skills CLI.
        if ! npx skills add . --skill computer-use-linux-isolated --global; then
            echo 'The application is installed, but skill installation did not complete.' >&2
            echo 'Retry: npx skills add . --skill computer-use-linux-isolated --global' >&2
            exit 1
        fi
        ;;
    *) echo 'Skipped skill installation.' ;;
esac
