# Kavi'ka OS: Surface test targets

Updated 19 October 2026 | Two Surface machines. The Surface Pro 8 is the final install target; the Surface Laptop Studio is the Fedora test machine. Physical testing is pending on both.

**Machines at a glance**

| Machine | Role | State |
|---|---|---|
| Surface Pro 8 Wi-Fi (model 1983) | Final install target | Never booted with Kavi'ka; CPU, RAM and disk unmeasured |
| Surface Laptop Studio (Core i5-11300H, 16 GiB, Iris Xe) | Test machine, already runs Fedora 44 | Hardware identified; nothing run on it yet. See [its page](surface-laptop-studio-test-machine.md) |

Results from the Laptop Studio are evidence only. It has a different CPU model, a different form factor and different input hardware.

The immediate deliverable is a private live diagnostic preview, not an installation on the HP Envy. Windows replacement is authorised for the Pro 8; the first preview deliberately does not install on either Surface.

## Target and permissions

| Item | State |
|---|---|
| Printed model | 1983, Surface Pro 8 Wi-Fi ([Microsoft service guide](https://learn.microsoft.com/en-us/surface/service-guides/surface-pro8/surface-pro8-device-information-and-service-parts)) |
| Architecture family | Intel/x86_64; exact CPU/RAM configuration unmeasured ([Microsoft specifications](https://support.microsoft.com/en-us/surface/models/surface-pro-8-features-and-specs)) |
| Factory storage marking | 128 GB, user-reported; supersedes earlier 1 TB estimate |
| Actual internal SSD | Capacity/model/path still unmeasured; factory marking is not proof of an unchanged drive |
| Current OS | Windows 11, user-reported; account password unavailable |
| Internal installation intent | Complete replacement of the Surface's Windows is explicitly authorised |
| External medium | Empty 512 GB SSD; erasure for installation media explicitly authorised |
| External input | USB keyboard and mouse plus necessary connection hardware available |
| Helper computer | HP Envy builds the ISO and runs only slow emulated tests; its internal disk must remain untouched |
| Test machine | Surface Laptop Studio running Fedora; its internal disk and firmware settings are **not** in the erase approval |
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
