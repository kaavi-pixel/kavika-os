#!/usr/bin/env python3
"""Kavi'ka OS installer pre-flight.

The consent layer between the "Install Kavi'ka OS" entry and Anaconda. It refuses to launch
the installer unless the operator has named the exact target device twice and every safety
check passes, then substitutes that device into the kickstart template and only then runs
the installer.

This module is deliberately importable so the unit tests exercise the refusal logic with
synthetic inventories and no disk access. Importing it performs no destructive action.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

PLACEHOLDER = "@@TARGET_DEVICE@@"
KICKSTART_TEMPLATE = "/usr/lib/kavika/installer/kavika.ks"
INSTALLER_CMD = "/usr/sbin/liveinst"  # the real Fedora live installer; NOT the guarded /usr/bin/liveinst
DEFAULT_MIN_BYTES = 240 * 1024 ** 3   # provisional: the v1 layout totals ~211 GiB, plus headroom


def lsblk_json():
    out = subprocess.run(
        ["lsblk", "-J", "-b", "-o", "name,size,rm,tran,type,mountpoints,model"],
        capture_output=True, text=True)
    out.check_returncode()
    return json.loads(out.stdout)


def whole_disks(blk):
    """Whole-disk block devices only (type == 'disk'), excluding pseudo-disks."""
    excluded_prefixes = ("zram", "loop", "ram", "fd")
    out = []
    for d in blk.get("blockdevices", []):
        name = d.get("name", "")
        if d.get("type") != "disk" or name.startswith(excluded_prefixes):
            continue
        out.append(d)
    return out


def find_device(disks, path):
    name = path.removeprefix("/dev/")
    return next((d for d in disks if d.get("name") == name), None)


def refusals(disks, device, confirm_device, min_bytes, template_text):
    """Return a list of refusal reasons; empty means it is safe to proceed."""
    reasons = []
    if device != confirm_device:
        reasons.append(
            f"--device ({device}) and --confirm-device ({confirm_device}) differ; "
            "nothing will be written")
    dev = find_device(disks, device)
    if dev is None:
        reasons.append(f"{device} is not a whole-disk block device on this system")
        return reasons  # the rest cannot be evaluated without the device record

    mounts = [m for m in (dev.get("mountpoints") or []) if m]
    if mounts:
        reasons.append(f"{device} is mounted ({', '.join(mounts)}); an install target must not be mounted")

    size = int(dev.get("size", 0))
    if size < min_bytes:
        reasons.append(f"{device} is too small ({size} bytes < {min_bytes} bytes minimum)")

    if PLACEHOLDER not in template_text:
        reasons.append(f"the kickstart template is missing the {PLACEHOLDER} placeholder")
    return reasons


def resolve_kickstart(template_text, device):
    if PLACEHOLDER not in template_text:
        raise ValueError(f"kickstart template has no {PLACEHOLDER} placeholder")
    resolved = template_text.replace(PLACEHOLDER, device)
    if PLACEHOLDER in resolved:
        raise ValueError(f"kickstart still contains {PLACEHOLDER} after substitution")
    return resolved


def inventory_report(disks):
    lines = ["Target candidates (whole disks):"]
    for d in disks:
        size_gib = int(d.get("size", 0)) / 1024 ** 3
        model = d.get("model") or ""
        tran = d.get("tran") or ""
        mounts = ",".join(m for m in (d.get("mountpoints") or []) if m)
        lines.append(
            f"  /dev/{d['name']}  {size_gib:>7.0f} GiB  tran={tran or '-'}  "
            f"model={model or '-'}  mounts={mounts or '-'}")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Kavi'ka OS installer pre-flight (consent + safety).")
    ap.add_argument("--device", required=True, help="whole-disk install target, e.g. /dev/sda")
    ap.add_argument("--confirm-device", required=True, help="must be identical to --device")
    ap.add_argument("--min-size", type=int, default=DEFAULT_MIN_BYTES, help="minimum target size in bytes")
    ap.add_argument("--kickstart", default=KICKSTART_TEMPLATE, help="kickstart template path")
    ap.add_argument("--installer-cmd", default=INSTALLER_CMD, help="installer to launch after the checks")
    ap.add_argument("--dry-run", action="store_true", help="run every check and print the plan; write nothing")
    ap.add_argument("--yes", action="store_true", help="required (without --dry-run) to actually launch the installer")
    args = ap.parse_args(argv)

    try:
        template_text = Path(args.kickstart).read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"refusing: kickstart template not found at {args.kickstart} "
              "(run inside the Kavi'ka image, or pass --kickstart <path>)", file=sys.stderr)
        return 2
    disks = whole_disks(lsblk_json())
    reasons = refusals(disks, args.device, args.confirm_device, args.min_size, template_text)

    print(inventory_report(disks))
    if reasons:
        for r in reasons:
            print(f"refusing: {r}", file=sys.stderr)
        return 2

    resolved = resolve_kickstart(template_text, args.device)
    print(f"kickstart resolved for {args.device}")

    if args.dry_run:
        print("--dry-run: all checks passed; nothing was written")
        return 0
    if not args.yes:
        print("refusing: re-run with --yes to launch the installer (a destructive operation)",
              file=sys.stderr)
        return 3

    ks_path = "/run/kavika-install-resolved.ks"
    Path(ks_path).write_text(resolved, encoding="utf-8")
    cmd = [args.installer_cmd, "--kickstart", ks_path]
    print("launching:", " ".join(cmd))
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
