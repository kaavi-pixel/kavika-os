# Kavi'ka OS: Surface live-preview guide

Version 0.1.0 | Private diagnostic preview | Guide updated 19 October 2026

**Two machines:** the Surface Laptop Studio (Fedora, KVM-capable) is the first test machine and the Surface Pro 8 is the final target. Test in a disposable VM on the Laptop Studio first ([steps](surface-laptop-studio-test-machine.md)), then boot from external media. Laptop Studio results are evidence for the Pro 8, never proof.

This is a draft guide for the first Linux hardware test, not the finished Linux/Windows OS. **Do not flash at this checkpoint:** the latest rebuilt image has not been booted yet, and its predecessor failed the Meta+F12 workspace test. Follow the [handoff](../handoff.md) before resuming, then read the matching [validation record](validation/live-preview-0.1.0.md); an image being built is not proof that its desktop or your Surface works.

## What is in it

- **Base:** pinned Fedora KDE 44 x86_64 with its stock kernel and desktop.
- **Branding:** the original Kavi'ka logo, unchanged, used as a fitted wallpaper.
- **Test Centre:** guide, filtered hardware inventory, report saving and workspace demonstration.
- **Navigation prototype:** two Linux desktops, “Linux” and “Windows (not installed),” with `Meta+F12` intended to toggle them. Meta is the Windows-logo key on most PC keyboards.
- **Installation guard:** normal live installer entry points are hidden/disabled. Underlying upstream installer packages remain; do not bypass the guard or run Anaconda manually.

No Windows guest, Comet, cross-OS shared folder, VM lifecycle, persistence or installed-system update path is included. The second desktop is not Windows, and the live image does not meet the full product requirements.

## Prepare on the HP Envy

Use the approved empty 512 GB external SSD only. Keep the Surface's internal SSD in the Surface, unplug other external storage, and never choose the HP's internal drive.

1. Download the ISO and its matching `.iso.sha256` file from the supplied deliverables. Do not rename a ZIP to `.iso` or simply copy the ISO onto the SSD as a normal file.
2. In PowerShell, from the download folder, verify the file using the command below. Its SHA-256 must exactly match the 64-character value in the supplied checksum file; stop on any mismatch.
3. Obtain Fedora Media Writer using the official [Fedora KDE download page](https://fedoraproject.org/kde/download). Select its custom/local-image workflow and choose the Kavi'ka ISO.
4. Select the external SSD by its model, connection and roughly 512 GB marketed capacity. Review the destructive-write warning and destination carefully. If you cannot distinguish it from an internal disk, cancel and ask for help using a cropped disk-list screenshot without serials.
5. Write the image, let verification finish, then safely eject the SSD. This erases the external SSD; it should not write to either laptop's internal drive.

```powershell
Get-FileHash -Algorithm SHA256 .\Kavika-OS-0.1.0-Surface-Pro-8-Live-Preview.iso
```

The media is a raw live-image layout, not a general 512 GB data volume. Do not accept a Windows prompt to format the newly written Linux partitions. Live home-directory files disappear at shutdown; unused SSD capacity is not automatically a persistent save area.

## Boot the Surface

Connect power and have the USB keyboard/mouse ready. Start with the SSD attached and avoid unrelated storage.

Microsoft's Surface USB-boot sequence is: shut down, connect the boot medium, hold Volume Down, press/release Power, and release Volume Down when spinning dots appear ([Microsoft USB boot instructions](https://support.microsoft.com/en-us/surface/drivers-firmware/boot-surface-from-a-usb-device)). Use the available hub/ports for keyboard and mouse once boot is underway; if a hub prevents boot, try the SSD directly first.

Choose the Kavi'ka live-preview entry and wait for the desktop. If the firmware reports a security violation, a locked boot policy or management restriction, stop and record the message without identifiers; do not disable Secure Boot, clear the TPM or enrol keys as a guess.

The preview preserves the upstream signed boot components but its complete Secure Boot path has not been validated on your Surface. The linux-surface compatibility table lists Pro 8 native keyboard/touchpad/touch/pen with a custom-kernel requirement, so this stock-kernel preview relies on your external input for its first test ([linux-surface device matrix](https://github.com/linux-surface/linux-surface/wiki/Supported-Devices-and-Features)).

## First-session checklist

- **Desktop:** report whether the desktop and Kavi'ka Test Centre appear; photograph a failure screen if necessary without serials or private data.
- **External input:** test typing, pointer movement and clicks.
- **Hardware inventory:** open Test Centre → View hardware report. Record CPU model, memory, actual internal SSD capacity, GPU and KVM status; the 128 GB factory marking is not a live measurement.
- **Navigation:** try Windows-logo key + F12 both directions. The destination must clearly remain “Windows (not installed).” Do not treat this as a Windows compatibility test.
- **Devices:** try Wi-Fi with credentials entered only on the Surface, display brightness and audio. Report native Type Cover/touch/pen separately from USB input; failures here do not mean USB input failed.
- **Shutdown:** use the desktop's normal shutdown, remove the SSD after power-off, then start the Surface. Its previous Windows installation should remain unchanged, including its existing password requirement.

Do not mount the old Windows volumes or inspect their files. Do not install packages or save important work in the temporary session; collect only expendable test data.

## Report results

The report intentionally excludes disk serials, UUIDs, MAC/IP addresses, usernames, keys and user files. It does contain hardware model/capacity and capability information; review before sharing.

If networking works, upload a reviewed report from the live session before shutdown. Alternatively photograph only the relevant displayed fields. Do not save it onto the old Windows partitions just to retain it; a future persistent data area needs a separate storage-layout decision.

Send these first results:

```text
Booted to desktop: yes/no
Test Centre appeared: yes/no
USB keyboard/mouse: pass/fail
CPU:
Reported RAM:
Internal disk model/capacity (no serial):
KVM device exists / accessible:
Wi-Fi:
Meta+F12 switches both ways:
Other errors:
```

## What follows

Actual memory/storage determine whether this Surface can comfortably run Linux plus full Windows and Comet. Do not reuse the old HP allocation or assume 1 TB; a 128 GiB Windows disk is not a safe default for a device marked 128 GB.

Next work is native Surface input/kernel validation, measured Windows feasibility and an installer tested on disposable disks. Your permission to erase the Surface and external SSD is preserved; it does not replace those validation steps or authorise changing the HP disk or firmware security.
