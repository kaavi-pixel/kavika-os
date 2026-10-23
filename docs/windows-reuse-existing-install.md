# Reusing the Envy's own Windows as the Kavi'ka Windows workspace

Question put by the user on 23 October 2026:

> The HP Envy still has Windows on it. Could Kavi'ka be installed there, but with the
> Windows side being *the Windows I already have*? Once file sharing works between the two,
> moving everything over would be easy.

Short answer: **yes, three different ways, and only one of them is the risky one.** They
differ in what "the same Windows" means. Read this with [envy-transfer.md](envy-transfer.md)
(which still governs whether anything may be written) and
[windows-workspace.md](windows-workspace.md) (what the Windows workspace actually is).

> **Nothing here authorises a write to the Envy.** Its 1 TB internal disk holds Windows and
> is in no erase approval. Every route below needs the [envy-transfer.md §4 gate](envy-transfer.md#4-the-gate-before-any-envy-write)
> first, and a fresh explicit go-ahead at the moment of the write.

## The design fact that decides everything

In Kavi'ka the Windows workspace is a **QEMU/KVM guest displayed full-screen on desktop 2**
([windows-workspace.md](windows-workspace.md)). A guest boots a **disk it is given**. So
"reuse my Windows" always reduces to one question:

> **How does the guest get access to the bytes of the existing Windows install?**

There are exactly three answers, and this is the whole decision:

| Route | The guest's disk is | The Windows you get |
|---|---|---|
| **1. Neighbour** | a fresh guest disk (or none yet) | not reused; Windows stays native |
| **2. Copy** | a one-time copy of your Windows install, as a QCOW2 | a byte-for-byte clone, frozen at copy time, original untouched |
| **3. In place** | the physical Windows partitions themselves | literally the same install, live |

## Route 1: keep Windows native, share its files to Kavi'ka (no reuse)

The cheapest route, and the right first step, because **it is the one that actually achieves
the user's stated goal** — moving files across — with none of the virtualisation risk.

- Shrink the Windows partition from Windows' own Disk Management (non-destructive; NTFS
  shrink is bounded by unmovable files), leaving free space for Kavi'ka.
- Install Kavi'ka into that free space. Windows stays exactly where it is and still boots
  **natively** from firmware when selected.
- For file transfer, two paths, both already in the spec:
  - **Guest off:** Kavi'ka mounts the Windows NTFS partition directly (`ntfs3`, read/write).
    Drag files at native speed. This is the F04 shared-folder workflow with the partition as
    the shared folder.
  - **Guest on:** the ordinary F04/F07 network share between host and guest.

What you get: full native Windows speed whenever you boot it, and the fastest possible file
migration. What you do not get: Windows as a workspace you can *swipe* to — the swipe would
land on a separate VM, not on this Windows. What it costs: about 30 minutes, one shrink, one
install.

## Route 2: copy the install into a guest disk, once

If the user wants their **apps, settings and profile** to be the Windows side, but is willing
to accept a copy:

- Shrink as in Route 1, then copy the Windows partitions (ESP + MSR + Windows + WinRE) into a
  single QCOW2 on the Kavi'ka side: `qemu-img convert`/`dd` of the partition range, or capture
  the set into a raw image and preallocate it. Roughly 1 TB of growth on a 1 TB disk, so in
  practice this needs a second disk or an external SSD as the destination.
- Point the existing launcher at that image instead of a freshly built `windows11.qcow2`.
  The launcher already takes a disk path, and it already presents an NVMe device
  (`-device nvme,drive=nvme0,serial=KAVIKA0000000001`), which Windows' in-box `stornvme`
  driver handles — so the storage-controller change is the least of the problems.
- The original Windows on the Envy remains untouched and bootable. The copy is a snapshot: it
  stops matching the original the moment either side is used.

What you get: a Windows workspace containing everything you had, with the original intact as
a fallback. What it costs: disk space equal to the Windows install, and a one-way freeze.

## Route 3: P2V in place, the guest boots the physical Windows partitions

This is literally "the Windows I have". It is also the route with the sharp edges, and it is
well-trodden outside this project: the published recipe is to build a synthetic disk out of
loopback files plus the real NTFS partition merged with `mdadm --build --level=linear`, lay a
GPT on top, and attach that; or, more simply, hand QEMU the raw device
(`-drive format=raw,file=/dev/...`) with `-cpu host` (Windows frequently fails to boot without
it). Both are in the wild and both are fragile.

