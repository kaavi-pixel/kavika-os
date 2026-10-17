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
| QEMU boot | UEFI/GRUB boot and serial logs reached Fedora 44 live-session login in the prior **TCG** attempt. A later WHPX launch of this same ISO stayed black; its serial/stderr logs were empty when inspected, and no visible desktop was confirmed | KDE/Test Centre and project GUI functions remain unverified on this hash. WHPX tiny-guest capability probe is separate evidence, not ISO validation |

| VM safety boundary | Disposable QCOW2 disk, no physical disk passthrough, user-mode NAT, 4 GiB guest RAM; QEMU command configured for TCG | Linux diagnostic sandbox, not the planned KVM/libvirt Windows workspace. WHPX probe below is separate and does not test this ISO |
| Surface hardware | Not tested | Do not flash/install; no hardware matrix or installer validation |
| Product requirements | Not implemented in this ISO | No Windows 11 guest, Comet, integration, persistence, update/recovery or supported install |

Current local ISO (`Downloads/Kavika-OS-0.1.0-Surface-Pro-8-Live-Preview.iso`) SHA-256: `10074299b974eb005d0a38144d74b0dc02e1fa128684eb0f81b9cc9829a177ac`; output size: 3370254336 bytes; embedded `checkisomd5` passed. The tracked repository sidecar/manifest are an older build and must not be used for the local ISO.

## QEMU accelerator probe (separate artifact)

On the helper, QEMU 11.1 executed a tiny 64-MiB real-mode guest under WHPX, wrote the expected marker (byte 0x57), and exited through QEMU debug-exit (return code 33). This proves tiny-guest execution only—not Fedora/KDE graphics or this ISO. The earlier full Fedora attempt used TCG, reached serial login, and displayed a black GTK window.


## Next actions

1. Diagnose the blank QEMU graphics output from serial logs and exact guest/host configuration; do not presume the cause. A QEMU process or login prompt is not a graphical boot pass.
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
