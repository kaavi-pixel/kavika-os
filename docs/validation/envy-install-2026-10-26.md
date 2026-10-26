# Install to the Envy's NVMe from the dev host, 26 October 2026

**Outcome: the install completed and the disk is now Kavi'ka — but the ISO used predates the
D44/D45 fixes, so the disk is expected to land in emergency mode on the Envy. Reinstalling from
a fixed ISO is the corrective step.**

## What was done

The Envy's own NVMe (Samsung `MZVL81T0HELB-00BH1`, serial `S79UNX0XA54624`, 953.9 GiB) was
attached to the dev host over USB and the physical disk was passed into a QEMU guest as an
emulated NVMe device. This is the "install from the dev host" workaround for a machine whose
firmware offers the USB stick but falls through to Windows when it is selected.

- Media: `~/envy-install/install-to-nvme0n1.iso`, SHA-256 `12ccf347…`, 5,036,703,744 bytes,
  manifest `test_target: /dev/nvme0n1`, `compact: false`, `build_time_utc 2026-10-26T01:42:17Z`
  (09:42 local).
- Runner: `~/envy-install/run-install.sh`, which resolves the target by model and serial,
  refuses a partition or this host's own system disk, refuses when the target carries the
  installation media, refuses while anything on the target is mounted, and then boots the ISO
  in QEMU with the disk attached as NVMe and `-no-reboot`.
- The run started 11:16 and the console log ends `reboot: Restarting system` (2215 s), so the
  install finished rather than failing part-way.

## What the disk looks like afterwards

`lsblk -o NAME,SIZE,TYPE,FSTYPE,LABEL,PARTTYPENAME /dev/sda`:

| Partition | Size | Type |
|---|---|---|
| sda1 | 1G | EFI System |
| sda2 | 2G | Linux filesystem |
| sda3 | 128G | Linux filesystem |
| sda4 | 20G | Linux filesystem |
| sda5 | 802.9G | Linux filesystem |

That is the product layout: ESP, `/boot`, the 128 GiB Windows-guest volume, `/home`, and `/`
grown. **No NTFS, BitLocker or recovery partition remains** — the Windows install that was on
this disk is gone, as the runbook warned it would be. This also closes the question of reusing
the Envy's existing Windows as the Windows workspace: it is no longer on the disk. The three
routes in [windows-reuse-existing-install.md](../windows-reuse-existing-install.md) were never
executed, and this installer has no dual-boot mode; it wipes the whole disk.

## Why it is expected to fail on the Envy

The ISO that ran was built at 09:42, before the D44/D45 fix landed at 12:31. Read back out of
the ISO's kickstart:

| Fix | In the ISO that installed | In the source |
|---|---|---|
| `dracut-config-generic` (generic initramfs, D44) | absent | present |
| ESP UUID reconciled with `/etc/fstab` (D45) | absent | present |

D45's symptom is exactly "it did not work": `/etc/fstab` names an ESP UUID that does not exist on
the disk, `/boot/efi` cannot mount, systemd falls into emergency mode, and emergency mode asks for
a root password that cannot exist because the kickstart sets `rootpw --lock`.

## Correction built and verified

Rebuilt from the fixed source with the target baked in (`--test-target /dev/nvme0n1`), so the
install needs no boot-menu editing: `~/envy-install/install-to-nvme0n1.iso`, SHA-256
`5a4a2e97…`, 5,036,703,744 bytes, `build_time_utc 2026-10-26T05:08:14Z`. Read back out of the
ISO: `dracut-config-generic` present, the ESP UUID fix present, the removable-media fallback
`EFI/BOOT/BOOTX64.EFI` written by the `%post`, baked cmdline
`kavika.target=/dev/nvme0n1 kavika.confirm=/dev/nvme0n1`, and `checkisomd5` OK. The generic
offline ISO was rebuilt from the same source and verified the same way.

## Still unproven

- The corrected ISO's install has not been run at the time of writing.
- Whether the disk boots on the Envy at all — no install from this host has yet been booted on
  the target hardware. That is the only evidence that counts, and it is outstanding.
- The Envy's firmware behaviour with the finished disk is unknown.
