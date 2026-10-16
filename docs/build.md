# Kavi'ka OS: diagnostic preview build

This builder composes an experimental, non-installation live image from one exact upstream Fedora KDE ISO. It neither installs an OS nor mounts/chroots into user disks; the full RPM-based distribution pipeline remains future work.

## Pinned input

| Input | Value |
|---|---|
| Base | `Fedora-KDE-Desktop-Live-44-1.7.x86_64.iso` |
| Base SHA-256 | `c8295961d4c41adbf785a31a17c21a971d3b7415fda72dcad0c11c49577bf03a` |
| Architecture | x86_64 |
| Kernel | `6.19.10-300.fc44.x86_64`, unchanged upstream kernel |
| Payload source | `image/live-preview/root/` and original `assets/branding/kavi-ka-os-logo.png` |
| Windows, guest disk, secrets | Not included |

Obtain the base and signed checksum through the [Fedora KDE download page](https://fedoraproject.org/kde/download); the build performed for this preview verified the checksum signature as well as the ISO hash. The script enforces the pinned hash but does not independently download or verify a signing key.

## Builder requirements and commands

Use an isolated Linux builder with Python 3.11 or newer, `xorriso`, GNU `cpio`, `grub-script-check` and `implantisomd5` from isomd5sum. Allow room for the approximately 3.37 GB base, another approximately 3.37 GB output and temporary overlay files; no root privileges are needed for composition.

From a clean repository checkout, run:

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

Output must be a new `.iso` file, never a device or existing file. The builder emits the ISO, a SHA-256 sidecar and a JSON manifest containing input/output hashes, original-logo hash and payload-file hashes. Do not commit binary images, guest disks or raw device reports.

## Composition mechanism

The original ISO's `LiveOS/squashfs.img` contains EROFS on this pinned build; the builder does not unpack or rewrite it. It adds a cpio archive containing `/updates`, appends it as a second GRUB initrd, and relies on the pinned initramfs's existing `20-apply-live-updates.sh` pre-pivot hook to copy those files into the RAM-backed live root.

The builder preserves the Fedora live-root label and uses xorriso's boot replay to preserve the existing hybrid/UEFI structure. It changes menu wording, adds serial logging for the diskless VM check, and regenerates the embedded media MD5. This mechanism is tied to the exact verified upstream image, not a generic recipe for arbitrary Fedora releases.

A `systemd-tmpfiles-setup.service` drop-in relabels affected ancestor directories non-recursively and the small payload recursively, after SELinux policy is loaded but before ordinary services and live-user setup. The earlier pre-pivot attempt did not correct the observed `tmpfs_t` directory labels and was removed. This affects only the RAM-backed live root; SELinux is not disabled. Fedora's supported `livesys-session-extra` hook reapplies workspace defaults after the upstream KDE setup writes its own `kwinrc`.

The pinned upstream GRUB config declares functions inside an `if` block; both the booted GRUB and the build-host parser reject that structure. The builder moves the video function to top level while preserving its platform-specific module choices. Menu branding uses quote-neutral “Kavika”; the apostrophe is preserved in the desktop branding. The complete generated configuration must pass `grub-script-check` before ISO composition.

The original logo is copied without changes. Python bytecode/cache files are excluded from the payload; no sandbox paths or compiled test caches should be packaged.

## Validation scope

Run output SHA-256 and embedded media checksum checks, inspect boot metadata, then test a diskless UEFI VM. No writable hard disk should be exposed during the first boot check.

Record whether KDE, Test Centre, hardware reporting, workspace toggle and installer guard work, with exact tool versions. Physical Surface boot/input, Secure Boot, Windows, installation, persistence and performance are separate gates. See [the build validation record](validation/live-preview-0.1.0.md).

Do not claim byte-identical reproducibility from a single successful build. Fixed payload timestamps and a pinned base aid repeatability, but independent clean builds and their complete inputs still need comparison.
