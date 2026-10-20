# Kavi'ka: first physical Surface boot, Surface Laptop Studio, 20 October 2026

The diagnostic preview was booted from USB **on real Surface hardware for the first time**, on the Laptop Studio test machine, and the workspace switch worked repeatedly. Nothing was installed and the internal Fedora installation is unchanged.

This is the Surface Laptop Studio, not the Pro 8. Its results are evidence about the Pro 8, never proof of it.

## Image and media

| Item | Value |
|---|---|
| Image | `build/Kavika-OS-0.1.0-Surface-Pro-8-Live-Preview.iso` |
| SHA-256 | `bd8407d6393a12f8a5829ef15a86371b854f08834d9fd7df4a85ddbdc8820e0d` |
| Media | 4 GB removable USB stick, raw-written (`Fedora-KDE-Live-44` label, the preserved upstream one) |
| Media verification | Payload checked on the stick before boot: `boot/kavika-preview.cpio` and `boot/grub2/grub.cfg` hashes matched the built image exactly |
| Prior evidence for this hash | [VM boot record](vm-boot-2026-10-20-laptop-studio.md) (KDE desktop, Test Centre, Meta+F12, SELinux enforcing, 0 failed units) |

## Results as reported by the user

Reported directly after using the live session:

| Function | Result |
|---|---|
| Pointer / mouse input | **Works** |
| **Meta+F12 workspace switch** | **Works, tested many times, every time** |
| Speakers | **Work** |
| Microphone | **Works** |
| Camera | **Works** |
| Wi-Fi | **Works** |

No failures were reported. The repeated switching is the most significant item: it is the fourth independent confirmation of the B06 fix (build-level inspection, two KVM boots, and now physical hardware), and the first on real firmware rather than OVMF.

## Corroborating machine evidence

The report is user-supplied; these facts were observed independently on the machine afterwards:

| Observation | Value |
|---|---|
| Host | `Surface Laptop Studio`, 11th Gen Core i5-11300H, 15.4 GiB RAM |
| Current Fedora boot started | 2026-10-20 15:14:02 PST (the machine restarted between the test and this check) |
| USB stick afterwards | detached; `/dev/sda` no longer present |
| Internal disk | unchanged: `nvme0n1p1` vfat `/boot/efi`, `nvme0n1p2` ext4 `/boot`, `nvme0n1p3` btrfs `fedora` (root and `/home`) |
| Firmware boot entries | unchanged set (`Fedora` current); the one-shot USB boot registered no new entry |
| Installation performed | none; `liveinst` is guarded in the preview |

## Evidence status

**Proven on Surface hardware:** the image boots from USB on a real Surface; the desktop is usable with a pointer; Meta+F12 switches workspaces reliably under repeated use; speakers, microphone, camera and Wi-Fi all function on the stock Fedora kernel.

**Not tested, and not to be inferred from the above:**

- Suspend/resume and hibernate.
- Native touch, pen, touchpad gestures and slate/tablet mode. The read-only preflight found **no touchscreen or pen input device exposed by the stock kernel** on this machine, so touch should be expected to be absent until a linux-surface kernel is used; the pointer that worked may have been an external mouse.
- Bluetooth, battery reporting, thermal behaviour, display scaling and graphics performance.
- The Secure Boot path. This machine has Secure Boot disabled and its firmware platform is in Setup Mode, so the boot did **not** exercise a Secure Boot chain. The Pro 8's firmware state is unknown and must not be assumed to match.
- Any Windows content: none is included.
- The Pro 8 itself: Type Cover, its own touch/pen hardware, its 128 GB storage budget, and whether Linux plus a full Windows guest fits on it.

## Follow-ups

1. In the next live session, open the Kavi'ka Test Centre and **save the hardware report** to removable media, so the machine's own inventory is on record rather than transcribed by hand.
2. Test suspend/resume from the live session, and note whether the touchpad works without an external mouse.
3. Record what the firmware's USB boot sequence required, for the Pro 8.
4. Then boot the same stick, still without installing, on the Pro 8.

This remains a diagnostic preview: not an installation release, not approved for flashing as a product, and it contains no Windows workspace.
