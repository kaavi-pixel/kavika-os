# Kavi'ka OS: Surface Laptop Studio test machine

Updated 20 October 2026 | Hardware identified from a Fedora "System Details" report; the read-only preflight has now been run on the machine and its results are recorded below. Nothing from Kavi'ka has been booted on it yet.

The Surface Laptop Studio is the project's **second machine**. It already runs Fedora, so it is where the Linux side and the virtual-machine work are tested first. The **Surface Pro 8 stays the final install target.** Results from the Laptop Studio are evidence about the Pro 8, never proof.

## What we know

Supplied by the user from the Fedora GNOME "System Details" report (19 October 2026); the disk capacity field was `(null)` there, and the preflight of 20 October 2026 measured it (256 GB NVMe).

| Item | Value |
|---|---|
| Model | Microsoft Corporation Surface Laptop Studio |
| CPU | 11th Gen Intel Core i5-11300H, 8 logical processors |
| Memory | 16.0 GiB |
| Graphics | Intel Iris Xe (TGL GT2) only. This matches Microsoft's i5 configuration, which has no discrete GPU |
| Firmware | 33.104.143 |
| OS | Fedora Linux 44 Workstation (GNOME 50, Wayland) |
| Kernel | 6.19.10-300.fc44.x86_64: the same stock kernel as the diagnostic ISO |
| Disk | 256 GB NVMe (`HFM256GD3GX013N`), 255,060,320,256 bytes; measured by the preflight on 20 October 2026 |

