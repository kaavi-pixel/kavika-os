"""Checks on the Kavi'ka Windows workspace, without needing KDE or a touchpad.

These verify the parts that can be verified on any host: the script parses, it refuses bad
input, it fails cleanly when nothing is provisioned, and it uses the documented mechanisms
rather than invented ones.
"""
import os
import subprocess
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


if __name__ == "__main__":
    unittest.main()
