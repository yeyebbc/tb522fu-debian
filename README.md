# Debian 13 on Lenovo TB522FU

Experimental native Linux port for the Lenovo Legion Y900 13 / TB522FU
(SM8750, Snapdragon 8 Elite). The intended installation is Debian 13 ARM64
with GNOME and 256 GiB of storage, preserving Android for dual boot.

GitHub Actions builds two kernel profiles on native ARM64 runners:

- `disk-test`: an embedded BusyBox maintenance/boot environment with matching
  modules, e2fsck and a900-second independent EDL return for host restoration.
- `installed`: the same device support with normal reboot semantics and no
  test timer. USB debugging is opt-in. This profile is not hardware-tested yet.

Both locate Debian by GPT label, verify its256GiB geometry and installation
marker, check ext4 and load the matching root. They never create partitions or
format filesystems automatically. Before installation, disk-test remains in a
read-only maintenance shell. SimpleDRM borrows the firmware framebuffer;
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

No repartitioning or persistent installation has occurred. Native display/GPU,
Wi-Fi, audio, charging, suspend and installed Android/Linux switching remain
unverified. These artifacts are development components, not an installer.

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

`device/` contains the pending installation overlay: ordered touch loading,
200% GNOME scale, sleep disabled while power management is unverified, and
optional SSH restricted to the USB peer with public-key authentication.
The installer must supply this tablet's firmware, root PARTUUID and authorized
key privately. Debugging is off unless `/etc/tb522fu/usb-debug-enabled` exists.
Default SSH services are masked; no credentials or firmware are in the overlay.
These files have passed syntax/unit checks, not persistent hardware validation.

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
