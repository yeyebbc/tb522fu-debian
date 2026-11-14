# TB522FU Debian build repository

This repository is public. Keep firmware, identifiers, credentials, backups,
stock partition images and local environment paths out of tracked files.

- Kernel source and imported drivers must retain pinned origins and licenses.
- Build artifacts do not establish hardware support. State only observed results.
- CI must never flash a device, deploy images, use a self-hosted runner, or need
  account secrets. Use GitHub-hosted ARM64 runners and read-only permissions.
- Preserve Android and verified stock recovery. RAM tests precede storage changes.
- ci11 verified physical GNOME with normal clock-provider coldplug, MMCX at320 after RPMh sync, and correctly aligned real finger input. Preserve these fixes. Native display/GPU, suspend and pen remain unverified.
- ci12 verified six UFS LUNs, both GPTs, full partition hashes and a read after runtime suspend. Stock Android restoration passed. The requested persistent Debian allocation is256GiB. Disk-test has an independent900-second EDL return; installed has normal restart semantics and no test timer. Both embed their matching modules and e2fsck. Before root verification storage stays read-only. No automatic partition creation or formatting.
- A running GNOME process or a framebuffer capture does not prove physical output. Keep camera evidence and source/image hashes.
- Do not change the kernel version or source commit without updating its manifest.
- Validate Python/shell syntax, patch applicability, and the resulting workflow.

- Resolve every explicit modprobe/blacklist name against built modules with modinfo; Kconfig and driver names do not reliably match module filenames. ci12 artifact uses ufs_qcom; its original helper typo is corrected in RAM before the first storage test.

- Camera candidate: secondary rear OV02B10 only. CI45 full ID and two short
  RAW10 cycles pass; scene/color quality and ordinary applications do not.
  Preserve all six camera module blacklist entries until broader acceptance.
  Camera presence or enumeration is insufficient. The installed baseline isCI44.
- The new native-display wake candidate restores the prior native patches plus
  the slave timing-mux disconnect. Keep the earlier slave-first DSI shutdown.
  Native modules coldplug only in disk profiles; FastRPC and camera remain manual.
  The89-patch stack must reproduce kernel/source.json patched_tree. Preserve
  keyboard/BT/audio/camera wiring checks alongside display checks. No promotion
  until actual fresh screen frames after wake and clean fault logs pass.
- CI46 was tested and rejected: grey physical panel after wake and CTL reset,
  frame/vblank timeouts after a fresh GNOME update. The slave mux disconnect is
  insufficient. Preserve this failure and CI44 production; no unchanged repeat.
- Isolated libcamera 0.7.1 CPU processing on CI45 captured 90+8 RGB888 frames;
  images remain dark/purple. Quality, timing and ordinary camera apps are open.
  The private bundle preserves Debian 0.4/PipeWire/accepted audio libraries.
- The next candidate imports upstream 32d04280ddeb unchanged as patch0196:
  secondary DPU encoder shutdown before primary, with original attribution.
  It is distinct from DSI host clock shutdown. The90-patch tree must replay
  exactly. CI47 bounded physical wake testing now rejects this candidate too:
  initial hardware pixels pass, but grey wake and CTL reset/frame/vblank faults
  recur before post-wake input. Android/graphics restoration passed; keep CI44
  installed and do not repeat CI47 unchanged. Continue targeted lifecycle
  analysis before selecting another change.

- Patch0197 is diagnostic only, disabled by default. The91-patch stack must
  replay exactly. Enable only DPU_LIFECYCLE formats for a bounded test; collect
  the display driver's stored devcoredump without triggering a fresh snapshot.
  This does not make CI47 wake accepted and must not be promoted to production.

## Current candidate: CI49 VBIF handshake

- CI48 diagnostic capture passed, wake failed. Both teardown resets returned0;
  first pending reset was observed after resume/fresh-frame request. Do not infer
  a particular root cause from the ordering. Android/graphics/fullfsck and all
  worker cleanup passed. CI44 remains installed.
- Current93-patch recipe excludes0197 and adds0198–0200, imported unchanged from
  the pinned same-SoC port. Preserve original author/co-author/license metadata;
  do not fabricate missing nominal-author signoffs to silence checkpatch.
- Only SM8750 enables AXI halt; other VBIF fields are unchanged. No OPP, panel,
  RAM, camera or accepted audio changes. Source/ARM64/replay/12 recipe checks
  pass; original metadata findings are separate from the clean code-style check.
- First hardware test remains one bounded DPMS cycle, physical camera evidence,
  fault checks after each action and exact Android/graphics rollback. No CI48
  lifecycle-debug option for a kernel without its14 sites. No promotion until
  actual fresh screen frames and clean fault logs pass.

