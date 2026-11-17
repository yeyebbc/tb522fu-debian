# OnePlus Pad 2 Pro SM8750 display-wake audit — 2026-11-17

User reference: https://github.com/yzddmr6/onepluspad-2pro-mainline

This is a source assessment. No tablet operation, kernel edit, build, CI run,
installation or publication was performed. The Fedora failure checkpoint remains
valid. The findings below are candidates, not hardware acceptance or an
established root cause. A subsequent checkpoint records the next selected route.

## Exact comparison

- Integration commit: [a82cd442c5e4](https://github.com/yzddmr6/onepluspad-2pro-mainline/tree/a82cd442c5e4c1e460bfc65483d4344698ced62a).
- Its current [kernel manifest](https://github.com/yzddmr6/onepluspad-2pro-mainline/blob/a82cd442c5e4c1e460bfc65483d4344698ced62a/kernel/source.json)
  pins linux-sm8750-erhai commit `1c21cb9895d69c1c5e83ceae68952fedf522644a`,
  branch `sm8750/v7.4-dev`, baseline `v7.4-rc2`. Older changelog sections do
  not describe this current source pin.
- Our tested CI91 source: `fd7d0301638316f990c0e0605a11da1d1460beb5`,
  tree `5f8d64bb9212b28af229b2d6f11bf06f040b7f98`, 114 patches; recipe
  `a83b3187cdcf5e2cb25e79b94d34bff2f343b3fd`.
- Comparison used `git show` of the exact tested commit, preserving unrelated
  working-tree changes.
- Fifteen downloaded source/package/document files were archived and their
  Git blob IDs verified. Seven baseline driver files plus dsi_host.c and
  twelve donor commit records are retained privately with SHA-256 sums.
  Presence checks in source-comparison.json supplement direct function review;
  a name match by itself does not establish behavioral equivalence.

Raw source snapshots, commit diffs and physical-test evidence are retained
privately. The public [Fedora checkpoint](checkpoints/2026-11-17-fedora45-ci91.md)
records the failed physical test and completed recovery.

## Most useful finding: their default avoids display-link restart

The package's [GSD adapter](https://github.com/yzddmr6/onepluspad-2pro-mainline/blob/a82cd442c5e4c1e460bfc65483d4344698ced62a/packaging/erhai-display-power/gsd-backlight-compat.c)
interposes GNOME Settings Daemon's display power setter and sends requests to
a backlight service instead of Mutter's ordinary connector-off path. The
[mode utility](https://github.com/yzddmr6/onepluspad-2pro-mainline/blob/a82cd442c5e4c1e460bfc65483d4344698ced62a/packaging/erhai-display-power/tree/usr/sbin/erhai-display-power-mode)
states that compat is the package default: keep the MDSS parent runtime-active,
leave the display pipeline running and blank only the LEDs. The matching
[udev rule](https://github.com/yzddmr6/onepluspad-2pro-mainline/blob/a82cd442c5e4c1e460bfc65483d4344698ced62a/packaging/erhai-device-support/tree/usr/lib/udev/rules.d/81-erhai-display-power.rules)
explicitly records its power cost and lack of a system-suspend fix.

This is a credible fallback or controlled diagnostic for our blank/wake path,
but it bypasses the failing lifecycle. It would not establish proper display
power collapse, low standby drain or system suspend. Its exact GSD50 preload
ABI and OnePlus led-backlight discovery must not be copied blindly into our
Debian/Ubuntu/Fedora environments or Lenovo KTZ8869 driver.

The [suspend report](https://github.com/yzddmr6/onepluspad-2pro-mainline/blob/a82cd442c5e4c1e460bfc65483d4344698ced62a/docs/SUSPEND.en.md)
does report successful real s2idle/RTC/button/cover tests, including some
standard-display-mode tests. Its long 23-cycle deepest-state run was USB
connected; unplugged standby drain remains unmeasured. Successful system sleep
on that board does not establish our unplugged display-only Lock/Space case.

## Candidate changes absent from our exact tested source

| Area | Actual difference | Fit and limit |
| --- | --- | --- |
| Post-link PHY resynchronization | [282ca2a9](https://github.com/yzddmr6/linux-sm8750-erhai/commit/282ca2a9a9c49091d8ebb6b16bae341eabf208bc) toggles each retime FIFO 0→1 after BOTH host link clocks start; [3b4689ae](https://github.com/yzddmr6/linux-sm8750-erhai/commit/3b4689ae948f0e3fd36fa9b09ade279ae36d4c6b) then resets the bonded SM8750 controllers before panel commands. Our FIFO setup occurs in PLL prepare, and no equivalent manager-stage callbacks/late reset exist. | Strong source-level sequencing lead. The donor describes vendor prepare ordering; Lenovo stock ordering still needs direct comparison. Our PLL prepare repeats three times before panel commands, so moving a one-time synchronization boundary out of CCF is relevant. Neither change is a demonstrated Lenovo fix. |
| Shared DPU controller lifecycle | [cece3773](https://github.com/yzddmr6/linux-sm8750-erhai/commit/cece3773ddb522f50f63c1965e5ed5125fb84923) submits a shared video CTL only once. [8b53b972](https://github.com/yzddmr6/linux-sm8750-erhai/commit/8b53b972e9bd2fee977401a36f8f130bb30df266), [f6dafb3d](https://github.com/yzddmr6/linux-sm8750-erhai/commit/f6dafb3dbc4201e92d93cf5188518f077ba4f1c3) and [1fead179](https://github.com/yzddmr6/linux-sm8750-erhai/commit/1fead1793340e023ab6f9112d542f46460d00351) defer pixel-path cleanup and perform a staged slave handoff before full teardown. Our slave-first disable still performs per-physical cleanup/reset and our kickoff lacks the shared-CTL skip. | Our logs confirm two INTFs share CTL0, so this is relevant common hardware code. However, their later failure signature includes missing VBIF halt ACK and DSI DMA timeout; CI91 already has a real halt ACK and neither timeout. Treat the series as a coherent lifecycle review, not isolated reversal of our slave-first fix. Our existing slave timing-mux disconnect also changes the interaction. |
| PLL bias reference counting | [cd497360](https://github.com/yzddmr6/linux-sm8750-erhai/commit/cd497360ce38c45a7b387e96747cd6adb3642e64) writes PLL_SYSTEM_MUXES on every bias-enable call. Our patch0207 writes it at PHY enable but retains the bias helper's nonzero-reference early return. | This is a real remaining difference, not a duplicate of0207. CI91 already reads master mux0xc0 and locked PLL at failed wake, identical to connected success, so evidence makes it a lower-priority explanation. |
| DSI error propagation / PM reference balance | [18673e2b](https://github.com/yzddmr6/linux-sm8750-erhai/commit/18673e2bf85f27e8b0057669dae06517f79f6a0f) stops on resume/rate/clock failures and balances acquired PM refs. Our xfer preparation ignores these return values. | Useful correctness and diagnostic improvement. An unchecked failure can hide the earlier cause; current evidence does not demonstrate such a failure. |
| GMU interrupt races | [813b1de4](https://github.com/yzddmr6/linux-sm8750-erhai/commit/813b1de4068ae74bb6afbe31a33a8e47cfedbd57) masks HFI before boot; [6721b336](https://github.com/yzddmr6/linux-sm8750-erhai/commit/6721b3361f07f1097443a4829733b4fbf646a773) clears only the handled fault bit, preserving polled acknowledgements. Our source has the older behavior. | Valid separate runtime-PM race candidates. Latest Fedora log contains no GMU firmware fault, HFI timeout or GPU_SET timeout, while the compositor's GPU accounting survives wake. Lower priority for this physical-output failure. |

Our Lenovo is C-PHY (`cphy=1` in the actual boot log). The donor's resync
change deliberately skips CLK_EN_SEL clearing for C-PHY. Our0x30/0x34 values
must not be judged against its D-PHY0x20/0x24 example. Do not import the donor
panel timing, strength, GPIO, rail, lane or DSC settings: its CSOT XN242 board
and our Lenovo BOE panel differ.

The donor [slave-divider patch](https://github.com/yzddmr6/linux-sm8750-erhai/commit/d0f6d61204c78be72610d64132402ac0e0d6b322)
adds another configure-before-start operation. Our observed CLK_CFG0 is already
0x21 on both PHYs and our existing code writes PERF_OPTIMIZE0x22 to the slave.
The reported reset-divider mismatch is not established here; copying its
D-PHY-specific example is not justified.

## Differences that are already covered or have weaker causal support

The DPU core-clock [restore-vote helper](https://github.com/yzddmr6/linux-sm8750-erhai/commit/32bf5e5fd79c89a07b5a001d4bf9d1b706061f77)
is absent, but the commit's specific motivating zero-rate OPP request is already
prevented by our `if (!clk_rate) return 0` in dpu_core_perf.c. This is the same
mechanism audited from the earlier Xiaomi reference. A different transient
power problem remains possible, but the missing helper is insufficient reason
to add a high vote or declare it the fix. The current donor also retains the
zero-rate guard, so its historical commit explanation cannot substitute for a
fresh causal comparison.

We already carry slave-first DSI host shutdown, upstream slave-first DPU
encoder shutdown, the VBIF AXI-halt series, initial PLL mux restoration,
idle-XO clock parking, CCF-owned PLL start and GMU component-lifetime fixes.
Reimporting those does not create a changed hypothesis.

## What CI91 evidence changes about the ranking

During the failed battery transition:

- DPU shutdown at401.6299s receives halt status0x31 with poll return0.
- DPU resume at434.1154s enables clocks with return0.
- Both PHYs report C-PHY; master PLL mux0xc0/status0x51 and both retime FIFOs1.
- The shared controller is CTL0, INTF active0x6/master0x2, DSC0xf.
- No new matched DPU/DSI/GMU failure appears. Camera frames before USB reconnect
  still show blank output while the software reports active linear XR30.

These are sampled registers and software state; they cannot exclude a bad
transient, wrong retime synchronization or panel state. They do rule against
claiming that the donor's missing-halt-ACK, zero-mux or GMU-timeout mechanism
has been observed on the current failure. RBUF=1 alone does not prove its
required 0→1 edge occurred at the correct post-link-clock boundary.

## Recommended next investigation

First compare Lenovo's exact vendor prepare/teardown ordering against the
post-link FIFO/controller-reset sequence and shared-CTL series. Select one
minimal correction or one inseparable prerequisite set with a written expected
difference; do not import the whole OnePlus tree, upgrade every driver together
or mix in a permanent vote. The post-link synchronization boundary is the
best new sequencing lead from this audit; shared-CTL lifetime is the other
substantial candidate.

Any later hardware test must retain the same-boot signed-in connected physical
wake gate before one unplugged Lock/Space cycle, local USB-power/key chronology,
pre-reconnect camera frames, full supported-driver inventory and independent
return/rollback. Keep actual system sleep masked for that display-only test.
Backlight-only blanking is a separately labelled workaround if requested;
measure its power cost before treating it as a normal sleep policy.

No candidate has been built, booted, promoted or selected by this assessment.
