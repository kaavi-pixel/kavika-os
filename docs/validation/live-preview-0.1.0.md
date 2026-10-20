# Kavi'ka OS 0.1.0: live-preview validation

Checkpoint: 17 October 2026. Paused development checkpoint; not a release and not approved for flashing. The exact local ISO hash and matching untracked sidecar/manifest are recorded below. Repository tracked sidecar/manifest remain a superseded build and must not be used for this ISO. No ISO is published.

| Gate | Result | Limitation |
|---|---|---|
| Pinned Fedora base | SHA-256 verified against Fedora's published signature/checksum | Base is Fedora KDE 44 x86_64 |
| Build | Completed in WSL Ubuntu; ISO composed from the unchanged Fedora base plus the project live overlay | Diagnostic live image only, no installer or Windows guest |
| Unit tests | 14 passed in WSL Linux source tree; Windows checkout also passed 14 with GRUB parser skipped (parser unavailable on Windows) | Source tests do not establish full OS behavior |
| Shell/GRUB preflight | Packaged shell scripts pass `bash -n`; generated GRUB config passes `grub-script-check` | Only in Linux builder environment |
| ISO media integrity | `checkisomd5` PASS | Integrity is not usability proof |
| Derived ISO SHA-256 | `10074299b974eb005d0a38144d74b0dc02e1fa128684eb0f81b9cc9829a177ac` | `C:\\Users\\kavsb\\Downloads\\Kavika-OS-0.1.0-Surface-Pro-8-Live-Preview.iso`; 3370254336 bytes |
| QEMU boot | Prior TCG attempt reached Fedora live-session login over serial; later WHPX attempt of the same ISO showed a black display with empty serial/stderr logs when inspected | No graphical desktop is verified. Tiny-guest WHPX probe is separate evidence, not ISO validation |

| VM safety boundary | Disposable QCOW2 disk, no physical disk passthrough, user-mode NAT, 4 GiB guest RAM; QEMU command configured for TCG | Linux diagnostic sandbox, not the planned KVM/libvirt Windows workspace. WHPX probe below is separate and does not test this ISO |
| Surface hardware | Not tested | Do not flash/install; no hardware matrix or installer validation |
| Product requirements | Not implemented in this ISO | No Windows 11 guest, Comet, integration, persistence, update/recovery or supported install |

Current local ISO (`Downloads/Kavika-OS-0.1.0-Surface-Pro-8-Live-Preview.iso`) SHA-256: `10074299b974eb005d0a38144d74b0dc02e1fa128684eb0f81b9cc9829a177ac`; output size: 3370254336 bytes; embedded `checkisomd5` passed. The tracked repository sidecar/manifest are an older build and must not be used for the local ISO.

## QEMU accelerator probe (separate artifact)

On the helper, QEMU 11.1 executed a tiny 64-MiB real-mode guest under WHPX, wrote the expected marker (byte 0x57), and exited through QEMU debug-exit (return code 33). This proves tiny-guest execution only—not Fedora/KDE graphics or this ISO. The earlier full Fedora attempt used TCG, reached serial login, and displayed a black GTK window.


## WHPX functional test of `10074299…` (19 October 2026)

Disposable QEMU/WHPX guest (4 GiB, 2 vCPU, UEFI, private 8-GiB QCOW2, user-mode NAT, no physical disk, no shared folder). The display was captured with the QEMU monitor `screendump` and keystrokes were sent with `sendkey`. Serial output was read from the guest's own `/dev/ttyS0`.

