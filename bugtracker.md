# Kavi'ka OS: bug tracker

Initial snapshot | 14 October 2026 | No implementation or hardware testing has occurred.

**Confirmed bugs: none recorded.** This means there is no tested implementation yet, not that the proposed system is bug-free. The entries below are unverified risks and planned tests, not invented defect reports.

## Live tracking policy

Use [GitHub Issues](https://github.com/kaavi-pixel/kavika-os/issues) as the source of truth for current status. This document defines triage and the initial validation checklist; update its date and counts whenever a snapshot is refreshed.

The initial live tracker contains six milestone tasks and five unverified risks, all open. No issues have been filed as confirmed bugs; each task or risk includes its dependencies and acceptance or validation criteria.

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
| [R02 / #8](https://github.com/kaavi-pixel/kavika-os/issues/8) | Windows virtual-display performance or memory pressure may make the 16 GB setup unsuitable | P0 | Compare 6 GiB guest mixed workload against VM-off baseline; test candidate display backends. Stop or narrow scope if it fails. |
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

## Minimum defect record

Use the GitHub bug-report form. Include a concise title, affected requirement/test, host and guest software versions, hardware summary without identifiers, reproducible steps, expected/actual behaviour, frequency, impact, and a sanitised evidence attachment.

Never attach activation/recovery keys, passwords, cookies, full clipboard contents, the original hardware screenshot, or unreviewed diagnostic dumps. Confirm a fix on the affected build and rerun the relevant regression before closing.
