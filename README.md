# Debian 13 on Lenovo TB522FU

Experimental native Linux port for the Lenovo Legion Y900 13 / TB522FU
(SM8750, Snapdragon 8 Elite). Debian 13 ARM64 with GNOME is installed on a
256 GiB partition on one test tablet, with Android preserved and on-device switching verified in both
directions. This remains a development port with substantial peripheral work
outstanding.

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
SimpleDRM borrows the firmware framebuffer;
native display and GPU remain disabled. A separate, optional workflow job builds
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
remain unvalidated. A charging icon alone does not establish these. Wi-Fi is
the next development priority, followed by audio; further charging refinements
are deferred.

The Wi-Fi candidate imports the Peach (`17cb:110e`) ath12k implementation from
[GEEKiDoS/linux](https://github.com/GEEKiDoS/linux/commit/b0c05eb72e10140f87efd0e499ad840e6c3e6975),
including TME-L patch loading, QDSS transfer, and firmware-directed PDC votes.
The original source attribution is retained; the import is limited to Wi-Fi
and its power-sequencing dependencies. Bluetooth remains disabled.
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

Native display/GPU, brightness, audio, sustained charging, suspend and pen input
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
