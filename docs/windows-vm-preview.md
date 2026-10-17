# Kavi'ka OS Windows-host preview VM

This is a **throwaway Fedora-based Linux diagnostic VM** to resume the handoff's requested fresh-boot check. It is not Windows, has no Comet, and does not demonstrate the Kavi'ka Linux/Windows product.

## Isolation and resource budget

The launcher validates the ISO file size and SHA-256 against the validation record before it creates VM storage. It creates only a new, sparse 24 GiB QCOW2 file and private disposable UEFI variable file inside an otherwise-empty VM directory. It does not pass through physical disks, share a host folder, or bridge the VM onto the local network. Networking is QEMU user-mode NAT. The empty QCOW2 is not an installation target for this preview; do not start Anaconda from the live session.

The Windows hypervisor on this helper reports no SLAT for nested virtualization. The Windows VM launcher requires **at least 5 GiB free RAM** (4-GiB guest plus 1-GiB headroom), checks current free RAM, and uses slow TCG software emulation. It does not check installed RAM or use WHPX. Recheck free memory before launch; the Fedora desktop may be very slow. This test VM does not validate Surface hardware.

## Launch on the configured Windows helper

The helper must have QEMU 11.1 under `C:\Program Files\qemu\`. The local ISO hash from the validation record is `10074299b974eb005d0a38144d74b0dc02e1fa128684eb0f81b9cc9829a177ac` (3370254336 bytes). The hash `226d4fc0c57b18c43a725503664c59dcbb7e7767fa479be331760a91f5b5fc82` in tracked sidecar/manifest files is an older build and not accepted by the current launcher. Verify ISO provenance before use. Do not disable execution-policy/security controls.

From the checkout, using a fresh empty directory:

```powershell
python .\tools\launch-preview-vm-windows.py `
  --iso "C:\path\to\Kavika-OS-0.1.0-Surface-Pro-8-Live-Preview.iso" `
  --vm-dir "C:\Users\<your-user>\Kavika-Preview-Test"
```

The launcher refuses to reuse a non-empty VM directory. It opens a QEMU GUI window; if the VM firmware shows a boot menu, choose the Fedora live preview. On first boot, inspect the visible Linux desktop/Test Centre and KWin workspace toggle manually; check the generated `qemu.log` alongside the VM manifest. The VM is expected to boot from UEFI; if it fails, close it and capture the error/log. No previous-candidate evidence transfers to a new ISO hash.

## Start/stop and cleanup

Close the VM window normally to stop it. The VM's files remain under the requested VM directory. Preserve the ISO, `manifest.json`, `qemu.log`, and `efi-vars.fd` only if you need to keep testing; they are not product-release artifacts. Delete the **whole throwaway VM directory** only after the VM has exited and only after confirming the exact path. The sparse virtual disk contains no user files unless you explicitly save data within the guest.

A successful launcher return merely means QEMU started; only an observed guest desktop and recorded output-hash check count as a boot test. Do not publish, flash, or install this preview from that result.
