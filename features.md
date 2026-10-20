# Kavi'ka OS: features v2

Version 0.9 | 20 October 2026 | Product specification; Surface Pro 8 final target, Surface Laptop Studio Fedora test machine with the read-only preflight complete (KVM usable), diagnostic live preview built.

Work resumed on 19 October 2026. The previous diagnostic image reached a working KDE desktop in a disposable VM but its Meta+F12 workspace switch failed (line-ending defect, fixed in source and rebuilt, not yet re-tested). See [handoff.md](handoff.md) before treating any image as ready for a Surface.

This expands the supplied brief into testable requirements without replacing its original goals. Technical choices and numerical targets below are proposals, not measured results or additional user commitments.

## Problem statement

The user wants to move between a Linux environment and a real Windows environment as easily as changing virtual desktops. Switching should preserve work and make file movement simple, rather than requiring a reboot for every change.

The original brief describes the intended experience:

> Desktop 2 in windows is a seamless way to switch between 2 desktops with a 4 finger swipe. This is what I want for Kavi'ka OS. Simple switch, and easy file transfer between the two.

> High speed and light the way Linux is, but compatible with most programs through windows.

These statements remain the product goals. “Light” and “most programs” are aspirations to validate, not compatibility or performance guarantees.

### User clarification: full Windows, including Comet

> windows should have everything, like comet. remember, everything.

The Windows workspace must be a full, general-purpose Windows installation, not a curated app launcher, stripped-down image, browser-only environment, or Wine substitute. Preserve the normal desktop, Start menu, File Explorer, Settings, Windows Update, security components, and app installation paths available in the selected Windows edition, including Microsoft Store where supplied.

The user must be able to install and use applications of their choice, with Comet explicitly required. A compatibility test list is evidence coverage, never an allowlist limiting what may be installed; “everything” does not mean every program is preinstalled or that the current laptop's files and apps have already been migrated.

Full Windows functionality is the product requirement; universal VM compatibility is not an established technical fact. If an important workload fails because of the proposed VM architecture, investigate an architecture change and discuss the trade-off rather than silently narrowing the requirement.

## Goals

- **Natural switching:** a four-finger horizontal touchpad swipe or configurable shortcut moves between Linux and Windows, without restarting either environment.
- **Continuity:** applications remain open when their workspace is hidden; returning does not relaunch them.
- **Simple file access:** one explicitly shared folder is accessible from both environments with matching file contents.
- **Responsive Linux:** Linux remains usable with Windows active under an agreed, measured workload.
- **Full Windows capability:** preserve normal Windows features and user-chosen app installation, with Comet required; maintain a growing test matrix without imposing an app allowlist.

### First physical target

The final install target is Surface Pro 8 Wi-Fi, identified by the user's model 1983 marking ([Microsoft service guide](https://learn.microsoft.com/en-us/surface/service-guides/surface-pro8/surface-pro8-device-information-and-service-parts)). The user reports Windows 11 and a 128 GB factory marking, replacing the earlier 1 TB estimate; actual installed capacity remains unmeasured. The user authorises replacing its Windows installation and erasing an empty 512 GB external SSD for media; precise disk identification remains mandatory before writing either disk.

The first test machine is the Surface Laptop Studio, which already runs Fedora and has KVM-capable Intel hardware ([test-machine page](docs/surface-laptop-studio-test-machine.md)). Its results are evidence for the Pro 8, never proof.

