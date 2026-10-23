# Windows provisioning: the tooling and its first end-to-end proof

Recorded 23 October 2026, on the Surface Laptop Studio. This covers the Windows track's
change from "the image ships a launcher nobody can use" to "an installed system can
provision, start and be handed a Windows workspace".

Nothing here writes to a physical disk. The Windows guest is a private QCOW2 in the
repository's test directories; the media are plain files.

## What changed

| Piece | Before | Now |
|---|---|---|
| Boot ESP + answer stick build | documented by hand in [windows-install-recipe.md](../windows-install-recipe.md); no tool | `tools/kavika-windows-media.py` builds both from the ISO |
| Installing Windows | run the launcher by hand with the right five arguments | `kavika-windows-provision --iso <iso>` does it |
| First-login offer | none | `kavika-windows-optin` (T20) - asks once, never provisions on its own |
| Shipping | the launcher shipped; nothing else | launcher, media builder, provisioner, opt-in and `autounattend.xml` all ship |

The media builder produces two plain files, with no root and no loop mount (the FAT is
written through mtools at a partition offset):

- `esp.img` - 1 GiB GPT, one ESP (FAT32, label `KAVIKAESP`) carrying the ISO's own
  `/efi/boot/bootx64.efi` (3,087,400 B), `/boot/bcd` (16,384 B), `/boot/boot.sdi`
  (3,170,304 B), the whole `/efi/microsoft/boot/` tree and `/sources/boot.wim`
  (619,980,682 B).
- `af.img` - 64 MiB FAT32, label `KAVIKAANSW`, with `autounattend.xml` at the root.

Verified after a build: `parted` prints the GPT with the ESP flagged `boot, esp`, and `mdir`
lists every file at the expected size.

## The end-to-end proof

The media were built by the new tool from
`Windows11_Client_x64_en-gb_26300_9457.iso` and handed to the launcher exactly as
`kavika-windows-provision` does.

1. **Setup booted from the builder-made ESP.** The serial shows the firmware failing the
   DVD (`Time out`, the known `cdboot.efi` behaviour, D17) and then starting
   `Boot0005 "QEMU QEMU USB HARDDRIVE"` - the ESP.
2. **Windows installed and reached the desktop.** `windows11.qcow2` grew to ~18 GB and the
   guest booted `Boot0009 "Windows Boot Manager" from HD(1,GPT,...)/\EFI\Microsoft\Boot\bootmgfw.efi`
   - the **target disk's own ESP**, so the D21 fix holds with the new media.
   Screenshot: `docs/evidence/win-media-desktop-2026-10-23.png`.
3. **The guest is self-contained.** A second boot with **only the disk attached**
   (`--reuse`: no ISO, no ESP, no answer stick; `launch.txt` records `iso=None`,
   `physical_disks=none`) reached the desktop again, this time from
   `Boot0004 "UEFI QEMU NVMe Ctrl KAVIKA0000000001 1"`.
   Screenshot: `docs/evidence/win-media-selfcontained-2026-10-23.png`.
4. **Firefox opens in the guest.** Installed inside the guest
   (`winget install Mozilla.Firefox`) and launched from Start; a full Firefox window with
   its onboarding modal is on screen.
   Screenshot: `docs/evidence/win-media-firefox-2026-10-23.png`.

## Two defects this work found and fixed

**D30 - the workspace launcher could never start a guest.** `tools/launch-windows-vm-linux.py`
ran `vm_dir.mkdir(parents=True)` unconditionally, *after* the `--reuse` validation that
requires the directory to exist. So `--reuse` (and therefore `kavika-windows-workspace`,
which passes it) failed with `File exists` on every provisioned guest. The `--reuse` tests
passed because they used `--dry-run`, which returns before that line. Fixed to
`mkdir(parents=True, exist_ok=True)`; the boot in step 3 above is the real-run proof.

**D31 - the installed system could not run the shipped tooling.** The kickstart installed
`mtools` but not `7zip`, `parted` or `dosfstools`, which the media builder needs (extract the
Windows UDF ISO, partition the ESP image, format the answer stick). Fixed in the kickstart
`%packages`, with the post-install verification extended to check them. Verified by a real
install:

```
KAVIKA-VERIFY: overlay delivered from /run/install/repo/kavika-overlay.cpio
KAVIKA-VERIFY: os-release=Kavika
KAVIKA-VERIFY: pkg qemu-kvm-10.2.2-1.fc44.x86_64
KAVIKA-VERIFY: pkg swtpm-0.10.2-1.fc44.x86_64
KAVIKA-VERIFY: pkg edk2-ovmf-20260812-8.fc44.noarch
KAVIKA-VERIFY: pkg mtools-4.0.49-3.fc44.x86_64
KAVIKA-VERIFY: pkg 7zip-26.04-1.fc44.x86_64
KAVIKA-VERIFY: pkg parted-3.6-15.fc44.x86_64
KAVIKA-VERIFY: pkg dosfstools-4.2-18.fc44.x86_64
```

## What is not proven here

- **The full nested path.** This run proves the tooling works and that an installed system
  *carries* it. It does not run `kavika-windows-provision` inside a booted Kavi'ka and watch
  Windows install there; that needs the interactive first-boot (initial-setup) to be
  completed, which is a user step, or a serial getty added to the installed system.
- **The desktop switch and the swipe.** `qdbus6 ... setCurrentDesktop` and the three-finger
  gesture still need a KDE host with a touchpad (see [windows-workspace.md](../windows-workspace.md)).
- **The opt-in dialog's appearance.** Its script is tested (silent without qemu, answered
  once, marker respected), but no KDE session has drawn the kdialog.
- A `[FAILED] Failed to start systemd-tmpfiles-setup` line appeared during the install's
  `%post`. It did not stop the install (2452/2452 packages, `%post` verification ran), but it
  is not yet explained and is recorded rather than dismissed.

## Artefacts

| File | SHA-256 |
|---|---|
| `Kavika-OS-0.1.0-netinst-offline.iso` | `1ff7308e897a70b6e932aecdd475a8cb616b132a665b5eae3cf9bd23d0470032` |
| `Kavika-OS-0.1.0-netinst-network.iso` | `18d67f92cfb734e07436e92e1be8db9cfb75adb2bd15f51564532ccdba73ea0a` |
| `Kavika-OS-0.1.0-Surface-Pro-8-Live-Preview.iso` | `0d5a39a7188930c002a873e0fa57e9f6cc6e90f5df7ae5ecc8453b95d3beeeb4` |

All three pass `checkisomd5`. The overlay payload of each was extracted and checked to
contain the eight Windows pieces (`kavika-windows-workspace`, `-provision`, `-optin`, the
opt-in autostart, `launch-windows-vm-linux.py`, `kavika-windows-media.py`,
`autounattend.xml`, `WINDOWS.txt`).
