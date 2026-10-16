# Kavi'ka OS 0.1.0: live-preview validation

Checkpoint: 16 October 2026. Work is paused at the user's request; the newest image is not approved for flashing and has not been published.

## Latest build, not yet boot-tested

| Field | Value |
|---|---|
| Filename | `Kavika-OS-0.1.0-Surface-Pro-8-Live-Preview.iso` |
| SHA-256 | `226d4fc0c57b18c43a725503664c59dcbb7e7767fa479be331760a91f5b5fc82` |
| Bytes | `3370254336`, about 3.37 GB / 3.14 GiB |
| Composition | Completed; GRUB parser passed, boot structures replayed, embedded media MD5 regenerated |
| Source tests | Nine unit/regression tests passed before this build |
| Manifest | [Payload and builder hashes](live-preview-0.1.0.manifest.json) |
| Latest change | Wallpaper startup now retries the actual `plasma-apply-wallpaperimage --fill-mode preserveAspectFit` operation |
| Fresh VM boot | Not run on this hash |
| Independent media check | Not rerun on this hash; do not carry forward an older candidate's PASS |
| Delivery | Retained as a build checkpoint; no ISO release, GitHub upload or user flash-ready handoff |

Read [handoff.md](../../handoff.md) before resuming. A successful build is not a boot, hardware or installation acceptance pass.

## Pinned input and tools

- **Upstream base:** `Fedora-KDE-Desktop-Live-44-1.7.x86_64.iso`.
- **Base SHA-256:** `c8295961d4c41adbf785a31a17c21a971d3b7415fda72dcad0c11c49577bf03a`.
- **Base verification:** ISO hash matched the signed checksum; signature verified against the downloaded Fedora keyring, Fedora 44 key fingerprint `36F612DCF27F7D1A48A835E4DBFCF71C6D9F90A6`.
- **Kernel:** unchanged upstream `6.19.10-300.fc44.x86_64`; not a linux-surface kernel.
- **Original logo SHA-256:** `f2cdcad70f8c289e5ac1628f9c2092647c6eae91e1cbbb813d6fe595a644fd6d`.
- **Builder:** Python 3.14.3, xorriso 1.5.6, GNU cpio 2.15, isomd5sum 1.2.3, GRUB parser 2.14.
- **VM:** QEMU 10.2.1, OVMF 2025.11, software emulation, two vCPUs, 4096 MiB RAM, no hard disk or physical disk passthrough.

Upstream downloads and verification instructions are provided by [Fedora KDE downloads](https://fedoraproject.org/kde/download). The sandbox lacks host `/dev/kvm`; VM timings are not measurements of Surface performance.

## Runtime evidence from the preceding candidate

These results apply to SHA-256 `bb581a008dbc7ef17843468f32bd1c1f33e64063c703d5c8ac0693f46a2d921a`, before the wallpaper retry change. They establish useful progress, not fresh-boot acceptance for the newest hash.

| Check | Result | Scope |
|---|---|---|
| Embedded media integrity | PASS | `checkisomd5` on this preceding candidate |
| UEFI → Linux → KDE | PASS | Disposable diskless VM reached the graphical desktop |
| Test Centre autostart | PASS | Menu appeared, accurately stating Windows absent / installation disabled |
| Two workspace defaults | PASS | KWin reported count 2 and retained Linux / Windows-not-installed configuration |
| Menu shortcut callback | PASS | `KavikaToggle` moved desktop 1 → 2 → 1 through the same D-Bus action used by Test Centre |
| Actual Meta+F12 input | PASS | QEMU key events moved to desktop 2 and back; current-desktop properties confirmed both states |
| Hardware report CLI | PASS | Generated valid JSON with actual VM model, CPU, memory, graphics and block-device fields |
| Report privacy scope | Unit-tested / inspected | Serial/UUID/partition fields excluded; no old Windows files queried |
| SELinux | Enforcing | Console `getenforce` returned Enforcing |
| Overlay labels | PASS for inspected paths | `/` root_t, `/etc` etc_t, `/usr` usr_t, binaries bin_t; live console login worked |
| System service failures | None at inspection | `systemctl --failed` listed zero loaded units |
| Fedora Welcome Centre | Not displayed in observed desktop | Test Centre used instead after preview launcher replacement |
| Logo at startup | FAIL / corrected in source, retest pending | Script queried a D-Bus method before it was ready |
| Wallpaper helper after startup | Command reported success | `preserveAspectFit` accepted; final visual logo and full revised startup still unconfirmed |
| GUI report/save and installer guard interaction | Not fully exercised | Do not infer GUI-flow passes from the CLI report or static guard |

The report's block-device list can include virtual devices such as `zram0`; it is not an installer target-selection list. Physical disk identification still requires model/capacity/connection review on the Surface.

## Corrections and limits

- **B01:** Fedora live KDE setup overwrote `kwinrc`; reapply project defaults through `livesys-session-extra`.
- **B02:** live-overlay ancestor directories had `tmpfs_t` labels. A pre-pivot attempt was ineffective; the post-policy-load tmpfiles-service drop-in corrected the inspected paths without disabling SELinux.
- **B03:** the unmodified upstream GRUB config reproduced a syntax error from nested function declarations. Normalize the video function to top level and parse the full generated config before composition.
- **B04:** the upstream Welcome Centre advertised installation. Replace its live-preview launcher and use Test Centre.
- **B05:** object existence did not establish wallpaper-method readiness. The latest script retries the actual wallpaper command; fresh-image verification is outstanding.
- **P01:** an internal build included Python bytecode. The builder excludes caches; the current manifest contains no `.pyc` or `__pycache__` entries.

The VM guest-agent runs under a confined SELinux domain, so some administrative diagnostic commands were denied there. Selected privileged checks were instead run through the disposable live VM's console; SELinux was not disabled and no user laptop or disk was accessed.

Surface boot/input/network/sleep, host Secure Boot, target resource feasibility, Windows/Comet, sharing, four-finger gestures, persistence and installation remain untested or unimplemented. No prototype or distribution milestone is closed by this record.
