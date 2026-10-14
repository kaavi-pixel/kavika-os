# Kavi'ka OS: implementation plan

Version 0.2 | 14 October 2026 | Proposed roadmap.

Build a reversible integration prototype before packaging a custom distribution. This plan does not authorise installation, disk changes, or Windows licence purchases, and none of the milestones below has been completed.

## Architecture decision

Use Linux as the host, KDE Plasma on Wayland as the candidate desktop, and QEMU/KVM with libvirt for a Windows 11 guest. Start with a supported Fedora KDE release as the candidate test environment, but pin the exact distribution, kernel, Plasma, QEMU, libvirt, viewer, guest build, and driver versions only after M0 validation.

Use a full-screen `virt-viewer`/SPICE console as the first display candidate. SPICE documents guest agents, clipboard integration, dynamic sizing, and audio, but its general manual is not evidence that every feature works on the selected Windows 11 driver stack; treat those as explicit tests ([SPICE user manual](https://www.spice-space.org/spice-user-manual.html)).

If the console cannot meet responsiveness/display gates, evaluate FreeRDP as an alternative on the private VM network. Built-in Windows RDP hosting requires a supported edition such as Pro, Enterprise, or Education; Windows Home cannot host it ([Microsoft Learn](https://learn.microsoft.com/en-us/windows-server/remote/remote-desktop-services/remotepc/remote-desktop-allow-access)). Do not patch Home to bypass that restriction or assume the existing laptop licence covers a guest.

Keep the SPICE console for installation and recovery even if RDP wins the interactive test. A backend change must rerun focus, audio, scaling, reconnect, security, and session-continuity tests; do not assume console and RDP sessions behave identically.

### Component boundaries

| Component | Proposed responsibility | Boundary |
|---|---|---|
| `kavika-session` | Start/observe the VM, manage viewer lifecycle, show states, prevent duplicate launches | Python 3 controller using libvirt APIs; runs as the desktop user. No root GUI or credentials in command arguments. |
| Desktop integration | Place the viewer on the Windows workspace, expose toggle/escape actions, preserve focus | KWin window rules and a minimal JS/QML script only where the tested desktop APIs support it. Native gestures first; no generic global key-injection daemon. |
| Guest definition | CPU, RAM, firmware, disk, network, virtual devices | libvirt-managed QEMU/KVM. First create manually; automate only the known-good definition. |
| Viewer adapter | Attach, resize, reconnect, release input | SPICE first; optional RDP behind the same narrow controller interface. |
| Shared folder | A single host-owned directory mapped in Windows | Authenticated Samba share on the private VM interface; deny LAN access and access outside the approved directory. |
| Setup and checks | Explain prerequisites, apply opt-in config, preserve backups, validate removal | Shell for small checks; no destructive disk installer in the MVP. |

The controller should use libvirt state events plus bounded retries, not blind sleeps or screen scraping. Invoke subprocesses with argument arrays and allowlisted VM identifiers, not shell-interpolated user input.

## Hardware envelope

The supplied screenshot reports Ryzen 7 8840HS/Radeon 780M, 16 GB installed RAM, and 954 GB storage. The image does not establish the complete GPU inventory, available virtualisation settings, Linux device support, Windows edition, or free space available after a safe Linux setup.

Proposed first benchmark profile:

- **Guest CPU:** 4 vCPUs; adjust after measuring concurrent host/guest use, not by dedicating all host resources.
- **Guest memory:** fixed 6 GiB initially; account separately for QEMU, the host, filesystem cache, and integrated graphics. Test 8 GiB only if measured host headroom supports it.
- **Guest storage:** a 128 GiB maximum sparse qcow2 disk on a backed-up filesystem; monitor actual host free space. Sparse capacity is not reserved free space.
- **Guest firmware/security:** UEFI with appropriately enrolled Secure Boot keys and an emulated TPM 2.0; verify inside Windows, not just in XML.
- **Guest display:** virtual display, no passthrough, conservative starting resolution of 1920 × 1080 if supported, followed by native panel/DPI tests.
- **Networking:** private libvirt NAT network with outbound guest connectivity; explicitly restrict host services to the required guest interface/subnet. NAT alone is not a host-service firewall.

Microsoft lists VM requirements including at least 4 GB RAM, 64 GB storage, two virtual processors, Secure Boot capability, and virtual TPM; these are installation minima, not a promise of good performance ([Windows 11 requirements](https://learn.microsoft.com/en-gb/windows/whats-new/windows-11-requirements)). Libvirt documents UEFI, Secure Boot-capable firmware, memory/vCPU configuration, and an emulated TPM backend using `swtpm`; capability flags alone do not prove Secure Boot is enabled in the guest ([libvirt domain format](https://libvirt.org/formatdomain.html)).

## Milestones and dependencies

```text
M0: feasibility and permissions
 └── M1: manually validated guest and display
      ├── M2: swipe, toggle, focus, escape
      └── M3: shared folder and permissions
           M2 + M3
              └── M4: lifecycle, recovery, security
                   └── M5: packaging, regression, pilot
```

M2 and M3 can proceed independently after M1. Do not assign calendar dates until the setup route, available hardware access, and must-have applications are known.

### M0: feasibility and safety gate

Tasks:

- Obtain the must-have application list, Windows edition/licensing decision, backup/recovery readiness, and approval for a reversible Linux test route.
- Check real GPU inventory, firmware virtualisation availability, `/dev/kvm`, storage headroom, and the target release's device support.
- Verify touchpad four-finger input separately from touchscreen support; check Wi-Fi, keyboard, audio, display brightness, touch/pen, and suspend.
- Record VM-off CPU/RAM/battery baseline and exact software versions. Do not publish hardware identifiers, recovery keys, or raw private logs.

Exit: documented pass/fail evidence and explicit permission for the next device-changing step. If the hardware route is unsuitable, compare a Windows-host/Linux-guest fallback separately with the user; do not quietly replace the Linux-first goal.

### M1: guest and display proof of concept

Tasks:

- Provision a fresh guest on the approved test environment using user-supplied legitimate installation media and licensing.
- Validate UEFI, Secure Boot, TPM, storage/network drivers, and guest shutdown using supported signed packages.
- Benchmark SPICE and the chosen Windows display driver with typing, scrolling, window movement, browser use, and a short video/audio sample.
- Evaluate RDP only if the edition permits it and SPICE does not meet the agreed quality bar. Record dropped features and security configuration.
- Verify the 6 GiB profile under a 30-minute mixed workload; stop if the host becomes unstable.

Exit: one documented backend passes a usable desktop workflow with no passthrough. If neither backend passes, stop at feasibility; do not call the MVP working.

### M2: desktop switching and input

Tasks:

- Configure exactly two named desktops in one row and define swipe direction, wrapping policy, and visible transition.
- Restrict the VM viewer window to the Windows desktop and prevent duplicate windows.
- Implement a configurable toggle, initially proposing `Meta+F12` after a conflict check, plus a separate host escape action.
- Verify four-finger switching with the full-screen viewer focused, guest full-screen applications, different keyboard layouts, and held modifiers.
- Prefer native compositor gestures. If custom KWin support is required, verify the actual API before implementation; do not promise a script can override a hardcoded gesture.

Exit: F02/F03 and the switch/focus metrics pass. A shortcut-only result is a useful prototype, but not a completed four-finger MVP.

### M3: file sharing

Tasks:

- Create `~/Kavika/Shared` with user-only host permissions and an explicit Windows mapping named `Kavika Shared`.
- Configure an authenticated SMB share limited to this directory and private VM network; prohibit guest/anonymous access, SMB1, wide links, and escape through symlinks.
- Store credentials in the OS credential store or enter them interactively, never in Git, shell history, command-line arguments, or diagnostics.
- Test read/write access in both directions, Unicode filenames, overwrites, permission failures, network interruption, and insufficient disk space.
- Explain that this is one shared working directory, not a backup or automatic synchronisation of both home folders. Do not edit the same file concurrently during the MVP tests.

Exit: F04/F07 and all file-integrity fixtures pass; access from an unapproved LAN device is denied. Keep clipboard, drive redirection, and drag-and-drop off so they cannot bypass this boundary.

### M4: lifecycle, recovery, security

Tasks:

- Implement observable states: `off`, `starting`, `running`, `reconnecting`, `stopping`, and `error`; saved-state support is deferred.
- Distinguish VM state from viewer state: a disconnected viewer does not mean Windows is off.
- Add single-instance protection, startup timeout, safe reconnect, and non-destructive failure messages.
- Try a 120-second provisional startup timeout and 60-second graceful-shutdown timeout; on expiry offer retry/cancel or explicit force-off confirmation, never automatic destruction.
- Preserve the guest on viewer close; request guest shutdown before host shutdown and do not forcibly terminate unsaved work without confirmation.
- Test host suspend/resume, lock/unlock, guest reboot/update, network loss, viewer crash, and disk-space exhaustion with expendable test data.
- Use local SPICE sockets where feasible, scope libvirt/polkit privileges, validate any RDP certificate, retain NLA, and expose no remote-console ports to the public network.

Exit: recovery tests pass, no unresolved data-loss/input-trap/security blocker, and diagnostic logs contain no secrets or file contents.

### M5: reproducible setup and pilot

Tasks:

- Package only the configuration and small integration components already proven in M1–M4.
- Make setup idempotent and preserve previous KWin/desktop settings. Require confirmation for privileged changes.
- Provide an uninstall path that restores settings without deleting the shared folder, guest disk, or user-owned credentials automatically.
- Record the exact tested dependency versions, known limitations, app compatibility matrix, and upgrade/rollback procedure.
- Back up guest disk, UEFI NVRAM, and TPM state consistently with the guest shut down; test restoration. Keep recovery keys outside this repository.
- Run the full tracker checklist and a real user pilot before tagging `v0.1.0`.

Exit: another clean supported test installation reproduces the approved experience, all P0 requirements pass, and the user accepts remaining limitations. A distributable OS image is a later decision, not this milestone's output.

## Test strategy

- **Unit tests:** controller state transitions, duplicate-start protection, timeouts, validation, log redaction, and backend selection using a fake libvirt adapter.
- **Integration tests:** guest start/stop, viewer reconnect, share permissions, and repeatable setup/uninstall in a disposable VM environment.
- **Hardware tests:** actual touchpad gestures, captured-input escape, HiDPI, audio, suspend, battery, and the target apps on the laptop.
- **Regression evidence:** attach sanitised versions, reproduction steps, timing samples, and pass/fail results to the relevant issue. A planning checkbox is not evidence of a passed test.

## Definition of done

The first release is a tested Linux/Windows workspace integration, not merely a working Windows VM. Do not release until four-finger switching, the escape path, file integrity, reversible setup, and the user-approved application workflows pass on the documented target configuration.
