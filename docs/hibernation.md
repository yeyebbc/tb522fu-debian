# Disk hibernation

Protected firmware reboot trials have restored the saved Linux memory image.
UFS I/O, Wi-Fi and display recovery remain unreliable after the old kernel
returns. Use the GNOME backlight-only Suspend action during driver work and
keep the actual sleep targets masked.

The dedicated partition is installed. The 244 GiB Debian root passed full
offline checks before and after shrinking. Both GPT copies and the 12 GiB
swap header were verified. Swap is active and the empty-target boot path
works. Android and the other Linux trial roots were preserved.

## CI102 protected firmware restore

- Review of the CI101 in-place restore logs found 57 abnormal UFS completion
  queue entries and a UFS DMA translation fault. Temporarily selecting system
  PM level 5 on CI101 eliminated those errors in a read-only in-place resume.
  Direct I/O confirmed the root superblock and consumed swap signature.
- CI102 makes the link-off policy reproducible and enlarges the kernel log to
  4 MiB. Both kernel profiles built in workflow 44245979484. The installed
  build passed the cold-boot checks and the image-free `core` test.
- A firmware reboot returned the original boot ID and completed the saved
  hibernation syscall. A RAM-based logger exported the kernel log over USB.
  The first recorded post-restore timeout was a CPU SCMI reply. The PCIe host
  then failed to find the Wi-Fi endpoint. UFS retried UIC link startup and
  returned `-ETIMEDOUT`. DSI command DMA, GPI and Bluetooth also timed out.
  The filesystem and its block device were read-only throughout the trial.
- The timed recovery booted CI102 again. A direct read confirmed the empty
  swap header, a synced write to the root filesystem passed, and both boot
  images matched their expected hashes.

## CI103 interrupt controller restore

