# Kavi'ka OS: hand-off

This repository contains the product specification, prototype and OS roadmaps, and a preliminary Windows diagnostic script. There is no runnable desktop integration or bootable OS, and no hardware acceptance gate has passed.

## Current state

- **User goal:** preserve Linux and Windows workspaces, switch with a four-finger swipe or keybind, and transfer files easily.
- **Approved logo:** `assets/branding/kavi-ka-os-logo.png`, supplied and selected by the user on 15 October 2026. Keep the original artwork unchanged unless a new variant is requested.
- **Explicit clarification:** Windows should have “everything,” including Comet. Preserve a full general-purpose Windows installation, not a stripped-down desktop, Wine substitute, or allowlisted app collection; Comet is now a P0 requirement (F15/T16).
- **Target observations:** HP Envy x360 14-fa0xxx, Ryzen 7 8840HS/Radeon 780M, 16 GB RAM, and about 954 GB storage from the supplied screenshot.
- **Recommended direction:** Linux/KDE host with a real Windows VM and a dedicated shared folder; validate the display backend before building the integration.
- **Not user-approved decisions:** exact distro/version, guest Windows edition, software stack, memory allocation, additional test coverage, and laptop installation route. A test matrix must never restrict what the user may install.
- **Safety boundary:** this planning request does not authorise repartitioning, firmware changes, OS replacement, or VM provisioning on the laptop.
- **Imported additions:** `os-implementation-plan.md`, `tools/Test-KavikaHost.ps1`, and `docs/validation/m0.md`; the script is preserved unchanged from the supplied archive.
- **Evidence status:** Windows 11 Home Single Language and capacity/virtualisation values are archive-reported, not reproduced in this review. Guest edition/licensing and Linux device/KVM checks remain unresolved.
- **Review record:** [archive review](docs/review-upload.md) documents corrected status, expanded release tests, and preflight limitations.

## Next task

The supplied project changes add a roadmap toward an installable OS.
Follow [the OS implementation plan](os-implementation-plan.md) after the existing
feasibility and integration gates. A read-only Windows preflight is available at
`tools/Test-KavikaHost.ps1`; record reviewed target-machine evidence in
`docs/validation/m0.md`. Repository development is distinct from laptop disk
changes or VM provisioning; those need separate approval. No OS image has been built.

Complete M0 in [the implementation plan](implementation-plan.md), tracked in [issue #1](https://github.com/kaavi-pixel/kavika-os/issues/1). Full Windows and Comet are already required; ask only for additional representative workloads, the Windows edition/licensing route, and whether a backed-up external SSD or another reversible test environment is available.

The VM architecture remains provisional, not more important than full Windows capability. If it blocks an important workload, compare alternatives with the user rather than silently excluding that workload or promising universal compatibility.

Test the touchpad rather than assuming touchscreen touch-point support implies a working four-finger gesture. Do not start packaging a custom distro, implementing GPU passthrough, or importing the existing physical Windows partition before the feasibility gate.

## Working rules

- Keep the original goal wording in `docs/original-features.md`; propose changes separately.
- Keep plan, implementation, and measured test results clearly distinguished.
- Use GitHub Issues for current state; link acceptance evidence before marking milestones complete.
- Keep the repository private unless the user explicitly requests otherwise.
- Decide a project licence with the user before public distribution.
