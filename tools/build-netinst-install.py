#!/usr/bin/env python3
"""Build the Kavi'ka OS automated (dnf/netinst) installer ISO using xorriso.

Path B of the installer: instead of the interactive live install, this drives Anaconda in a
real dnf-based install from the Fedora 44 Everything repo. A full kickstart (image/install/
kavika-net.ks) is bundled on the media and referenced via inst.ks=hd:LABEL=...; it carries the
fail-closed device consent (%pre), the virtualization-stack %packages, and the %post that
delivers the Kavi'ka overlay onto the installed root.

Requires Linux, Python 3.11+, pycdlib 1.22+, xorriso, cpio, grub-script-check and
implantisomd5. The source ISO is never mounted or modified; a fresh ISO is written with
xorriso's boot-image replay, preserving the upstream volume label.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

_TOOLS_DIR = str(Path(__file__).resolve().parent)
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)
import kavika_overlay

NETINST_BASE_SHA256 = "bd285201494dd0ba09b54d05ac707de1401668b8512a573edb5922dcf9d7067e"
NETINST_BASE_NAME = "Fedora-Everything-netinst-x86_64-44-1.7.iso"
LABEL = "KAVIKA"
# The upstream netinst's own volume id, still present in its GRUB config and stage2 paths.
# Every reference to it is rewritten to LABEL so the media identifies itself as Kavi'ka and
# cannot be confused with a stock Fedora netinst, which produced real confusion in testing.
BASE_LABEL = "Fedora-E-dvd-x86_64-44"
KICKSTART_SOURCE = "image/install/kavika-net.ks"
KICKSTART_ON_ISO = "/kavika-net.ks"
OVERLAY_ON_ISO = "/kavika-overlay.cpio"

GRUB_CHECK_CANDIDATES = ("grub-script-check", "grub2-script-check")


def grub_script_check():
    for candidate in GRUB_CHECK_CANDIDATES:
        found = shutil.which(candidate)
        if found:
            return found
    return None


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def grub_netinst(text: str, test_target: str | None = None, test_consent: str | None = None,
                 compact: bool = False) -> str:
    """Add an automated 'Install Kavi'ka OS' entry that points at the bundled kickstart.

    The entry is inserted first and becomes the default. `test_consent` bakes an arbitrary
    kernel-cmdline consent string verbatim (for exercising the refusal matrix); otherwise
    `test_target` bakes matching kavika.target/confirm tokens. With neither, the installer's
    %pre refuses (fail-closed). `compact` bakes `kavika.compact=1`, which selects the
    compact layout and lower size floor in the %pre for a target under 240 GiB.
    """
    if f"inst.stage2=hd:LABEL={BASE_LABEL}" not in text:
        raise ValueError("Unexpected upstream netinst GRUB configuration")
    # Rename the media: every reference to the upstream label (the `search --set=root` line and
    # each `inst.stage2=hd:LABEL=` / `inst.ks=hd:LABEL=`) becomes LABEL, so the rewritten config
    # is self-consistent with the volume id xorriso writes.
    text = text.replace(BASE_LABEL, LABEL)
    extra = ""
    if test_consent:
        extra = " " + test_consent.strip()
    elif test_target:
        extra = f" kavika.target={test_target} kavika.confirm={test_target}"
    if compact:
        extra += " kavika.compact=1"
    entry = (
        'menuentry "Install Kavi\'ka OS (automated)" --class fedora --class gnu-linux --class gnu --class os {\n'
        f'\tlinux /images/pxeboot/vmlinuz inst.stage2=hd:LABEL={LABEL} '
        f'inst.ks=hd:LABEL={LABEL}:{KICKSTART_ON_ISO}{extra} quiet '
        'console=tty0 console=ttyS0,115200n8\n'
        '\tinitrd /images/pxeboot/initrd.img\n'
        '}\n'
    )
    text = text.replace('set default="1"', 'set default="0"')
    # The consent tokens are normally added BY HAND at this menu, so the entry has to stay on
    # screen long enough to read it and press `e`. A 5-second timeout turns that into a race:
    # miss it and the boot lands on a refusal. Only a build whose decision is already baked in
    # (--test-target/--test-consent) may boot unattended, so only that keeps the short timeout.
    unattended = bool(test_target or test_consent)
    text = text.replace("set timeout=60", f"set timeout={5 if unattended else 60}")
    text = text.replace("menuentry 'Install Fedora 44'", entry + "menuentry 'Install Fedora 44'", 1)
    return text


def extract_grub(base: Path, destination: Path, iso_path: str) -> None:
    import pycdlib
    iso = pycdlib.PyCdlib()
    iso.open(str(base))
    try:
        with iso.open_file_from_iso(iso_path=iso_path) as source:
            with destination.open("wb") as target:
                shutil.copyfileobj(source, target, length=1024 * 1024)
    finally:
        iso.close()


def skip_firstboot(text: str) -> str:
    """TEST ONLY: drop `firstboot --enable` so a build boots straight to the display manager.

    Initial Setup is interactive, so a headless KVM run can never complete it and therefore
    can never observe whether SDDM actually starts. Disabling it in a throwaway build is the
    only way to prove the graphical target is reachable without a human at the console. Never
    applied to a shipped ISO.
    """
    out = text.replace("firstboot --enable",
                       "# firstboot --enable  (skipped in this TEST-only build)", 1)
    if out == text:
        raise ValueError("kickstart has no 'firstboot --enable' line to skip")
    return out


def extract_esp(base: Path, destination: Path) -> int:
    """Copy the base ISO's appended EFI System Partition out to a file; return its number.

    UEFI booting from USB mounts this partition and runs \\EFI\\BOOT\\BOOTX64.EFI, whose GRUB
    loads the EFI/BOOT/grub.cfg *inside this partition* - a different file from the ISO9660
    one. `-boot_image replay` copies it verbatim from the base, so anything written only into
    the ISO9660 tree never reaches it.
    """
    out = subprocess.run(["parted", "-s", str(base), "unit", "s", "print"],
                         capture_output=True, text=True, check=True).stdout
    for line in out.splitlines():
        fields = line.split()
        if len(fields) >= 4 and fields[0].isdigit() and "esp" in line:
            number = int(fields[0])
            start = int(fields[1].rstrip("s"))
            size = int(fields[3].rstrip("s"))
            with base.open("rb") as handle:
                handle.seek(start * 512)
                destination.write_bytes(handle.read(size * 512))
            return number
    raise ValueError("base ISO has no ESP partition to patch")


def patch_esp_grub(source: Path, destination: Path, test_target: str | None,
                   test_consent: str | None, compact: bool) -> None:
    """Copy the ESP and rewrite the GRUB config inside it with the same transforms."""
    shutil.copy2(source, destination)
    upstream = subprocess.run(["mtype", "-i", str(destination), "::/EFI/BOOT/grub.cfg"],
                              capture_output=True, text=True, check=True).stdout
    patched = grub_netinst(upstream, test_target, test_consent, compact)
    scratch = destination.with_suffix(".grub.cfg")
    scratch.write_text(patched, encoding="utf-8")
    subprocess.run(["mcopy", "-o", "-i", str(destination), str(scratch),
                    "::/EFI/BOOT/grub.cfg"], check=True)


def rewrite_kickstart_source(text: str, repo_dir: str | None) -> str:
    """Point the kickstart at the offline repo bundled on the media, or leave the network url."""
    if not repo_dir:
        return text
    for line in text.splitlines():
        if line.strip().startswith("url --url="):
            return text.replace(line, "cdrom", 1)
    raise ValueError("kickstart has no 'url --url=' line to replace with cdrom")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True, help="verified Fedora 44 netinst ISO")
    parser.add_argument("--output", type=Path, required=True, help="new .iso output path")
    parser.add_argument("--test-target", help="bake kavika.target/confirm for a disposable KVM run (e.g. /dev/vda)")
    parser.add_argument("--test-consent", help="bake an arbitrary kernel-cmdline consent string verbatim (refusal-matrix testing)")
    parser.add_argument("--test-skip-firstboot", action="store_true",
                        help="TEST ONLY: disable Initial Setup so a headless run can reach the display manager")
    parser.add_argument("--compact", action="store_true",
                        help="bake kavika.compact=1: compact layout and a lower size floor, for a target under 240 GiB (a small test disk). A 64 GiB guest will not fit; provision with --disk-gib 32")
    parser.add_argument("--repo-dir", type=Path, help="bundle this local repo (repodata + *.rpm) onto the media and switch the source to cdrom")
    args = parser.parse_args()
    base = args.base.resolve(strict=True)
    output = args.output.resolve()
    if not base.is_file() or base.suffix.lower() != ".iso":
        parser.error("--base must be an existing ISO file")
    if output.exists() or output == base or str(output).startswith("/dev/"):
        parser.error("--output must be a new regular file, never a device or existing file")
    if output.suffix.lower() != ".iso" or not output.parent.is_dir():
        parser.error("--output must be a new .iso in an existing directory")
    for tool in ("xorriso", "cpio", "implantisomd5", "parted", "mtype", "mcopy"):
        if shutil.which(tool) is None:
            parser.error(f"Missing builder tool: {tool}")
    grub_check = grub_script_check()
    if grub_check is None:
        parser.error("Missing builder tool: grub-script-check (on Fedora this is grub2-script-check)")
    base_hash = digest(base)
    if base_hash != NETINST_BASE_SHA256:
        parser.error("Fedora netinst input ISO SHA-256 mismatch; no output was created")

    import pycdlib  # noqa: F401
    repo = Path(__file__).resolve().parents[1]
    kickstart = repo / KICKSTART_SOURCE
    if not kickstart.is_file():
        parser.error(f"kickstart not found: {kickstart}")
    repo_dir = args.repo_dir.resolve(strict=True) if args.repo_dir else None
    if repo_dir is not None and not (repo_dir / "repodata" / "repomd.xml").is_file():
        parser.error("--repo-dir must contain repodata/repomd.xml (run createrepo_c first)")

    with tempfile.TemporaryDirectory(prefix="kavika-netinst-", dir=output.parent) as temp_dir:
        work = Path(temp_dir)
        overlay_cpio = kavika_overlay.build_overlay_cpio(repo, work)

        # Kickstart: switch the install source to the bundled cdrom repo when --repo-dir is given.
        ks_text = kickstart.read_text(encoding="utf-8")
        ks_text = rewrite_kickstart_source(ks_text, str(repo_dir) if repo_dir else None)
        if args.test_skip_firstboot:
            ks_text = skip_firstboot(ks_text)
        ks_file = work / "kavika-net.ks"
        ks_file.write_text(ks_text, encoding="utf-8")

        # Rewrite both the BIOS and UEFI GRUB configs with the automated install entry.
        grub_paths = {
            "boot/grub2/grub.cfg": "/BOOT/GRUB2/GRUB.CFG;1",
            "EFI/BOOT/grub.cfg": "/EFI/BOOT/GRUB.CFG;1",
        }
        grub_files = {}
        for rel, iso_path in grub_paths.items():
            upstream = work / ("upstream-" + rel.replace("/", "-"))
            extract_grub(base, upstream, iso_path)
            patched = work / ("patched-" + rel.replace("/", "-"))
            patched.write_text(grub_netinst(upstream.read_text(encoding="utf-8"), args.test_target,
                                            args.test_consent, args.compact), encoding="utf-8")
            subprocess.run([grub_check, str(patched)], check=True)
            grub_files[rel] = patched

        # D36: the appended ESP carries its own EFI/BOOT/grub.cfg, which `-boot_image replay`
        # copies verbatim from the base. Patch it too, or UEFI booting from USB runs the stock
        # Fedora menu whose entries reference a label the renamed media no longer has, which
        # fails with "you need to load the kernel first".
        esp_upstream = work / "esp-upstream.img"
        esp_number = extract_esp(base, esp_upstream)
        esp_patched = work / "esp-patched.img"
        patch_esp_grub(esp_upstream, esp_patched, args.test_target, args.test_consent,
                       args.compact)

        xorriso_cmd = ["xorriso", "-indev", str(base), "-outdev", str(output),
                       "-volid", LABEL]
        for rel, patched in grub_files.items():
            xorriso_cmd += ["-map", str(patched), "/" + rel]
        xorriso_cmd += [
            "-map", str(ks_file), KICKSTART_ON_ISO,
            "-map", str(overlay_cpio), OVERLAY_ON_ISO,
        ]
        if repo_dir is not None:
            xorriso_cmd += ["-map", str(repo_dir), "/"]
        xorriso_cmd += ["-boot_image", "any", "replay",
                        "-append_partition", str(esp_number), "0xef", str(esp_patched),
                        "-commit"]
        subprocess.run(xorriso_cmd, check=True)
        subprocess.run(["implantisomd5", "--force", str(output)], check=True)

        sha = digest(output)
        manifest = {
            "name": "Kavi'ka OS 0.1.0 automated netinst installer (dnf, Fedora 44 Everything)",
            "base": NETINST_BASE_NAME, "base_sha256": base_hash,
            "output_sha256": sha, "output_bytes": output.stat().st_size,
            "architecture": "x86_64", "installer_supported": True,
            "install_method": "dnf (Anaconda) + kickstart, fail-closed device consent",
            "install_source": ("cdrom (bundled offline repo)" if repo_dir is not None else
                               "https://download.fedoraproject.org/pub/fedora/linux/releases/44/Everything/x86_64/os/"),
            "offline_repo_bundled": repo_dir is not None,
            "kickstart": KICKSTART_ON_ISO, "overlay": OVERLAY_ON_ISO,
            "volume_label": LABEL, "test_target": args.test_target, "compact": args.compact,
            "overlay_cpio_sha256": digest(overlay_cpio),
            "kickstart_sha256": digest(ks_file),
            "builder_sha256": digest(Path(__file__)),
            "build_time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        output.with_suffix(".iso.sha256").write_text(f"{sha}  {output.name}\n", encoding="ascii")
        output.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"iso": str(output), "sha256": sha, "bytes": output.stat().st_size}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
