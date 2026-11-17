# Two independently tested display-power paths

The [audit checkpoint](checkpoints/2026-11-17-oneplus-display-audit.md) preserves
the failed CI91 battery-wake baseline. Subsequent implementation covers both
the donor's kernel wake sequence and selectable backlight-only blanking.
Neither is hardware accepted yet; installed Debian CI78 remains selected.

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

## Acceptance

Test normal and compat paths separately against explicit source/image and
userspace manifests. A compat pass cannot mark normal kernel wake as passed.
Each cold boot needs matching modules, the supported-driver baseline, settled
fault checks, connected physical off/on, then a local-logged unplugged
Lock/Space cycle with camera evidence before reconnection. Preserve independent
return and exact Android/default/graphics/filesystem restoration.
