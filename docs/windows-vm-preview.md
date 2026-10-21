# Kavi'ka OS Windows-host preview VM

This is a **throwaway Fedora-based Linux diagnostic VM** to resume the handoff's requested fresh-boot check. It is not Windows, has no Comet, and does not demonstrate the Kavi'ka Linux/Windows product.

## Isolation and resource budget

The launcher verifies the ISO hash/size, current 5-GiB free-RAM guard, and an empty VM directory before creating any guest storage. It creates only a private 24-GiB QCOW2 disk and disposable UEFI variable file. The QEMU command has no physical disk passthrough or shared-folder option; networking is user-mode NAT. The QCOW2 is not a Fedora installation target—do not start Anaconda.

The Windows hypervisor reports no SLAT for nested virtualization. The launcher checks for **5 GiB free RAM** before allocating the 4-GiB guest and defaults to slow TCG. A tiny real-mode guest has been verified under WHPX on this helper; that does not establish that Fedora/KDE will work there. The launcher accepts `--accel whpx` and writes QEMU diagnostics to `qemu.stderr.log`. Recheck free RAM immediately before launch. This test VM does not validate Surface hardware.

## Launch on the configured Windows helper

The helper must have QEMU 11.1 under `C:\Program Files\qemu\`. The local ISO hash from the validation record is `10074299b974eb005d0a38144d74b0dc02e1fa128684eb0f81b9cc9829a177ac` (3370254336 bytes). The hash `226d4fc0c57b18c43a725503664c59dcbb7e7767fa479be331760a91f5b5fc82` in tracked sidecar/manifest files is an older build and not accepted by the current launcher. Verify ISO provenance before use. Do not disable execution-policy/security controls.

From the checkout, using a fresh empty directory:

```powershell
python .\tools\launch-preview-vm-windows.py `
  --iso "C:\path\to\Kavika-OS-0.1.0-Surface-Pro-8-Live-Preview.iso" `
  --vm-dir "C:\Users\<your-user>\Kavika-Preview-Test"
```

Use the new `--accel whpx` option only after the tiny WHPX probe passes. The probe only showed tiny guest CPU execution, so GUI/KDE may still fail. Inspect the QEMU window, serial `qemu.log`, and `qemu.stderr.log` before claiming a GUI boot. If display remains black or boot stalls, stop the VM and preserve logs for diagnosis. Never fall back to full TCG on this host for another long boot.

## Start/stop and cleanup

Close the VM window normally to stop it. The VM's files remain under the requested VM directory. Preserve the ISO, `manifest.json`, `qemu.log`, and `efi-vars.fd` only if you need to keep testing; they are not product-release artifacts. Delete the **whole throwaway VM directory** only after the VM has exited and only after confirming the exact path. The sparse virtual disk contains no user files unless you explicitly save data within the guest.

A successful launcher return merely means QEMU started; only an observed guest desktop and recorded output-hash check count as a boot test. Do not publish, flash, or install this preview from that result.

## Linux hosts (including the Surface Laptop Studio)

A Linux host with KVM does not need this Windows launcher or software emulation. Use `tools/launch-preview-vm-linux.py` instead. It requires an ISO hash (or `.sha256` file), a new empty VM directory, at least 5 GiB of available RAM and a usable `/dev/kvm`. It attaches only a private QCOW2 disk and user-mode networking, never a physical disk or shared folder. See [the Laptop Studio page](surface-laptop-studio-test-machine.md).

### A full Windows 11 guest on a Linux/KVM host

`tools/launch-windows-vm-linux.py` is the feasibility harness for the product's Windows side: it boots a general-purpose Windows 11 guest so the real question — does full Windows run acceptably here alongside Linux — can be measured. It fetches nothing: you supply your own Windows 11 ISO, and no licence key, recovery key or activation data is stored by the project.

What it presents, chosen so Windows 11 Setup boots without extra drivers:

| Component | Choice | Why |
|---|---|---|
| Firmware | OVMF UEFI with a private variable store | Windows 11 requires UEFI |
| TPM | `swtpm`, TPM 2.0, state inside the VM directory | Windows 11 requires TPM 2.0 |
| System disk | NVMe (`stornvme` is in-box) | avoids needing virtio-win just to install |
| Network | `e1000e` on user-mode NAT, no forwarding | in-box driver, host not exposed |
| Display | standard VGA | virtio-gpu would need guest drivers first |

`--virtio-iso` attaches a virtio-win CD once you want virtio devices. Isolation is the same as the preview launcher: new private QCOW2, private TPM state, user-mode NAT, and no physical disk or shared folder. Run `--dry-run` first; it performs every host check, prints the exact QEMU command and creates nothing.

Windows-specific caveats: licensing and activation are yours to handle, the guest's performance on this host has not been measured yet, and a VM limitation must be reported rather than quietly redefined as out of scope. This harness does not restrict what you install inside Windows.

**The launcher alone is not enough to boot Setup.** The Windows ISO's El Torito payload hangs under OVMF, so Setup has to be booted from an ESP image attached as USB storage, with a separate removable answer stick and `--allow-reboot`. The full, verified procedure (the ESP layout, the answer-file bypass, and the write-protect trap) is in [the Windows install recipe](windows-install-recipe.md).
