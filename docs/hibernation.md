# Disk hibernation preparation

The next requested test is actual software hibernation: write a memory snapshot
to storage, power off/reboot, then restore it. The working GNOME backlight-only
Suspend action is the rollback policy. It does not enter a CPU sleep state.
No successful hibernation test is claimed yet.

The dedicated partition is now installed and Debian 13.7 boots CI100 with all
39 supported modules and the retained Adreno/Mesa desktop. The filesystem
passed full offline checks before and after shrinking; both GPT copies and
the swap header were verified. Swap is active and the empty-target boot path
works. Android and the other Linux trial roots were preserved.

The first normal logind reboot-mode request on CI98 caused a fresh boot,
not a restored session. The prior boot ID and RAM-only cookie did not return,
there is no post-restore receipt, and the swap header remains byte-identical
to its initial empty header. The retained journal stops at hibernation entry;
this does not identify the resetting component. No real snapshot restore or
shutdown-mode test has passed. The normal menu remains backlight-only and
sleep/hibernate/suspend targets are masked again.

Incremental, image-free kernel diagnostics then returned in the same boot:
`freezer`, `devices`, and `processors`. The first two also passed fresh Adreno
rendering checks. The processors test returned with `qdss already disabled`
and `qdss already unprepared` warnings through `amba_pm_runtime_suspend()`;
it is not a clean acceptance. Kernel test-mode messages saying an image was
restored are not proof of a real restore: this path creates no image.

