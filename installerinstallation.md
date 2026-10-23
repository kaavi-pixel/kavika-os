# installerinstallation.md — the Kavi'ka OS installer, build plan

Version 0.1 | 22 October 2026 | **Plan. Nothing here is built yet, and nothing here
authorises writing any machine's internal disk.** The HP Envy's disk is in no erase
approval; every step below is validated on disposable media only, and the Envy needs a
fresh explicit go/no-go with its exact disk identified before anything touches it.

This is the roadmap for the OS4 milestone: turning the diagnostic live preview into an
image that can install Kavi'ka OS to a real disk, safely. Every step names what "done"
means. The acceptance criteria come from [features.md](features.md) (O02) and
[bugtracker.md](bugtracker.md) (T19/T20); the gap this closes is the first row of the
[Fedora gap table in handoff.md](handoff.md#gaps-vs-a-normal-installed-fedora-and-vs-windows).

## Status update — 22 October 2026 (post-validation)

The automated installer (Path B) now works end-to-end and is verified in a disposable KVM
guest: see [docs/validation/vm-install-2026-10-22-laptop-studio.md](docs/validation/vm-install-2026-10-22-laptop-studio.md).

Key facts established since this plan was first written:

- **A Fedora live install cannot be kickstart-automated.** Anaconda gates every kickstart
  path (`--kickstart`, `inst.ks`) on `not options.liveinst` and always loads
  `interactive-defaults.ks` in live mode; it also ignores kickstart `part` commands. So the
  live image is an *interactive* installer only.
- **The automated installer is a dnf/netinst build (Path B), not the live image.** A new
  kickstart `image/install/kavika-net.ks` drives Anaconda from the Fedora 44 Everything repo
  (or a bundled offline repo), where `%packages`, `part`, and unattended automation all work.
- **The fail-closed consent lives in the kickstart `%pre`** (not the Python pre-flight): it
  reads `kavika.target=`/`kavika.confirm=` from the kernel command line and aborts before any
  storage write unless they match and the device is a whole, unmounted, large-enough disk.
- **Data partitions use ext4, not btrfs.** btrfs + `--grow` root produced an invalid root
  filesystem ("bad superblock") in validation; ext4 is the robust choice for v1.
- **The overlay delivery needs `cpio -idmu`.** The overlay cpio is built `--reproducible`
  (1970 timestamps), so plain `cpio -i` skipped overwriting newer on-disk files and the
  Kavi'ka os-release identity never landed.
- New tooling: `tools/build-netinst-install.py` (netinst builder, optional `--repo-dir` and
  `--test-target`), `tools/kavika_overlay.py` (shared overlay-cpio builder), and
  `image/install/kavika-net.ks`.

## 0. What the installer must satisfy (acceptance)

- **T19 / O02:** installation requires **explicit target confirmation**, succeeds on a
  blank disposable disk, and leaves **attached non-selected disks unchanged** — proven by
  fixture hashes taken before and after, not by the installer's exit code.
- **T20 / O02:** first boot creates a usable desktop and requests **explicit opt-in**
  before Windows provisioning or any sensitive share/redirection change. Nothing Windows
  happens automatically.
- **T22 / O04:** recovery/rollback is defined before any release gate; an update path is
  validated.
- **Identification rule (project law):** a target disk is matched by **role, model,
  capacity, connection and path** — never by a drive letter, "Disk 0", or an assumed
  `/dev/nvme0n1`.

## 1. What exists today (the starting line)

- The live image carries upstream **Anaconda** packages untouched; the install entry is
  deliberately **guarded** (`usr/bin/liveinst` is replaced by a refusal, the desktop entry
  is hidden). The installer work replaces that guard with a real, consent-driven flow.
- The builder (`tools/build-live-preview.py`) replays the pinned Fedora KDE 44 base ISO
  plus a files-only cpio overlay; it maps files into the ISO and rebuilds the boot config.
- The Windows workspace **plumbing already ships in the image** (the guest launcher at
  `/usr/local/lib/kavika/launch-windows-vm-linux.py`, `kavika-windows-workspace`, the
  provisioning guide `WINDOWS.txt`, and the two-desktop `kwinrc` layout).
- The guarded USB writer (`tools/write-preview-to-usb.sh`) is the model for
  consent-driven destructive operations: refuse unless every check passes, and require the
  target to be named twice.
- `os-release` already presents Kavi'ka OS with `ID_LIKE=fedora`, so an installed system
  keeps resolving Fedora repositories.

## 2. Decisions to make first (each blocks the step that depends on it)

| # | Decision | Recommendation | Blocks |
|---|---|---|---|
| D1 | Installer engine | **Reuse upstream Anaconda driven by a Kavi'ka kickstart.** A hand-rolled partitioner is a non-goal: Anaconda already handles GPT/ESP/LUKS, storage sizing and error paths, and it is already in the image | everything |
| D2 | Entry shape | One hybrid ISO with **two boot/menu entries**: "Live preview" (today's behaviour) and "Install Kavi'ka OS" (pre-flight + `liveinst --kickstart`). No separate install media to keep in sync | §5 |
| D3 | Partition layout | ESP 1 GiB (FAT32), `/boot` 2 GiB, `/` (btrfs, Fedora default), `/home`, and a dedicated **`/var/lib/kavika/windows`** volume sized for a Windows guest (≥128 GiB, sparse qcow2). Decide LUKS default (recommend: on, passphrase chosen at install) | §3, §7 |
| D4 | Installed-system payload delivery | The live image ships its Kavi'ka files as a cpio overlay; an **installed** root needs them too. Short term: kickstart `%post` copies them off the install media. Long term (better): build a small `kavika` RPM so updates can carry them | §3 |
| D5 | First boot | Anaconda creates the user (kickstart); a Kavi'ka first-boot dialog then presents the **Windows-workspace opt-in** (T20) and never runs it without consent | §7 |
| D6 | Update policy | Keep stock Fedora repos (works because `ID_LIKE=fedora`, `VERSION_ID=44`); Kavi'ka-only content ships via the RPM from D4 | §3 |

**Decisions recorded 22 October 2026.** D1 = Anaconda driven by a Kavi'ka kickstart. D2 = one
hybrid ISO with two entries, but only the *assets* ship today (the boot entry is not wired yet).
D3 = the layout in `image/install/kavika.ks` (sizes provisional until measured). D4 = short-term
`%post` from media, long-term a `kavika` RPM. D5 = `firstboot --enable` for user creation, then the
Windows opt-in. D6 = stock Fedora repos.

## 3. The kickstart (step 1 of the build)

`image/install/kavika.ks`, owned by the repo:

- `ignoredisk --only-use=<the device the pre-flight confirmed>` — the kickstart never
  sees a disk the operator did not name twice.
- `clearpart --all --initlabel` scoped to that device.
- Partitions per D3, including the Windows-guest volume.
- `%packages`: the KDE base plus the virtualization stack the live preview deliberately
  omits — `qemu-kvm`, `swtpm`, `swtpm-tools`, `edk2-ovmf`, `mtools`, `virt-install` — so
  the **installed** system can actually provision the Windows workspace (that is the whole
  point: the live preview cannot).
- `%post`: install the Kavi'ka overlay onto the installed root (`kavika-*` scripts, the
  kwinrc two-desktop layout, `WINDOWS.txt`, the os-release identity), and **disable the
  preview installation guard** on the installed system only.
- No `%post` may weaken SELinux or add keys/passwords to logs.

**Done when:** the kickstart parses, and a dry-run (see §6) shows the intended partitions
on a disposable image with nothing else touched.

## 4. The pre-flight: `tools/kavika-install.py` (step 2)

The consent layer that sits between the menu entry and Anaconda. Model it on
`write-preview-to-usb.sh`:

1. Inventory every block device: name, size, transport, model, mountpoints; display
   **without serials** on screen, but match internally on everything.
2. Require the operator to **type the exact device path twice**
   (`--device` and `--confirm-device` must agree, like the USB writer).
3. Refuse unless: the path exists, is a whole disk, is not the live medium itself, is not
   mounted, and is large enough for the layout.
4. Show exactly what will be erased and require an explicit yes.
5. Record the chosen device, the inventory snapshot and the ISO hash into a log the
   operator can keep as evidence.
6. Only then exec `liveinst --kickstart /run/initramfs/live/Kickstart/kavika.ks` (or the
   mapped media path) with `ignoredisk` pinned to the confirmed device.

**Done when:** the unit suite covers every refusal path (mismatched confirm, mounted
target, too-small target, live medium selected, cancellation at each prompt), and the
happy path emits exactly the intended command.

## 5. Builder changes (step 3)

Extend `tools/build-live-preview.py`:

- Map `kavika.ks` and `kavika-install.py` into the ISO.
- Add the "Install Kavi'ka OS" boot/menu entry alongside the live entry; the live entry's
  guard stays exactly as it is today.
- Manifest gains `installer_supported: true` for install-capable builds, and the
  validation record states which entry was tested.

**Done when:** a built ISO carries both entries, the live entry still boots unchanged
(regression: desktop + Test Centre), and the install entry reaches the pre-flight.

## 6. Validation ladder (step 4 — the gate, in order)

Each rung must pass before the next, and every rung hashes **all** attached disks before
and after:

1. **Disposable KVM target.** Install into a blank qcow2 attached to a disposable guest —
   zero physical risk. Done when: the installed image boots to first boot, and the guest's
   *other* disks (a second qcow2 fixture with a known hash) are byte-identical after.
2. **Refusal matrix.** Every §4 refusal path exercised and recorded.
3. **Physical disposable USB disks.** Two sacrificial USB **disks of at least 240 GiB each** —
   the `%pre` refuses any target below 240 GiB (`MIN_BYTES`), so an ordinary flash stick can
   never serve as the install *target* (it can only be the boot medium). Install to one, prove
   the other unchanged by hash. This is the T19 evidence. Procedure: write
   `build/Kavika-OS-0.1.0-netinst-network.iso` (or `-offline`) to USB disk A; attach USB disk
   B (known hash) beside it; boot, and at the GRUB menu edit the entry to append
   `kavika.target=/dev/sdA kavika.confirm=/dev/sdA` (disk A's exact device); confirm the
   install lands on A and B is byte-identical after. Both product ISOs ship fail-closed (no
   consent baked), so nothing is written until that device is named twice.

   **Designated sacrificial disk (23 October 2026).** The 1 TB Toshiba external
   (`usb-TOSHIBA_EXTERNAL_USB_20260806007777F-0:0`, `TOSHIBA MQ04UBF100`, 931.5 GiB, USB,
   `RM=0`) is the intended rung-3/4 target. It was verified **empty** on 23 October 2026
   (NTFS, 115 MB used, no entries at the top level), so erasing it destroys nothing. The boot
   medium remains the 3.8 GB flash stick, which is too small to be a target. Note the `RM=0`:
   that flag only matters to `write-preview-to-usb.sh`, not to the installer, whose `%pre`
   checks whole-disk, unmounted, non-pseudo and ≥ 240 GiB but says nothing about `RM`.

   **Writing the installer media.** Identify the target first, by model and size, never by
   position (USB enumeration order changes between boots):

   ```bash
   lsblk -o NAME,SIZE,TYPE,RM,TRAN,LABEL,FSTYPE,MOUNTPOINT,MODEL
   ```

   Then write it, naming the device twice. `--dry-run` runs every check and writes nothing,
   so run that first:

   ```bash
   # network installer (1.2 GB, needs internet during install)
   sudo bash tools/write-preview-to-usb.sh \
     --iso build/Kavika-OS-0.1.0-netinst-network.iso \
     --sha256-file build/Kavika-OS-0.1.0-netinst-network.iso.sha256 \
     --device /dev/sdX --confirm-wipe /dev/sdX --dry-run

   # offline installer (5.0 GB, bundles the repo; needs a >= 5.1 GB disk)
   sudo bash tools/write-preview-to-usb.sh \
     --iso build/Kavika-OS-0.1.0-netinst-offline.iso \
     --sha256-file build/Kavika-OS-0.1.0-netinst-offline.iso.sha256 \
     --device /dev/sdX --confirm-wipe /dev/sdX --dry-run
   ```

   Drop `--dry-run` to actually write. Media sizing: the **offline** ISO is 5,030,150,144 B
   and needs a disk of at least 5.1 GB (the 3.8 GB stick used for the earlier physical boot
   tests is too small for it and the writer refuses it on the size check); the **network** ISO
   is 1,218,707,456 B and fits that stick with ~2.6 GiB to spare. Unmount the target first
   (`udisksctl unmount -b /dev/sdX1`) — the writer treats a mounted partition as fatal for a
   write, though only a warning for a dry run. If the unmount fails with **"target is busy"**,
   a file manager is holding the mountpoint: find the holder with `fuser -vm <mountpoint>`
   (GNOME Files appears as `nautilus`, KDE as `dolphin`), quit it (`nautilus -q`) or close that
   window, then unmount again. A read-only ISO mount cannot lose data by being unmounted, so
   this is always safe. After flashing, the stick's volume label reads
   `Fedora-E-dvd-x86_64-44` (the label baked into the ISO), not "Kavika".

   Two further notes: a **USB flash stick** reports `RM=1`, but
   an **external USB hard drive** almost always reports `RM=0` (its bridge does not advertise
   removable media), which the writer refuses by default — pass `--allow-fixed-usb` for those,
   which relaxes only that flag and keeps every other check. And the live media cannot be its
   own install target, so installing *onto* a disk means booting the installer from a
   different one. The writer is `tools/write-preview-to-usb.sh`; the agent cannot perform the
   raw write itself and hands the operator the guarded command.
4. **First boot on real hardware** (a disposable machine or the Laptop Studio's **USB**
   disk, never its internal NVMe, and again at least 240 GiB): user created, opt-in dialog
   shown, no Windows provisioning started (T20).
5. **Recovery/update rehearsal (T22):** define and test the rollback story before any
   release gate.

The Envy is **not** on this ladder. It enters only after every rung passes and the user
gives a fresh explicit go/no-go with its exact disk identified.

### The physical rung, end to end (runbook)

Two disks, two jobs. Confusing them is the only way this goes wrong:

| Disk | Node here (23 Oct) | Job |
|---|---|---|
| 3.8 GB USB stick | `/dev/sdb`, `RM=1`, `usb` | installer media. Boot only, never a target |
| 1 TB Toshiba external | `/dev/sdc`, `RM=0`, `usb` | the Kavi'ka **system** disk, and the home of the 128 GiB guest volume |

**Nodes change between boots and between machines.** Derive them from `lsblk` model and size
every time; this disk has already been `/dev/sda`, `/dev/sdb` and `/dev/sdc` in one session.

1. **Flash the installer** to the stick (`write-preview-to-usb.sh`, below). Done when the
   read-back SHA-256 matches the sidecar.
2. **Capture the before state** of every disk in the test computer, without root:
   `lsblk -o NAME,SIZE,TYPE,FSTYPE,LABEL,UUID,PARTUUID,MOUNTPOINT`. UUIDs and PARTUUIDs are
   the fingerprint; if the installer touches a disk it did not name, they change.
3. **Attach both disks to the test computer**, enable USB boot, and check Secure Boot. Fedora's
   shim is Microsoft-signed, so it normally boots with Secure Boot on; changing firmware is
   outside this project's approval and is the operator's call.
4. **Boot the stick.** Nothing is written yet. Before committing, get a shell in the installer
   and run `lsblk -o NAME,SIZE,TYPE,TRAN,MODEL` **there**: the Toshiba will not carry the node
   it had on the dev host.
5. **At GRUB**, press `e` on "Install Kavi'ka OS" and append the target **twice**, both tokens
   being the Toshiba's node as the installer sees it, then Ctrl+X:
   `kavika.target=/dev/sdX kavika.confirm=/dev/sdX`. The install erases that disk completely.
   The ≥ 240 GiB size check protects against naming the stick, but **not** against naming a
   large internal disk, so be certain.
6. **Read the console.** Proceed only on `KAVIKA CONSENT: <name> confirmed (<GiB>)`; a
   `KAVIKA CONSENT-REFUSED:` line means nothing was written and the reason is stated.
7. **Re-run the step-2 fingerprint on the test computer.** The named disk should now carry the
   Kavi'ka layout; every other disk must be byte-identical. This, not the installer's exit
   code, is the T19 evidence.
8. **Boot the test computer from the Toshiba**, complete first boot (initial-setup creates the
   user), and answer the Windows opt-in.
9. **Give the guest its volume** (Anaconda leaves it `root:root`):
   `sudo chown "$USER" /var/lib/kavika/windows`.
10. **Get your Windows ISO onto the installed system** (8.5 GB; the installer stick cannot
    carry it). Offline method: boot the dev host, plug the Toshiba in, mount its `/home` and
    copy the ISO in.
11. **Provision and show it:** `kavika-windows-provision --iso <iso>`, then
    `kavika-windows-workspace`. See [windows-workspace.md](../docs/windows-workspace.md).

### Compact profile: targets under 240 GiB

The product layout needs 240 GiB (ESP 1 + `/boot` 2 + `/home` 20 + a 128 GiB guest volume +
`/` 60). A smaller target is refused outright. For a small test disk there is an opt-in
compact profile:

| | product | compact |
|---|---|---|
| size floor | 240 GiB | 76 GiB |
| `/home` | 20 GiB | 10 GiB |
| guest volume | 128 GiB | 40 GiB |
| `/` | 60 GiB minimum, grow | 20 GiB minimum, grow |

Selected with `kavika.compact=1` on the kernel command line, or baked at build time with
`--compact`. On a 119.2 GiB disk (a 128 GB SSD) it yields 66 GiB for `/`. The guest volume is
40 GiB, so provision there with `--disk-gib 32`; the default 64 GiB guest does **not** fit.
Compact is never the default, and both the floor and the volume sizes are asserted in
`tests/test_kavika_install.py` so the product layout cannot silently regress.

Built 23 October 2026: `build/Kavika-OS-0.1.0-netinst-compact.iso`, SHA-256
`1123230d…`, 1,218,707,456 bytes, built with `--compact --test-target /dev/vda`,
`checkisomd5` OK.

### When the target machine will not boot the installer medium

Observed 23 October 2026 on the test PC: the firmware **offered** the USB stick, the operator
selected it, and it fell through to Windows. That is the firmware finding no acceptable boot
entry on the stick; the machine itself boots a GPT disk with an ESP, in UEFI mode.

Because the machine *does* boot its own internal disk, the install can be driven from the dev
host instead:

1. Attach **only** the target disk to the dev host, and identify it by model, size and serial.
2. Build with `--compact --test-target /dev/vda`. A baked `/dev/vda` target is safe on bare
   metal, because virtio nodes do not exist there and the `%pre` refuses.
3. Boot that ISO in QEMU with the physical disk attached as virtio-blk, so it appears as
   `/dev/vda` inside the guest. Use `-no-reboot` so the installer's own reboot ends QEMU
   instead of restarting into the installer again, and `-boot order=d` so the firmware boots
   the CD rather than the Windows already on the target.
4. Watch the console for `KAVIKA CONSENT: vda confirmed` and the `KAVIKA-VERIFY:` lines.

**The boot entry travels with the disk, not the machine.** Anaconda registers its entry with
`efibootmgr` on whatever machine ran the installer, so a disk installed in a VM has no entry
on the target machine. The `%post` therefore also writes the UEFI removable-media fallback
`\EFI\BOOT\BOOTX64.EFI` onto the ESP, which is what firmware with no valid entry boots. If a
machine still will not boot it, add an entry in firmware pointing at
`\EFI\fedora\shimx64.efi` on that ESP.

The agent does not perform raw writes to physical disks. The operator runs the command.

## 7. First boot and the Windows opt-in (step 5)

- Anaconda creates the user (D5); the desktop comes up as Kavi'ka OS with the two-desktop
  layout.
- A first-boot dialog offers: "Set up the Windows workspace now?" — **opt-in only**. If
  declined, the workspace stays empty and `kavika-windows-workspace` explains itself
  (already implemented). If accepted, the system opens the provisioning guide
  (`WINDOWS.txt`) and its recipe; it still downloads and ships nothing itself, and
  licensing remains the user's.
- Done when T20 passes with a record.

## 8. Traps this project has already paid for

- **Never identify a disk by name or position** — USB enumeration order changes between
  boots; the D23 lesson (a stale path/BCD pointing at something that no longer exists) is
  the same class of bug one layer down. Concrete case, 23 October 2026: `/dev/sda` was the
  3.8 GB installer stick on the host, and became the 1 TB Toshiba the moment the stick was
  unplugged. **A command that was correct ten minutes ago can name a different disk now**, so
  re-derive the device from `lsblk` model and size before every write, and never reuse a
  command's `/dev/sdX` from an earlier session.
- **The installer's exit code is not evidence.** The before/after hashes of non-selected
  disks are.
- **A mounted target must be refused**, not unmounted by the tool (surprising unmounts
  are how the wrong disk gets erased).
- **The live medium itself must be refused** as a target (installing onto the stick you
  booted from is a real, destructive mistake).
- **Keep the preview's guard on the live entry.** Only the new install entry may run
  Anaconda; a blanket guard removal re-opens the "diagnostic image installs by accident"
  risk the guard exists to prevent.
- **No keys in logs:** LUKS passphrases, and any future Windows credentials, never enter
  a log, a manifest or a validation record.

## 9. Work breakdown (ordered)

**Status 22 October 2026 (post-validation):** the automated dnf/netinst installer (Path B)
is built and **verified end-to-end in a disposable KVM guest** — see
`docs/validation/vm-install-2026-10-22-laptop-studio.md`. Items 1–5 below are done via the
netinst build (`kavika-net.ks`, `build-netinst-install.py`, the `%pre` consent, the overlay
`%post`). The live-image "install entry" (the earlier items 2–4 wording) remains an
*interactive* installer only, because live installs cannot be kickstart-automated. Rungs 1
and 2 of the validation ladder are done: rung 1 (disposable KVM target + a second fixture
proven byte-identical) and rung 2 (refusal matrix — none/mismatch/too-small/pseudo all
refuse and terminate before any storage write). Remaining: rung 3 (physical USB disks),
first-boot opt-in polish (item 7), and recovery rehearsal (item 8).

| # | Item | Size | Done when |
|---|---|---|---|
| 1 | Decisions D1–D6 recorded (update this file) | S | the table has answers, not recommendations |
| 2 | `image/install/kavika.ks` v1 + `%post` overlay install | M | §3 done-when |
| 3 | `tools/kavika-install.py` pre-flight + refusal tests | M | §4 done-when, suite green |
| 4 | Builder: install entry + payload mapping | M | §5 done-when |
| 5 | Validation rung 1 (KVM target + unchanged second fixture) | M | record in `docs/validation/` |
| 6 | Refusal matrix + rung 3 (two USB sticks, hashes) | M | T19 evidence recorded |
| 7 | First boot + Windows opt-in | S | T20 evidence recorded |
| 8 | Recovery/update rehearsal + docs + gates | M | T22 defined; handoff/README updated |

Estimates are relative, not promises. Steps 1–5 are achievable on this machine with zero
physical-disk risk; steps 6 needs sacrificial USB sticks and a careful operator.

## 10. Not authorised by this document

- Any write to any machine's internal disk, including the Envy's 1 TB and the Laptop
  Studio's NVMe (it holds the build host).
- Any firmware or Secure Boot change.
- Shipping Windows, a Windows licence, or activation handling.
- A public ISO release.

See [handoff.md](handoff.md) for the gates, and [docs/envy-transfer.md](docs/envy-transfer.md)
for the route from "installer works on disposable disks" to "the Envy".
