# Debian 13 on Lenovo TB522FU

Experimental native Linux port for the Lenovo Legion Y900 13 / TB522FU
(SM8750, Snapdragon 8 Elite). Debian 13 ARM64 with GNOME is installed on a
256 GiB partition on one test tablet, with Android preserved and on-device switching verified in both
directions. This remains a development port with substantial peripheral work
outstanding.

Current installed kernel: `7.3.0-tb522fu-installed-ci44`, built from recipe
`0a1847dd0b67991af502bfea9da36c5db50be3c4`. The installed image SHA256 is
`02adcbeb01e7742b3999a6ac5d2082cee3d10ad8c1a780612acd84c3f3d6468e`.
CI39 and CI32 remain available for rollback. Android return, stock boot and
filesystem checks passed; the temporary acceptance timer has been removed.

Native graphics candidates CI46 and CI47 are rejected for installation.
Initial rendering works, but the panel remains grey after wake with CTL reset,
frame and vblank timeouts. The split-slave timing-mux disconnect and unchanged
[upstream encoder shutdown ordering](https://github.com/torvalds/linux/commit/32d04280ddebb6eb964990931b0f1001f63b35e7)
are insufficient on this tablet. Do not repeat these candidates unchanged.

CI48 added 14 scoped diagnostic callsites. Both controller cleanup resets
completed successfully before display runtime suspend. The first observed stuck
reset came after runtime resume and a fresh GNOME frame request. The physical
panel stayed grey. The existing display fault snapshot was captured, and debug
flags were restored. This narrows the failure boundary but does not establish a
root cause: the hardware can initiate controller resets too. Android, exact
graphics rollback and filesystem checks passed; CI44 remains installed.

The current candidate imports the original three-patch
[VBIF AXI halt sequence](https://github.com/TheMojoMan/oneplus-erhai-linux-old/commit/8bb2fed028a210cc2fca2eee3b4560e6e78f9f07)
from the same-SoC community port, with original attribution and unchanged code
patch IDs. It halts the display bus before runtime power collapse and releases
it on resume, enabled only for SM8750. Its register sequence and bounded polling
match Lenovo's stock display driver. The 93-patch stack replays exactly, eight
ARM64 objects compile, and 12 recipe tests pass. CI48's diagnostic patch is
excluded. Hardware testing rejects CI49 before the wake cycle: startup shows
patterned display corruption, DSI FIFO-class errors, a panel-initialization DMA
timeout and controller reset failures. SSH eventually becomes available, and
GPU pixel tests pass, but the physical display fails. No DPMS test is attempted.
Android, exact graphics rollback and filesystem checks are restored; CI44 stays
installed. Do not install or repeat the unchanged CI49 candidate. The next source
audit examines initialization and shared display-bus power ownership; no specific
cause is yet established. The code-only style check passes; original commit
messages retain their missing author signoffs and nonstandard co-author tags,
rather than inventing certifications for their authors.

The current CI50 source adds eight early logging sites around the existing
VBIF halt/release and DPU runtime callbacks. It records clock-control state,
halt request/status, acknowledgement versus idle fallback, and whether DRM
registration has occurred. It is diagnostic only and is active before userspace
can connect. No register writes, votes, retries or delays are added, but readbacks
and logging can affect ordering/timing. Do not install or treat this as a fix.

CI50 diagnostic capture succeeded, but wake is rejected. It reached a visible
GNOME greeter, then became grey after one display power cycle and reported
CTL reset/frame/vblank errors. Startup halt requests received acknowledgements;
screen-off polling timed out with idle status and the existing fallback returned
success. That distinction is not proof of the root cause. Android, the graphics
configuration and filesystem checks were restored; CI44 remains installed.

CI51 is an experimental protocol test based on Lenovo's pinned stock driver:
assert the display QACTIVE override before the bus halt, then restore its prior
value after release. The SM8750 register address is checked against both device
tree mappings, with runtime bounds checking. Existing logging remains active;
acknowledgement and physical wake must be checked separately. No clock rates,
voltages, OPPs or polling deadlines change. Keep CI44 installed; this is not an
accepted production fix or a full CESTA integration.

CI51 completed one recorded wake cycle. All three bus halts received real
acknowledgements, and the saved QACTIVE value was restored each time. No matched
DSI/controller/frame/vblank fault recurred, and fresh GNOME GPU rendering passed.
However, the physical panel remained grey after wake throughout the fresh-frame
probes. **Wake is rejected**; software success is not physical display acceptance.
Android, exact graphics rollback and filesystem checks passed; CI44 remains
installed. Do not install or repeat CI51 unchanged. The next audit targets panel,
dual-DSI and DSC output lifecycle; the remaining failure's cause is not established.

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

CI53 adds nine scoped dynamic-debug callsites for panel wake and backlight
output. They record existing callback results, effective brightness/blanking
state, and existing writes to both backlight chips. They are disabled by default;
no new register reads, writes, retries, delays or power policy are introduced.
Successful transport is not proof of LED light or panel output. The 97-patch
recipe remains diagnostic only. A bounded test must enable only these formats,
restore their flags, review Pixel 6 footage and preserve CI44/Android/graphics.

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

CI54 stopped at its configuration guard before compilation: making the class
core built-in exposed an inherited built-in chip-driver setting. No image was
produced or tested. CI55 explicitly keeps KTZ8866 modular; a fresh configuration
merge passes all 95 recipe setting checks. The only functional change from CI53
is the built-in backlight class core. Source and diagnostic scope are unchanged;
physical wake acceptance is still pending.

CI55 now passes the backlight-control check but still fails physical wake.
The compiled panel imports the real backlight helper. During one off/on cycle,
both backlight chips receive zero brightness/disable and then the requested
positive brightness/enable, with successful transport returns. The user sees
the backlight on without an image; camera footage confirms a visible greeter
before the cycle and blank output afterward, including fresh focus updates.
No matched display-controller fault recurs. Android, exact graphics rollback,
filesystem checks and cleanup pass. CI44 remains installed; do not install or
repeat CI55 unchanged. The next audit targets panel/video restart, not additional
backlight writes. Software rendering success remains separate from physical wake.

The next candidate preserves the stock BOE DVT2 setup packet types. All 32
command payloads and delays match stock, but the generic helper encoded 23
two-byte vendor commands as short writes (0x15), whereas stock uses long writes
(0x39). A board-specific helper retains long packets for the 30 vendor commands;
sleep-out/display-on remain standard short commands. Other panels, shutdown,
PPS/compression, reset pins and supplies are unchanged. This is a verified
protocol mismatch, not yet a verified wake fix. The actual C sequence passes a
host test of all packets, LP/HS flags, channel handling, 64 injected transfer
failures and early exits. CI runs that contract check against the patched source.
The 98-patch stack reproduces the pinned tree. Keep CI44 installed while the
diagnostic candidate undergoes its bounded camera-recorded wake test.

CI56's bounded test also rejects physical wake. Initial GNOME is visible, but
the image stays blank after wake; the user confirms the backlight is on.
Panel setup/PPS, both backlight chips and software rendering return success
without matched display-controller faults. The long-packet correction alone
is insufficient. Android, exact graphics rollback, filesystem and cleanup
checks passed; CI44 remains installed. Do not repeat or install CI56 unchanged.
Next work compares display-link and compression state at startup versus wake.

The next image is diagnostic only. Seven new log sites compare DSI timing,
each link's first video start, clock/lane/control readbacks, the panel PPS
fingerprint and DPU compression resources. Ten existing control/status/timing
registers are read only at a first video start with the host powered and enabled;
no IRQ/FIFO flags or arbitrary addresses are read. An execution test of the actual
old/new start functions checks all 16 state combinations and confirms identical
writes and runtime state. The added reads/logging can affect timing, so a changed
screen result would require further verification. No hardware sequence changes
are included, and CI44 remains installed. The 99-patch source reproduces its
pinned tree; affected ARM64 objects, packet contracts and 12 recipe tests pass.

CI45 verified the secondary rear OV02B10's full sensor ID and two8-frame RAW10
capture cycles through SM8750 CAMSS, with clean Android restoration. Frames were
nearly black. An isolated Debian libcamera 0.7.1 CPU software-ISP test subsequently
captured 90+8 RGB888 frames in two stream cycles. Scene detail is visible, but
images remain dark and purple-tinted; color, exposure, timing metadata and normal
camera applications remain unaccepted. The other three sensors remain disabled. All six camera
modules stay blocked from automatic startup for further bounded testing.
No firmware, proprietary camera libraries, stock dumps, images or calibration data
are distributed.

Automatic keyboard/trackpad startup, US Wi-Fi regulation, 5 GHz association and
LAN transfers have passed on this unit. The six-speaker path and two WCD939x
analog microphones are working and accepted by the owner. Microphone capture
defaults to +12 dB digital gain. Audio was not retested in the latest update at
the owner's request; earlier desktop acoustic automation remains incomplete.

CI44 adds [white keyboard lighting](configs/keyboard/README.md) through the
standard `lenovo:white:kbd_backlight` LED interface. It exposes only off/on,
with white enabled by default. Camera recordings of bounded and normal installed
boots show three successful off/on cycles and visible GNOME. Both attempted
dimming mappings produced indistinguishable nonzero levels, so dimming is not
advertised. Physical Fn+Space, typing after this transport update and suspend
remain unverified. The accepted input decoder and reconnect delay are unchanged.

[Bluetooth automatic address provisioning](configs/bluetooth/README.md), fresh
discovery, idle HCI responses and quick off/on passed through both boot paths.
The installed test received 19 fresh MGMT discovery packets from 11 nearby peers,
reopened after a 0.500-second powered-off interval, then received an actual HCI
response after idle. Both host IBS states reset to asleep; Wi-Fi association
and 5/5 gateway pings passed, with no relevant driver errors. CI44 carries the
unchanged [upstream power-off IBS reset](https://lore.kernel.org/r/20261014180201.57109-1-birk.skyum@pm.me)
after a later CI42 test exposed an intermittent second-setup firmware timeout.
Pairing, peripheral traffic/reconnection and Bluetooth suspend remain untested.
Startup takes about 65 seconds and power reopening about 32–34 seconds; download
pacing and the second setup for public-address provisioning are unchanged.

The controller implementation retains GEEKiDoS's TB322FC provenance and the IBS
fix retains Birk Skyum/Vladyslav Tymoshchuk attribution in `patches/sources.json`.
Private firmware, calibration and the tablet's stock address are required
separately; none are distributed here. Wi-Fi-only US settings do not change
Bluetooth calibration or the user's system locale.

The CI35 bounded GPU test passed native display, Adreno 830 hardware pixel
readback for210seconds, rejection of a forced software renderer, and actual
GNOME compositor GPU activity. The Mesa26.1.6 device-table backport is pinned
in`configs/graphics/source.json`. CI36 additionally passed normal display/GPU
autoload, hardware GTK OpenGL/Vulkan rendering and GPU runtime suspend/resume,
but the panel stays black after DPMS wake with DSI/CTL errors. CI36 is rejected
for production until display wake is fixed. FastRPC remains staged. Matching userspace must
retire the old display/touch blacklist and manual touch unit, then select the
isolated Mesa library directory through ld.so.conf.d. Distribution packages and
the accepted CI32 rollback remain intact. Native display/touch power transitions and installed cold boot
remain outstanding; this is not a release.

CI37 changes only bonded DSI host shutdown order: slave before master,
matching Lenovo's display clock driver. This removes the first slave-clock
shutdown warnings, but visible wake still fails with a blank grey panel.
A follow-up test clears GNOME's screen shield and requests fresh UI activity;
the shield is inactive but DPU CTL reset, frame and vblank timeouts appear.
CI37 is rejected for promotion; installed CI44 retains the accepted framebuffer display baseline. The remaining display
resume failure needs a separate fix.
No RAM reservation, audio, panel timing or voltage changes are included.

A separate manual workflow builds a [CPU-label backport](configs/cpu-label/README.md)
for GNOME's blank ARM processor field. It uses the existing Ubuntu libgtop
patch with Debian packaging. It is installed on the test tablet; libgtop now
returns Oryon for all eight cores, matching lscpu. Original Debian packages
are saved for rollback. Visible GNOME System Details acceptance is pending.

GitHub Actions builds two kernel profiles on native ARM64 runners:

- `disk-test`: an embedded BusyBox maintenance/boot environment with matching
  modules, e2fsck and a900-second independent EDL return for host restoration.
- `installed`: the same device support with normal reboot semantics and no
  test timer. USB debugging is opt-in. Persistent GNOME boot and on-device
  Android/Linux switching have passed hardware tests on one tablet.

Both locate Debian by GPT label, verify its256GiB geometry and installation
marker, check ext4 and load the matching root. They never create partitions or
format filesystems automatically. Before installation, disk-test remains in a
read-only maintenance shell when the partition is absent or cannot be mounted
read-only. This also permits explicit installation onto a newly created, blank
partition. A mounted root with a wrong board marker, PARTUUID or module tree
is still rejected; the installed profile never falls back to a maintenance shell.
The blank-partition maintenance path and the first persistent installation
have passed hardware tests on one tablet.
The accepted CI39 installation still uses the firmware framebuffer;
the newer candidate enables native display and GPU as described above. A separate, optional workflow job builds
Debian13 GNOME from authenticated Debian archives. The original RAM-only
profile remains available with `scripts/build-kernel.py --profile ram`.

RAM Debian and the **physical GNOME welcome screen with correctly aligned
finger input** are verified on one TB522FU using recipe
`a4727557d10818f2872fdd4e9bd9e45a08e81e21` from
[CI run 43247675167](https://github.com/yeyebbc/tb522fu-debian/actions/runs/43247675167).
Linux `7.3.0-tb522fu-probe-ci11+` kept the display visible through normal
multimedia clock-driver loading, RPMh provider synchronization, GNOME startup
and touch firmware loading. The framebuffer holds MMCX at NOM_L1 (320),
matching the stock display driver's 575 MHz vote. Native touch X is inverted
before the axes are swapped; the user verified Next and Previous under the
finger. GNOME also works at 200% interface scale in this RAM session.

The prior ci10 control isolated the blackout to the final clock provider
allowing RPMh synchronization without a framebuffer power-domain consumer.
Both ci10 tests returned on the kernel timer and restored verified stock
Android. The explicit power vote fixes that failure in ci11 without a clock
module blacklist. GPI/SPI/touch loading remains manual during these probes.
Pen input and display/touch suspend lifecycle have not been tested.

Read-only UFS hardware validation passed with recipe
`20e462f1290cbe9f1824d96bfcc948a6c54d182c` from
[CI run43252153700](https://github.com/yeyebbc/tb522fu-debian/actions/runs/43252153700).
All six LUNs enumerated; both GPT copies matched stock identity and geometry.
Complete boot/recovery/init_boot reads matched their expected hashes, including
a successful recovery read after UFS runtime suspend. No UFS filesystem was
mounted or written. Timed EDL return, stock boot restoration and Android boot
all passed. The module name is `ufs_qcom`; explicit module names are now checked
against build outputs. Controller initialization can change UFS attributes.

The standalone maintenance profile also passed a cold boot with recipe
`4a19510f43ebc603a2225a595ce8017a553ea303` from
[CI run 43261296424](https://github.com/yeyebbc/tb522fu-debian/actions/runs/43261296424).
Its embedded modules enumerated and protected all six UFS LUNs. With no Debian
partition present, it stayed in maintenance mode; USB and the physical console
worked. On a64MiB RAM-backed ext4 image, native formatting, GNU tar copying
and e2fsck passed, preserving numeric owners, permissions, ACLs, extended
attributes, capabilities and links. All twelve GPT copies stayed byte-identical.
An explicit early EDL return restored verified stock Android. The900-second
fallback timer was armed; this test did not wait for it to expire.

The 256 GiB ext4 root has been created and populated on-device, with complete
file verification and a clean filesystem check. Android was reset for its
smaller userdata partition and booted successfully. The CI15 disk-test kernel
from recipe `f5c8b6a5db577e786602f591ee360ad90805884c` booted that persistent
root into a physically visible GNOME welcome screen. After the host-key unit
ordering fix in `1e7087a`, authenticated USB SSH and a clean systemd reboot
through host-assisted stock restoration passed. The CI16 installed profile
from recipe `66a17356b8ebec2679df3ec4a4e63511a2c8f803`, built in
[CI run 43363084665](https://github.com/yeyebbc/tb522fu-debian/actions/runs/43363084665),
then passed repeated Android → Debian → Android switching entirely on-device.
The Magisk Action verified and wrote the Linux boot image; the Linux helper
restored the Android image and shut down through systemd. Full image readbacks,
Android root preservation and a clean Debian ext4 filesystem were verified.
GNOME was physically visible, and the user verified Next and Previous directly
under their finger on the installed root. A separate debugging-off startup
reached GNOME with no configured USB gadget, no SSH listener and no failed
system units; its clean on-device return to Android also passed.

An unplugged shutdown and subsequent USB-triggered cold start reached visible
GNOME. Its debugging-off journal, clean Android return and filesystem state
were verified after replacing a USB cable. The battery-only attempt stopped
at the bootloader's Power-key confirmation screen, with no recorded Debian
boot; battery-only startup still needs that confirmation tested. Local account
setup is complete and the GNOME desktop is physically visible. GUI switching
remains pending.


The UART keyboard/trackpad driver now has initial hardware validation. With
CI18 recipe `0ecb61c`, real A/B/C and Shift+A input, pointer motion,
two-finger scrolling and clicks reached the standard Linux input stack.
GNOME recognized all three accessory input devices. Lid close/open reached
logind, and the user confirmed typing/trackpad recovery after attachment and
lid reopening, with an approximately five-second delay accepted by the owner.
No decoder errors were reported during the test. Keyboard LED transmission
and system suspend support are not included yet.

CI17 initially stopped before UART registration because the board lacked a
serial alias. CI18's explicit `serial0` alias fixed that failure. The build
checks the compiled alias. CI19 recipe `012bfc0` removes a spurious physical
right-button capability from the single-button clickpad. Its installed image
loaded the keyboard automatically, registered all three accessory input devices,
and received valid synchronization packets without decoder errors. The libinput
right-button warning is gone. GNOME was physically visible, and the temporary
acceptance timer returned cleanly to Android using the on-device switch helper.
The acceptance timer was then removed. Subsequent disk tests retain keyboard
automatic loading; the legacy RAM probe retains explicit loading.
The existing GNOME two-finger right-click preference is preserved.

CI20 recipe `4575d23` verified the first explicit ADSP load using privately
supplied stock firmware under `qcom/sm8750/lenovo/tb522fu/`. The 86 MiB image
and 512 KiB configuration regions match the stock runtime tree; firmware
hashes and split MDT bounds were checked locally. Proprietary files are never
published. GPR/FastRPC clients remain disabled.

ADSP reached running state and its charger service came up. Battery properties
changed from EAGAIN to 84%, 4.247 V and 22 degrees C, consistent with adjacent
stock Android readings. UPower reported no warning, and the physical screen's
red battery warning cleared. The test returned cleanly through EDL and stock
Android restoration. No direct charger registers or charging limits were written.

CI21 recipe `9c4937a` passed automatic ADSP startup in both bounded and
installed boots. Battery percentage, voltage, temperature and full-charge
capacity are available automatically; the installed boot reported 84% and
12.096 Ah full charge against 12.7 Ah design capacity. A physical USB unplug
and reconnect changed both the kernel power status and UPower correctly,
while ADSP remained running. Keyboard automatic loading and physical GNOME
also passed. The installed test returned cleanly to Android entirely on-device;
its temporary acceptance timer was then removed and the filesystem checked.

Current direction, USB voltage, runtime estimates and sustained net charging
remain unvalidated. A charging icon alone does not establish these. Further
charging refinements are deferred; brightness and ambient-light sensing are next.

The Wi-Fi candidate imports the Peach (`17cb:110e`) ath12k implementation from
[GEEKiDoS/linux](https://github.com/GEEKiDoS/linux/commit/b0c05eb72e10140f87efd0e499ad840e6c3e6975),
including TME-L patch loading, QDSS transfer, and firmware-directed PDC votes.
The original source attribution is retained; the import is limited to Wi-Fi
and its power-sequencing dependencies. Bluetooth was disabled in that early
Wi-Fi candidate; CI39 support is described above.
The board uses its own stock CNSS pinmux, supply ranges and PDC mappings.
The upstream Qualcomm PCIe IOMMU-map parser fix preserves normal DMA isolation.
The seven matching firmware files, including calibration, are supplied privately
from this tablet. CI22 built successfully but was not booted; this fuller
initialization sequence supersedes its candidate.

CI24 recipe `67b4301` passed the first bounded hardware test: PCIe trained at
8 GT/s with normal IOMMU isolation; board API 1, QDSS and all ten firmware PDC
entries were accepted. The owner connected through GNOME. The link used 5 GHz
at 80 MHz; DHCP, DNS and HTTPS worked, an 8 MiB download averaged 2.68 MB/s,
and twelve subsequent internet pings had no loss. No WLAN firmware crash or
SMMU context fault occurred. A clean early return restored Android, and the
filesystem check passed. This establishes initial networking, not sustained
performance or suspend support.

The next candidate enables Wi-Fi and keyboard coldplug in both disk profiles;
automatic Wi-Fi startup and address stability still need fresh-boot acceptance.
Install the distribution's `wireless-regdb` before that boot. The test initially
lacked this database and used the conservative world domain; country policy
and stock SAR behavior still need follow-up. The legacy RAM probe keeps manual
Wi-Fi loading.

CI15 also exposed a clock failure: fake-hwclock restored the saved date, then
the late PMIC RTC probe set system time to 1970. The configuration now disables
automatic RTC-to-system and system-to-RTC synchronization until the stock
RTC offset format is understood. Debian's existing fake-hwclock load/save
units remain responsible for the offline clock floor. CI16 disk-test and
installed boots verified that the saved date survives RTC probing without
host clock correction. This does not provide accurate elapsed time while
powered off or network time synchronization.

Native display/GPU, brightness, sustained charging, suspend and pen input
remain unverified under Linux. These artifacts
are development components, not an installer.

Own-kernel recovery images trigger a firmware CrashDump on the tested Lenovo
firmware. A standalone normal-boot entry test successfully returned to EDL,
followed by verified stock restoration and Android boot. The USB2 reference-
clock provider must be built into this module-free probe; the build checks
it and the required USB suppliers before building modules. The firmware text console includes a
bounded error-display pause.
Packaging and testing require the
owner's matching stock images and a prepared EDL restoration tool.
Firmware, device identifiers, partition dumps and keys
are not stored here or sent to CI.

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

## Build

Push a source/configuration change to `main`, or use **Actions → Build ARM64
artifacts → Run workflow**. Download `kernel-disk-test` and
`kernel-installed`. Enable `build_rootfs` only when rebuilding the Debian base;
that optional job produces `debian13-arm64-gnome`. Each contains SHA-256 checksums
and a source or package manifest. Artifacts expire after seven days.

The jobs use Debian 13 containers on `ubuntu-24.04-arm`. The kernel build uses
ccache. Root filesystem construction runs natively, avoiding QEMU overhead.
Workflow permissions are read-only; there is no deployment or flashing job.

To build the kernel locally on Debian 13 ARM64:

```sh
sudo apt-get install build-essential bc bison flex libssl-dev libelf-dev \
  ccache device-tree-compiler busybox-static cpio python3 git zstd kmod e2fsprogs
python3 scripts/build-kernel.py --profile disk-test
```

For an x86_64 Debian build host, also install `gcc-aarch64-linux-gnu` and
provide an ARM64 static BusyBox with `--busybox /path/to/arm64/busybox`
for the RAM profile. Disk profiles require native ARM64 for e2fsck libraries.
Build the root filesystem on ARM64 as root with:

```sh
apt-get install mmdebstrap debian-archive-keyring ca-certificates zstd
python3 scripts/build-rootfs.py
```

## Device userspace layer

`device/` contains the tested installation overlay: ordered touch loading,
200% GNOME scale, sleep disabled while power management is unverified, and
optional SSH restricted to the USB peer with public-key authentication.
The installer must supply this tablet's firmware, root PARTUUID and authorized
key privately. Debugging is off unless `/etc/tb522fu/usb-debug-enabled` exists.
Default SSH services are masked; no credentials or firmware are in the overlay.
Touch loading, visible GNOME and authenticated USB SSH have passed a persistent
boot; a fresh kernel startup with the debugging marker absent also verified
that neither a USB gadget nor an SSH listener was exposed. The
image-rotation helper verifies both saved images and the current boot image,
then writes and reads back only boot_b. File-backed failure tests verify
rollback after a partial write, wrong readback or read error; unknown images
are refused. `android-module/` supplies the Magisk Action entry and requires
a clean ext4 filesystem before mounting Debian read-only. Both switching
helpers have passed repeated on-device round trips with the installed profile.
A temporary userspace timer invoked the Linux helper during acceptance; it is
not included in the production overlay or kernel. The Magisk GUI Action and
Linux desktop launcher still need user-session acceptance.

## Combined Wi-Fi and speaker candidate

CI25 started Wi-Fi and keyboard automatically on one tablet and reconnected
its saved Wi-Fi profile. The selected Debian regulatory database did not match
this kernel's signing keys; the rootfs hook now selects the upstream database
and matching signature through Debian alternatives. NetworkManager uses a stable
private address per network because the firmware address changed across boots.
These two configuration fixes still require a fresh hardware test. Set a local
regulatory country only for the device's actual operating region.

The next candidate adds the six AW88461 amplifiers and the stock secondary TDM
interface. Shared reset, per-amplifier tuning selection, 48 kHz/eight 32-bit slots,
SD1, the TDM clock ID and stereo duplication were checked against this tablet's
stock evidence. Firmware remains private. The amplifier volume ceiling stays
at least 24 dB below the stock tuning gain; DSP speaker protection is not enabled.
Speaker output passed quiet-tone hardware tests and owner confirmation. CI32
adds WCD939x microphone capture with stock-verified wiring and rails, correct
AudioReach capture trigger lifecycle, and +12 dB capture gain. Raw stereo capture
passed acoustic checks; the owner accepted desktop audio. Automated desktop
acceptance did not complete. Headphones and suspend remain unverified.

The `audio-topology` CI artifact includes the compiled playback/capture graph and UCM
configuration. Its build checks PCM compatibility, graph links, configuration
sizes, channel maps and coefficients. Local build:

```sh
apt-get install git python3 m4 alsa-utils
python3 scripts/build-audio-topology.py
```

## Sources and patches

The exact-device kernel is pinned in [kernel/source.json](kernel/source.json)
to [arkylin/y900-linux](https://github.com/arkylin/y900-linux/tree/eccf7f8cde20924b8a22654f525f73f3cec0829e),
based on Linux 7.3. The unmodified source compiled successfully locally.

The applied patches guard diagnostic framebuffer writes, preserve initramfs
boundaries during the built-in FDT merge, panic on a failed merge, and disable
peripherals outside the initial USB test. A temporary, board-gated SCM patch
provides the EDL return protocol checked against the stock driver and exercised
by the standalone entry test and the ci8 Linux test. The probe configuration
retains Qualcomm support and omits debug symbols.

The NT36536 patches now build as a module for explicit loading after USB
logging is available. The DMA correction has passed identification, firmware loading and real finger input on one unit. Its
source is [yzddmr6/linux-sm8750-erhai](https://github.com/yzddmr6/linux-sm8750-erhai/tree/958a2b4654196bb52dfa0217a0f65ffeaa919f81/drivers/input/touchscreen/nt36536).
The TB522FU adaptation uses the stock driver's CRC-command lengths, report
length and pen pressure range. Finger orientation passed; pen and power lifecycle validation remain pending. Native panel takeover must establish the panel-follower relationship
before display power management can be tested. Firmware is supplied privately
on the USB link and is never uploaded to this repository or CI.

## License

New integration scripts are GPL-2.0-only. Imported code retains its original
copyright and license notices, including the GPL-2.0-or-later Novatek driver
and BSD-3-Clause board device tree. [NOTICE.md](NOTICE.md) records provenance.
Debian packages retain their individual licenses. No firmware extracted from the tablet is included. The root filesystem uses
Debian’s redistributable firmware packages.

The first combined CI27 boot reached GNOME, automatically connected Wi-Fi,
and loaded the keyboard and all six amplifier drivers. Speaker playback did
not start: the topology was installed under a filename the loader does not use,
and a probe-time GPR callback race caused the DSP readiness query to time out.
The next candidate installs `qcom/sm8750/TB522FU-tplg.bin` and includes the
attributed upstream callback fixes plus failed-probe receive draining.
Wi-Fi needs an explicit local country hint for its self-managed PHY; a global
module hint alone does not configure the radio. Those early speaker blockers
were resolved before CI28; current acceptance is described at the top of this page.

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
