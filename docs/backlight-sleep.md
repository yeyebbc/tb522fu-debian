# GNOME Suspend with backlight-only sleep

The optional GNOME48 extension is installed and verified on Debian13.7 with
CI96, native GSD48.7, Mesa26.1.6 and the finalized display-power overlay.
Choosing Suspend invokes GNOME's ordinary password-lock action. The existing
adapter blanks only the LEDs while the system/display link stay awake. Space
returns to the password screen. This uses more battery than real suspend.

Kernel sleep targets remain masked. The extension checks this protection,
respects lock policy and greeter/locked sessions, and never falls back to real
kernel sleep. It verifies the running GSD adapter/compat mode before each action.
Startup checks only static protection because GSD may start after Shell; no
fixed startup delay or daemon restart is introduced. Disabling the extension
restores the original GNOME action/capability. Other extensions/settings remain.

## Verified results — 2026-11-17

The installed source is device/gnome-backlight-sleep. Its extension.js SHA256 is
`2570027d70ad2a4cd48d4eddb6ac316d1948fb94355cdf005f9170bd4247127c`.
Nine behavior checks cover lock redirection, disabled capability, board/mask
refusal, runtime adapter/mode checks, startup ordering, locked/greeter policy,
mid-call lock-policy changes, duplicate activation and complete method cleanup.

After a fresh GNOME login, the extension reported ACTIVE. A real connected
Suspend menu action blanked the screen for14.86seconds. Space restored a clear
password screen on camera; the stored brightness stayed1135, MDSS/KMS remained
active, suspend success stayed0 and Adreno pixels passed.

The battery test then passed on the same CI96 boot. Unplug was observed before
the actual GNOME Suspend action. The accessory Space press arrived24.86seconds
after blanking, with USB power0. The password screen returned on battery and
camera confirmed it before reconnection. USB returned8.40seconds after wake,
passing the8second minimum observation guard. The user confirmed Working.
MDSS stayed active, suspend count stayed0 and password lock/GPU checks passed.
This accepts one connected and one short battery backlight-only cycle, without
claiming actual suspend, long-duration standby, measured drain or repeated wake.

## Package and rollback

The architecture-independent extension package has its own workflow,
Build GNOME backlight-only Suspend. It runs the nine checks and publishes the
ZIP, committed source/file manifest and SHA256SUMS. It neither builds a kernel
nor flashes a device. Firmware, private evidence and identifiers stay local.

Install metadata.json/extension.js under the per-user UUID directory
backlight-sleep@tb522fu.local and append that UUID to enabled-extensions without
replacing existing entries. GNOME needs a new login to discover a new extension.
To undo, disable that UUID and remove only its exact owned files/setting entry.
The underlying display workaround and real-sleep masks are independent.

The user subsequently requested a separate actual disk-hibernation experiment.
That requires swap and a verified early-boot resume path; it has not replaced
this working backlight-only action yet. Preserve this configuration as rollback.
