#!/usr/bin/env python3
"""Create a detached QEMU test clone of the paused Kavi'ka Linux preview."""
import argparse
import ctypes
import hashlib
import json
import shutil
from pathlib import Path
import subprocess
import sys
import time

EXPECTED_ISO_SHA256 = "10074299b974eb005d0a38144d74b0dc02e1fa128684eb0f81b9cc9829a177ac"
EXPECTED_ISO_BYTES = 3370254336
QEMU = Path(r"C:\Program Files\qemu\qemu-system-x86_64.exe")
QEMU_IMG = Path(r"C:\Program Files\qemu\qemu-img.exe")
EFI_CODE = Path(r"C:\Program Files\qemu\share\edk2-x86_64-code.fd")
EFI_VARS_TEMPLATE = Path(r"C:\Program Files\qemu\share\edk2-i386-vars.fd")
VM_NAME = "Kavika-Preview-Test"
def require_memory_budget(available_bytes: int) -> int:
    """Allow at least 1 GiB headroom above the fixed 4-GiB TCG guest allocation."""
    guest_mib = 4096
    minimum_bytes = guest_mib * 1024**2 + 1024**3
    if available_bytes < minimum_bytes:
        raise ValueError("Need at least 5 GiB free host RAM to launch a 4 GiB software-emulated guest")
    return guest_mib


def available_memory_bytes() -> int:
    """Read current free RAM; the emulator needs 4 GiB plus host headroom."""
    class MemoryStatus(ctypes.Structure):
        _fields_ = [("length", ctypes.c_ulong), ("memory_load", ctypes.c_ulong),
                    ("total_phys", ctypes.c_ulonglong), ("avail_phys", ctypes.c_ulonglong),
                    ("total_page_file", ctypes.c_ulonglong), ("avail_page_file", ctypes.c_ulonglong),
                    ("total_virtual", ctypes.c_ulonglong), ("avail_virtual", ctypes.c_ulonglong),
                    ("avail_extended_virtual", ctypes.c_ulonglong)]
    status = MemoryStatus()
    status.length = ctypes.sizeof(status)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        raise OSError("Unable to inspect available host RAM before VM allocation")
    return status.avail_phys


def build_qemu_command(*, iso: Path, disk: Path, efi_vars: Path,
                       qemu: Path, efi_code: Path, serial_log: Path,
                       accel: str = "tcg", display: str = "gtk",
                       stderr_log: Path | None = None) -> list[str]:
    if accel not in {"tcg", "whpx"}:
        raise ValueError("Unsupported QEMU accelerator; choose tcg or whpx")
    command = [str(qemu), "-name", "Kavika-Preview-Test", "-machine", f"q35,accel={accel}",
            "-cpu", "max", "-smp", "2", "-m", "4096",
            "-drive", f"if=pflash,format=raw,readonly=on,file={efi_code}",
            "-drive", f"if=pflash,format=raw,file={efi_vars}",
            "-drive", f"file={disk},format=qcow2,if=virtio",
            "-cdrom", str(iso), "-boot", "menu=on,order=dc",
            "-nic", "user,model=virtio-net-pci", "-display", display,
            "-serial", f"file:{serial_log}", "-no-reboot"]
    if stderr_log is not None:
        command += ["-D", str(stderr_log), "-d", "guest_errors"]
    return command


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", type=Path, required=True)
    parser.add_argument("--vm-dir", type=Path, required=True)
    parser.add_argument("--expected-sha256", default=EXPECTED_ISO_SHA256)
    parser.add_argument("--expected-bytes", type=int, default=EXPECTED_ISO_BYTES)
    parser.add_argument("--accel", choices=("tcg", "whpx"), default="tcg",
                        help="TCG is slow; WHPX should be used only after a successful tiny-guest probe")
    try:
        return run_vm(parser.parse_args())
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        parser.error(str(exc))


