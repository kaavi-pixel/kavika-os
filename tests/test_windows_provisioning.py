"""Checks on the Kavi'ka Windows provisioning pieces, without a Windows ISO or a guest.

These verify what is checkable on any host: the scripts parse, they refuse bad input and
missing prerequisites cleanly, the media builder's contract matches the recipe (the ESP
carries the ISO's boot files; the answer stick carries autounattend.xml), and the overlay
builder actually ships every Windows piece. They do not install Windows.
"""
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "image/live-preview/root/usr/local/bin"
PROVISION = BIN / "kavika-windows-provision"
OPTIN = BIN / "kavika-windows-optin"
MEDIA_TOOL = ROOT / "tools/kavika-windows-media.py"
ANSWER = ROOT / "image/windows/autounattend.xml"
WINDOWS_TXT = ROOT / "image/live-preview/root/usr/share/kavika/WINDOWS.txt"

sys.path.insert(0, str(ROOT / "tools"))
import kavika_overlay  # noqa: E402


def load_media_tool():
    spec = importlib.util.spec_from_file_location("kavika_windows_media", MEDIA_TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


BASH = shutil.which("bash") or "/usr/bin/bash"


def run_script(path, *args, env=None):
    # Absolute bash: the script under test must be found through the child PATH, but bash
    # itself must not be, or stripping PATH to hide qemu breaks the interpreter too.
    return subprocess.run([BASH, str(path), *args], capture_output=True, text=True,
                          env=env)


def minimal_bin(td, with_qemu=False, with_kdialog=False):
    """A PATH dir holding only what the scripts need, so qemu/kdialog can be hidden."""
    b = Path(td) / "bin"
    b.mkdir(exist_ok=True)
    for tool in ("mkdir", "dirname", "cat", "grep"):
        src = shutil.which(tool)
        if src:
            os.symlink(src, b / tool)
    for name, want in (("qemu-system-x86_64", with_qemu), ("kdialog", with_kdialog)):
        if want:
            p = b / name
            p.write_text("#!/bin/sh\nexit 0\n")
            p.chmod(0o755)
    return b


class MediaBuilderTests(unittest.TestCase):
    def test_tool_is_present_and_compiles(self):
        self.assertTrue(MEDIA_TOOL.is_file(), MEDIA_TOOL)
        self.assertTrue(ANSWER.is_file(), ANSWER)
        proc = subprocess.run([sys.executable, "-m", "py_compile", str(MEDIA_TOOL)],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_contract_matches_the_recipe(self):
        m = load_media_tool()
        # The ESP must carry the ISO's boot files and boot.wim on the same volume.
        self.assertIn("sources/boot.wim", m.ISO_FILES)
        self.assertIn("efi/boot/bootx64.efi", m.ISO_FILES)
        self.assertIn("boot/bcd", m.ISO_FILES)
        self.assertIn("efi/microsoft/boot", m.ISO_TREES)
        # The pristine BCD sizes from the recipe.
        self.assertEqual(m.BCD_EXPECT["boot/bcd"], 16384)
        self.assertEqual(m.BCD_EXPECT["efi/microsoft/boot/bcd"], 16384)
        self.assertEqual(m.BOOTX64_EXPECT, 3087400)
        self.assertEqual(m.ESP_LABEL, "KAVIKAESP")
        self.assertEqual(m.ANSWER_LABEL, "KAVIKAANSW")

    def test_help_exits_zero(self):
        proc = subprocess.run([sys.executable, str(MEDIA_TOOL), "--help"],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_missing_iso_argument_is_rejected(self):
        proc = subprocess.run([sys.executable, str(MEDIA_TOOL), "--out-dir", "/tmp/x"],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)  # argparse

    def test_nonexistent_iso_fails_cleanly(self):
        proc = subprocess.run(
            [sys.executable, str(MEDIA_TOOL), "--iso", "/nonexistent/win.iso",
             "--out-dir", "/tmp/kavika-nowhere"],
            capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("ISO not found", proc.stderr)

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as td:
            fake_iso = Path(td) / "fake.iso"
            fake_iso.write_bytes(b"not really windows")
            out = Path(td) / "out"
            proc = subprocess.run(
                [sys.executable, str(MEDIA_TOOL), "--iso", str(fake_iso),
                 "--out-dir", str(out), "--dry-run"],
                capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("dry run", proc.stdout)
            self.assertFalse((out / "esp.img").exists())

    def test_sha256_pin_mismatch_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            fake_iso = Path(td) / "fake.iso"
            fake_iso.write_bytes(b"x")
            proc = subprocess.run(
                [sys.executable, str(MEDIA_TOOL), "--iso", str(fake_iso),
                 "--out-dir", str(Path(td) / "out"),
                 "--expected-sha256", "0" * 64],
                capture_output=True, text=True)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("sha256 mismatch", proc.stderr)


class ProvisionScriptTests(unittest.TestCase):
    def test_syntactically_valid(self):
        proc = subprocess.run(["bash", "-n", str(PROVISION)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_help_exits_zero(self):
        proc = run_script(PROVISION, "--help")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("kavika-windows-provision", proc.stdout)

    def test_missing_iso_is_required(self):
        proc = run_script(PROVISION)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("--iso is required", proc.stderr)

    def test_unknown_argument_is_rejected(self):
        proc = run_script(PROVISION, "--bogus")
        self.assertEqual(proc.returncode, 2)

    def test_nonexistent_iso_fails_cleanly(self):
        proc = run_script(PROVISION, "--iso", "/nonexistent/win.iso")
        self.assertEqual(proc.returncode, 3)
        self.assertIn("ISO not found", proc.stderr)

    def test_install_uses_a_new_empty_guest_subdirectory(self):
        # The media builder writes <volume>/media before the launcher starts. Passing the
        # volume itself as --vm-dir therefore trips the launcher's new-or-empty guard.
        text = PROVISION.read_text()
        self.assertIn('GUEST_DIR="$VM_DIR/guest"', text)
        self.assertIn('--vm-dir "$GUEST_DIR"', text)
        self.assertIn('MEDIA_DIR="$VM_DIR/media"', text)

    def test_missing_launcher_fails_cleanly(self):
        # qemu may or may not be on this host; force the launcher check with a real ISO path.
        with tempfile.TemporaryDirectory() as td:
            iso = Path(td) / "win.iso"
            iso.write_bytes(b"x")
            env = {**os.environ, "KAVIKA_WINDOWS_LAUNCHER": "/nonexistent/launcher.py"}
            proc = run_script(PROVISION, "--iso", str(iso), env=env)
            self.assertEqual(proc.returncode, 4)
            self.assertIn("launcher not found", proc.stderr)


class OptInTests(unittest.TestCase):
    def test_syntactically_valid(self):
        proc = subprocess.run(["bash", "-n", str(OPTIN)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_silent_when_no_qemu(self):
        # No qemu on PATH: the live-preview case. Silent, exit 0, no marker.
        with tempfile.TemporaryDirectory() as td:
            env = {**os.environ, "PATH": str(minimal_bin(td, with_qemu=False)), "HOME": td}
            proc = run_script(OPTIN, env=env)
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(proc.stderr.strip(), "")
            self.assertFalse((Path(td) / ".config/kavika/windows-optin-answered").exists())

    def test_records_answer_once_when_no_dialog(self):
        # qemu present (installed system) but no kdialog: record the answer, do nothing else.
        with tempfile.TemporaryDirectory() as td:
            env = {**os.environ, "PATH": str(minimal_bin(td, with_qemu=True)), "HOME": td}
            proc = run_script(OPTIN, env=env)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            marker = Path(td) / ".config/kavika/windows-optin-answered"
            self.assertTrue(marker.exists())

    def test_marker_suppresses_the_prompt(self):
        with tempfile.TemporaryDirectory() as td:
            marker = Path(td) / ".config/kavika/windows-optin-answered"
            marker.parent.mkdir(parents=True)
            marker.write_text("")
            env = {**os.environ, "PATH": str(minimal_bin(td, with_qemu=True)), "HOME": td}
            proc = run_script(OPTIN, env=env)
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(proc.stderr.strip(), "")


class OverlayShippingTests(unittest.TestCase):
    """The overlay builder must ship every Windows piece on an installed system."""

    EXPECTED = (
        "usr/local/bin/kavika-windows-workspace",
        "usr/local/bin/kavika-windows-provision",
        "usr/local/bin/kavika-windows-optin",
        "usr/local/lib/kavika/launch-windows-vm-linux.py",
        "usr/local/lib/kavika/kavika-windows-media.py",
        "usr/share/kavika/autounattend.xml",
        "usr/share/kavika/WINDOWS.txt",
    )

    def test_all_windows_pieces_are_shipped(self):
        with tempfile.TemporaryDirectory() as td:
            payload = kavika_overlay.build_overlay_payload(ROOT, Path(td) / "payload")
            for rel in self.EXPECTED:
                self.assertTrue((payload / rel).is_file(), f"missing from overlay: {rel}")

    def test_shipped_scripts_are_executable(self):
        with tempfile.TemporaryDirectory() as td:
            payload = kavika_overlay.build_overlay_payload(ROOT, Path(td) / "payload")
            for rel in ("usr/local/bin/kavika-windows-workspace",
                        "usr/local/bin/kavika-windows-provision",
                        "usr/local/bin/kavika-windows-optin",
                        "usr/local/lib/kavika/kavika-windows-media.py"):
                self.assertTrue(os.access(payload / rel, os.X_OK), f"not executable: {rel}")

    def test_shipped_answer_file_matches_the_repo_copy(self):
        with tempfile.TemporaryDirectory() as td:
            payload = kavika_overlay.build_overlay_payload(ROOT, Path(td) / "payload")
            shipped = (payload / "usr/share/kavika/autounattend.xml").read_bytes()
            # The overlay normalizes line endings; compare with that normalization applied.
            want = kavika_overlay.normalize_shell_payload(ANSWER.read_bytes())
            self.assertEqual(shipped, want)

    def test_windows_txt_names_the_shipped_commands(self):
        text = WINDOWS_TXT.read_text()
        self.assertIn("kavika-windows-provision", text)
        self.assertIn("kavika-windows-workspace", text)


class InstallerDependencyTests(unittest.TestCase):
    """The installed system must carry what the shipped media builder needs."""

    def test_kickstart_installs_the_media_builder_dependencies(self):
        ks = (ROOT / "image/install/kavika-net.ks").read_text()
        block = ks.split("%packages", 1)[1].split("%end", 1)[0]
        pkgs = {ln.strip() for ln in block.splitlines()
                if ln.strip() and not ln.strip().startswith("#")}
        # qemu/swtpm/OVMF run the guest; 7zip+parted+dosfstools+mtools build its media.
        for required in ("qemu-kvm", "swtpm", "edk2-ovmf", "mtools",
                         "7zip", "parted", "dosfstools"):
            self.assertIn(required, pkgs, f"kickstart %packages must install {required}")
        # D34: the KDE group alone installs no display manager, so the system boots to text.
        self.assertIn("sddm", pkgs, "kickstart %packages must install a display manager (sddm)")

    def test_post_verification_checks_them(self):
        ks = (ROOT / "image/install/kavika-net.ks").read_text()
        self.assertIn("rpm -q --root=\"$SYSROOT\"", ks)
        for pkg in ("7zip", "parted", "dosfstools", "mtools"):
            self.assertIn(pkg, ks.split("rpm -q --root=", 1)[1].split("\n", 1)[0])

    def test_text_install_sets_graphical_default_target(self):
        # D34: `text` makes Anaconda leave the installed system on multi-user.target, so the
        # finished install boots to a text console with no desktop. The kickstart must undo it,
        # and must also ensure the display manager is enabled rather than relying on a preset.
        ks = (ROOT / "image/install/kavika-net.ks").read_text()
        self.assertIn("text", ks.splitlines(), "the installer still runs in text mode")
        self.assertIn('set-default graphical.target', ks,
                      "text-mode installs must set the installed system back to graphical.target")
        self.assertIn('enable "$dm.service"', ks,
                      "the display manager must be enabled explicitly")
        self.assertIn("default.target ->", ks,
                      "the install log must read back what default.target was actually set to")
        # D34: the live-only SELinux drop-in must not survive onto an installed root; it
        # restorecon's /var/lib/livesys, which is absent there, and fails tmpfiles-setup.
        self.assertIn("systemd-tmpfiles-setup.service.d", ks,
                      "%post must remove the live-only tmpfiles drop-in from installed roots")


    def test_installed_system_is_configured_for_network(self):
        # D35: without a saved connection the installed system has no route and no DNS, so dnf
        # and the Windows provisioner's downloads fail.
        ks = (ROOT / "image/install/kavika-net.ks").read_text()
        self.assertRegex(ks, r"(?m)^network .*--bootproto=dhcp")
        self.assertRegex(ks, r"(?m)^network .*--onboot=yes")

    def test_media_identifies_as_kavika(self):
        # The media must not present itself as a Fedora netinst: that confusion cost real time,
        # and both a stock netinst's label and ours were identical.
        ks = (ROOT / "image/install/kavika-net.ks").read_text()
        self.assertIn("LABEL=KAVIKA", ks)
        self.assertNotIn("LABEL=Fedora-E-dvd-x86_64-44", ks)
        builder = (ROOT / "tools/build-netinst-install.py").read_text()
        self.assertIn('LABEL = "KAVIKA"', builder)
        self.assertIn('"-volid", LABEL', builder)


if __name__ == "__main__":
    unittest.main()
