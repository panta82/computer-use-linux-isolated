# computer-use-linux-isolated

A fork of [agent-sh/computer-use-linux](https://github.com/agent-sh/computer-use-linux). The original authors retain attribution under the MIT license.

## Explanation

This is basically a spinoff of the linux computer use skill, where instead of messing with your own desktop, it uses a separate X11 desktop session on a virtual display.

Models operate an Xvfb display with its own cursor, keyboard focus, D-Bus session, and XFCE desktop components. You can watch and interact through a local VNC viewer. Your files and installed applications remain available under your normal Linux account.

**What's included:**
- XFCE lightweight desktop, so you can do things in the agent session
- A skill, so you can tell your clanker to go use the desktop and it'll know what to do
- VNC viewer, so you can connect to it and watch what the little guy is doing

**Advantages over VM:**
- Trivially shared file system and installed apps (it's the same computer)
- Lower resource use (no need to allocate RAM etc.)

**Disadvantages over VM:**
- It's the same OS, the clanker can still (probably) interfere with you

**Advantages over a shared session:**
- Clanker no longer steals your focus or mouse

**Disadvantages over a shared session:**
- You have to log into stuff anew (but it's persistent once you do)

## Installation

Initial target: Ubuntu with systemd user services, an X11-capable package stack, and working unprivileged bubblewrap. Runtime tested in a clean Ubuntu 25.10 x86_64 VM. Other distributions and architectures are not yet validated. Ubuntu package repositories and security policy must permit the listed packages and bubblewrap user namespaces; the installer does not disable AppArmor or change kernel policy.

Install Git and a current stable Rust toolchain, following [rustup's instructions](https://rustup.rs). Then:

```bash
git clone https://github.com/panta82/computer-use-linux-isolated.git
cd computer-use-linux-isolated
sudo apt-get update
./install.sh --dependencies
./install.sh
~/.local/bin/computer-use-linux-isolated desktop start
~/.local/bin/computer-use-linux-isolated doctor
~/.local/bin/computer-use-linux-isolated desktop view
```

Review `install.sh` before running it. Only `--dependencies` uses sudo, for native packages. The build uses Cargo.lock. The normal install writes one executable to `~/.local/bin`, desktop resources and profiles to `~/.local/share/computer-use-linux-isolated`, a user service, and an application menu entry. After installing the application, it offers to install the skill for your agents. It does not edit your MCP configuration, alter the main desktop, or copy browser data. Include `~/.local/bin` in PATH if you want to omit the absolute path.

On repeat interactive installs, if `target/release/computer-use-linux-isolated` already exists and is executable, the installer asks `Rebuild before installing? [y/N]`. Press Enter to reuse it, or answer `y` to include source changes. Reusing a binary also reuses its embedded desktop manager; changes to the skill itself can still be installed without rebuilding. Use `./install.sh --rebuild` to run Cargo without the rebuild prompt, optionally combined with `--skip-skill`. Fresh installs and noninteractive runs always run Cargo's normal incremental build. This prompt does not interrupt a build already in progress.

XFCE supplies the Applications menu, taskbar, app finder, terminal, file manager, and normal window controls. These are standard packaged components, not a custom desktop UI. We supervise the components directly instead of launching another login manager or importing the host session environment.

The user service starts at login. Reconnecting an MCP client starts it if needed. Settings and app profiles survive restarts; running application windows and unsaved work do not. Startup before login requires separately enabling user lingering with `loginctl enable-linger YOUR_USERNAME`; installation does not enable this automatically.

Display `:199`, resolution `1600x1000`, and loopback VNC port `5999` are currently fixed. An occupied display causes failure, never attachment to an existing desktop. Only one instance per Unix account/machine is supported in this first version.

## Connect an MCP host

Use your absolute executable path and `mcp` argument. Generic MCP JSON:

```json
{
  "mcpServers": {
    "computer-use-linux-isolated": {
      "command": "/home/YOUR_USERNAME/.local/bin/computer-use-linux-isolated",
      "args": ["mcp"]
    }
  }
}
```

Disable any old `computer-use-linux` MCP entry so models do not accidentally select the upstream server. Do not install `@agent-sh/computer-use-linux` as a substitute: that package is upstream and can control the main session. This fork currently distributes through source installation, not npm or crates.io.

The installer asks `Install the skill for your agents? [Y/n]`. Accept to run the [skills CLI](https://github.com/vercel-labs/skills) against this local checkout, then select your harnesses and the recommended Symlink installation method. Node.js/npm with `npx` is required only for this optional step. The CLI may download its own npm package, but the skill comes from the checkout rather than another GitHub download.

Use `./install.sh --skip-skill` to install or update only the application. Without an interactive terminal, the installer skips the skill step and prints the separate command. To install or refresh [the included model skill](skills/computer-use-linux-isolated/SKILL.md) later without rebuilding the application, run from the repository:

```bash
npx skills add . --skill computer-use-linux-isolated --global
```

Global installation applies to your user across projects. The CLI manages the shared installed skill and harness symlinks; these are not live links into this checkout. Run the command again after changing the skill. MCP server configuration remains a separate step in each harness. If you accept skill installation but `npx` is missing or the CLI fails, `install.sh` exits unsuccessfully and prints a retry command; the application remains installed.

You can also install the skill through your host's own skill mechanism. Models must check `doctor`, observe windows and modal dialogs before input, stop on isolation errors, and coordinate with the human viewer. Input actions are serialized by the MCP server, but there is no whole-task ownership lock or automatic human takeover detection.

## Commands

```bash
computer-use-linux-isolated --help
computer-use-linux-isolated desktop install
computer-use-linux-isolated desktop start
computer-use-linux-isolated desktop status
computer-use-linux-isolated desktop view
computer-use-linux-isolated desktop run thunar
computer-use-linux-isolated desktop run xfce4-terminal
computer-use-linux-isolated desktop run google-chrome
computer-use-linux-isolated doctor
computer-use-linux-isolated windows
computer-use-linux-isolated desktop stop
```

Install Chrome separately if wanted. Its supplied launcher always uses `~/.local/share/computer-use-linux-isolated/chrome-profile`. Sign in manually in the viewer once, including any keyring and MFA prompts. No passwords or cookies are imported. Do not run two Chrome instances against one profile; see [Chromium's profile documentation](https://chromium.googlesource.com/chromium/src/+/main/docs/user_data_dir.md). Browser extensions, sessions, and logins from the primary desktop do not automatically appear here.

Applications can read and write your normal files. They use separate XDG configuration/cache/data directories. Some apps enforce a single instance using their own sockets or ignore XDG settings; snap/Flatpak portals, GPU-heavy apps, audio integration, desktop logout buttons, and host Chrome web-app shortcuts may not work as expected. A second session cannot make every application share its running state. The supported Chrome entry avoids the primary profile, but arbitrary commands and third-party launchers are not a security sandbox. Use another user or VM if untrusted code must be contained.

MCP runs inside bubblewrap with private `/dev`, `/run`, `/tmp`, and networking, exposing only the dedicated filesystem X socket. uinput, ydotool, host session hydration, and portal input are disabled in the required build feature. App processes retain networking and normal user file permissions. X11/VNC bells and clipboard forwarding are disabled. The VNC listener accepts only localhost connections and requires a generated password stored with user-only permissions; do not expose port 5999 directly to a network.

## Update, diagnose, and remove

```bash
git pull --ff-only
./install.sh
# Close/save work first, then restart to load updated desktop resources:
computer-use-linux-isolated desktop stop
computer-use-linux-isolated desktop start
journalctl --user -u computer-use-linux-isolated.service
```

Pin a Git commit before installation if two computers must use the same source version. Cargo.lock pins Rust dependencies; distro package updates, browser updates, and the local Rust toolchain mean this is a repeatable setup, not a bit-for-bit reproducible OS image. The laptop prototype under `~/.local/share/computer-use-linux` is a separate installation and is not automatically migrated or deleted. Stop the old service before starting this one because both use `:199` and port 5999. Copy any old isolated Chrome profile only while both Chrome instances are stopped, preserving the old copy for rollback.

```bash
computer-use-linux-isolated desktop uninstall
rm ~/.local/bin/computer-use-linux-isolated
```

Uninstall removes the service and menu entry, preserving all profiles/settings/files. Remove the MCP entry and installed skill separately. Delete the data directory yourself only if you no longer need its browser logins and settings. Native distro packages are deliberately not removed because other applications may use them.

See [validation details](docs/validation.md) for the tested environment and remaining gaps.

## Development

```bash
cargo fmt --all -- --check
cargo test --locked --lib
cargo build --locked --bin computer-use-linux-isolated
python3 -m py_compile desktop/*.py
```

`desktop/manage.py` and `desktop/session.py` are embedded into the Rust binary at build time. Python 3 is a runtime dependency. Changes to those files require rebuilding the executable. A build with `--no-default-features` fails deliberately; it cannot turn this fork into a shared-input server.

The maintained branch excludes the abandoned MPX implementation and handmade GTK panel. Upstream compositor code remains internally for now, but the supported CLI always enters the managed X11 session. Upstream history and license attribution are retained. This fork's CI does not publish to upstream npm or crates.io accounts.