CI99 imports Rafael Wysocki's
[maintainer review attachment](https://lore.kernel.org/all/CAJZ5v0g3zU51Q4sQvmTNH-Jtycu1D5Qm9c6r2t_DCp03ePzV-g@mail.gmail.com/)
for the matching runtime-clock accounting issue. It excludes devices with
runtime PM callbacks from automatic callback-free smart-suspend eligibility.
The initial proposed `device_resume_noirq()` exception was not imported because
the maintainer identified an unsafe parent/child case. CI99 did not carry the
separate wake IRQ patch. All previous 117 patches remain
identical; this adds only three PM-core files, with no board/driver/voltage
changes. The earlier reset remains unexplained until native evidence says more.

CI99's matching all-driver processors test returns in the same boot without
the AMBA/qdss clock warnings, and fresh Adreno rendering passes. The next,
`core` diagnostic reaches the CPU/IRQ-off system-device stage and returns,
but its Wi-Fi PCIe link is inaccessible during restore. MHI initialization
fails, followed by ath12k/mac80211 restore warnings; this is a failed diagnostic
despite a clear physical desktop and a later NetworkManager connected state.
A clean reboot returns Wi-Fi to its baseline. No disk image was created by
either diagnostic and the GNOME hibernation action stays disabled.

CI100 adds the upstream
[Qualcomm PCIe hibernation freeze callback](https://lore.kernel.org/all/179181074907.22199.10556821368232442334@pm.me/)
and its required [complete PME bus walk](https://lore.kernel.org/all/20261114-shutdown-v9-1-5430c9f242ed@oss.qualcomm.com/)
and [explicit forced L2 API](https://lore.kernel.org/all/20261114-shutdown-v9-2-5430c9f242ed@oss.qualcomm.com/).
Hibernation must record a powered-down controller because the restoring kernel
may not have initialized it. Ordinary suspend and the final poweroff callbacks
retain their existing D3cold policy. The forced path still collects every
endpoint's PME capability so it preserves required auxiliary wake power.

Patches0239–0241 retain author attribution. The freeze change has identical
added/removed lines to v2; only context changes. The force API is adapted to
this older base, which has no `suspend_poweroff` field or R-Car caller. The
unrelated shutdown callback and MSI changes are omitted. All previous118 patches
are unchanged;121 patches pin tree461f3577347c11567d0f57f047710e2a35a2fbe1.
Six local cases compile the actual bus-walk/DWC functions to check ordinary
suspend, forced freeze, PME preservation and shutdown errors; the original
early-exit callback fails the late-PME-device case. Both CI profiles built.
The native core diagnostic, fresh GPU pixels and actual Wi-Fi gateway
traffic passed with all 39 supported modules loaded.

CI100's real `test_resume` diagnostic wrote and read about 3.4 GiB, then
failed restore with `EBUSY`. The preceding freeze had recorded a wake event
from the Wi-Fi root port's dedicated PCIe wake IRQ. A buffered userspace
write retried the sysfs action during close, so the original trace contains
two image attempts. The corrected diagnostic writes once even on error.
With only that port's wake setting temporarily disabled, the next attempt
left written image metadata and a consumed signature on swap, then started
a fresh boot. The saved session and RAM cookie did not return. This places
the reset after creation and the start of image handling. It does not
identify the failing restore phase.

Patch 0242 imports Abel Vesa's
[proposed wake IRQ fix](https://lore.kernel.org/all/20261102-b4-pm-sleep-hibernation-fixes-v1-2-51fac96d080d@oss.qualcomm.com/)
without functional changes. It skips arming device wake IRQs for freeze and
quiesce and balances the matching disarm on completion or failure.
The [placement remains under review](https://lists.openwall.net/linux-kernel/2026/11/12/2535).
The actual PM functions are tested for both phases, ordinary suspend, final
hibernation poweroff and failure unwind. The prior code fails the freeze
test. The tablet still needs an image restore test with the new kernel.

The runtime preflight reads the swap header with aligned direct I/O. Kernel
snapshot writes bypass the block page cache, so a buffered read can report
an older empty header. The setup path issues one unbuffered write for each
sysfs action and refuses short writes.

The user authorizes repartitioning Debian and explicitly chooses **12 GiB swap**.
The applied split is 244 GiB ext4 plus 12 GiB dedicated Linux swap, inside the
existing 256 GiB Linux allocation. Android partitions must remain byte-identical.
Root start and PARTUUID are retained. The filesystem must be checked and shrunk
offline before its GPT end is reduced. Both live GPT copies, CRCs, bounds,
unchanged entries and filesystem size are verified around the transaction.

The installed kernel enables ARM64 hibernation and LZO. The initial resume
build retained the device tree, drivers and graphics stack. It required a
rebuild because the forced embedded initramfs previously
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

The dedicated244+12GiB split is now applied. Both GPT copies and the swap header
were read back, Android re-enumerated both partitions, and the244GiB filesystem
passed an offline full check. The original early helper incorrectly required
equal disk/partition major numbers; native Android uses8:0 for the disk and
259:2 for swap. Source136b04b removes that false condition while preserving the
validated sysfs parent relationship. CI97 was retired before any Linux boot;
CI98 rebuilds the same driver/kernel tree with the corrected embedded helper.

The runtime preflight checks the private selected image, kernel, partition and
swap identities, empty header, active swap, resume device and free-space budget.
Its setup mode configures only an EMPTY target; it must never attempt a late
restore after root is mounted. The prepared systemd drop-ins prohibit RAM,
hybrid and suspend-then-hibernate modes. Reboot is the initial test mode; change
to shutdown only after a verified restore. Startup return protection must be
retired before creating a snapshot.

`hibernate-sleep@tb522fu.local` is a separately selectable GNOME48 action and is
staged disabled. It requires a root-owned acceptance marker and uses logind's
normal Hibernate authorization/PrepareForSleep/inhibitor protocol. It never
falls back to RAM suspend. Keep the tested backlight extension installed and
enable only one of the two actions. An actual power-off hibernation normally
needs the Power button to boot and restore; Space wake is not promised.

Upstream references: [software suspend and early resume](https://docs.kernel.org/power/swsusp.html),
[hibernation debugging and reboot mode](https://docs.kernel.org/power/basic-pm-debugging.html).
