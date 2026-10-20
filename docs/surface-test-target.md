# Kavi'ka OS: target machines

Updated 20 October 2026 | The HP Envy x360 with 1 TB storage is now the intended **final install target**. The Surface Laptop Studio is the **test machine**. The Surface Pro 8's status is awaiting confirmation.

## Target change, 20 October 2026

On 20 October 2026 the user stated: *"this should be the test, the real thing that should be the final result is the hp envy with 1tb storage"* — that is, the Laptop Studio is the test bed and the finished Kavi'ka OS should end up on the **HP Envy x360 (1 TB)**.

What this changes:

| Item | Before | Now |
|---|---|---|
| Final install target | Surface Pro 8 Wi-Fi (model 1983) | **HP Envy x360, 1 TB (user-reported)** |
| Test machine | Surface Laptop Studio | Surface Laptop Studio (unchanged, now actively in use) |
| Surface Pro 8 | Final install target | **Awaiting confirmation: dropped, or a later goal?** |
| Surface-specific kernel work | On the critical path (Type Cover, touch, pen) | **Off the target's critical path** — an Envy is a normal laptop with ordinary input |
| Guest sizing pressure | Severe: Pro 8 recorded as 128 GB | Relaxed: 1 TB of storage and 16 GiB of RAM to work with |

**What this does NOT authorise.** The previously recorded approvals were for the Surface Pro 8's internal disk and for erasing an empty 512 GB external SSD. They do **not** transfer to the HP Envy. The Envy currently runs Windows and is the project's build/emulation helper; **no write, repartition or erasure of its internal 1 TB disk is approved, and none has occurred.** Identify the exact physical disk and obtain a fresh explicit go/no-go immediately before any write, as the rules below require.

Also note the platform change this implies: the Envy is an **AMD Ryzen 7 8840HS with Radeon 780M graphics**, not Intel Tiger Lake. Kernel, graphics and KVM specifics measured on the Tiger Lake Surfaces do not carry over, and virtualisation on the Envy is AMD-V (`svm`), not `vmx`. Its CPU, RAM and storage numbers below are carried forward from earlier records and should be re-measured rather than trusted.

**Machines at a glance**

| Machine | Role | State |
|---|---|---|
| **HP Envy x360 (Ryzen 7 8840HS, 16 GB, 1 TB)** | **Intended final install target**, pending confirmation of scope and approvals | Windows host today; project build/emulation helper; specs carried from earlier records and not re-measured. Its internal disk is **not** in any erase approval |
| Surface Laptop Studio (Core i5-11300H, 16 GiB, 256 GB NVMe, Iris Xe) | Test machine, runs Fedora 44 | Preflight done (KVM usable); KVM guest boot passed; **physical USB boot passed 20 October 2026** — Meta+F12 repeated reliably, pointer, speakers, microphone, camera, Wi-Fi, battery and thermals fine; **touchscreen does not work on the stock kernel**; no pen available to test. See [its page](surface-laptop-studio-test-machine.md) |
| Surface Pro 8 Wi-Fi (model 1983) | Previously the final install target; **status awaiting confirmation** | Never booted with Kavi'ka; CPU, RAM and disk unmeasured |

Results from the Laptop Studio are evidence only. It has a different CPU family from the Envy, a different form factor and different input hardware.

The immediate deliverable is still a private live diagnostic preview, not an installation on any machine. The first preview deliberately does not install anywhere.

## Target and permissions

