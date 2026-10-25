#!/usr/bin/env bash
# Write the Kavi'ka diagnostic preview ISO to a removable USB device.
#
# This is a DESTRUCTIVE raw write: everything on the target device is erased.
# Because of that it refuses to run until several independent checks pass, and
# it must be given the device explicitly twice. Run it yourself, with root:
#
#   sudo bash tools/write-preview-to-usb.sh \
#       --iso build/Kavika-OS-0.1.0-Surface-Pro-8-Live-Preview.iso \
#       --sha256-file build/Kavika-OS-0.1.0-Surface-Pro-8-Live-Preview.iso.sha256 \
#       --device /dev/sdX --confirm-wipe /dev/sdX
#
# Add --dry-run to execute every check and print the plan without writing.
#
# External USB *hard drives* (SATA/ATA bridges in an enclosure) usually report RM=0
# because the bridge does not advertise removable media, unlike a USB flash stick.
# Such a disk is still a legitimate USB target, so pass --allow-fixed-usb to accept
# it. That override relaxes ONLY the removable-media flag: the whole-disk, USB
# transport, not-mounted, size, hash and double-naming checks all still apply, and the
# disk must still be named twice.
#
# Refused unless ALL of these hold:
#   * the target is a whole disk, not a partition
#   * the target is removable (RM=1) and on the USB transport, or RM=0 on USB with
#     --allow-fixed-usb
#   * the target is not the internal NVMe/NVMe-style system disk
#   * nothing on the target is mounted
#     If a device will not unmount with "target is busy", a file manager is almost always
#     holding the mountpoint: find it with `fuser -vm <mountpoint>` (GNOME Files shows as
#     `nautilus`, KDE as `dolphin`), quit it (`nautilus -q`) or close that window, then
#     unmount. This script deliberately never unmounts the target itself: a surprising
#     unmount is how the wrong disk gets erased.
#   * the target is at least as large as the image
#   * the ISO's SHA-256 matches the sidecar or --sha256 value
#   * --device and --confirm-wipe name the same device
#
# After writing it reads the image size back off the device and compares the
# SHA-256, so a short or corrupted write is reported rather than assumed.

set -u

die() { printf 'refusing: %s\n' "$1" >&2; exit 1; }

iso="" sha_file="" expected="" device="" confirm="" dry_run=0 verify_only=0 allow_fixed=0
while [ $# -gt 0 ]; do
  case "$1" in
    --iso) iso=$2; shift 2 ;;
    --sha256-file) sha_file=$2; shift 2 ;;
    --sha256) expected=$2; shift 2 ;;
    --device) device=$2; shift 2 ;;
    --confirm-wipe) confirm=$2; shift 2 ;;
    --dry-run) dry_run=1; shift ;;
    --verify-only) verify_only=1; shift ;;
    --allow-fixed-usb) allow_fixed=1; shift ;;
    *) die "unknown argument: $1" ;;
  esac
done

[ -n "$iso" ] || die "--iso is required"
[ -n "$device" ] || die "--device is required"
[ -n "$confirm" ] || die "--confirm-wipe is required (pass the same path as --device)"
[ -f "$iso" ] || die "no such ISO file: $iso"
[ -b "$device" ] || die "not a block device: $device"
[ "$device" = "$confirm" ] || die "--device and --confirm-wipe differ; nothing was written"

# A whole disk, never a partition.
if ! lsblk -ndo TYPE "$device" 2>/dev/null | grep -qx disk; then
  die "$device is not a whole disk (partitions must not be targeted)"
fi

# Never the system disk, whatever its transport claims.
root_source=$(findmnt -no SOURCE / 2>/dev/null | sed 's/\[.*//')
root_parent=$(lsblk -no PKNAME "$root_source" 2>/dev/null | head -1)
if [ -n "$root_parent" ] && [ "$device" = "/dev/$root_parent" ]; then
  die "$device carries the running system's root filesystem"
fi
case "$device" in
  *nvme*|*mmcblk*boot*|*loop*|*zram*) die "$device looks like an internal or virtual disk" ;;
esac