Patch 0244 imports Zhu Ling's proposed GICv3 SPI context patch without
functional changes. It saves SPI and ESPI enable, trigger, priority and
routing attributes in the hibernation image and restores them before device
callbacks. The upstream author reports real S4 testing on Phytium E2000Q.
[GICv3 patch v2](https://lore.kernel.org/all/20261024144720.113165-2-zhuling2709@phytium.com.cn/)

Both CI103 kernel profiles built in workflow 44250011415. The installed
kernel passed a cold boot and image-free control with the original
configuration and device tree. The firmware restart restored the original
boot ID and ran the GIC restore callback. The CPU SCMI timeout from CI102
was absent. UFS again logged 20 UIC command timeouts across five failed
host reinitialization attempts. The Wi-Fi endpoint and DSI DMA failed as
before. The diagnostic left the root mount and block device read-only.

## CI104 UFS diagnostics

Patch 0245 reads the host status, interrupt status, command result and IRQ
controller state on an SM8750 UIC link-startup timeout during a UFS power
transition. These samples can distinguish a missing hardware command
completion from a completion that did not reach the handler. The patch
keeps the existing timeout, error handling, power policy and retry sequence.
Both profiles built in workflow 44252518751. The image-free control completed
without a link or queue failure.

In the protected firmware restore, all 20 timeouts had interrupt status
`0x4` (UIC error) and lacked the `0x400` command-completion bit. Host
control remained enabled and host status read zero. The IRQ was unmasked
and pending. The controller reported a link error before reporting
command completion. The sample did not identify which link component failed.
Wi-Fi and DSI still failed. The logger delivered the report before the
early recovery reboot. The fresh boot passed direct swap reads and a
synced root write.

## CI105 pin controller restore

Patch 0246 adapts Birk Skyum's pin controller context save and restore.
The firmware restart can leave GPIOs in a different configuration from
what the restored drivers expect. The diagnostics have a UFS link error
and missing PCIe endpoint, so restore the SM8750 pin settings that Linux
owns, including the UFS reset pad and the pin mux for PCIe. The board
opts into hibernation callbacks. [Qualcomm pin controller patch v4](https://lists.openwall.net/linux-kernel/2026/10/21/2649)

Both CI105 profiles built in workflow 44254725551. The cold boot and
read-only image-free control passed. Its protected firmware test restored
the original memory and again reported 20 link-startup timeouts with UIC
error and no completion. The PCIe Wi-Fi endpoint and DSI DMA also failed.
The USB logger saved the report before automatic recovery. The next boot
passed a synced root write, a direct read of the empty swap header and
verification of both boot image hashes.

## CI106 UFS queue comparison

The earlier CI101 host dump showed capability register `0xd5c7033f`.
It advertises MCQ, and the legacy single-doorbell removal bit is clear.
Patch 0247 selects single doorbell and Hibern8 system sleep when both
modes are supported on this board. The queue mode is chosen before DMA
allocation and applies to the saved and loading kernels. The standard
restore callback programs the saved legacy request-list addresses. Verify
the queue selection and clean direct storage reads before using a writable
root. Other restored drivers still require hardware verification.

CI106 built both profiles in workflow 44258332289. The installed image
booted with one UFS hardware queue, all 39 supported modules, native Adreno
rendering and Bluetooth. The protected image-free test passed direct reads
of the root and swap. The firmware restore returned the original boot and
logged no link-startup timeout or abnormal MCQ completions. A later UIC
Hibern8 exit timed out, and the restored system did not serve an SSH
banner. The timed recovery returned to a healthy cold boot.

A separate protected test held only the UFS host and device WLUN active
for runtime PM. It also restored the original memory. The UIC Hibern8
exit and subsequent link startup failed, and the RAM logger recorded
`EIO` from direct reads of both root and swap. The report arrived before
automatic recovery. A fresh boot verified the original runtime settings,
an empty swap header, a synced root write and both boot image hashes.

## CI107 active UFS link comparison

Patch 0248 keeps the legacy queue selected by patch 0247. It chooses UFS
level 0 for both runtime and system PM and leaves the automatic Hibern8
timer at zero for the matching Lenovo controller. This uses the existing
clock-gating path with the device and link active. It tests whether the
explicit or automatic Hibern8 transition accounts for the timeout. Verify
the reported policy and hardware timer before testing. Treat its idle
power behaviour as experimental and keep the working backlight action.


CI107 built in [workflow 44264599202](https://github.com/yeyebbc/tb522fu-debian/actions/runs/44264599202).
The cold boot showed a Debian greeter and answered USB pings. Selecting the
account did not open its password field. The operator switched to a text
console and observed `I/O error, dev sda`. USB SSH also closed before
authentication. This comparison ended at cold boot before any snapshot.

The last CI106 repeat with default runtime PM restored its USB connection
after firmware startup. Both the RAM logger and timed recovery stopped
without reporting, and the operator restarted the tablet. A subsequent
check confirmed a writable root, empty swap and both expected boot hashes.
That run did not establish whether the old kernel completed restore.

## Factory UFS power sequencing

The TB522FU factory Linux 6.6.102 image enables `CONFIG_HIBERNATION`. Its
vendor boot ramdisk contains the Qualcomm UFS host and Sun QMP PHY modules.
The stock host delegates the freeze and restore calls to the UFS core. The
[published downstream UFS core](https://github.com/lenovo-basements/android_kernel_lenovo_sm8750/blob/210981a0ad749c30080b853d31bc009d9db0592d/drivers/ufs/core/ufshcd.c)
and our mainline core both rewrite the legacy transfer and task DMA list
addresses after host resume. The kernel configuration establishes capability
only. Android's use of disk hibernation remains unverified.

The factory device tree binds the UFS device reference-clock pad supply to
PMIC i LDO2 at 1.2 V. Its UFS host module has regulator operations before
lane-clock enable. The code enables that rail at probe and leaves it on
through Hibern8. The factory `vccq-parent` vote is PMIC i SMPS7. Mainline
already describes SMPS7 as the parent of the VCCQ regulator, and it was
active in the CI106 regulator summary. Mainline's QMP PLL and analog PHY
regulators are on different rails from the LDO2 pad supply. The factory tree
also sets `qcom,bypass-pbl-rst-wa` for this host.
[Downstream UFS host source](https://github.com/lenovo-basements/android_kernel_lenovo_sm8750/blob/210981a0ad749c30080b853d31bc009d9db0592d/drivers/ufs/host/ufs-qcom.c)

Patch 0249 resumes testing from the CI106 storage policy and adds just the
LDO2 vote to the board device tree. The loading kernel applies the nominal
1.2 V constraint before reading a snapshot. Verify the regulator state,
cold storage, the image-free control, and a protected reboot-mode restore
before changing the normal boot or sleep policy. Save the hibernation return
log before issuing the post-restore direct reads.

The missing UFS rail is a specific storage lead. PCIe and DSI also lose
hardware state after firmware restart. A recent Qualcomm clock RFC explains
how cached rates can diverge from hardware after hibernation. It tests a
Glymur display controller and does not establish the SM8750 failure cause.
[Qualcomm clock restore RFC](https://lists.openwall.net/linux-kernel/2026/10/28/880)


## CI108 read-only firmware result

Both [CI108 builds](https://github.com/yeyebbc/tb522fu-debian/actions/runs/44271797556)
passed archive verification and the independently replayed DTB comparison.
The maintenance profile reported LDO2 enabled at 1.2 V and completed six
identical direct reads of both partitions after UFS runtime suspend. All
storage stayed read-only and the maintenance return booted CI106 again.
CI108 then cold-booted normal Debian with all 39 supported modules, native
Adreno rendering, Bluetooth and successful graphical login.

The first protected firmware cycle produced no post-restore packet. Its
fresh boot passed both boot-image checks, empty swap and a synced root write.
The second test added USB serial capture and recorded the old boot ID,
a successful hibernation syscall return and the kernel's image-restore
confirmation. UIC command `0x18` (`DME_HIBER_EXIT`) timed out, followed by
four link-start timeouts. Direct reads from both Linux partitions returned
`EIO`. PCIe Wi-Fi and DSI command DMA also failed. The monitor received both
complete reports, and automatic recovery returned to a verified fresh CI108
boot. This establishes that the UFS pad supply vote alone is insufficient.

The factory QMP PHY also uses PMIC i LDO3 for `vdda-qref` and PMIC f LDO1 for
`vdda-refgen`. The stock PHY powers those circuits before enabling its
reference clocks. The Lenovo mainline DT already describes both regulators.
The series 0250–0252 adds these optional SM8750 PHY consumers to the existing
bulk power operations, with the factory load requests and the current board
voltage ranges. LDO3 is shared with the display PHYs, and LDO1 is shared with
the PCIe PHY. The next comparison checks the rail votes and read-only storage
before attempting another firmware restore.
[Downstream Qualcomm UFS PHY source](https://github.com/lenovo-basements/android_kernel_lenovo_sm8750/blob/210981a0ad749c30080b853d31bc009d9db0592d/drivers/phy/qualcomm/phy-qcom-ufs.c)

## CI109 PHY supplies and CI111 symbol clocks

Both [CI109 profiles](https://github.com/yeyebbc/tb522fu-debian/actions/runs/44278125002)
built successfully. The maintenance boot confirmed active QREF and REFGEN
consumers and matched six direct-read pairs after UFS runtime suspend.
The normal installation booted the graphical desktop with all 39 supported
modules, native Adreno rendering and Bluetooth. An image-free control
returned all eight CPUs and matched both direct reads.

The protected firmware reboot restored the original boot ID. UIC Hibern8
exit and four link-start attempts timed out. Both direct reads returned
`EIO`. PCIe Wi-Fi and DSI DMA also failed. USB serial and Ethernet each
retained the full report. The automatic recovery verified a synced root
write, an empty swap header and both boot image hashes on a fresh CI109
boot. The extra PHY supply votes alone were insufficient for firmware resume.

The shipped driver selects the XO reference for RX0, RX1 and TX0 when
entering Hibern8 and selects the PHY again on exit. Patch 0253 applies
Qualcomm's proposed Glymur clock sequence to the existing SM8750 muxes.
The clock controller selects the PHY when the lane clocks are enabled
and parks the muxes at XO when they are disabled.
[Qualcomm Glymur clock patch](https://lore.kernel.org/linux-clk/20260915-glymur-ufs-clk-changes-v2-2-d0aa1c60c269@oss.qualcomm.com/)

Read-only CI109 samples uncovered a second issue. All three branch clock
enable counts increased from 55 to 60 across six runtime-suspended samples.
The Hibern8 prepare callback and device-resume callback both enable the
same clocks, while suspend releases one reference. Patch 0254 uses the
existing driver flag to skip a duplicate enable. CI110 built both profiles
with the mux change. The clock reference evidence made CI111 with both
patches the next hardware test. Check the muxes and branch enable counts
alongside repeated direct reads in maintenance before firmware restore.
[CI110 build](https://github.com/yeyebbc/tb522fu-debian/actions/runs/44282410275)

## CI101 restore results

- An actual `test_resume` image returned the original boot ID and RAM-only
  marker. Its swap header acquired image metadata and returned to its empty
  signature. With all 39 supported modules and PCIe wake enabled, the restored
  session rendered fresh Adreno frames and passed Wi-Fi gateway traffic. The
  later UFS log review found hardware errors during that same cycle.
- A separate `disk=reboot` test showed the firmware bootloader and returned
  the same boot ID and RAM marker over USB. The root filesystem went into
  ext4 emergency read-only mode after UFS I/O errors. Direct swap reads returned
  `EIO`. GMU clock errors, GPU lockups and a black physical display followed.
  The repeating GPU errors displaced the earliest restore messages from the
  kernel ring before collection. The initial UFS failure remains undetermined.
- A hardware restart returned to ordinary CI101 Debian. Direct reads confirmed
  the consumed swap signature, the selected boot and Android init_boot hashes
  matched, and an fsynced root write passed. The partition split is unchanged.

Use a read-only root and a RAM-based logger before repeating the failing
reboot. Require clean storage reads after restoration before running a test
with a writable root. Continue to require a physical display and native
rendering check before power-off testing or enabling the GNOME hibernation action.

The protected CI101 retry remounted ext4 read-only and made its block device
read-only before entering hibernation. USB returned, but neither the volatile
logger nor the timed recovery delivered a result. A hardware restart returned
to a writable root with the swap signature consumed. The protected retry did
not identify the first failing callback.

Patch 0243 is an SM8750 diagnostic. The cold boot configures nine UFS hardware
queues and uses system sleep level 3 (sleep/Hibern8). The core's normal
hibernation restore rewrites the legacy DMA queue addresses. The diagnostic
uses the existing level 5 path to power down the link, so resume takes the
host and device reinitialization path that configures the hardware queues.
Runtime UFS power management and other Qualcomm hosts retain their prior
policy. The installed build also keeps a 4 MiB kernel log for early restore
errors. Validate this candidate before attributing the failure to the link
or the queues.

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
test. Both CI101 kernel profiles built in workflow 44241035598. The actual
image and firmware-reboot tests are recorded above.

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
Real shutdown-mode wake and correct operation of all restored devices remain
unverified.

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
