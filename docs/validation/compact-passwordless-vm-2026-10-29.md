# Compact passwordless VM validation — 29 October 2026

## Scope and artefact

End-to-end validation of the **test-only compact, passwordless** installer on a disposable 120 GB
QCOW2 disk. This is not a shipped product configuration and must not be used for the Envy.

- Image: `build/Kavika-OS-0.1.0-test-passwordless-compact.iso`
- SHA-256: `7e40a7f8cfdb82d9af240031821ae02167efb1bcd1430651e5376bdf15dcd0fa`
- `checkisomd5`: **PASS**
- Install VM allocation: **2.5 GiB RAM** (reduced after D48's OOM kill)
- Target presented to the installer as `/dev/nvme0n1`

## Install result

The installer reached **2465/2465 packages**, generated the initramfs, completed `%post`, and
ended with `reboot: Restarting system`. Console evidence included:

- `installed PRETTY_NAME="Kavi'ka OS 0.1.0 (Fedora KDE 44)"`
- `os-release=Kavika`
- `default target = graphical`
- `display manager enabled: sddm`
- `initial-setup masked (D46)`
- `ESP UUID matches fstab`
- `/boot/efi marked nofail`
- `TEST-ONLY passwordless autologin and sudo enabled`

## Graphical session

The installed disk booted with no install media attached. The KDE first-run wizard completed
(`Your device is now ready. Enjoy Kavi'ka OS!`). After a subsequent reboot, SDDM autologin produced
a graphical `calebz` session.

Final evidence: [compact-passwordless-desktop-2026-10-29.png](../evidence/compact-passwordless-desktop-2026-10-29.png)

Runtime checks inside the installed system:

- `plasmashell`, `kwin_wayland`, `Xwayland`, and `kded6` running
- `systemctl is-system-running`: **running**
- Failed units: **0**
- `loginctl`: graphical `calebz` session present

## Account, sudo and password behaviour

- `id`: `calebz` is UID 1000 and a member of `wheel`
- `sudo -n true`: **PASS** (the test-only NOPASSWD rule works)
- The normal fallback password also works for a text-console login
- The root filesystem is mounted **read-write**
- `/usr/bin/passwd` has its setuid bit
- `/etc/shadow` attributes are normal

D47 reproduction attempt: after `chage -d 0 calebz`, `passwd` accepted the old password and
successfully set a new one (`passwd: *** updated successfully`). **The Envy password-change
failure is not reproducible with this installer path**, so no general account-creation fix is
indicated by that report alone.

## Network, MAC and package/tool checks

- Default route through the VM network: present
- DNS resolution for the Fedora download host: works
- `getenforce`: **Enforcing**
- Installed and verified: `sddm`, `plasma-workspace`, `qemu-kvm`, `swtpm`, `edk2-ovmf`, `mtools`,
  `7zip`, `parted`, `dosfstools`
- `kavika-windows-provision`, `kavika-windows-workspace`, and `kavika-windows-optin` are present
- `kavika-windows-provision --help` runs and documents `--dry-run` and `--disk-gib`

No new Windows guest was provisioned in this run; the existing Windows provisioning proof remains
a separate validation record.

## Compact layout

- `/`: 66 GB, 9.5 GB used
- `/home`: 10 GB
- `/var/lib/kavika/windows`: 40 GB

The compact layout is suitable for the 119.2 GB test target. A future Windows guest must use a
smaller disk allocation (for example `--disk-gib 32`), not the default 64 GiB.

## Physical follow-up

The first physical KIOXIA attempt was OOM-killed (D48). The physical rerun script now uses 3 GiB
and its dry-run passes against the correctly identified target. A raw physical write still requires
the operator's interactive sudo command; this VM result does not claim that write has happened.
