# Envy physical install and boot test — 24 to 27 October 2026

Single consolidated record of the physical-install arc. This exists so that nothing important
lives only in a chat transcript: the conversation is compacted, files are not.

## Goal and route

Get Kavi'ka OS onto the **HP Envy x360's own ~954 GB NVMe**, while that disk is attached to the
build machine through a USB enclosure, by booting the installer inside QEMU on the build machine.
The guest sees the physical disk as an emulated NVMe (`/dev/nvme0n1`), so the device name matches
what it will be on the Envy. No install media is needed on the Envy at all for this route.

The Envy's Windows is already gone (user-reported 24 October 2026, wiped accidentally), so there
is nothing left there to preserve.

## Disk identities — never use a /dev/sd letter

Letters moved repeatedly during this work (sda, sdb, back to sda). Everything is keyed on
model + serial.

| Role | Device | Detail |
|---|---|---|
| Build machine's own disk | 237.5 GB Hynix `HFM256GD3GX013N` | **never a target**; carries the repo and ISOs |
| Install target | 953.9 GB Samsung `MZVL81T0HELB-00BH1`, serial `S79UNX0XA54624` | the Envy's NVMe, in a USB enclosure |
| Stable target path | `/dev/disk/by-id/ata-SAMSUNG_MZVL81T0HELB-00BH1_S79UNX0XA54624` | what every script resolves |
| Install medium | 931.5 GB Toshiba `MQ04UBF100`, label `KAVIKA` | a USB hard disk, not a flash stick |

## Images

| Image | SHA-256 |
|---|---|
| `~/envy-install/install-to-nvme0n1.iso` (test-consented, targets `/dev/nvme0n1`) | `8982cc3d897063ef8fd77f9411ed72ea4ba0d1a6342272be2c120c21a0e72711` |
| `build/Kavika-OS-0.1.0-netinst-offline.iso` | `e88de828848cc9caa6961abdd4e98879d3f872185a82b798d360013e955476af` |
| `build/Kavika-OS-0.1.0-netinst-network.iso` | `e86a38088b3dcf32bb918acd263f0083e242e0c2dab9d7ffcf9e61b842aea6fd` |
| Fedora KDE 44 base (pinned input) | `c8295961d4c41adbf785a31a17c21a971d3b7415fda72dcad0c11c49577bf03a` |

The test-consented image is what the physical install actually used. It carries
`kavika.target=/dev/nvme0n1 kavika.confirm=/dev/nvme0n1` on the kernel command line, so the
operator does not have to type anything at a GRUB menu. It is NOT a shipped image.

## Defects found and fixed in this arc

| ID | Symptom | Root cause | Fix |
|---|---|---|---|
| D36 | `you need to load the kernel first` | UEFI reads GRUB config from the **appended ESP**, which still searched for the Fedora label | builder patches and replaces that partition |
| D37 | dead pane, typing did nothing | consent refusal was masked by a missing `%include` file | seed the include, print a bordered refusal banner |
| D38 | the boot stick could be its own target | medium not excluded | refuse the parent of `blkid -L KAVIKA` |
| D39 | operator typed `/dev/sdX` literally | banner showed a placeholder | banner lists the machine's real disks |
| D40 | writer refused a stock Fedora ISO | check demanded a Kavi'ka menu | compare device ESP config with the image's own |
| D41 | install brands itself **Live Preview** | `/etc/os-release` never updated | **still open** |
| D42 | offline USB install fell back to interactive | kickstart said `cdrom`, but there is no optical drive | `inst.repo=hd:LABEL=KAVIKA:/` |
| D43 | `No match for argument: nvme-cli` | `@anaconda-tools` members missing from the curated repo | packages and dependencies added |
| D44 | initramfs was host-only | a VM-installed system can lack the physical machine's drivers | `dracut-config-generic` |
| D45 | root-password emergency mode risk | ESP UUID in fstab could be stale | reconcile UUID from blkid, add `nofail` |

Commits: `0dd1dd9`, `22d1f39`, `3a8a245`, `318e265`, `33f2679`, `2bd8831`, `c025355`,
`2810244`, `7277772`, `b60efb1`, `f62879a`..`0a6a002`, `e7ca365` (record).

## Operator-run scripts (all need sudo; the harness blocks raw device writes)

`~/envy-install/`:

- **`run-install.sh`** — resolves the target by model+serial, refuses the build machine's own
  disk, any partition, the install medium and any too-small disk, unmounts target filesystems,
  then boots the test-consented ISO in QEMU with the physical disk attached as an emulated NVMe.
- **`run-boot-test.sh`** — boots the **installed** disk with no media attached.
  `-snapshot` means the physical disk is only ever **read**; guest writes go to a throwaway file.
  `-no-shutdown` keeps the VM around so the last screen can be captured. Deliberately **no**
  `-no-reboot`: a fresh install's first boot does an SELinux autorelabel and then reboots, and
  killing the VM there looks exactly like a crash.
