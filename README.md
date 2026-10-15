# Kavi'ka OS

<img src="assets/branding/kavi-ka-os-logo.png" alt="Kavi'ka OS logo: a black and pale-gold angular star on a mustard-gold background, with KAVI'KA above and OS below" width="320">

A Linux-first desktop experience with a real Windows workspace one four-finger swipe away. The goal is to keep both environments available and make moving files between them straightforward.

The Windows side must be full, general-purpose Windows, including Comet and normal user-chosen app installation, not a restricted collection of supported apps. A test matrix measures compatibility; it must not become an app allowlist, and a VM limitation must be reported rather than silently redefined as out of scope.

**Status: early development, not an installable OS.** The repository includes a preliminary Windows diagnostic script and an installable-OS roadmap, but no session controller, installer, guest image, or bootable ISO. The supplied archive records a Windows preflight run; this review did not reproduce it, and no Linux, VM-performance, or hardware acceptance gate has passed.

## Project documents

- [Features v2](features.md): revised product specification, preserving the original goal wording.
- [Implementation plan](implementation-plan.md): architecture, dependencies, milestones, and release gates.
- [OS implementation plan](os-implementation-plan.md): roadmap from the validated integration prototype to a live ISO, installer, and maintained OS release.
- [M0 evidence](docs/validation/m0.md): pending decisions and hardware validation record.
- [Surface test target](docs/surface-test-target.md): current spare-device target, approved erase scope, installation-media route, and identification blocker.
- [Archive review](docs/review-upload.md): changes reviewed, documentation corrections, and verification limits.
- [Bug tracker](bugtracker.md): confirmed-defect policy, untested risks, and verification checklist.
- [Hand-off](hand-off.md): current state, next task, and unresolved decisions.
- [Original brief](docs/original-features.md): supplied text, with Markdown heading syntax repaired only.
- [GitHub Issues](https://github.com/kaavi-pixel/kavika-os/issues): live task and risk tracking.

## Linux distribution

The proposed Linux base is **Fedora KDE Plasma Desktop**, using KDE Plasma on Wayland. Fedora is the distribution; KDE Plasma is the desktop environment.

- **Linux host:** Fedora KDE Plasma Desktop for native Linux applications and workspace switching.
- **Windows workspace:** a full Windows 11 installation in a QEMU/KVM virtual machine managed by libvirt, including Comet and normal user-chosen applications.
- **Release version:** not pinned yet. Select a supported Fedora release and record the exact versions after the M0 hardware and gesture checks pass.

This is the initial implementation target, not a claim that the laptop or every Windows workload has already been validated. If testing exposes an important compatibility limitation, revisit the architecture rather than silently reducing the full-Windows requirement.

### Why Fedora KDE?

- **Desktop integration:** KDE provides virtual desktops and window rules for assigning applications to a particular desktop, useful building blocks for the proposed dedicated Windows workspace ([KDE window behaviour](https://docs.kde.org/stable_kf6/en/kwin/kcontrol/windowbehaviour/index.html)).
- **Virtualisation tooling:** Fedora documents a QEMU/KVM and libvirt workflow with tools such as virt-manager and virt-viewer, matching the proposed guest architecture ([Fedora virtualisation guide](https://docs.fedoraproject.org/en-US/quick-docs/virtualization-getting-started/)).
- **Customisation and current software:** Fedora KDE emphasises a customisable desktop and updated drivers and kernels; these make it a reasonable candidate for the project's integration work, not proof of compatibility with this laptop ([Fedora KDE](https://fedoraproject.org/kde/)).

The trade-off is ongoing maintenance: Fedora documents approximately 13 months of updates per release, so the project must plan regular upgrades and regression tests ([Fedora KDE](https://fedoraproject.org/kde/)). Four-finger switching with a full-screen Windows viewer, memory headroom, and full-Windows application workflows still need hardware validation; choosing Fedora does not establish those results.

## Proposed experience

```text
Laptop
└── Fedora KDE Plasma Desktop (Wayland)
    ├── Linux workspace: native applications
    └── Windows workspace: full-screen VM viewer
        └── Windows 11 in QEMU/KVM, managed by libvirt

Linux <── dedicated, permission-limited shared folder ──> Windows
```

Four-finger horizontal swipes should move between the two workspaces. A configurable host-owned keyboard shortcut should remain available as an alternative and emergency exit.

Wine is optional for individual applications; it is not the Windows workspace. Wine implements Windows application interfaces rather than running an installed Windows OS ([Wine](https://www.winehq.org/about)).

## Project logo

The user-selected project logo is stored at [`assets/branding/kavi-ka-os-logo.png`](assets/branding/kavi-ka-os-logo.png). The supplied image is preserved unchanged; the README only sets its display width.

## First target: spare Surface Pro

The user has selected an old Surface Pro with Windows 11 and approximately 1 TB internal storage as the first physical test computer. Its exact model, architecture, CPU, RAM, and GPU are not yet known; the user cannot sign into its current Windows account.

The user explicitly permits replacing Windows on that spare Surface and erasing an empty 512 GB external SSD for installation media. The external SSD carries the installer; the intended installation uses the Surface's own 1 TB drive, not a 512 GB capacity limit.

The earlier HP Envy x360/Ryzen/16 GB evidence belongs to the helper computer, not this Surface. Do not carry its resource allocation into the Surface build; identify the Surface first and test the live environment before installation.

See the [Surface test plan](docs/surface-test-target.md) for no-login identification and the recorded erase scope. Keep the HP Envy's internal drive untouched.

## Scope and safety

- **In scope:** repository development toward a reversible prototype and, after validation, an installable Fedora-based OS. Build, installation, and release work have separate gates in the OS implementation plan.
- **Approved target scope:** replace Windows on the spare Surface and erase the empty 512 GB external SSD for media. Identify the exact physical disks before writes; no erasure has occurred.
- **Outside that approval:** HP Envy internal-disk changes, other drives, firmware-security changes, Windows licence purchases, and public distribution. Guest provisioning remains a separate opt-in step.
- **Not included:** Windows installation media, activation keys, VM disks, recovery keys, device identifiers, or the original hardware screenshot.
- **Licensing:** no project-wide open-source licence has been selected. Third-party components retain their own licences; a Windows licence decision remains a setup gate.

The user has requested a testable OS for the spare Surface. An explicitly labelled private boot/diagnostic preview may be built before all integration gates pass, but the full installer/release gates remain; booting a preview is not proof of full Windows functionality.

An upstream Fedora KDE 44 x86_64 ISO has been integrity-verified in the build sandbox. It remains unmodified Fedora, not a Kavi'ka image, and is not selected for the Surface until its architecture is known.

## Preliminary Windows checks

[`tools/Test-KavikaHost.ps1`](tools/Test-KavikaHost.ps1) queries Windows CIM information and prints a JSON report. Static review found no explicit configuration-changing commands; it was not executed during this review, and its existence is not a compatibility pass.

Run it only on the intended Windows test machine after reviewing the script:

```powershell
.\tools\Test-KavikaHost.ps1
```

Do not disable execution-policy or security controls just to run a downloaded script. Review the output before recording selected results in the M0 worksheet; Windows checks do not establish Linux touchpad, KVM, graphics, or sleep support.
