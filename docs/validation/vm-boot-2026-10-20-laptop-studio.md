# Kavi'ka: disposable KVM guest boot, Surface Laptop Studio, 20 October 2026

The locally rebuilt ISO was booted in a disposable KVM guest on the Laptop Studio. **The Meta+F12 workspace switch worked, in both directions**, which closes B06 for this build. Everything here is Linux preview evidence on virtual hardware; it says nothing about Surface hardware or Windows.

## Image under test

| Item | Value |
|---|---|
| ISO | `build/Kavika-OS-0.1.0-Surface-Pro-8-Live-Preview.iso` |
| SHA-256 | `bd8407d6393a12f8a5829ef15a86371b854f08834d9fd7df4a85ddbdc8820e0d` |
| Size | 3,370,319,872 bytes |
| Build record | [build-2026-10-20-laptop-studio.md](build-2026-10-20-laptop-studio.md) |
| Hash check | Launcher refused nothing: the sidecar hash matched before boot |

This is **not** the WSL-built `57a851a7…` candidate. Its results do not transfer to that image, and neither hash is canonical.

## Guest configuration

Launched from `tools/launch-preview-vm-linux.py`'s own command builder (imported, not copied), with a monitor socket and headless display added so screenshots and keystrokes could be captured.

- q35 machine, `accel=kvm`, `-cpu host`, 2 vCPU, 4096 MiB guest RAM on a 15.4 GiB host with 8.1 GiB available
- OVMF UEFI firmware with a private variable store copied into the VM directory
- 16 GiB **new** QCOW2 disk, empty before first boot
- CD-ROM: the ISO; boot order `d`; `-no-reboot`
- `-nic user` (user-mode NAT, no host forwarding), `virtio-vga`, `qemu-xhci`, `usb-tablet`
- **No physical disk, no host directory share, no block device passthrough**
- Display `none`; QEMU monitor on a UNIX socket for `screendump`/`sendkey`

The GTK window having shown black in earlier runs was not re-tested: `-display none` plus monitor `screendump` produced correct frames throughout, which is the workflow this record recommends.

## Results

| Check | Result | Evidence |
|---|---|---|
| UEFI boot from the ISO | Pass | PBS/serial boot log; Plasma splash captured |
| KDE Plasma desktop | Pass | Screendump: Kavi'ka wallpaper and branding, panel present |
| Kavi'ka Test Centre opens automatically | Pass | Window titled "Kavi'ka OS · Live preview" with the seven-item menu |
| Two virtual desktops defined | Pass | Two desktop indicators in the panel; `kwinrc` has `Number=2` |
| **Meta+F12 workspace switch** | **Pass, both directions** | See pixel measurements below |
| SELinux | **Enforcing** | `getenforce` → `Enforcing` in a Konsole terminal |
| systemd state | `running` | `systemctl is-system-running` |
| Failed units | **0** | `systemctl --list-units --state=failed` → "0 loaded units listed" |
| Hardware report runs in the guest | Pass | `kavika-hardware` printed its JSON inventory and returned to the prompt |
| Guest sees no host disks | Pass | `lsblk` lists only `vda` (16G virtio), `sr0` (QEMU DVD-ROM), `loop0`, `zram0` |
| Guest network | user-mode NAT | NIC configured `user` with no `hostfwd` |

### Meta+F12 evidence

Two screenshots were taken per state with the QEMU monitor `screendump`, then compared with ImageMagick `compare -metric AE`:

| Transition | Differing pixels | Interpretation |
|---|---|---|
| Desktop 1 → press Meta+F12 → Desktop 2 | 361,232 of 1,024,000 (35.3%) | Action occurred: wallpaper and content change |
| Desktop 2 → press Meta+F12 → Desktop 1 | 361,341 (35.3%) | Action occurred again |
| Desktop 1 (original) vs Desktop 1 (returned) | **105** (0.01%) | Returned to the *same* desktop; the 105 px is the clock |

Screenshots also identify the two desktops visually: desktop 1 shows the faint "KAVI'KA / OS" wallpaper with the Test Centre window open; desktop 2 shows the large pale-gold star logo with no window. The return trip restores desktop 1 exactly, so the toggle is not a one-way change and not a window-close artefact.

### Key-name pitfall (worth keeping in the tooling notes)

`sendkey meta-f12` does nothing — QEMU's monitor rejects that key name and the frame is unchanged (96 px, i.e. the clock). The working command is **`sendkey meta_l-f12`**. Anyone scripting this check should use `meta_l`, and should treat "no pixel change" as a failed injection rather than a failed shortcut.

## What this proves and what it does not

**Proves, for this exact ISO hash in a virtual machine:** the image boots to a working KDE desktop through UEFI, the Test Centre opens, two workspaces exist, Meta+F12 switches between them in both directions, SELinux is enforcing, the system reaches `running` with no failed units, the hardware report runs, and the guest had no access to host disks.

**Does not prove:** anything about Surface hardware (graphics, Wi-Fi, audio, camera, touch, pen, sleep, Secure Boot); Windows, Comet or any guest Windows workspace (none is included); four-finger gesture switching (a keyboard shortcut was tested); persistence, installation, update or recovery; or performance under mixed workload. The 4 GiB/2 vCPU guest is not a sizing decision for the Pro 8.

**Still a diagnostic preview**, not an installation release, and not approved for flashing.
