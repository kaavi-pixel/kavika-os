# GNOME desktop variant

Status: **implemented in the installer, awaiting end-to-end boot validation**.

## Build

KDE remains the default and is unchanged. To build the GNOME network installer:

```sh
PATH="$HOME/.local/bin:$PATH" ~/src/kavika-build-venv/bin/python \
  tools/build-netinst-install.py \
  --base ~/Downloads/Fedora-Everything-netinst-x86_64-44-1.7.iso \
  --output build/Kavika-OS-0.1.0-gnome-network.iso \
  --desktop gnome
```

For a disposable QEMU target, add `--test-target /dev/nvme0n1`.

The current offline RPM repository contains the KDE dependency set. **Do not use `--repo-dir`
for a GNOME build until the GNOME group and its dependency closure have been added.**

## What changes

- `@kde-desktop-environment` → `@workstation-product-environment`
- `sddm` → `gdm`
- installed identity says `Fedora GNOME 44` rather than `Fedora KDE 44`
- KWin/Plasma-only overlay files are removed (`kwinrc`, device automounter config,
  `plasma-welcome`, and the KWin shortcut script)
- a first-login `kavika-gnome-session-setup` requests two static workspaces with gsettings

The consent gate, storage layout, `calebz` account creation, D41/D46 handling, generic initramfs,
and Windows provisioning tooling are shared with KDE.

## What is not claimed

**Swipe-to-Windows is not established on GNOME.** KWin's built-in three-finger desktop switch and
its two-desktop `kwinrc` are not portable. GNOME uses a different workspace model, and the KWin
D-Bus switch in `kavika-windows-workspace` cannot switch GNOME workspaces. The two-workspace
gsettings configuration is only a starting point; touchpad behaviour and the full-screen guest
must be validated separately on GNOME hardware.

The live preview is also not covered: it would need a Fedora Workstation base rather than the
KDE live base.