- CI49 now fails initial display before DPMS: patterned physical output,
  DSI FIFO-class errors and panel-init DMA timeout, then CTL reset errors.
  GPU readback passing does not validate physical display. Android/graphics/
  filesystem/timer/worker restoration passed; keep CI44. No unchanged repeat.
  Audit initialization and shared MDSS/DSI bus ownership before another patch;
  the newly added handshake also runs during pre-registration runtime PM.

## CI50 initialization diagnostic

Patch0201 adds8 info-level logging sites active from boot. It changes no hardware
writes, retries, delays or votes; all new register reads stay within existing
clock-active VBIF operations. Readbacks/logging may affect ordering/timing.
The94-patch source must replay exactly. Keep CI44 installed; CI50 is diagnostic
only even if the logging changes the observed startup. Preserve the improved
coldplug fault gate and existing-snapshot capture. No unchanged CI49 repeat.

CI50 is tested and rejected for wake: visible initial greeter, grey after one
cycle, CTL reset/frame/vblank faults. Startup ACK passes; screen-off ACK poll
times out with idle bits and fallback success. Diagnostic capture passed;
readback/logging timing prevents treating improved startup as a fix. Exact
Android/graphics/fullfsck/timer/worker restoration passed. CI44 retained.
No unchanged repeat or promotion. Audit stock QACTIVE/CESTA applicability and
shared-bus lifecycle before selecting another correction; do not guess writes.

## CI51 paired QACTIVE protocol experiment

Patch0202 adds the stock QACTIVE assertion before AXI halt, with local save/restore
after release for mainline shared-parent PM. Only SM8750 enables it; register
0xae8000c is MDP-relative0x7f00c, NOT the stock MDSS-relative0x8000c. Resource
bounds are checked.95 patches must replay exactly. Retain CI50 logs/readbacks;
this is experimental, not installable. No extra clocks, rates, OPPs, voltages,
delays or retries. Evaluate halt ACK separately from physical wake/fresh frames.
No promotion without a later clean candidate and appropriate regression checks.

CI51 completed one recorded wake cycle. All three bus halts received real
acknowledgements, and the saved QACTIVE value was restored each time. No matched
DSI/controller/frame/vblank fault recurred, and fresh GNOME GPU rendering passed.
However, the physical panel remained grey after wake throughout the fresh-frame
probes. **Wake is rejected**; software success is not physical display acceptance.
Android, exact graphics rollback and filesystem checks passed; CI44 remains
installed. Do not install or repeat CI51 unchanged. The next audit targets panel,
dual-DSI and DSC output lifecycle; the remaining failure's cause is not established.

## CI52 panel shutdown transfer mode

A changed CI51 evidence probe compared private compositor screenshots with
Pixel 6 camera footage in a signed-in session, without forcing ScreenShield
state. GNOME screenshots show the desktop after wake, but the physical panel
stays dark. This places the failure after compositor image production; it does
not distinguish scanout, DSI, panel or backlight. No matched display fault
appeared. Screenshot flash and user activity are timing/scene confounders.
All Android, graphics, filesystem, timer and worker restoration checks passed.
CI51 remains rejected; private recordings/screenshots are not published.

CI52 adds one board-specific correction: send the BOE DVT2 panel shutdown
commands in high-speed mode, matching its stock off-command-state. Restore the
original transfer flags on success or error so initialization remains low-power.
Commands, delays, supplies and other panel variants are unchanged. The 96-patch
recipe retains the prior bus diagnostics and is experimental only. Physical
wake/fresh frames and clean faults are required before any later clean candidate
can be considered for installation. CI44 remains the installed baseline.

CI52 is now tested and rejected for physical wake. The greeter is visible
before one DPMS cycle; Pixel 6 footage then shows a dark panel throughout the
post-wake focus probes. Software checks pass without matched display-controller
faults, so the stock high-speed shutdown correction alone is insufficient.
Android, exact graphics rollback, filesystem checks, timer retirement and worker
cleanup all passed. Keep CI44 installed; do not repeat CI52 unchanged.
The next audit separates backlight recovery from the panel/video path. The
current driver's `actual_brightness` is cached software state, not LED readback.

## CI53 output diagnostics

CI53 adds nine scoped dynamic-debug callsites for panel wake and backlight
output. They record existing callback results, effective brightness/blanking
state, and existing writes to both backlight chips. They are disabled by default;
no new register reads, writes, retries, delays or power policy are introduced.
Successful transport is not proof of LED light or panel output. The 97-patch
recipe remains diagnostic only. A bounded test must enable only these formats,
restore their flags, review Pixel 6 footage and preserve CI44/Android/graphics.

