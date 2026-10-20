#!/usr/bin/env python3
"""Boot a Kavi'ka ISO in a disposable KVM guest and capture visual evidence.

This wraps tools/launch-preview-vm-linux.py rather than replacing it: the boot
subcommand loads that module and reuses its checks (ISO hash, /dev/kvm access,
memory budget, empty VM directory) and its QEMU command builder, so the two
tools cannot drift apart. It adds two things the launcher deliberately omits:

  * a QEMU monitor on a UNIX socket inside the VM directory, which provides
    `screendump` (screenshots) and `sendkey` (keystrokes); and
  * the option of a headless display, because the GTK window has been observed
    to show black even when the guest is drawing correctly.

Safety properties are unchanged from the launcher: a new private QCOW2 disk, a
private UEFI variable store, user-mode NAT with no host forwarding, and no
physical disk or shared folder is ever attached.

Usage
-----
    # boot (refuses a hash mismatch or a non-empty VM directory)
    python3 tools/capture-vm-evidence.py boot \
        --iso build/Kavika-OS-0.1.0-Surface-Pro-8-Live-Preview.iso \
        --sha256-file build/Kavika-OS-0.1.0-Surface-Pro-8-Live-Preview.iso.sha256 \
        --vm-dir ~/kavika-vm-test

    python3 tools/capture-vm-evidence.py shot --vm-dir ~/kavika-vm-test before.ppm
    python3 tools/capture-vm-evidence.py key  --vm-dir ~/kavika-vm-test meta_l-f12
    python3 tools/capture-vm-evidence.py shot --vm-dir ~/kavika-vm-test after.ppm
    python3 tools/capture-vm-evidence.py quit --vm-dir ~/kavika-vm-test

Then compare frames, e.g. `compare -metric AE before.ppm after.ppm null:` (or
convert to PNG first). A workspace switch changes roughly a third of the frame;
if almost nothing changes, the keystroke probably never reached the guest.

Keystroke pitfall: the QEMU monitor wants `meta_l-f12`, not `meta-f12`. The
latter is rejected and the screen does not change, which reads exactly like a
broken shortcut. A running QEMU process is not a boot pass either — inspect the
screenshots and the serial log.
"""
import argparse
import importlib.util
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAUNCHER = HERE / "launch-preview-vm-linux.py"

# Characters that need an explicit QEMU key name when typing into the guest.
KEY_ALIASES = {
    " ": "spc", "-": "minus", "=": "equal", ";": "semicolon", ".": "dot",
    "/": "slash", ",": "comma", "'": "apostrophe", "[": "bracket_left",
    "]": "bracket_right", "\\": "backslash", "`": "grave_accent",
}


def load_launcher():
    spec = importlib.util.spec_from_file_location("kavika_launcher", LAUNCHER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def monitor_socket(vm_dir: Path) -> Path:
    return vm_dir / "mon.sock"


def talk(sock_path: Path, lines, settle: float = 1.0):
    """Send monitor commands over the UNIX socket and drain the replies."""
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.settimeout(15)
    client.connect(str(sock_path))
    out = b""
    try:
        time.sleep(0.3)
        for line in lines:
            client.sendall((line + "\n").encode())
            time.sleep(settle)
        client.settimeout(3)
        try:
            while True:
                chunk = client.recv(65536)
                if not chunk:
                    break
                out += chunk
        except socket.timeout:
            pass
    finally:
        client.close()
    return out.decode(errors="replace")


def keys_for(text: str):
    """Translate a string into QEMU monitor key names (one per character)."""
    sequence = []
    for char in text:
        if char == "\n":
            sequence.append("ret")
        elif char.isupper():
            sequence.append("shift-" + char.lower())
        else:
            sequence.append(KEY_ALIASES.get(char, char))
    return sequence


def do_boot(args) -> int:
    L = load_launcher()
    iso = args.iso.resolve(strict=True)
    vm_dir = args.vm_dir.resolve()
    if vm_dir.exists() and any(vm_dir.iterdir()):
        print(f"refusing: {vm_dir} already exists and is not empty", file=sys.stderr)
        return 1
    expected = (args.expected_sha256.lower() if args.expected_sha256
                else L.read_sidecar_hash(args.sha256_file))
    actual = L.digest(iso)
    if actual != expected:
        print(f"refusing: ISO SHA-256 mismatch\n  expected {expected}\n  actual   {actual}",
              file=sys.stderr)
        return 1
    print(f"ISO hash verified: {actual}")
    qemu = shutil.which("qemu-system-x86_64") or shutil.which("qemu-kvm")
    qemu_img = shutil.which("qemu-img")
    if not qemu or not qemu_img:
        print("QEMU not found; on Fedora run: sudo dnf install qemu-kvm qemu-img", file=sys.stderr)
        return 1
    use_kvm = not args.no_kvm
    if use_kvm and not os.access("/dev/kvm", os.R_OK | os.W_OK):
        print("/dev/kvm is missing or not accessible; pass --no-kvm for slow emulation",
              file=sys.stderr)
        return 1
    efi_code = L.first_existing(L.OVMF_CODE_CANDIDATES, os.environ.get("OVMF_CODE"))
    efi_vars_template = L.first_existing(L.OVMF_VARS_CANDIDATES, os.environ.get("OVMF_VARS"))
    guest_mib = L.require_memory_budget(L.mem_available_mib(Path("/proc/meminfo").read_text()))
    if args.guest_mib:
        guest_mib = args.guest_mib
    print(f"memory budget OK ({guest_mib} MiB guest requested)")

    vm_dir.mkdir(parents=True)
    disk = vm_dir / "preview-test.qcow2"
    efi_vars = vm_dir / "efi-vars.fd"
    serial_log = vm_dir / "serial.log"
    sock_path = monitor_socket(vm_dir)
    subprocess.run([qemu_img, "create", "-f", "qcow2", str(disk), "16G"], check=True, capture_output=True)
    shutil.copyfile(efi_vars_template, efi_vars)

    command = L.build_qemu_command(qemu=qemu, iso=iso, disk=disk, efi_code=efi_code,
                                   efi_vars=efi_vars, serial_log=serial_log,
                                   use_kvm=use_kvm, display=args.display, cpus=args.cpus)
    command += ["-monitor", f"unix:{sock_path},server,nowait"]
    (vm_dir / "launch.txt").write_text(
        f"iso={iso}\niso_sha256={actual}\naccel={'kvm' if use_kvm else 'tcg'}\n"
        f"display={args.display}\nmonitor={sock_path}\n"
        "physical_disks=none\nshared_folders=none\nnetwork=user-mode NAT (no hostfwd)\n",
        encoding="utf-8")
    print("command: " + " ".join(command))
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                               stderr=open(vm_dir / "qemu.stderr.log", "wb"), start_new_session=True)
    (vm_dir / "qemu.pid").write_text(str(process.pid), encoding="ascii")
    time.sleep(5)
    if process.poll() is not None:
        print(f"QEMU exited early (status {process.returncode}); see {vm_dir / 'qemu.stderr.log'}",
              file=sys.stderr)
        return 1
    print(f"QEMU running as PID {process.pid}; monitor {sock_path}")
    print("A running process is not a boot pass: take screenshots and check serial.log.")
    return 0


