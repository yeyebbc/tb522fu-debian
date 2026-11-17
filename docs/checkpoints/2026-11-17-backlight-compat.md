# Backlight workaround checkpoint — 2026-11-17

The user confirmed the unplugged Fedora Lock/Space wake works, then requested
finalization, commit/push, a new CI build and Debian13 return preparation.

- Audit rollback point: checkpoint-oneplus-display-audit-20261117.
- Final implementation/build source: c6941972289c88e6122ad2dca1062c40adcc97b3,
  branch oneplus-display-method. Public code retains donor attribution.
- [CI96](https://github.com/yeyebbc/tb522fu-debian/actions/runs/44095613555):
  Debian-root kernel profiles plus independent display-power-aarch64 artifact.
  Overlay build and29 checks pass; the downloaded archive/manifest are verified.
- CI93's separate117-patch PHY/controller kernel candidate passed both builds;
  it has not been booted on the tablet. No kernel or system-suspend acceptance.
- Backlight trial: connected physical off/on passes; visible lock screen after
  Space on battery appears before USB power returns. Stored brightness, running
  GSD adapter, active MDSS/KMS and unchanged panel lifecycle were checked.
- Observation limit: reconnect atSpace+5.44s violates the probe's eight-second
  guard, so native probe1 is preserved. Longer observation and fresh unlocking
  were not completed. One positive lock-screen wake is not a drain or repeated
  reliability result.
- Recovery/cleanup and exact overlay removal/fullfsck pass. Android is running;
  DebianCI78, both comparison roots, graphics and partition geometry remain.
- Debian13 read-only preflight and native GSD binding check pass. Exact
  hash-guarded install/rollback payloads are prepared and remain unapplied.

See [implementation evidence](../oneplus-display-method.md) and
[Debian return preparation](../debian13-display-return.md). The workaround
keeps the display link active and costs power. Actual system sleep stays masked.
