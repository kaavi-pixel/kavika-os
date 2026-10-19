import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("linux_vm_launcher", ROOT / "tools/launch-preview-vm-linux.py")
LAUNCHER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LAUNCHER)

SHA = "ab" * 32


class LinuxLauncherTests(unittest.TestCase):
    def command(self, **extra):
        values = dict(qemu="qemu", iso=Path("p.iso"), disk=Path("d.qcow2"), efi_code=Path("c.fd"),
                      efi_vars=Path("v.fd"), serial_log=Path("s.log"))
        values.update(extra)
        return LAUNCHER.build_qemu_command(**values)

    def test_kvm_command_is_isolated_from_physical_disks_and_shares(self):
        joined = " ".join(self.command())
        self.assertIn("q35,accel=kvm", joined)
        self.assertIn("-cpu host", joined)
        self.assertIn("user,model=virtio-net-pci", joined)
        for forbidden in ("/dev/sd", "/dev/nvme", "host_device", "virtfs", "-fsdev", "hostfwd", "-snapshot"):
            self.assertNotIn(forbidden, joined)
        # Only the private QCOW2, the firmware files and the ISO are attached as storage.
        files = [part for part in self.command() if part.startswith("file=")]
        self.assertTrue(any("d.qcow2" in item and "format=qcow2" in item for item in files))

    def test_tcg_fallback_is_explicit(self):
        joined = " ".join(self.command(use_kvm=False))
        self.assertIn("q35,accel=tcg", joined)
        self.assertIn("-cpu max", joined)

    def test_memory_guard_needs_guest_plus_headroom(self):
        with self.assertRaisesRegex(ValueError, "available host RAM"):
            LAUNCHER.require_memory_budget(5 * 1024 - 1)
        self.assertEqual(LAUNCHER.require_memory_budget(5 * 1024), 4096)

    def test_mem_available_is_parsed_in_mib(self):
        text = "MemTotal: 16000000 kB\nMemAvailable: 10485760 kB\n"
        self.assertEqual(LAUNCHER.mem_available_mib(text), 10240)
        with self.assertRaises(ValueError):
            LAUNCHER.mem_available_mib("MemTotal: 1 kB\n")

    def test_sidecar_hash_is_validated(self):
        with tempfile.TemporaryDirectory() as temp:
            good = Path(temp) / "a.sha256"
            good.write_text(f"{SHA.upper()}  image.iso\n", encoding="ascii")
            self.assertEqual(LAUNCHER.read_sidecar_hash(good), SHA)
            bad = Path(temp) / "b.sha256"
            bad.write_text("not-a-hash  image.iso\n", encoding="ascii")
            with self.assertRaises(ValueError):
                LAUNCHER.read_sidecar_hash(bad)

    def test_firmware_lookup_reports_missing_ovmf(self):
        with self.assertRaisesRegex(FileNotFoundError, "edk2-ovmf"):
            LAUNCHER.first_existing(("/nonexistent/one.fd", "/nonexistent/two.fd"))

    def test_mismatched_iso_is_refused_before_any_vm_files_exist(self):
        with tempfile.TemporaryDirectory() as temp:
            iso = Path(temp) / "x.iso"
            iso.write_bytes(b"not the right image")
            vm_dir = Path(temp) / "vm"
            args = type("A", (), dict(iso=iso, vm_dir=vm_dir, expected_sha256=SHA, sha256_file=None,
                                      display="none", no_kvm=True))()
            fake = Path(temp) / "fw.fd"
            fake.write_bytes(b"fw")
            from unittest.mock import patch
            with patch.object(LAUNCHER.sys, "platform", "linux"), \
                 patch.object(LAUNCHER.shutil, "which", return_value="/usr/bin/fake"), \
                 patch.object(LAUNCHER, "first_existing", return_value=fake), \
                 patch.object(LAUNCHER, "mem_available_mib", return_value=10000), \
                 patch.object(LAUNCHER.Path, "read_text", return_value="MemAvailable: 1 kB"):
                with self.assertRaisesRegex(ValueError, "mismatch"):
                    LAUNCHER.launch(args)
            self.assertFalse(vm_dir.exists())


if __name__ == "__main__":
    unittest.main()
