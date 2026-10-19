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

    @unittest.skipUnless(shutil.which("grub-script-check"), "GRUB parser unavailable")
    def test_upstream_nested_video_function_is_normalized(self):
        source = (
            'if [ "$grub_platform" == "efi" ]; then\n'
            '\tfunction load_video {\n\t\tinsmod all_video\n\t}\n'
            'else\n\tfunction load_video {\n\t\tinsmod all_video\n\t}\nfi\n'
            'load_video\nlinux root=live:CDLABEL=Fedora-KDE-Live-44\n')
        result = builder.grub_preview(source)
        parsed = subprocess.run(["grub-script-check"], input=result, text=True, capture_output=True)
        self.assertEqual(parsed.returncode, 0, parsed.stderr)

    def test_preview_is_explicit_about_missing_windows(self):
        guide = (ROOT / "image/live-preview/root/usr/share/kavika/START-HERE.txt").read_text()
        self.assertIn("not Windows", guide)
        self.assertIn("not an installation release", (
            ROOT / "image/live-preview/root/usr/bin/liveinst").read_text())

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

    def test_wallpaper_retries_the_real_operation(self):
        session = (ROOT / "image/live-preview/root/usr/local/bin/kavika-live-session").read_text()
        self.assertIn("if plasma-apply-wallpaperimage --fill-mode preserveAspectFit", session)
        self.assertIn("seq 1 45", session)

if __name__ == "__main__":
    unittest.main()
