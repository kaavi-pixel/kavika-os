# Kavi'ka OS: spare Surface test target

Updated 15 October 2026 | Target identification pending.

The immediate goal is a private test build for the user's spare Surface Pro, not a general-purpose release or an installation on the HP Envy. The user says the Surface runs Windows 11, has approximately 1 TB of internal storage, and contains nothing important to preserve.

## Confirmed choices and remaining unknowns

| Item | State |
|---|---|
| Primary test computer | Old Surface Pro; exact model/generation unknown |
| Current OS | Windows 11, user-reported; account password unknown |
| Internal storage | Approximately 1 TB, user-reported; actual disk identity unverified |
| Installation intent | User explicitly requests complete Windows replacement with Kavi'ka |
| External media | Empty 512 GB external SSD; user explicitly permits erasing it for installation media |
| HP Envy | Helper computer only; its internal drive must remain untouched |
| Surface CPU architecture, CPU, RAM, GPU | Unknown; do not inherit the HP Envy's specifications |
| Surface firmware/USB-boot access | Not tested; a firmware password or management restriction, if present, is a separate issue |
| Windows workspace | Still required as full Windows including Comet; new guest installation/media/licensing remain separate from erasing the old host Windows |

Preserve the permission already given: do not repeatedly ask whether Windows or the empty media may be erased. Before a destructive operation, identify the connected physical disk by role, model, capacity, and the actual target path; never select solely by “Disk 0,” drive letter, or an assumed `/dev/nvme0n1`.

No disk has been erased or written. Permission applies only to the identified spare Surface's internal drive and the empty 512 GB external SSD, not the HP Envy's internal storage, other attached drives, firmware security changes, or public distribution.

## Installation route

Recommended sequence:

1. Identify the exact Surface model and architecture without signing in.
2. Prepare a model-appropriate test image and document what works versus what is still missing.
3. On the HP Envy, write installation media only to the identified empty external SSD. This erases that external SSD, not the Surface's 1 TB disk or the HP's disk.
4. Boot the Surface from the external media and test the live environment before installation.
5. Confirm display, keyboard/Type Cover or alternate input, networking, internal-storage detection, and firmware boot support; collect CPU/RAM/GPU/KVM information from the live environment.
6. Once the image's installer and disk targeting are validated, replace Windows on the identified Surface internal drive, as requested.
7. Reboot from the internal drive without external media, then test updates/recovery and the Windows-workspace integration as it becomes available.

The 512 GB medium carries the installer; it does not cap the installed system at 512 GB. The intended installed system uses the Surface's own approximately 1 TB drive, with some space allocated to system partitions and files.

```text
HP Envy                     Empty 512 GB external SSD
prepare media only  ───────> bootable installer/live environment
                                      │
                                      ▼
                             Spare Surface Pro
                             boot and test first
                                      │
                                      ▼
                             Its own ~1 TB drive
                             replace existing Windows
```

No complete disk clone from the 512 GB SSD is proposed. Do not remove the Surface's internal storage merely to avoid a nonexistent installer-capacity limit.

## Identify it without the Windows password

Microsoft says Surface markings can include model and storage information alongside the serial, and directs Surface Pro owners to the area under the kickstand ([Microsoft device markings](https://support.microsoft.com/en-us/surface/service-repair/find-the-serial-number-for-your-surface-device-and-accessories-or-microsoft-accessories)). Ask for the printed model/model number or a cropped photo of that marking; cover the serial number and other identifiers.

For current Surface UEFI access, Microsoft instructs users to shut down, wait about 10 seconds, hold Volume Up, press and release Power, and keep holding Volume Up until the UEFI screen appears ([Microsoft Surface UEFI](https://support.microsoft.com/en-us/surface/drivers-firmware/how-to-use-surface-uefi)). Microsoft's older Surface Pro 3-and-earlier guide instead says to release Volume Up when the Surface logo appears ([older Surface firmware guide](https://support.microsoft.com/en-us/surface/drivers-firmware/how-do-i-use-the-bios-uefi-on-surface-pro-3-and-earlier-devices)).

Viewing firmware is for identification only; do not change Secure Boot keys, TPM settings, boot security, or firmware passwords. If firmware access itself is password-protected or organisation-managed, stop and use the legitimate owner/support route; this plan does not bypass that protection.

Windows account recovery is not a prerequisite for the proposed clean-install workflow. Do not attempt account-password recovery or inspect old user files simply to obtain a hardware model.

## Internal SSD transplant proposal

Treat removal and preparation through the HP as an alternative requiring model-specific evaluation, not the default route. Microsoft lists removable-SSD service procedures for specific Surface models, including Pro 7+, Pro 8, Pro 9, and Pro X; that does not establish that an unidentified older Surface has safely removable storage ([Microsoft SSD removal guidance](https://learn.microsoft.com/en-us/surface/surface-ssd-removal-guide)).

If removal is later selected, first verify the exact service guide, SSD form factor/interface, and compatible enclosure or adapter. Do not assume the HP has a suitable spare slot; do not install with the HP's internal drive exposed as a possible target, and do not assume bootloader configuration prepared on the HP will automatically work on the Surface.

Direct installation while the drive remains in the Surface is the preferred path. The proposed transplant provides no capacity advantage for this workflow.

## Build status and release boundary

An upstream Fedora KDE 44 x86_64 live ISO has been downloaded in the sandbox. Its checksum-file signature and the ISO's SHA-256 were verified; it is still unmodified Fedora, not a Kavi'ka OS build or evidence of Surface compatibility.

| Candidate input | Value |
|---|---|
| Filename | `Fedora-KDE-Desktop-Live-44-1.7.x86_64.iso` |
| SHA-256 | `c8295961d4c41adbf785a31a17c21a971d3b7415fda72dcad0c11c49577bf03a` |
| Status | Verified upstream candidate; target architecture not yet established |

Fedora's download page supplies this x86_64 image and verification instructions ([Fedora KDE download](https://fedoraproject.org/kde/download)). Do not flash or customise it as a Surface-specific release until the device architecture and boot path are identified; discard the candidate if unsuitable.

An early private boot/diagnostic preview may precede completion of the Windows integration to help test the Surface. Label it explicitly as a preview, state whether it contains an installer, and do not mark M0–M5 or OS3–OS6 complete merely because it boots.

No Kavi'ka ISO, functional Windows workspace, or Surface hardware pass exists yet. Full Windows/Comet and four-finger switching remain the goal, not features to claim in an initial diagnostic preview.