| Item | State |
|---|---|
| Printed model | 1983, Surface Pro 8 Wi-Fi ([Microsoft service guide](https://learn.microsoft.com/en-us/surface/service-guides/surface-pro8/surface-pro8-device-information-and-service-parts)) |
| Architecture family | Intel/x86_64; exact CPU/RAM configuration unmeasured ([Microsoft specifications](https://support.microsoft.com/en-us/surface/models/surface-pro-8-features-and-specs)) |
| Factory storage marking | 128 GB, user-reported; supersedes earlier 1 TB estimate |
| Actual internal SSD | Capacity/model/path still unmeasured; factory marking is not proof of an unchanged drive |
| Current OS | Windows 11, user-reported; account password unavailable |
| Internal installation intent | **Recalculating after the target change:** complete replacement of the *Surface Pro 8's* Windows was authorised earlier, but the intended final target is now the HP Envy. No replacement is approved on any machine's internal disk. Confirm scope before acting |
| External medium | Empty 512 GB SSD; erasure for installation media was authorised for the Pro 8 route. The 4 GB USB stick already written with the preview was an approved media step |
| External input | USB keyboard and mouse plus necessary connection hardware available |
| Helper computer | The HP Envy builds the ISO, ran early emulated tests and is now the intended final install target. Its internal 1 TB disk currently holds Windows and **must not be written** without a fresh explicit go/no-go |
| Test machine | Surface Laptop Studio running Fedora; its internal disk and firmware settings are **not** in any erase approval |
| Windows workspace | Full Windows including Comet remains required; absent from the preview |
| Firmware, Secure Boot, Linux/KVM | Physical test pending; no firmware-security changes authorised |

Do not ask again for general erase permission. Before any write, match the actual physical disk by role, model, capacity, connection and target path; never choose only by a drive letter, “Disk 0” or assumed `/dev/nvme0n1`. No user drive has been written by this build process.

The user's device serial is deliberately excluded from the repository and diagnostic schema. Do not upload old Windows files, activation/recovery keys, firmware identifiers or unreviewed logs.

## First test route

The Laptop Studio has KVM-capable hardware, so run the VM test there first (see [the Laptop Studio page](surface-laptop-studio-test-machine.md)). The steps below describe the Pro 8 live-media route, which comes only after the VM and Laptop Studio checks pass.

1. Finish the disposable UEFI VM check documented in [preview evidence](validation/live-preview-0.1.0.md).
2. Verify the delivered ISO checksum on the HP, then write the image only to the identified empty external SSD.
3. Leave the Surface's internal SSD installed. Boot the external medium and use the USB keyboard/mouse for the first test.
4. Open Kavi'ka Test Centre. Check display/input and collect the privacy-filtered hardware report; inspect actual RAM, CPU, disks and KVM.
5. Test networking, audio, brightness and shutdown using disposable data. Keep internal Windows partitions unmounted; do not use the preview to install.
6. Decide whether the measured memory/storage supports full Windows and Comet. Implement and validate native Surface input, an installer and the Windows workspace before the authorised internal replacement.

The 512 GB external medium is ample for the approximately 3.37 GB image; it does not limit a later internal installation to its own capacity. The Surface's actual internal capacity is the constraint. Do not use a 128 GiB guest-disk default on the basis of a 128 GB factory marking.

Windows 11's documented VM storage minimum is 64 GB, before allocating Linux and practical update/free-space headroom ([Microsoft requirements](https://learn.microsoft.com/en-gb/windows/whats-new/windows-11-requirements)). That makes measured storage planning essential, not optional. Reusing the external SSD for permanent guest storage would be a separate layout decision, not part of the current media plan.

## Surface-specific input and firmware

The linux-surface matrix lists Pro 8 Type Cover/touchpad, touch and pen with the custom-kernel footnote, and camera support is not established as working ([linux-surface matrix](https://github.com/linux-surface/linux-surface/wiki/Supported-Devices-and-Features)). This preview deliberately uses the stock Fedora kernel, so external inputs are the supported first-test route; native gestures are not promised.

After shutting down, Microsoft's USB-boot procedure is to insert the boot medium, hold Volume Down, press and release Power, then release Volume Down when spinning dots appear ([Microsoft USB boot](https://support.microsoft.com/en-us/surface/drivers-firmware/boot-surface-from-a-usb-device)). If boot is blocked by firmware management, a password or a security error, record the non-sensitive message and stop; do not disable security, reset the TPM or enrol keys blindly.

The linux-surface installation guide describes a separate kernel and Secure Boot enrollment workflow, which is future work rather than an automatic preview action ([linux-surface setup](https://github.com/linux-surface/linux-surface/wiki/Installation-and-Setup)). Changing host firmware settings requires explicit scope approval.

## Why not move the internal SSD into the HP?

Microsoft provides a Surface Pro 8 removable-SSD service procedure, but removable does not mean the HP has a compatible spare slot or that a transplanted installation has been validated ([Microsoft SSD guidance](https://learn.microsoft.com/en-us/surface/surface-ssd-removal-guide)). The USB route avoids opening either computer and keeps the HP's internal drive out of the installation path.

Direct testing, and later installation, while the SSD remains in the Surface is preferred. There is no installer-capacity problem to solve by transplanting it.

## Build boundary

The diagnostic preview pins Fedora KDE 44 `44-1.7.x86_64`, preserves the upstream kernel/base filesystem and adds an original-logo live overlay. Its build provenance and test results are in [the validation record](validation/live-preview-0.1.0.md); end-user instructions are in [the preview guide](live-preview.md).

It contains no Windows guest or Comet and does not implement cross-OS switching, shared folders or persistent installation. Successful VM boot would not pass Surface hardware, Windows or installer gates.
