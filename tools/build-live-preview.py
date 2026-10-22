#!/usr/bin/env python3
"""Build the Kavi'ka diagnostic live preview as a separate ISO using xorriso.

This is not a Windows installer or the full Linux/Windows product. The exact
output must pass the disposable UEFI VM gate before any physical-media test.
Requires Linux, Python 3.11+, pycdlib 1.22+, xorriso, cpio, grub-script-check,
and implantisomd5. The source ISO is never mounted or modified.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time

BASE_SHA256 = "c8295961d4c41adbf785a31a17c21a971d3b7415fda72dcad0c11c49577bf03a"
BASE_NAME = "Fedora-KDE-Desktop-Live-44-1.7.x86_64.iso"

# Fedora packages the GRUB check as `grub2-script-check` (from grub2-tools) while
# upstream and other distributions use `grub-script-check`. Accept either name so
# a stock Fedora host does not need a shim.
GRUB_CHECK_CANDIDATES = ("grub-script-check", "grub2-script-check")


def grub_script_check():
    """Path to the GRUB configuration checker, or None when neither name exists."""
    for candidate in GRUB_CHECK_CANDIDATES:
        found = shutil.which(candidate)
        if found:
            return found
    return None


def normalize_shell_payload(data: bytes) -> bytes:
    """Normalize Windows CRLF/CR to Unix LF in overlay shell scripts."""
    return data.replace(bytes([13, 10]), bytes([10])).replace(bytes([13]), bytes([10]))


def normalize_payload_tree(root: Path) -> None:
    """Normalize CRLF/CR to LF in every text file of the overlay (configs, desktop
    entries and scripts). A stray CR corrupts KDE config values such as
    Number=2, so this must cover more than the shell scripts. Binary files
    (anything containing NUL bytes, e.g. PNG) are left byte-identical."""
    for item in sorted(root.rglob("*")):
        if item.is_file() and not item.is_symlink():
            data = item.read_bytes()
            if b"\x00" not in data:
                fixed = normalize_shell_payload(data)
                if fixed != data:
                    item.write_bytes(fixed)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def grub_preview(text: str) -> str:
    if "root=live:CDLABEL=Fedora-KDE-Live-44" not in text:
        raise ValueError("Unexpected upstream Fedora GRUB configuration")
    text = text.replace('set default="1"', 'set default="0"')
    text = text.replace("set timeout=10", "set timeout=5")
    text = text.replace("Fedora-KDE-Desktop-Live", "Kavika OS 0.1.0 - LIVE PREVIEW (no install)")
    if "\tfunction load_video {" in text:
        text, count = re.subn(
            r'if \[ "\$grub_platform" == "efi" \]; then\n.*?\nfi\n',
            '''function load_video {
    if [ "$grub_platform" == "efi" ]; then
        insmod efi_gop
        insmod efi_uga
        insmod video_bochs
        insmod video_cirrus
    fi
    insmod all_video
}
if [ "$grub_platform" == "efi" ]; then
    set basicgfx="nomodeset"
else
    set basicgfx="nomodeset vga=791"
fi
''', text, count=1, flags=re.S)
        if count != 1:
            raise ValueError("Could not normalize upstream GRUB video function")
    lines = []
    for line in text.splitlines():
        if line.strip().startswith("initrd "):
            line += " ($root)/boot/kavika-preview.cpio"
        if line.strip().startswith("linux "):
            line += " console=tty0 console=ttyS0,115200n8"
        lines.append(line)
    return "\n".join(lines) + "\n"


def extract_grub(base: Path, destination: Path) -> None:
    import pycdlib
    iso = pycdlib.PyCdlib()
    iso.open(str(base))
    try:
        with iso.open_file_from_iso(iso_path="/BOOT/GRUB2/GRUB.CFG;1") as source:
            with destination.open("wb") as target:
                shutil.copyfileobj(source, target, length=1024 * 1024)
    finally:
        iso.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True, help="verified Fedora KDE 44 x86_64 ISO")
    parser.add_argument("--output", type=Path, required=True, help="new .iso output path")
    args = parser.parse_args()
    base = args.base.resolve(strict=True)
    output = args.output.resolve()
    if not base.is_file() or base.suffix.lower() != ".iso":
        parser.error("--base must be an existing ISO file")
    if output.exists() or output == base or str(output).startswith("/dev/"):
        parser.error("--output must be a new regular file, never a device or existing file")
    if output.suffix.lower() != ".iso" or not output.parent.is_dir():
        parser.error("--output must be a new .iso in an existing directory")
    for tool in ("xorriso", "cpio", "implantisomd5"):
        if shutil.which(tool) is None:
            parser.error(f"Missing builder tool: {tool}")
    grub_check = grub_script_check()
    if grub_check is None:
        parser.error("Missing builder tool: grub-script-check "
                     "(on Fedora this is grub2-script-check, from grub2-tools)")
    base_hash = digest(base)
    if base_hash != BASE_SHA256:
        parser.error("Fedora input ISO SHA-256 mismatch; no output was created")

    import pycdlib  # noqa: F401
    repo = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="kavika-build-", dir=output.parent) as temp_dir:
        work = Path(temp_dir)
        stage = work / "stage"
        payload = stage / "updates"
        shutil.copytree(repo / "image/live-preview/root", payload,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))
        logo = repo / "assets/branding/kavi-ka-os-logo.png"
        shutil.copy2(logo, payload / "usr/share/kavika/logo.png")
        # Ship the Windows guest launcher inside the image so the Windows workspace
        # has its plumbing; the source of truth stays tools/launch-windows-vm-linux.py.
        launcher_dst = payload / "usr/local/lib/kavika/launch-windows-vm-linux.py"
        launcher_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(repo / "tools/launch-windows-vm-linux.py", launcher_dst)
        normalize_payload_tree(payload)
        for relative in ("usr/local/bin/kavika-hardware", "usr/local/bin/kavika-test-centre",
                         "usr/local/bin/kavika-live-session",
                         "usr/local/bin/kavika-windows-workspace",
                         "usr/local/lib/kavika/launch-windows-vm-linux.py",
                         "usr/bin/liveinst", "usr/bin/plasma-welcome"):
            (payload / relative).chmod(0o755)
        for item in stage.rglob("*"):
            if not item.is_symlink():
                os.utime(item, (0, 0))

        entries = sorted(item.relative_to(stage).as_posix() for item in stage.rglob("*"))
        cpio_path = work / "kavika-preview.cpio"
        with cpio_path.open("wb") as archive:
            subprocess.run(["cpio", "--null", "-o", "--format=newc", "--owner=0:0", "--reproducible"],
                           cwd=stage, input=("\0".join(entries) + "\0").encode(),
                           stdout=archive, check=True)

        upstream_grub = work / "upstream-grub.cfg"
        extract_grub(base, upstream_grub)
        grub = work / "grub.cfg"
        grub.write_text(grub_preview(upstream_grub.read_text(encoding="utf-8")), encoding="utf-8")
        subprocess.run([grub_check, str(grub)], check=True)

        subprocess.run(["xorriso", "-indev", str(base), "-outdev", str(output),
                        "-map", str(grub), "/boot/grub2/grub.cfg",
                        "-map", str(cpio_path), "/boot/kavika-preview.cpio",
                        "-map", str(payload / "usr/share/kavika/START-HERE.txt"),
                        "/KAVIKA-README.txt", "-boot_image", "any", "replay", "-commit"], check=True)
        subprocess.run(["implantisomd5", "--force", str(output)], check=True)
        sha = digest(output)
        manifest = {
            "name": "Kavika OS 0.1.0 Surface live diagnostic preview (Pro 8 target, Laptop Studio test machine)",
            "base": BASE_NAME, "base_sha256": base_hash,
            "output_sha256": sha, "output_bytes": output.stat().st_size,
            "architecture": "x86_64", "installer_supported": False,
            "windows_included": False, "surface_kernel_included": False,
            "persistence_supported": False,
            "logo_sha256": digest(logo), "builder_sha256": digest(Path(__file__)),
            "payload_files": [{"path": item.relative_to(payload).as_posix(), "sha256": digest(item)}
                              for item in sorted(payload.rglob("*")) if item.is_file()],
            "build_method": "xorriso hybrid/UEFI replay with initramfs cpio overlay",
            "build_time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        output.with_suffix(".iso.sha256").write_text(f"{sha}  {output.name}\n", encoding="ascii")
        output.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"iso": str(output), "sha256": sha, "bytes": output.stat().st_size}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
