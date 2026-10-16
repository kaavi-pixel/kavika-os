# Kavi'ka OS: handoff

Paused at the user's request on 16 October 2026. This is a source/build checkpoint, not a released installation image; do not resume testing, publish an ISO or change either laptop until the user asks to continue.

## Where we stopped

The Fedora-based diagnostic preview is implemented. A disposable UEFI VM reached KDE and Kavi'ka Test Centre, generated a hardware report, and switched between two Linux desktops both through the menu's shortcut action and Meta+F12. SELinux remained enforcing after correcting the live overlay's directory labels.

The last change replaces a racy wallpaper readiness check with bounded retries of Plasma's actual wallpaper command. That command reported success in the running VM, but the complete revised startup script has not yet passed a fresh-image boot and visual check. The newest ISO must not inherit the previous candidate's runtime pass.

The current build finished successfully before stopping. Its final filename/hash and precise validation boundary are recorded in [the validation record](docs/validation/live-preview-0.1.0.md); no ISO has been handed over as ready to flash, and no VM test remains running.

## Fixed product requirements

- **Experience:** Linux and full general-purpose Windows, kept running and switched like desktops, with four-finger input or a host-owned shortcut and simple file transfer.
- **Windows:** normal Windows features and user-chosen apps, explicitly including Comet. No stripped Windows, app allowlist or Wine substitute; universal VM compatibility is not promised.
- **Architecture:** Fedora KDE/Wayland host, QEMU/KVM and libvirt guest, initially SPICE/virt-viewer. This remains a feasibility candidate, not validated full-Windows functionality.
- **Logo:** preserve `assets/branding/kavi-ka-os-logo.png` unchanged. The earlier full desktop theme specification remains a draft, not an approved implemented theme.

## Actual target and permissions

- **Surface:** printed model 1983 identifies Surface Pro 8 Wi-Fi; the sourced hardware record is [here](docs/surface-test-target.md).
- **Capacity:** the user's factory marking says 128 GB, superseding the earlier approximately 1 TB assumption. Actual installed SSD capacity/model, exact CPU and RAM are still unmeasured.
- **Input:** external USB keyboard/mouse and connection hardware are available. The preview uses Fedora's stock kernel; native Surface Type Cover/touch/pen and gestures remain unvalidated.
- **Sign-in:** Windows sign-in is unavailable, but it is not required for the proposed live-test route. Do not inspect old Windows files or attempt account recovery.
- **Authorised erase scope:** eventual replacement of the spare Surface's Windows and erasure of the empty 512 GB external SSD for media. Keep that approval; still match physical disks before any write.
- **Excluded:** HP Envy internal storage, other drives, firmware-security changes, Windows purchases and unapproved guest provisioning. The HP is only the helper.
- **Privacy:** do not retain or publish the device serial, old Windows files, recovery/activation keys or raw private device logs.

No user disk has been written. Keep the Surface's SSD installed: preparing USB media does not impose a 512 GB limit on a later internal installation.

## Implemented source

| Path | What exists |
|---|---|
| `tools/build-live-preview.py` | Pinned-input image builder, GRUB normalization/parser check, cpio live overlay, boot replay, checksum and manifest |
| `image/live-preview/root/` | Test Centre, filtered hardware report, live-session setup, original-logo integration and two-desktop KWin shortcut |
| `image/live-preview/root/usr/lib/systemd/system/systemd-tmpfiles-setup.service.d/20-kavika-labels.conf` | Post-policy-load ancestor/payload relabelling, without disabling SELinux |
| `image/live-preview/root/var/lib/livesys/livesys-session-extra` | Reapplies workspace defaults after Fedora's live KDE setup |
| `image/live-preview/root/usr/bin/liveinst` | Preview installer guard; underlying upstream installer packages are not removed |
| `tests/test_live_preview.py` | Nine passing unit/regression tests at this checkpoint |
| `docs/build.md` | Builder prerequisites, exact command and composition limits |
| `docs/live-preview.md` | Draft user test guide, gated on final image validation |

The live preview has no Windows guest, Comet, cross-OS shared folder, VM controller, persistence or supported internal installation. Its “Windows (not installed)” desktop is another Linux desktop, not Windows.

## Evidence and defects

- **Passed on the previous candidate:** UEFI boot into KDE/Test Centre, two named desktops, shortcut callback both directions, Meta+F12 out and back, CLI hardware-report generation, enforcing SELinux, expected root/etc/usr/bin labels and zero failed system units at inspection.
- **Build checks:** nine unit tests passed; generated GRUB syntax is checked during composition. Input signature/checksum and output media checks are documented with the matching candidate, not assumed across rebuilds.
- **Corrected defects:** B01 upstream workspace-default replacement; B02 wrong overlay directory labels; B03 upstream nested GRUB function syntax; B04 installer-oriented Welcome Centre. B05 is the latest wallpaper startup race and still needs clean-boot verification.
- **Not proved:** final image startup/visual branding, GUI report/save flow, Surface boot/input/network/sleep, host Secure Boot, actual target resource feasibility, installation, full Windows/Comet, sharing and gestures.

See [the bug tracker](bugtracker.md) and [exact candidate evidence](docs/validation/live-preview-0.1.0.md). No M0–M5 or OS3–OS6 milestone is closed by this checkpoint.

## Resume here, only when asked

1. Read this handoff and the latest validation record. Re-run source tests; rebuild only if needed and preserve the input/output hash distinction.
2. Boot the newest ISO in a fresh, diskless UEFI VM. Leave SELinux enforcing and use disposable firmware variables; do not expose physical disks.
3. Verify the updated wallpaper retry, original logo's aspect ratio, automatic Test Centre, GUI hardware report/save handling, both shortcut paths and installer guard. Check guest logs and failed units; do not substitute an older screenshot for the new candidate.
4. Record the exact tested hash and remaining limitations. Only after that checkpoint, share the ISO, checksum and matching guide for the Surface live test.
5. Collect the Surface's actual CPU/RAM/internal disk/KVM report before allocating Windows resources. Do not reuse the HP's 6 GiB RAM / 128 GiB guest-disk proposal on a machine marked 128 GB.
6. Validate native Surface input/kernel/security needs, Windows licensing and full-Windows/Comet feasibility. Implement a disposable-disk-tested installer before carrying out the already-authorised internal replacement.

## Repository and publication scope

The existing repository is [kaavi-pixel/kavika-os](https://github.com/kaavi-pixel/kavika-os), currently public. After that visibility was reported, the user explicitly requested this checkpoint and a GitHub update; publish the source/docs checkpoint to that existing repository without changing visibility.

This does not authorise a public ISO release, Windows payload distribution, licence purchases or firmware changes. No project-wide open-source licence has been selected; third-party licences and release/trademark decisions remain separate.
