#!/usr/bin/env python3
"""Boot a Kavi'ka diagnostic ISO in a disposable KVM guest on a Linux host.

Intended for the Fedora Surface test machine (Surface Laptop Studio). It never
attaches a physical disk or a shared folder: the guest gets a new private QCOW2
disk, its own UEFI variable store and user-mode NAT. The ISO must match a
SHA-256 you supply (or a `.sha256` sidecar), so an unverified image is refused.

This tests the Linux preview only. It is not the planned Windows workspace.
"""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

GUEST_MIB = 4096
HEADROOM_MIB = 1024
OVMF_CODE_CANDIDATES = (
    "/usr/share/edk2/ovmf/OVMF_CODE.fd",
    "/usr/share/OVMF/OVMF_CODE.fd",
    "/usr/share/OVMF/OVMF_CODE_4M.fd",
    "/usr/share/edk2-ovmf/x64/OVMF_CODE.fd",
)
OVMF_VARS_CANDIDATES = (
    "/usr/share/edk2/ovmf/OVMF_VARS.fd",
    "/usr/share/OVMF/OVMF_VARS.fd",
    "/usr/share/OVMF/OVMF_VARS_4M.fd",
    "/usr/share/edk2-ovmf/x64/OVMF_VARS.fd",
)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_sidecar_hash(sidecar: Path) -> str:
    """First token of a `sha256sum`-style file; must be 64 hex characters."""
    token = sidecar.read_text(encoding="ascii").split()[0].lower()
    if len(token) != 64 or any(ch not in "0123456789abcdef" for ch in token):
        raise ValueError("Checksum file does not start with a 64-character SHA-256")
    return token


def mem_available_mib(meminfo_text: str) -> int:
    for line in meminfo_text.splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) // 1024
    raise ValueError("MemAvailable not found in /proc/meminfo")


def require_memory_budget(available_mib: int) -> int:
    """Guest RAM plus headroom must be free; returns the guest size in MiB."""
    if available_mib < GUEST_MIB + HEADROOM_MIB:
        raise ValueError(
            f"Need at least {(GUEST_MIB + HEADROOM_MIB) // 1024} GiB available host RAM "
            f"for a {GUEST_MIB // 1024} GiB guest; only {available_mib} MiB is available")
    return GUEST_MIB


def first_existing(candidates, env_override=None):
    if env_override and Path(env_override).is_file():
        return Path(env_override)
    for item in candidates:
        if Path(item).is_file():
            return Path(item)
    raise FileNotFoundError("UEFI firmware not found; install edk2-ovmf (Fedora: sudo dnf install edk2-ovmf)")


def build_qemu_command(*, qemu, iso, disk, efi_code, efi_vars, serial_log,
                       use_kvm=True, display="gtk", cpus=2):
    accel = "kvm" if use_kvm else "tcg"
    cpu = "host" if use_kvm else "max"
    return [str(qemu), "-name", "Kavika-Preview-Test",
            "-machine", f"q35,accel={accel}", "-cpu", cpu, "-smp", str(cpus), "-m", str(GUEST_MIB),
            "-drive", f"if=pflash,format=raw,readonly=on,file={efi_code}",
            "-drive", f"if=pflash,format=raw,file={efi_vars}",
            "-drive", f"file={disk},format=qcow2,if=virtio",
            "-cdrom", str(iso), "-boot", "order=d",
            "-nic", "user,model=virtio-net-pci",
            "-device", "virtio-vga", "-device", "qemu-xhci", "-device", "usb-tablet",
            "-display", display, "-serial", f"file:{serial_log}", "-no-reboot"]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", type=Path, required=True)
    parser.add_argument("--vm-dir", type=Path, required=True, help="new, empty directory for the throwaway VM")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--expected-sha256", help="64-character SHA-256 the ISO must have")
    group.add_argument("--sha256-file", type=Path, help="sha256sum-style sidecar for the ISO")
    parser.add_argument("--display", default="gtk", choices=("gtk", "sdl", "none"))
    parser.add_argument("--no-kvm", action="store_true", help="use slow software emulation")
    args = parser.parse_args(argv)
    try:
        return launch(args)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        parser.error(str(exc))


def launch(args) -> int:
    if sys.platform != "linux":
        raise ValueError("This launcher is for Linux hosts; use launch-preview-vm-windows.py on Windows")
    iso = args.iso.resolve(strict=True)
    if not iso.is_file() or iso.suffix.lower() != ".iso":
        raise ValueError("--iso must identify an existing .iso file")
    vm_dir = args.vm_dir.resolve()
    if vm_dir.exists() and any(vm_dir.iterdir()):
        raise ValueError("VM directory must not already exist or contain data")
    expected = args.expected_sha256.lower() if args.expected_sha256 else read_sidecar_hash(args.sha256_file)
    if len(expected) != 64:
        raise ValueError("Expected SHA-256 must be 64 hex characters")

    qemu = shutil.which("qemu-system-x86_64") or shutil.which("qemu-kvm")
    qemu_img = shutil.which("qemu-img")
    if not qemu or not qemu_img:
        raise FileNotFoundError("QEMU not found; on Fedora run: sudo dnf install qemu-kvm qemu-img")
    use_kvm = not args.no_kvm
    if use_kvm and not os.access("/dev/kvm", os.R_OK | os.W_OK):
        raise ValueError("/dev/kvm is missing or not accessible. Add your user to the 'kvm' group "
                         "and log in again, or pass --no-kvm for slow emulation")
    efi_code = first_existing(OVMF_CODE_CANDIDATES, os.environ.get("OVMF_CODE"))
    efi_vars_template = first_existing(OVMF_VARS_CANDIDATES, os.environ.get("OVMF_VARS"))
    require_memory_budget(mem_available_mib(Path("/proc/meminfo").read_text()))

    actual = digest(iso)
    if actual != expected:
        raise ValueError(f"ISO SHA-256 mismatch: expected {expected}, got {actual}; nothing was created")

    vm_dir.mkdir(parents=True)
    disk = vm_dir / "preview-test.qcow2"
    efi_vars = vm_dir / "efi-vars.fd"
    serial_log = vm_dir / "serial.log"
    subprocess.run([qemu_img, "create", "-f", "qcow2", str(disk), "16G"], check=True, capture_output=True)
    shutil.copyfile(efi_vars_template, efi_vars)
    command = build_qemu_command(qemu=qemu, iso=iso, disk=disk, efi_code=efi_code, efi_vars=efi_vars,
                                 serial_log=serial_log, use_kvm=use_kvm, display=args.display)
    (vm_dir / "launch.txt").write_text(
        f"iso={iso}\niso_sha256={actual}\naccel={'kvm' if use_kvm else 'tcg'}\n"
        "physical_disks=none\nshared_folders=none\nnetwork=user-mode NAT\n", encoding="utf-8")
    print("Starting disposable VM (no physical disks, no shared folders):")
    print(" ".join(command))
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                               stderr=open(vm_dir / "qemu.stderr.log", "wb"), start_new_session=True)
    time.sleep(5)
    if process.poll() is not None:
        raise RuntimeError(f"QEMU exited early (status {process.returncode}); see {vm_dir / 'qemu.stderr.log'}")
    print(f"QEMU running as PID {process.pid}. A running process is not a boot pass: inspect the window "
          f"and {serial_log}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
