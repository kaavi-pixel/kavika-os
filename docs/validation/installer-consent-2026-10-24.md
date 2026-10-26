# Installer consent, media identity and the first physical install attempt

**Date:** 24 October 2026
**Scope:** the automated dnf/netinst installer (Path B) — media identity, the consent gate, and
what happens when it refuses.
**Machine:** Surface Laptop Studio (build and KVM verification). The physical attempt was made on
a separate machine booted from the Kavi'ka stick.
**Evidence:** `docs/evidence/install-console-2026-10-24.txt` (filtered serial, privacy-scanned:
no serials, UUIDs, MACs or IPs).

## Why this record exists

The installer was already proven to install correctly under KVM, so the interesting failures were
all in the **media and the refusal path** — the parts a KVM boot on a virtual CD never exercises.
Five defects were found and fixed in this arc, and the end-to-end install was re-proven on the
final code rather than assumed.

## The defect chain

| # | Defect | Caught by |
|---|---|---|
| D36 | Booting from **USB** died at GRUB with *"you need to load the kernel first"*, showing the stock Fedora menu with no Kavi'ka entry | Booting the ISO as a **USB device** instead of as a CD |
| D37 | A consent refusal left a **dead pane** where keystrokes did nothing, and the only visible error was a missing kickstart file that hid the real reason | Reproduced in KVM, then confirmed on hardware |
| D38 | The installation medium satisfied every target check, so naming the stick you booted from would erase the medium mid-install | Review while preparing a physical install |
| D39 | The refusal banner printed a copyable `/dev/sdX` template; the operator typed it verbatim and got a correct-but-bewildering `cannot inspect /dev/sd with lsblk` | The operator's photograph of the banner on real hardware |
| D40 | The USB writer **rejected stock Fedora ISOs**, demanding the Kavi'ka menu in the ESP of any image it wrote | Writing stock Fedora to an external drive |
| D42 | The **offline ISO could not install from USB at all**: its kickstart used `cdrom` as the source, which needs an optical drive, so Anaconda reported `Error setting up repositories` and fell to a prompt that cannot install | Rehearsing the real install invocation instead of a CD boot |
| D43 | The offline repo could not satisfy **`@anaconda-tools`**, which Anaconda installs implicitly; the package transaction died with `No match for argument: nvme-cli` | The same rehearsal, after D42 was fixed and could no longer mask it |

D36 and D40 share a root cause worth naming: **a byte-perfect copy of a broken image is still
broken, and a check written for one image rejects a different valid one.** D36 was masked because
a `-cdrom` boot reads a different config than a USB boot; D40 was masked because the writer had
only ever been pointed at Kavi'ka builds.

## End-to-end install on the final code

Booted the built ISO as a USB device with `kavika.target=/dev/vda` (via the builder's
`--test-target`, which bakes the consent tokens into the entry) against a 300 GiB whole disk.

```
Creating disklabel on /dev/vda
Creating efi on /dev/vda1
Creating ext4 on /dev/vda2 .. vda5
KAVIKA CONSENT: storage scoped to /dev/vda (compact=0)
KAVIKA-VERIFY: os-release=Kavika
KAVIKA-VERIFY: default target = graphical
KAVIKA-VERIFY: display manager enabled: sddm
KAVIKA-VERIFY: default.target -> /usr/lib/systemd/system/graphical.target
KAVIKA-VERIFY: overlay delivered from /run/install/repo/kavika-overlay.cpio
KAVIKA-VERIFY: ESP fallback EFI/BOOT/BOOTX64.EFI installed
KAVIKA-VERIFY: pkg qemu-kvm / swtpm / edk2-ovmf / mtools / 7zip / parted / dosfstools
2427/2427 packages
```

The install completed and rebooted into the installed system:

```
Welcome to Kavi'ka OS 0.1.0 (Live Preview, Fedora KDE 44)!
```

That last line is **D41** — the installed system reuses the live-preview branding. Cosmetic, open.

