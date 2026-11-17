# OnePlus display-method checkpoint — 2026-11-17

The same-SoC [source audit](../onepluspad-2pro-display-audit.md) is complete.
The next selected route adapts the donor's backlight-only display blanking:
keep the display link running and switch its LEDs off. It is an explicit
workaround with a power cost, not an accepted system-suspend or kernel fix.
Implementation and hardware acceptance have not started at this checkpoint.

## Preserved baseline

- The [Fedora CI91 checkpoint](2026-11-17-fedora45-ci91.md) remains valid:
  connected physical wake passes, unplugged Lock/Space physical output fails.
- CI91 recipe: `a83b3187cdcf5e2cb25e79b94d34bff2f343b3fd`.
- Kernel source: `fd7d0301638316f990c0e0605a11da1d1460beb5`.
- Patched tree: `5f8d64bb9212b28af229b2d6f11bf06f040b7f98`.
- Boot SHA-256: `b6aaf10b944ca71532e35e220843389279ca4ca6456af27a3e499bd6cc6b0983`.
- Selected installed/default Linux remains Debian CI78; retained Ubuntu and
  Fedora trial roots, Android and approved partition geometry are preserved.
- Latest verified device state is restored Android with selected-image,
  graphics, filesystem, independent-return and host/camera cleanup complete.
  This source-only audit performed no new device operation.

## Pinned donor

Integration `a82cd442c5e4c1e460bfc65483d4344698ced62a` pins kernel
`1c21cb9895d69c1c5e83ceae68952fedf522644a`, based on v7.4-rc2.
Fifteen archived donor files match their Git blob IDs; the comparison uses
eight exact baseline files and twelve donor commit records. Raw references
and hardware logs remain private.

## Next implementation boundary

Adapt the donor's display-power adapter/service to the actual Lenovo backlight
driver and selected GNOME ABI. Preserve screen-lock authentication, brightness
and user locale settings. Keep normal system sleep masked. Do not combine this
workaround with the candidate DSI/CTL/GMU changes or a kernel-version upgrade.
Record the workaround and its exit condition in technical debt.

First require offline build/interface checks and a rollback manifest. Then
use an independent bounded return, local logging and physical camera evidence
for a connected backlight off/on check before an unplugged Lock/Space check.
Require actual fresh physical frames; GNOME display-on state is insufficient.
Do not promote the default image or claim low standby power from this test.
