# Kavi'ka OS: OS implementation plan

Checkpoint updated 19 October 2026. WSL Ubuntu produced the pinned Fedora-derived diagnostic ISO. A WHPX-accelerated disposable VM booted the previous build to a working KDE desktop; the Test Centre, hardware report, installer guard, SELinux and network checks passed, but the Meta+F12 workspace switch failed because overlay files had CRLF line endings. The source fix is committed and a fixed ISO is rebuilt; it is not yet re-tested. A second machine, a Fedora-running Surface Laptop Studio, is available for KVM and virtual-machine testing; the Surface Pro 8 remains the final target. Nothing has run on a Surface yet.

Version 0.5 | Updated 19 October 2026 for the Surface Pro 8 target, the Surface Laptop Studio test machine and the current diagnostic-preview gate.

## Product and scope

Build an installable Fedora KDE based Linux distribution with Kavi'ka branding,
a real Windows workspace, four-finger switching, and a dedicated shared folder.
Use the Linux kernel and upstream desktop rather than building a kernel or desktop
from scratch. Preserve full general-purpose Windows, including Comet and normal
user-chosen applications. VM compatibility must be measured, not promised.

The supplied project changes introduce this OS roadmap and repository implementation.
The user now authorises complete Windows replacement on the Surface Pro 8 (not the Laptop Studio)
and erasure of an empty 512 GB external SSD for installation media. Identify the
actual devices before writing. HP Envy disk changes, firmware-security changes,
Windows purchases, guest provisioning, and a public ISO release are not included.
The user requested this checkpoint's source/docs be updated in the existing public
repository after the visibility notice; do not change its visibility.
Preserve the approved logo and original brief unchanged.

## Architecture

- Base: Fedora KDE 44 `44-1.7.x86_64` is pinned for the diagnostic preview; Surface Pro 8 Wi-Fi (final target) and Surface Laptop Studio (Fedora test machine) are Intel/x86_64 Tiger Lake machines. Hardware approval remains pending; see the sourced [target record](docs/surface-test-target.md).
- Windows: QEMU/KVM and libvirt, with SPICE as the first viewer candidate.
- Integration: an unprivileged session controller, desktop rules, explicit escape,
  and a private authenticated shared folder. Windows starts on demand.
- Packaging: RPM packages for our integration, assets, and configuration; use
  upstream packages for the kernel, desktop, hypervisor, and installer.
- Installation media: evaluate Fedora's Kickstart and Lorax livemedia-creator
  workflow after prototype validation. Reuse the upstream KDE live configuration
  at a recorded revision instead of inventing a minimal desktop image.
- Updates: upstream Fedora repositories plus a signed Kavi'ka package repository
  when distribution is approved. Keep upstream OS identity useful to package tools;
  apply product branding through supported mechanisms.
- Windows installation media, licence keys, user files, guest disks, and account
  credentials are never bundled in the Linux ISO or source repository.

The preview pins its upstream ISO SHA-256 and records payload hashes and build
tools; the production package set remains subject to hardware validation.
Its small initramfs live-update overlay is an interim diagnostic build mechanism,
not a replacement for the planned RPM-based installation/update pipeline.
See [build instructions](docs/build.md) and [preview evidence](docs/validation/live-preview-0.1.0.md).

## Delivery stages

