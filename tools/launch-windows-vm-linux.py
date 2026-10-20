#!/usr/bin/env python3
"""Boot a full Windows 11 guest under QEMU/KVM on a Linux host.

This is the feasibility harness for the product's Windows side: the goal is to
find out whether a general-purpose Windows 11 guest runs on this hardware, not to
ship anything. It deliberately does NOT restrict what can be installed inside
Windows, and it does not fetch, bundle or activate Windows.

Safety, mirroring tools/launch-preview-vm-linux.py:

  * you supply the Windows ISO; nothing is downloaded, and no key is stored here
  * the guest gets a NEW private QCOW2 disk, its own UEFI variable store and its
    own TPM state directory
  * networking is user-mode NAT only, with no host forwarding by default
  * no physical disk, no block device, no shared host folder is ever attached
  * nothing is written outside --vm-dir, and the directory must be new or empty

Hardware presented for a first boot without extra drivers: NVMe system disk,
Intel e1000e NIC, standard VGA, xHCI plus a USB tablet. Those are the devices
Windows 11 Setup has in-box drivers for, which is why virtio is not used by
default. Pass --virtio-iso to attach a virtio-win CD once you want virtio
devices, and see --help for the switching options.

Usage
-----
    # dry run first: prints the plan and the full QEMU command, creates nothing
    python3 tools/launch-windows-vm-linux.py --iso /path/Win11.iso \
        --vm-dir ~/kavika-win11-test --dry-run

    python3 tools/launch-windows-vm-linux.py --iso /path/Win11.iso \
        --vm-dir ~/kavika-win11-test --guest-mib 6144 --cpus 4

Then connect to it with the QEMU monitor or a viewer; use --display gtk for a
window, or --display none with --monitor for headless capture as in
tools/capture-vm-evidence.py.
"""
import argparse
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

OVMF_CODE_CANDIDATES = (
    "/usr/share/edk2/ovmf/OVMF_CODE.fd",
    "/usr/share/OVMF/OVMF_CODE.fd",
    "/usr/share/OVMF/OVMF_CODE_4M.fd",
)
OVMF_VARS_CANDIDATES = (
    "/usr/share/edk2/ovmf/OVMF_VARS.fd",
    "/usr/share/OVMF/OVMF_VARS.fd",
    "/usr/share/OVMF/OVMF_VARS_4M.fd",
)
# Windows 11 wants 4 GiB minimum and 64 GB of disk for a comfortable install.
DEFAULT_GUEST_MIB = 6144
DEFAULT_DISK_GIB = 80
HEADROOM_MIB = 2048


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def mem_available_mib() -> int:
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) // 1024
    raise ValueError("MemAvailable not found in /proc/meminfo")


def first_existing(candidates, env_override=None) -> Path:
    if env_override and Path(env_override).is_file():
        return Path(env_override)
    for item in candidates:
        if Path(item).is_file():
            return Path(item)
    raise FileNotFoundError(
        "UEFI firmware not found; on Fedora: sudo dnf install edk2-ovmf")


def require(name: str) -> str:
    found = shutil.which(name)
    if not found:
        raise FileNotFoundError(f"{name} not found on PATH")
    return found