# Removable USB only, with an explicit opt-in for fixed-mode USB bridges.
tran=$(lsblk -ndo TRAN "$device" 2>/dev/null | tr -d ' ')
[ "$tran" = "usb" ] || die "$device transport is '$tran', not 'usb'"
rm_flag=$(lsblk -ndo RM "$device" 2>/dev/null | tr -d ' ')
if [ "$rm_flag" != "1" ]; then
  if [ "$allow_fixed" = "1" ]; then
    echo "note: $device reports RM=$rm_flag (a USB hard drive, not removable media)."
    echo "      --allow-fixed-usb was given, so this is accepted; the remaining checks still apply."
    lsblk -ndo NAME,SIZE,TYPE,RM,TRAN,MODEL "$device"
  else
    die "$device is not removable (RM=$rm_flag). A USB flash stick reports RM=1; an external USB hard drive usually reports RM=0 and is refused here. If this really is the external USB disk you mean, confirm its model above and rerun with --allow-fixed-usb."
  fi
fi

# Nothing mounted: fatal before a write, only a warning for the read-only paths.
mounted=$(lsblk -no MOUNTPOINT "$device" 2>/dev/null | grep -v '^$' || true)
if [ -n "$mounted" ]; then
  if [ "$dry_run" = "1" ] || [ "$verify_only" = "1" ]; then
    echo "note: $device has mounted partitions (harmless for this read-only run):"
    echo "$mounted" | sed 's/^/  /'
  else
    die "$device still has mounted partitions:
$mounted
Unmount them first, for example: udisksctl unmount -b ${device}1"
  fi
fi

# Size check.
iso_size=$(stat -c %s "$iso")
dev_size=$(lsblk -bndo SIZE "$device" | tr -d ' ')
[ "$dev_size" -ge "$iso_size" ] || die "image is $iso_size bytes but $device is only $dev_size bytes"
slack=$(( (dev_size - iso_size) / 1048576 ))

# Image identity.
echo "computing ISO SHA-256 (this reads the whole file)..."
actual=$(sha256sum "$iso" | cut -d' ' -f1)
if [ -n "$sha_file" ]; then
  expected=$(head -c 64 "$sha_file")
fi
if [ -n "$expected" ]; then
  [ "$actual" = "$expected" ] || die "ISO SHA-256 mismatch: expected $expected, got $actual"
  echo "ISO hash verified: $actual"
else
  echo "WARNING: no --sha256-file/--sha256 given; writing $actual without checking it"
fi

# Report what is about to be destroyed.
actual_label=$(blkid -p "$iso" -o value -s LABEL 2>/dev/null || true)
echo
echo "device : $device"
lsblk -o NAME,SIZE,TYPE,RM,TRAN,LABEL,FSTYPE,MODEL "$device"
echo "image  : $iso"
echo "         $iso_size bytes, slack ${slack} MiB"
echo

# The UEFI boot path is resolved by the GRUB config INSIDE the ISO's EFI System Partition, a
# different file from the one in the ISO9660 tree. If the two disagree about the volume label,
# a byte-perfect write still boots to "you need to load the kernel first". Read the ESP's own
# config directly (mtools at a partition offset, no loop mount) and say plainly what it holds.
esp_offset=""
esp_start=$(parted -s "$iso" unit s print 2>/dev/null | awk '$NF ~ /esp/ {print $2}' \
            | head -1 | tr -d 's')
case "$esp_start" in ''|*[!0-9]*) esp_start="" ;; esac
[ -n "$esp_start" ] && esp_offset=$(( esp_start * 512 ))

esp_config=""
if [ -n "$esp_offset" ] && command -v mtype >/dev/null 2>&1; then
  esp_config=$(mtype -i "${iso}@@${esp_offset}" ::/EFI/BOOT/grub.cfg 2>/dev/null || true)
fi

if [ -n "$esp_config" ]; then
  esp_label=$(printf '%s' "$esp_config" | sed -n "s/.*--set=root -l '\(.*\)'.*/\1/p" | head -1)
  if printf '%s' "$esp_config" | grep -qF "Install Kavi'ka OS (automated)"; then
    echo "ESP check: the EFI System Partition carries the Kavi'ka installer menu"
    echo "           (searches for label '${esp_label:-?}', image label '${actual_label:-?}')"
    if [ -n "$esp_label" ] && [ -n "$actual_label" ] && [ "$esp_label" != "$actual_label" ]; then
      die "the ESP searches for label '$esp_label' but the image is labelled '$actual_label'. UEFI would boot the stock menu, fail to find the media and report 'you need to load the kernel first'."
    fi
  else
    # Not an error: the writer also flashes stock Fedora media, which legitimately has no
    # Kavi'ka menu and boots its own upstream installer. The dangerous case - renamed media
    # whose ESP still searches for the old label - is caught by the label check above.
    echo "note: this media carries no Kavi'ka installer menu (expected for a stock Fedora ISO)."
    echo "      It will boot its own upstream Fedora installer menu."
  fi
