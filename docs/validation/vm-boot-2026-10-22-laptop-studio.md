# Kavi'ka preview rebuilt with OS identity and Windows plumbing — boot verified

**Date:** 22 October 2026
**Build:** SHA-256 `f9e6e5693b682924ae4042c4203fd265a98ee98fecf28f1e815e13410612bc34`, 3,370,319,872 bytes, `checkisomd5` PASS ("It is OK to use this media.")
**Method:** disposable KVM guest on the Surface Laptop Studio (`tools/capture-vm-evidence.py boot --display none`), no physical disk, no shared folder.
**Supersedes for testing:** `bd8407d6…` (20 Oct) and `55d8d559…` / `1dfb0cda…` (intermediate 21–22 Oct builds; `1dfb0cda` lacked a last-minute START-HERE fix and was rebuilt).

## What changed in this image

- **OS identity:** `/usr/lib/os-release` now presents **Kavi'ka OS** (`NAME="Kavi'ka OS"`, `ID=kavika`, `ID_LIKE=fedora`, `PRETTY_NAME="Kavi'ka OS 0.1.0 (Live Preview, Fedora KDE 44)"`, `KAVIKA_VERSION="0.1.0"`). `VERSION_ID` deliberately stays `44` so anything reading `$releasever` keeps resolving. The base's `/etc/os-release` is a symlink to this file, so both names resolve.
- **Windows workspace plumbing ships in the image:** `usr/local/lib/kavika/launch-windows-vm-linux.py` (copied by the builder from `tools/`, source of truth unchanged, mode 0755) and the updated `kavika-windows-workspace`, which now explains that the live preview carries no virtualization stack and exits 6 if `qemu-system-x86_64` is missing.
- **In-image Windows guide:** `usr/share/kavika/WINDOWS.txt` — what works (guest installs self-contained, browser opens), what the image does not contain, and the provisioning path on an installed system, including the D16 (removable stick) and D23 (never reuse an ESP image) traps.
- **Test Centre wording:** the menu now reads "Kavi'ka live preview (HP Envy install target, Laptop Studio test machine). Windows is not included; the workspace plumbing ships. Internal installation is disabled." — replacing the stale "Pro 8 target" text — and the "Windows workspace status" entry states the current truth instead of claiming the browser is unimplemented.
- **START-HERE.txt** lists the identity and the WINDOWS.txt guide.

## Verification

Build level (payload extracted from the shipped ISO's `/boot/kavika-preview.cpio`):
- `usr/lib/os-release`, `usr/local/lib/kavika/launch-windows-vm-linux.py` (executable), `usr/share/kavika/WINDOWS.txt`, `kavika-windows-workspace`, `kavika-test-centre` all present; the START-HERE identity line is present.
- No CR byte in any payload text (the only binary flagged is `logo.png`, as expected).

Runtime (disposable KVM guest, `~/kavika-vm-f9e6`):
- The image **boots to the KDE Plasma desktop** with the Kavi'ka wallpaper and the Test Centre dialog — the os-release overlay did not break the live boot.
- The Test Centre **shows the new wording at runtime**, proving the new payload applied.
- Selecting "Windows workspace status" and pressing Enter opens the status dialog (frame comparison: 70.8% of pixels changed from the menu frame).
- The guest was stopped cleanly afterwards (`quit`).

## Limits

- `/etc/os-release` was verified at **payload level**, not by reading it back inside the guest: `capture-vm-evidence.py cmd` types into the QEMU monitor, not the guest console, so no in-guest `cat` was possible. The boot itself is the runtime evidence that the overlay applies cleanly.
- The three-finger swipe remains untested (no touchpad in a VM).
- This image still contains **no Windows, no virtualization stack and no bootable installer**
  (the installer *assets* ship, but the install entry is not wired); it is a diagnostic preview.

## Addendum — build `b5b650bc…` (same day)

A further build added the **installer assets** (the pre-flight `tools/kavika-install.py` and
the kickstart template `image/install/kavika.ks`, both shipped into the image via the
builder, plus `installer_assets_included: true` in the manifest — `installer_supported`
stays `false`). This is additive and does not change the live preview's behaviour.

- Build level: the payload carries `usr/local/sbin/kavika-install` (executable) and
  `usr/lib/kavika/installer/kavika.ks` (placeholder + virtualization stack intact),
  `checkisomd5` passes.
- Runtime: the image **boots to the KDE desktop** again (disposable KVM guest
  `~/kavika-vm-b5b6`; frame is 62% wallpaper gold, 28% white dialog/panel, ~0% black —
  the same desktop signature as `f9e6e569`), clean shutdown.

No installer was *run* — only its assets were shipped and the pre-flight's logic unit-tested
(68 tests pass). The boot entry and an actual Anaconda install remain the next rung
([installerinstallation.md](../../installerinstallation.md) §5–§6).
