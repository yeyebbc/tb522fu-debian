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

CI64 is a bounded touch-isolation diagnostic. It disables only the touchscreen
DT node; the complete compiled-tree comparison leaves SPI, keyboard, panel,
clock and PHY settings unchanged. This tests whether Linux touch firmware
reload, suspend/resume or IRQ activity is necessary for the blank wake. It is
not a touch removal from the product or a wake fix. Runtime checks must confirm
no touch module, SPI device or input nodes before and after the cycle; keyboard
focus injection and display fault checks are unchanged. Six negative guard
cases reject unexpected touch activity or configuration. Initial physical
pixels, one recorded wake cycle and exact restoration are required. Even if
wake succeeds, remove this diagnostic before production acceptance and resolve
the interaction with touch enabled. If it fails, shared TDDI hardware/reset
causes remain open. CI44 stays installed; neither CI64 profile may be promoted.

CI64 completed: touch isolation was verified before and after the cycle, but
physical display wake still failed. The initial greeter was visible; the panel
remained blank after wake, also confirmed by the user. Both PHYs and routing
were captured without matched display-controller faults; panel and backlight
calls returned success. Linux touch activity is therefore not necessary for
this failure, while shared TDDI hardware/reset remains unexcluded. Android,
exact graphics rollback, filesystem checks, timer retirement and all worker
cleanup passed. CI44 remains installed. Do not install or repeat CI64 unchanged.
The next user-requested experiment reuses CI63 with touch and keyboard enabled
to distinguish real whole-system suspend from the earlier display-only cycles.

## CI65 full-driver suspend candidate

Whole-system s2idle on CI63 restarted the tablet after all supported drivers
and Bluetooth startup were ready. The recovered kernel had a different boot
ID, so the later visible desktop was a new boot, not a successful resume.
Persistent crash storage was empty; the failing callback remains unidentified.
Android, graphics and filesystem restoration passed. CI44 remains installed.

