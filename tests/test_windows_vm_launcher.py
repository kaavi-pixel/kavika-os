import argparse
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("windows_vm_launcher", ROOT / "tools/launch-preview-vm-windows.py")
LAUNCHER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LAUNCHER)


class WindowsVmSafetyTests(unittest.TestCase):
    def test_memory_budget_refuses_low_ram_and_allows_five_gib(self):
        with self.assertRaisesRegex(ValueError, "free host RAM"):
            LAUNCHER.require_memory_budget(5 * 1024**3 - 1)
        self.assertEqual(LAUNCHER.require_memory_budget(5 * 1024**3), 4096)

    def test_insufficient_ram_is_reported_before_any_vm_directory_is_created(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            iso = root / "preview.iso"
            iso.write_bytes(b"not-read-because-of-ram-guard")
            vm_dir = root / "new-vm"
            for name in ("QEMU", "QEMU_IMG", "EFI_CODE", "EFI_VARS_TEMPLATE"):
                (root / (name + ".exe")).write_text("test stub")
            args = argparse.Namespace(iso=iso, vm_dir=vm_dir,
                                      expected_sha256="irrelevant",
                                      expected_bytes=iso.stat().st_size)
            with patch.object(LAUNCHER, "QEMU", root / "QEMU.exe"), \
                 patch.object(LAUNCHER, "QEMU_IMG", root / "QEMU_IMG.exe"), \
                 patch.object(LAUNCHER, "EFI_CODE", root / "EFI_CODE.exe"), \
                 patch.object(LAUNCHER, "EFI_VARS_TEMPLATE", root / "EFI_VARS_TEMPLATE.exe"), \
                 patch.object(LAUNCHER, "digest", return_value="irrelevant"), \
                 patch.object(LAUNCHER, "available_memory_bytes", return_value=4 * 1024**3), \
                 patch.object(LAUNCHER, "require_memory_budget", side_effect=ValueError("Need at least 5 GiB free host RAM")), \
                 patch.object(LAUNCHER.subprocess, "run") as run:
                with self.assertRaisesRegex(ValueError, "free host RAM"):
                    LAUNCHER.run_vm(args)
                run.assert_not_called()
            self.assertFalse(vm_dir.exists())

    def test_qemu_command_uses_only_the_named_iso_and_qcow2_disk(self):
        command = LAUNCHER.build_qemu_command(
            iso=Path("preview.iso"), disk=Path("throwaway.qcow2"),
            efi_vars=Path("vars.fd"), qemu=Path("qemu.exe"),
            efi_code=Path("code.fd"), serial_log=Path("serial.log"),
        )
        joined = " ".join(command)
        self.assertIn("accel=tcg", joined)
        self.assertIn("preview.iso", joined)
        self.assertIn("throwaway.qcow2", joined)
        self.assertNotIn("host_device", joined)
        self.assertNotIn("hostfwd", joined)
        self.assertNotIn("smb=", joined)
        self.assertNotIn("-hda", command)

    def test_qemu_command_can_use_w_h_p_x_without_changing_default(self):
        tcg = LAUNCHER.build_qemu_command(
            iso=Path("preview.iso"), disk=Path("throwaway.qcow2"),
            efi_vars=Path("vars.fd"), qemu=Path("qemu.exe"),
            efi_code=Path("code.fd"), serial_log=Path("serial.log"),
        )
        whpx_log = Path("probe.stderr.log")
        whpx = LAUNCHER.build_qemu_command(
            iso=Path("preview.iso"), disk=Path("throwaway.qcow2"),
            efi_vars=Path("vars.fd"), qemu=Path("qemu.exe"),
            efi_code=Path("code.fd"), serial_log=Path("serial.log"),
            accel="whpx", stderr_log=whpx_log,
        )
        self.assertIn("q35,accel=tcg", tcg)
        self.assertIn("q35,accel=whpx", whpx)
        self.assertIn("-D", whpx)
        self.assertIn(str(whpx_log), whpx)
        with self.assertRaises(ValueError):
            LAUNCHER.build_qemu_command(
                iso=Path("preview.iso"), disk=Path("throwaway.qcow2"),
                efi_vars=Path("vars.fd"), qemu=Path("qemu.exe"),
                efi_code=Path("code.fd"), serial_log=Path("serial.log"), accel="bad",
            )

    def test_launcher_pins_derived_iso_separately_from_fedora_base(self):
        self.assertEqual(LAUNCHER.EXPECTED_ISO_SHA256, "10074299b974eb005d0a38144d74b0dc02e1fa128684eb0f81b9cc9829a177ac")
        self.assertEqual(LAUNCHER.EXPECTED_ISO_BYTES, 3370254336)
        self.assertEqual(len(LAUNCHER.EXPECTED_ISO_SHA256), 64)


if __name__ == "__main__":
    unittest.main()
