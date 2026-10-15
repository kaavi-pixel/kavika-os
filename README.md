# Kavi'ka OS

<img src="assets/branding/kavi-ka-os-logo.png" alt="Kavi'ka OS logo: a black and pale-gold angular star on a mustard-gold background, with KAVI'KA above and OS below" width="320">

A Linux-first desktop experience with a real Windows workspace one four-finger swipe away. The goal is to keep both environments available and make moving files between them straightforward.

The Windows side must be full, general-purpose Windows, including Comet and normal user-chosen app installation, not a restricted collection of supported apps. A test matrix measures compatibility; it must not become an app allowlist, and a VM limitation must be reported rather than silently redefined as out of scope.

**Status: planning repository, not an installable OS.** No runtime, installer, VM image, or hardware test results are included. The architecture below is a proposal to validate on the target laptop.

## Project documents

- [Features v2](features.md): revised product specification, preserving the original goal wording.
- [Implementation plan](implementation-plan.md): architecture, dependencies, milestones, and release gates.
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

## First target

The supplied screenshot identifies an HP Envy x360 14-fa0xxx with an AMD Ryzen 7 8840HS, Radeon 780M graphics, 16 GB installed RAM, and approximately 954 GB total storage. These are screenshot observations, not hardware measurements or a compatibility certification.

The MVP should retain the graphics device for Linux and test a virtual display for Windows. Do not assume a second GPU, GPU passthrough support, smooth GPU-heavy workloads, or an available Windows VM licence.

## Scope and safety

- **In scope:** feature design, an implementation roadmap, issue tracking, and a later reversible prototype.
- **Not yet approved:** repartitioning, replacing the current Windows installation, changing firmware settings, or provisioning a VM on the user's laptop.
- **Not included:** Windows installation media, activation keys, VM disks, recovery keys, device identifiers, or the original hardware screenshot.
- **Licensing:** no project-wide open-source licence has been selected. Third-party components retain their own licences; a Windows licence decision remains a setup gate.

Start with milestone M0 in the implementation plan. Do not turn this repository into a distro image before the laptop feasibility gates pass.
