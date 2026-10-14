# Kavi'ka OS

A Linux-first desktop experience with a real Windows workspace one four-finger swipe away. The goal is to keep both environments available and make moving files between them straightforward.

**Status: planning repository, not an installable OS.** No runtime, installer, VM image, or hardware test results are included. The architecture below is a proposal to validate on the target laptop.

## Project documents

- [Features v2](features.md): revised product specification, preserving the original goal wording.
- [Implementation plan](implementation-plan.md): architecture, dependencies, milestones, and release gates.
- [Bug tracker](bugtracker.md): confirmed-defect policy, untested risks, and verification checklist.
- [Hand-off](hand-off.md): current state, next task, and unresolved decisions.
- [Original brief](docs/original-features.md): supplied text, with Markdown heading syntax repaired only.
- [GitHub Issues](https://github.com/kaavi-pixel/kavika-os/issues): live task and risk tracking.

## Proposed experience

```text
Laptop
└── Linux + KDE Plasma Wayland
    ├── Linux workspace: native applications
    └── Windows workspace: full-screen VM viewer
        └── Windows 11 in QEMU/KVM, managed by libvirt

Linux <── dedicated, permission-limited shared folder ──> Windows
```

Four-finger horizontal swipes should move between the two workspaces. A configurable host-owned keyboard shortcut should remain available as an alternative and emergency exit.

Wine is optional for individual applications; it is not the Windows workspace. Wine implements Windows application interfaces rather than running an installed Windows OS ([Wine](https://www.winehq.org/about)).

## First target

The supplied screenshot identifies an HP Envy x360 14-fa0xxx with an AMD Ryzen 7 8840HS, Radeon 780M graphics, 16 GB installed RAM, and approximately 954 GB total storage. These are screenshot observations, not hardware measurements or a compatibility certification.

The MVP should retain the graphics device for Linux and test a virtual display for Windows. Do not assume a second GPU, GPU passthrough support, smooth GPU-heavy workloads, or an available Windows VM licence.

## Scope and safety

- **In scope:** feature design, an implementation roadmap, issue tracking, and a later reversible prototype.
- **Not yet approved:** repartitioning, replacing the current Windows installation, changing firmware settings, or provisioning a VM on the user's laptop.
- **Not included:** Windows installation media, activation keys, VM disks, recovery keys, device identifiers, or the original hardware screenshot.
- **Licensing:** no project-wide open-source licence has been selected. Third-party components retain their own licences; a Windows licence decision remains a setup gate.

Start with milestone M0 in the implementation plan. Do not turn this repository into a distro image before the laptop feasibility gates pass.
