# Kavi'ka OS

<img src="assets/branding/kavi-ka-os-logo.png" alt="Kavi'ka OS logo: a black and pale-gold angular star on a mustard-gold background, with KAVI'KA above and OS below" width="320">

A Linux-first desktop experience with a real Windows workspace one four-finger swipe away. The goal is to keep both environments available and make moving files between them straightforward.

The Windows side must be full, general-purpose Windows, including Comet and normal user-chosen app installation, not a restricted collection of supported apps. A test matrix measures compatibility; it must not become an app allowlist, and a VM limitation must be reported rather than silently redefined as out of scope.

**Status: development checkpoint, not an installation release.** A Fedora-based diagnostic ISO and its source are implemented. The previous build reached a working KDE desktop in a disposable VM, and the Test Centre, hardware report, installer guard, SELinux and networking checks passed there. Its Meta+F12 workspace switch failed because of a line-ending defect that is now fixed in source; the fixed image is rebuilt but not yet re-tested. No ISO is approved for flashing. Windows/Comet, cross-OS integration, a Surface-specific kernel and supported installation are not included. No Kavi'ka image has been booted on Surface hardware yet; a read-only inventory preflight has now been run on the Laptop Studio test machine (see [the Laptop Studio page](docs/surface-laptop-studio-test-machine.md)), which installed and changed nothing.

See [the preview guide](docs/live-preview.md), [build instructions](docs/build.md), and [validation record](docs/validation/live-preview-0.1.0.md) before using an image. A desktop named “Windows (not installed)” is a Linux workspace, not a Windows implementation.

## Project documents

- [Features v2](features.md): revised product specification, preserving the original goal wording.
- [Implementation plan](implementation-plan.md): architecture, dependencies, milestones, and release gates.
- [OS implementation plan](os-implementation-plan.md): roadmap from the validated integration prototype to a live ISO, installer, and maintained OS release.
- [Windows preview VM guide](docs/windows-vm-preview.md): disposable Linux smoke-test guest, not the full Windows product workspace.
- [Get a diagnostic ISO](docs/getting-the-iso.md): prepare an isolated Ubuntu-on-WSL builder, verify Fedora input and build the explicitly non-installable preview.
- [Build instructions](docs/build.md): pinned source, builder prerequisites, and validation limits.

