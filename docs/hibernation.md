# Disk hibernation preparation

The next requested test is actual software hibernation: write a memory snapshot
to storage, power off/reboot, then restore it. The working GNOME backlight-only
Suspend action is the rollback policy. It does not enter a CPU sleep state.
No successful hibernation test is claimed yet.

The user authorizes repartitioning Debian and explicitly chooses **12 GiB swap**.
The planned split is 244 GiB ext4 plus 12 GiB dedicated Linux swap, inside the
existing 256 GiB Linux allocation. Android partitions must remain byte-identical.
Root start and PARTUUID are retained. The filesystem must be checked and shrunk
offline before its GPT end is reduced. Both live GPT copies, CRCs, bounds,
unchanged entries and filesystem size are verified around the transaction.

The current kernel already enables ARM64 hibernation and LZO. This candidate
retains the same kernel source, device tree, 117 patches, drivers and graphics
stack. A rebuild is required because the forced embedded initramfs previously
checked and mounted ext4 before providing any resume support.

`configs/disk-root-prepare` admits only the original 256 GiB layout or the exact
244+12 GiB layout. In the latter it locates a unique adjacent `debian-swap`
partition on the same UFS LUN and calls the static `tb522fu-resume` helper before
ANY filesystem mount, including read-only mounts. No private UUID or per-device
boot argument is sent to CI. The helper validates swap size/version/header and
restores only a recognized hibernation image. A restore that returns to the new
kernel is fatal, even if the sysfs write reported success; it must not continue
to fsck or mount. Bounded disk-test kernels inspect and refuse a pending image
instead of trying to restore an image from a different kernel.

The explicit `maintenance` root environment is restricted to the bounded
disk-test profile. It exposes the existing read-only USB maintenance channel
without mounting even a healthy root. It includes e2fsck, resize2fs and mkswap;
partitioning and formatting remain manual, separately guarded transactions.

Before a real snapshot, verify ordinary no-image startup with the new initramfs,
matching modules, usable swap, early resume selection, local logs and independent
image-aware recovery. Recovery must inspect or explicitly discard a saved image
before any root mount/check; old generic cleanup scripts are unsafe while an
image is pending. The older CI96 image intentionally rejects the smaller root;
returning to that old image requires removing swap and restoring the original
root geometry first. The backlight-only GNOME policy works independently of
that kernel rollback and must remain available on the new kernel.

Start with reboot-mode hibernation so a complete firmware boot/restore can be
observed automatically. A restored session, physical display, input, hardware
rendering and retained logs are required before changing the menu action or
testing power-off hibernation. The 12 GiB target needs a free-space check before
each request; RAM size alone does not guarantee a sufficiently free swap area.
Actual kernel freeze/thaw and restore callbacks remain unverified.

Upstream references: [software suspend and early resume](https://docs.kernel.org/power/swsusp.html),
[hibernation debugging and reboot mode](https://docs.kernel.org/power/basic-pm-debugging.html).
