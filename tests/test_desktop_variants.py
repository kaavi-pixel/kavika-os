"""Desktop-variant checks: GNOME is an option, KDE remains the unchanged default."""
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "tools"))
import importlib.util
import kavika_overlay  # noqa: E402

spec = importlib.util.spec_from_file_location("netinst_builder", ROOT / "tools/build-netinst-install.py")
netinst_builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(netinst_builder)


class DesktopVariantTests(unittest.TestCase):
    def test_kde_remains_the_default_kickstart(self):
        source = (ROOT / "image/install/kavika-net.ks").read_text()
        self.assertEqual(netinst_builder.apply_desktop(source, "kde"), source)

    def test_gnome_uses_fedora_workstation_and_gdm(self):
        source = (ROOT / "image/install/kavika-net.ks").read_text()
        out = netinst_builder.apply_desktop(source, "gnome")
        self.assertIn("@workstation-product-environment", out)
        self.assertIn("\ngdm\n", out)
        self.assertNotIn("@kde-desktop-environment", out)
        self.assertNotIn("\nsddm\n", out)
        self.assertIn("Fedora GNOME 44", out)
        self.assertNotIn("Fedora KDE 44", out)

    def test_gnome_overlay_drops_kde_only_files(self):
        with tempfile.TemporaryDirectory() as td:
            payload = kavika_overlay.build_overlay_payload(ROOT, Path(td) / "payload", desktop="gnome")
            for rel in ("etc/skel/.config/kwinrc",
                        "etc/skel/.config/kded_device_automounterrc",
                        "usr/bin/plasma-welcome",
                        "usr/share/kwin/scripts/kavika-preview/metadata.json"):
                self.assertFalse((payload / rel).exists(), rel)
            self.assertTrue((payload / "usr/local/bin/kavika-gnome-session-setup").is_file())
            self.assertTrue((payload / "etc/skel/.config/autostart/kavika-gnome-session-setup.desktop").is_file())

    def test_kde_overlay_keeps_kde_workspace_configuration(self):
        with tempfile.TemporaryDirectory() as td:
            payload = kavika_overlay.build_overlay_payload(ROOT, Path(td) / "payload", desktop="kde")
            self.assertTrue((payload / "etc/skel/.config/kwinrc").is_file())
            self.assertTrue((payload / "usr/share/kwin/scripts/kavika-preview/metadata.json").is_file())


if __name__ == "__main__":
    unittest.main()
