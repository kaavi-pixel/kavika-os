# Installing Windows 11 in a KVM guest on this host

The verified way to get a full Windows 11 desktop in a disposable guest here, and the
reason each non-obvious step exists. Every claim below was observed on the Surface Laptop
Studio on 20-21 October 2026; see
[the ESP evidence page](validation/windows-setup-esp-2026-10-20.md) for the raw record.

This is a **feasibility harness**, not the product. It does not ship Windows, does not
bundle a licence key, and does not restrict what you install inside the guest.

## Why the obvious thing does not work

Booting the Windows 11 ISO straight from `-cdrom` fails:

```
BdsDxe: failed to start "UEFI QEMU DVD-ROM QM00005" ... : Time out
>>Start PXE over IPv4.  PXE-E16: No valid offer received.
```

Microsoft ISOs are **UDF hybrids with no partition table**, so OVMF cannot mount an EFI
System Partition on them and depends entirely on El Torito. The EFI payload in that El
Torito image is **`cdboot.efi`**, and `cdboot.efi` hangs under OVMF. The ISO's own
`/efi/boot/bootx64.efi` is the real **`bootmgfw.efi`**, and that one boots.

So Setup is booted from an **ESP disk image attached as USB mass storage**, and reads its
sources from the ISO still attached as `-cdrom`.

## The boot medium

Two images. Neither is a physical disk; both are plain files.

### 1. Boot ESP (`esp.img`)

A 1 GiB GPT disk, one EFI System partition (type `C12A7328-F81F-11D2-BA4B-00A0C93EC93B`)
starting at LBA 2048, FAT32, volume label `KAVIKAESP`, holding:

| Path on the ESP | Where it comes from |
|---|---|
| `/efi/boot/bootx64.efi` | the ISO's `/efi/boot/bootx64.efi` (that is `bootmgfw.efi`, 3,087,400 bytes) |
| `/efi/microsoft/boot/` (whole tree: `BCD`, `boot.stl`, `cdboot.efi`, `cdboot_noprompt.efi`, `cipolicies/`, `efisys.bin`, `efisys_noprompt.bin`, `fonts/`, `memtest.efi`, `resources/`, `winsipolicy.p7b`) | the ISO's `/efi/microsoft/boot/` |
| `/boot/BCD` | 16,384 bytes |
| `/boot/boot.sdi` | 3,170,304 bytes |
| `/sources/boot.wim` | the ISO's `/sources/boot.wim`, 619,980,682 bytes |

`/sources/boot.wim` **must be on the same volume as `bootmgfw.efi`**. The setup BCD
resolves `[boot]` to the volume it was loaded from; without it, boot fails with
`0xc000000f` and the machine resets.

### 2. Answer stick (`af.img`)

A 64 MiB FAT volume, label `KAVIKAANSW`, with `autounattend.xml` at its root. The file is
tracked in the repo as [`image/windows/autounattend.xml`](../image/windows/autounattend.xml).

## The three things that will bite you

**1. The boot ESP must be writable.** Do **not** attach it `readonly=on`. After applying
the image, Setup services the boot files, and it targets the volume it booted from. A
read-only volume gives:

```
BFSVC: BfspCopyFile(... bootmgfw.efi -> ... HarddiskVolume1/EFI/Boot/bootx64.efi) failed!
  Last Error = 0x13          (60 attempts)
CUpdateBootCode::DoExecute: Error is fatal
Operation failed: Update Boot Code. Error: 0x80070013
```

`0x13` is `ERROR_WRITE_PROTECT`. The install aborts at the downlevel Finalize phase with
"Windows 11 installation has failed", the target disk's own ESP is left empty, and
`\Windows` is never populated.

**2. The answer stick must be REMOVABLE.** QEMU's `usb-storage` presents its media as a
**fixed** disk by default (`removable` defaults to `off`), and Windows Setup's implicit
unattend search does not scan fixed disks. Without `removable=on` the stick is invisible
and Setup stops at the language page.

**3. Windows 11 build 26300 refuses to install without a bypass.** Setup stops at "This PC
doesn't currently meet Windows 11 system requirements" (TPM 2.0, Secure Boot) even though
`swtpm --tpm2` is running, because the guest uses the non-Secure-Boot OVMF build. The
answer file carries a `RunSynchronous` block in its `windowsPE` pass that sets the
`LabConfig` values `BypassTPMCheck`, `BypassSecureBootCheck`, `BypassRAMCheck`,
`BypassCPUCheck`, `BypassStorageCheck` and `BypassDiskCheck`. This is the Rufus 4.6+
method and it runs before the compatibility check.

## The command

```bash
python3 tools/launch-windows-vm-linux.py \
  --iso /path/to/Windows11.iso \
  --vm-dir ~/kavika-win11-install \
  --esp-image  /path/to/esp.img \
  --answer-image /path/to/af.img \
  --allow-reboot
```

`--allow-reboot` matters: the launcher otherwise adds `-no-reboot`, which turns Setup's
own reboots into a QEMU exit and kills the install partway.

`--expected-sha256` pins the ISO. The guest gets a new private QCOW2, its own UEFI
variables and its own TPM state, with no physical disk and no shared folder.

## What success looks like

1. Setup passes the compatibility check and shows "Installing Windows 11" with a
   percentage.
2. It reboots, and the serial log shows a new firmware entry:
   `starting Boot000B "Windows Boot Manager" ... bootmgfw.efi`.
3. Post-reboot it shows "Getting things ready for you", then the OOBE, then the desktop
   with the `autounattend.xml` local account signed in.

The install takes roughly 15 to 25 minutes on this host.

## Known limitation

The boot files land on the **USB ESP**, not on the target disk's own ESP, because Setup
services boot files to the volume it booted from. Windows boots and runs, but the guest
currently depends on that attached ESP. In a normal libvirt install the ESP lives on the
target disk and this does not arise; closing that gap means either adding `bcdboot` to the
flow or giving the Windows ISO a real partition table so it can be booted directly.

## Reading the logs when it fails

`setuperr.log` and `setupact.log` sit at `$Windows.~BT/Sources/Panther/` on the Windows
partition. With the guest stopped they can be read without root:

```bash
qemu-img convert -O raw -S 4k windows11.qcow2 win11.raw   # needs the guest stopped
fdisk -l win11.raw                                       # note the partition start, in MiB
dd if=win11.raw of=ntfs.img bs=1M skip=<start> count=<size> conv=sparse
ntfsls -a -l -p '/$Windows.~BT/Sources/Panther' ntfs.img
ntfscat ntfs.img '/$Windows.~BT/Sources/Panther/setuperr.log' | tail -40
```

`ntfscat` has no offset flag, so the partition has to be extracted first. If
`ntfsls -p '/Windows'` prints only `.`, the OS was never applied.
