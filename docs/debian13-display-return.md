# Debian 13 return completed

Debian 13.7 is now running `7.3.0-tb522fu-installed-ci96` on the original 256 GiB
filesystem, with matching modules and the finalized backlight compatibility
fix. The user's later explicit installation request superseded the earlier
prepare-only/defaultCI78 plan. CI78/CI74/CI44 rollback images, Android and the
Ubuntu/Fedora comparison roots remain. The existing account, locale, firmware,
brightness policy and native Debian graphics libraries were preserved.

## Installed versions

[CI96](https://github.com/yeyebbc/tb522fu-debian/actions/runs/44095613555)
passed both Debian-root kernel profiles and the ARM64 backlight overlay build.
The build recipe is `c6941972289c88e6122ad2dca1062c40adcc97b3`; its 117-patch
kernel tree is `a6fa3410d3f9e3b61d5788505b9215ccff2bc570`.

- Selected installed boot image SHA256:
  `5587888d02086c27c98bac0ed9f06e79efbc402c681ffe18f02266f31e876c02`.
- Matching installed modules archive SHA256:
  `ebd746209985b764aa0d5278faee8f509b545f091683657a8f692fdd518a5566`.
- Backlight overlay archive SHA256:
  `8dbdc78aec00a26b3c196babf5a2bc27a0bb927dfa0d08b41db5485f5d41ef04`.

The eight overlay files and socket-enable symlink were installed with exact
new-file/hash guards; native Debian GSD 48 libraries were retained. Versioned
CI96 modules and the installed image were staged with clean unmount/fullfsck.
CI78 remains available for rollback. Prepared removal now guards CI96; the
historical CI78-only removal/first-boot payloads must not be replayed unchanged.

## Startup and physical verification

The normal on-device switching action booted the selected CI96 installed image.
All 39 supported baseline modules loaded and no failed system units were listed.
Wi-Fi connected with its US radio domain, Bluetooth reported Powered=true and
the TB522FU ALSA card was present. These checks do not establish new pairing,
camera image quality or full physical acceptance of every peripheral.

Debian's existing Mesa 26.1.6 rendered real Adreno 830 pixels; the llvmpipe
negative control was rejected. The signed-in GNOME process used that hardware
stack. Native GSD 48 mapped the adapter, MDSS stayed active and KMS kept scanning.
An automatic connected backlight off/on cycle preserved stored brightness.
Camera review confirmed clear desktop, physical darkness, then clear desktop;
no matched display faults appeared before or after the cycle.

An optional BlueZ startup status query initially timed out. Its failed result
was retained; an owned same-boot diagnostic resume passed all required checks
and the settled Bluetooth query. No second boot or display-gate weakening was
used. The independent 600-second first-boot return was retired only after native and
physical checks. Debian was left running; host network, ModemManager, camera
settings and owned workers were cleaned up.

## Acceptance limits

This is an experimental installed CI96 plus compat configuration. Connected
physical blank/unblank passes on Debian. The positive short Fedora battery
Lock/Space result remains separate; unplugged Debian Lock/Space, longer blanking,
repeated wake, fresh unlocking and blank-state drain have not been accepted.

The workaround keeps the display link active and costs power. Actual system
sleep targets remain masked. CI96 contains the new post-link PHY/controller
sequence, but its normal display-power wake path has not been tested separately
from compat. Disable/remove the adapter, service and runtime-active rule before
that independent experiment. A compat pass cannot establish kernel-wake or
system-suspend acceptance. Existing camera and other peripheral limits remain.
