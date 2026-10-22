# Kavi'ka OS: handoff

Checkpoint updated 20 October 2026. This remains a diagnostic image, not an installation release. Do not flash/install or perform destructive disk actions without passing the gates below and a fresh explicit user go/no-go.

## Target change (20 October 2026)

Confirmed by the user in answer to direct questions:

- **The HP Envy x360 (1 TB) is the only install target.** The finished OS replaces Windows there.
- **The Surface Laptop Studio is the test machine**, and is where the product must first "work perfectly".
- **The Surface Pro 8 is dropped.** Its earlier approvals are withdrawn, not deferred.
- **The route:** prove it on the Laptop Studio, then replace Windows on the Envy. Nothing is written to the Envy until that point and until a fresh explicit go-ahead.
- **The Envy's specs stay as recorded** (Ryzen 7 8840HS, 16 GB, 1 TB) — deliberately not re-measured yet.

Consequences:

- **No erase approval covers the Envy.** Its 1 TB internal disk holds Windows and the project builds there. Nothing has been written.
- **The Envy is AMD** (Ryzen 7 8840HS, Radeon 780M, AMD-V), unlike the Intel Tiger Lake Surfaces. Platform-specific findings do not transfer.
- **Surface-specific work leaves the critical path**: the linux-surface kernel and Type Cover/touch/pen gaps no longer block the product, though they still limit what the Laptop Studio can test.

## Where we stopped

The latest ISO was built from the pinned Fedora KDE 44 base in WSL Ubuntu. SHA-256: `10074299b974eb005d0a38144d74b0dc02e1fa128684eb0f81b9cc9829a177ac`; `checkisomd5` passed. File: `C:\\Users\\kavsb\\Downloads\\Kavika-OS-0.1.0-Surface-Pro-8-Live-Preview.iso` (3,370,254,336 bytes).

On 19 October 2026 a disposable WHPX guest booted the earlier ISO (`10074299…`) to a working KDE desktop with the Test Centre, valid hardware report, enforcing SELinux and no failed units. **Meta+F12 workspace switching failed** because overlay files had CRLF line endings. That is fixed in source and in a rebuilt ISO (`57a851a70b1f6fdb17c0b1c1801bad52e4237c0888aaa88c5c15a5a2c2cfefd9`, 3,370,319,872 bytes, builder `b9141011…`), whose checksum, embedded media check and 30 Linux tests pass. **The rebuilt ISO has not been booted yet.** No physical disk, shared folder or Surface was used.

The project now has two Surface machines. The **Surface Pro 8** is the final install target and has never been booted with Kavi'ka. The **Surface Laptop Studio** (Core i5-11300H, 16 GiB, 256 GB NVMe, Iris Xe) already runs Fedora 44 and has KVM-capable hardware, so it is the first test machine; see `docs/surface-laptop-studio-test-machine.md`. Its results are evidence only, not proof for the Pro 8.

On 20 October 2026 the read-only preflight (`tools/surface-fedora-preflight.sh`) was run **on the Surface Laptop Studio**. It installed nothing and changed nothing. Result: **KVM is usable** (`vmx` present, `/dev/kvm` writable by the user, `kvm_intel` loaded, `qemu-system-x86_64`/`qemu-img`/`virsh`/`swtpm` and both OVMF files present), 7.0 GiB RAM available of 15.4 GiB, 203 GB free on the 235 GB root, TPM present, Secure Boot disabled **and the platform in Setup Mode**. `virt-manager` is missing and libvirt is not running (not needed by the direct-QEMU launcher). No touchscreen or pen input device was detected on the stock kernel, and a 1 TB USB disk (`sda`, "One Touch w/PW") is attached — enumerated only, never written. Full table in the Laptop Studio page. **Resume-plan step 1 is now complete; step 2 (booting the rebuilt ISO in a disposable KVM guest) is unblocked.**

B05's wallpaper readiness retry is not visually validated on this image. KDE/Test Centre passes belong to a previous ISO candidate and must not transfer to the current hash.

### Independent rebuild on the Laptop Studio (20 October 2026)

