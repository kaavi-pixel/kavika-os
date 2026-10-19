# Kavi'ka OS: Surface Laptop Studio test machine

Updated 19 October 2026 | Hardware identified from a Fedora "System Details" report; nothing from Kavi'ka has been run on it yet.

The Surface Laptop Studio is the project's **second machine**. It already runs Fedora, so it is where the Linux side and the virtual-machine work are tested first. The **Surface Pro 8 stays the final install target.** Results from the Laptop Studio are evidence about the Pro 8, never proof.

## What we know

Supplied by the user from the Fedora GNOME "System Details" report (19 October 2026). The disk capacity field was `(null)`, so storage is still unmeasured.

| Item | Value |
|---|---|
| Model | Microsoft Corporation Surface Laptop Studio |
| CPU | 11th Gen Intel Core i5-11300H, 8 logical processors |
| Memory | 16.0 GiB |
| Graphics | Intel Iris Xe (TGL GT2) only. This matches Microsoft's i5 configuration, which has no discrete GPU |
| Firmware | 33.104.143 |
| OS | Fedora Linux 44 Workstation (GNOME 50, Wayland) |
| Kernel | 6.19.10-300.fc44.x86_64: the same stock kernel as the diagnostic ISO |
| Disk | Not reported; measure with the preflight script below |

Microsoft lists the i5-11300H (H35) configuration with 16 or 32 GB of RAM ([Microsoft Surface Laptop Studio page](https://www.microsoft.com/en-us/d/surface-laptop-studio/8srdf62swkpf/cmqj)).

## How it differs from the Pro 8

| | Laptop Studio (test) | Pro 8 (target) |
|---|---|---|
| CPU | Core i5-11300H, 4 cores / 8 threads | Core i5-1135G7 or i7-1185G7, 4 cores / 8 threads ([Microsoft](https://support.microsoft.com/en-us/surface/models/surface-pro-8-features-and-specs)) |
| RAM | 16 GiB | 8, 16 or 32 GB (unmeasured on the owner's unit) |
| Form | Laptop with pull-forward screen | Tablet with Type Cover |
| Same generation | Tiger Lake | Tiger Lake |
| Disk | unmeasured | factory marking 128 GB (owner-reported), unmeasured |

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

- It holds the owner's working Fedora installation. **Never write an image to its internal drive, repartition it, or change firmware or Secure Boot settings** without a fresh, explicit instruction.
- Test the ISO in a disposable VM first, then from external media. Do not use it to install.
- Do not upload raw logs. The report contains no serials, UUIDs, MAC or IP addresses, but review the output before sharing.
- Installing virtualisation packages changes the machine. Treat `sudo dnf install` as a separate, approved step.

## Step-by-step on the Laptop Studio

1. Get this repository onto it (`git clone https://github.com/kaavi-pixel/kavika-os.git`).
2. Run the read-only preflight. It installs and changes nothing:

   ```bash
   bash tools/surface-fedora-preflight.sh
   ```

   It reports Fedora version, KVM and tool readiness, libvirt state, free RAM and disk, Secure Boot and TPM, and the full hardware JSON. Review the output before sharing it.
3. If KVM is not usable, the script says why. Typical fixes are installing `qemu-kvm` and `edk2-ovmf`, and adding your user to the `kvm` group. Do these only once you have decided to.
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
| Hardware identified | Done (user-supplied report) |
| Preflight run on the machine | Not yet |
| KVM usable | Not yet measured |
| ISO boots in a KVM guest | Not yet |
| ISO boots from external media | Not yet |
| Windows 11 guest | Not started |