The Windows account password is unknown; signing in is not a prerequisite for the live-test route. The model family is Intel/x86_64, but exact CPU, RAM, installed GPU configuration and storage need live measurement ([Microsoft specifications](https://support.microsoft.com/en-us/surface/models/surface-pro-8-features-and-specs)). External USB keyboard and mouse are available; no resource or compatibility claims transfer from the HP.

The external medium does not limit the size of the installation on the Surface's internal drive. See [the Surface test target](docs/surface-test-target.md) for scope and the staged test route.

### What the first preview implements

The 0.1.0 live preview pins Fedora KDE 44 x86_64, adds the unchanged logo, Test Centre, a privacy-filtered hardware report and a `Meta+F12` two-desktop demonstration. The second desktop is labelled “Windows (not installed)”; both desktops are Linux. Implementation and runtime validation are tracked separately in [the preview evidence](docs/validation/live-preview-0.1.0.md).

Windows, Comet, a guest VM, cross-OS file sharing, four-finger acceptance, persistence and installation are not provided by this preview. Full Windows remains the requirement; diagnostic media is an earlier testing aid, not a scope reduction or completion of F01–F15/O01–O04.

Surface Pro 8 native Type Cover/touchpad, touch and pen are listed with a custom-kernel requirement by linux-surface, so the stock-kernel first preview uses the available external inputs ([linux-surface matrix](https://github.com/linux-surface/linux-surface/wiki/Supported-Devices-and-Features)). A custom-kernel/signing path requires separate implementation and testing; no automatic firmware changes are permitted.

## Non-goals

- **A new kernel:** the initial product is an integration layer on an existing Linux distribution.
- **Unverified blanket guarantees:** GPU-heavy programs, anti-cheat-dependent games, specialised drivers, DRM, and peripherals need validation. These categories are not automatically excluded from the user's goal; failures may require revisiting the architecture.
- **Zero overhead:** a hidden Windows VM still runs unless explicitly stopped or saved.
- **GPU passthrough in the laptop MVP:** no suitable additional GPU has been verified.
- **An unattended migration:** no disk conversion, repartitioning, OEM Windows-image reuse, activation bypass, or silent destructive setup.

## User stories

- **Daily use, P0:** as the laptop user, I want to swipe into Windows and back so that I can use both environments without interrupting my work.
- **Files, P0:** as the laptop user, I want an obvious shared folder so that I can move a document between environments without cloud uploads.
- **Recovery, P0:** as the laptop user, I want a reliable way back to Linux even if the Windows viewer disconnects or captures input.
- **Resource control, P0:** as the laptop user, I want an explicit Windows on/off state so that I can choose responsiveness over keeping Windows ready.
- **Convenience, P1:** as the laptop user, I want optional text copy/paste and remembered display sizing without sharing more data than intended.

## Requirements

### Must have: P0

| ID | Requirement | Acceptance criterion | Dependency |
|---|---|---|---|
| F01 | Full general-purpose Windows workspace; Linux host is the proposed implementation | Given a running guest, when either workspace is selected, then its applications remain available without a host reboot. Windows retains its desktop, Explorer, Settings, Update, security components, and edition-provided installation paths; no Kavi'ka app allowlist or stripped-down replacement is imposed. | M0, M1 |
| F02 | Exactly two named workspaces for the MVP | Given the validated desktop configuration, when a four-finger horizontal swipe completes, then the adjacent Linux or Windows workspace is selected once, including while the viewer is full-screen. Test both directions. | M2; actual touchpad validation |
| F03 | Host-owned toggle and escape | Given focus in the Windows viewer, including a captured-input state, when the configured toggle or separate escape action is used, then Linux receives control without terminating Windows. If the viewer cannot honour this, that backend fails the gate. | M2 |
| F04 | Dedicated shared folder | Given an authenticated share connection, when a file is created in `~/Kavika/Shared` or its Windows mapping, then the other side can open the completed file with identical SHA-256 content. Test both directions. | M3 |
| F05 | Explicit lifecycle | Given Windows is off, starting it shows a starting state; given it is running, switching workspaces does not stop it; given shutdown is requested, normal guest shutdown is attempted and progress is shown. A timeout must not force power-off. | M1, M4 |
| F06 | Fail-safe return to Linux | Given the viewer fails or the guest is unreachable, when the user switches back, then Linux remains usable and a reconnect action is offered without silently rebooting or recreating the guest. | M2, M4 |
| F07 | Scoped access | Given the shared folder is enabled, attempts to access unshared home-directory paths or expose its service to the LAN are denied. Clipboard and USB redirection are off until separately enabled. | M3, M4 |
| F08 | Reversible setup | Given a backed-up host configuration, when integration is removed, then prior desktop settings are restored and user files and guest disks are retained unless separately approved for deletion. | M5 |
| F15 | Comet works as a native Windows application | Given the selected Windows build and backend, when Comet is installed from its official distribution, then launch, user-driven sign-in, browsing, assistant interaction, downloads to the shared folder, available update flow, and retained tabs/session after workspace switching are tested successfully. Report failures explicitly; do not replace it with a different browser without approval. | M1, M2, M3, M5; user performs account sign-in |

### Should have: P1

- **F09, optional text clipboard:** given explicit opt-in, copying plain text works in both directions; after opt-out, it no longer crosses environments. Do not log clipboard contents.
- **F10, media and scaling:** given the validated display backend, guest audio playback, supported resolutions, and the tested scale factor remain usable after reconnect. Mic and camera access require separate consent.
- **F11, recovery polish:** given host suspend and resume, the viewer can reconnect to the same guest session without duplicate viewers or data loss.

### Could have: P2

- **F12, app routing:** optional Wine-based launching for individually tested applications.
- **F13, power profiles:** an opt-in save/shutdown policy when Windows is unused, with clear loss of instant return.
- **F14, other hardware:** multi-monitor support and a separately validated GPU-passthrough profile.

### Not in the first release

Universal drag-and-drop, automatic clipboard-file transfer, arbitrary gesture remapping, custom Windows branding, a bootable distro image, and guaranteed native gaming performance are outside the first release. A shared folder, not drag-and-drop, is the required file-transfer mechanism.

Scope update: the supplied project changes extend delivery to an installable OS.
The integration prototype is the first deliverable, not a finished OS. Live media
and an installable OS follow its validation under [the OS implementation plan](os-implementation-plan.md).

### Installable-OS delivery requirements

These are required for the later OS release, not reasons to skip the prototype gates. Preserve existing feature IDs; use O-prefixed IDs for distribution deliverables.

| ID | Requirement | Acceptance criterion | Dependency |
|---|---|---|---|
| O01 | Bootable Linux live image | Given an isolated builder and pinned inputs, when an ISO is built, then it boots in a disposable UEFI VM into KDE, exposes diagnostics and the installer, and contains no Windows media, guest disk, credentials, or user data. Booting live media performs no automatic installation. | OS3; T17/T18 |
| O02 | Explicit, safe installation and first boot | Given expendable test disks, when installation is requested, then the installer requires explicit target selection and confirmation, creates a working user desktop, and leaves non-selected test disks unchanged. First boot requires explicit opt-in before guest provisioning. | OS4; T19/T20 |
| O03 | Validated host security and hardware | Given the candidate image and separately approved test route, when live boot and installation are tested, then the intended host Secure Boot path and device suite pass, followed by the full Windows/Comet and switching suite. Host Secure Boot is tested separately from guest Secure Boot. | OS3–OS5; T21 and prototype tests |
| O04 | Maintainable, documented release | Given a candidate release, when another isolated build and an upgrade/recovery test are run, then the procedure is repeatable, versions/manifests/checksums are recorded, and rollback/recovery works. Licence, trademark, signing, and publication decisions must be resolved before distribution. Byte-identical reproducibility is a separate claim requiring evidence. | OS6; T22/T23 |

The diagnostic tools and live preview are preliminary implementations, not completion of F01–F15 or O01–O04. In particular, the preview intentionally lacks the installer required for O01's eventual release gate.

## Success metrics

All values are provisional acceptance targets. Record the baseline and raw test results in M0/M1; adjust any unrealistic target through a documented specification change rather than quietly declaring success.

| Metric | Proposed target | Measurement |
|---|---|---|
| Warm switch | At least 95 of 100 switches reach a usable target workspace within 500 ms after the gesture/shortcut is recognised | Measure 50 switches each direction with both environments already running; report p50/p95 and failures. Excludes cold boot and saved-state restore. |
| Focus correctness | 100 of 100 switch cycles route the next click and typed test string to the intended environment; zero stuck modifiers | Controlled dummy text only; test with full-screen guest apps as well as the desktop. |
| File correctness | All 20 fixture transfers in each direction match SHA-256; overwrite and interrupted-transfer cases have no silent corruption | Include Unicode names, spaces, empty files, and a 1 GiB file; use copies, not move/delete tests. |
| Responsiveness | No host/guest crash or OOM kill during a 30-minute agreed mixed workload | Record RAM, memory pressure, swap, CPU, temperatures where available, and Linux interaction delays versus VM-off baseline. |
| App compatibility | Full-Windows baseline and Comet workflows pass, alongside additional user-required workflows | Record exact app/version, display backend, scenario, and result. Additional test coverage is not an installation allowlist; unresolved failures trigger architecture review, not silent scope reduction. |
| Recovery | 10 viewer reconnects and 10 suspend/resume cycles preserve the test document and restore access | Save fixture edits before suspend; investigate unsaved-session continuity separately. |

## Open questions

| Question | Owner | Blocking |
|---|---|---|
| Which Windows edition and valid VM licensing route will be used? | User | Blocks guest provisioning and RDP selection, not documentation. |
| Which additional workloads should be tested first beyond the full Windows baseline and Comet? | User | Guides test coverage; does not restrict app installation. Comet is already required. |
| What are the actual Surface RAM, CPU and installed disk capacity/identity? | User / implementer | Model 1983/Pro 8 Wi-Fi and Intel/x86_64 family are established; live measurements still block guest sizing and destructive installation. Erase scope is already approved. |
| Does the actual touchpad expose reliable four-finger gestures under Linux? | Implementer | Blocks F02. Touchscreen “10 touch points” in the screenshot does not answer this. |
| Which supported Linux/KDE release and viewer build pass the hardware gates? | Implementer | Blocks a pinned installation guide. |
| Is optional clipboard sharing desired, and should Windows start at login? | User | Non-blocking; defaults are clipboard off and Windows started on demand. |

## Technical rationale

### Why Fedora KDE Plasma Desktop?

The proposed Linux base is Fedora KDE Plasma Desktop on Wayland. This is an initial architecture choice to validate, not a tested conclusion that it is the only or best distribution for the laptop.

- **Workspace controls fit the concept:** KDE provides named virtual desktops, switching animations, and rules that place particular application windows on a chosen desktop, giving us building blocks for a dedicated Windows workspace without writing a desktop environment from scratch ([KDE virtual desktops](https://docs.kde.org/stable_kf6/en/kwin/kcontrol/desktop/index.html), [KDE window behaviour](https://docs.kde.org/stable_kf6/en/kwin/kcontrol/windowbehaviour/index.html)).
- **The VM stack is documented:** Fedora documents QEMU/KVM, libvirt, virt-manager, and virt-viewer, matching the proposed Windows guest architecture ([Fedora virtualisation guide](https://docs.fedoraproject.org/en-US/quick-docs/virtualization-getting-started/)).
- **The desktop can become Kavi'ka's own interface:** Fedora KDE emphasises customisation and updated drivers and kernels; that makes it a reasonable starting point for our branding and integration, without proving compatibility or performance on this laptop ([Fedora KDE](https://fedoraproject.org/kde/)).

The maintenance trade-off is Fedora's approximately 13-month update period per release, which requires planned upgrades and regression testing rather than leaving one installation unchanged for years ([Fedora KDE](https://fedoraproject.org/kde/)). Fedora 44 is pinned for the diagnostic preview; a production dependency set still requires M0 validation and upgrade regression tests.

KDE's available controls do not establish that our exact full-screen viewer/gesture combination works. A KDE community report describes four-finger horizontal switching, but also limitations on remapping; verify the selected release and touchpad instead of treating that report as a universal API guarantee ([KDE discussion](https://discuss.kde.org/t/plasma-6-7-wayland-how-can-i-remap-three-finger-touchpad-gestures-independently-of-four-finger-gestures/48621)).

This choice does not guarantee that concurrent Linux and Windows use will feel lightweight, or that every Windows workload works. Full Windows, explicitly including Comet, remains the requirement; a failed VM approach must prompt architecture review rather than an app allowlist or silent scope reduction.

### Graphics and application validation

Looking Glass documents a requirement for two usable GPU devices, including some integrated/discrete or virtual-GPU combinations ([Looking Glass requirements](https://looking-glass.io/docs/B7/requirements/)). No such configuration has been verified on the Surface, so it remains deferred from the baseline.

Comet's published requirements include 64-bit Windows 10/11, 4 GB minimum RAM and 8 GB recommended; those OS requirements do not certify the proposed VM/display configuration ([Comet operating system requirements](https://www.perplexity.ai/help-center/comet/en/articles/11734730-operating-system-requirements)). Test it inside the guest with Linux concurrently active before claiming it works in Kavi'ka OS.
