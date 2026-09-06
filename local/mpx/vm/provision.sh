#!/bin/bash
# PANTA: run ONLY inside the disposable guest, never on the laptop.
set -eu
[ "$(hostname)" = mpx-lab ] || exit 90
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends plasma-desktop plasma-session-x11 kwin-x11 sddm xserver-xorg xinput xdotool x11-utils x11-xserver-utils dbus-x11 konsole python3-gi gir1.2-gtk-3.0 python3-websocket libnss3 libnspr4 libasound2t64 libatk-bridge2.0-0t64 libxss1 fonts-liberation screen imagemagick wmctrl at-spi2-core
systemctl stop sddm
cat > /usr/local/bin/mpx-before-desktop <<'EOF'
#!/bin/sh
# PANTA: create once per X server, before SDDM greeter and Plasma; never remove while clients live.
set -eu
[ -f /etc/mpx-lab-enabled ] || exit 0
/usr/bin/xinput create-master 'Computer Use Agent' 0 1
/usr/bin/xinput list > /var/log/mpx-before-desktop.log
EOF
chmod +x /usr/local/bin/mpx-before-desktop
touch /etc/mpx-lab-enabled
mkdir -p /etc/sddm.conf.d
cat > /etc/sddm.conf.d/mpx-lab.conf <<'EOF'
# PANTA: disposable guest uses X11 and creates MPX before Qt clients start.
[General]
DisplayServer=x11
[X11]
DisplayCommand=/usr/local/bin/mpx-before-desktop
[Autologin]
User=lab
Session=plasmax11.desktop
Relogin=false
EOF
systemctl set-default graphical.target
systemctl enable sddm
# Start separately after package versions and session filename have been checked.
touch /home/lab/provision-complete
