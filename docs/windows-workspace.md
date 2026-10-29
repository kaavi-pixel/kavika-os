# The Windows workspace, and how the swipe reaches it

How Kavi'ka presents Windows as a workspace you can swipe to, and what is actually verified
versus still assumed. Read this before believing any part of it works.

## The shape of it

Kavi'ka has two virtual desktops, side by side in one row:

| Desktop | Contents |
|---|---|
| 1, `Linux` | the native Linux desktop |
| 2, `Windows (not installed)` | the full-screen Windows guest |

The Windows workspace is the guest running full-screen on desktop 2. Nothing about it is
synthetic: it is a real Windows 11 machine displayed as a desktop, which is what makes
switching feel like changing workspace rather than opening a window.

`image/live-preview/root/etc/skel/.config/kwinrc` defines that layout, with `Number=2` and
`Rows=1`. **`Rows=1` matters**: a single row is what a horizontal swipe navigates.

## How you get there

**The swipe is Plasma's, not ours.** This is the important finding, and it changed the
design:

- **KWin's scripting API has no way to register a touchpad swipe.** It exposes
  `registerShortcut` and `registerScreenEdge`; there is no `registerTouchpadSwipe`. So the
  existing `kavika-preview` KWin script cannot grow a four-finger handler.
- **Plasma's built-in touchpad gestures are not user-configurable.** The stock set is fixed.
- **Plasma already switches virtual desktops on a three-finger horizontal swipe.**

Put together: with the guest on desktop 2 and a single-row layout, the stock three-finger
horizontal swipe already lands on Windows. No gesture code is needed, and none is written.

**Meta+F12 is the keyboard fallback**, registered by `kavika-preview`. It is the
hardware-verified path (it worked on the Laptop Studio and on the HP Envy) and it is what to
reach for if a gesture misbehaves.

## The pieces

| Component | Role |
|---|---|
| `usr/local/bin/kavika-windows-workspace` | switches to the Windows desktop and starts the guest full-screen if it is not already running |
| `usr/local/bin/kavika-windows-provision` | builds the media from your Windows ISO and runs the unattended install (one command) |
| `usr/local/bin/kavika-windows-optin` (+ `/etc/skel/.config/autostart/kavika-windows-optin.desktop`) | offers the workspace once on first login (T20); silent where qemu is absent |
| `usr/local/lib/kavika/kavika-windows-media.py` | builds the boot ESP and the answer stick from the ISO |
| `/usr/share/kavika/autounattend.xml` | the unattended answer file |
| `usr/local/lib/kavika/launch-windows-vm-linux.py --reuse` | starts an **already-provisioned** guest: no disk creation, no wipe, no install media attached |
| `usr/local/lib/kavika/launch-windows-vm-linux.py --full-screen` | `-display gtk,full-screen=on` |
| `kavika-preview` KWin script | Meta+F12 toggle |
| `kwinrc` | the two-desktop, single-row layout |

`kavika-windows-provision` builds the boot ESP and answer stick with the media builder, then
calls the launcher with `--esp-image`, `--answer-image` and `--allow-reboot`. The builder is
the reason the ESP is never reused: it rebuilds from the ISO every run (D23).

`--full-screen` composes the display option exactly as this QEMU documents it:
`-display gtk[,full-screen=on|off][,gl=on|off][,grab-on-hover=on|off]`, taken from the
binary's own help text rather than from memory.

`--reuse` deliberately does **not** attach the install ISO and does **not** force the boot
order at the CD; a provisioned guest boots its own disk. It attaches the boot ESP **only if
one exists**: since the D21 fix a provisioned guest owns its boot files on its own disk, so
no external media is needed to start it.

## Verified, and not

**Verified here:**

- `--reuse` **really starts** a provisioned guest, not only in dry-run: a real boot with
  nothing but the guest's own disk attached reached the Windows desktop. (D30: `mkdir` used
  to fail on the existing directory, so this had never worked - see [bugtracker](../bugtracker.md).)
- The launcher's `--reuse` and `--full-screen` behave correctly, checked by dry-run against a
  real provisioned guest: no `-cdrom`, no `-boot`, boot ESP attached, `-display
  gtk,full-screen=on` emitted.
- `--reuse` refuses a directory that is not a provisioned guest, with a clear message.
- `kavika-windows-workspace` passes `bash -n`, prints usage, exits 2 on an unknown argument,
  and exits 3 with actionable guidance when no guest is provisioned.
- 50 unit tests pass, including that a **self-contained guest starts without a boot ESP** and
  that an ESP is attached only when one is present.

