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
# Refused unless ALL of these hold:
#   * the target is a whole disk, not a partition
#   * the target is removable (RM=1) and on the USB transport
#   * the target is not the internal NVMe/NVMe-style system disk
#   * nothing on the target is mounted
#   * the target is at least as large as the image
#   * the ISO's SHA-256 matches the sidecar or --sha256 value
#   * --device and --confirm-wipe name the same device
#
# After writing it reads the image size back off the device and compares the
# SHA-256, so a short or corrupted write is reported rather than assumed.

set -u

die() { printf 'refusing: %s\n' "$1" >&2; exit 1; }

iso="" sha_file="" expected="" device="" confirm="" dry_run=0 verify_only=0
while [ $# -gt 0 ]; do
  case "$1" in
    --iso) iso=$2; shift 2 ;;
    --sha256-file) sha_file=$2; shift 2 ;;
    --sha256) expected=$2; shift 2 ;;
    --device) device=$2; shift 2 ;;
    --confirm-wipe) confirm=$2; shift 2 ;;
    --dry-run) dry_run=1; shift ;;
    --verify-only) verify_only=1; shift ;;
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

# Removable USB only.
rm_flag=$(lsblk -ndo RM "$device" 2>/dev/null | tr -d ' ')
[ "$rm_flag" = "1" ] || die "$device is not removable (RM=$rm_flag); refusing to treat it as a USB stick"
tran=$(lsblk -ndo TRAN "$device" 2>/dev/null | tr -d ' ')
[ "$tran" = "usb" ] || die "$device transport is '$tran', not 'usb'"

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
echo
echo "device : $device"
lsblk -o NAME,SIZE,TYPE,RM,TRAN,LABEL,FSTYPE,MODEL "$device"
echo "image  : $iso"
echo "         $iso_size bytes, slack ${slack} MiB"
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
  echo "write verified. The volume label is the preserved upstream one (Fedora-KDE-Live-44), not 'Kavika'."
else
  echo "read-back SHA-256 MISMATCH: got $readback" >&2
  echo "expected                    $actual" >&2
  echo "the write is NOT verified; do not boot this media as a Kavi'ka image." >&2
  exit 1
fi