## Refusal behaviour, verified by firing it

Each refusal was **fired and observed**, not merely grepped for in the source:

| Case | Command line | Result |
|---|---|---|
| No target named | (none baked) | `REFUSED: no kavika.target= on the kernel command line` + banner, nothing written |
| Target is the boot medium | `kavika.target=/dev/sda` | `REFUSED: /dev/sda carries the installation media booted from; name a different disk` |
| Target is a placeholder, not a device | `kavika.target=/dev/sdX` (operator's real mistake) | `REFUSED: cannot inspect /dev/sd with lsblk` |

In every case the banner states that nothing was written, and the misleading
`Unable to open input kickstart file` error is gone (count: 0).

## Offline media, end to end, after D42 and D43

The offline ISO was re-rehearsed with the repository fix in place, booted as a USB device:

```
3) [x] Installation source                     <- no "Error setting up repositories"
Creating disklabel on /dev/nvme0n1
Creating efi on /dev/nvme0n1p1 .. nvme0n1p5
Downloading 2464 RPMs, 3.54 GiB / 3.54 GiB (98%) done.
Installing rootfiles.noarch (2464/2464)
KAVIKA-VERIFY: os-release=Kavika
KAVIKA-VERIFY: default target = graphical
KAVIKA-VERIFY: display manager enabled: sddm
KAVIKA-VERIFY: overlay delivered from /run/install/repo/kavika-overlay.cpio
KAVIKA-VERIFY: ESP fallback EFI/BOOT/BOOTX64.EFI installed
reboot: Restarting system
```

The whole install now runs **from the media's own repository, with no optical drive present**,
and reboots into the installed system.

## Installing to a physical disk via a VM

The Envy's NVMe was installed by passing the **physical disk** into a QEMU guest as an emulated
**NVMe** device, so the guest targets `/dev/nvme0n1` exactly as the real machine does. This
deliberately avoids both previous failure modes: there is no boot menu to catch and no device name
to mistype, because `--test-target` bakes the consent tokens into the entry.

Three things this method requires, each learned the hard way:

- **`-no-reboot`.** The kickstart ends with `reboot`; without it the guest boots the install media
  again and reinstalls in a loop.
- **The installer must not resolve by `/dev/sd` letter.** The wrapper script resolves the target by
  model and serial and refuses this machine's system disk, a partition, or the install media itself.
- **The initramfs must carry the NVMe driver**, or a disk installed in a VM will not boot in real
  hardware. Checked after install, not assumed.

## Media identity

- Volume label renamed to **`KAVIKA`** with *every* upstream label reference rewritten, including
  the `search --no-floppy --set=root -l '...'` line — otherwise a Kavi'ka stick and a stock Fedora
  netinst are indistinguishable at boot and in a file manager.
- The **ESP's own GRUB config** is patched too, because UEFI booting from USB reads that file and
  not the ISO9660 one (D36).
- The writer reads the ESP of **both** the image and the written device and refuses when they
  differ, and refuses when the ESP searches for a label the image does not carry.

## Verification method note

Every installer claim here was checked by **booting and reading the console**, including booting
the ISO as a *USB device* rather than a CD. Grepping the kickstart for a new string proves the
text exists; it does not prove the behaviour. Two of these defects (D36, D40) were invisible to
the checks that were passing at the time.

## Still open

- **D41** — installed system brands itself "Live Preview" (cosmetic, needs a design decision).
- **The physical install is under way.** The Envy's own NVMe was attached to the build machine and
  Kavi'ka is being installed to it directly, by passing the disk into a QEMU guest as an NVMe
  device (above). This replaces the failed on-target attempts, which never got past the boot menu
  and the hand-typed consent token. **Still unproven until the disk boots in the Envy itself** —
  installing in a VM and moving the disk to real hardware is precisely where a host-only initramfs
  bites.
- The live-preview ISO still offers a dead `Install Kavi'ka OS` entry that should be stripped.
- Initial Setup's graphical rendering on first boot remains unverified.
