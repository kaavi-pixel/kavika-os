# Kavi'ka OS: handoff

Checkpoint updated 17 October 2026. This remains a diagnostic image, not an installation release. Do not flash/install or perform destructive disk actions without passing the gates below and a fresh explicit user go/no-go.

## Where we stopped

The latest ISO was built from the pinned Fedora KDE 44 base in WSL Ubuntu. SHA-256: `10074299b974eb005d0a38144d74b0dc02e1fa128684eb0f81b9cc9829a177ac`; `checkisomd5` passed. File: `C:\\Users\\kavsb\\Downloads\\Kavika-OS-0.1.0-Surface-Pro-8-Live-Preview.iso` (3,370,254,336 bytes).

A fresh disposable WHPX boot of the current ISO (SHA-256 `10074299b974eb005d0a38144d74b0dc02e1fa128684eb0f81b9cc9829a177ac`) produced a blank black display. QEMU serial and stderr logs were empty when inspected; no Fedora login or graphical session was confirmed. The earlier TCG attempt reached Fedora live-session login over serial but also displayed black. A QEMU process remains running from the WHPX test; close it before another VM test. No physical disk or host folder was attached; only disposable QCOW2 storage and user-mode NAT were configured. No Surface boot/install occurred.

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

- The ISO's embedded checksum passes. The earlier TCG attempt reached Fedora live-session login over serial; the later WHPX test showed a black display with empty logs. Current GUI state remains unverified.
- Previous candidate (different SHA-256: `bb581a008dbc7ef17843468f32bd1c1f33e64063c703d5c8ac0693f46a2d921a`) reached KDE/Test Centre and passed listed workspace, report CLI and SELinux checks. Not evidence for current image.
- Tests: Windows checkout 14 passed, 1 skipped for unavailable GRUB parser; Linux tree 14 passed including parser. `git diff --check` passed.
- Surface boot, native input, network, audio/camera, suspend/resume, Windows/Comet, file sharing, gestures, persistence, installation, update/recovery, release licensing and maintenance remain unverified or unimplemented.
- No project-wide open-source licence is selected. No ISO release is authorized.

## Resume plan

1. Do not start another VM while QEMU process PID 23428 is still present. Close it normally before further VM diagnostics.
2. The Downloads ISO, its sidecar, and manifest agree on SHA-256 `10074299b974eb005d0a38144d74b0dc02e1fa128684eb0f81b9cc9829a177ac` and size 3,370,254,336 bytes. All 18 manifest payload hashes match the present source payloads, including the logo, when CRLF-to-LF normalization is accounted for. However, manifest builder SHA-256 `d1578511e3bbfc0acdc70c1d50c3a577b74c614c585dd9025288b4b5d3046191` matches neither available builder snapshot. The exact Fedora base ISO was not found in searched build/download locations, so its local hash cannot be rechecked. The exact artifact provenance remains unresolved; do not claim this source tree produced that ISO or use it as a flash candidate.
3. Keep the canonical WSL tree and Windows checkout separate until their changes are reviewed and deliberately reconciled. The Windows builder has uncommitted edits and is not provenance for the current ISO.
4. Identify the original builder snapshot or explicitly record provenance as unknown. Then rebuild only from the verified canonical source and exact Fedora base into a new output path; verify base/output hashes, embedded integrity, and manifest. Boot that exact hash in a fresh disposable accelerated VM and inspect GUI, serial, and stderr. Do not transfer validation from another ISO hash.
5. Before any Surface test, pass current-image GUI, source/provenance, and non-destructive hardware boot gates. Never flash this diagnostic ISO: supported installer, full Windows 11/Comet workspace, recovery/update, and maintenance are still absent.

## Repository/publishing

Repository: [kaavi-pixel/kavika-os](https://github.com/kaavi-pixel/kavika-os), public. The prior request authorizes source/documentation updates there without changing visibility; no ISO release. Do not claim a push unless verified.
