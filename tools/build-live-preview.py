#!/usr/bin/env python3
"""Build a non-installation Kavi'ka preview from the exact verified Fedora live ISO.

No mount/chroot/installer/root privileges are used. Dracut's existing live-updates
hook applies the appended /updates archive to the RAM-backed live root at boot.
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

BASE_SHA256 = "c8295961d4c41adbf785a31a17c21a971d3b7415fda72dcad0c11c49577bf03a"
BASE_NAME = "Fedora-KDE-Desktop-Live-44-1.7.x86_64.iso"


def digest(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def grub_preview(text):
    if "root=live:CDLABEL=Fedora-KDE-Live-44" not in text:
        raise ValueError("Unexpected upstream boot configuration")
    text = text.replace('set default="1"', 'set default="0"')
    text = text.replace("set timeout=10", "set timeout=5")
    # Keep boot-menu names quote-neutral for future upstream title changes.
    text = text.replace("Fedora-KDE-Desktop-Live", "Kavika OS 0.1.0 - LIVE PREVIEW (no install)")
    # This pinned upstream config nests function definitions inside an if block,
    # rejected by both the booted GRUB and grub-script-check. Define the function
    # at top level while preserving the same platform-specific module choices.
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
            # Serial logging supports a diskless VM smoke test; the display stays active.
            line += " console=tty0 console=ttyS0,115200n8"
        lines.append(line)
    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    base, output = args.base.resolve(), args.output.resolve()
    if output.exists() or base == output:
        p.error("Output must be a new file, never overwrite a device or input.")
    if output.suffix != ".iso" or not output.parent.is_dir():
        p.error("Use an .iso filename in an existing directory.")
    if str(output).startswith("/dev/"):
        p.error("Refusing device output.")
    for tool in ("xorriso", "cpio", "implantisomd5", "grub-script-check"):
        if not shutil.which(tool):
            p.error(f"Missing build tool: {tool}")
    if digest(base) != BASE_SHA256:
        p.error("Base ISO hash mismatch; no output created.")
    repo = Path(__file__).resolve().parents[1]
    source = repo / "image/live-preview/root"
    with tempfile.TemporaryDirectory(prefix="kavika-build-", dir=output.parent) as temp:
        work = Path(temp)
        stage = work / "stage"
        shutil.copytree(source, stage / "updates",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))
        shutil.copy2(repo / "assets/branding/kavi-ka-os-logo.png",
                     stage / "updates/usr/share/kavika/logo.png")
        executable = (
            "usr/local/bin/kavika-hardware", "usr/local/bin/kavika-test-centre",
            "usr/local/bin/kavika-live-session", "usr/bin/liveinst", "usr/bin/plasma-welcome",
        )
        for rel in executable:
            (stage / "updates" / rel).chmod(0o755)
        for path in stage.rglob("*"):
            if not path.is_symlink():
                os.utime(path, (0, 0))
        names = sorted(str(path.relative_to(stage)) for path in stage.rglob("*"))
        cpio = work / "kavika-preview.cpio"
        with cpio.open("wb") as f:
            subprocess.run(["cpio", "--null", "-o", "--format=newc", "--owner=0:0",
                            "--reproducible"], cwd=stage,
                           input=("\0".join(names) + "\0").encode(),
                           stdout=f, check=True)
        grub = work / "grub.cfg"
        subprocess.run(["xorriso", "-osirrox", "on", "-indev", str(base),
                        "-extract", "/boot/grub2/grub.cfg", str(grub)], check=True)
        grub.write_text(grub_preview(grub.read_text()))
        subprocess.run(["grub-script-check", str(grub)], check=True)
        subprocess.run([
            "xorriso", "-indev", str(base), "-outdev", str(output),
            "-map", str(grub), "/boot/grub2/grub.cfg",
            "-map", str(cpio), "/boot/kavika-preview.cpio",
            "-map", str(stage / "updates/usr/share/kavika/START-HERE.txt"), "/KAVIKA-README.txt",
            "-boot_image", "any", "replay", "-commit",
        ], check=True)
        subprocess.run(["implantisomd5", "--force", str(output)], check=True)
        sha = digest(output)
        output.with_suffix(".iso.sha256").write_text(f"{sha}  {output.name}\n")
        manifest = {
            "name": "Kavika OS 0.1.0 Surface Pro 8 live preview",
            "base": BASE_NAME, "base_sha256": BASE_SHA256,
            "output_sha256": sha, "output_bytes": output.stat().st_size,
            "architecture": "x86_64", "installer_supported": False,
            "windows_included": False, "surface_kernel_included": False,
            "persistence_supported": False,
            "logo_sha256": digest(repo / "assets/branding/kavi-ka-os-logo.png"),
            "builder_sha256": digest(Path(__file__)),
            "payload_files": [
                {"path": path.relative_to(stage).as_posix(), "sha256": digest(path)}
                for path in sorted(stage.rglob("*")) if path.is_file()
            ],
        }
        output.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        print(json.dumps({"iso": str(output), "sha256": sha, "bytes": output.stat().st_size}))


if __name__ == "__main__":
    main()
