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
3. **Physical disposable USB disks.** Two sacrificial sticks: install to one, prove the
   other unchanged by hash. This is the T19 evidence. Procedure: write
   `build/Kavika-OS-0.1.0-netinst-network.iso` (or `-offline`) to USB disk A; attach USB disk
   B (known hash) beside it; boot, and at the GRUB menu edit the entry to append
   `kavika.target=/dev/sdA kavika.confirm=/dev/sdA` (disk A's exact device); confirm the
   install lands on A and B is byte-identical after. Both product ISOs ship fail-closed (no
   consent baked), so nothing is written until that device is named twice.
4. **First boot on real hardware** (a disposable machine or the Laptop Studio's **USB**
   disk, never its internal NVMe): user created, opt-in dialog shown, no Windows
   provisioning started (T20).
5. **Recovery/update rehearsal (T22):** define and test the rollback story before any
   release gate.

The Envy is **not** on this ladder. It enters only after every rung passes and the user
gives a fresh explicit go/no-go with its exact disk identified.

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
  the same class of bug one layer down.
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
