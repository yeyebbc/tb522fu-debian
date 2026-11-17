# Backlight-only GNOME Suspend

This optional GNOME48 extension redirects the normal Suspend menu/search action
through GNOME's existing password-lock action. The installed GSD compatibility
adapter then switches off only the backlight; Space follows normal lock-screen
wake and password authentication. The system and display link keep running.
This consumes more battery than real suspend. systemctl suspend stays blocked.

The extension requires this board and both existing sleep-target masks. Each
action requires the actual running GSD adapter and compat mode. It rechecks mode before every action and
never falls back to kernel sleep or a compositor power cycle. Lockdown policy
and greeter/locked sessions remain respected. Disabling the extension restores
the original GNOME action and its original unsupported-suspend availability.
No kernel, systemd sleep policy, locale or brightness value is changed.

Install metadata.json and extension.js in the user's GNOME extension directory
backlight-sleep@tb522fu.local and append its UUID to enabled-extensions, preserving
existing entries. A fresh GNOME login is required to discover the new extension.
Disable it before removal; delete only the exact installed files. Supports48
only, checked against Debian GNOME48.7's embedded SystemActions source.

Uses the GNOME InjectionManager API and SystemActions.activateLockScreen:
https://gjs.guide/extensions/topics/extension.html#injectionmanager
https://gitlab.gnome.org/GNOME/gnome-shell/-/blob/48.7/js/misc/systemActions.js