| Stage | Work and deliverable | Acceptance gate |
|---|---|---|
| OS0: feasibility | Complete existing M0; record host checks, Windows edition/licensing, backup readiness, test route, device tests and VM-off baseline | Sanitised evidence and an approved reversible environment; unknown results remain unknown |
| OS1: working integration | Complete existing M1-M4: full Windows and Comet, display, gestures, input escape, file sharing, lifecycle and recovery | F01–F07/F15 and T01–T13/T16 pass on target hardware; F08 belongs to OS2/M5. No unresolved critical compatibility issue. |
| OS2: packaged prototype | Complete M5 reproducible setup, uninstall, backup/restore and pilot; package controller, desktop assets and defaults as RPMs | F08 and T14/T15 pass; clean test system reproduces the experience; removal preserves guest/user data and restores settings. Regression of all prototype requirements passes. |
| OS3: development live ISO | Pin supported base and upstream KDE live sources; add tested RPMs and original logo; build in a disposable Linux builder | ISO boots in a disposable UEFI VM, reaches KDE, exposes diagnostics and installer; no Windows payload or automatic disk changes |
| OS4: installed OS | Validate upstream installer, first boot, user creation, networking and recovery; add an opt-in Windows setup assistant | Installation to a blank disposable virtual disk passes; installer requires explicit target selection; existing-disk tests use expendable fixtures |
| OS5: target laptop pilot | Boot live media first, test devices and Secure Boot; install only to the separately approved test disk; repeat full acceptance suite | Hardware evidence, Windows/Comet workflows, four-finger switching, recovery and performance pass |
| OS6: release and maintenance | Select project licence, review Fedora branding/trademark conditions, third-party notices and redistribution; sign RPMs/checksums and publish release notes after approval | Independently repeatable build procedure, validated installation/upgrade/recovery, no release-blocking failures and user acceptance |

OS0-OS2 implement the existing integration plan. OS3-OS6 extend it into an OS
product; they do not declare the integration prototype to be a finished OS.
Full integration/release image composition remains gated by OS2. The user's
request for a testable system permits an earlier private boot/diagnostic preview
for the Surface, clearly labelled as incomplete; it does not pass or bypass the
full Windows, installer-safety, or hardware acceptance gates.

The later OS requirements O01–O04 are defined in `features.md`; T17–T23 in `bugtracker.md` cover image provenance, live boot, installation safety, first-run consent, host Secure Boot, upgrades/recovery, and distribution readiness. No later-stage test starts as passed.

