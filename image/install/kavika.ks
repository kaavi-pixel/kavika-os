# Kavi'ka OS installer kickstart — v1 TEMPLATE
#
# Not validated against a live Anaconda run yet (see installerinstallation.md §3 and the
# validation ladder). It is a template: the operator-confirmed target device is substituted
# into every @@TARGET_DEVICE@@ by tools/kavika-install.py, which refuses to launch Anaconda
# until the device has been confirmed twice and every safety check has passed.
#
# D2 (the "Install Kavi'ka OS" boot entry) and D4 (the %post that delivers the Kavi'ka
# overlay onto the installed root) are now wired; see installerinstallation.md.

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

%post --nochroot --log=/root/kavika-overlay.log
# D4: deliver the Kavi'ka overlay delta onto the installed root. Anaconda's live install
# copies the stock Fedora KDE squashfs; the overlay is what makes it Kavi'ka OS (os-release
# identity, branding, kavika tooling, Windows-workspace plumbing, wallpaper). The builder
# nests a clean cpio of the overlay at /usr/lib/kavika/installer/kavika-overlay.cpio.
SYSROOT=/mnt/sysimage
[ -d /mnt/sysroot ] && SYSROOT=/mnt/sysroot
if [ -f /usr/lib/kavika/installer/kavika-overlay.cpio ]; then
    ( cd "$SYSROOT" && cpio -idmu --quiet < /usr/lib/kavika/installer/kavika-overlay.cpio )
else
    echo "KAVIKA: overlay cpio missing; installed system is stock Fedora KDE" >&2
fi
# Live-preview-only hooks must not run on the installed system.
rm -f "$SYSROOT/etc/xdg/autostart/kavika-live.desktop"
rm -f "$SYSROOT/var/lib/livesys/livesys-session-extra"
# Installer-only files are meaningless on an installed system.
rm -f "$SYSROOT/usr/bin/liveinst" "$SYSROOT/usr/libexec/kavika/real-liveinst"
rm -f "$SYSROOT/usr/local/sbin/kavika-install" "$SYSROOT/usr/lib/kavika/installer/kavika.ks"
%end

# NOTE (installerinstallation.md D5): live installs copy the squashfs, so %packages is not
# honored here. The virtualization stack (qemu-kvm, swtpm, swtpm-tools, edk2-ovmf, mtools,
# virt-install) is provisioned post-install by the Windows-workspace opt-in (T20), tracked
# separately; it is deliberately not baked into this live install.
