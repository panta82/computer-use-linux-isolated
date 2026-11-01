#!/usr/bin/env bash
# Build the upstream Trash fix against the Ubuntu 24.04 / XFCE 4.18 libraries.
set -euo pipefail
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
output="$repo_dir/target/xfdesktop"
if [[ $# == 2 && $1 == --output ]]; then
    output=$2
elif [[ $# != 0 ]]; then
    echo 'Usage: scripts/build-xfdesktop.sh [--output DIRECTORY]' >&2
    exit 2
fi
for program in curl sha256sum tar patch pkg-config make cc realpath; do
    command -v "$program" >/dev/null || { echo "Missing build dependency: $program" >&2; exit 1; }
done
output=$(realpath -m -- "$output")
pkg-config --exists gtk+-3.0 libxfce4ui-2 libxfce4util-1.0 libxfconf-0 libwnck-3.0 exo-2 garcon-1 garcon-gtk3-1 thunarx-3 libnotify || {
    echo 'Missing XFCE development libraries. See scripts/xfdesktop-backport.Dockerfile for the Ubuntu packages.' >&2
    exit 1
}
build_dir=$(mktemp -d "${TMPDIR:-/tmp}/cul-xfdesktop.XXXXXXXX")
trap 'rm -rf -- "$build_dir"' EXIT
cd -- "$build_dir"
archive=xfdesktop-4.18.1.tar.bz2
curl --fail --location --proto '=https' --tlsv1.2 --connect-timeout 20 --max-time 180 --retry 2 \
    "https://archive.xfce.org/src/xfce/xfdesktop/4.18/$archive" -o "$archive"
echo "ef9268190c25877e22a9ff5aa31cc8ede120239cb0dfca080c174e7eed4ff756  $archive" | sha256sum --check --strict
tar -xjf "$archive"
cd xfdesktop-4.18.1
patch --batch --fuzz=0 -p1 < "$repo_dir/patches/xfdesktop-trash-name.patch"
# Use the distro's existing resources; only the patched binary is installed privately.
./configure --prefix=/usr --disable-debug
make -j"${CUL_BUILD_JOBS:-4}"
mkdir -p -- "$output"
install -m755 src/xfdesktop "$output/xfdesktop.new"
mv -f -- "$output/xfdesktop.new" "$output/xfdesktop"
echo "Built $output/xfdesktop with XFCE commit 03f8af7daf70bf08dbcbc5c04ebe63fad616fb76"