| Later stage | Live issue | Review state |
|---|---|---|
| OS3: development live ISO | [#12](https://github.com/kaavi-pixel/kavika-os/issues/12) | Blocked by OS2/M5 |
| OS4: installer and first boot | [#13](https://github.com/kaavi-pixel/kavika-os/issues/13) | Blocked by OS3 |
| OS5: hardware pilot | [#14](https://github.com/kaavi-pixel/kavika-os/issues/14) | Blocked by OS4 and specific test-disk approval |
| OS6: maintained release | [#15](https://github.com/kaavi-pixel/kavika-os/issues/15) | Blocked by OS5 and release decisions |

## Implementation order

1. Model identification is complete: Surface Pro 8 Wi-Fi, model 1983. Validate the
   x86_64 diagnostic preview in a disposable VM, then collect live Surface
   resources/device information without depending on Windows or PowerShell.
   Record source-machine role, UTC time and tool revision/hash; earlier HP/archive
   results do not establish Surface hardware.
2. Use the approved empty 512 GB external SSD as media and the Surface's internal
   drive as the eventual installation destination. Its factory marking is 128 GB,
   replacing the earlier 1 TB assumption; measure actual capacity and identities
   before writes and keep the HP Envy internal drive untouched. Record guest
   Windows edition/licensing and additional representative workloads. An
   existing Windows activation is not proof of guest licensing rights.
3. On that Linux environment, check `/dev/kvm`, GPU inventory, touchpad four-finger
   events, Wi-Fi, keyboard, audio, brightness, touch/pen and suspend. Measure
   VM-off CPU, memory and battery baseline and record exact software versions.
4. Manually validate a fresh Windows guest and viewer before writing provisioning
   automation. Choose a Surface-specific memory/storage budget against Comet and
   concurrent Linux work; do not reuse the HP's 6 GiB/128 GiB proposal.
5. Implement and test a narrow controller with libvirt state events, bounded
   timeouts, duplicate-launch protection and reconnect. Never force power-off on
   timeout. Add workspace rules only against the validated Plasma API.
6. Implement authenticated directory sharing restricted to the guest network.
   Keep clipboard, drive and USB redirection off by default. Test integrity,
   symlink/path escapes, unauthorised access and LAN isolation.
7. Package the proven components and validate setup, removal and restoration.
8. Create and validate the live-image configuration and isolated build procedure.
   Use a disposable Linux VM/builder with no physical disks exposed. Never run
   `livemedia-creator --no-virt` on the user's everyday host.
9. Test live boot and installation, then updates, rollback/recovery, and laptop
   acceptance. Publish only after the release gate is satisfied.

## Repository deliverables

Add directories when their corresponding implementation starts, not as placeholders:

| Path | Purpose |
|---|---|
| `tools/` | Read-only diagnostics and later explicit build helpers |
| `docs/validation/` | Reviewed evidence, versions and unresolved results |
| `src/` and `tests/` | Session controller and meaningful lifecycle/security tests |
| `packaging/` | RPM specs, supported defaults and removal procedures |
| `image/` | Pinned upstream inputs and Kavi'ka live-image configuration |
| `docs/build.md` | Validated builder prerequisites and exact build commands |
| `docs/install.md` | Tested installation, recovery and Windows setup instructions |

## Validation and release evidence

Retain the existing features and tracker acceptance criteria. Add ISO checksum,
source commit, build tool versions, package manifest, build logs reviewed for
secrets, firmware mode and clean-install results to each candidate record.
Record results as pass, fail, blocked or not tested with reproduction steps.
Do not claim bit-for-bit reproducibility until two isolated builds demonstrate it.

Test UEFI and the intended Secure Boot path; upstream signed components alone do
not prove a custom image boots with Secure Boot enabled. Test the installer only
on disposable disks first. Validate a supported base upgrade and recovery before
calling the OS maintainable. Track upstream security updates and rerun integration
acceptance after kernel, Plasma, viewer, libvirt or Windows changes.

Use GitHub Issues for live milestone state, linking evidence before closure.
- High-severity plan/delivery gates remain OPEN: KDE graphics boot, Surface hardware acceptance, Windows/Comet guest, supported installer, recovery/update, and project/release license. The exact currently verified milestone and blocked conditions are in the validation record. No Surface flash/install authorization has been granted by this diagnostic run.

## Current execution status

- OS roadmap created and the prototype/OS release boundary documented.
- WSL build completed from the pinned Fedora KDE 44 input; current local derived ISO SHA-256 is recorded in validation evidence.
- Current QEMU test reached Fedora live-session login on serial; GTK graphics black, so KDE/Test Centre remain unverified.
- No Surface boot/write, supported installer, Windows/Comet guest, integration, or milestone acceptance is complete.
- No Windows VM provisioned, user disk altered, or milestone declared complete.
- Fedora KDE 44 input signature/checksum verified; current diagnostic ISO and its exact validation boundary are recorded in [current evidence](docs/validation/live-preview-0.1.0.md).
- Surface model is identified; actual RAM/storage, native input, KVM, security
  and full Windows/Comet feasibility remain outstanding.

The desktop theme specification drafted earlier remains unapproved design work;
the uploaded archive contains no theme package or theme implementation. Packaging
the original logo is separate from approving derived icons or a custom theme.

## Builder safety and reference limits

The Fedora wiki example targets Fedora 39 and uses `--no-virt`; it is a historical workflow reference, not a current release choice or a command to copy unchanged ([Fedora live-image workflow](https://fedoraproject.org/wiki/Livemedia-creator-_How_to_create_and_use_a_Live_CD)). The Lorax source documentation warns that no-virt operation can affect real devices and recommends expendable/virtual build systems; it also notes that current supported operation can use SELinux enforcing ([Lorax documentation](https://github.com/weldr/lorax/blob/master/docs/livemedia-creator.rst)).

Keep any build tooling inside a disposable Linux VM with no physical-disk passthrough, private credentials, or shared writable host directories. A container/mock chroot alone is not the isolation boundary promised by this plan; do not weaken SELinux or run installer tooling on the everyday host to reproduce an old example.

Snapshot and record repository metadata/package inputs if repeatability is claimed; pinned package names without retrievable versions are not enough. Signing packages and checksums is separate from proving the UEFI Secure Boot chain; validate both through their respective release gates.

## Build references

- [Fedora live-image workflow](https://fedoraproject.org/wiki/Livemedia-creator-_How_to_create_and_use_a_Live_CD)
- [Lorax livemedia-creator source documentation](https://github.com/weldr/lorax/blob/master/docs/livemedia-creator.rst)

These establish the candidate image-building mechanism; validate the selected
release's actual tooling before writing executable image-build commands.
