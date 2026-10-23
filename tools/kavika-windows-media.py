#!/usr/bin/env python3
# kavika-windows-media: build the boot ESP and the answer stick for a Windows 11 KVM install.
#
# Output is two raw images, both plain files. Nothing here touches a physical disk and
# nothing needs root: the FAT partition is written through mtools at an offset, so no
# loop mount is required.
#
#   <out>/esp.img   a 1 GiB GPT disk with one EFI System partition (FAT32, label
#                   KAVIKAESP) carrying the ISO's own boot files and /sources/boot.wim
#   <out>/af.img    a 64 MiB FAT volume (label KAVIKAANSW) with autounattend.xml at its root
#
# WHY AN ESP IMAGE AT ALL
# -----------------------
# Microsoft ISOs are UDF hybrids with no partition table, so OVMF cannot mount an EFI
# System Partition on one and depends on El Torito; that payload (cdboot.efi) hangs under
# OVMF ("UEFI QEMU DVD-ROM ... Time out"). The ISO's own /efi/boot/bootx64.efi is really
# bootmgfw.efi, and that one boots. So Setup is booted from a FAT ESP image attached as
# USB mass storage, and reads its sources from the ISO still attached as -cdrom.
#
# /sources/boot.wim MUST sit on the same volume as bootmgfw.efi: the setup BCD resolves
# [boot] to the volume it was loaded from, and without it boot fails 0xc000000f.
#
# WHY THE ANSWER STICK MUST BE REMOVABLE
# --------------------------------------
# QEMU's usb-storage presents its media as a FIXED disk by default (removable defaults to
# off), and Windows Setup's implicit unattend search does not scan fixed disks. Attach the
# answer stick with usb-storage,removable=on or Setup stops at the language page. The
# launcher does that; this tool only builds the image.
#
# DO NOT REUSE A CAPTURED ESP IMAGE
# ---------------------------------
# Setup rewrites \EFI\Microsoft\Boot\bcd when it services boot files (16,384 -> 45,056
# bytes, pointing at the install that run created). Booting that on a fresh guest gives
# 0xc000000e. Rebuild the ESP from the ISO every run. That is what this tool is for.
#
# See docs/windows-install-recipe.md for the full narrative and the failure modes.

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ANSWER = REPO_ROOT / "image" / "windows" / "autounattend.xml"

ESP_LABEL = "KAVIKAESP"
ANSWER_LABEL = "KAVIKAANSW"
ESP_MIB = 1024
ANSWER_MIB = 64
ESP_OFFSET = "1M"  # the ESP partition starts at LBA 2048 = 1 MiB

# Files the ESP must carry, relative to the ISO root.
ISO_FILES = (
    "efi/boot/bootx64.efi",
    "boot/bcd",
    "boot/boot.sdi",
    "sources/boot.wim",
)
# Directory trees to copy in whole.
ISO_TREES = ("efi/microsoft/boot",)

# Pristine sizes (bytes) taken from a stock Windows 11 ISO. A mismatch means the medium is
# not stock media, and the install will fail in confusing ways, so refuse it.
BCD_EXPECT = {"boot/bcd": 16384, "efi/microsoft/boot/bcd": 16384}
BOOTX64_EXPECT = 3087400  # the ISO's /efi/boot/bootx64.efi (really bootmgfw.efi)


def die(msg: str, code: int = 1):
    print(f"kavika-windows-media: {msg}", file=sys.stderr)
    raise SystemExit(code)


def which(name: str) -> str | None:
    return shutil.which(name)


def require_tools(names) -> dict:
    found = {}
    missing = []
    for n in names:
        p = which(n)
        if p:
            found[n] = p
        else:
            missing.append(n)
    if missing:
        die(
            "missing required tool(s): "
            + ", ".join(missing)
            + "\n  install: mtools (mformat/mcopy), parted, dosfstools (mkfs.vfat), and 7zip (7z)"
            + " or libarchive (bsdtar)",
        )
    return found


