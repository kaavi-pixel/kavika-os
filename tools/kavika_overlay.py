#!/usr/bin/env python3
"""Shared builder for the Kavi'ka overlay (the delta between stock Fedora KDE and Kavi'ka OS).

Both the live-preview and the netinst-install builders must ship the SAME overlay so the
installed system's Kavi'ka identity matches the live preview. This module assembles the
overlay payload tree (image/live-preview/root plus the logo, the Windows guest launcher and
the installer files) and can emit a clean, root-relative cpio of it.
"""
import os
import shutil
import subprocess
from pathlib import Path

_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo")

_EXECUTABLES = (
    "usr/local/bin/kavika-hardware",
    "usr/local/bin/kavika-test-centre",
    "usr/local/bin/kavika-live-session",
    "usr/local/bin/kavika-windows-workspace",
    "usr/local/bin/kavika-windows-provision",
    "usr/local/bin/kavika-windows-optin",
    "usr/local/bin/kavika-gnome-session-setup",
    "usr/local/lib/kavika/launch-windows-vm-linux.py",
    "usr/local/lib/kavika/kavika-windows-media.py",
    "usr/local/sbin/kavika-install",
    "usr/bin/liveinst",
    "usr/bin/plasma-welcome",
)


_KDE_ONLY = (
    "etc/skel/.config/kwinrc",
    "etc/skel/.config/kded_device_automounterrc",
    "usr/bin/plasma-welcome",
    "usr/share/kwin/scripts/kavika-preview",
)


def normalize_shell_payload(data: bytes) -> bytes:
    """Normalize Windows CRLF/CR to Unix LF in overlay shell scripts."""
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def normalize_payload_tree(root: Path) -> None:
    """Normalize CRLF/CR to LF in every text file of the overlay (configs, desktop entries and
    scripts). A stray CR corrupts KDE config values such as Number=2. Binary files (anything
    containing NUL bytes, e.g. PNG) are left byte-identical."""
    for item in sorted(root.rglob("*")):
        if item.is_file() and not item.is_symlink():
            data = item.read_bytes()
            if b"\x00" not in data:
                fixed = normalize_shell_payload(data)
                if fixed != data:
                    item.write_bytes(fixed)


def build_overlay_payload(repo: Path, payload: Path, desktop: str = "kde") -> Path:
    """Assemble the overlay payload tree under `payload` and return it.

    `repo` is the repository root (the parent of image/ and tools/). KDE remains the default.
    The GNOME variant removes KWin/Plasma-only files and overlays image/gnome/root; shared
    identity, account, hardware and Windows-provisioning files stay unchanged.
    """
    shutil.copytree(repo / "image/live-preview/root", payload, ignore=_IGNORE)
    if desktop == "gnome":
        for relative in _KDE_ONLY:
            target = payload / relative
            if target.is_dir():
                shutil.rmtree(target)
            elif target.exists():
                target.unlink()
        gnome_root = repo / "image/gnome/root"
        if gnome_root.is_dir():
            shutil.copytree(gnome_root, payload, dirs_exist_ok=True, ignore=_IGNORE)
    elif desktop != "kde":
        raise ValueError(f"unsupported desktop: {desktop}")
    logo = repo / "assets/branding/kavi-ka-os-logo.png"
    shutil.copy2(logo, payload / "usr/share/kavika/logo.png")
    launcher_dst = payload / "usr/local/lib/kavika/launch-windows-vm-linux.py"
    launcher_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(repo / "tools/launch-windows-vm-linux.py", launcher_dst)
    # The Windows provisioning media builder ships so an installed system can build the
    # boot ESP + answer stick from the user's own Windows ISO without the repository.
    media_tool_dst = payload / "usr/local/lib/kavika/kavika-windows-media.py"
    shutil.copy2(repo / "tools/kavika-windows-media.py", media_tool_dst)
    answer_dst = payload / "usr/share/kavika/autounattend.xml"
    answer_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(repo / "image/windows/autounattend.xml", answer_dst)
    installer_dst = payload / "usr/local/sbin/kavika-install"
    installer_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(repo / "tools/kavika-install.py", installer_dst)
    ks_dst = payload / "usr/lib/kavika/installer/kavika.ks"
    ks_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(repo / "image/install/kavika.ks", ks_dst)
    normalize_payload_tree(payload)
    for relative in _EXECUTABLES:
        target = payload / relative
        if target.exists():
            target.chmod(0o755)
    for item in payload.rglob("*"):
        if not item.is_symlink():
            os.utime(item, (0, 0))
    return payload


def build_overlay_cpio(repo: Path, work: Path, desktop: str = "kde") -> Path:
    """Assemble the overlay payload and emit a clean, root-relative newc cpio of it."""
    payload = build_overlay_payload(repo, work / "overlay-root", desktop=desktop)
    entries = sorted(p.relative_to(payload).as_posix() for p in payload.rglob("*"))
    cpio_path = work / "kavika-overlay.cpio"
    with cpio_path.open("wb") as archive:
        subprocess.run(
            ["cpio", "--null", "-o", "--format=newc", "--owner=0:0", "--reproducible"],
            cwd=payload, input=("\0".join(entries) + "\0").encode(),
            stdout=archive, check=True)
    return cpio_path
