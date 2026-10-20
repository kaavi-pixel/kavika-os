# Kavi'ka OS: bug tracker

Reviewed snapshot | 20 October 2026 | Diagnostic live preview built; read-only preflight run on the Surface Laptop Studio test machine; no full integration or installed-OS acceptance gate has passed.

The primary target is Surface Pro 8 Wi-Fi, model 1983, Intel/x86_64 family; sources and evidence are in [the target record](docs/surface-test-target.md). The user's 128 GB factory marking supersedes the earlier 1 TB estimate; actual capacity and RAM are unknown. External keyboard/mouse are available. Windows replacement and erasure of the empty 512 GB media are approved; exact disk identification and validation remain blockers, not general erase consent.

The archive reports a preliminary Windows preflight run, which this review did not reproduce. Live-preview-specific tests and any observed defects are recorded separately in [preview validation](docs/validation/live-preview-0.1.0.md); they must not be presented as full Windows or physical Surface acceptance.

## Live tracking policy

Use [GitHub Issues](https://github.com/kaavi-pixel/kavika-os/issues) as the source of truth for current status. This document defines triage and the initial validation checklist; update its date and counts whenever a snapshot is refreshed.

The checked GitHub tracker contains ten milestone tasks and five unverified risks, all open. OS0–OS2 reuse prototype issues #1–#6; OS3–OS6 are separately tracked in [#12](https://github.com/kaavi-pixel/kavika-os/issues/12), [#13](https://github.com/kaavi-pixel/kavika-os/issues/13), [#14](https://github.com/kaavi-pixel/kavika-os/issues/14), and [#15](https://github.com/kaavi-pixel/kavika-os/issues/15). Preview defects B01–B05/P01 below are checkpoint records linked from the live task, not newly created standalone GitHub issues. The user requested the source/docs update after the public-visibility notice; no ISO release or visibility change is included.

- **`type:task`:** implementation work or a milestone.
- **`type:risk`:** a possible limitation requiring validation; not a confirmed bug.
- **`bug`:** an observed defect with environment, expected/actual behaviour, and reproduction evidence.
- **Priority:** `priority:p0` blocks the MVP, `priority:p1` should follow soon, and `priority:p2` is optional.
- **Workflow:** `status:blocked`, `status:ready`, `status:in-progress`, `status:needs-verification`, then close only after evidence is attached. Apply exactly one open-status label.

A future failing risk test should produce a separate bug linked to the risk and its milestone. Do not relabel an untested concern as a confirmed defect, and do not count a completed task as a passed acceptance test without evidence.

## Severity and triage

| Severity | Definition | Required response |
|---|---|---|
| S0 | Data loss, credential exposure, unintended access outside the share, or destructive automation | Stop affected testing, preserve sanitised evidence, fix and verify before release. |
| S1 | Input trapped in the guest, host unusable, repeated crash, or core switching/file transfer broken | Blocks the MVP; document a recovery path before further user testing. |
| S2 | Degraded scaling/audio/reconnect or a workaround exists for a non-core feature | Schedule based on the affected requirement. |
| S3 | Cosmetic or documentation issue without functional impact | Fix opportunistically; do not confuse with compatibility risk. |

Severity describes impact; priority describes sequencing. A task can have P0 priority without being a severe bug.

## Initial risk register

| ID | Risk, not a confirmed bug | Priority | Validation / release response |
|---|---|---|---|
| [R01 / #7](https://github.com/kaavi-pixel/kavika-os/issues/7) | Four-finger gestures or the escape key may be intercepted by the full-screen viewer | P0 | Run F02/F03 and 100 switch cycles on actual hardware. Reject the backend or integration if Linux cannot reliably regain input. |
| [R02 / #8](https://github.com/kaavi-pixel/kavika-os/issues/8) | Unknown Surface RAM/actual storage or virtual-display performance may make concurrent Linux/Windows unsuitable | P0 | Measure CPU/RAM/storage; do not use the HP's 6 GiB RAM/128 GiB guest-disk proposal. Factory marking is 128 GB, not the earlier 1 TB estimate. Compare mixed workload with VM-off baseline; investigate alternatives rather than narrowing full Windows. |
| [R03 / #9](https://github.com/kaavi-pixel/kavika-os/issues/9) | Shared-folder configuration may leak private paths or expose SMB to the LAN | P0 | Test unauthenticated access, path/symlink escapes, firewall scope, and file integrity before enabling real files. |
| [R04 / #10](https://github.com/kaavi-pixel/kavika-os/issues/10) | Suspend, guest updates, or viewer crashes may break session continuity | P0 | Run disconnect and suspend/resume fixtures and preserve data. Never “recover” by silently resetting the VM. |
| [R05 / #11](https://github.com/kaavi-pixel/kavika-os/issues/11) | The VM may fail the full-Windows requirement, including Comet or another user-chosen application | P0 | Validate the normal Windows baseline and Comet first, then expand test coverage without an app allowlist. Investigate architecture changes for important failures rather than silently reducing scope. |

## Acceptance checklist

All boxes start unchecked. Tick only after linking a test record with exact versions and a date.

- [ ] T01: host device support, actual GPU inventory, and virtualisation checked.
- [ ] T02: Windows edition/licensing and safe test route confirmed.
- [ ] T03: guest UEFI/Secure Boot/TPM and clean start/shutdown validated.
- [ ] T04: four-finger switching works both directions with full-screen guest focus.
- [ ] T05: keyboard toggle and emergency escape work; no stuck modifiers.
- [ ] T06: 100 warm switch cycles meet latency and focus targets.
- [ ] T07: fixture files match SHA-256 in both directions.
- [ ] T08: overwrite, interruption, Unicode, permission, and low-space cases tested.
- [ ] T09: unshared paths and unauthorised network clients are blocked.
- [ ] T10: optional clipboard stays off until consent and stops sharing when disabled.
- [ ] T11: 30-minute mixed workload passes on the chosen memory profile.
- [ ] T12: viewer reconnect and host suspend/resume preserve the test session.
- [ ] T13: full Windows features and ordinary user-chosen app installation remain available; additional required workflows pass without an app allowlist.
- [ ] T14: setup is repeatable; uninstall restores host settings and preserves data.
- [ ] T15: consistent guest backup and restore include disk, NVRAM, and TPM state.
- [ ] T16: Comet native Windows install, launch, user-driven sign-in, browsing, assistant interaction, shared-folder download, available update flow, and tab/session retention across switches pass (F15).

### Installable-OS acceptance

These extend the prototype checklist; they do not replace or pass it.

- [ ] T17: isolated build records source revision, selected supported Fedora release, input/repository snapshots, tool versions, package manifest, reviewed logs, and ISO checksum (O01/OS3).
- [ ] T18: ISO live-boots into KDE in a disposable UEFI VM, exposes diagnostics/installer, performs no automatic installation, and contains no Windows payload, guest disk, credentials, or user data (O01/OS3).
- [ ] T19: installation requires explicit target confirmation, succeeds on a blank disposable disk, and leaves attached non-selected expendable disks unchanged; fixture hashes confirm this (O02/OS4).
- [ ] T20: first boot creates a usable desktop and requests explicit opt-in before Windows provisioning or sensitive share/redirection changes (O02/OS4).
- [ ] T21: intended host UEFI/Secure Boot chain and target-laptop live-device suite pass; guest security and full switching/Windows/Comet regression are separately verified (O03/OS3–OS5).
- [ ] T22: supported base upgrade and recovery/rollback preserve user/guest data; a second isolated build demonstrates procedural repeatability, with byte-identical reproducibility claimed only if measured (O04/OS6).
- [ ] T23: licence/trademark/redistribution decisions, third-party notices, signing/trust distribution, update ownership, known limitations, and publication approval are recorded (O04/OS6).
- [ ] T24: exact Surface model/architecture and resources are recorded; live input/storage/boot checks pass; the Surface internal drive and empty 512 GB media are identified independently of the HP internal drive before any write.

## Review findings and follow-up

| ID | Finding | Classification and state | Follow-up |
|---|---|---|---|
| D01 | README/tracker still said no implementation existed despite the new preflight script | Documentation inconsistency; corrected in this review | Keep diagnostic-tool progress distinct from desktop/OS completion. |
| D02 | OS1 gate incorrectly included F08, while OS2 omitted explicit T14/T15 | Gate mapping inconsistency; corrected | F08/T14/T15 belong to OS2/M5. |
| D03 | “Ran successfully in this workspace” lacked source-machine provenance | Evidence gap; unresolved, wording corrected | Identify source machine role and script hash; collect reviewed target-machine results before M0 acceptance. |
| S01 | Script key `installedMemoryGiB` describes `TotalPhysicalMemory`, not installed module totals | Static-review naming mismatch; code unchanged | Rename/document the field and test output before treating it as installed RAM. Worksheet now warns about the distinction. |
| S02 | All CIM queries share a generic failure handler | Static-review robustness concern; not a reproduced failure | Test failed/denied queries; consider partial results and sanitised per-check errors in later tool work. |
| R06 | Custom image composition, disk selection, signing, or upgrades may fail despite a working prototype | Unverified OS-release concern covered by tasks #12–#15, not a sixth live risk issue | Require O01–O04 and T17–T23; no physical-disk exposure during builder/installer tests. |
| D04 | Surface target was previously recorded as unidentified / approximately 1 TB | Corrected after user model and factory marking | Model 1983 / Pro 8 Wi-Fi; 128 GB factory marking, actual installed capacity unmeasured; no serial retained. |
| D05 | A second machine, a Fedora-running Surface Laptop Studio, was supplied | Recorded as a test machine, not an install target. Its i5-11300H/16 GiB figures are not the Pro 8's | Keep results separate; the Laptop Studio's disk and firmware are outside the erase approval. |
| R07 | Stock-kernel preview may lack native Surface input | Hardware validation pending under #14 | Use confirmed USB keyboard/mouse; native input/custom-kernel and Secure Boot paths require separate validation. **Preflight evidence 20 October 2026: no touchscreen or pen input device was detected on the stock kernel of the Laptop Studio; still a risk, not a confirmed defect, and the Pro 8's own Type Cover, touch and pen remain untested.** |
| D06 | The Laptop Studio's storage was recorded as unmeasured | Measured by the preflight on 20 October 2026 | 256 GB NVMe (`HFM256GD3GX013N`), 255,060,320,256 bytes; root and home share a 235 GB filesystem with 203 GB free. Recorded in the Laptop Studio page and README. |
| D07 | KVM readiness on the test machine was unknown | Measured 20 October 2026: **usable** | `vmx` present, `/dev/kvm` writable by the user, `kvm_intel` loaded, `qemu-system-x86_64`/`qemu-img`/`virsh`/`swtpm` and both OVMF files present. `virt-manager` missing and libvirt inactive, but the direct-QEMU launcher does not need them. Unblocks resume-plan step 2. |
| D08 | The Laptop Studio's firmware security state was unrecorded | Observed 20 October 2026 | Secure Boot **disabled** and the platform in **Setup Mode** (no enrolled platform keys). Not a failure and nothing was changed; this does not carry over to the Pro 8's T21 check. |
| D09 | Cameras, audio, Bluetooth and battery are enumerated but unverified | Inventory only | 4 video-capture devices, one HDA-Intel card, 1 Bluetooth controller, battery present at 72%. Enumeration is not functional evidence; no camera/audio/sleep test has run. |
| D10 | A 1 TB USB disk (`sda`, "One Touch w/PW") is attached to the Laptop Studio | Enumerated only; nothing read or written | Not the approved 512 GB media SSD. Identify every physical disk explicitly before any future write or media step. |
| D11 | The repo's test counts were not reproduced on the Laptop Studio | `pytest` is not installed there | Do not cite the earlier test results as verified on this machine; installing test tooling is a separate approved step. |

## Live-preview defects and packaging corrections

| ID | Observed result | Correction / verification |
|---|---|---|
| B01 | Upstream live KDE setup replaces the preview's workspace `kwinrc` | Corrected through `livesys-session-extra`; previous candidate verified two named desktops and toggle both ways. Final candidate regression remains. |
| B02 | First VM desktop showed an SELinux AVC alert; guest inspection later found `/`, `/etc`, `/usr` and overlay ancestors labelled `tmpfs_t` | Post-policy-load relabelling verified on the previous candidate: expected labels, enforcing SELinux and working console login. The earlier pre-pivot attempt was ineffective and removed. Final candidate regression remains. |
| B03 | GRUB reported syntax errors before showing the boot menu | Reproduced with `grub-script-check` on the unmodified upstream config: nested function declaration at line 6. Normalize to a top-level video function, preserve platform choices and require a parser pass; regression test added. Initial suspicion about the title apostrophe was not supported. |
| B04 | First desktop opened Fedora's installer-oriented Welcome Centre | Previous candidate opened Test Centre without that Welcome Centre after disabling its preview launcher; final candidate regression remains. |
| B05 | Wallpaper setup reported a missing D-Bus method during startup although it existed once Plasma finished loading | Object existence was not a sufficient readiness check. Retry the actual `plasma-apply-wallpaperimage --fill-mode preserveAspectFit` operation instead; bounded retry regression added. |
| B06 | Meta+F12 did nothing in the booted image: only one desktop existed | **Root cause found:** overlay files had CRLF endings, so `livesys-session-extra` created paths with a literal CR and the two-desktop `kwinrc` was never applied. Builder now normalizes every overlay text file and `.gitattributes` forces LF; regression tests added. Rebuilt ISO `57a851a7…` is **not yet booted**, so B06 stays open until the toggle is seen working. |
| P01 | Internal image manifest contained a Python test cache | Exclude `__pycache__`/bytecode during composition; check final manifest |

These records refer to disposable VM/internal-build observations, not Surface failures. They do not change the untested status of Windows, Comet, installer safety or four-finger input.

Work is paused at the user's request. Resume from [handoff.md](handoff.md); do not mark the newest image ready or close milestones based on the previous candidate's results. Resume-plan step 1 (the read-only preflight on the Laptop Studio) is complete as of 20 October 2026; the next action is the disposable KVM guest boot of the rebuilt ISO, which no result here has performed.

See [the archive review](docs/review-upload.md) for review scope and verification limits. The preflight tool was preserved unchanged; no runtime fix or test is claimed. The D06–D11 observations come from the read-only run filed at [docs/validation/preflight-surface-laptop-studio-2026-10-20.md](docs/validation/preflight-surface-laptop-studio-2026-10-20.md).

## Minimum defect record

Use the GitHub bug-report form. Include a concise title, affected requirement/test, host and guest software versions, hardware summary without identifiers, reproducible steps, expected/actual behaviour, frequency, impact, and a sanitised evidence attachment.

Never attach activation/recovery keys, passwords, cookies, full clipboard contents, the original hardware screenshot, or unreviewed diagnostic dumps. Confirm a fix on the affected build and rerun the relevant regression before closing.
