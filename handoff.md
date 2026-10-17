# Kavi'ka OS: handoff

Checkpoint updated 17 October 2026. This remains a diagnostic image, not an installation release. Do not flash/install or perform destructive disk actions without passing the gates below and a fresh explicit user go/no-go.

## Where we stopped

The latest ISO was built from the pinned Fedora KDE 44 base in WSL Ubuntu. SHA-256: `10074299b974eb005d0a38144d74b0dc02e1fa128684eb0f81b9cc9829a177ac`; `checkisomd5` passed. File: `C:\\Users\\kavsb\\Downloads\\Kavika-OS-0.1.0-Surface-Pro-8-Live-Preview.iso` (3,370,254,336 bytes).

A fresh QEMU attempt booted through UEFI/GRUB and reached Fedora 44 live-session login on serial console. The GTK window remained black, so KDE, Test Centre, wallpaper, GUI report/privacy flow, workspace switching and installer guard are unverified for this hash. The software TCG boot was extremely slow and consumed host CPU; the QEMU process was stopped. No physical disk passthrough or shared folders were configured; the guest had only a disposable QCOW2 disk and user-mode NAT. No Surface boot/install occurred.

B05's wallpaper readiness retry is not visually validated on this image. KDE/Test Centre passes belong to a previous ISO candidate and must not transfer to the current hash.

## Current host/test constraint

- QEMU TCG made the full Fedora guest extremely slow and was stopped; do not rerun that full boot routinely.
- **WHPX capability probe:** a separate 64-MiB real-mode boot sector under `accel=whpx` wrote its expected marker and exited through QEMU's debug-exit device (return code 33). This proves WHPX can execute a tiny guest on this helper; it does not validate Fedora, KDE, graphics, or Surface hardware.
- **Next VM test:** the launcher now accepts `--accel whpx` and saves diagnostics to `qemu.stderr.log`, while preserving the ISO hash check, disposable QCOW2/UEFI vars, and no physical disk/shared-folder exposure. Launch the current ISO once with WHPX using a fresh empty VM directory. Inspect graphics, serial output and stderr. If graphics stays black or boot stalls, stop and diagnose from logs or move to Linux/KVM; do not fall back to full TCG on this helper.
- Recheck free RAM before starting a 4-GiB guest; the launch guard is 5 GiB free RAM.

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
| `tests/test_live_preview.py` | 14 passing tests in Windows checkout; one GRUB-parser test skipped there; all 14 pass in Linux |
| `tools/launch-preview-vm-windows.py` | ISO-pinned isolated QEMU launcher with disposable QCOW2 |

The ISO contains no Windows guest, Comet, cross-OS file sharing, persistence, supported installer, or update/recovery path. “Windows (not installed)” is a Linux workspace.

## Evidence and limits

- Current hash media checksum passes; serial boot reaches Fedora live-session login; graphical KDE session is not verified.
- Previous candidate (different SHA-256: `bb581a008dbc7ef17843468f32bd1c1f33e64063c703d5c8ac0693f46a2d921a`) reached KDE/Test Centre and passed listed workspace, report CLI and SELinux checks. Not evidence for current image.
- Tests: Windows checkout 14 passed, 1 skipped for unavailable GRUB parser; Linux tree 14 passed including parser. `git diff --check` passed.
- Surface boot, native input, network, audio/camera, suspend/resume, Windows/Comet, file sharing, gestures, persistence, installation, update/recovery, release licensing and maintenance remain unverified or unimplemented.
- No project-wide open-source licence is selected. No ISO release is authorized.

## Resume plan

1. Read [the OS implementation plan](os-implementation-plan.md), [validation record](docs/validation/live-preview-0.1.0.md), [Surface target](docs/surface-test-target.md), and [bug tracker](bugtracker.md).
2. Reconcile WSL and Windows source trees into one canonical state. Run tests, shell syntax checks and GRUB parsing on exactly that tree. Record source revision and base/output hashes.
3. Test WHPX using a tiny guest that demonstrably executes. If unavailable, use Linux/KVM-capable hardware; do not relaunch slow TCG routinely.
4. Rebuild if source changes, verify ISO checksum/hash, then boot that exact hash in an accelerated disposable VM. Visually verify KDE, logo/wallpaper, Test Centre/report privacy, workspace switching, installer guard; save sanitized evidence.
5. Only then test the Surface from external live media non-destructively: measure CPU/RAM/SSD and test graphics, input, Wi-Fi, audio, camera, sleep/resume, battery and Secure Boot. No disk writes, partitioning, installation or firmware/security changes without a fresh explicit go/no-go.
6. Feasibility-test full Windows 11, including Comet/user-chosen apps, licensing, performance/resources, acceleration, switching, least-privilege sharing, networking, suspend/resume and rollback. Do not reduce the compatibility requirement silently.
7. After all preview/hardware/architecture gates pass, implement supported installer, recovery/update/signing, maintenance, CI and licensing/provenance/redistribution policy. Test on disposable virtual storage before any separately authorized Surface install.
8. Record every gate against exact source revision and ISO hash. A bootable diagnostic image is a prototype, not a maintained installable OS.

## Repository/publishing

Repository: [kaavi-pixel/kavika-os](https://github.com/kaavi-pixel/kavika-os), public. The prior request authorizes source/documentation updates there without changing visibility; no ISO release. Do not claim a push unless verified.
