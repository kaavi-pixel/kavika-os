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
  (offline variant: bundled repo of 2455 RPMs + comps.xml, source = `cdrom`).
  The install proof below used build `6df5fe2537594656d0ef81cef4d61c3996ed12d35245149f1bcc0cd29e2591b6`;
  the current build is `160b805824705d13ac646d5bc1440702cc0af0699ff19fa6dc3b7ce9fa1304d5`
  (identical except the `%pre` now prints refusal reasons to the serial console).
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

## T19 evidence — attached non-selected disk unchanged

The installer was run with **two** disks attached in the same guest: the target (`/dev/vda`,
256 GiB virtio qcow2) and a fixture (`/dev/vdb`, 256 MiB raw) whose content was hashed
before and after.

- fixture before: `a6d72ac7690f53be6ae46ba88506bd97302a093f7108472bd9efc3cefda06484`
- fixture after:  `a6d72ac7690f53be6ae46ba88506bd97302a093f7108472bd9efc3cefda06484`
- `sha256sum -c`: **OK** ; target after: 14.6 GiB (the install ran)

Anaconda's log shows the layout was created on `/dev/vda` only (`Creating ext4 on
/dev/vda3…vda5`, `efi on /dev/vda1`) — `/dev/vdb` was never touched. The before/after hash
is the evidence, not the installer's exit code.

## Refusal matrix (validation rung 2)

Each refusal ISO boots the automated installer with bad consent baked into the install
entry (via `build-netinst-install.py --test-consent "<string>"`), with the same target +
fixture attached. In every case the `%pre` refused, printed its reason to the serial
console, and Anaconda terminated **before any storage write** — the target qcow2 stayed at
196 KiB and no `Creating ext4` line appeared:

| Case | Consent on the cmdline | `%pre` refusal (serial) | Target |
|---|---|---|---|
| none | *(none)* | `KAVIKA CONSENT-REFUSED: no kavika.target= on the kernel command line; refusing to install` | 196 KiB |
| mismatch | `kavika.target=/dev/vda kavika.confirm=/dev/vdb` | `KAVIKA CONSENT-REFUSED: kavika.target (/dev/vda) != kavika.confirm (/dev/vdb)` | 196 KiB |
| small | `kavika.target=/dev/vdb kavika.confirm=/dev/vdb` | `KAVIKA CONSENT-REFUSED: vdb is too small (268435456 < 257698037760 bytes)` | 196 KiB |
| pseudo | `kavika.target=/dev/zram0 kavika.confirm=/dev/zram0` | `KAVIKA CONSENT-REFUSED: /dev/zram0 is a pseudo-disk` | 196 KiB |

In every case the anaconda error was `Unable to open input kickstart file: … '/tmp/kavika-storage.ks'`
followed by `The installer will now terminate.` — the `%pre` did not write the scoped-storage
include, so Anaconda had nothing to act on and stopped. The fixture hash stayed
`a6d72ac7…` in all four cases too.

## Not done / not authorised here

- A physical-disk install, and any write to the Laptop Studio NVMe or the HP Envy. The
  Envy still needs a fresh explicit go/no-go with its exact disk identified.
- The interactive graphical consent UI (the fail-closed device consent is the `%pre`
  reading `kavika.target`/`kavika.confirm` from the kernel command line; a friendlier
  in-boot dialog is a later UX step).
- The Windows guest itself (this install provisions the *stack*; Windows provisioning
  stays the T20 first-boot opt-in, which does nothing automatically).
