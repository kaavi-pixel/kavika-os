"""Checks on the Kavi'ka Windows workspace, without needing KDE or a touchpad.

These verify the parts that can be verified on any host: the script parses, it refuses bad
input, it fails cleanly when nothing is provisioned, and it uses the documented mechanisms
rather than invented ones.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "image/live-preview/root/usr/local/bin/kavika-windows-workspace"
KWINRC = ROOT / "image/live-preview/root/etc/skel/.config/kwinrc"


class WindowsWorkspaceTests(unittest.TestCase):
    def test_script_is_present_and_syntactically_valid(self):
        self.assertTrue(SCRIPT.is_file(), SCRIPT)
        proc = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_unknown_argument_is_rejected(self):
        proc = subprocess.run(["bash", str(SCRIPT), "--bogus"],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)

    def test_unprovisioned_guest_fails_cleanly(self):
        # Must refuse, not start something unexpected, and say why.
        proc = subprocess.run(
            ["bash", str(SCRIPT), "--show"], capture_output=True, text=True,
            env={**os.environ, "KAVIKA_WINDOWS_VM_DIR": "/nonexistent-kavika-guest"})
        self.assertEqual(proc.returncode, 3)
        self.assertIn("no Windows guest provisioned", proc.stderr)

    def test_uses_the_documented_kwin_desktop_switch(self):
        self.assertIn("org.kde.KWin.setCurrentDesktop",
                      SCRIPT.read_text(encoding="utf-8"))

    def test_does_not_invent_a_gesture_api(self):
        # KWin has no touchpad-swipe registration API, so a custom swipe handler cannot
        # exist. The swipe is Plasma's built-in desktop switch. This guards the invariant.
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("registerTouchpadSwipe", text)

    def test_starts_the_guest_in_reuse_full_screen_mode(self):
        text = SCRIPT.read_text(encoding="utf-8")
        for flag in ("--reuse", "--full-screen", "--esp-image"):
            self.assertIn(flag, text)

    def test_desktop_layout_is_a_single_row_of_two(self):
        # A horizontal swipe only navigates a single-row layout.
        text = KWINRC.read_text(encoding="utf-8")
        self.assertIn("Number=2", text)
        self.assertIn("Rows=1", text)
        self.assertIn("Name_1=Linux", text)
        self.assertIn("Name_2=", text)

    def _run_with_fake_launcher(self, vm):
        """Run the script against a fake launcher and return the argv it was called with."""
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            record = td / "argv.json"
            launcher = td / "launcher.py"
            launcher.write_text(
                "import json, os, sys, pathlib\n"
                "pathlib.Path(os.environ['KAVIKA_TEST_ARGV']).write_text(json.dumps(sys.argv))\n",
                encoding="utf-8")
            env = {**os.environ,
                   "KAVIKA_WINDOWS_VM_DIR": str(vm),
                   "KAVIKA_WINDOWS_LAUNCHER": str(launcher),
                   "KAVIKA_PYTHON": sys.executable,
                   "KAVIKA_TEST_ARGV": str(record)}
            proc = subprocess.run(["bash", str(SCRIPT), "--show"],
                                  capture_output=True, text=True, env=env)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            return json.loads(record.read_text(encoding="utf-8"))

    def test_self_contained_guest_starts_without_a_boot_esp(self):
        # Since D21 the installed guest owns its boot files, so the ESP is optional.
        with tempfile.TemporaryDirectory() as td:
            vm = Path(td) / "guest"
            vm.mkdir()
            (vm / "windows11.qcow2").write_bytes(b"")
            argv = self._run_with_fake_launcher(vm)
        self.assertIn("--reuse", argv)
        self.assertNotIn("--esp-image", argv)

    def test_boot_esp_is_attached_when_present(self):
        with tempfile.TemporaryDirectory() as td:
            vm = Path(td) / "guest"
            vm.mkdir()
            (vm / "windows11.qcow2").write_bytes(b"")
            (vm / "boot-esp.img").write_bytes(b"")
            argv = self._run_with_fake_launcher(vm)
        self.assertIn("--esp-image", argv)


if __name__ == "__main__":
    unittest.main()
