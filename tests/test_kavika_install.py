"""Checks on the Kavi'ka installer pre-flight and its kickstart template.

These exercise the refusal and substitution logic against synthetic inventories, with no
disk access and no destructive action. The pre-flight module is imported directly, so the
tests pin the safety behaviour rather than the CLI plumbing.
"""
import importlib.machinery
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


kavika_install = load("kavika_install", ROOT / "tools/kavika-install.py")
KICKSTART = (ROOT / "image/install/kavika.ks").read_text(encoding="utf-8")

# A synthetic lsblk-style inventory: two whole disks, one 1 TiB empty, one small, one mounted.
DISKS = [
    {"name": "sda", "size": 1000 * 1024 ** 3, "rm": False, "tran": "sata",
     "type": "disk", "mountpoints": [None], "model": "BigInternal"},
    {"name": "sdb", "size": 8 * 1024 ** 3, "rm": True, "tran": "usb",
     "type": "disk", "mountpoints": [None], "model": "SmallUSB"},
    {"name": "sdc", "size": 512 * 1024 ** 3, "rm": False, "tran": "sata",
     "type": "disk", "mountpoints": ["/mnt/held"], "model": "MountedDisk"},
]
MIN = 240 * 1024 ** 3


class PreflightTests(unittest.TestCase):
    def test_mismatched_confirmation_is_refused(self):
        reasons = kavika_install.refusals(DISKS, "/dev/sda", "/dev/sdb", MIN, KICKSTART)
        self.assertTrue(any("differ" in r for r in reasons))

    def test_unknown_device_is_refused(self):
        reasons = kavika_install.refusals(DISKS, "/dev/sdz", "/dev/sdz", MIN, KICKSTART)
        self.assertTrue(any("not a whole-disk" in r for r in reasons))

    def test_mounted_target_is_refused(self):
        reasons = kavika_install.refusals(DISKS, "/dev/sdc", "/dev/sdc", MIN, KICKSTART)
        self.assertTrue(any("is mounted" in r for r in reasons))

    def test_too_small_target_is_refused(self):
        reasons = kavika_install.refusals(DISKS, "/dev/sdb", "/dev/sdb", MIN, KICKSTART)
        self.assertTrue(any("too small" in r for r in reasons))

    def test_template_without_placeholder_is_refused(self):
        reasons = kavika_install.refusals(DISKS, "/dev/sda", "/dev/sda", MIN, "no placeholder here")
        self.assertTrue(any("missing the @@" in r for r in reasons))

    def test_clean_target_passes(self):
        reasons = kavika_install.refusals(DISKS, "/dev/sda", "/dev/sda", MIN, KICKSTART)
        self.assertEqual(reasons, [])

    def test_pseudo_disks_are_not_candidates(self):
        blk = {"blockdevices": [
            {"name": "zram0", "type": "disk", "size": 1024 ** 4, "rm": False,
             "tran": None, "mountpoints": ["[SWAP]"], "model": ""},
            {"name": "loop0", "type": "disk", "size": 1024 ** 4, "rm": False,
             "tran": None, "mountpoints": [None], "model": ""},
            {"name": "sda", "type": "disk", "size": 1000 * 1024 ** 3, "rm": False,
             "tran": "sata", "mountpoints": [None], "model": "Real"},
        ]}
        self.assertEqual([d["name"] for d in kavika_install.whole_disks(blk)], ["sda"])

    def test_resolve_substitutes_and_rejects_absent_placeholder(self):
        resolved = kavika_install.resolve_kickstart(KICKSTART, "/dev/sda")
        self.assertNotIn("@@TARGET_DEVICE@@", resolved)
        self.assertIn("ignoredisk --only-use=/dev/sda", resolved)
        self.assertIn("clearpart --all --initlabel --drives=/dev/sda", resolved)
        self.assertIn("bootloader --boot-drive=/dev/sda", resolved)
        with self.assertRaises(ValueError):
            kavika_install.resolve_kickstart("nothing", "/dev/sda")


class KickstartTests(unittest.TestCase):
    def test_template_scopes_storage_to_the_confirmed_device(self):
        self.assertIn("ignoredisk --only-use=@@TARGET_DEVICE@@", KICKSTART)
        self.assertIn("clearpart --all --initlabel --drives=@@TARGET_DEVICE@@", KICKSTART)
        self.assertIn("bootloader --boot-drive=@@TARGET_DEVICE@@", KICKSTART)

    def test_template_has_a_dedicated_windows_guest_volume(self):
        self.assertIn("part /var/lib/kavika/windows", KICKSTART)

    def test_template_ships_the_virtualization_stack(self):
        for pkg in ("qemu-kvm", "swtpm", "edk2-ovmf", "mtools"):
            self.assertIn(pkg, KICKSTART)

    def test_template_does_not_bake_in_a_user_password(self):
        self.assertNotIn("--password", KICKSTART)
        self.assertNotIn("plaintext", KICKSTART)

    def test_template_enables_first_boot(self):
        self.assertIn("firstboot --enable", KICKSTART)


if __name__ == "__main__":
    unittest.main()