**Not verified. Do not claim otherwise:**

- **The desktop switch still needs on-hardware confirmation.** This host runs GNOME on Wayland, so
  there is no KWin or touchpad gesture stack to test against. The primary call is
  `qdbus6 org.kde.KWin /KWin org.kde.KWin.setCurrentDesktop <n>`. After D49 there is also a
  systemd-native fallback, `busctl --user call org.kde.KWin /KWin org.kde.KWin setCurrentDesktop i <n>`,
  because qdbus is not guaranteed to be installed.
- **No swipe has ever been performed.** Touchpad gestures cannot be exercised in a VM (no
  touchpad) and this host is GNOME. The three-finger behaviour is Plasma's documented default,
  not something measured here.
- **The full-screen guest has never been displayed.** The guest reached a desktop in a headless
  run; nobody has looked at it full-screen on desktop 2.

## Testing it for real

Needs a KDE host with a touchpad: either the Laptop Studio booted into the Kavi'ka image, or
any Fedora KDE install.

1. Confirm the desktops exist and are one row:
   `qdbus6 org.kde.KWin /KWin org.kde.KWin.VirtualDesktopManager.desktops`
2. Confirm the switch works at all: `qdbus6 org.kde.KWin /KWin org.kde.KWin.setCurrentDesktop 2`
3. Provision a Windows guest: `kavika-windows-provision --iso /path/to/Windows11.iso`.
4. Run `kavika-windows-workspace`. The guest should appear full-screen on desktop 2.
5. Now the actual question: **swipe three fingers left and right** and see whether the desktop
   changes. If it does not, check whether the desktop layout is still a single row.
6. Repeat with Meta+F12, which should always work.
7. Record what happened, including failures. A gesture that misbehaves is a result.

## The open limitation — resolved 21 October 2026

The guest used to depend on an attached boot ESP, because Windows Setup serviced the boot
files to the volume it booted from rather than to the target disk's own ESP. **That is
closed (D21).** The answer file now assigns the target ESP drive letter `S:` and runs a
plain `bcdboot C:\Windows /s S: /f UEFI` in the `specialize` pass, so the NVMe's own ESP is
populated and the guest boots with only its own disk attached (verified in
`Kavika-Win11-Install11`; see [windows-install-recipe.md](windows-install-recipe.md) and
[bugtracker.md](../bugtracker.md) D21). `kavika-windows-workspace` therefore treats the boot
ESP as **optional** and starts a provisioned guest without one.

## Status

No Windows is shipped in this image and none can be: provisioning is a separate, opt-in,
licensed step. What the image now ships is the tooling to do it on an installed system -
`kavika-windows-provision` builds the media and runs the unattended install, and the
first-login opt-in offers it once. Until a guest is provisioned the Windows workspace is an
empty desktop and `kavika-windows-workspace` says so rather than starting something
unexpected.

The guest installed from builder-made media reached the desktop, booted with nothing but its
own disk attached and ran Firefox ([provisioning record](validation/windows-provisioning-2026-10-23.md)).
What still needs a KDE host with a touchpad, rather than a headless VM: the opt-in dialog
being drawn, and the desktop switch and the swipe themselves.

### Why there is no single image with Windows already in it

Asked directly on 23 October 2026. Three independent reasons, any one of which is fatal:

- **Licensing and policy.** Kavi'ka ships no Windows, no licence and no guest disk; Windows is
  provisioned from the user's own ISO on an installed system. That is a product decision, not
  a missing feature.
- **The live preview has no virtualization stack.** `qemu-kvm`, `swtpm`, `edk2-ovmf` and
  `mtools` are in the *installed* package set, not on the live media, so a guest can neither be
  provisioned nor run from a live session.
- **Size.** The installer's layout includes a dedicated `/var/lib/kavika/windows` volume of
  128 GiB and a default guest disk of 64 GiB, and the installer refuses any target under
  **240 GiB**. A 3.8 GB flash stick is short by about a factor of 60, and can only ever be the
  boot medium.

The installed media do now ship the tooling, so the shortest real route is: **install** to a
disk of at least 240 GiB, boot it, then `kavika-windows-provision --iso /path/to/Windows11.iso`,
then `kavika-windows-workspace`.

**D49 path correction (29 October 2026):** new provisions place the VM in
`<volume>/guest` and the boot media in `<volume>/media`; the launcher requires a new or empty VM
directory, so media and guest state cannot share one directory. The workspace resolves the same
paths, with legacy direct-under-volume guests still supported. Compact installations use a smaller
guest allocation such as `--disk-gib 32` rather than the default 64 GiB.
