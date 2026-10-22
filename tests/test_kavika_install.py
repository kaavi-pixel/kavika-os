"""Checks on the Kavi'ka installer pre-flight and its kickstart template.

These exercise the refusal and substitution logic against synthetic inventories, with no
disk access and no destructive action. The pre-flight module is imported directly, so the
tests pin the safety behaviour rather than the CLI plumbing.
"""
import importlib.machinery
import importlib.util
import os
from pathlib import Path
import tempfile
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
NET_KICKSTART = (ROOT / "image/install/kavika-net.ks").read_text(encoding="utf-8")
netinst_builder = load("netinst_builder", ROOT / "tools/build-netinst-install.py")

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

    def test_template_omits_packages_for_liveinstall(self):
        # Live installs copy the squashfs, so a %packages directive is not honored; the
        # template must not contain an actual %packages line (only a comment mentioning it).
        for line in KICKSTART.splitlines():
            self.assertFalse(line.strip().startswith("%packages"), line)
        # The virtualization stack is still documented as a post-install (T20) provision.
        for pkg in ("qemu-kvm", "swtpm", "edk2-ovmf", "mtools"):
            self.assertIn(pkg, KICKSTART)

    def test_template_delivers_overlay_in_post(self):
        self.assertIn("%post --nochroot", KICKSTART)
        self.assertIn("kavika-overlay.cpio", KICKSTART)
        self.assertIn("cpio -idmu", KICKSTART)

    def test_template_does_not_bake_in_a_user_password(self):
        self.assertNotIn("--password", KICKSTART)
        self.assertNotIn("plaintext", KICKSTART)

    def test_template_enables_first_boot(self):
        self.assertIn("firstboot --enable", KICKSTART)


    def test_livecmd_drops_kickstart_for_liveinstall(self):
        # --liveinst ignores --kickstart and inst.ks; the kickstart is delivered to
        # interactive-defaults.ks instead (see deliver_kickstart).
        self.assertEqual(kavika_install.livecmd("text"), "anaconda --liveinst --text")
        self.assertEqual(kavika_install.livecmd("graphical"), "anaconda --liveinst --graphical")

    def test_deliver_kickstart_writes_both_locations_and_backs_up(self):
        with tempfile.TemporaryDirectory() as tmp:
            defaults = os.path.join(tmp, "interactive-defaults.ks")
            with open(defaults, "w", encoding="utf-8") as f:
                f.write("stock")
            resolved = os.path.join(tmp, "resolved.ks")
            written = kavika_install.deliver_kickstart(
                "kickstart content", interactive_defaults=defaults, resolved_path=resolved)
            self.assertIn(resolved, written)
            self.assertIn(defaults, written)
            self.assertEqual(open(defaults, encoding="utf-8").read(), "kickstart content")
            self.assertTrue(os.path.exists(defaults + ".kavika-orig"))
            # a second delivery must not clobber the original backup
            kavika_install.deliver_kickstart(
                "v2", interactive_defaults=defaults, resolved_path=resolved)
            self.assertEqual(open(defaults + ".kavika-orig", encoding="utf-8").read(), "stock")


class NetinstKickstartTests(unittest.TestCase):
    """The dnf/netinst kickstart (Path B): automated, with %packages honored."""

    def test_uses_the_everything_repo_and_packages(self):
        self.assertIn("url --url=", NET_KICKSTART)
        self.assertIn("Everything/x86_64/os/", NET_KICKSTART)
        self.assertIn("%packages", NET_KICKSTART)
        for pkg in ("qemu-kvm", "swtpm", "edk2-ovmf", "mtools", "virt-install"):
            self.assertIn(pkg, NET_KICKSTART)

    def test_pre_consent_is_fail_closed(self):
        # The %pre must refuse without kavika.target and kavika.confirm, and must require they match.
        self.assertIn("kavika.target=", NET_KICKSTART)
        self.assertIn("kavika.confirm=", NET_KICKSTART)
        self.assertIn("no kavika.target=", NET_KICKSTART)
        self.assertIn("no kavika.confirm=", NET_KICKSTART)
        self.assertIn("kavika.target ($TARGET) != kavika.confirm ($CONFIRM)", NET_KICKSTART)
        self.assertIn("exit 1", NET_KICKSTART)

    def test_scopes_storage_via_generated_include(self):
        self.assertIn("%include /tmp/kavika-storage.ks", NET_KICKSTART)
        self.assertIn("ignoredisk --only-use=$TARGET", NET_KICKSTART)
        self.assertIn("clearpart --all --initlabel --drives=$TARGET", NET_KICKSTART)

    def test_delivers_overlay_in_post_and_reboots(self):
        self.assertIn("%post --nochroot", NET_KICKSTART)
        self.assertIn("kavika-overlay.cpio", NET_KICKSTART)
        self.assertIn("cpio -idmu", NET_KICKSTART)
        self.assertIn("reboot", NET_KICKSTART)

    def test_no_baked_password(self):
        self.assertNotIn("--password", NET_KICKSTART)
        self.assertNotIn("plaintext", NET_KICKSTART)
        self.assertIn("rootpw --lock", NET_KICKSTART)

    def test_grub_netinst_adds_entry_and_consent(self):
        source = ('set default="1"\nset timeout=60\n'
                  'menuentry \'Install Fedora 44\' {\n'
                  '\tlinux /images/pxeboot/vmlinuz inst.stage2=hd:LABEL=Fedora-E-dvd-x86_64-44 quiet\n'
                  '\tinitrd /images/pxeboot/initrd.img\n}\n')
        result = netinst_builder.grub_netinst(source)
        self.assertIn('menuentry "Install Kavi\'ka OS (automated)"', result)
        self.assertIn("inst.ks=hd:LABEL=Fedora-E-dvd-x86_64-44:/kavika-net.ks", result)
        self.assertIn('set default="0"', result)
        # without a test target there must be no baked consent token
        self.assertNotIn("kavika.target=", result)

        with_target = netinst_builder.grub_netinst(source, test_target="/dev/vda")
        self.assertIn("kavika.target=/dev/vda kavika.confirm=/dev/vda", with_target)

        with_consent = netinst_builder.grub_netinst(source, test_consent="kavika.target=/dev/vda kavika.confirm=/dev/vdb")
        self.assertIn("kavika.target=/dev/vda kavika.confirm=/dev/vdb", with_consent)

    def test_rewrite_kickstart_source_switches_to_cdrom(self):
        ks = 'lang en_GB.UTF-8\nurl --url="https://example.invalid/os/"\ntext\n'
        self.assertEqual(netinst_builder.rewrite_kickstart_source(ks, "/some/repo"),
                         'lang en_GB.UTF-8\ncdrom\ntext\n')
        # without a repo dir the network url is preserved
        self.assertEqual(netinst_builder.rewrite_kickstart_source(ks, None), ks)


if __name__ == "__main__":
    unittest.main()
