# Two separate display-power paths

The [audit checkpoint](checkpoints/2026-11-17-oneplus-display-audit.md) preserves
the failed CI91 battery-wake baseline. Subsequent implementation covers both
the donor's kernel wake sequence and selectable backlight-only blanking.
The backlight workaround restored a physically visible lock screen on battery.
CI96 now boots installed Debian13 with the compatibility path and passes a
connected physical backlight cycle. The kernel sequence's independent normal
display-power wake test is deferred; CI78 remains a rollback option.

## Kernel sequence candidate

Two pinned donor changes add a post-link-clock retime FIFO edge on each PHY,
followed by a controller-only reset before panel commands. C-PHY retains its
CLK_EN_SEL state. The patches preserve the existing clock parking, PLL startup,
panel configuration, shared-controller policy and supported drivers.

The actual Lenovo vendor source at
`e1f324632d70b2427751820cd48eefc45baab0ce` independently confirms the order:

- `dsi_display.c:2922`: toggle every retime FIFO, then skip CLK_EN_SEL clearing
  for C-PHY; the post-HS-clock callback invokes that function.
- `dsi_display.c:8758`: link clocks on, optional esync clocks, controller reset
  at8783, then panel preparation at8791.
- `dsi_phy_hw_v7_2.c:533`: FIFO0, write barrier, FIFO1, write barrier.
- `dsi_ctrl_hw_cmn.c:304`: disable engines, temporarily force the existing
  clock mask, pulse reset for1us, restore clock control and controller state.

This matches the imported operations without copying OnePlus panel values.
Patch0235 adapts only context around an existing logging callback and older PHY
fields. Patch0236 preserves the existing clock-parking helper. Added/removed
lines match the donor changes exactly; original author, dates and coauthors
are retained. Both original and imported patch IDs are recorded because
context changes affect patch identity.

Source after the pair: `63ffe260b42f2c80866fc5db47f05613af186e0b`;
116-patch tree: `d63040f08622885c246dd033a0542e9cd1c12917`.
All116 patches replay exactly to that tree;11 root-selection/geometry/module
guard cases pass. Strict checkpatch reports the donor's missing signoffs,
commit-message/trailer style, uncommented barriers and one alignment check.
These findings are retained; no original-author signoff is invented. Full
ARM64 CI and physical wake remain required. No kernel-version change.

The first CI92 build exposed an older-header API difference: this manager
includes dsi.h, whereas the donor placed new declarations in the private PHY
header. Patch0237 moves those declarations into the existing manager-facing
API without changing hardware operations. The failed CI92 build is retained;
the corrected117-patch tree is pinned by kernel/source.json. CI93 at recipe
`1ee503c68daf00310df99e5dd656fd38db88944a` passed installed and Fedora disk-test
builds. Its tree is `a6fa3410d3f9e3b61d5788505b9215ccff2bc570`.
The audited bounded boot image has SHA256
`5ab604ee02ce4f93137f0a61b1a8239bda5168c9f5923f40c4c8ed678facbcfc`.
It has not been booted. No normal kernel-wake acceptance is inferred.

## Backlight compatibility path

Adapt the pinned donor service and generated GSD power-setter adapter. Lenovo's
primary KTZ8869 backlight already controls both chips. Use its standard
`bl_power` to blank without changing saved brightness or tearing down DSI.
Verify the actual active daemon imports the setter and maps the adapter;
do not infer this from an environment variable alone.

Retain GNOME screen locking and authentication, brightness/ambient-light policy
and the user's locale. Scope any MDSS runtime-active policy to compat mode.
Standard mode must use the ordinary connector-off path with no compat adapter.
Keep actual system sleep masked in both display-only tests.

The compatibility path consumes more power while blanked. It is a temporary
workaround with an explicit rollback, not proper suspend or kernel-wake
acceptance. Remove it after normal unplugged display-power restoration passes
repeated physical fresh-frame tests and its power behavior is measured.

The board-scoped overlay is implemented in device/display-power. Its29
donor-derived checks pass, covering seat authorization, ambiguous backlights,
foreign boards/files, manual blanking ownership and mode switching. The ARM64
adapter loads against the extracted Fedora45 libc and overrides a dynamically
imported setter; its no-adapter negative control exits99. A separate ARM64
socket transport check delivers AUTO3/AUTO0. These are software/interface
checks, not physical acceptance. The actual Fedora51 gsd-power has an undefined
dynamic import of the setter and libgsd exports it. No distro library is copied.

## First physical backlight result — 2026-11-17

The unchanged CI91 control kernel ran Fedora45 with only the owned eight-file
overlay and socket-enable symlink added. All39 supported modules, Adreno pixels,
software-renderer rejection and the settled fault gate passed. The active user
GSD mapped the adapter; MDSS stayed runtime-active. Connected blank/unblank
physically passed with KMS active, Mutter PowerSaveMode0, stored brightness1256
unchanged and no new panel/DSI lifecycle entries.

During GNOME Lock on battery, the backlight service reported off. Space arrived
at200.39s uptime while both USB supply indicators were0. The lock screen became
clearly visible on camera before reconnect, and the user confirmed “It works!”
The authoritative USB supply stayed0 through204.28s, then returned at205.83s.
No matched display faults appeared.

The automated probe returned1 because reconnect atSpace+5.44s did not satisfy
its eight-second offline observation guard. The complete ten-second observation
and subsequent unlock/fresh desktop phase were therefore not reached. Preserve
that protocol failure alongside the positive physical wake evidence. This is
one short unplugged Lock/Space result, not repeated or long-duration acceptance.

Android stock boot readback, boot completion, selectedCI78/graphics preservation,
timer retirement/fullfsck, ModemManager, temporary network profile, camera and
owned-worker cleanup were verified. The trial overlay was removed with its
exact hashes and another fullfsck. Fedora and Ubuntu roots are retained.

The user then requested finalization, CI packaging and return preparation for
Debian13. CI now publishes display-power-aarch64 independently of the kernel
artifacts. [Debian return preparation](debian13-display-return.md) keeps the
successful workaround and untested kernel candidate distinct.

## Acceptance

Test normal and compat paths separately against explicit source/image and
userspace manifests. A compat pass cannot mark normal kernel wake as passed.
Each cold boot needs matching modules, the supported-driver baseline, settled
fault checks, connected physical off/on, then a local-logged unplugged
Lock/Space cycle with camera evidence before reconnection. Preserve independent
return and exact Android/default/graphics/filesystem restoration.