**The Kavi'ka-specific problem:** Kavi'ka and Windows live on the **same physical NVMe**, so
handing QEMU the whole disk would expose Kavi'ka's own partitions to Windows. The guests must
therefore be given the *Windows partitions individually*, reassembled into a synthetic disk —
which is the messy half of the recipe above.

Hard prerequisites and their consequences:

| Prerequisite | Why | Consequence if ignored |
|---|---|---|
| **BitLocker off** (or the recovery key in hand) | the guest gets a **virtual** TPM (`swtpm`), a different TPM from the physical one, so the volume master key will not unseal | Windows stops at a BitLocker recovery prompt every boot in the guest; without the 48-digit key the install is unreadable |
| **Fast Startup / hibernation off** | a hibernated NTFS is not cleanly mountable, and hiberboot leaves the volume in a suspended state | the partition cannot be shared to the host while Windows is off, and mounting it risks corruption |
| **Windows activation accepted as at-risk** | the licence is bound to the physical board; running it under virtual hardware commonly drops activation | "Windows isn't activated" watermark; MS licensing does not treat an OEM licence as a VM licence, which the project records as a licensing gate, not a technical one |
| **Storage controller** | the guest presents a different (emulated) NVMe/AHCI controller | `INACCESSIBLE_BOOT_DEVICE` unless an in-box or pre-staged driver covers it; `-cpu host` is normally required too |
| **Never both at once** | the host and the guest must not mount the same NTFS simultaneously | corruption. With Route 3, file sharing while the guest runs must go over the network (F07), not over a host mount |
| **No GPU acceleration** | no passthrough in this architecture | the Windows side is software-rendered: fine for browsing and office work, poor for games, video editing or GPU compute. Native boot remains the answer for those. |
| **Native boot becomes unsafe** | a Windows install that has been booted on emulated hardware and then booted natively can require repair | after P2V, booting this Windows natively again is not a rollback path |

What you get: the actual install, apps and profile, swipeable as the Windows workspace. What
it costs: all of the above, permanently, plus a partition handoff that has to be scripted and
re-established on every host boot.

## Recommended sequence

1. **Do Route 1 first.** It needs no P2V, no BitLocker work, no activation risk, and it is the
   thing the user actually wants: files moving easily. It is also fully reversible.
2. **Route 2 if the workspace must contain the old profile** — with the original kept as the
   fallback.
3. **Route 3 only if the user insists the workspace be the live install and accepts the table
   above.** Treat it as a research spike, proven first on the Laptop Studio against a
   throwaway Windows install, never first on the Envy.

## What must be measured on the Envy before choosing

All read-only, all from Windows, none of it a write. These decide whether Route 3 is even live:

```powershell
# BitLocker state per volume (decides the biggest Route 3 risk)
Get-BitLockerVolume | Select-Object MountPoint, VolumeStatus, ProtectionStatus, EncryptionMethod
# Windows edition (activation/licensing reality)
Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, BuildNumber
# Free space and shrinkability headroom
Get-Disk | Select-Object Number, FriendlyName, BusType, Size, PartitionStyle
Get-Partition | Select-Object DiskNumber, PartitionNumber, DriveLetter, Size, Type, Offset
Get-Volume | Select-Object DriveLetter, FileSystemLabel, FileSystem, SizeRemaining, Size
# Fast Startup, hibernation, pagefile as unmovable-file obstacles to a shrink
powercfg /a
(Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Power').HiberbootEnabled
# Whether a second internal slot exists at all (decides if Route 2/3 can use a second NVMe)
Get-PhysicalDisk | Select-Object DeviceId, FriendlyName, MediaType, BusType, Size
```

Cross-check the physical slot count against the Envy's service manual before promising a
second NVMe; on many Envy x360 2-in-1 chassis there is exactly one M.2 slot.

## If the goal is only "get my files over"

Then **no reuse is needed at all**, and this is worth saying plainly: F04 needs *a* shared
folder with *a* Windows, not the user's particular Windows. Route 1 plus the F04 share moves
files faster than any P2V would, and it does not put the existing install at any risk.

## Status

Recorded 23 October 2026 as a **design decision, not a tested result**. Nothing in Routes 2 or
3 has been attempted in this project: no physical partition has been handed to a guest, no
Windows install has been copied into a QCOW2, and the Envy's BitLocker state, edition and slot
count are all **unmeasured**. Every claim above about virtual hardware, virtual TPMs and
activation is either vendor documentation or well-known field practice in the sources listed
here, not a measurement from this project.
