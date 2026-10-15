# Kavi'ka OS: hand-off

This repository contains the product specification, prototype and OS roadmaps, and a preliminary Windows diagnostic script. There is no runnable desktop integration or bootable OS, and no hardware acceptance gate has passed.

## Current state

- **User goal:** preserve Linux and Windows workspaces, switch with a four-finger swipe or keybind, and transfer files easily.
- **Approved logo:** `assets/branding/kavi-ka-os-logo.png`, supplied and selected by the user on 15 October 2026. Keep the original artwork unchanged unless a new variant is requested.
- **Explicit clarification:** Windows should have “everything,” including Comet. Preserve a full general-purpose Windows installation, not a stripped-down desktop, Wine substitute, or allowlisted app collection; Comet is now a P0 requirement (F15/T16).
- **Primary test target:** spare old Surface Pro, user-reported Windows 11 and approximately 1 TB internal storage; exact model/architecture, CPU, RAM, and GPU unknown. Windows account password is unavailable.
- **Helper only:** the HP Envy x360/Ryzen/16 GB observations belong to the main/helper computer and must not be treated as Surface measurements.
- **Recommended direction:** Linux/KDE host with a real Windows VM and a dedicated shared folder; validate the display backend before building the integration.
- **Approved erase scope:** replace Windows on the spare Surface and erase the empty 512 GB external SSD for media. Preserve that approval; still identify exact physical disks before writes. The HP internal drive and other disks are out of scope.
- **Undecided:** model-specific image/architecture, guest edition/licensing, resource allocations, and firmware-security changes. A test matrix must never restrict app installation.
- **Imported additions:** `os-implementation-plan.md`, `tools/Test-KavikaHost.ps1`, and `docs/validation/m0.md`; the script is preserved unchanged from the supplied archive.
- **Evidence status:** Windows 11 Home Single Language and capacity/virtualisation values are historical archive reports, not Surface measurements. Surface Windows 11 is user-reported, but edition, guest licensing, and Linux device/KVM support remain unresolved.
- **Review record:** [archive review](docs/review-upload.md) documents corrected status, expanded release tests, and preflight limitations.

## Next task

The supplied project changes add a roadmap toward an installable OS.
Follow [the OS implementation plan](os-implementation-plan.md) after the existing
feasibility and integration gates. A read-only Windows preflight is available at
`tools/Test-KavikaHost.ps1`; record reviewed target-machine evidence in
`docs/validation/m0.md`. Windows sign-in is unavailable on the Surface, so identify
it without login and use compatible live media for measurements. No Kavi'ka image
has been built; an upstream x86_64 Fedora candidate is verified but not selected.

Complete M0 in [the implementation plan](implementation-plan.md), tracked in [issue #1](https://github.com/kaavi-pixel/kavika-os/issues/1). First obtain the Surface's printed model number or a cropped photograph without serials; use [the Surface test plan](docs/surface-test-target.md). The external media and permission to erase it are already confirmed, so do not ask those questions again.

The VM architecture remains provisional, not more important than full Windows capability. If it blocks an important workload, compare alternatives with the user rather than silently excluding that workload or promising universal compatibility.

Test the touchpad rather than assuming touchscreen touch-point support implies a working four-finger gesture. Do not start packaging a custom distro, implementing GPU passthrough, or importing the existing physical Windows partition before the feasibility gate.

## Working rules

- Keep the original goal wording in `docs/original-features.md`; propose changes separately.
- Keep plan, implementation, and measured test results clearly distinguished.
- Use GitHub Issues for current state; link acceptance evidence before marking milestones complete.
- Keep the repository private unless the user explicitly requests otherwise.
- Decide a project licence with the user before public distribution.
