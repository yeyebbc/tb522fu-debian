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
