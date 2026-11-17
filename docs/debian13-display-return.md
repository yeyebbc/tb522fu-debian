# Debian13 return preparation

The user selected Debian13 after the Fedora backlight workaround restored a
visible lock screen on battery. Android is running after verified recovery.
Debian CI78 remains selected on the existing256GiB filesystem; both comparison
roots and rollback kernels are preserved. No new kernel is installed by the
display overlay or this plan.

The Build ARM64 artifacts workflow produces installed and bounded Debian-root
kernel images when dispatched with trial_root=debian. It also publishes
display-power-aarch64: the board-scoped overlay, source/file manifest and
SHA256SUMS. The kernel contains the117-patch source stack and the separate,
hardware-untested post-link PHY/controller sequence. A successful build does
not accept its display-wake behavior.

Before the Debian return:

1. Recheck AndroidB, selectedCI78 and graphics hashes, filesystem cleanliness
   and the approved partition geometry through the existing read-only mount.
2. Inspect Debian13's own gsd-power/libgsd dynamic setter binding and the new
   adapter's ARM64/glibc requirements. Preserve Debian's distro libraries,
   account, locale, brightness policy and supported drivers.
3. Prepare an exact new-file install and hash-checked rollback for the eight
   overlay files plus socket-enable symlink. Refuse existing or foreign files.
   The Fedora trial install has already been removed; it must not establish
   Debian installation or runtime acceptance.
4. Use the existing Debian selection and independent recovery for a bounded
   first boot. Verify the active GSD maps the adapter, MDSS stays active and
   the backlight blanks without KMS shutdown. Check unplugged Lock/Space and
   unlocking to a fresh desktop before any permanent kernel promotion.

Keep actual system-sleep targets masked. The workaround costs power because
the panel link/GPU display pipeline remain active. Drain, long-duration blanking,
Power/lid behavior and repeated wake remain pending. Retire compatibility once
normal unplugged connector power cycling reliably restores physical images and
its power behavior has been measured.

The kernel candidate should receive its own normal-path test after removing or
disabling the adapter/rule/service and proving they are absent from the running
GSD. Do not use a backlight-only pass to accept kernel or system-suspend wake.
