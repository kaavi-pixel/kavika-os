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
- **Physical install on the Envy is unproven.** The operator's attempt reached the consent gate,
  refused on a mistyped placeholder, and has not yet been retried. Nothing has been written to any
  machine by this installer outside KVM.
- The live-preview ISO still offers a dead `Install Kavi'ka OS` entry that should be stripped.
- Initial Setup's graphical rendering on first boot remains unverified.