| Check | Result |
|---|---|
| Boot to desktop | PASS: GRUB entry "Kavika OS 0.1.0 - LIVE PREVIEW (no install)", serial login in about 40 s, KDE Plasma desktop on screen after about 3 min under this configuration |
| Branding | PASS: mustard background with logo wallpaper, "Kavi'ka Test Centre" desktop icon |
| Test Centre menu and guide | PASS: menu opens; guide text matches `START-HERE.txt` |
| Hardware report (GUI and CLI) | PASS: valid JSON; no disk serials, UUIDs, MACs or IPs collected (the only `serial`/`uuid` string match is the report's own disclaimer) |
| Installer guard | PASS on the console path: `liveinst` prints that installation is disabled and exits 1. The GUI dialog path was not exercised |
| SELinux and units | PASS: `Enforcing`; zero failed systemd units |
| Network | PASS: virtio NIC up with a NAT address |
| **Meta+F12 / Switch workspace** | **FAIL: only "Desktop 1" exists (`Number=1`). The preview's two workspaces were never created, so the toggle does nothing** |
| Windows/Comet, sharing, gestures, persistence, installer, Surface hardware | Not present or not tested |

Root cause of the workspace failure: the overlay files were packaged with CRLF line endings. In the booted image `livesys-session-extra` contains 7 CR characters, so its `mkdir` and `cp` commands created `/home/liveuser/.config/autostart\r` and `kwinrc\r` (literal CR in the names). The two-desktop `kwinrc` was therefore never applied. The same CRs are in the config and desktop-entry files (the image also reports `kavika-live.desktop` as executable and world-writable). The earlier builder normalized only five shell scripts.

Fix, not yet in a rebuilt ISO: `tools/build-live-preview.py` now normalizes every text file in the overlay, leaves binary files untouched, and `.gitattributes` forces LF for the payload. Tests cover both. A rebuild creates a new ISO hash, so none of the results above transfer to it.

The GTK window of the launcher stayed black in the capture tool even though the monitor screendump shows a rendered desktop for the same ISO. Whether the GTK window itself displays correctly is not established; the capture method may be at fault.

## Rebuild with fixes (19 October 2026), not yet booted

Built in WSL Ubuntu from the pinned Fedora KDE 44 base (SHA-256 verified, `c8295961…`) after the CRLF fix and the two-machine hardware report.

| Item | Value |
|---|---|
| File | `Kavika-OS-0.1.1-Surface-Live-Preview-20261019-065635.iso` (the file name says 0.1.1; the strings inside the image and manifest still say 0.1.0) |
| SHA-256 | `57a851a70b1f6fdb17c0b1c1801bad52e4237c0888aaa88c5c15a5a2c2cfefd9` |
| Size | 3,370,319,872 bytes |
| Builder SHA-256 (recorded in manifest) | `b91410112fd58f8ee539c2a1bb7ee2576cdd663280e19b96ae19f04d27fa25e0`; matches the builder used in the Linux build copy |
| Fedora base | `c8295961d4c41adbf785a31a17c21a971d3b7415fda72dcad0c11c49577bf03a` (re-downloaded and checked this session) |
| Embedded media check | `checkisomd5`: PASS |
| Sidecar check | `sha256sum -c`: OK |
| Tests (Linux, with the GRUB parser) | 30 passed, 0 skipped |
| Shell syntax | `bash -n` passes for the three packaged scripts and the new preflight script |
| Line endings | The build copy is normalized to LF before the tests run; no CR remained afterwards. The builder also normalizes the packaged overlay. This is a source check, not a check of the booted image |

This ISO is not yet booted. At the time of the build the helper had only about 3.7 GiB of free RAM, under the 5 GiB guard for a 4 GiB guest, so the boot test was deferred rather than forced. **None of the results for `10074299…` transfer to this hash.** Its provenance is known: base hash, builder hash and payload hashes are all recorded and the builder is the committed one.

What changed in the image: every overlay text file now has LF endings (the fix for the workspace-switch defect), the hardware report covers both Surface machines, and the guide and Test Centre text name both machines.

## Next actions

1. Boot the rebuilt ISO (`57a851a7…`) in a disposable VM and repeat the functional test above. Meta+F12 must switch between two workspaces before the image advances. Prefer the Surface Laptop Studio with KVM (`tools/launch-preview-vm-linux.py`); the Windows helper needs at least 5 GiB free RAM. **Partially done on a different build:** the independently rebuilt `bd8407d6…` was booted in a KVM guest on the Laptop Studio and passed the workspace-switch, SELinux, failed-unit and isolation checks ([boot record](vm-boot-2026-10-20-laptop-studio.md)). `57a851a7…` itself remains unbooted; do not transfer those results to it.
2. Reconcile WSL and Windows worktrees and use one canonical source commit. Run tests and shell/GRUB checks on the exact tree used to rebuild.
3. Boot the rebuilt exact ISO in QEMU until KDE, logo/wallpaper, Test Centre/report privacy, workspace switching and installer guard are visually verified. Record its SHA-256 with results.
4. Boot the verified image from external media on the Surface for non-destructive compatibility tests only. Identify CPU/RAM/storage and verify graphics, input, Wi-Fi, audio, camera, sleep/resume and Secure Boot state. No disk writes, firmware/security changes, or installation without a fresh explicit user go/no-go.
5. Feasibility-test the planned full Windows 11 VM, including Comet and user-chosen apps, licensing, performance/resource budget, host acceleration limits, gestures/shortcut, sharing security, networking, sleep, updates and rollback. Report compatibility gaps honestly; do not narrow the Windows app requirement silently.
6. Only after preview, hardware and architecture gates pass, build a supported installer, recovery/update/signing and maintenance process, licensing/provenance/redistribution policy, and CI/reproducible release. Test installation on disposable virtual storage before any separately authorised Surface install.

## Previous-candidate evidence (different hash)

The earlier candidate SHA-256 `bb581a008dbc7ef17843468f32bd1c1f33e64063c703d5c8ac0693f46a2d921a` reached the KDE desktop and Test Centre, had two Linux workspaces with shortcut toggle, CLI hardware report, enforcing SELinux and no failed system units at inspection. It does not validate the newer wallpaper change or the current ISO.

## Known corrections and limits

- B01: reapply project KWin workspace defaults after Fedora live setup.
- B02: relabel live overlay directories after SELinux policy loads; do not disable SELinux.
- B03: normalize nested upstream GRUB video functions and parser-check generated config.
- B04: replace upstream Welcome Centre's install-oriented entry in the preview.
- B05: wallpaper startup now retries the real Plasma command; latest graphical verification remains outstanding.
- P01: exclude Python bytecode/cache from the image manifest.

The hardware report omits serials, UUIDs and partitions. A VM device list is not an installer disk-selection list. Surface boot/input/network/sleep, Windows/Comet, sharing, gestures, persistence, and installation remain untested or unimplemented.

The VM guest-agent runs under a confined SELinux domain, so some administrative diagnostic commands were denied there. Selected privileged checks were instead run through the disposable live VM's console; SELinux was not disabled and no user laptop or disk was accessed.

Surface boot/input/network/sleep, host Secure Boot, target resource feasibility, Windows/Comet, sharing, four-finger gestures, persistence and installation remain untested or unimplemented. No prototype or distribution milestone is closed by this record.