def run_vm(args) -> int:
    iso = args.iso.resolve(strict=True)
    vm_dir = args.vm_dir.resolve()
    if not iso.is_file() or iso.suffix.lower() != ".iso":
        raise ValueError("--iso must identify an existing ISO file")
    if vm_dir.exists() and any(vm_dir.iterdir()):
        raise ValueError("VM directory must not already exist or contain data")
    for tool in (QEMU, QEMU_IMG, EFI_CODE, EFI_VARS_TEMPLATE):
        if not tool.is_file():
            raise FileNotFoundError(f"Required QEMU file missing: {tool}")
    if iso.stat().st_size != args.expected_bytes:
        raise ValueError("This is not the project-created Kavi'ka preview ISO (Fedora's base is a different size)")
    actual = digest(iso)
    if actual != args.expected_sha256:
        raise ValueError("ISO SHA-256 does not match the validation record")

    available_bytes = available_memory_bytes()
    try:
        guest_mib = require_memory_budget(available_bytes)
    except ValueError as exc:
        raise ValueError(str(exc)) from exc


    vm_dir.mkdir(parents=True)
    disk = vm_dir / "kavika-preview-test.qcow2"
    efi_vars = vm_dir / "efi-vars.fd"
    qemu_log = vm_dir / "qemu.log"
    manifest = {
        "name": VM_NAME, "purpose": "disposable live-preview validation",
        "iso": str(iso), "iso_bytes": iso.stat().st_size, "iso_sha256": actual,
        "disk": str(disk), "disk_format": "qcow2", "disk_virtual_capacity_gib": 24,
        "ram_mib": guest_mib, "vcpus": 2, "cpu_mode": f"{args.accel} acceleration",
        "firmware": "OVMF UEFI (EDK2 x64 code, firmware variables saved for this VM)", "physical_disk_passthrough": False,
        "minimum_host_free_ram_mib": 5120,
        "network": "user-mode NAT", "shared_folders": False,
        "host_shared_writable_directory": False,
        "windows_included": False,
        "warning": "throwaway empty QCOW2 disk; guest is a Linux diagnostic preview, not a full Windows product test",
    }
    manifest_path = vm_dir / "manifest.json"
    try:
        shutil.copyfile(EFI_VARS_TEMPLATE, efi_vars)
        subprocess.run([str(QEMU_IMG), "create", "-f", "qcow2", str(disk), "24G"],
                       check=True, capture_output=True, text=True)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        command = build_qemu_command(iso=iso, disk=disk, efi_vars=efi_vars,
                                     qemu=QEMU, efi_code=EFI_CODE, serial_log=qemu_log,
                                     accel=args.accel, stderr_log=vm_dir / "qemu.stderr.log")
        print(json.dumps({"vm": VM_NAME, "manifest": str(manifest_path),
                          "disk": str(disk), "iso_sha256": actual,
                          "installed_host_ram_gib": round(available_bytes / 1024**3, 2),
                          "launch": "QEMU GUI launch request submitted; do not treat this as guest boot validation",
                          "command": command}, indent=2))
        # Starting the child and returning lets QEMU keep running independently.
        process = subprocess.Popen(command, cwd=str(vm_dir), stdin=subprocess.DEVNULL,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   creationflags=0x00000200)  # CREATE_NEW_PROCESS_GROUP
        time.sleep(8)
        if process.poll() is not None:
            err_file = vm_dir / "qemu.stderr.log"
            detail = err_file.read_text(errors="replace")[-4000:] if err_file.exists() else "no stderr log"
            raise RuntimeError(f"QEMU exited early with status {process.returncode}: {detail}")
        if qemu_log.exists() and qemu_log.stat().st_size:
            print("QEMU_SERIAL_LOG=" + str(qemu_log))
        print("QEMU_STARTED=True; guest desktop/readiness must be inspected in the VM window")
        return 0
    except Exception:
        # Preserve the isolated VM directory and log for diagnosis; never touch a host disk.
        print(f"VM setup/launch failed. Inspect {vm_dir}", file=sys.stderr)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