elif [ -n "$esp_offset" ]; then
  echo "note: could not read the ISO's ESP GRUB config (is mtools installed?); skipping the check"
fi
echo

if [ "$dry_run" = "1" ]; then
  echo "--dry-run: all checks passed; nothing was written"
  exit 0
fi

# Read-back only: compare the image-sized prefix of the device with the ISO.
# Useful after writing the media by other means (for example Fedora Media Writer).
if [ "$verify_only" = "1" ]; then
  [ "$(id -u)" = "0" ] || die "reading a raw device needs root: rerun with sudo --verify-only"
  echo "reading the first $iso_size bytes back off $device..."
  readback=$(dd if="$device" bs=8M iflag=direct count=$(( iso_size / 8388608 + 1 )) 2>/dev/null \
             | head -c "$iso_size" | sha256sum | cut -d' ' -f1)
  if [ "$readback" = "$actual" ]; then
    echo "read-back SHA-256 MATCH: $readback"
    echo "the device carries exactly this ISO."
    exit 0
  fi
  echo "read-back SHA-256 MISMATCH: got $readback" >&2
  echo "expected                    $actual" >&2
  exit 1
fi

[ "$(id -u)" = "0" ] || die "writing needs root: rerun with sudo"
if [ -n "$mounted" ]; then
  die "$device still has mounted partitions:
$mounted
Unmount them first, for example: udisksctl unmount -b ${device}1"
fi

echo "writing..."
dd if="$iso" of="$device" bs=8M conv=fsync oflag=direct status=progress || die "dd failed"
sync

echo
echo "verifying the first $iso_size bytes on the device..."
readback=$(dd if="$device" bs=8M iflag=direct count=$(( iso_size / 8388608 + 1 )) 2>/dev/null \
           | head -c "$iso_size" | sha256sum | cut -d' ' -f1)
if [ "$readback" = "$actual" ]; then
  echo "read-back SHA-256 MATCH: $readback"
  echo "write verified. The media keeps the volume label baked into the ISO."
  echo "image label: ${actual_label:-unknown}"
else
  echo "read-back SHA-256 MISMATCH: got $readback" >&2
  echo "expected                    $actual" >&2
  echo "the write is NOT verified; do not boot this media as a Kavi'ka image." >&2
  exit 1
fi

# A matching SHA-256 only proves the copy is faithful; it cannot tell a good image from a bad
# one. Re-read the ESP off the DEVICE and compare it with the image's: the UEFI boot path is
# the one thing a byte count cannot confirm, and D36 showed a mismatched ESP boots to failure.
# This is deliberately a comparison rather than "does it say Kavi'ka": the same writer flashes
# stock Fedora ISOs too, which have no Kavi'ka menu and must not be rejected for it.
if [ -n "$esp_offset" ] && command -v mtype >/dev/null 2>&1; then
  dev_config=$(mtype -i "${device}@@${esp_offset}" ::/EFI/BOOT/grub.cfg 2>/dev/null || true)
  if [ -z "$dev_config" ]; then
    echo "note: could not read the ${device} ESP config; skipping the ESP check" >&2
  elif [ -n "$esp_config" ] && [ "$dev_config" != "$esp_config" ]; then
    echo "WARNING: the ${device} EFI System Partition config differs from the image's." >&2
    echo "         The UEFI boot path does not match what was written (bugtracker D36);" >&2
    echo "         do not rely on this media booting." >&2
    exit 1
  else
    echo "ESP check on the device: the UEFI boot config matches the image."
    if printf '%s' "$dev_config" | grep -qF "Install Kavi'ka OS (automated)"; then
      echo "           (this media boots the Kavi'ka installer menu)"
    fi
  fi
fi
