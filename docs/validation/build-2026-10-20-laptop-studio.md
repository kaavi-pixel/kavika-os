# Kavi'ka: local rebuild on the Surface Laptop Studio, 20 October 2026

An independent build of the diagnostic live preview, produced on the Fedora test machine instead of WSL. It records a build and its static checks only. **This ISO has not been booted**, so it passes no desktop, workspace-switch or Surface gate.

## Result

| Item | Value |
|---|---|
| Output | `build/Kavika-OS-0.1.0-Surface-Pro-8-Live-Preview.iso` |
| SHA-256 | `bd8407d6393a12f8a5829ef15a86371b854f08834d9fd7df4a85ddbdc8820e0d` |
| Size | 3,370,319,872 bytes |
| Build time (UTC) | 2026-10-20T01:48:59Z |
| Embedded media check | `checkisomd5` **PASS** ("It is OK to use this media") |
| Manifest | `build/Kavika-OS-0.1.0-Surface-Pro-8-Live-Preview.manifest.json`, 18 payload files |
| Sidecar | `build/Kavika-OS-0.1.0-Surface-Pro-8-Live-Preview.iso.sha256` matches the recomputed hash |

## Inputs, verified not assumed

| Input | Value |
|---|---|
| Base ISO | `Fedora-KDE-Desktop-Live-44-1.7.x86_64.iso` |
| Base SHA-256 | `c8295961d4c41adbf785a31a17c21a971d3b7415fda72dcad0c11c49577bf03a` — matches the pin in `tools/build-live-preview.py` and the PGP-signed `Fedora-KDE-44-1.7-x86_64-CHECKSUM` |
| Base size | 3,368,683,520 bytes |
| Builder SHA-256 | `b91410112fd58f8ee539c2a1bb7ee2576cdd663280e19b96ae19f04d27fa25e0` — the same builder (prefix `b9141011…`) recorded for the WSL-built candidate |

The earlier `Fedora-Workstation-Live-44-1.7.x86_64.iso` in the same directory is the **GNOME Workstation** spin (`1620295f…`). It is not a substitute: the builder rejects the hash, and `grub_preview()` requires the `Fedora-KDE-Live-44` CD label that only the KDE image carries.

## Toolchain

| Component | Version |
|---|---|
| Host | Surface Laptop Studio, Fedora 44 Workstation, kernel `6.19.10-300.fc44.x86_64` |
| Python | 3.14.8 (system) |
| pycdlib | 1.22.0 (isolated venv; the Fedora 44 package is 1.15.0) |
| xorriso | 1.5.8.pl02 |
| GNU cpio | 2.15 |
| grub-script-check | GRUB 2.12 (`grub2-tools-2.12-56.fc44`) |
| isomd5sum | 1.2.5-6.fc44 |

Two environment notes, both resolved without root:

- **`grub2-tools` is installed but ships `grub2-script-check`**, while the builder requires the name `grub-script-check`. A user-local symlink supplied the expected name; no package was installed.
- **`xorriso` is not installed on this host.** The Fedora RPMs for `xorriso`, `libisoburn`, `libisofs` and `libburn` were extracted into `~/.local/xorriso-root` and invoked through a wrapper that sets `LD_LIBRARY_PATH`. Nothing was written outside the home directory and no system package changed.

## Static checks performed

| Check | Result |
|---|---|
| Repo test suite | `Ran 30 tests, OK (skipped=1)` before the build |
| `bash -n` / GRUB syntax stage | Passed inside the builder (it aborts otherwise) |
| `checkisomd5` | PASS |
| Sidecar vs recomputed SHA-256 | Match |
| Overlay line endings (B06 root cause) | **No text file in the `/boot/kavika-preview.cpio` overlay contains a CR byte** |
| Negative control | The same extraction from the earlier ISO (`10074299…`) contains `\r\n` in `etc/skel/.config/kwinrc`, so the detector is sensitive to the defect |

The overlay's `etc/skel/.config/kwinrc` in this build contains:

```
[Desktops]
Number=2
Rows=1
...
Name_1=Linux
Name_2=Windows (not installed)
```

with LF endings only. That is the input the Meta+F12 switch depends on; whether the switch actually works is a runtime question this build has not answered.

## Not byte-identical to the WSL build

This output is 3,370,319,872 bytes — the **same size** as the WSL-built `57a851a7…` candidate — but hashes differently (`bd8407d6…`). Same builder source, same payload, different toolchain and timestamps; ISO 9660 metadata is not reproducible across environments. **Do not treat either hash as the canonical image**: reproducibility remains unproven, as `docs/build.md` already warns.

## What this does not establish

- No boot, no KDE desktop, no Test Centre run, no Meta+F12 switch, no SELinux or network check at runtime.
- No Surface hardware, Secure Boot, native input, audio, camera or suspend evidence.
- Not an installation release and not approved for flashing.
- Windows and Comet are not included.
