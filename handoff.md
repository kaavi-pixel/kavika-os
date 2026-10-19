# Kavi'ka OS: handoff

Checkpoint updated 17 October 2026. This remains a diagnostic image, not an installation release. Do not flash/install or perform destructive disk actions without passing the gates below and a fresh explicit user go/no-go.

## Where we stopped

The latest ISO was built from the pinned Fedora KDE 44 base in WSL Ubuntu. SHA-256: `10074299b974eb005d0a38144d74b0dc02e1fa128684eb0f81b9cc9829a177ac`; `checkisomd5` passed. File: `C:\\Users\\kavsb\\Downloads\\Kavika-OS-0.1.0-Surface-Pro-8-Live-Preview.iso` (3,370,254,336 bytes).

On 19 October 2026 a disposable WHPX guest booted the current ISO (`10074299…`) to a working KDE desktop with the Test Centre, valid hardware report, enforcing SELinux and no failed units. **Meta+F12 workspace switching fails**: the image has one desktop because CRLF line endings in the overlay broke the livesys setup script. The fix is in the builder (all overlay text files normalized, `.gitattributes` added) but no new ISO has been built, so the fix is unvalidated. No physical disk, shared folder or Surface was used.

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

- The ISO's embedded checksum passes. A WHPX guest reaches the KDE desktop and the Test Centre works; Meta+F12 workspace switching fails (CRLF defect, fix not yet rebuilt). Surface hardware is untested.
- Previous candidate (different SHA-256: `bb581a008dbc7ef17843468f32bd1c1f33e64063c703d5c8ac0693f46a2d921a`) reached KDE/Test Centre and passed listed workspace, report CLI and SELinux checks. Not evidence for current image.
- Tests: Windows checkout 14 passed, 1 skipped for unavailable GRUB parser; Linux tree 14 passed including parser. `git diff --check` passed.
- Surface boot, native input, network, audio/camera, suspend/resume, Windows/Comet, file sharing, gestures, persistence, installation, update/recovery, release licensing and maintenance remain unverified or unimplemented.
- No project-wide open-source licence is selected. No ISO release is authorized.

## Resume plan

1. Obtain the pinned Fedora KDE 44 base ISO (the previous copy was not found locally; it must hash to `c8295961d4c41adbf785a31a17c21a971d3b7415fda72dcad0c11c49577bf03a`). Rebuild into a new output path from the verified canonical source in WSL, then run the checksum and manifest checks.
2. Boot the new hash in a disposable WHPX guest and repeat the functional test in `docs/validation/live-preview-0.1.0.md`. The workspace toggle (Meta+F12) must work. Capture with the QEMU monitor `screendump`.
3. The current ISO's recorded builder hash `d1578511e3bbfc0acdc70c1d50c3a577b74c614c585dd9025288b4b5d3046191` matches no available builder, so its provenance stays unresolved. Do not use it as a flash candidate.
4. Only after the rebuilt image passes, run non-destructive Surface live-media tests (graphics, input, Wi-Fi, audio, camera, sleep, Secure Boot). No disk writes, partitioning, firmware changes or installation without a fresh explicit go/no-go.
5. Still absent: full Windows 11 plus Comet, file sharing, gestures, supported installer, recovery and update. This is a diagnostic image and must not be flashed as the product.

## Repository/publishing

Repository: [kaavi-pixel/kavika-os](https://github.com/kaavi-pixel/kavika-os), public. The prior request authorizes source/documentation updates there without changing visibility; no ISO release. Do not claim a push unless verified.
