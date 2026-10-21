# Kavi'ka preview booted live on the HP Envy x360

**Date:** 21 October 2026
**Machine:** HP Envy x360 (Ryzen 7 8840HS, 16 GB, 1 TB), AMD
**Image:** the rebuilt preview, SHA-256 `bd8407d6393a12f8a5829ef15a86371b854f08834d9fd7df4a85ddbdc8820e0d`
**Method:** booted live from USB. **Nothing was installed.** No partition was created, and
no firmware or Secure Boot setting was changed.

## Why this matters

This is the **first boot of Kavi'ka on the HP Envy**, which is the project's only install
target. Everything before it was measured on the Surface Laptop Studio (Intel Tiger Lake).
The Envy is **AMD** (AMD-V, Radeon 780M), so this is the first AMD data point in the
project and the first evidence that the image boots on the eventual target hardware at all.

It is a live boot only. It does not demonstrate installation, persistence, Windows, or the
swipe-to-Windows feature, none of which exist in this image yet.

## Reported results

User-reported, immediately after the boot:

| Check | Result |
|---|---|
| Boots live from USB on the Envy | **Yes** |
| Meta+F12 switches workspaces | **Yes** |
| Bluetooth | **Yes** |
| Everything else exercised | Reported as working |

The Meta+F12 result is the important one: it distinguishes this image from the earlier
build (`10074299…`) whose workspace switch does nothing.

## What is not established

Stated plainly, because the difference between "reported" and "measured" has mattered
repeatedly on this project:

- **No screenshots or captured output.** Every result above is user-reported. There is no
  frame, hash or log backing it, unlike the Laptop Studio records.
- **No before/after disk layout.** The claim that the internal disk was untouched was not
  captured with `lsblk`/`blkid`, so it is asserted rather than evidenced. The internal disk
  is in no erase approval and must be identified explicitly before any future write.
- **Individual devices were not itemised.** Wi-Fi, audio out, microphone, touchpad
  behaviour, battery reporting, thermals and display scaling were not separately recorded
  on the Envy; "everything worked" is the user's summary, not a per-item result.
- **The image on the stick was not re-verified.** The write was pre-validated against the
  hash above, but the stick was removed before it could be read back, so the exact bytes
  booted are inferred rather than confirmed.
- **The Envy's touchscreen was not reported on.** The known stock-kernel touch/pen gap is
  Surface-specific and says nothing about the Envy either way.

## Follow-up

- Repeat the boot with the per-item checklist in [testinstall.md](../../testinstall.md),
  capturing screenshots and the before/after `lsblk` output so the record is evidence.
- Confirm the stick's contents against the ISO hash on the next run.
- Nothing in this record authorises installing to the Envy. That needs the OS release
  gates and a fresh explicit go-ahead with the exact disk identified first.
