# Kavi'ka OS: Surface live-preview guide

Version 0.1.0 | Private diagnostic preview | Guide updated 21 October 2026

**The machines:** the **HP Envy x360 (1 TB)** is the install target; the **Surface Laptop Studio** (Fedora, KVM-capable) is the test machine; the **Surface Pro 8 is dropped**. This guide covers booting the preview on a Surface; to boot and evaluate it on the Envy, use [testinstall.md](../testinstall.md). Test in a disposable VM on the Laptop Studio first ([steps](surface-laptop-studio-test-machine.md)), then boot from external media. Laptop Studio results are evidence, never proof for the AMD Envy.

**Do not flash this as an installation.** The rebuilt image (SHA-256 `bd8407d6…`) **has been booted** — in a KVM guest, from USB on the Laptop Studio, and live from USB on the Envy — and its Meta+F12 workspace switch works; but it is a diagnostic preview with no installer and no Windows guest. Follow the [handoff](../handoff.md) before resuming, then read the matching [validation record](validation/live-preview-0.1.0.md); an image being built is not proof that your target works.

## What is in it

- **Base:** pinned Fedora KDE 44 x86_64 with its stock kernel and desktop.
- **Identity:** the booted system presents itself as **Kavi'ka OS** in `os-release` (`ID=kavika`, `ID_LIKE=fedora`, `VERSION_ID=44` kept so `$releasever` still resolves). The volume label stays `Fedora-KDE-Live-44` because the live boot depends on it.
- **Branding:** the original Kavi'ka logo, unchanged, used as a fitted wallpaper.
- **Test Centre:** guide, filtered hardware inventory, report saving and workspace demonstration.
- **Navigation prototype:** two Linux desktops, “Linux” and “Windows (not installed),” with `Meta+F12` intended to toggle them. Meta is the Windows-logo key on most PC keyboards.
- **Windows workspace plumbing:** `kavika-windows-workspace` and the guest launcher (`/usr/local/lib/kavika/launch-windows-vm-linux.py`) now ship in the image, plus an in-image provisioning guide at `/usr/share/kavika/WINDOWS.txt`. The guest itself needs an installed system with the virtualization stack; this live preview carries no Windows.
- **Installation guard:** normal live installer entry points are hidden/disabled. Underlying upstream installer packages remain; do not bypass the guard or run Anaconda manually.

No Windows guest, browser, cross-OS shared folder, VM lifecycle, persistence or installed-system update path is included. The second desktop is not Windows, and the live image does not meet the full product requirements.

## Prepare the media

Use a normal USB flash drive (a 4 GB stick is enough). Keep any laptop's internal drive out of the write — never choose an internal device, and on Windows hosts use the **HP Envy** only as a helper, choosing the external stick explicitly.

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

## Testing an image in a disposable VM first

Before any physical media, boot the ISO on a KVM-capable Linux host — the Surface Laptop Studio fills that role. `tools/launch-preview-vm-linux.py` refuses an image whose SHA-256 does not match the supplied value or sidecar, and attaches only a new private QCOW2 disk and user-mode networking: no physical disk and no shared folder.

For evidence rather than assumption, `tools/capture-vm-evidence.py` wraps that launcher and adds a QEMU monitor socket, so the desktop can be captured and keystrokes injected:

```sh
python3 tools/capture-vm-evidence.py boot --iso <iso> --sha256-file <sidecar> --vm-dir ~/kavika-vm-test
python3 tools/capture-vm-evidence.py shot --vm-dir ~/kavika-vm-test before.ppm
python3 tools/capture-vm-evidence.py key  --vm-dir ~/kavika-vm-test meta_l-f12
python3 tools/capture-vm-evidence.py shot --vm-dir ~/kavika-vm-test after.ppm
python3 tools/capture-vm-evidence.py quit --vm-dir ~/kavika-vm-test
```

Notes that cost time to rediscover:

- Boot is headless by default because the GTK window has been observed to show black while the guest drew correctly. `screendump` is the reliable view.
- The monitor key name is **`meta_l-f12`**; `meta-f12` is rejected and the frame does not change, which looks identical to a broken shortcut.
- Compare frames numerically (for example `compare -metric AE before.ppm after.ppm null:`). A workspace switch changes roughly a third of the frame; on the tested build, switch was ~361,200 pixels and the return trip matched the original to within ~110 pixels (the clock).
- A running QEMU process is not a boot pass. Check the screenshots, `serial.log` and the guest's own answers (`getenforce`, `systemctl is-system-running`, `systemctl --list-units --state=failed`) before recording anything.

## Writing the image to a USB stick (Linux host)

Writing a live image is a raw, destructive write, so the agent will not perform it: raw block-device writes are blocked outright. Use the guarded writer, which refuses anything that is not a removable USB whole disk, that carries the running system, that is mounted, or that is too small — and which verifies the image hash before the write and the device contents after it:

```sh
sudo bash tools/write-preview-to-usb.sh \
    --iso build/Kavika-OS-0.1.0-Surface-Pro-8-Live-Preview.iso \
    --sha256-file build/Kavika-OS-0.1.0-Surface-Pro-8-Live-Preview.iso.sha256 \
    --device /dev/sdX --confirm-wipe /dev/sdX
```

`--dry-run` runs every check and prints the plan without writing; do that first and confirm the device size, model, label and transport are the stick you mean. The image is a hybrid layout, so the volume label stays the preserved upstream one (`Fedora-KDE-Live-44`) rather than anything saying "Kavika". The stick boots the same image that was validated in the VM; it is a preview, not an installer.

## What follows

Actual memory/storage determine whether a machine can comfortably run Linux plus full Windows and the user's browser. On the **HP Envy (16 GB host RAM, 1 TB)** a full Windows guest is far more comfortable than the dropped Pro 8 route would have been, but the guest sizing is **not decided** and must be measured, not assumed. Next work is measured Windows feasibility on the installed OS, an installer tested on disposable disks, and the [Envy readiness gate](envy-transfer.md). No permission is on record to erase the Envy's disk, and no firmware-security change is authorised.
