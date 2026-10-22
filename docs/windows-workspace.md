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
| `tools/launch-windows-vm-linux.py --reuse` | starts an **already-provisioned** guest: no disk creation, no wipe, no install media attached |
| `tools/launch-windows-vm-linux.py --full-screen` | `-display gtk,full-screen=on` |
| `kavika-preview` KWin script | Meta+F12 toggle |
| `kwinrc` | the two-desktop, single-row layout |

`--full-screen` composes the display option exactly as this QEMU documents it:
`-display gtk[,full-screen=on|off][,gl=on|off][,grab-on-hover=on|off]`, taken from the
binary's own help text rather than from memory.

`--reuse` deliberately does **not** attach the install ISO and does **not** force the boot
order at the CD; a provisioned guest boots its own disk. It attaches the boot ESP **only if
one exists**: since the D21 fix a provisioned guest owns its boot files on its own disk, so
no external media is needed to start it.

## Verified, and not

**Verified here:**

- The launcher's `--reuse` and `--full-screen` behave correctly, checked by dry-run against a
  real provisioned guest: no `-cdrom`, no `-boot`, boot ESP attached, `-display
  gtk,full-screen=on` emitted.
- `--reuse` refuses a directory that is not a provisioned guest, with a clear message.
- `kavika-windows-workspace` passes `bash -n`, prints usage, exits 2 on an unknown argument,
  and exits 3 with actionable guidance when no guest is provisioned.
- 50 unit tests pass, including that a **self-contained guest starts without a boot ESP** and
  that an ESP is attached only when one is present.

**Not verified. Do not claim otherwise:**

- **The desktop switch has never been executed on KDE.** This host runs GNOME on Wayland, so
  there is no KWin, no `qdbus6`, and no touchpad gesture stack to test against. The call used,
  `qdbus6 org.kde.KWin /KWin org.kde.KWin.setCurrentDesktop <n>`, is the documented one and is
  reported working on current Plasma 6, but it must be confirmed on an actual KDE host.
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
3. Provision a Windows guest (see [windows-install-recipe.md](windows-install-recipe.md)).
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

No Windows is shipped in this image and none can be: Windows provisioning is a separate,
opt-in, licensed step. Until a guest is provisioned, the Windows workspace is an empty
desktop and `kavika-windows-workspace` says so rather than starting something unexpected.
