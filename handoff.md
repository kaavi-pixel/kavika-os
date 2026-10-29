# Kavi'ka OS: handoff

**Current status (29 October 2026).** The installer now has a proven graphical path: a compact passwordless test install completed all 2465 packages in a 2.5 GiB VM, booted into an autologged-in KDE desktop, and passed account, sudo, network, SELinux and provisioning-tool checks with 0 failed units ([record](docs/validation/compact-passwordless-vm-2026-10-29.md)). On the physical Envy, the D46 install reached SDDM; the reported password-change failure (D47) was not reproducible in the VM. The physical KIOXIA rewrite also completed and its read-only boot reached the Plasma first-run wizard (D48 resolved). The Envy's password repair uses the updated KAVIKA media's rescue mode. Consolidated physical-install history: [envy-physical-install-2026-10-27.md](docs/validation/envy-physical-install-2026-10-27.md).

Checkpoint updated 22 October 2026. The last boot-verified image (`b5b650bc…`) presents itself as **Kavi'ka OS** in `os-release`, ships the Windows workspace plumbing and the installer assets (pre-flight + kickstart), and is boot-verified in a KVM guest ([record](docs/validation/vm-boot-2026-10-22-laptop-studio.md)). A separate **automated dnf/netinst installer** installs Kavi'ka OS with the virtualization stack and the Windows provisioning tooling, and boots to first-boot. On 23 October 2026 the Windows track gained the tooling it was missing: a media builder, a one-command provisioner and a first-login opt-in, with the guest installed end-to-end from builder-made media, self-contained and running Firefox ([record](docs/validation/windows-provisioning-2026-10-23.md)). The live preview remains a diagnostic image, not an installation release. The [gap checklist below](#gaps-vs-a-normal-installed-fedora-and-vs-windows) states exactly what is missing versus a normal installed Fedora and versus Windows. Do not flash/install or perform destructive disk actions without passing the gates below and a fresh explicit user go/no-go.

**Progress to a full working OS: about 25%.** Per-stage breakdown is tracked in [os-implementation-plan.md](os-implementation-plan.md#stage-progress-22-october-2026).

## Target change (20 October 2026)

Confirmed by the user in answer to direct questions:

- **The HP Envy x360 (1 TB) is the only install target.** The finished OS replaces Windows there.
- **The Surface Laptop Studio is the test machine**, and is where the product must first "work perfectly".
- **The Surface Pro 8 is dropped.** Its earlier approvals are withdrawn, not deferred.
- **The route:** prove it on the Laptop Studio, then replace Windows on the Envy.
- **The Envy's specs stay as recorded** (Ryzen 7 8840HS, 16 GB, 1 TB) — deliberately not re-measured yet.
- **The Envy's Windows is already gone** (user-reported 24 October 2026: wiped accidentally during an earlier install attempt). The "do not touch the Envy" constraint is therefore moot in practice — there is no Windows left there to preserve — and its internal disk is now just a ~954 GB NVMe.

Consequences:

- **Standing erase permission now covers the test machines and the Envy** (user, 24 October 2026: "EVERY single test computer I have has either been Wiped, or is ok to be Wiped. I give you all permissions."). This does **not** relax the consent gate: the target must still be named explicitly on the kernel command line, and the gate still refuses unknown, mounted, too-small and pseudo disks plus the boot medium itself. Permission to wipe is not a licence to guess *which* disk.
- **The machine the agent runs on is never a target.** It carries a 237.5 GB Hynix NVMe and holds the repo and the ISOs; the booted machine's 954 GB Samsung NVMe is a different machine, so wiping it cannot destroy the build tree.
- **The Envy is AMD** (Ryzen 7 8840HS, Radeon 780M, AMD-V), unlike the Intel Tiger Lake Surfaces. Platform-specific findings do not transfer.
- **Surface-specific work leaves the critical path**: the linux-surface kernel and Type Cover/touch/pen gaps no longer block the product, though they still limit what the Laptop Studio can test.
- **Open product question (raised 24 October 2026): can the desktop be swapped from KDE to GNOME?** Yes, and the installer is already most of the way there — but the **swipe-to-Windows gesture is the part that is not portable**, because there is no custom swipe code: it relies on Plasma's built-in three-finger horizontal swipe switching virtual desktops, configured by `/etc/skel/.config/kwinrc` (`Number=2`, `Rows=1`). GNOME also switches workspaces on a horizontal three-finger swipe, but its workspace model differs (dynamic and vertical by default), so this needs real testing on hardware rather than a config copy. The rest is mechanical: the package group, the display manager, a handful of KDE-only skel files (`kwinrc`, `kded_device_automounterrc`, `plasma-welcome`), the Meta+F12 fallback (a KWin script, needing a gsettings equivalent), and the `os-release` wording. `%post` already enables whichever display manager it finds (`sddm`/`gdm`/`lightdm`), so it needs no change. The live preview would also need the Workstation live ISO as its base instead of the KDE one. Preferred shape if it happens: a build option (`--desktop kde|gnome`) so both are first-class and testable, not a fork.

## Where we stopped

The latest ISO was built from the pinned Fedora KDE 44 base in WSL Ubuntu. SHA-256: `10074299b974eb005d0a38144d74b0dc02e1fa128684eb0f81b9cc9829a177ac`; `checkisomd5` passed. File: `C:\\Users\\kavsb\\Downloads\\Kavika-OS-0.1.0-Surface-Pro-8-Live-Preview.iso` (3,370,254,336 bytes).

On 19 October 2026 a disposable WHPX guest booted the earlier ISO (`10074299…`) to a working KDE desktop with the Test Centre, valid hardware report, enforcing SELinux and no failed units. **Meta+F12 workspace switching failed** because overlay files had CRLF line endings. That is fixed in source and in a rebuilt ISO (`57a851a70b1f6fdb17c0b1c1801bad52e4237c0888aaa88c5c15a5a2c2cfefd9`, 3,370,319,872 bytes, builder `b9141011…`), whose checksum, embedded media check and 30 Linux tests pass. **The rebuilt ISO has not been booted yet.** No physical disk, shared folder or Surface was used.

The project's target is now the **HP Envy x360 (1 TB)**, which has been booted live from USB with Kavi'ka (first Envy boot, 21 October 2026, Meta+F12 and Bluetooth reported working). The **Surface Laptop Studio** (Core i5-11300H, 16 GiB, 256 GB NVMe, Iris Xe) runs Fedora 44 and is the **test machine**; see `docs/surface-laptop-studio-test-machine.md`. Its results are evidence only, never proof for the AMD Envy. The **Surface Pro 8 is dropped** as a target, and its earlier approvals are withdrawn rather than transferred.

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

## Gaps vs a normal installed Fedora and vs Windows

Recorded 22 October 2026 so "what is missing" is an explicit checklist, not an implication.
Each gap names what closes it.

### Versus a normal installed Fedora

| Gap | Why it exists | What closes it |
|---|---|---|
| **Installable** — an automated dnf/netinst installer is built and KVM-verified both offline (`cdrom` source) and over the network (`url` source): installs Kavi'ka OS + the virtualization stack, boots to first-boot; the live image itself is still an *interactive* installer only | live installs cannot be kickstart-automated (Anaconda ignores kickstart in live mode), so the automated path is a separate netinst build | T19 rungs 1–2 done (non-selected disk proven byte-identical; refusal matrix none/mismatch/too-small/pseudo all fail closed). **Rung 3 (physical USB) is in progress, and a real attempt reshaped the media and refusal path:** media identity fixed so USB boot works at all (D36), a refusal now prints a readable banner instead of leaving a dead pane (D37), the boot medium can no longer be named as its own target (D38), the banner names the machine's real disks instead of a copyable `/dev/sdX` placeholder (D39), and the writer no longer rejects stock Fedora ISOs (D40). **Written to real hardware on 24 October 2026:** the Envy's NVMe was installed through QEMU while in a USB enclosure, using a test-consented image targeting `/dev/nvme0n1`. ESP contents, the fstab ESP UUID and the generic initramfs are verified on the mounted disk. The physical Envy reached SDDM after D46; a complete autologged-in KDE desktop is now also proven in the compact VM validation, with D47 not reproducible there. Then the Envy gate — **plan: [installerinstallation.md](installerinstallation.md); proofs: [install record](docs/validation/vm-install-2026-10-22-laptop-studio.md), [consent and media validation](docs/validation/installer-consent-2026-10-24.md), [physical install record](docs/validation/envy-physical-install-2026-10-27.md)** |
| **No persistence** — the session runs from RAM; files, settings and any guest vanish at shutdown | live-image architecture; the 3.8 GB stick also cannot hold an overlay plus a 16 GB Windows guest | installation to real storage (OS4); optionally a persistent live overlay on a larger stick |
| **No user accounts / first boot** — a single live user; no account creation or personal settings | live session | the installer's first-boot setup (T20) |
| **No system updates** — no persistent root to `dnf update` | live session | an installed system plus a validated update/upgrade procedure (O04/T22) |
| **No recovery/rollback** — no rescue path defined | nothing is installed, so there is nothing to roll back to | OS4: recovery/rollback that preserves user and guest data (T22) |
| **Secure Boot chain unvalidated** — upstream signed components are preserved, but the full chain is untested on every machine | measurement work not done | live and installed Secure Boot validation on the target (T21) |
| **Identity** — the volume label stays `Fedora-KDE-Live-44`, which is load-bearing for live boot | `root=live:CDLABEL=…` depends on the label; changing it breaks the live boot | **partially closed 22 Oct**: `/usr/lib/os-release` now presents Kavi'ka OS while keeping `VERSION_ID=44` so `$releasever` still resolves; the label stays until the installed-OS milestone makes it irrelevant |

### Versus Windows (the product's promised Windows workspace)

| Gap | Why it exists | What closes it |
|---|---|---|
| **No Windows guest in the image** — no Windows, no licence, no guest disk (Kavi'ka ships none of that, by policy) | provisioning is an opt-in, licensed step | **Tooling closed 23 October 2026**: the image ships a one-command provisioner (`kavika-windows-provision`), the media builder, `autounattend.xml` and a first-login opt-in; the installer now carries their dependencies (D31). Verified end-to-end: builder-made media installs Windows 11, the guest boots self-contained, Firefox opens ([record](docs/validation/windows-provisioning-2026-10-23.md)). Still open: the opt-in dialog drawn in a real KDE session, the desktop switch and swipe on a touchpad host, and running the provisioner from inside a booted Kavi'ka |
- **No cross-OS shared folder** | not implemented | the authenticated, guest-network-restricted share (F07–F09). Note that F04 does **not** require reusing the user's existing Windows install: a shared folder with any Windows satisfies it, and mounting the existing NTFS partition directly while the guest is off is the fastest migration path ([windows-reuse-existing-install.md](docs/windows-reuse-existing-install.md)). |
| **No swipe** — three-finger switching is Plasma's built-in default on a single-row layout, but it has never been exercised on a KDE host with a touchpad | the dev machine runs GNOME, and a VM has no touchpad | live/installed boot on a touchpad machine, then the F02/F03 tests |
| **No VM lifecycle controls** — suspend/resume with the guest, snapshots, guest updates | not implemented | the controller milestone (R04, T12, T15) |
| **No clipboard sharing** | deliberately off until consent | opt-in clipboard after T10 |

Everything in these tables is already tracked in features.md and the implementation plans; this section is the single checklist view of "what is missing vs a real OS".

## Resume plan

1. **On the Surface Laptop Studio:** clone the repo, run `bash tools/surface-fedora-preflight.sh` (read-only; installs and changes nothing) and review its output. It reports KVM, tools, Secure Boot, TPM, RAM, disk and the hardware JSON. **Done 20 October 2026 — KVM usable, preflight page updated. No blockers.**
2. Copy the rebuilt ISO and its `.sha256` file to that machine. Boot it in a disposable KVM guest with `python3 tools/launch-preview-vm-linux.py --iso <iso> --sha256-file <sidecar> --vm-dir <new dir>`. The launcher refuses a hash mismatch and attaches no physical disk or shared folder. Repeat the functional test in `docs/validation/live-preview-0.1.0.md`. **Meta+F12 must now switch workspaces.** **Done 20 October 2026 for `bd8407d6…`: switch works both directions, SELinux enforcing, no failed units, no host disks visible.**
3. If the Windows helper is used instead, it needs at least 5 GiB free RAM (it had 3.7 GiB when last checked). The QEMU GTK window showed black in earlier captures, while screenshots taken with the QEMU monitor `screendump` command showed the desktop, so use `screendump` to see the screen.
4. Test the same ISO on the Surface Laptop Studio from external media, still without installing. **Done 20 October 2026:** USB boot worked, Meta+F12 repeated reliably, pointer, speakers, microphone, camera, Wi-Fi, battery and thermals all fine; touchscreen does not work on the stock kernel and no pen was available. **Bluetooth is now reported working as well, and Meta+F12 re-confirmed, on a live USB boot on 21 October 2026 (machine to confirm).** Instructions for the same test on the install-target laptop are in [testinstall.md](testinstall.md). The Pro 8 route is dropped, so the next machine is the HP Envy once the Laptop Studio "works perfectly" — and replacing the Envy's Windows needs a fresh explicit go/no-go, with its exact disk identified first.
5. Then feasibility-test full Windows 11 plus Comet in a KVM guest on the Laptop Studio (16 GiB host RAM), and record what does and does not transfer to the HP Envy, which is AMD and not Intel like the test machine. **Started 20 October 2026:** the ISO's own El Torito path still fails (`Time out`), but booting Setup from a GPT/ESP image attached as USB storage works — **Windows 11 Setup reached its "Select language settings" screen**. The `Time out` is `cdboot.efi` hanging, and the ESP must carry `\sources\boot.wim`. Recipe and evidence: [windows-setup-esp-2026-10-20.md](docs/validation/windows-setup-esp-2026-10-20.md). **D16 confirmed, D17 found:** the unattended `autounattend.xml` was not read because QEMU's `usb-storage` reports its media as **fixed** by default (`removable` default `off`); with the stick marked `removable=on` the answer file was read. Setup then blocked on the Windows 11 hardware requirements (TPM 2.0 / Secure Boot) despite `swtpm --tpm2`, because the guest OVMF is not the Secure Boot build; a `RunSynchronous` `LabConfig` bypass in the `windowsPE` pass cleared it, and Setup began **installing Windows 11**, then failed at the downlevel Finalize phase: **D18** — Setup serviced the boot files to the boot ESP attached `readonly=on` (`HarddiskVolume1`) and hit `0x13 ERROR_WRITE_PROTECT` (`0x80070013`), so the NVMe ESP stayed empty. **Fixed 21 October 2026:** with the boot ESP writable, Setup wrote the boot files, created a `Windows Boot Manager` firmware entry, and the install **completed — Windows 11 reached the desktop** (`Kavika-Win11-Install4`). Still to do: cross-OS integration (the Windows workspace and swipe), and the Envy transfer notes (now drafted in [docs/envy-transfer.md](docs/envy-transfer.md)). **Comet/Firefox (21 October 2026, user-reported):** the user clarified that "Comet" is their browser — Firefox — and reports it **opens without problem** in the installed Windows guest (D24). **Install6 (21 October 2026):** with the boot ESP writable the install reached OOBE and created a `kavika` profile, but offline inspection through `qemu-nbd` showed the **NVMe's own ESP still empty** — the boot files sit on the attached USB ESP, so the guest still depends on external media (**D21**, the D20 caveat). **Fix applied:** the answer file now assigns the target ESP drive letter `S:` in `DiskConfiguration` and runs a plain (character-clean) `bcdboot C:\Windows /s S: /f UEFI` in the `specialize` pass — commit `bae321b`, answer stick `af.img` rebuilt. **D23 found while retrying:** every ESP image captured from an earlier run (`espD`/`espE`/`espF`/`espG`) is unusable as boot media — Setup rewrites `\EFI\Microsoft\Boot\bcd` (16,384 B pristine → 45,056 B) so its default entry points at the Windows that run installed, and on a fresh guest `bootmgfw` fails with `0xc000000e` and the guest powers off or reset-loops before Setup ever starts. Building a **pristine** ESP from the ISO's BCDs (`espP.img`) fixed it: `Kavika-Win11-Install11` booted once and started "Installing Windows 11". **Verified 21 October 2026:** install11 installed to the **desktop** (15.7 GiB), the NVMe's own ESP (partition 1) now carries `\EFI\Boot\bootx64.efi`, `\EFI\Microsoft\Boot\bootmgfw.efi` and `\EFI\Microsoft\Boot\BCD` (97 boot files), and a boot with **only the NVMe attached** (no USB ESP, no answer stick) reached the desktop — **the guest is self-contained** (**D21 closed**).
6. **Still absent from the shipped image:** a Windows guest (the feasibility install now works and is self-contained, but the preview provisions no Windows), cross-OS file sharing, the gesture-driven workspace switch, a supported installer, recovery/rollback and an update path. A Surface-specific kernel is off the critical path (the Pro 8 is dropped). This is a diagnostic image and must not be flashed as the product. Next step on the Windows track is wiring the guest and the swipe into a booted image, then the [Envy readiness gate](docs/envy-transfer.md). A design question raised 23 October 2026 — whether the Windows workspace can be the Windows **already installed on the machine** — is analysed (three routes, with the costs of P2V in place) in [windows-reuse-existing-install.md](docs/windows-reuse-existing-install.md); nothing about it has been tested, and the Envy's BitLocker state, Windows edition and M.2 slot count are unmeasured.

## Current next actions (29 October 2026)

1. **Refit the KIOXIA disk in the other test computer and complete the Plasma first-run wizard.** The physical install completed and its read-only boot reached that wizard; all disk checks passed.
2. **Finish the Envy account repair** through the updated KAVIKA media's **Troubleshooting → Rescue a Fedora system** path, then boot its own disk. D47 was not reproducible in the VM; do not change the shared account-creation logic based on that report alone.
3. **D41 and D46 are fixed in source and verified**; the installed identity is Kavi'ka OS and first boot reaches SDDM/KDE.
4. **Live preview's `Install Kavi'ka OS` entry** remains a known dead end and the live image remains diagnostic only.
5. **Then the product milestones**: wire the Windows guest and the swipe into a booted installed system, the opt-in dialog in a real KDE session, cross-OS file sharing (F07–F09), VM lifecycle (R04/T12/T15), updates and recovery/rollback (O04/T22), Secure Boot validation (T21).

## Repository/publishing

Repository: [kaavi-pixel/kavika-os](https://github.com/kaavi-pixel/kavika-os), public. The prior request authorizes source/documentation updates there without changing visibility; no ISO release. Do not claim a push unless verified.
