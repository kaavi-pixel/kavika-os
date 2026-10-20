# Kavi'ka OS: diagnostic preview build

The repository contains a Fedora-based live diagnostic preview, **not** the full Kavi'ka Linux/Windows product and not an installation release. This guide supports reproducing the pinned source build; booting and installation require separate validation gates.

## Pinned input

| Input | Value |
|---|---|
| Base | `Fedora-KDE-Desktop-Live-44-1.7.x86_64.iso` |
| Base SHA-256 | `c8295961d4c41adbf785a31a17c21a971d3b7415fda72dcad0c11c49577bf03a` |
| Architecture | x86_64 |
| Kernel | Fedora's upstream stock kernel; no Surface-specific kernel |
| Payload source | `image/live-preview/root/` and `assets/branding/kavi-ka-os-logo.png` |
| Windows VM, Comet, guest disk, credentials | Not included |

Obtain the Fedora ISO from the official [Fedora KDE download page](https://fedoraproject.org/kde/download) (mirror directory `releases/44/KDE/x86_64/iso/`) and follow Fedora's checksum/signature verification instructions. The builder independently checks the pinned SHA-256, but does not retrieve or verify Fedora's signing key itself.

## Build prerequisites and commands

The validated recipe targets an isolated Linux builder with Python 3.11+, `pycdlib` 1.22+, xorriso, GNU cpio, `grub-script-check`, `implantisomd5` (isomd5sum), and Bash. Keep at least 10 GB of free scratch space. Never pass a block device as an image output, mount or chroot into the host's drives, or run Fedora installer/image tools on an everyday host.

On Fedora the GRUB checker is packaged as `grub2-script-check` (in `grub2-tools`) while the builder looks for the name `grub-script-check`; provide the name the builder expects, for example:

```sh
ln -sf /usr/bin/grub2-script-check ~/.local/bin/grub-script-check
```

From a clean repository checkout:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
bash -n image/live-preview/root/usr/local/bin/kavika-live-session
bash -n image/live-preview/root/usr/local/bin/kavika-test-centre
bash -n image/live-preview/root/usr/bin/liveinst
mkdir -p build
python3 tools/build-live-preview.py \
  --base /absolute/path/Fedora-KDE-Desktop-Live-44-1.7.x86_64.iso \
  --output "$PWD/build/Kavika-OS-0.1.0-Surface-Pro-8-Live-Preview.iso"
```

The output must be a new `.iso` in an existing directory. The builder produces an ISO, SHA-256 sidecar and JSON manifest of the base, output, builder, logo and payload hashes. Do not commit built ISO files, VM disks, or raw hardware reports.

The builder normalizes staged shell payloads and runs `bash -n` on the three packaged shell entry points, then checks generated GRUB syntax with `grub-script-check` before composition. These are syntax/build preflights only; they do not establish that the live desktop or Kavi'ka services boot.


The builder retains the pinned Fedora squashfs and appends a `newc` cpio `/updates` archive to the initramfs path. It relies on the pinned Fedora initramfs `20-apply-live-updates.sh` hook to apply that overlay to the RAM-backed live root at boot. It changes the GRUB menu, preserves the upstream live volume label, adds serial logging, and regenerates Fedora's embedded media checksum. This mechanism is tied to the exact pinned Fedora ISO, not a generic Fedora build recipe.

The staged payload scripts are normalized to Unix line endings, syntax-checked with `bash -n`, and the generated GRUB configuration is checked with `grub-script-check` before composition. These checks are build preflights, not GUI boot evidence. SELinux remains enforcing; the overlay label fix and `livesys-session-extra` workspace setup are project-specific.

Before booting the preview anywhere, verify the image SHA-256 sidecar and embedded media check. The exact local build record and current hash are in [the validation record](validation/live-preview-0.1.0.md); do not use the older tracked sidecar/manifest for the current local ISO. Boot a fresh, disposable UEFI VM with no physical disks or writable shared host folders before considering physical preview testing. Record the exact tested ISO hash and boot result. The QEMU-on-Windows helper, if used, performs software emulation and is slow; a started VM process is not evidence that KDE booted successfully.

Physical Surface boot, Secure Boot, native Surface input, Windows/Comet, file sharing, gestures, performance, persistence and installation are separate gates. This preview does not include Windows or a supported internal-disk installer. It must not be flashed as an install/release image or used as a daily operating system.

Do not claim reproducible builds based on one build. A pinned base, fixed payload timestamps and manifests aid repeatability, but independent clean builds and a full recorded toolchain are required to prove it.