- **`capture-screen.py`, `capture-series.py`** — ask the QEMU monitor for a `screendump`. The
  monitor socket belongs to the root QEMU process, so these are run with sudo.
- **`kavika-rehearsal3/`** — rehearsal against a fake 300 GB NVMe; reached 2464/2464 packages.

### Reading a VM screen without a vision provider

The installed kernel logs to the **VGA console, not to serial**, so the serial log stops after
GRUB's `Booting ...` even on a perfectly healthy boot. Do not read that silence as a failure.

To see the screen: `screendump` via the monitor, then OCR locally. The vision provider was
unavailable in this environment, so tesseract was fetched and **extracted without installing**:

```bash
dnf5 download --resolve --destdir /tmp/tessrpms tesseract tesseract-langpack-eng
for r in /tmp/tessrpms/*.rpm; do rpm2cpio "$r" | (cd /tmp/tess && cpio -idm --quiet); done
LD_LIBRARY_PATH=/tmp/tess/usr/lib64:/tmp/tess/usr/lib \
  /tmp/tess/usr/bin/tesseract screen.png stdout \
  --tessdata-dir /tmp/tess/usr/share/tesseract/tessdata
```

A quick colour histogram also separates the two cases cheaply: a text console is ~92% black with
about five colour buckets; a GUI has hundreds.

## Evidence — the install itself

`~/envy-install/serial.log` after the physical write:

```
KAVIKA-VERIFY: ESP UUID matches fstab (20A9-0F92)
KAVIKA-VERIFY: /boot/efi marked nofail
KAVIKA-VERIFY: ESP fallback EFI/BOOT/BOOTX64.EFI installed
KAVIKA-VERIFY: os-release=Kavika
KAVIKA-VERIFY: default target = graphical
KAVIKA-VERIFY: display manager enabled: sddm
reboot: Restarting system
```

Confirmed directly on the mounted disk, not just from the log:

- **ESP populated**: `EFI/BOOT/BOOTX64.EFI` (1,036,008 bytes) and `EFI/fedora/{shim,grub}*`.
  Earlier in the arc the same partition was found **empty**, which is what produced the Envy's
  `3F0` firmware "no OS" screen.
- **fstab**: `UUID=20A9-0F92 /boot/efi vfat,nofail ...` matching the real ESP UUID.
- **Initramfs generic**: `/usr/lib/dracut/dracut.conf.d/02-generic-image.conf` contains
  `hostonly="no"`, and the image is **237,877,441 bytes** versus **43.9 MB** on the previous
  host-only build. The size difference is independent corroboration that all storage drivers,
  including `nvme`, are present.

## Boot test findings (27 October 2026)

The installed disk was booted in QEMU with no media attached.

**Good:** GRUB 2.12 loads the installed kernel, and a normal systemd boot brings up the full
desktop stack — `polkit`, `accounts-daemon`, `udisks2`, `upower`, `ModemManager`, `chronyd`,
`abrtd`, `NetworkManager-dispatcher`, `sshd`, `virtqemud`, `initial-setup.service`. No emergency
mode, no `Give root password for maintenance`, no failed units in the captured text.

**Problems seen on screen:**

```
dnf5(2296): segfault at 0 ... error 6 in libstdc++.so.6.0.36
coredump: 2296(dnf5): /usr/lib/systemd/systemd-coredump pipe failed
```

**Not a fault:** `tsc: Marking TSC unstable due to clocksource watchdog` and the large timestamp
jumps are VM clock artifacts and will not occur on the Envy.

**Still unproven: that the boot reaches a graphical desktop.** Every captured frame was a text
boot log. No `sddm.service` start line appears in the serial log, and no greeter, wizard or
desktop was observed. The VM has since exited.

## Open items, in order

1. **Prove the GUI.** Re-run `sudo bash ~/envy-install/run-boot-test.sh`; it now captures the
   screen automatically after 90 s and keeps QEMU's own error log.
2. **Investigate the `dnf5` segfault** if it recurs. A crashing package manager on first boot is
   a defect even when it does not block the desktop.
3. **Refit the disk in the Envy and boot on real hardware.** The actual target; nothing in KVM
   substitutes for it.
4. **D41** — installed system still announces itself as "Live Preview".
5. **Live preview's `Install Kavi'ka OS` entry** is still a known dead end.
6. **KDE → GNOME** remains an open design question: the desktop swap is mechanical, but the
   three-finger swipe is **not** portable and needs real testing on a touchpad host.

## What is explicitly not proven

- A graphical desktop on the installed system.
- Any boot on the Envy's own hardware.
- Suspend/resume, Secure Boot, or the AMD-specific graphics path.
- Whether the earlier empty-ESP incident can recur. It has not been root-caused; the current
  disk's ESP is verified populated, but the original loss is unexplained.
