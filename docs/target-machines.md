# Kavi'ka OS: target machines

Updated 20 October 2026 | The **HP Envy x360 with 1 TB storage is the only install target**. The Surface Laptop Studio is the **test machine**. The Surface Pro 8 has been **dropped** — it is not a target. (This file was previously `docs/surface-test-target.md`; the name changed with the target.)

## Decisions, 20 October 2026

The user was asked directly and answered:

| Question | Decision |
|---|---|
| The finished OS should end up on which machine? | **The HP Envy x360 (1 TB). No other install target.** |
| What happens to the Surface Pro 8? | **Dropped.** It is no longer a target. |
| How does the HP Envy get Kavi'ka? | **Prove it on the Laptop Studio first; only after it "works perfectly" replace Windows on the Envy.** |
| Replace the Envy's Windows or dual-boot it? | Replacement is the stated end state; nothing is written until the Laptop Studio passes and a fresh go-ahead is given. |
| Re-measure the Envy's specs? | **Not now — keep the recorded numbers** (Ryzen 7 8840HS, 16 GB, 1 TB). Treat them as inherited until measured. |

What this changes:

| Item | Before | Now |
|---|---|---|
| Final install target | Surface Pro 8 Wi-Fi (model 1983) | **HP Envy x360, 1 TB** |
| Test machine | Surface Laptop Studio | Surface Laptop Studio (unchanged, actively in use) |
| Surface Pro 8 | Final install target | **Dropped** — earlier intentions for it are withdrawn, not deferred |
| Surface-specific kernel work | On the critical path (Type Cover, touch, pen) | **Off the target's critical path** — the Envy is a normal laptop with ordinary input |
| Guest sizing pressure | Severe: Pro 8 recorded as 128 GB | Relaxed: 1 TB of storage and 16 GiB of RAM |

**What this does NOT authorise.** The HP Envy currently runs Windows and is the project's build/emulation helper. **No write, repartition or erasure of its internal 1 TB disk is approved, and none has occurred.** The earlier approvals covered the Surface Pro 8's internal disk and an empty 512 GB external SSD; with the Pro 8 dropped, the internal-disk approval is withdrawn rather than transferred. Identify the exact physical disk and obtain a fresh explicit go/no-go immediately before any write.

Also note the platform change this implies: the Envy is an **AMD Ryzen 7 8840HS with Radeon 780M graphics**, not Intel Tiger Lake. Kernel, graphics and KVM specifics measured on the Tiger Lake Surfaces do not carry over, and virtualisation on the Envy is AMD-V (`svm`), not `vmx`.

## Machines at a glance

| Machine | Role | State |
|---|---|---|
| **HP Envy x360 (Ryzen 7 8840HS, 16 GB, 1 TB)** | **The only install target.** Windows replacement is the end state, gated on the Laptop Studio passing and a fresh go-ahead | Windows host today; project build/emulation helper; specs inherited from earlier records, deliberately not re-measured yet. Its internal disk is **not** in any erase approval |
| Surface Laptop Studio (Core i5-11300H, 16 GiB, 256 GB NVMe, Iris Xe) | Test machine, runs Fedora 44 | Preflight done (KVM usable); KVM guest boot passed; **physical USB boot passed 20 October 2026** — Meta+F12 repeated reliably, pointer, speakers, microphone, camera, Wi-Fi, battery and thermals fine; **touchscreen does not work on the stock kernel**; no pen available to test. See [its page](surface-laptop-studio-test-machine.md) |
| Surface Pro 8 Wi-Fi (model 1983) | **Dropped** — not a target | Never booted with Kavi'ka. Earlier plans for it are withdrawn; its details are retained only as a record |

Results from the Laptop Studio are evidence about the image. They are **not** evidence about the Envy: different CPU vendor, different graphics, different everything that matters for the product.

The immediate deliverable is still a private live diagnostic preview. The preview deliberately does not install anywhere.

## Target and permissions

