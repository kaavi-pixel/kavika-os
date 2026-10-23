import importlib.machinery
import importlib.util
from pathlib import Path
import unittest
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


hardware = load("hardware", ROOT / "image/live-preview/root/usr/local/bin/kavika-hardware")
builder = load("builder", ROOT / "tools/build-live-preview.py")


class PreviewTests(unittest.TestCase):
    def test_disks_never_include_serial_uuid_or_partitions(self):
        data = {"blockdevices": [
            {"name": "nvme0n1", "type": "disk", "size": 128000000000,
             "serial": "PRIVATE", "uuid": "PRIVATE", "children": [{"uuid": "PRIVATE"}]},
            {"name": "nvme0n1p1", "type": "part", "serial": "PRIVATE"},
        ]}
        result = hardware.sanitize_disks(data)
        self.assertEqual(len(result), 1)
        self.assertNotIn("serial", result[0])
        self.assertNotIn("uuid", result[0])
        self.assertNotIn("children", result[0])

    def test_boot_preserves_root_label_and_adds_update_archive(self):
        source = ('set default="1"\nset timeout=10\n'
                  'linux ($root)/boot/x86_64/loader/linux root=live:CDLABEL=Fedora-KDE-Live-44 rd.live.image\n'
                  'initrd ($root)/boot/x86_64/loader/initrd\n')
        result = builder.grub_preview(source)
        self.assertIn("root=live:CDLABEL=Fedora-KDE-Live-44", result)
        self.assertIn("initrd ($root)/boot/x86_64/loader/initrd ($root)/boot/kavika-preview.cpio", result)
        self.assertIn('set default="0"', result)

    def test_wrong_base_config_rejected(self):
        with self.assertRaises(ValueError):
            builder.grub_preview("unrelated ISO")

    def test_single_quoted_recovery_title_remains_balanced(self):
        result = builder.grub_preview(
            "menuentry 'Start Fedora-KDE-Desktop-Live in basic graphics mode' {\n"
            "linux root=live:CDLABEL=Fedora-KDE-Live-44\n}\n")
        self.assertEqual(result.splitlines()[0].count("'"), 2)

    def test_grub_adds_install_entry_with_flag(self):
        source = (
            'set default="1"\nset timeout=10\n'
            'menuentry "Start Fedora-KDE-Desktop-Live" {\n'
            'linux ($root)/boot/x86_64/loader/linux root=live:CDLABEL=Fedora-KDE-Live-44 rd.live.image\n'
            'initrd ($root)/boot/x86_64/loader/initrd\n}\n'
            'menuentry "Test this media & start Fedora-KDE-Desktop-Live" {\n'
            'linux ($root)/boot/x86_64/loader/linux root=live:CDLABEL=Fedora-KDE-Live-44 rd.live.image rd.live.check\n'
            'initrd ($root)/boot/x86_64/loader/initrd\n}\n'
        )
        result = builder.grub_preview(source)
        self.assertIn('menuentry "Install Kavi\'ka OS"', result)
        self.assertIn("kavika.install=1", result)
        self.assertIn("rd.live.image kavika.install=1", result)
        # the install entry's initrd must also carry the overlay cpio
        self.assertIn("kavika-preview.cpio", result)
        if builder.grub_script_check():
            parsed = subprocess.run([builder.grub_script_check()], input=result,
                                    text=True, capture_output=True)
            self.assertEqual(parsed.returncode, 0, parsed.stderr)

    def test_guard_forwards_to_real_installer_on_flag(self):
        guard = (ROOT / "image/live-preview/root/usr/bin/liveinst").read_text()
        self.assertIn("kavika.install=1", guard)
        self.assertIn("/usr/libexec/kavika/real-liveinst", guard)

    def test_real_liveinst_is_vendored(self):
        real = ROOT / "image/live-preview/root/usr/libexec/kavika/real-liveinst"
        self.assertTrue(real.is_file())
        text = real.read_text()
        self.assertIn("anaconda --liveinst", text)  # the LIVECMD default

    @unittest.skipUnless(builder.grub_script_check(), "GRUB parser unavailable")
    def test_upstream_nested_video_function_is_normalized(self):
        source = (
            'if [ "$grub_platform" == "efi" ]; then\n'
            '\tfunction load_video {\n\t\tinsmod all_video\n\t}\n'
            'else\n\tfunction load_video {\n\t\tinsmod all_video\n\t}\nfi\n'
            'load_video\nlinux root=live:CDLABEL=Fedora-KDE-Live-44\n')
        result = builder.grub_preview(source)
        parsed = subprocess.run([builder.grub_script_check()], input=result, text=True, capture_output=True)
        self.assertEqual(parsed.returncode, 0, parsed.stderr)

    def test_preview_is_explicit_about_missing_windows(self):
        guide = (ROOT / "image/live-preview/root/usr/share/kavika/START-HERE.txt").read_text()
        self.assertIn("not Windows", guide)
        # The default path still refuses to install; only the install entry forwards.
        guard = (ROOT / "image/live-preview/root/usr/bin/liveinst").read_text()
        self.assertIn("installation is disabled", guard)
        self.assertIn("kavika.install=1", guard)

    def test_live_defaults_run_after_upstream_kde_setup(self):
        extra = (ROOT / "image/live-preview/root/var/lib/livesys/livesys-session-extra").read_text()
        self.assertIn("cp /etc/skel/.config/kwinrc /home/liveuser/.config/kwinrc", extra)
        welcome = (ROOT / "image/live-preview/root/usr/bin/plasma-welcome").read_text()
        self.assertIn("exit 0", welcome)

    def test_overlay_is_relabelled_not_selinux_disabled(self):
        hook = (ROOT / "image/live-preview/root/usr/lib/systemd/system/systemd-tmpfiles-setup.service.d/20-kavika-labels.conf").read_text()
        self.assertIn('ExecStartPost=/usr/sbin/restorecon -RF', hook)
        self.assertIn('ExecStartPost=/usr/sbin/restorecon -F / /etc', hook)
        self.assertNotIn("setenforce", hook)
        self.assertNotIn("selinux=0", builder.grub_preview(
            "linux root=live:CDLABEL=Fedora-KDE-Live-44\n"))

    def test_payload_shell_scripts_are_normalized_to_unix_line_endings(self):
        source = bytes.fromhex("23212f62696e2f626173680d0a6563686f2072656164790d0a")
        expected = bytes.fromhex("23212f62696e2f626173680a6563686f2072656164790a")
        self.assertEqual(builder.normalize_shell_payload(source), expected)

    def test_payload_text_files_are_normalized_but_binary_files_are_untouched(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "etc/skel/.config").mkdir(parents=True)
            (root / "var/lib/livesys").mkdir(parents=True)
            kwin = root / "etc/skel/.config/kwinrc"
            kwin.write_bytes(b"[Desktops]\r\nNumber=2\r\n")
            session = root / "var/lib/livesys/livesys-session-extra"
            session.write_bytes(b"#!/usr/bin/sh\r\nmkdir -p /home/liveuser/.config/autostart\r\n")
            png = root / "logo.png"
            binary = b"\x89PNG\r\n\x1a\n\x00\r\n\x00data"
            png.write_bytes(binary)
            builder.normalize_payload_tree(root)
            self.assertEqual(kwin.read_bytes(), b"[Desktops]\nNumber=2\n")
            self.assertNotIn(b"\r", session.read_bytes())
            self.assertEqual(png.read_bytes(), binary)

    def test_repository_forces_lf_for_live_payload(self):
        attributes = (ROOT / ".gitattributes").read_text()
        self.assertIn("image/live-preview/root/** text eol=lf", attributes)

    def test_target_matching_is_exact_for_both_surfaces(self):
        pro = hardware.match_target("Surface Pro 8")
        self.assertTrue(pro["matched"])
        self.assertEqual(pro["id"], "surface-pro-8")
        studio = hardware.match_target("Surface Laptop Studio")
        self.assertEqual(studio["id"], "surface-laptop-studio")
        self.assertIn("test machine", studio["role"])
        self.assertFalse(hardware.match_target("Surface Laptop Studio 2")["matched"])
        self.assertFalse(hardware.match_target("Standard PC (Q35 + ICH9, 2009)")["matched"])
        self.assertFalse(hardware.match_target(None)["matched"])

    def test_secure_boot_variable_is_parsed(self):
        self.assertTrue(hardware.parse_secure_boot(bytes([6, 0, 0, 0, 1])))
        self.assertFalse(hardware.parse_secure_boot(bytes([6, 0, 0, 0, 0])))
        self.assertIsNone(hardware.parse_secure_boot(None))
        self.assertIsNone(hardware.parse_secure_boot(b"\x06"))

    def test_input_report_never_contains_device_names(self):
        sample = "\n\n".join([
            'N: Name="Microsoft Surface Keyboard"',
            'N: Name="Microsoft Surface Touchpad"',
            'N: Name="Private Headphones BT"',
            'N: Name="IPTS Touch"',
            'N: Name="Surface Pen"',
        ])
        result = hardware.classify_input(sample)
        self.assertEqual(result, {"has_keyboard": True, "has_touchpad": True,
                                  "has_touchscreen": True, "has_pen": True})
        self.assertNotIn("Headphones", str(result))
        self.assertEqual(hardware.classify_input(""), {"has_keyboard": False, "has_touchpad": False,
                                                       "has_touchscreen": False, "has_pen": False})

    def test_audio_cards_keep_only_short_names(self):
        sample = " 0 [sofhdadsp      ]: sof-hda-dsp - sof-hda-dsp\n                      Microsoft Corporation Surface\n"
        self.assertEqual(hardware.parse_audio_cards(sample), ["sof-hda-dsp"])

    def test_surface_kernel_modules_are_filtered(self):
        sample = "surface_aggregator 1 0 - Live\nkvm_intel 1 0 - Live\nsurface_hid 1 0 - Live\n"
        self.assertEqual(hardware.surface_modules(sample), ["surface_aggregator", "surface_hid"])

    def test_report_has_expected_fields_and_no_identifiers(self):
        data = hardware.report()
        text = str(data).lower()
        for banned in ("serial_number", "uuid", "mac_address", "ip_address"):
            self.assertNotIn(banned, text.replace("serial numbers, uuids", ""))
        for key in ("target", "secure_boot_enabled", "input", "firmware_version", "display_panels"):
            self.assertIn(key, data)

    def test_wallpaper_retries_the_real_operation(self):
        session = (ROOT / "image/live-preview/root/usr/local/bin/kavika-live-session").read_text()
        self.assertIn("if plasma-apply-wallpaperimage --fill-mode preserveAspectFit", session)
        self.assertIn("seq 1 45", session)

    def test_os_release_presents_kavika_identity(self):
        osr = (ROOT / "image/live-preview/root/usr/lib/os-release").read_text()
        self.assertIn('NAME="Kavi\'ka OS"', osr)
        self.assertIn("ID=kavika", osr)
        self.assertIn("ID_LIKE=fedora", osr)
        # $releasever must keep resolving, so VERSION_ID stays the Fedora release.
        self.assertIn("VERSION_ID=44", osr)

    def test_windows_provisioning_guide_ships_and_is_honest(self):
        guide = (ROOT / "image/live-preview/root/usr/share/kavika/WINDOWS.txt").read_text()
        self.assertIn("WHAT IT DOES NOT CONTAIN", guide)
        self.assertIn("No Windows, no Windows licence", guide)
        self.assertIn("windows-install-recipe.md", guide)
        self.assertIn("NEVER reuse", guide)  # the D23 trap
        self.assertIn("kavika-windows-provision", guide)  # names the shipped command

    def test_builder_ships_the_windows_launcher(self):
        # The overlay assembly now lives in the shared kavika_overlay module used by both builders.
        overlay_src = (ROOT / "tools/kavika_overlay.py").read_text()
        self.assertIn('payload / "usr/local/lib/kavika/launch-windows-vm-linux.py"', overlay_src)
        self.assertIn("tools/launch-windows-vm-linux.py", overlay_src)

    def test_builder_ships_the_installer_assets(self):
        overlay_src = (ROOT / "tools/kavika_overlay.py").read_text()
        self.assertIn('payload / "usr/local/sbin/kavika-install"', overlay_src)
        self.assertIn('payload / "usr/lib/kavika/installer/kavika.ks"', overlay_src)
        builder_src = (ROOT / "tools/build-live-preview.py").read_text()
        self.assertIn('"installer_assets_included": True', builder_src)
        self.assertNotIn('installer_supported": True', builder_src)  # still a preview, not an installer

    def test_workspace_script_explains_missing_virtualization_stack(self):
        script = (ROOT / "image/live-preview/root/usr/local/bin/kavika-windows-workspace").read_text()
        self.assertIn("qemu-system-x86_64", script)
        self.assertIn("WINDOWS.txt", script)

    def test_test_centre_wording_is_current(self):
        tc = (ROOT / "image/live-preview/root/usr/local/bin/kavika-test-centre").read_text()
        self.assertNotIn("Pro 8 target", tc)
        self.assertIn("HP Envy install target", tc)
        self.assertIn("Firefox", tc)

if __name__ == "__main__":
    unittest.main()
