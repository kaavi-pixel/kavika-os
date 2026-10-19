# Kavi'ka OS: handoff

Checkpoint updated 19 October 2026. This remains a diagnostic image, not an installation release. Do not flash/install or perform destructive disk actions without passing the gates below and a fresh explicit user go/no-go.

## Where we stopped

The latest ISO was built from the pinned Fedora KDE 44 base in WSL Ubuntu. SHA-256: `10074299b974eb005d0a38144d74b0dc02e1fa128684eb0f81b9cc9829a177ac`; `checkisomd5` passed. File: `C:\\Users\\kavsb\\Downloads\\Kavika-OS-0.1.0-Surface-Pro-8-Live-Preview.iso` (3,370,254,336 bytes).

On 19 October 2026 a disposable WHPX guest booted the earlier ISO (`10074299…`) to a working KDE desktop with the Test Centre, valid hardware report, enforcing SELinux and no failed units. **Meta+F12 workspace switching failed** because overlay files had CRLF line endings. That is fixed in source and in a rebuilt ISO (`57a851a70b1f6fdb17c0b1c1801bad52e4237c0888aaa88c5c15a5a2c2cfefd9`, 3,370,319,872 bytes, builder `b9141011…`), whose checksum, embedded media check and 30 Linux tests pass. **The rebuilt ISO has not been booted yet.** No physical disk, shared folder or Surface was used.

The project now has two Surface machines. The **Surface Pro 8** is the final install target and has never been booted with Kavi'ka. The **Surface Laptop Studio** (Core i5-11300H, 16 GiB, Iris Xe) already runs Fedora 44 and has KVM-capable hardware, so it is the first test machine; see `docs/surface-laptop-studio-test-machine.md`. Its results are evidence only, not proof for the Pro 8.

B05's wallpaper readiness retry is not visually validated on this image. KDE/Test Centre passes belong to a previous ISO candidate and must not transfer to the current hash.

## Current host/test constraint

- Latest WHPX ISO test: same pinned ISO hash; blank black display and empty serial/stderr logs at inspection. A QEMU process remains present; close it before another VM test.
- A separate 64-MiB real-mode guest under `accel=whpx` wrote its expected marker and exited with debug-exit 33. This proves tiny-guest execution only, not Fedora/KDE or Surface hardware.
- The launcher accepts `--accel whpx` and writes `qemu.stderr.log`. Keep guest storage disposable, without physical disks or host shared folders, use user-mode networking, and recheck RAM before another guest.

## Product requirements

- Fedora KDE/Linux plus full general-purpose Windows 11, switchable like workspaces, with a four-finger gesture or host-owned shortcut and straightforward file sharing.
- Windows must include Comet and normal user-selected applications; do not silently replace it with Wine, a stripped guest, or an app allowlist. Report architecture incompatibilities honestly.
- Candidate architecture: Fedora KDE/Wayland host and Windows 11 guest using QEMU/KVM/libvirt plus a viewer such as SPICE/virt-viewer. Feasibility is not established.
- Surface Pro 8 Wi-Fi, printed model 1983. Exact CPU/RAM/installed SSD and hardware support are unmeasured. Preserve the supplied logo unchanged.
- Eventual Surface replacement and erasure of the empty 512-GB external media SSD were approved, but no disk was written. Identify physical disks and obtain a fresh explicit confirmation immediately before any destructive action. HP internal storage, firmware-security changes and licence purchases remain excluded unless separately authorized.

## Implemented source

| `tools/build-live-preview.py` | Pinned Fedora input, GRUB normalization/parser check, cpio live overlay, image composition, checksum/manifest |
| `image/live-preview/root/` | Test Centre, filtered hardware report, live-session setup, logo, two Linux workspace demo |
| `image/live-preview/root/usr/lib/systemd/system/systemd-tmpfiles-setup.service.d/20-kavika-labels.conf` | SELinux label correction without disabling SELinux |
| `image/live-preview/root/var/lib/livesys/livesys-session-extra` | Reapplies workspace defaults after Fedora live KDE setup |
| `image/live-preview/root/usr/bin/liveinst` | Preview installer guard; not a supported installer |
| `tests/test_live_preview.py` | Windows test suite currently reports 15 passed, 1 skipped (GRUB parser unavailable) |
| `tools/launch-preview-vm-windows.py` | ISO-pinned isolated QEMU launcher with disposable QCOW2 |

The ISO contains no Windows guest, Comet, cross-OS file sharing, persistence, supported installer, or update/recovery path. “Windows (not installed)” is a Linux workspace.

## Evidence and limits

- The earlier ISO reached the KDE desktop and the Test Centre worked, but Meta+F12 workspace switching failed (CRLF defect). The rebuilt ISO has the fix and passes its checksum and media checks, but has not been booted. No Surface has been tested.
- Previous candidate (different SHA-256: `bb581a008dbc7ef17843468f32bd1c1f33e64063c703d5c8ac0693f46a2d921a`) reached KDE/Test Centre and passed listed workspace, report CLI and SELinux checks. Not evidence for current image.
- Tests: Windows checkout 14 passed, 1 skipped for unavailable GRUB parser; Linux tree 14 passed including parser. `git diff --check` passed.
- Surface boot, native input, network, audio/camera, suspend/resume, Windows/Comet, file sharing, gestures, persistence, installation, update/recovery, release licensing and maintenance remain unverified or unimplemented.
- No project-wide open-source licence is selected. No ISO release is authorized.

## Resume plan

1. **On the Surface Laptop Studio:** clone the repo, run `bash tools/surface-fedora-preflight.sh` (read-only; installs and changes nothing) and review its output. It reports KVM, tools, Secure Boot, TPM, RAM, disk and the hardware JSON.
2. Copy the rebuilt ISO and its `.sha256` file to that machine. Boot it in a disposable KVM guest with `python3 tools/launch-preview-vm-linux.py --iso <iso> --sha256-file <sidecar> --vm-dir <new dir>`. The launcher refuses a hash mismatch and attaches no physical disk or shared folder. Repeat the functional test in `docs/validation/live-preview-0.1.0.md`. **Meta+F12 must now switch workspaces.**
3. If the Windows helper is used instead, it needs at least 5 GiB free RAM (it had 3.7 GiB when last checked). The QEMU GTK window showed black in earlier captures, while screenshots taken with the QEMU monitor `screendump` command showed the desktop, so use `screendump` to see the screen.
4. Only after the VM test passes, boot the same ISO from external media on the Laptop Studio, still without installing, then on the Pro 8. Test graphics, input, Wi-Fi, audio, camera, sleep and Secure Boot. No disk writes, partitioning, installation or firmware/security changes without a fresh explicit go/no-go.
5. Then feasibility-test full Windows 11 plus Comet in a KVM guest on the Laptop Studio (16 GiB host RAM), and record what does and does not transfer to the Pro 8.
6. Still absent: Windows 11 and Comet, file sharing, gestures, a Surface-specific kernel, a supported installer, recovery and update. This is a diagnostic image and must not be flashed as the product.

## Repository/publishing

Repository: [kaavi-pixel/kavika-os](https://github.com/kaavi-pixel/kavika-os), public. The prior request authorizes source/documentation updates there without changing visibility; no ISO release. Do not claim a push unless verified.
