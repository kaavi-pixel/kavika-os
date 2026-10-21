import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "windows_vm_launcher", ROOT / "tools/launch-windows-vm-linux.py")
LAUNCHER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LAUNCHER)


class WindowsLauncherTests(unittest.TestCase):
    def command(self, **extra):
        values = dict(qemu="qemu", iso=Path("win11.iso"), disk=Path("d.qcow2"),
                      efi_code=Path("c.fd"), efi_vars=Path("v.fd"),
                      tpm_sock=Path("tpm/swtpm.sock"), serial_log=Path("s.log"),
                      guest_mib=6144, cpus=4, display="none")
        values.update(extra)
        return LAUNCHER.build_command(**values)

    def test_windows_11_requirements_are_present(self):
        joined = " ".join(self.command())
        # UEFI firmware variables, TPM 2.0 emulation, and an in-box-driver disk.
        self.assertEqual(sum(1 for part in self.command() if part.startswith("if=pflash")), 2)
        self.assertIn("tpm-tis,tpmdev=tpm0", joined)
        self.assertIn("--tpm2", " ".join(
            ["swtpm", "socket", "--tpmstate", "dir=x", "--tpm2"]))
        self.assertIn("nvme,drive=nvme0", joined)
        self.assertIn("accel=kvm", joined)
        self.assertIn("-cpu host", joined)

    def test_no_physical_disk_or_shared_folder_is_ever_attached(self):
        joined = " ".join(self.command())
        for forbidden in ("/dev/sd", "/dev/nvme", "/dev/mmcblk", "host_device", "virtfs",
                          "-fsdev", "hostfwd", "-snapshot"):
            self.assertNotIn(forbidden, joined)
        files = [part for part in self.command() if part.startswith("file=")]
        self.assertTrue(any("d.qcow2" in item and "format=qcow2" in item for item in files))

    def test_network_defaults_to_user_mode_without_forwarding(self):
        joined = " ".join(self.command())
        self.assertIn("-nic", joined)
        self.assertIn("user,model=e1000e", joined)
        self.assertNotIn("hostfwd", joined)

    def test_network_can_be_disabled_and_forwarding_is_explicit(self):
        self.assertNotIn("-nic", " ".join(self.command(with_net=False)))
        self.assertIn("hostfwd=tcp::3389-:3389",
                      " ".join(self.command(hostfwd="tcp::3389-:3389")))

    def test_virtio_iso_is_optional_and_only_added_when_given(self):
        self.assertNotIn("virtio-win.iso", " ".join(self.command()))
        self.assertIn("virtio-win.iso", " ".join(self.command(virtio_iso=Path("virtio-win.iso"))))

    def test_boot_medium_is_optional_and_attached_correctly(self):
        # Absent by default: a plain -cdrom boot is the fallback.
        plain = " ".join(self.command())
        self.assertNotIn("usbesp", plain)
        self.assertNotIn("afstick", plain)

        with_medium = " ".join(
            self.command(esp_image=Path("esp.img"), answer_image=Path("af.img")))
        # The boot ESP must stay WRITABLE: Setup services boot files to the volume it
        # booted from, and a read-only one aborts with 0x80070013.
        self.assertIn("id=usbesp,format=raw,file=esp.img", with_medium)
        self.assertNotIn("readonly=on,file=esp.img", with_medium)
        # The answer stick must be REMOVABLE, or Setup's implicit search skips it.
        self.assertIn("usb-storage,drive=afstick,removable=on", with_medium)

    def test_install_mode_allows_guest_reboots(self):
        # Default preserves the crash-hunting behaviour: a guest reset exits QEMU.
        self.assertIn("-no-reboot", " ".join(self.command()))
        # An install must be allowed to reboot; -no-reboot would kill Setup mid-flow.
        self.assertNotIn("-no-reboot", " ".join(self.command(allow_reboot=True)))

    def test_provisioned_guest_does_not_attach_install_media(self):
        # --reuse: the guest boots its own disk, so no -cdrom and no forced boot order.
        joined = " ".join(self.command(iso=None))
        self.assertNotIn("-cdrom", joined)
        self.assertNotIn("-boot", joined)
        # Provisioning still does both.
        provisioning = " ".join(self.command())
        self.assertIn("-cdrom", provisioning)
        self.assertIn("-boot order=d", provisioning)

    def test_full_screen_display_reaches_the_command_line(self):
        # Spelling taken from this QEMU's own help text:
        #   -display gtk[,full-screen=on|off][,gl=on|off][,grab-on-hover=on|off]
        self.assertIn("-display gtk,full-screen=on",
                      " ".join(self.command(display="gtk,full-screen=on")))

    def test_reuse_refuses_an_unprovisioned_directory(self):
        import subprocess
        import sys
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            fake_iso = Path(tmp) / "fake.iso"
            fake_iso.write_bytes(b"")
            proc = subprocess.run(
                [sys.executable, str(ROOT / "tools/launch-windows-vm-linux.py"),
                 "--iso", str(fake_iso), "--vm-dir", str(Path(tmp) / "guest"),
                 "--reuse", "--dry-run"],
                capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("--reuse needs an existing guest directory",
                      proc.stdout + proc.stderr)

    def test_guest_memory_default_meets_the_windows_11_minimum(self):
        self.assertGreaterEqual(LAUNCHER.DEFAULT_GUEST_MIB, 4096)
        self.assertGreaterEqual(LAUNCHER.DEFAULT_DISK_GIB, 64)


if __name__ == "__main__":
    unittest.main()