| Item | State |
|---|---|
| **Install target** | **HP Envy x360, 1 TB.** The only machine Kavi'ka is intended to replace Windows on. Windows replacement is the end state, gated on the Laptop Studio passing and a fresh explicit go-ahead |
| **Test machine** | Surface Laptop Studio running Fedora 44. Internal disk and firmware settings are **not** in any erase approval |
| Envy internal disk | Currently holds Windows and is the build/emulation helper. **Must not be written, repartitioned or erased** without a fresh explicit go/no-go. No approval is on record for it |
| Envy specifications | Inherited from earlier records: Ryzen 7 8840HS, 16 GB, Radeon 780M, 1 TB. Deliberately **not** re-measured yet; treat as unverified |
| Windows workspace | Full Windows including the user's browser (recorded as "Comet"; Firefox) is **verified working in a KVM feasibility guest** on the Laptop Studio — installed to the desktop and self-contained (D21). It is still **absent from the bootable preview image**, which ships no Windows |
| Media | A 4 GB USB stick already written with the preview (payload verified on the stick). No other medium is claimed |
| External input | USB keyboard and mouse plus connection hardware are available |
| Firmware, Secure Boot | No firmware-security changes are authorised on any machine. The Laptop Studio has Secure Boot disabled and its platform in Setup Mode; the Envy's state is unmeasured |
| Surface Pro 8 (dropped) | Model 1983 Wi-Fi, 128 GB factory marking, Windows 11, exact CPU/RAM/SSD never measured. **Dropped as a target**; its earlier approvals are withdrawn, not transferred. Retained only as a record |

Do not ask again for general erase permission on the Surface Pro 8 — that route is withdrawn. For the HP Envy: before any write, match the actual physical disk by role, model, capacity, connection and path; never choose by a drive letter, "Disk 0" or an assumed `/dev/nvme0n1`. No internal disk on any machine has been written by this build process.

The user's device serial is deliberately excluded from the repository and diagnostic schema. Do not upload old Windows files, activation/recovery keys, firmware identifiers or unreviewed logs.

## Test route

1. **Test on the Laptop Studio**, which has KVM-capable hardware and now runs the preview from USB. Done: preflight, KVM guest boot, and a physical USB boot with the workspace switch working repeatedly.
2. **Fill the product gaps while the test machine is the target:** the Windows guest works (`tools/launch-windows-vm-linux.py`) — a full Windows 11 installed to the desktop, now **self-contained** (D21), with the user's browser (Firefox, recorded as "Comet") opening (D24). Still outstanding: cross-OS switching by gesture, wiring the guest into the image, and file sharing between the two sides.
3. **Only when it works perfectly on the Laptop Studio**, prepare the HP Envy: identify its exact internal disk, back up anything that matters (including the BitLocker recovery key), and treat replacing its Windows as a separate destructive step needing a fresh explicit go/no-go. See [the Envy transfer and readiness notes](envy-transfer.md).
4. Then install on the Envy and validate there. Nothing measured on the Intel/Tiger Lake Laptop Studio should be assumed to hold on the AMD Envy.

Windows 11's documented minimums are 64 GB of storage and 4 GB of RAM before practical headroom ([Microsoft requirements](https://learn.microsoft.com/en-gb/windows/whats-new/windows-11-requirements)). The Envy's 1 TB and 16 GB make a full Windows guest far more comfortable than the dropped Pro 8 route would have been, but the guest sizing is not decided and must be measured, not assumed.

## Surface-specific input and firmware

This now affects only the **test bed**, not the product: with the Envy as the target, Surface-specific kernel work is off the critical path. It still matters for what the Laptop Studio can be used to test.

The linux-surface matrix lists Surface touchscreen and pen, and the Pro 8's Type Cover keyboard and touchpad, as needing its custom kernel ([linux-surface matrix](https://github.com/linux-surface/linux-surface/wiki/Supported-Devices-and-Features)). Consistent with that, the preview on the Laptop Studio **exposes no touchscreen or pen input device at all** under the stock kernel, and the physical boot confirmed the touchscreen does not respond. Native touch and pen therefore need a linux-surface kernel, and pen remains untested because no pen is available.

The linux-surface installation guide describes a separate kernel and Secure Boot enrollment workflow, which is future work rather than an automatic preview action ([linux-surface setup](https://github.com/linux-surface/linux-surface/wiki/Installation-and-Setup)). Changing host firmware settings requires explicit scope approval.

## The old SSD-transplant question

Previously recorded as "why not move the Pro 8's internal SSD into the HP?". It is now moot: the HP Envy *is* the target, so there is nothing to transplant. Retained only so the earlier reasoning is not mistaken for a live plan.

## Build boundary

The diagnostic preview pins Fedora KDE 44 `44-1.7.x86_64`, preserves the upstream kernel/base filesystem and adds an original-logo live overlay. Its build provenance and test results are in [the validation record](validation/live-preview-0.1.0.md); end-user instructions are in [the preview guide](live-preview.md).

It contains no Windows guest (the feasibility guest is separate and is not shipped) and does not implement cross-OS switching, shared folders or persistent installation. Successful VM boot would not pass target hardware, Windows or installer gates.
