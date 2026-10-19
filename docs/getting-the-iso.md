# Getting the Kavi'ka diagnostic ISO (Windows build helper)

> Updated 19 October 2026. A Fedora-running Linux machine, such as the Surface Laptop Studio, can build the ISO directly with the same `tools/build-live-preview.py` (it needs `xorriso`, `cpio`, `grub2-tools` for `grub2-script-check`, `isomd5sum`, `python3-pycdlib`), so WSL is only needed on Windows. Use the official mirror path `.../releases/44/KDE/x86_64/iso/` for the base ISO, and always compare its SHA-256 with the pinned value in `docs/build.md`.

The ISO does not exist in the repository yet. This process builds a **private diagnostic live image** from the Fedora KDE 44 base plus Kavi'ka's overlay. It is not an installer release and does not include Windows, Comet, a Surface kernel, or persistent storage. Do not use it to install or replace Windows.

The supported source build needs Linux tools, so the documented path for this helper PC uses Ubuntu under Windows Subsystem for Linux (WSL).

## 1. Finish enabling WSL

Windows optional features were requested for WSL2 and Virtual Machine Platform. DISM returned `3010`, which means the feature servicing needs a Windows restart. Save work and restart Windows before continuing. After restart, open PowerShell and run:

```powershell
wsl.exe --status
```

If it still says WSL is not installed, open **PowerShell as Administrator**, then run:

```powershell
wsl.exe --install --no-distribution
```

Restart if Windows asks. Open **PowerShell as Administrator** again and install Ubuntu:

```powershell
wsl.exe --install -d Ubuntu-24.04
```

If that Ubuntu distribution name is not listed, check `wsl.exe --list --online` and choose the listed Ubuntu 24.04 distribution. Open **Ubuntu 24.04** from Start and create its initial Linux username/password when prompted. That Linux password is only for Ubuntu's `sudo`; do not send it to me.

## 2. Install the builder tools in Ubuntu

In the Ubuntu terminal:

```bash
sudo apt update
sudo apt install -y python3 python3-venv git xorriso cpio grub-common isomd5sum bash
python3 -m venv ~/.venvs/kavika-builder
source ~/.venvs/kavika-builder/bin/activate
python -m pip install pycdlib==1.22.0
```

Check tools are present:

```bash
source ~/.venvs/kavika-builder/bin/activate
python --version
python -c 'import pycdlib; print("pycdlib import OK")'
xorriso -version
cpio --version | head -n 1
grub-script-check --version
implantisomd5 --help
```

## 3. Prepare the working checkout and Fedora input

`cp -a` copies the repository state as it exists when run. If you build again later, refresh only the project checkout from the Windows worktree before rebuilding; do not overwrite the Fedora ISO or your generated build output.

```bash
cp -a /mnt/c/tmp/kavika-os-current "$HOME/kavika-os-build"
cd "$HOME/kavika-os-build"
mkdir -p input build
```

The pinned Fedora base ISO is stored on Windows. Set the WSL path and verify its full SHA-256:

```bash
FEDORA_ISO=/mnt/c/Users/kavsb/AppData/Local/hermes/cache/scratch/kavika/Fedora-KDE-Desktop-Live-44-1.7.x86_64.iso
sha256sum "$FEDORA_ISO"
```

It must match the full value in `docs/build.md`. Stop if it differs. If the file is missing, download Fedora KDE 44 x86_64 from [Fedora's official download page](https://fedoraproject.org/kde/download), verify it using Fedora's instructions, and point `FEDORA_ISO` to the verified file.

## 4. Run checks and build

```bash
source ~/.venvs/kavika-builder/bin/activate
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
bash -n image/live-preview/root/usr/local/bin/kavika-live-session
bash -n image/live-preview/root/usr/local/bin/kavika-test-centre
bash -n image/live-preview/root/usr/bin/liveinst
python tools/build-live-preview.py \
  --base "$FEDORA_ISO" \
  --output "$PWD/build/Kavika-OS-0.1.0-Surface-Pro-8-Live-Preview.iso"
```

Keep at least 10 GiB free. The build produces an ISO, `.iso.sha256` sidecar and `.manifest.json` under `build/`. It writes no USB or laptop disks. After success, copy the ISO to Windows Downloads:

```bash
cp build/Kavika-OS-0.1.0-Surface-Pro-8-Live-Preview.iso /mnt/c/Users/kavsb/Downloads/
```

## 5. Before sharing or booting it

First check the output SHA-256 against the sidecar. A successfully built ISO is **not yet verified bootable**. The newest build must boot in a fresh, disposable UEFI VM with **no physical disks attached**. Follow `docs/windows-vm-preview.md` for the Windows helper instructions if the local VM memory gate permits. Record the exact image hash and boot outcome. Do not flash it to the Surface or replace Windows based on build success alone.

If anything fails, send me the exact error text and the ISO hash if one was produced. Do not send passwords, recovery keys, serial numbers, or private raw logs.
