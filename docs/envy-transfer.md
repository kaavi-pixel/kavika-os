# HP Envy x360: transfer notes and install readiness

What carries over from the Surface Laptop Studio test bed to the **HP Envy x360**, the
project's only install target, and exactly what must be true before its Windows is
replaced. Read this with [target-machines.md](target-machines.md) and
[testinstall.md](../testinstall.md).

> **Nothing here authorises a write.** The Envy runs Windows today and is the project's
> build/emulation helper. Its internal 1 TB disk is in **no** erase approval. Replacing its
> Windows is a separate, destructive step that needs a fresh explicit go/no-go **at the
> moment of the write**, with the exact physical disk identified first. No Kavi'ka image
> has ever been installed anywhere; the Envy has only been *booted live from USB*
> (21 October 2026, [record](validation/hardware-boot-2026-10-21-envy.md)).

## 1. The machine, and why it is not the test bed

| | HP Envy x360 | Surface Laptop Studio |
|---|---|---|
| Role | **The only install target** | Test machine |
| CPU | AMD Ryzen 7 8840HS (AMD-V / `svm`) | Intel Core i5-11300H (VT-x / `vmx`) |
| GPU | AMD Radeon 780M (integrated) | Intel Iris Xe |
| RAM | 16 GB (inherited record, not re-measured) | 16 GB (measured) |
| Disk | 1 TB, holds Windows | 256 GB NVMe, holds Fedora 44 |

The two are **different CPU and GPU vendors**. Nothing platform-specific measured on the
Intel Laptop Studio — KVM accelerator, graphics driver behaviour, kernel module, thermal or
kernel-out-of-the-box results — transfers to the AMD Envy. Treat any result as evidence for
the machine it was measured on, never proof for the other.

## 2. What transfers, and what does not

**Transfers (platform-independent):**

- **The image boots on AMD hardware.** The preview (SHA-256 `bd8407d6…`) booted live from
  USB on the Envy on 21 October 2026, with Meta+F12 workspace switching and Bluetooth
  reported working. This is the one Envy fact on record, and it is **user-reported**, not
  captured ([record](validation/hardware-boot-2026-10-21-envy.md)). The newest build
  (`b5b650bc…`, 22 Oct) adds the Kavi'ka identity, the Windows plumbing and the installer
  assets; it is boot-verified
  in a KVM guest but has not yet been booted on the Envy.
- **The Windows-in-KVM recipe is host-agnostic in shape.** The ESP-on-USB boot, the
  `removable=on` answer stick, the `LabConfig` hardware bypass, and the `bcdboot` ESP
  population fix are all QEMU/guest facts, not Intel facts
  ([windows-install-recipe.md](windows-install-recipe.md)).

**Does not transfer:**

- KVM/`svm` behaviour and any virtualisation performance number from Intel.
- GPU/driver results (Iris Xe ≠ Radeon 780M), including the stock-kernel graphics path.
- Thermal, battery, suspend/resume and input results.
- The Laptop Studio's RAM headroom: the Envy's is an inherited record, and its free RAM
  under a live Kavi'ka session is unmeasured.

## 3. Readiness today

| Piece | State |
|---|---|
| Bootable Linux preview on the Envy | **Works** (live USB, 21 Oct 2026) |
| Windows 11 in a KVM guest (feasibility) | **Works** — full install to desktop, and now **self-contained**: the guest boots with only its own NVMe, no attached USB ESP (D21 closed, commit `bae321b`) |
| The user's browser (Firefox) in the Windows guest | **Works** — reported opening without problem (user-reported) |
| Cross-OS workspace + swipe, end-to-end | **Not verified** — the layout and the `kavika-windows-workspace` script exist, but no booted image has a real guest on desktop 2, and no swipe has ever been performed on a KDE host |
| Product Windows workspace (guest wired into the image) | **Not built** — the Test Centre says so; the preview ships no Windows |
| **Reusing the Envy's existing Windows as the workspace** | **Designed, not tested** — three routes (keep it native + share its files; copy it into a guest disk; or P2V the physical partitions in place) are analysed in [windows-reuse-existing-install.md](windows-reuse-existing-install.md). The Envy's BitLocker state, Windows edition and M.2 slot count are **unmeasured**, and none of the three has been attempted. |
| A supported **installer**, recovery/rollback, updates | **Not built** |
| Secure Boot chain | **Unmeasured** on every machine |

## 4. The gate before any Envy write

All of the following must be true, and then a **fresh explicit go-ahead** given at the
moment of the write:

1. It "works perfectly" on the Laptop Studio test bed: full Windows in the guest, the
   workspace/swipe path, and file sharing, tested per F01–F15/O01–O04.
2. An installer exists that requires **explicit target selection and confirmation** and
   leaves non-selected disks unchanged (O02/T19).
3. The exact Envy disk is identified by **role, model, capacity, connection and path** —
   never by a drive letter, "Disk 0", or an assumed `/dev/nvme0n1`.
4. Anything worth keeping on the Envy is backed up, **including the BitLocker recovery key**
   if the drive is encrypted — losing it makes recovery impossible. **Decide first whether the
   existing Windows is to be *reused* as the workspace, and if so by which route**
   ([windows-reuse-existing-install.md](windows-reuse-existing-install.md)); P2V in place makes
   the install dependent on a virtual TPM and a partition handoff, and is not a rollback path.
5. Recovery/rollback for the Envy is defined.

## 5. Procedure, once the gate passes (sketch, not authorisation)

1. Capture the Envy's before-layout: `lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINT` and
   `sudo blkid`, with serials cropped.
2. Back up Windows data and record the recovery key.
3. Verify the Kavi'ka image hash, then write it to a USB stick with the guarded writer
   (`tools/write-preview-to-usb.sh`); the agent cannot perform the raw write.
4. Boot live first and re-run the [testinstall.md](../testinstall.md) checklist, capturing
   evidence this time.
5. Only then run the installer, selecting the Envy's internal disk explicitly.
6. Validate first boot, the Windows guest, switching, and recovery on the Envy itself.

## 6. What is not authorised

- Any write, repartition or erasure of the Envy's internal 1 TB disk.
- Any firmware or Secure Boot change on any machine.
- A public ISO release, or Windows licence/activation handling by the project.

The earlier approvals covered the Surface Pro 8's internal disk and an empty 512 GB
external SSD. With the Pro 8 dropped, the internal-disk approval is **withdrawn, not
transferred**. No internal disk on any machine has been written by this project.