def build_command(*, qemu, iso, disk, efi_code, efi_vars, tpm_sock, serial_log,
                  guest_mib, cpus, display, virtio_iso=None, hostfwd=None,
                  with_net=True):
    command = [
        qemu, "-name", "Kavika-Windows11-Feasibility",
        "-machine", "q35,accel=kvm", "-cpu", "host", "-smp", str(cpus),
        "-m", str(guest_mib),
        "-drive", f"if=pflash,format=raw,readonly=on,file={efi_code}",
        "-drive", f"if=pflash,format=raw,file={efi_vars}",
        # NVMe system disk: Windows 11 Setup has an in-box NVMe driver, so no
        # driver CD is needed for the first boot.
        "-drive", f"file={disk},format=qcow2,if=none,id=nvme0",
        "-device", "nvme,drive=nvme0,serial=KAVIKA0000000001",
        # TPM 2.0, required by Windows 11.
        "-chardev", f"socket,id=chrtpm,path={tpm_sock}",
        "-tpmdev", "emulator,id=tpm0,chardev=chrtpm",
        "-device", "tpm-tis,tpmdev=tpm0",
        "-device", "VGA", "-device", "qemu-xhci", "-device", "usb-tablet",
        "-cdrom", str(iso), "-boot", "order=d",
        "-serial", f"file:{serial_log}", "-no-reboot",
    ]
    if with_net:
        # e1000e has an in-box Windows driver; virtio-net would need virtio-win.
        nic = "user,model=e1000e"
        if hostfwd:
            nic += f",hostfwd={hostfwd}"
        command += ["-nic", nic]
    if virtio_iso:
        command += ["-drive", f"file={virtio_iso},media=cdrom,readonly=on"]
    command += ["-display", display]
    return command


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--iso", type=Path, required=True,
                        help="your own Windows 11 ISO; nothing is downloaded")
    parser.add_argument("--vm-dir", type=Path, required=True,
                        help="new or empty directory for this guest")
    parser.add_argument("--expected-sha256", default=None,
                        help="optional: refuse to boot if the ISO differs")
    parser.add_argument("--guest-mib", type=int, default=DEFAULT_GUEST_MIB)
    parser.add_argument("--disk-gib", type=int, default=DEFAULT_DISK_GIB)
    parser.add_argument("--cpus", type=int, default=4)
    parser.add_argument("--display", default="gtk", choices=("gtk", "sdl", "none"))
    parser.add_argument("--virtio-iso", type=Path, default=None,
                        help="optional virtio-win CD to attach for virtio devices")
    parser.add_argument("--hostfwd", default=None,
                        help="optional host->guest forward, e.g. tcp::3389-:3389; off by default")
    parser.add_argument("--no-net", action="store_true", help="no NIC at all")
    parser.add_argument("--monitor", action="store_true",
                        help="add a monitor socket at <vm-dir>/mon.sock")
    parser.add_argument("--dry-run", action="store_true",
                        help="run every check, print the command, create nothing")
    args = parser.parse_args(argv)

    if sys.platform != "linux":
        parser.error("this launcher is for Linux hosts with KVM")

    iso = args.iso.resolve(strict=False)
    if not iso.is_file():
        parser.error(f"Windows ISO not found: {iso}")
    if iso.suffix.lower() != ".iso":
        parser.error("--iso must be an .iso file")
    if args.expected_sha256:
        actual = digest(iso)
        if actual != args.expected_sha256.lower():
            parser.error(f"ISO SHA-256 mismatch: expected {args.expected_sha256}, got {actual}")
        print(f"ISO hash verified: {actual}")
    if args.virtio_iso and not args.virtio_iso.resolve().is_file():
        parser.error(f"virtio ISO not found: {args.virtio_iso}")

    vm_dir = args.vm_dir.resolve()
    if vm_dir.exists() and any(vm_dir.iterdir()):
        parser.error(f"VM directory must be new or empty: {vm_dir}")

    qemu = require("qemu-system-x86_64")
    qemu_img = require("qemu-img")
    swtpm = require("swtpm")
    if not os.access("/dev/kvm", os.R_OK | os.W_OK):
        parser.error("/dev/kvm is missing or not accessible; add your user to the 'kvm' group")
    efi_code = first_existing(OVMF_CODE_CANDIDATES, os.environ.get("OVMF_CODE"))
    efi_vars_template = first_existing(OVMF_VARS_CANDIDATES, os.environ.get("OVMF_VARS"))

    needed = args.guest_mib + HEADROOM_MIB
    available = mem_available_mib()
    if available < needed:
        parser.error(f"need about {needed} MiB free RAM for a {args.guest_mib} MiB guest "
                     f"plus headroom; only {available} MiB is available")

    if args.dry_run:
        print("host checks passed:")
        print(f"  qemu        {qemu}")
        print(f"  swtpm       {swtpm}")
        print(f"  uefi code   {efi_code}")
        print(f"  uefi vars   {efi_vars_template}")
        print(f"  free RAM    {available} MiB (guest {args.guest_mib} MiB)")
        print(f"  iso         {iso}")
        print(f"  vm dir      {vm_dir} (would be created)")
        print(f"  disk        {args.disk_gib} GiB new QCOW2")
        print(f"  network     {'none' if args.no_net else 'user-mode NAT' + (f', hostfwd {args.hostfwd}' if args.hostfwd else ', no forwarding')}")
        print("  physical disks: none    shared host folders: none")
        planned = build_command(
            qemu=qemu, iso=iso, disk=vm_dir / "windows11.qcow2", efi_code=efi_code,
            efi_vars=vm_dir / "efi-vars.fd", tpm_sock=vm_dir / "tpm/swtpm.sock",
            serial_log=vm_dir / "serial.log", guest_mib=args.guest_mib, cpus=args.cpus,
            display=args.display, virtio_iso=args.virtio_iso, hostfwd=args.hostfwd,
            with_net=not args.no_net)
        if args.monitor:
            planned += ["-monitor", f"unix:{vm_dir / 'mon.sock'},server,nowait"]
        print("would run: " + " ".join(planned))
        print("--dry-run: nothing was created")
        return 0

    vm_dir.mkdir(parents=True)
    disk = vm_dir / "windows11.qcow2"
    efi_vars = vm_dir / "efi-vars.fd"
    serial_log = vm_dir / "serial.log"
    tpm_dir = vm_dir / "tpm"
    tpm_dir.mkdir()
    tpm_sock = tpm_dir / "swtpm.sock"

    subprocess.run([qemu_img, "create", "-f", "qcow2", str(disk), f"{args.disk_gib}G"],
                   check=True, capture_output=True)
    shutil.copyfile(efi_vars_template, efi_vars)
    subprocess.run([swtpm, "socket", "--tpmstate", f"dir={tpm_dir}",
                    "--ctrl", f"type=unixio,path={tpm_sock}", "--tpm2",
                    "--log", f"file={tpm_dir}/swtpm.log", "--daemon"],
                   check=True)

    command = build_command(qemu=qemu, iso=iso, disk=disk, efi_code=efi_code,
                            efi_vars=efi_vars, tpm_sock=tpm_sock, serial_log=serial_log,
                            guest_mib=args.guest_mib, cpus=args.cpus, display=args.display,
                            virtio_iso=args.virtio_iso, hostfwd=args.hostfwd,
                            with_net=not args.no_net)
    if args.monitor:
        command += ["-monitor", f"unix:{vm_dir / 'mon.sock'},server,nowait"]
    (vm_dir / "launch.txt").write_text(
        f"iso={iso}\nguest_mib={args.guest_mib}\ncpus={args.cpus}\ndisk_gib={args.disk_gib}\n"
        f"accel=kvm\ntpm=swtpm (tpm2, state in {tpm_dir})\n"
        "physical_disks=none\nshared_folders=none\n"
        f"network={'none' if args.no_net else 'user-mode NAT'}\n"
        "note=Windows licence and activation are not handled by this tool\n",
        encoding="utf-8")

    print("starting Windows 11 feasibility guest (no physical disks, no shared folders)")
    print("command: " + " ".join(command))
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                               stderr=open(vm_dir / "qemu.stderr.log", "wb"),
                               start_new_session=True)
    (vm_dir / "qemu.pid").write_text(str(process.pid), encoding="ascii")
    print(f"QEMU running as PID {process.pid}")
    print(f"A running process is not a boot pass: inspect the display and {serial_log}.")
    print(f"Remember to stop swtpm when finished (its state is in {tpm_dir}).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
