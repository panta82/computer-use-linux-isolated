FROM ubuntu:24.04
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    build-essential ca-certificates curl patch pkg-config intltool \
    libgtk-3-dev libxfce4ui-2-dev libxfce4util-dev libxfconf-0-dev \
    libwnck-3-dev libexo-2-dev libgarcon-1-dev libgarcon-gtk3-1-dev \
    libthunarx-3-dev libnotify-dev && rm -rf /var/lib/apt/lists/*
