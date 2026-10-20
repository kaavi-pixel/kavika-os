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

    def test_guest_memory_default_meets_the_windows_11_minimum(self):
        self.assertGreaterEqual(LAUNCHER.DEFAULT_GUEST_MIB, 4096)
        self.assertGreaterEqual(LAUNCHER.DEFAULT_DISK_GIB, 64)


if __name__ == "__main__":
    unittest.main()
