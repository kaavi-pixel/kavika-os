# Kavi'ka OS installer kickstart — v1 TEMPLATE
#
# Not validated against a live Anaconda run yet (see installerinstallation.md §3 and the
# validation ladder). It is a template: the operator-confirmed target device is substituted
# into every @@TARGET_DEVICE@@ by tools/kavika-install.py, which refuses to launch Anaconda
# until the device has been confirmed twice and every safety check has passed.
#
# Still to wire (installerinstallation.md): the "%post" delivery of the Kavi'ka overlay onto
# the installed root (D4), and the "Install Kavi'ka OS" boot entry (D2). This file describes
# the storage, packages and first-boot contract; it is not, by itself, a working installer.

lang en_GB.UTF-8
keyboard uk
timezone UTC --utc

# Storage — scoped to the one confirmed device; every other disk is ignored.
ignoredisk --only-use=@@TARGET_DEVICE@@
clearpart --all --initlabel --drives=@@TARGET_DEVICE@@
part /boot/efi --fstype=efi --size=1024
part /boot --fstype=ext4 --size=2048
part / --fstype=btrfs --size=61440 --grow
part /home --fstype=btrfs --size=20480
part /var/lib/kavika/windows --fstype=btrfs --size=131072

# Bootloader pinned to the confirmed device (Anaconda handles the EFI path).
bootloader --boot-drive=@@TARGET_DEVICE@@

# First boot runs the interactive user-creation step (initial-setup), then the Kavi'ka
# Windows-workspace opt-in (T20). No user password is baked in here.
firstboot --enable

%packages
@kde-desktop-environment
# The virtualization stack the live preview omits, so the installed system can provision
# and run the Windows workspace (WINDOWS.txt / docs/windows-install-recipe.md).
qemu-kvm
swtpm
swtpm-tools
edk2-ovmf
mtools
virt-install
virt-manager
%end