def require_socket(vm_dir: Path) -> Path:
    sock_path = monitor_socket(vm_dir)
    if not sock_path.exists():
        raise SystemExit(f"no monitor socket at {sock_path}; boot the VM with this tool first")
    return sock_path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="action", required=True)

    boot = sub.add_parser("boot", help="start a disposable guest (hash-checked)")
    boot.add_argument("--iso", type=Path, required=True)
    group = boot.add_mutually_exclusive_group(required=True)
    group.add_argument("--expected-sha256")
    group.add_argument("--sha256-file", type=Path)
    boot.add_argument("--vm-dir", type=Path, required=True)
    boot.add_argument("--display", default="none", choices=("gtk", "sdl", "none"))
    boot.add_argument("--cpus", type=int, default=2)
    boot.add_argument("--guest-mib", type=int, default=None)
    boot.add_argument("--no-kvm", action="store_true")
    boot.set_defaults(func=do_boot)

    shot = sub.add_parser("shot", help="screendump the guest to a file")
    shot.add_argument("--vm-dir", type=Path, required=True)
    shot.add_argument("path", type=Path)

    key = sub.add_parser("key", help="send one or more key names (e.g. meta_l-f12)")
    key.add_argument("--vm-dir", type=Path, required=True)
    key.add_argument("keys", nargs="+")

    typ = sub.add_parser("type", help="type a string into the guest")
    typ.add_argument("--vm-dir", type=Path, required=True)
    typ.add_argument("text")

    cmd = sub.add_parser("cmd", help="send a raw monitor command")
    cmd.add_argument("--vm-dir", type=Path, required=True)
    cmd.add_argument("command", nargs="+")

    quitp = sub.add_parser("quit", help="ask the guest to exit")
    quitp.add_argument("--vm-dir", type=Path, required=True)

    args = parser.parse_args(argv)

    if args.action == "boot":
        try:
            return args.func(args)
        except (OSError, ValueError, subprocess.CalledProcessError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    sock_path = require_socket(args.vm_dir.resolve())
    if args.action == "shot":
        talk(sock_path, [f"screendump {args.path.resolve()}"], settle=2.0)
        target = args.path.resolve()
        if not target.exists():
            print(f"screendump failed: {target} was not created", file=sys.stderr)
            return 1
        print(f"screendump -> {target} ({target.stat().st_size} bytes)")
        return 0
    if args.action == "key":
        talk(sock_path, [f"sendkey {k}" for k in args.keys], settle=0.4)
        print("keys sent: " + " ".join(args.keys))
        return 0
    if args.action == "type":
        sequence = keys_for(args.text)
        talk(sock_path, [f"sendkey {k}" for k in sequence], settle=0.03)
        print(f"typed {len(sequence)} keys")
        return 0
    if args.action == "cmd":
        print(talk(sock_path, [" ".join(args.command)], settle=1.0))
        return 0
    if args.action == "quit":
        talk(sock_path, ["quit"], settle=1.0)
        print("quit sent")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