## CI54 panel/backlight reachability

CI53 captured all nine enabled diagnostic sites, then restored their print
flags. The panel disable/unprepare and enable/init/PPS callbacks completed, but
neither backlight chip received an update during the cycle. Physical wake still
failed; Android, graphics, filesystem and all cleanup checks passed.

The build configuration explains the missing backlight association: DRM is
built-in while BACKLIGHT_CLASS_DEVICE is modular. For that combination the
kernel header replaces drm_panel_of_backlight() with a successful no-op. The
actual CI53 panel module has no import of the real helper. CI54 changes only the
backlight class core to built-in; the chip and panel drivers remain modules.
Local compiled objects now import/export the real helper. CI checks both the
final configuration and the consumer's actual symbol reference. The 97-patch
source tree is unchanged and retains diagnostics for the bounded comparison.
This correction is not physical wake acceptance; keep CI44 installed until the
camera and callback results pass, followed by a clean candidate and regression.

CI54 stopped before compilation: its config guard caught the board fragment's
KTZ8866=y becoming effective when the class core changed to built-in. No image
or hardware test resulted. CI55 explicitly sets KTZ8866=m in the final fragment,
retaining the guard. A fresh defconfig/fragment merge passes all 95 recipe
setting assertions; the only functional change from CI53 is the class core=m→y.
Cross-toolchain labels, pahole availability and an explicitly disabled XML
validator differ locally. The source and diagnostic scope are unchanged.

CI55 hardware test: backlight association fixed, physical wake REJECTED.
Actual module linkage and off/on writes to both chips pass; the user observes
backlight on without an image, matching blank post-wake camera frames. Panel
init/PPS and software render checks pass without matched controller faults.
Android/graphics/fullfsck/timer/host-service/worker restoration passed; keepCI44.
No unchanged repeat or installation. Investigate panel/video restart; do not
guess reserved reset GPIOs or unsupported DCS reads. Diagnostic cleanup remains
conditional on later physical success and fresh broader regression acceptance.

Next candidate0205 corrects the DVT2 setup packet encoding only:23 two-byte
vendor payloads become stock type0x39 instead of generic type0x15. All32 payloads
and waits match stock; no PPS, shutdown, reset, supply or other-panel change.
The helper retains LP/channel and accumulated errors; MSM returns padded DMA
length, so successful transfer need not equal payload length. Actual C helper
and sequence pass32 packet contracts, LP/HS/channel,64 injected failures and
3 early exits. The old short-packet behavior fails the independent fixture.
CI now runs this check;98-patch replay/ARM64W1/strict checkpatch/12 recipe tests
pass. Still diagnostic only; require fresh physical wake/fault/rollback checks.

CI56 is tested and REJECTED for physical wake. Correct long setup packets,
PPS and both backlight-chip writes return success, but Pixel6 and user show a
backlit blank image after wake. No matched controller fault. Both CI profiles,
Android/graphics/fullfsck/timer/host-service/worker restoration pass. KeepCI44;
no unchanged repeat. Next compare startup/wake DSI/DSC/PPS state with targeted
diagnostics; do not guess resets or enable the broad inherited trace switch.

Next0206 is diagnostic only, with7 info-level DISPLAY_LINK sites active from
boot. DSI first-start readbacks are guarded by first_start/power_on/enabled;
10 audited control/status/timing registers are within both host resources.
No IRQ/FIFO flag reads, new writes, DCS reads, resets, rates, retries or delays.
DSC resource logs run only in ENABLING; PPS CRC reads memory. CRC32 is selected
but was already built-in, so effective config is unchanged. A16-case actual-C
comparison preserves old writes/state and tests read gating.99-patch replay,
ARM64 affected objects, strict checkpatch, packet contract and12 recipe tests
pass; inherited DPU kernel-doc warnings remain. Logging/reads perturb timing;
no promotion even if the image appears to wake. Keep9 scoped output sites and
one recorded cycle with exact rollback; do not enable broad y900.trace.

CI57 diagnostic capture passed, but physical wake is REJECTED. Both CI
profiles succeeded. The camera shows the greeter before screen-off and a blank
panel after wake. All28 link records were captured: timing, control/compression,
PPS checksum and DSC route metadata match initial startup. A dynamic clock-status
reading on one link and lane status on the other differ during sequential
first-start samples. These are not steady-state measurements or proof of a
root cause. Both backlight chips and panel commands return success, and no
matched controller fault occurs. Android, exact graphics rollback, filesystem,
timer, host-service and worker checks pass. Keep CI44 installed; do not promote
or repeat CI57 unchanged. Audit output restoration before selecting another
experiment. Private recordings and identifiers remain unpublished.