- [Surface test targets](docs/surface-test-target.md): the Pro 8 final target, approved erase scope, media route, and remaining hardware checks.
- [Surface Laptop Studio test machine](docs/surface-laptop-studio-test-machine.md): the Fedora machine used for KVM and VM testing, how it differs from the Pro 8, and the safe test steps.
- [Archive review](docs/review-upload.md): changes reviewed, documentation corrections, and verification limits.
- [Bug tracker](bugtracker.md): confirmed-defect policy, untested risks, and verification checklist.
- [Handoff](handoff.md): paused checkpoint, exact validation boundary, permissions and resume instructions.
- [Original brief](docs/original-features.md): supplied text, with Markdown heading syntax repaired only.
- [GitHub Issues](https://github.com/kaavi-pixel/kavika-os/issues): live task and risk tracking.

## Linux distribution

The proposed Linux base is **Fedora KDE Plasma Desktop**, using KDE Plasma on Wayland. Fedora is the distribution; KDE Plasma is the desktop environment.

- **Linux host:** Fedora KDE Plasma Desktop for native Linux applications and workspace switching.
- **Windows workspace:** a full Windows 11 installation in a QEMU/KVM virtual machine managed by libvirt, including Comet and normal user-chosen applications.
- **Preview base:** Fedora KDE 44, upstream image `44-1.7.x86_64`, stock kernel `6.19.10-300.fc44.x86_64`. This pins the diagnostic build, not a hardware-approved production configuration.

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

## Targets: Surface Pro 8 and Surface Laptop Studio

| Machine | Role |
|---|---|
| **Surface Pro 8 Wi-Fi (model 1983)** | Final install target. Intel x86_64; exact CPU and RAM still need measuring ([Microsoft specifications](https://support.microsoft.com/en-us/surface/models/surface-pro-8-features-and-specs)). |
| **Surface Laptop Studio** (Core i5-11300H, 16 GiB, 256 GB NVMe, Iris Xe) | Test machine that already runs Fedora 44. Its KVM was confirmed usable by the read-only preflight on 20 October 2026, so it is where the Linux preview and Windows-in-a-VM experiments are tried first. Disk capacity is now measured; see [the Laptop Studio page](docs/surface-laptop-studio-test-machine.md). |

Both are Intel Tiger Lake machines, so CPU virtualisation, the Iris Xe graphics driver and the stock kernel behave similarly. The Laptop Studio is **not** a proxy for the Pro 8's Type Cover, touch, pen, tablet mode, cameras or storage budget. Treat everything learned on it as evidence, never proof.

The printed model **1983** identifies the Pro 8 as a **Wi-Fi model** ([Microsoft service guide](https://learn.microsoft.com/en-us/surface/service-guides/surface-pro8/surface-pro8-device-information-and-service-parts)). The owner reports a **128 GB factory marking** on it; actual installed capacity is still unmeasured, and a 128 GiB Windows guest disk is not a safe default. The owner permits replacing Windows on the Pro 8 and erasing the empty 512 GB external SSD used for media. That SSD carries the image; it is not a capacity limit on a future installation. USB keyboard, mouse and connection hardware are available.

The linux-surface compatibility matrix lists touchscreen and pen on both machines, and the Pro 8's Type Cover keyboard and touchpad, as needing its custom kernel ([linux-surface device matrix](https://github.com/linux-surface/linux-surface/wiki/Supported-Devices-and-Features)). The preview uses Fedora's stock kernel, so native Surface input is not promised. Cameras, sleep and Secure Boot remain unvalidated on both machines. No firmware-security changes are authorised.

The earlier HP Envy x360 (Ryzen 7 8840HS, 16 GB) is the build and emulation helper, not a Surface. Do not carry its numbers into either Surface build. The Laptop Studio holds the owner's working Fedora installation: never write an image to its internal drive or change its firmware settings without a fresh, explicit instruction.

See [the Surface test targets](docs/surface-test-target.md) and [the Laptop Studio page](docs/surface-laptop-studio-test-machine.md).

## Scope and safety

- **In scope:** repository development toward a reversible prototype and, after validation, an installable Fedora-based OS. Build, installation, and release work have separate gates in the OS implementation plan.
- **Approved target scope:** replace Windows on the Surface Pro 8 and erase the empty 512 GB external SSD for media. Identify the exact physical disks before writes; no erasure has occurred. This approval does **not** cover the Laptop Studio's disk.
- **Outside that approval:** HP Envy and Laptop Studio internal-disk changes, other drives, firmware-security changes, Windows licence purchases, and a public ISO release. Guest provisioning remains a separate opt-in step.
- **Not included:** Windows installation media, activation keys, VM disks, recovery keys, device identifiers, or the original hardware screenshot.
- **Licensing:** no project-wide open-source licence has been selected. Third-party components retain their own licences; a Windows licence decision remains a setup gate.

The user has requested a testable OS for the spare Surface. An explicitly labelled private boot/diagnostic preview may be built before all integration gates pass, but the full installer/release gates remain; booting a preview is not proof of full Windows functionality.

On 16 October the user requested a stop at a good checkpoint and a GitHub update after being informed that the existing repository is public. Source and documentation are updated in that repository without changing visibility; the ISO is not published or released.

The preview is composed from an integrity-verified Fedora KDE 44 x86_64 image plus a project-owned live-session overlay. The original Fedora kernel and base filesystem remain unchanged; this is not a custom Surface-kernel build or a completed Linux/Windows OS.

## Preliminary Windows checks

[`tools/Test-KavikaHost.ps1`](tools/Test-KavikaHost.ps1) queries Windows CIM information and prints a JSON report. Static review found no explicit configuration-changing commands; it was not executed during this review, and its existence is not a compatibility pass.

Run it only on the intended Windows test machine after reviewing the script:

```powershell
.\tools\Test-KavikaHost.ps1
```

Do not disable execution-policy or security controls just to run a downloaded script. Review the output before recording selected results in the M0 worksheet; Windows checks do not establish Linux touchpad, KVM, graphics, or sleep support.