Microsoft lists the i5-11300H (H35) configuration with 16 or 32 GB of RAM ([Microsoft Surface Laptop Studio page](https://www.microsoft.com/en-us/d/surface-laptop-studio/8srdf62swkpf/cmqj)).

## Preflight result, 20 October 2026

`bash tools/surface-fedora-preflight.sh` was run on this machine on 20 October 2026 (UTC `2026-10-20T00:36Z`, inventory header `2026-10-19T08:10Z`). It is read-only: it installed nothing, wrote no files and changed no setting. Everything below is machine-reported inventory, not an acceptance pass.

| Check | Result |
|---|---|
| CPU virtualisation flag (`vmx`) | yes |
| `/dev/kvm` | present and usable by the current user (no group change needed) |
| Kernel modules | `kvm`, `kvm_intel` loaded |
| Tools | `qemu-system-x86_64`, `qemu-img`, `virsh`, `swtpm` installed; **`virt-manager` missing** |
| OVMF firmware | `OVMF_CODE.fd` and `OVMF_VARS.fd` both present |
| libvirt | `libvirtd`/`virtqemud` **inactive** (`libvirtd` disabled, `virtqemud` enabled-but-not-running) |
| RAM | 15.4 GiB total, 7.0 GiB available |
| Disk | root and home are the same 235 GB filesystem on `nvme0n1`, 203 GB free |
| Secure Boot | disabled, and the platform is in **Setup Mode** (no enrolled platform keys) |
| TPM | present |
| Session | Wayland, kernel `6.19.10-300.fc44` (stock, same as the ISO) |
| Bluetooth / audio | 1 controller; HDA-Intel card |
| Video capture | 4 devices (cameras enumerated; not functionally tested) |
| Battery | present, 72%, discharging |
| Surface kernel modules | `surface_aggregator`, `_registry`, `_tabletsw`, `surface_battery`, `surface_charger`, `surface_gpe`, `surface_hid`, `surface_hid_core`, `surface_platform_profile`, `surfacepro3_button` |

**Conclusion: KVM is usable on this machine.** The resume-plan step 2 disposable-guest test is therefore unblocked here, unlike on the earlier Windows host, which needed software emulation. The captured output is filed as evidence: [preflight evidence, 20 October 2026](validation/preflight-surface-laptop-studio-2026-10-20.md).

### Observations that need follow-up

1. **No touchscreen or pen input device was detected.** The report returns `has_touchscreen: false`, `has_pen: false`, and no touch/digitizer node appears in `/proc/bus/input/devices`; the Surface HID nodes present are `045E:09AE` and `045E:09B0` (keyboard) and `045E:09AF` (touchpad), plus `Microsoft Surface POS Tablet Mode Switch`. This is consistent with the upstream claim that the panel needs the linux-surface kernel, but it is an observation on one machine, not a proven cause. Until it is confirmed, do not assume the internal panel responds to touch on the stock-kernel preview.
2. **Secure Boot is disabled and the platform is in Setup Mode**, so it has no enrolled platform keys. This is a firmware state, not a failure; nothing was changed. The eventual Pro 8 Secure Boot check (T21) starts from a different state and this result does not carry over.
3. **`virt-manager` is missing and libvirt is not running.** Neither is needed by `tools/launch-preview-vm-linux.py`, which starts QEMU directly, but any `virsh`/virt-manager workflow would need `sudo dnf install` plus enabling a service first — a separate, approved step.
4. **A 1 TB USB disk is attached** (`sda`, `One Touch w/PW`, 1,000,204,885,504 bytes, USB, non-removable flag but USB transport). It was only enumerated; nothing was read from or written to it. Identify it explicitly before any future media step, since the approved erase scope covers a 512 GB external SSD and this is not that device.
5. **The repo test suite does run here.** `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests` reports **Ran 30 tests, OK (skipped=1)** on the system Python 3.14.8, matching the handoff's "30 Linux tests pass". It is a `unittest` suite, so no `pytest` install is needed; the one skip is the known GRUB-parser-availability skip.
6. **The build prerequisites are not all present.** `cpio`, `implantisomd5` and `checkisomd5` are installed, but **`xorriso` and `grub-script-check` (grub2-tools) are missing** and `pycdlib` is not importable. `tools/build-live-preview.py` refuses to run without them, so building the rebuilt ISO on this machine needs an approved `sudo dnf install xorriso grub2-tools` plus a `pycdlib` provider. See [build prerequisites](build.md).


## How it differs from the Pro 8

| | Laptop Studio (test) | Pro 8 (target) |
|---|---|---|
| CPU | Core i5-11300H, 4 cores / 8 threads | Core i5-1135G7 or i7-1185G7, 4 cores / 8 threads ([Microsoft](https://support.microsoft.com/en-us/surface/models/surface-pro-8-features-and-specs)) |
| RAM | 16 GiB | 8, 16 or 32 GB (unmeasured on the owner's unit) |
| Form | Laptop with pull-forward screen | Tablet with Type Cover |
| Same generation | Tiger Lake | Tiger Lake |
| Disk | 256 GB NVMe (preflight-measured) | factory marking 128 GB (owner-reported), unmeasured |

Both are Intel Tiger Lake, so the CPU virtualisation features, the Iris Xe graphics driver and the stock kernel behave similarly. That is why the Laptop Studio is a good proxy for the Linux and KVM questions. It is **not** a proxy for the Pro 8's keyboard, touch, pen, tablet mode, cameras or storage size.

## What the Laptop Studio can answer

- Whether KVM works and how fast a guest runs on Tiger Lake hardware (the Windows host used so far could not use KVM; it needed software emulation).
- Whether the diagnostic ISO boots to the KDE desktop on real Surface hardware, including graphics, Wi-Fi, audio, sleep and Secure Boot.
- A first full Windows 11 guest under QEMU/KVM with 16 GiB of host RAM: CPU, graphics, resource budget and switching.
- Which Surface-specific kernel and libinput fixes are actually needed on Surface hardware.

## What it cannot answer

- Pro 8 Type Cover, touch and pen behaviour, or the Pro 8's 128 GB storage budget.
- Whether Windows plus Linux fit on the Pro 8's disk.
- Anything about the Pro 8's firmware or Secure Boot configuration.

## Known upstream notes (not verified here)

Per the [linux-surface device matrix](https://github.com/linux-surface/linux-surface/wiki/Supported-Devices-and-Features) and the [Laptop Studio page](https://github.com/linux-surface/linux-surface/wiki/Surface-Laptop-Studio):

- Touchscreen, pen and tablet mode need the linux-surface kernel.
- The touchpad can fail with default libinput palm detection; the wiki documents a quirk for it.
- On Wayland, slate mode can disable the keyboard and touchpad unless a libinput quirk is added.
- Wi-Fi, Bluetooth, speakers, suspend, hibernate and cameras are listed as working.

These are third-party claims. The Kavi'ka report records what is detected on the machine so they can be confirmed or contradicted.

## Safety rules for this machine

- It holds the owner's working Fedora installation. **Never write an image to its internal drive, repartition it, or change firmware or Secure Boot settings** without a fresh, explicit instruction. The platform is currently in **Setup Mode** with Secure Boot disabled; leave it that way unless separately instructed.
- Test the ISO in a disposable VM first, then from external media. Do not use it to install.
- Do not upload raw logs. The report contains no serials, UUIDs, MAC or IP addresses, but review the output before sharing.
- Installing virtualisation packages changes the machine. Treat `sudo dnf install` as a separate, approved step.

## Step-by-step on the Laptop Studio

1. Get this repository onto it (`git clone https://github.com/kaavi-pixel/kavika-os.git`). **Done.**
2. Run the read-only preflight. It installs and changes nothing:

   ```bash
   bash tools/surface-fedora-preflight.sh
   ```

   It reports Fedora version, KVM and tool readiness, libvirt state, free RAM and disk, Secure Boot and TPM, and the full hardware JSON. Review the output before sharing it. **Done 20 October 2026; result above. KVM is usable, so the next step is unblocked.**
3. If KVM is not usable, the script says why. Typical fixes are installing `qemu-kvm` and `edk2-ovmf`, and adding your user to the `kvm` group. Do these only once you have decided to. **Not needed here: KVM, `qemu-system-x86_64` and the OVMF files are already present, and the user already has access to `/dev/kvm`.**
4. Copy the ISO and its `.sha256` file to the machine, then run the disposable VM test:

   ```bash
   python3 tools/launch-preview-vm-linux.py \
     --iso ~/Downloads/Kavika-OS-*.iso \
     --sha256-file ~/Downloads/Kavika-OS-*.iso.sha256 \
     --vm-dir ~/kavika-vm-test
   ```

   The launcher refuses an ISO whose hash does not match. It attaches only a new private disk file and a user-mode network. It never touches a physical disk or shares a folder.
5. In the VM, run the functional checklist from the [validation record](validation/live-preview-0.1.0.md) and note every result.
6. Only after the VM test passes, consider booting the same ISO from external media on this laptop, still without installing.

## Evidence status

| Gate | State |
|---|---|
| Hardware identified | Done (user-supplied report; disk now measured by preflight) |
| Preflight run on the machine | **Done, 20 October 2026** (read-only; nothing changed) |
| KVM usable | **Yes** — `/dev/kvm` usable, tools and OVMF present |
| ISO boots in a KVM guest | Not yet |
| ISO boots from external media | Not yet |
| Windows 11 guest | Not started |

Nothing in the preflight run booted Kavi'ka or a guest, and it did not validate graphics, Wi-Fi, audio, sleep or Secure Boot behaviour. Those remain open.
