# Kavi'ka: Surface Laptop Studio preflight evidence, 20 October 2026

Read-only output of `tools/surface-fedora-preflight.sh`, run on the Surface Laptop Studio
(Fedora 44, kernel 6.19.10-300.fc44, Wayland) on 20 October 2026.
The script installs nothing, changes no setting and writes no files.
Reviewed before committing: no serial numbers, UUIDs, MAC or IP addresses, usernames, keys or user files appear below.

Interpreting it:
- This is inventory only. It is **not** a Kavi'ka or Windows acceptance pass, and no guest or ISO was booted.
- Laptop Studio results are evidence for the Surface Pro 8, never proof.
- `MemAvailable` is a snapshot, not a reservation for a guest.
- Secure Boot is disabled and the platform is in **Setup Mode**; nothing was changed and no firmware setting was touched.
- `virt-manager` is absent and libvirt is inactive. The direct-QEMU launcher (`tools/launch-preview-vm-linux.py`) does not need either.
- No touchscreen or pen input device is reported, which is consistent with the stock kernel lacking linux-surface support.

Result summary: **KVM usable** — `/dev/kvm` is accessible to the user, `kvm_intel` is loaded, `qemu-system-x86_64`/`qemu-img`/`virsh`/`swtpm` and both OVMF firmware files are present.

```text
== Kavi'ka Fedora test-machine preflight ==
date_utc: 2026-10-20T00:38:11Z
os: Fedora Linux 44 (Workstation Edition)
kernel: 6.19.10-300.fc44.x86_64
session: wayland

== Virtualisation readiness ==
cpu_virtualisation_flag: yes
kvm_device: present, usable by this user
kernel_module: kvm_intel
kernel_module: kvm
tool_qemu-system-x86_64: installed
tool_qemu-img: installed
tool_virsh: installed
tool_virt-manager: missing
tool_swtpm: installed
firmware_OVMF_CODE.fd: present
firmware_OVMF_VARS.fd: present
libvirt: not running

== Resources ==
MemTotal: 15.4 GiB
MemAvailable: 7.8 GiB
disk: Mounted on  Size Avail
disk: /           235G  203G
disk: /home       235G  203G

== Secure Boot / TPM ==
secure_boot: SecureBoot disabled
secure_boot: Platform is in Setup Mode
tpm: present

== Kavi'ka hardware report (JSON) ==
{
  "preview": "Kavika 0.2.0 diagnostic report",
  "target": {
    "matched": true,
    "id": "surface-laptop-studio",
    "name": "Surface Laptop Studio",
    "role": "test machine (runs Fedora; has a KVM-capable Intel CPU)",
    "upstream_notes": [
      "Touchscreen, pen and slate/tablet mode: listed as needing the linux-surface kernel.",
      "Touchpad: may need a libinput quirk (see the linux-surface wiki).",
      "Wi-Fi, Bluetooth, speakers, suspend and cameras: listed as supported upstream."
    ]
  },
  "system_vendor": "Microsoft Corporation",
  "system_model": "Surface Laptop Studio",
  "firmware_version": "33.104.143",
  "firmware_date": "06/30/2026",
  "architecture": "x86_64",
  "kernel": "6.19.10-300.fc44.x86_64",
  "cpu_model": "11th Gen Intel(R) Core(TM) i5-11300H @ 3.10GHz",
  "logical_cpus": 8,
  "system_reported_memory_kib": 16171236,
  "cpu_virtualisation_flag": true,
  "kvm_device_exists": true,
  "kvm_accessible_to_current_user": true,
  "uefi_boot": true,
  "secure_boot_enabled": false,
  "tpm_present": true,
  "graphics_controllers": [
    "00:02.0 VGA compatible controller: Intel Corporation TigerLake-LP GT2 [Iris Xe Graphics] (rev 01)"
  ],
  "display_panels": [
    {
      "connector": "eDP-1",
      "first_mode": "2400x1600"
    }
  ],
  "disks": [
    {
      "name": "sda",
      "size": 1000204885504,
      "type": "disk",
      "tran": "usb",
      "rm": false,
      "ro": false,
      "model": "One Touch w/PW"
    },
    {
      "name": "zram0",
      "size": 8589934592,
      "type": "disk",
      "tran": null,
      "rm": false,
      "ro": false,
      "model": null
    },
    {
      "name": "nvme0n1",
      "size": 255060320256,
      "type": "disk",
      "tran": "nvme",
      "rm": false,
      "ro": false,
      "model": "HFM256GD3GX013N"
    }
  ],
  "wireless_interfaces": [
    "wlp242s0"
  ],
  "bluetooth_controllers": 1,
  "input": {
    "has_keyboard": true,
    "has_touchpad": true,
    "has_touchscreen": false,
    "has_pen": false
  },
  "audio_cards": [
    "HDA-Intel"
  ],
  "video_capture_devices": 4,
  "battery": {
    "present": true,
    "percent": 45,
    "status": "Charging"
  },
  "surface_kernel_modules": [
    "surface_aggregator",
    "surface_aggregator_registry",
    "surface_aggregator_tabletsw",
    "surface_battery",
    "surface_charger",
    "surface_gpe",
    "surface_hid",
    "surface_hid_core",
    "surface_platform_profile",
    "surfacepro3_button"
  ],
  "session_type": "wayland",
  "limitations": [
    "This is inventory, not a hardware or Windows-workspace acceptance pass.",
    "No serial numbers, UUIDs, usernames, MACs, IP addresses, EDID, keys or user files are collected.",
    "Upstream notes come from the linux-surface device matrix and are not verified on this device.",
    "Windows and Comet are not installed in this preview."
  ]
}

== Notes ==
- This is inventory, not a Windows or Kavi'ka acceptance pass.
- The Laptop Studio is a test machine; results are evidence only for the Surface Pro 8, not proof.
- Nothing here changed the machine. Review the output before sharing it.
```