The ISO was rebuilt **on the Laptop Studio itself** from the pinned Fedora KDE 44 base, which was verified by SHA-256 against the pin (`c8295961…`). Output SHA-256 **`bd8407d6393a12f8a5829ef15a86371b854f08834d9fd7df4a85ddbdc8820e0d`**, 3,370,319,872 bytes, `checkisomd5` PASS, sidecar and manifest written. Full record: [build-2026-10-20-laptop-studio.md](docs/validation/build-2026-10-20-laptop-studio.md).

It is the **same size** as the WSL-built `57a851a7…` candidate but a **different hash** — same builder source (`b9141011…`), different toolchain and timestamps, so this is not a reproducibility result and neither hash is "the" canonical image.

The B06 root cause is confirmed fixed at build level: no text file in this ISO's `/boot/kavika-preview.cpio` overlay contains a CR byte, and its `etc/skel/.config/kwinrc` has `Number=2` plus `Linux` and `Windows (not installed)` with LF endings. The earlier ISO (`10074299…`) contains `\r\n` in the same file, which validates the check.

That image was then **booted in a disposable KVM guest on this machine and the switch works**. UEFI boot reached the KDE desktop with the Test Centre open; **Meta+F12 switched workspaces in both directions** (361k pixels change per press, return trip matching the original desktop to within 105 px); `getenforce` reported `Enforcing`; `systemctl is-system-running` reported `running`; `systemctl --list-units --state=failed` listed **0 units**; the hardware report ran in the guest; and `lsblk` showed only the private 16 GiB virtio disk and the QEMU DVD-ROM, confirming no host disk was exposed. **B06 is closed for `bd8407d6…`.** Full record: [vm-boot-2026-10-20-laptop-studio.md](docs/validation/vm-boot-2026-10-20-laptop-studio.md).

Note for anyone repeating the check: the QEMU monitor key name is **`meta_l-f12`**; `meta-f12` is rejected and the screen does not change, which is easy to misread as a failed shortcut.

### First physical Surface boot (20 October 2026)

The same image was written to a 4 GB USB stick (payload hashes verified on the stick before boot) and booted **on the Surface Laptop Studio from USB**. Reported results: pointer input works, **Meta+F12 switched workspaces repeatedly and worked every time**, and speakers, microphone, camera and Wi-Fi all work. Nothing was installed; afterwards the internal disk was unchanged (`nvme0n1p1` EFI, `p2` `/boot`, `p3` btrfs `fedora`) and no new firmware boot entry was created. Full record: [hardware-boot-2026-10-20-laptop-studio.md](docs/validation/hardware-boot-2026-10-20-laptop-studio.md).

This is the fourth independent confirmation of the B06 fix and the first on real firmware. Still untested on hardware: suspend/resume, native touch and pen (the preflight found no touchscreen or pen device on the stock kernel), touchpad-only input, Bluetooth, display scaling, and any Secure Boot chain — this machine has Secure Boot disabled with the platform in Setup Mode, so that path was not exercised. **The Surface Pro 8 has still never been booted, and its firmware state is unknown.**

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

