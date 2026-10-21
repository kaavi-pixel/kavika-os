# Testing Kavi'ka OS on the HP Envy x360 (testinstall)

How to boot and evaluate the Kavi'ka preview on the HP Envy x360, **without touching
the Windows installation that is on it.**

> **Read this first.** The current image is a **diagnostic live preview**, not an
> installation release. It has no installer, no Windows guest and no swipe-to-Windows
> feature. Booting it from USB writes **nothing** to the Envy's disk; that is the whole
> point of this procedure. Do not install, do not repartition, do not change firmware or
> Secure Boot settings.

## The two machines, and why they are different

| Machine | Role | Notes |
|---|---|---|
| **HP Envy x360** (Ryzen 7 8840HS, 16 GB, 1 TB) | **The only install target** | AMD: AMD-V, Radeon 780M. Runs Windows today. Its internal disk is in **no** erase approval. |
| **Surface Laptop Studio** (i5-11300H, 16 GB, 256 GB NVMe) | Test machine | Intel Tiger Lake. Where the product must first "work perfectly". |

Because the Envy is **AMD** and the Laptop Studio is **Intel**, nothing platform-specific
measured on one transfers to the other. Treat every result as evidence for that machine
only.

## What this procedure tests, and what it does not

**Tests (host side, live session):**
- The image boots at all on AMD hardware (this would be the **first** Envy boot)
- KDE desktop, Test Centre, hardware report
- Meta+F12 workspace switching
- Wi-Fi, audio out, microphone, touchpad, Bluetooth, battery and thermals
- That the internal disk is untouched afterwards

**Does not test:**
- Windows in any form. There is no Windows guest in this image.
- Swipe-to-Windows. That feature does not exist yet.
- Any installer, persistence, recovery or update path.

## 1. Get the image and verify it

Use the rebuilt image whose workspace switch works. The copy in `~/Downloads` may be the
**older broken build** (`10074299…`) whose Meta+F12 does nothing, so always check the hash.

```bash
ISO=~/src/kavika-os/build/Kavika-OS-0.1.0-Surface-Pro-8-Live-Preview.iso
sha256sum "$ISO"
# must print:
# bd8407d6393a12f8a5829ef15a86371b854f08834d9fd7df4a85ddbdc8820e0d
```

If it does not match, do not use it. Rebuild from source instead of guessing.

## 2. Write the USB stick

Two ways, in order of preference.

### Preferred: the guarded writer in this repo

It refuses unless the target is a whole disk, removable (`RM=1`), on the USB transport,
not the system disk, unmounted, large enough, and named twice; it also verifies the hash
before and reads the image back off the stick afterwards.

```bash
cd ~/src/kavika-os
lsblk -o NAME,SIZE,RM,TRAN,LABEL,MOUNTPOINT,MODEL     # identify your stick first
udisksctl unmount -b /dev/sdX1                        # release it if mounted

sudo bash tools/write-preview-to-usb.sh \
  --iso build/Kavika-OS-0.1.0-Surface-Pro-8-Live-Preview.iso \
  --sha256-file build/Kavika-OS-0.1.0-Surface-Pro-8-Live-Preview.iso.sha256 \
  --device /dev/sdX --confirm-wipe /dev/sdX
```

Add `--dry-run` first to run every check and write nothing.

### Known obstructions

- **A large USB hard disk may report `RM=0`.** Some enclosures (a Seagate "One Touch", for
  example) do not advertise themselves as removable, so the guarded script will refuse
  them. That guard is deliberate: `RM` is how the script tells a USB stick from an internal
  disk. Prefer a normal flash drive for this.
- **The volume label stays `Fedora-KDE-Live-44`** after writing. That is expected: the
  Kavi'ka image is built on the Fedora KDE base and the live boot depends on
  `root=live:CDLABEL=Fedora-KDE-Live-44`, so the label is load-bearing. Only two files
  inside the image identify it as Kavi'ka: `/KAVIKA_README.TXT` and
  `/BOOT/KAVIKA_PREVIEW.CPIO`.
- A 4 GB stick is enough. The image is 3,370,319,872 bytes.

## 3. Boot the Envy from the stick

1. Power the Envy **off** completely.
2. Insert the stick.
3. Power on and repeatedly tap **F9** for the boot menu (**Esc** or **F10** enters the
   firmware setup; **F9** is the one you want).
4. Choose the USB device.
5. At the boot menu choose the **live session**. **Do not choose anything that says
   install.**

If the stick does not appear, re-check that it was written as a whole disk, and that USB
boot is enabled in the firmware.

## 4. What to check once it is up

- [ ] Reaches the KDE desktop
- [ ] Test Centre opens and runs
- [ ] Hardware report produces sensible output for AMD (CPU, GPU, memory)
- [ ] **Meta+F12 switches workspace, both directions.** This is the single most important
      check; it is the difference between the fixed build and the broken one
- [ ] Wi-Fi connects and passes traffic
- [ ] Audio out, microphone
- [ ] Touchpad (including tap-to-click and two-finger scroll)
- [ ] Bluetooth: pair one device
- [ ] Battery level reported, and sensible
- [ ] Display scaling and brightness keys
- [ ] Thermals and fan behaviour under light load

Note that the "touchscreen does not work on the stock kernel" finding is **Surface-specific**
(both Surfaces need the linux-surface kernel for touch and pen). It says nothing about the
Envy's touchscreen, which should be checked here on its own merits.

## 5. Confirm nothing was written to the disk

Before and after the test, record the disk layout so the claim "nothing was written" is
evidence rather than assertion:

```bash
lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINT
sudo blkid
```

The Envy should come back with the same partitions it had, and Windows should still boot
afterwards. If anything changed, stop and report it before doing anything else.

## 6. Record the result

Findings belong in the repo, not in chat. Add a page under `docs/validation/` named for
the date, and summarise it in `bugtracker.md`. Record at minimum:

- exact ISO SHA-256
- machine, and the fact that it was booted from USB, live, without installing
- each checklist item above, pass or fail
- anything that did not work, verbatim
- the before/after disk layout

Caveats are part of the result. A VM limitation must be reported, not quietly redefined as
out of scope.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Meta+F12 does nothing | You booted the older image. Check the ISO hash (step 1) |
| Stick not in the boot menu | Not written as a whole disk, or USB boot disabled in firmware |
| Boots straight to Windows | Firmware boot order; use F9 and pick the stick explicitly |
| Blank screen | Try a different display output; the image uses the stock Fedora kernel |
| Nothing identifies itself as Kavi'ka | Expected. See the label note in step 2 |

## Still ahead: installing to the Envy

Replacing Windows on the Envy is the project's end state, and it is deliberately gated. It
requires the Windows workspace and swipe integration, a real installer, the OS release
gates, and a **fresh explicit go-ahead at the moment of the write** with the exact disk
identified first. Nothing in this document authorises it.
