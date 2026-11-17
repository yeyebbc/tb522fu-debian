# Lenovo backlight-only display blanking

GPL-2.0-only adaptation of the pinned OnePlus display-power service, mode tool,
GSD generated-setter adapter and units. Provenance is in source.json. This
temporary workaround leaves DSI scanning and keeps MDSS runtime-active while
blanking both KTZ8869 LED strings through the existing primary backlight.
It consumes more standby power and does not implement system suspend.

The adapter is loaded only by gsd-power. Its pointer/int generated-setter ABI
and ELF symbol binding must be checked on the selected distribution. Fedora51
exports/imports this setter. The daemon refuses foreign boards, unidentified or
ambiguous backlight layouts and callers outside the active seat. It writes
bl_power0/4 while preserving brightness. GNOME retains authentication.

Build with scripts/build-display-power.py using an ARM64 compiler. The overlay
defaults to compat mode; install it only through the bounded trial transaction.
Use tb522fu-display-power-mode status to inspect the configured AND running
path. Standard mode masks the adapter/rule/service; compat restores them.
Changing drop-ins requires a fresh login or the explicit --restart-gsd-power
option. A mixed status is not a successfully selected path.

No Power-key or lid policy is changed by this package. Keep the existing
system-sleep masks. Use tb522fu-display-powerctl only for explicit backlight
requests; it does not lock or unlock a session. Test ordinary GNOME Lock and
Space separately with physical camera evidence before promotion. Remove the
workaround after normal display power restoration and its power use pass.
