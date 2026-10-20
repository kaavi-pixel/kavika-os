# Kavi'ka: Windows 11 Setup boot via a GPT/ESP image (20 October 2026)

Feasibility result for the Windows side of the product, recorded on the Surface Laptop Studio.
Disposable guest only: no physical disk, no shared host folder, user-mode NAT.

## Problem (D14)

The Windows 11 ISO does not UEFI-boot from its own El Torito entry in OVMF: `BdsDxe: failed to start
"UEFI QEMU DVD-ROM QM00005 " ... : Time out`, then the firmware falls through to PXE and stops.
Fedora/Kavi'ka ISOs boot because they are **isohybrid** (MBR `55AA`, partition type `0xEE`) and OVMF mounts
their own EFI System Partition; this ISO has **no partition table** (`0000`) and depends entirely on El Torito.

## What was tested

| # | Configuration | Result |
|---|---|---|
| 1 | ISO as `-cdrom`, boot order `d` | `Time out`, falls through to PXE |
| 2 | ESP on USB storage whose `\EFI\BOOT\BOOTX64.EFI` = **bootmgfw.efi**, no `boot.wim` | OVMF **starts** it; Windows returns `0xc000000f` and the machine resets |
| 3 | ESP on USB storage whose `\EFI\BOOT\BOOTX64.EFI` = **cdboot.efi** | OVMF reports `failed to start ... : Time out` (same as the CD path) |
| 4 | ESP on USB storage, **bootmgfw.efi** + `\sources\boot.wim` on the ESP | **Windows 11 Setup reaches the "Select language settings" screen** |

The ISO itself is intact and was ruled out earlier: 9,061,271,552 bytes, ISO9660 volume space matches the file
size, valid El Torito catalog, EFI image at LBA 555 is a valid FAT12 volume. Size, RAM and transport were each
ruled out separately (a Fedora ISO padded past 4 GiB still boots; 2 GiB guest RAM still times out).

## Key findings

1. **`cdboot.efi` is the `Time out`.** The El Torito EFI image is byte-identical to `\efi\microsoft\boot\efisys.bin`
   (sha256 `52f40745…`), and the `\EFI\Boot\BOOTX64.EFI` inside it is byte-identical to `cdboot.efi`
   (sha256 `7cd32d9c…`, 1,037,120 B). Loading that same file from the ESP reproduces the `Time out`, so the
   fault is in `cdboot.efi`, not in the firmware's El Torito read.
2. **The ISO's `\efi\boot\bootx64.efi` is `bootmgfw.efi`** (sha256 `4bb32c30…`, 3,087,400 B) — a different file
   from the one in the El Torito image.
3. **The setup BCD resolves `[boot]` to the ESP.** With `bootmgfw.efi` on the ESP but `boot.wim` only on the CD,
   boot fails with `0xc000000f` ("A required device isn't connected or can't be accessed"). Adding
   `\sources\boot.wim` to the ESP fixes it.

## Working recipe

ESP image (`espB.img`, sha256 `909f6a36e77e7e535f27978861539f9d3eecfe8cb7a224fa087f53b8382ba904`):

* 1 GiB GPT disk, one EFI System partition, type `C12A7328-F81F-11D2-BA4B-00A0C93EC93B`, start LBA 2048
* FAT32, populated from the ISO: `\EFI\` (with `\EFI\BOOT\BOOTX64.EFI` = bootmgfw.efi), `\boot\BCD`,
  `\boot\boot.sdi`, `\sources\boot.wim`

Guest command line (abridged; full argv in the run record):

```
qemu-system-x86_64 -machine q35,accel=kvm -cpu host -smp 4 -m 6144 \
  -drive if=pflash,format=raw,readonly=on,file=/usr/share/edk2/ovmf/OVMF_CODE.fd \
  -drive if=pflash,format=raw,file=efi-vars.fd \
  -drive file=windows11.qcow2,format=qcow2,if=none,id=nvme0 -device nvme,drive=nvme0,serial=KAVIKA0000000001 \
  -chardev socket,id=chrtpm,path=tpm/swtpm.sock -tpmdev emulator,id=tpm0,chardev=chrtpm -device tpm-tis,tpmdev=tpm0 \
  -device VGA -device qemu-xhci -device usb-tablet -device usb-kbd \
  -drive if=none,id=usbesp,format=raw,readonly=on,file=espB.img -device usb-storage,drive=usbesp \
  -cdrom Windows11_Client_x64_en-gb_26300_9457.iso -boot order=d -display none -no-reboot
```

## Evidence

Firmware serial trail (the CD still times out and is skipped):

```
BdsDxe: failed to start Boot0002 "UEFI QEMU DVD-ROM QM00005 " ... : Time out
BdsDxe: failed to load  Boot0003 "UEFI QEMU NVMe Ctrl KAVIKA0000000001 1" ... : Not Found
BdsDxe: loading Boot0004 "UEFI QEMU QEMU USB HARDDRIVE 1-0000:00:04.0-3" from PciRoot(0x0)/Pci(0x4,0x0)/USB(0x2,0x0)
BdsDxe: starting Boot0004 "UEFI QEMU QEMU USB HARDDRIVE 1-0000:00:04.0-3" from PciRoot(0x0)/Pci(0x4,0x0)/USB(0x2,0x0)
```

Screen samples at 60 s, 150 s and 240 s are byte-identical and show the Windows 11 Setup language page
("Select language settings", Language/Time-and-currency both "English (United Kingdom)", Back/Next). The VM
remained running (monitor reported `VM status: running`) — it no longer resets.

## Unattended answer file (D16)

Observed 20 October 2026: with `autounattend.xml` on the ESP's own root, and again on a second USB stick
attached beside the ESP, Setup still stopped at "Select language settings" instead of advancing unattended —
the answer file was never read.

Cause: QEMU's `usb-storage` device presents its media as a **fixed** disk by default. The `removable`
property defaults to `off` (`qemu-system-x86_64 -device usb-storage,help` → `removable=<bool> - on/off
(default: off)`), so the RMB bit is clear and both sticks report as fixed hard disks. Windows Setup's
implicit unattend search order covers removable media but not a fixed disk at those positions, so neither
copy was found.

Fix under test: attach the answer-file stick with `-device usb-storage,drive=afstick,removable=on` so it is
presented as removable media. Result pending; the relaunched guest run is in progress and is not yet evidence.

## Limits

* Setup has **reached its first page only**. No product key, no disk selection, no installation has run.
* It is **not** established that WinPE can read `install.wim` (8,158,846,937 B) from the CD.
* No Windows licence or activation is handled. No physical disk was touched.
* Whether Setup finds and acts on the unattended answer file on **removable** media (D16) is not yet confirmed.
