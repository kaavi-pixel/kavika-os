# Kavi'ka OS: OS implementation plan

Status: active roadmap; no bootable image or passed hardware gate yet.

Version 0.2 | Reviewed 15 October 2026.

## Product and scope

Build an installable Fedora KDE based Linux distribution with Kavi'ka branding,
a real Windows workspace, four-finger switching, and a dedicated shared folder.
Use the Linux kernel and upstream desktop rather than building a kernel or desktop
from scratch. Preserve full general-purpose Windows, including Comet and normal
user-chosen applications. VM compatibility must be measured, not promised.

The supplied project changes introduce this OS roadmap and repository implementation.
This does not authorise laptop disk changes, firmware changes, Windows purchases,
VM provisioning on the laptop, or public distribution. Keep the repository private.
Preserve the approved logo and original brief unchanged.

## Architecture

- Base: a supported Fedora KDE release, Plasma Wayland, x86_64 initially.
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

The exact Fedora release and dependencies remain unpinned until hardware validation.
Record upstream source revisions, package versions, repository configuration and
checksums before the first image build. Do not guess package groups or reuse an
obsolete release merely to make a build complete.

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
Small preparation tasks can proceed early, but image composition waits for OS2.

The later OS requirements O01–O04 are defined in `features.md`; T17–T23 in `bugtracker.md` cover image provenance, live boot, installation safety, first-run consent, host Secure Boot, upgrades/recovery, and distribution readiness. No later-stage test starts as passed.

| Later stage | Live issue | Review state |
|---|---|---|
| OS3: development live ISO | [#12](https://github.com/kaavi-pixel/kavika-os/issues/12) | Blocked by OS2/M5 |
| OS4: installer and first boot | [#13](https://github.com/kaavi-pixel/kavika-os/issues/13) | Blocked by OS3 |
| OS5: hardware pilot | [#14](https://github.com/kaavi-pixel/kavika-os/issues/14) | Blocked by OS4 and specific test-disk approval |
| OS6: maintained release | [#15](https://github.com/kaavi-pixel/kavika-os/issues/15) | Blocked by OS5 and release decisions |

## Implementation order

1. Run `tools/Test-KavikaHost.ps1` on the target Windows machine. It only reads
   hardware capacity and virtualisation indicators. Copy reviewed results into
   `docs/validation/m0.md`; do not commit raw system dumps or identifiers.
   Record source-machine role, UTC time and script revision/hash; the archive's
   earlier run summary is supplied evidence, not reproduced by this review.
2. Record Windows edition/licensing, additional representative workloads, and an
   approved backed-up external SSD or other reversible Linux test route. An
   existing Windows activation is not proof of guest licensing rights.
3. On that Linux environment, check `/dev/kvm`, GPU inventory, touchpad four-finger
   events, Wi-Fi, keyboard, audio, brightness, touch/pen and suspend. Measure
   VM-off CPU, memory and battery baseline and record exact software versions.
4. Manually validate a fresh Windows guest and viewer before writing provisioning
   automation. Test the initial 6 GiB memory proposal against Comet and concurrent
   Linux work; change or reject it based on measured performance.
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
No milestones are complete merely because this plan or a script exists.

## Current execution status

- OS roadmap created and the prototype/OS release boundary documented.
- Read-only Windows preflight implemented; execution results are preliminary,
  archive-reported and not reproduced during this review. Static inspection found
  no explicit configuration-changing commands; parser and runtime checks remain.
- M0 evidence worksheet created. User decisions and Linux hardware testing remain.
- No VM provisioned, image built, disk altered, or milestone declared complete.

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