def run(cmd, **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, **kw)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_iso(iso: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    if which("7z"):
        # 7z takes a path list; a directory prefix extracts that tree.
        run(
            [
                "7z",
                "x",
                "-y",
                "-bso0",
                "-bsp0",
                f"-o{dest}",
                str(iso),
                *ISO_FILES,
                *ISO_TREES,
            ]
        )
    else:
        run(["bsdtar", "-xf", str(iso), "-C", str(dest), *ISO_FILES, *ISO_TREES])


def verify_extracted(tmp: Path) -> None:
    for rel, size in BCD_EXPECT.items():
        p = tmp / rel
        if not p.is_file():
            die(f"ISO did not yield {rel}")
        got = p.stat().st_size
        if got != size:
            die(f"{rel} is {got} bytes, expected {size} - not stock Windows 11 media")
    b = tmp / "efi/boot/bootx64.efi"
    if not b.is_file():
        die("ISO did not yield efi/boot/bootx64.efi")
    if b.stat().st_size != BOOTX64_EXPECT:
        die(
            f"efi/boot/bootx64.efi is {b.stat().st_size} bytes, expected {BOOTX64_EXPECT}"
            " - not stock Windows 11 media",
        )
    wim = tmp / "sources/boot.wim"
    if not wim.is_file() or wim.stat().st_size < 100 * 1024 * 1024:
        die("ISO did not yield a plausible sources/boot.wim")


def build_esp(esp: Path, tmp: Path, tools: dict, esp_mib: int) -> None:
    if esp.exists():
        esp.unlink()
    # 1 GiB, a GPT, one ESP partition. parted writes the table straight into the file.
    run(["truncate", "-s", f"{esp_mib}M", str(esp)])
    run(
        [
            tools["parted"],
            "-s",
            str(esp),
            "mklabel",
            "gpt",
            "mkpart",
            ESP_LABEL,
            "fat32",
            ESP_OFFSET,
            "100%",
            "set",
            "1",
            "esp",
            "on",
        ]
    )
    # FAT32 at the partition offset, via mtools @@offset (no root, no loop mount).
    spec = f"{esp}@@{ESP_OFFSET}"
    run(["mformat", "-F", "-i", spec, "-v", ESP_LABEL, "::"])
    for d in ("::/efi", "::/efi/boot", "::/efi/microsoft", "::/boot", "::/sources"):
        run(["mmd", "-i", spec, d])
    run(["mcopy", "-i", spec, str(tmp / "efi/boot/bootx64.efi"), "::/efi/boot/"])
    # The whole microsoft/boot tree (BCD, boot.stl, cdboot*, cipolicies, fonts, ...).
    run(["mcopy", "-s", "-i", spec, str(tmp / "efi/microsoft/boot"), "::/efi/microsoft/"])
    run(["mcopy", "-i", spec, str(tmp / "boot/bcd"), "::/boot/"])
    run(["mcopy", "-i", spec, str(tmp / "boot/boot.sdi"), "::/boot/"])
    run(["mcopy", "-i", spec, str(tmp / "sources/boot.wim"), "::/sources/"])


def build_answer_stick(af: Path, answer: Path, answer_mib: int) -> None:
    if af.exists():
        af.unlink()
    run(["truncate", "-s", f"{answer_mib}M", str(af)])
    # A plain FAT volume (superfloppy), exactly as the recipe describes.
    run(["mkfs.vfat", "-F", "32", "-n", ANSWER_LABEL, str(af)])
    run(["mcopy", "-i", str(af), str(answer), "::/autounattend.xml"])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Build the boot ESP and answer stick for a Windows 11 KVM install.",
    )
    ap.add_argument("--iso", type=Path, required=True, help="the Windows 11 ISO")
    ap.add_argument("--out-dir", type=Path, required=True, help="where esp.img and af.img are written")
    ap.add_argument("--answer", type=Path, default=DEFAULT_ANSWER, help="autounattend.xml")
    ap.add_argument("--esp-mib", type=int, default=ESP_MIB)
    ap.add_argument("--answer-mib", type=int, default=ANSWER_MIB)
    ap.add_argument("--expected-sha256", default=None, help="pin the ISO by hash")
    ap.add_argument("--dry-run", action="store_true", help="report and stop before writing")
    args = ap.parse_args(argv)

    iso = args.iso.expanduser()
    if not iso.is_file():
        die(f"ISO not found: {iso}")
    answer = args.answer.expanduser()
    if not answer.is_file():
        die(f"answer file not found: {answer}")

    if args.expected_sha256:
        got = sha256_file(iso)
        if got.lower() != args.expected_sha256.lower():
            die(f"ISO sha256 mismatch:\n  got  {got}\n  want {args.expected_sha256}")

    out = args.out_dir.expanduser()
    esp = out / "esp.img"
    af = out / "af.img"
    print(f"ISO          {iso} ({iso.stat().st_size} bytes)")
    print(f"answer file  {answer}")
    print(f"esp.img      {esp} ({args.esp_mib} MiB, GPT, ESP/FAT32, label {ESP_LABEL})")
    print(f"af.img       {af} ({args.answer_mib} MiB, FAT32, label {ANSWER_LABEL})")

    if args.dry_run:
        print("dry run: nothing written")
        return 0

    tools = require_tools(["parted", "mformat", "mcopy", "mmd", "mkfs.vfat", "truncate"])
    out.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="kavika-winmedia-") as td:
        tmp = Path(td)
        print("extracting boot files from the ISO ...")
        extract_iso(iso, tmp)
        verify_extracted(tmp)
        print("building esp.img ...")
        build_esp(esp, tmp, tools, args.esp_mib)
        print("building af.img ...")
        build_answer_stick(af, answer, args.answer_mib)

    print("done.")
    print(f"  {esp}")
    print(f"  {af}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
