#!/usr/bin/env bash
# Kavi'ka: read-only preflight for a Fedora Surface test machine (for example the
# Surface Laptop Studio). It installs nothing, changes no settings and writes no
# files. It prints a privacy-filtered report you can review before sharing.
#
#   bash tools/surface-fedora-preflight.sh
#
# Output never includes serial numbers, UUIDs, MAC/IP addresses or user files.
set -u
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
report="$here/../image/live-preview/root/usr/local/bin/kavika-hardware"

echo "== Kavi'ka Fedora test-machine preflight =="
echo "date_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
. /etc/os-release 2>/dev/null && echo "os: ${PRETTY_NAME:-unknown}"
echo "kernel: $(uname -r)"
echo "session: ${XDG_SESSION_TYPE:-unknown}"

echo
echo "== Virtualisation readiness =="
if grep -qE '^flags.*\b(vmx|svm)\b' /proc/cpuinfo; then echo "cpu_virtualisation_flag: yes"; else echo "cpu_virtualisation_flag: NO (firmware may have it disabled)"; fi
if [ -e /dev/kvm ]; then
  if [ -r /dev/kvm ] && [ -w /dev/kvm ]; then echo "kvm_device: present, usable by this user"
  else echo "kvm_device: present but NOT usable by this user (add yourself to the 'kvm' group, then log in again)"; fi
else echo "kvm_device: MISSING"; fi
lsmod 2>/dev/null | grep -E '^kvm(_intel|_amd)? ' | awk '{print "kernel_module: "$1}'
for tool in qemu-system-x86_64 qemu-img virsh virt-manager swtpm; do
  if command -v "$tool" >/dev/null 2>&1; then echo "tool_$tool: installed"; else echo "tool_$tool: missing"; fi
done
for fw in /usr/share/edk2/ovmf/OVMF_CODE.fd /usr/share/edk2/ovmf/OVMF_VARS.fd; do
  if [ -f "$fw" ]; then echo "firmware_$(basename "$fw"): present"; else echo "firmware_$(basename "$fw"): missing (sudo dnf install edk2-ovmf)"; fi
done
if systemctl is-active --quiet libvirtd 2>/dev/null || systemctl is-active --quiet virtqemud 2>/dev/null; then echo "libvirt: running"; else echo "libvirt: not running"; fi

echo
echo "== Resources =="
awk '/MemTotal|MemAvailable/ {printf "%s %.1f GiB\n", $1, $2/1048576}' /proc/meminfo
df -h --output=target,size,avail -x tmpfs -x devtmpfs / /home 2>/dev/null | sed 's/^/disk: /'

echo
echo "== Secure Boot / TPM =="
if command -v mokutil >/dev/null 2>&1; then mokutil --sb-state 2>/dev/null | sed 's/^/secure_boot: /'; else echo "secure_boot: mokutil missing (the hardware report below reads it directly)"; fi
[ -e /sys/class/tpm/tpm0 ] && echo "tpm: present" || echo "tpm: not found"

echo
echo "== Kavi'ka hardware report (JSON) =="
if [ -f "$report" ]; then python3 "$report"; else echo "report script not found at $report"; fi

echo
echo "== Notes =="
echo "- This is inventory, not a Windows or Kavi'ka acceptance pass."
echo "- The Laptop Studio is a test machine; results are evidence only for the Surface Pro 8, not proof."
echo "- Nothing here changed the machine. Review the output before sharing it."