1. **On the Surface Laptop Studio:** clone the repo, run `bash tools/surface-fedora-preflight.sh` (read-only; installs and changes nothing) and review its output. It reports KVM, tools, Secure Boot, TPM, RAM, disk and the hardware JSON. **Done 20 October 2026 — KVM usable, preflight page updated. No blockers.**
2. Copy the rebuilt ISO and its `.sha256` file to that machine. Boot it in a disposable KVM guest with `python3 tools/launch-preview-vm-linux.py --iso <iso> --sha256-file <sidecar> --vm-dir <new dir>`. The launcher refuses a hash mismatch and attaches no physical disk or shared folder. Repeat the functional test in `docs/validation/live-preview-0.1.0.md`. **Meta+F12 must now switch workspaces.** **Done 20 October 2026 for `bd8407d6…`: switch works both directions, SELinux enforcing, no failed units, no host disks visible.**
3. If the Windows helper is used instead, it needs at least 5 GiB free RAM (it had 3.7 GiB when last checked). The QEMU GTK window showed black in earlier captures, while screenshots taken with the QEMU monitor `screendump` command showed the desktop, so use `screendump` to see the screen.
4. Test the same ISO on the Surface Laptop Studio from external media, still without installing. **Done 20 October 2026:** USB boot worked, Meta+F12 repeated reliably, pointer, speakers, microphone, camera, Wi-Fi, battery and thermals all fine; touchscreen does not work on the stock kernel and no pen was available. **Bluetooth is now reported working as well, and Meta+F12 re-confirmed, on a live USB boot on 21 October 2026 (machine to confirm).** Instructions for the same test on the install-target laptop are in [testinstall.md](testinstall.md). The Pro 8 route is dropped, so the next machine is the HP Envy once the Laptop Studio "works perfectly" — and replacing the Envy's Windows needs a fresh explicit go/no-go, with its exact disk identified first.
5. Then feasibility-test full Windows 11 plus Comet in a KVM guest on the Laptop Studio (16 GiB host RAM), and record what does and does not transfer to the HP Envy, which is AMD and not Intel like the test machine. **Started 20 October 2026:** the ISO's own El Torito path still fails (`Time out`), but booting Setup from a GPT/ESP image attached as USB storage works — **Windows 11 Setup reached its "Select language settings" screen**. The `Time out` is `cdboot.efi` hanging, and the ESP must carry `\sources\boot.wim`. Recipe and evidence: [windows-setup-esp-2026-10-20.md](docs/validation/windows-setup-esp-2026-10-20.md). **D16 confirmed, D17 found:** the unattended `autounattend.xml` was not read because QEMU's `usb-storage` reports its media as **fixed** by default (`removable` default `off`); with the stick marked `removable=on` the answer file was read. Setup then blocked on the Windows 11 hardware requirements (TPM 2.0 / Secure Boot) despite `swtpm --tpm2`, because the guest OVMF is not the Secure Boot build; a `RunSynchronous` `LabConfig` bypass in the `windowsPE` pass cleared it, and Setup began **installing Windows 11**, then failed at the downlevel Finalize phase: **D18** — Setup serviced the boot files to the boot ESP attached `readonly=on` (`HarddiskVolume1`) and hit `0x13 ERROR_WRITE_PROTECT` (`0x80070013`), so the NVMe ESP stayed empty. **Fixed 21 October 2026:** with the boot ESP writable, Setup wrote the boot files, created a `Windows Boot Manager` firmware entry, and the install **completed — Windows 11 reached the desktop** (`Kavika-Win11-Install4`). Still to do: Comet, cross-OS integration (the Windows workspace and swipe), and the Envy transfer notes. **Install6 (21 October 2026):** with the boot ESP writable the install reached OOBE and created a `kavika` profile, but offline inspection through `qemu-nbd` showed the **NVMe's own ESP still empty** — the boot files sit on the attached USB ESP, so the guest still depends on external media (**D21**, the D20 caveat). **Fix applied:** the answer file now assigns the target ESP drive letter `S:` in `DiskConfiguration` and runs a plain (character-clean) `bcdboot C:\Windows /s S: /f UEFI` in the `specialize` pass — commit `bae321b`, answer stick `af.img` rebuilt. **D23 found while retrying:** every ESP image captured from an earlier run (`espD`/`espE`/`espF`/`espG`) is unusable as boot media — Setup rewrites `\EFI\Microsoft\Boot\bcd` (16,384 B pristine → 45,056 B) so its default entry points at the Windows that run installed, and on a fresh guest `bootmgfw` fails with `0xc000000e` and the guest powers off or reset-loops before Setup ever starts. Building a **pristine** ESP from the ISO's BCDs (`espP.img`) fixed it: `Kavika-Win11-Install11` booted once and started "Installing Windows 11". **Verified 21 October 2026:** install11 installed to the **desktop** (15.7 GiB), the NVMe's own ESP (partition 1) now carries `\EFI\Boot\bootx64.efi`, `\EFI\Microsoft\Boot\bootmgfw.efi` and `\EFI\Microsoft\Boot\BCD` (97 boot files), and a boot with **only the NVMe attached** (no USB ESP, no answer stick) reached the desktop — **the guest is self-contained** (**D21 closed**).
6. Still absent: Windows 11 and Comet, file sharing, gestures, a Surface-specific kernel, a supported installer, recovery and update. This is a diagnostic image and must not be flashed as the product.

## Repository/publishing

Repository: [kaavi-pixel/kavika-os](https://github.com/kaavi-pixel/kavika-os), public. The prior request authorizes source/documentation updates there without changing visibility; no ISO release. Do not claim a push unless verified.