CI58 adds the unchanged [posted PHY mux initialization patch](https://lore.kernel.org/r/20261019130041.305805-1-xiaqinghuan@mail.ustc.edu.cn).
The current driver pre-seeds its bias reference count, so the bias helper can
skip restoring PLL_SYSTEM_MUXES. The patch writes its existing0xc0 value during
PHY enable under the existing lock. It changes no rates, voltages, reference
counting, reset sequence or delays. Source inspection supports testing it;
CI57 did not measure that register, so this is not a confirmed root cause.
The100-patch stack replays exactly and the affected ARM64 object compiles.
Original author/signoff/code patch ID are preserved. The posted Fixes title
mismatch and inherited trace-format warning are recorded separately from code
checks. Existing diagnostics remain: this candidate requires a bounded physical
wake test and exact rollback, then a later clean regression before promotion.

CI58 is tested and REJECTED for physical wake. The posted mux correction
alone is insufficient: initial greeter pixels pass, then the panel stays blank
with its backlight on. Both CI profiles and diagnostic capture pass. The
first-start clock-status differences also occur during working startup, so they
do not reliably identify the wake failure. No matched display-controller fault
was observed. Recovery initially failed to claim the USB interface before any
restore write; the existing guarded retry restored stock boot with full readback
verification. Android, graphics, filesystem, timers, services and workers were
independently verified afterward; the raw monitor error is preserved. CI44 stays
installed. Do not repeat this candidate unchanged or promote it. The next audit
examines panel supply/reset lifecycle; secure GPIO access remains excluded.

CI59 is a bounded panel-power diagnostic, not a production fix. It retains
only the BOE panel's three supply references through one screen-off/wake cycle.
Initial enable ordering and all settling delays, including warm prepares, are
preserved. Reuse does not add regulator references; devres cleanup releases them
before their handles are freed. The diagnostic refuses a reset GPIO and leaves
other panels unchanged. DCS/PPS, backlight, host/PHY/DSC and touch code are unchanged.
The101-patch tree replays exactly. Actual callbacks pass19 lifecycle/error cases
and three negative controls; packet checks, ARM64 compilation, strict checkpatch
and12 recipe tests pass. This tests a power/reset lead; it does not establish
rail voltages or successful wake. Remove0208 and its candidate-only build guard
before any production acceptance, even if this experiment wakes visibly. CI44
remains installed; use one recorded bounded cycle and exact Android restoration.

CI59 is tested and REJECTED for physical wake. The initial greeter is visible,
but the recorded panel stays blank after wake, matching the user's observation.
Logs confirm initial supply acquisition, retention during screen-off and reuse
at wake; this is not a voltage measurement. Retention is insufficient to fix
wake, and does not exclude every panel/reset failure. Both backlight chips and
panel commands return success, with no matched controller fault. Both CI profiles
pass. Normal Android return, exact graphics rollback, filesystem, timers, host
services and worker cleanup pass. CI44 stays installed. Remove the temporary
retention patch and its candidate-only build guard before the next candidate;
continue a bounded DPU/DSC/INTF routing audit. Do not repeat or promote CI59.

CI60 removes the unsuccessful panel-supply retention experiment and its build
guard. It adds seven diagnostic formats for actual DSC, CTL and INTF register
readbacks, restricted to SM8750 and the first kickoff of each enable. Each
snapshot reads 66 source-defined configuration/status locations across four DSC
blocks, one controller and two interfaces; 16 records before DSC setup and 16
after timing/DSI start are expected at startup and wake. There are no new writes,
delays, IRQ/FIFO reads or per-frame diagnostics. Mapped/subblock bounds, four
actual-C register allowlists,12 old/new kickoff comparisons, ARM64 objects and
strict style checks pass. Existing kernel-doc warnings remain. Readbacks/logging
can perturb timing and shadow-register values do not prove output on the wire.
This remains diagnostic only; preserve CI44 and require physical camera review
plus exact restoration. The recent upstream DSC cleanup proposal concerns
changed resource assignments; no such transition is established by current
captures, so it is not speculatively included.

CI60 diagnostic capture passed, but physical wake is REJECTED. Initial greeter
pixels are visible; the camera remains blank after wake and fresh focus input.
All64 routing records were captured. Sampled DSC/CTL/INTF routing, compression,
size and timing configuration matches working startup; only the current scan
line counters differ. These sequential readbacks do not prove active-shadow
latching or valid pixels on the wire. No matched controller fault appeared, and
panel/backlight commands succeeded. Both CI profiles and normal Android,
graphics, filesystem, timer, host-service and worker restoration pass. CI44 stays
installed. Do not install or repeat CI60 unchanged. Continue a bounded PHY/PLL
restart and clock-parent lifetime audit before changing hardware sequences.

CI61 corrects a concrete bonded-DSI clock mismatch. The driver puts PHY1 on
the master PLL0's external-clock path, while the inherited DSI1 host byte/pixel
clock inputs still pointed to PLL1. The board now points those two named inputs
to PHY0, following the [same-SoC correction](https://github.com/TheMojoMan/oneplus-erhai-linux-old/commit/07899dd43b1b4c8f12e11888344a31769ace4307)
and the active stock panel's PLL0 selection. This is a credited board adaptation,
not an unchanged import. The whole compiled device-tree comparison changes only
two provider cells; the other ten clocks and physical PHY1 lane connection are
preserved. No driver writes, reset sequence, delays, rates or voltages change.
The new CI topology guard rejects the old mismatch and four malformed variants.
No additional PHY diagnostic was added; existing bounded diagnostics remain.
Keep CI44 installed until recorded wake and a later clean regression pass.

CI61 is tested and REJECTED for physical wake. The built device tree contains
the verified two-provider correction, and the number of PLL prepare records
changes, but the panel still stays blank after wake. Initial greeter pixels
pass. All64 routing records were captured, with matching sampled configuration
and only transient scan-line differences. No matched controller fault occurs;
panel/backlight commands succeed. Both CI profiles and normal Android,
graphics, filesystem, timer, host-service and worker restoration pass. CI44
remains installed. The source clock mismatch is corrected but insufficient;
keep it as the next candidate baseline, without claiming physical wake support.
Do not install or repeat CI61 unchanged. Next compare actual powered PHY gate,
mux and divider state within existing ownership and register bounds.

CI62 adds read-only PHY state diagnostics at the first powered video start of
each enable, only for SM8750. An enabled PHY and active runtime power are
required. Mapped bounds guard eight common-register reads; seven PLL reads are
skipped when that PLL is off. The diagnostic uses cached rate state without
clock-framework callbacks and adds no writes, PM votes, rates, resets or delays.
The CI61 shared PLL0 topology correction remains. Four ARM64 objects, strict
style checks, unchanged DT/resource bounds and42 actual-C guard/equivalence
cases pass; the inherited trace-format warning remains. Sequential logging
between link starts can perturb timing, and values do not prove wire output.
This is diagnostic only and awaits one recorded bounded wake test with exact
restoration. Keep CI44 installed; remove diagnostics before promotion.

CI62 is tested and REJECTED for physical wake. The master PHY was captured
at startup and wake; common gates, mux and output divider match, while the
fractional divider's low byte differs by one. The slave snapshot was skipped:
the diagnostic mistook a per-controller ownership flag for physical PHY power.
The bonded manager enables both PHYs while either controller holds a reference.
This is a capture gap, not evidence that the slave was off or that PHY causes
are excluded. Correct the diagnostic guard against the actual enable/disable
lifecycle before another test. Routing capture and normal Android, graphics,
filesystem, timer, service and worker restoration passed. CI44 remains installed;
do not repeat CI62 unchanged or promote diagnostic code.

CI63 corrects only the PHY diagnostic ownership guard. When both bonded peers
exist, either controller reference proves both PHYs are enabled; standalone
and incomplete-pair behavior still follows the manager's existing lifecycle.
Actual enable/disable/diagnostic callbacks pass24 lifecycle/error cases and264
per-link or invalid-ID observations; the old guard fails that same oracle.
Only the manager diagnostic helper changes. ARM64 compilation and strict style
checks pass. First-host-start, runtime power, mapped bounds and PLL-on guards
remain unchanged, with no added hardware writes, waits, rates, resets or PM votes.
This fixes capture coverage, not physical wake. A bounded two-link capture and
exact restoration are still required; keep CI44 installed.

CI63 captured both PHYs successfully, but physical wake remains REJECTED.
All20 PHY and64 routing records are present. Sampled common gates, receive
buffers, mux/control/output dividers and cached state match working startup;
only the master's fractional divider low byte differs by one. Routing settings
match except transient scan-line counters. These observations do not measure
physical DSI signals or exclude every PHY/panel cause. Initial greeter pixels
pass, then the recorded panel stays blank after wake and focus input. No matched
controller fault appeared. Normal Android, exact graphics, filesystem, timers,
services and worker restoration passed. CI44 remains installed. The capture
guard is corrected; no wake fix or promotion is claimed. Audit stock panel/TDDI
wake ordering before selecting another changed test.
