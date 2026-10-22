# VM install validation — automated dnf/netinst installer

22 October 2026 | Surface Laptop Studio (KVM) | disposable qcow2 target | zero physical-disk risk

## What was proven

The automated (dnf) installer — Path B — installed Kavi'ka OS to a blank 256 GiB
virtio disk inside a disposable KVM guest, with **no interactive input**, and the
installed system booted with the Kavi'ka identity and the virtualization stack.

## Inputs

- Base: `Fedora-Everything-netinst-x86_64-44-1.7.iso`
  (sha256 `bd285201494dd0ba09b54d05ac707de1401668b8512a573edb5922dcf9d7067e`).
- Installer ISO: `build/Kavika-OS-0.1.0-netinst-installer.iso`
  sha256 `6df5fe2537594656d0ef81cef4d61c3996ed12d35245149f1bcc0cd29e2591b6`
  (offline variant: bundled repo of 2455 RPMs + comps.xml, source = `cdrom`).
- Kickstart: `image/install/kavika-net.ks` (bundled as `/kavika-net.ks`).
- Target: `/dev/vda` (256 GiB virtio qcow2), consented via the test GRUB entry's
  `kavika.target=/dev/vda kavika.confirm=/dev/vda`.

## Install flow (all unattended)

1. GRUB default entry `Install Kavi'ka OS (automated)` → `inst.ks=hd:LABEL=…:/kavika-net.ks`.
2. `%pre` consent: read `kavika.target`/`kavika.confirm`, verified match + whole-disk +
   not-mounted + size ≥ 240 GiB + not-pseudo, then wrote the scoped storage block
   (`ignoredisk --only-use`, `clearpart --drives`, five `part` lines, `bootloader --boot-drive`).
3. Anaconda automated (no remote-desktop prompt because "text mode was explicitly asked for").
4. ext4 filesystems created on vda3/4/5/2 + efi on vda1 (no btrfs — see bug note below).
5. 2452 packages installed from the bundled cdrom repo (offline).
6. `%post --nochroot` delivered the Kavi'ka overlay and wrote verification to the console.

## `%post` verification evidence (from the serial console)

```
KAVIKA-VERIFY: overlay delivered from /run/install/repo/kavika-overlay.cpio
KAVIKA-VERIFY: os-release=Kavika
KAVIKA-VERIFY: pkg qemu-kvm-10.2.2-1.fc44.x86_64
KAVIKA-VERIFY: pkg swtpm-0.10.2-1.fc44.x86_64
KAVIKA-VERIFY: pkg edk2-ovmf-20260812-8.fc44.noarch
KAVIKA-VERIFY: pkg mtools-4.0.49-3.fc44.x86_64
```

## First-boot evidence (after ejecting the installer media)

```
Welcome to Kavi'ka OS 0.1.0 (Live Preview, Fedora KDE 44)!
[ OK ] Listening on virtqemud.socket - libvirt QEMU daemon socket.
         Starting virtqemud.service - libvirt QEMU daemon...
         Starting initial-setup.service - Initial Setup configuration program...
1) [ ] User creation
```

- Identity: `/etc/os-release` (→ `usr/lib/os-release`) resolves to the Kavi'ka identity.
- Virtualization stack present (libvirt/QEMU daemon, plus swtpm/edk2-ovmf/mtools confirmed).
- `firstboot --enable` ran `initial-setup` for interactive user creation (T20 gate, no
  baked password).

## Bugs found and fixed during this validation

- **btrfs + `--grow` root failed** with `mount failed: bad superblock on /dev/vda5`
  (root btrfs invalid after "Creating btrfs"). Switched the data partitions to ext4;
  root `--grow` moved last. (ext4 is robust; btrfs is a later refinement.)
- **`cpio -idm` skipped overwrites** — the overlay cpio is built `--reproducible`
  (timestamps 1970), so plain `cpio -i` did not replace newer on-disk files and the
  os-release identity never landed. Fixed with `cpio -idmu` (unconditional) in both
  kickstarts.
- **offline repo needed group metadata** — anaconda's mandatory `@core` (and our
  `@kde-desktop-environment`) failed with "No match for argument: core" until `comps.xml`
  was added to the local repo (`createrepo_c -g comps.xml`).
- **offline repo was missing boot packages** — `grub2-tools-extra`/`grubby`/`dosfstools`
  (anaconda's bootloader mandatory set) were added.

## Not done / not authorised here

- A physical-disk install, and any write to the Laptop Studio NVMe or the HP Envy. The
  Envy still needs a fresh explicit go/no-go with its exact disk identified.
- The interactive graphical consent UI (the fail-closed device consent is the `%pre`
  reading `kavika.target`/`kavika.confirm` from the kernel command line; a friendlier
  in-boot dialog is a later UX step).
- The Windows guest itself (this install provisions the *stack*; Windows provisioning
  stays the T20 first-boot opt-in, which does nothing automatically).
