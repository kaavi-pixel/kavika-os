# Kavi'ka OS: hand-off

This repository captures the concept and a proposed technical path. It contains no runnable OS implementation and no passing hardware tests.

## Current state

- **User goal:** preserve Linux and Windows workspaces, switch with a four-finger swipe or keybind, and transfer files easily.
- **Target observations:** HP Envy x360 14-fa0xxx, Ryzen 7 8840HS/Radeon 780M, 16 GB RAM, and about 954 GB storage from the supplied screenshot.
- **Recommended direction:** Linux/KDE host with a real Windows VM and a dedicated shared folder; validate the display backend before building the integration.
- **Not user-approved decisions:** exact distro/version, guest Windows edition, software stack, memory allocation, application support list, and laptop installation route.
- **Safety boundary:** this planning request does not authorise repartitioning, firmware changes, OS replacement, or VM provisioning on the laptop.

## Next task

Complete M0 in [the implementation plan](implementation-plan.md). Ask for the must-have Windows applications, Windows edition/licensing route, and whether a backed-up external SSD or another reversible test environment is available.

Test the touchpad rather than assuming touchscreen touch-point support implies a working four-finger gesture. Do not start packaging a custom distro, implementing GPU passthrough, or importing the existing physical Windows partition before the feasibility gate.

## Working rules

- Keep the original goal wording in `docs/original-features.md`; propose changes separately.
- Keep plan, implementation, and measured test results clearly distinguished.
- Use GitHub Issues for current state; link acceptance evidence before marking milestones complete.
- Keep the repository private unless the user explicitly requests otherwise.
- Decide a project licence with the user before public distribution.