CI65 restores touch after the failed isolation experiment and imports the
[upstream SM8750 ISLAND1 reservation correction](https://lore.kernel.org/r/20261111-sm8750-llcc-island1-v1-1-64055702ca3f@gmail.com) unchanged.
Lenovo's pinned stock source agrees with the reserved-way field and register
mapping. This is a plausible reset fix, not verified on this tablet. Another
same-SoC report was not fixed by it. PM_DEBUG permits staged freezer, device
and platform callback tests before real s2idle. All supported modules stay
loaded. No permanent resource votes or unrelated USB changes are included.
No promotion until same-boot resume, measurable sleep and physical fresh
screen output pass, followed by exact restoration.

## CI65 staged suspend result

All supported drivers and Bluetooth startup completed. Freezing tasks passed.
The device suspend/resume test returned in the same boot, but the panel's
first initialization DCS command timed out (-110), followed by DSI lane/FIFO
errors. Camera footage confirms a blank display. The test stopped before
late/noirq callbacks and before actual s2idle. Thus the ISLAND1 correction's
effect on the prior full-sleep reset remains untested. Kernel suspend success
counters did not represent a working display. Android, graphics, filesystem,
timer, services, network and worker restoration passed; CI44 stays installed.
Do not install or repeat CI65 unchanged. Next inspect the first display command
transfer and clock ownership across device PM before selecting another patch.

## CI66 explicit idle DSI clock source

The next candidate implements the stock clock handoff before PLL shutdown.
Both DSI controllers receive the same crystal input used by DISPCC parent
zero. Their byte/pixel source clocks switch to it while the PLL is still
available, then existing slave-first link shutdown continues. Normal startup
still selects PLL0 for both hosts. Controllers without the optional input
retain their behavior; clock API errors are reported.

This adapts [tiopex's ROCKNIX patch](https://github.com/ROCKNIX/distribution/blob/bcf3b5bc574990b96543484575b06f912153a715/projects/ROCKNIX/devices/SM8750/patches/linux/0048-drm-msm-dsi-reparent-byte-pixel-src-to-xo-on-disable.patch), using a declared XO clock rather than assuming the initial parent is XO.
Lenovo's captured tree and pinned stock manager confirm the explicit input
and switch-before-PLL-off ordering. No rates, voltages, raw registers, delays
or permanent votes are added. Two per-shutdown API-result messages are
diagnostic only. Source and offline checks pass; hardware is untested. Keep
CI44 installed and require full-driver staged PM/real-sleep/physical-display
acceptance with exact Android restoration.

## CI66 staged suspend result

Both display controllers switched to the explicit crystal input successfully.
The device-PM resume now completes panel initialization and DSC PPS transfer
without CI65's first-command timeout or DSI lane/FIFO errors. This is partial
progress, not accepted display wake. The next test stage began about30ms after
device resume, while asynchronous touch resume was still running. A pending
frame timeout occurred during that second shutdown, before the platform
diagnostic reached late/noirq callbacks. Camera footage later showed patterned
output. Actual s2idle was not attempted.

All supported drivers remained loaded; the boot identity was unchanged. Android,
exact graphics rollback, filesystem, timer, services, network and workers were
restored. CI44 remains installed. Preserve this result and do not repeat the
back-to-back sequence unchanged. A single isolated device-PM cycle followed by
fresh compositor work and camera observation will distinguish first-resume
corruption from interference by the second transition. That diagnostic does
not enter real sleep or permit installation.

## CI66 follow-ups and CI67 USB candidate

A single device-PM diagnostic restored the visible desktop. A staged follow-up
waited for completed touch resume and fresh compositor activity between stages;
its first device wake restored pixels, but the later platform wake left the
panel blank despite clean display logs and fresh GPU work. Actual s2idle then
rebooted. A separate platform-only test from a fresh boot also rebooted, without
requesting actual sleep. Its last persistent event is the request; the failing
callback and suspend-versus-resume boundary remain unknown. The latter used the
login greeter while earlier physical success used a signed-in desktop, so do
not attribute the difference solely to PM depth or transition count. Recovery,
exact graphics restoration, filesystem checks and worker cleanup passed.

CI67 adds only the unchanged [upstream USB role-notification fix](https://lore.kernel.org/r/20261111090122.134-1-tvlad744@gmail.com),
[acknowledged by the USB maintainer](https://lore.kernel.org/r/avUdNnZ7GWREGQOp@vbox).
It moves glue notification into the existing freezable mode-switch work, so a
role change cannot touch controller registers while system-suspend has disabled
the clocks. The latest requested role is preserved, including changes that map
to the same controller mode. The original patch ID matches the import.

This fixes a known SM8750 USB defect; our reset has no captured role-change
trace, so it is not an established root cause. First test the single platform
PM scenario with all supported drivers, camera evidence and exact recovery.
Keep CI44 installed. Diagnostic display logging remains in the candidate and
must be removed and retested before any production promotion.

User-supplied Xiaomi Pad6Pro v0.6.2 [display power-vote fix](https://github.com/yzddmr6/linux-sm8450-liuqin/commit/8ec7416f90f6058acf343aacef33d1761bcde913)
was audited. Its motivating case is SM8750: a retained core-clock frequency
with a cleared DPU power request. Our newer pinned base already skips the
zero-rate OPP request on last-CRTC disable, and genpd restores the saved vote
before the DPU resume callback. The exact described path is therefore already
prevented in source; this does not exclude other power sequencing failures.
No Xiaomi rates, voltages, permanent votes or additional kernel patch are
imported. Tests already use s2idle. Correlate clock/power-state evidence with
physical output in the next bounded test.

## CI67 first platform-PM result

With all 39 supported modules loaded and Bluetooth startup complete, one
platform diagnostic returned in the same boot (success 1, fail 0). Camera
review confirms the display turned off, returned to the greeter, rendered
fresh focus changes and later showed the signed-in desktop. No actual sleep
was requested. This supports one diagnostic cycle only, not reliable suspend
or installation.

The cached display-core source and branch rates were 417MHz, with DPU/MMCX
performance state 192, at the sampled points before and after the transition.
These match the existing OPP table; they are not physical voltage measurements
and do not exclude a transient sequencing fault. The change remains the
original upstream USB role-notification patch; a causal role-change trace is
still missing. No extra display power vote was added.

Recipe `bd8fed615c964030fe6b20aee625be6982068352`, kernel source
`3588a61ee710eaed761a2deb3bdc75a6c72c1c2a`, boot SHA256
`a4b59b9d5c19bc11c6d0e6835f80bd9d075281d13230bbb1f01f91c5ab39a382`.
Android, exact graphics rollback, filesystem checks, temporary return units,
host services and worker cleanup all passed. Keep CI44 installed. The next
discriminator is one RTC-gated actual s2idle from cold boot, with no preceding
PM cycle, retaining all drivers and physical fresh-frame acceptance.

## CI67 actual suspend-to-idle result

A separate cold boot loaded all 39 supported modules and completed Bluetooth
startup. The user signed in before the test, and the probe selected that
current GNOME session. The awake RTC alarm interrupt passed; one real s2idle
request followed, with a verified 20-second alarm and no preceding PM cycle.
It never returned. A changed boot ID and camera footage of the bootloader and
new Linux console confirm a reboot. No saved crash dump was available.

The earlier single platform-PM pass remains narrow progress. Reliable display
wake and actual sleep are not fixed, and the USB role patch is insufficient
to fix full suspend. Do not install or repeat this candidate unchanged. Exact
Android and graphics restoration, filesystem checks, timer retirement, host
services and network/worker cleanup passed; CI44 stays installed. Source,
recipe and image hashes are unchanged from the platform result above.

In this kernel, the platform diagnostic returns after late/noirq device
callbacks, immediately before `s2idle_loop()`. Actual s2idle does not enter
the secondary-CPU-offline and syscore branches used by deep suspend. The next
source audit concerns CPU/cluster idle and wake-interrupt routing. This is a
remaining difference to investigate, not an established cause: only one
platform cycle passed, and that test used the greeter rather than the signed-in
session. Preserve all supported drivers and avoid guessed resource votes.

## CI68 complete SM8750 cache-table correction

Replace the earlier island-only patch with Konrad Dybcio's original
[upstream correction](https://lore.kernel.org/r/20261113-topic-8750_llcc-v1-1-6536cb46d7fe@oss.qualcomm.com).
It retains the island reservation and corrects CVP grouping/allocation, six
video/camera allocation flags and the CAMRTRF priority. All 32 entries match
Lenovo's pinned stock table after normalizing field names/defaults and the
explicit downstream grouping flag. Original authorship, signoff and code
patch ID are retained. The historical island patch stays available but is no
longer applied separately.

This is the only functional change from CI67. It corrects documented table
defects; it is not yet an established explanation or fix for our suspend
reset. CPU idle states, wake IRQs, DT, power votes and peripheral drivers are
unchanged. Keep CI44 installed and require all-driver physical wake and actual
sleep acceptance with exact recovery before any later promotion.

## CI68 suspend results

With the complete upstream LLCC table correction, one isolated platform-PM
diagnostic restored the greeter and fresh focus changes. All 39 supported
modules were loaded and Bluetooth startup was complete; the boot ID stayed
unchanged, with one successful PM cycle and no recorded failure.

A separate cold boot then attempted actual s2idle without a preceding PM
cycle. The signed-in GNOME session was selected, all drivers remained loaded,
and the awake RTC interrupt check and 20-second alarm readback passed. The
request never returned. A changed boot ID and recorded bootloader screen
confirm a reboot; persistent crash storage was empty. This candidate is
rejected for installation and unchanged retesting. The full table correction
is insufficient to fix the reset; the failing component remains unidentified.

Recipe `63d9e96a7ca697580282f8a1872a6051c1a2e5b3`, kernel source
`7bc64379ce1ced431d52a4e700d8848030a7939f`, boot SHA256
`1dd0a4d1e5b83c4bf1f3947466931becf73906105860c39acb58c1f82a4dcee6`.
Both CI profiles built successfully. Exact Android and graphics restoration,
full filesystem checks, temporary return-unit retirement, host services and
network/worker cleanup passed after both tests. CI44 remains installed.
Reliable display wake and actual suspend are still unresolved.

## CI69 system-idle isolation diagnostic

CI69 removes only the system power domain's SS3 idle-state reference from the
board device tree. CPU C4 and cluster CL5 states, their stock parameters and
timings, the domain hierarchy, RPMh notification path and all supported device
drivers remain intact. The generic PM-domain code supplies a zero-initialized
default state; the PSCI callback leaves the previously selected CPU/cluster
request unchanged when that state's data is absent. The change also restricts
runtime idle. It adds no resource vote or guessed firmware parameter.

This is a diagnostic configuration, not a suspend fix. It tests whether the
reset depends on enabling the deepest system request; success would not
identify the faulty consumer or demonstrate deep power collapse. Compare
same-boot RTC wake, measured sleep duration, fresh physical display output and
exact restoration. Keep CI44 installed, and remove this restriction and its
candidate-only build guard before any production acceptance.

All 1,201 compiled DT nodes were compared. The sole functional change is the
removed system idle-state reference; the now-unreferenced SS3 node loses its
generated phandle, and other phandles are consistently renumbered. No other
property value changes. The guard accepts this candidate and rejects the old
unrestricted tree plus seven malformed CPU/cluster/RPMh variants. DT compilation,
code style and the complete 110-patch tree replay pass. Hardware is untested.

## CI69 platform diagnostic result

The running device tree correctly omitted SS3 while preserving CPU C4, cluster
CL5 and the RPMh domain link. All 39 supported modules and Bluetooth startup
were ready. One platform-PM diagnostic returned in the same boot, with one
success and no failed callback count; asynchronous touch resume completed and
fresh GPU/compositor checks passed without matched display-controller errors.

Physical wake nevertheless failed. The recording shows a visible greeter and
signed-in desktop before the cycle, then a black panel throughout the resumed
fresh-frame checks. Actual s2idle was not attempted. This candidate is rejected
for installation and unchanged retesting. The earlier CI68 platform pass used
the greeter; this run used a signed-in session with Settings open, so the result
does not establish that omitting SS3 caused the blank output. Dependence of the
actual-sleep reset on SS3 remains untested.

Recipe `2d0391c793a623783803df1245a2cab1923b46de`, kernel source
`8b3c012c84b4f1755d316da5817f414f46c4a89f`, boot SHA256
`a2dbded7976335ae439e3f2d3f4989cd37cdfbb2ee125275d9304c27473fbbcb`.
Both CI builds, exact Android and graphics restoration, full filesystem checks,
return-unit retirement and host service/network/worker cleanup passed. CI44
remains installed. Remove the SS3 diagnostic restriction before selecting the
next functional candidate; improve retained failure evidence before more sleep
tests.


## CI70 retained-log mapping diagnostic

A non-suspend two-boot test on unchanged CI68 accepted a PMSG marker on the
first boot but found no stored record on the second. Pstore was mounted, both
live and archived directories were empty, and systemd skipped archival for an
empty directory. The previous marker was also absent from the second boot's
journal. Both local capture services and the USB reconnect path worked; Android
restoration and filesystem/temporary-service/host cleanup passed. This does not
identify loss in cache, firmware, the programmer path or early kernel startup.

CI70 replaces the rejected SS3 isolation patch with one ramoops mapping change
relative to CI68: `mem-type = <2>` becomes the documented default `<0>`. The
[upstream ramoops documentation](https://www.kernel.org/doc/html/latest/admin-guide/ramoops.html)
describes type2 as cacheable and recommends write-combined type0. Both the
vmap and ioremap paths select the normal noncacheable mapping for type0 on
arm64; the actual prior runtime mapping was not measured. This is a diagnostic
hypothesis, not an established explanation or a suspend correction.

The reserved address, region and record sizes, ECC and reason filter stay
unchanged. CPU C4, cluster CL5 and system SS3 are all restored to the CI68
configuration; no idle restriction, clock/power vote or restart-handler change
is added. First hardware acceptance is a bounded two-boot marker check without
suspend. Do not promote this image or claim hard-reset retention from a clean
EDL/programmer test. CI44 remains installed and prior failures remain recorded.

Local DT compilation and comparison of all1,201 nodes show only the ramoops
`mem-type` change relative to CI68. Eight negative geometry/idle guards pass;
keyboard, camera and display wiring guards remain satisfied. The complete
110-patch series replays to tree`57468fc57780b4a734cc55e0a0f9e0f8e96e3663`;
12 recipe tests and the new patch's strict code-style check pass. Hardware
retention remains untested for this candidate.
