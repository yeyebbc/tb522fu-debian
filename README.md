# Debian 13 on Lenovo TB522FU

Experimental native Linux port for the Lenovo Legion Y900 13 / TB522FU
(SM8750, Snapdragon 8 Elite). The intended installation is Debian 13 ARM64
with GNOME and 128 GiB of storage, preserving Android for dual boot.

GitHub Actions builds two independent artifacts on native ARM64 runners:

- A kernel, device tree and matching modules for a bounded RAM desktop test.
  Its BusyBox initramfs exposes USB NCM/ACM, protects block devices, and keeps
  UFS disabled. An opt-in kernel timer requests EDL after 600 seconds from
  SCM readiness, allowing the attached host to restore Android. SimpleDRM
  borrows the firmware framebuffer. Native display and GPU remain disabled.
  The USB host can supply a hash-verified SquashFS root, matching modules and
  private touch firmware to a disposable RAM overlay before starting Debian.
- A Debian 13 GNOME root filesystem from authenticated Debian archives,
  including security updates and the Mesa stack from trixie-backports.

The RAM probe has **booted successfully on one TB522FU**. Recipe
`ac9549fbbafa83e9d8409446118c05541766f15f` from
[CI run 43222822022](https://github.com/yeyebbc/tb522fu-debian/actions/runs/43222822022)
produced Linux `7.3.0-tb522fu-probe-ci8+`: visible firmware framebuffer text,
working USB networking and a network shell, followed by timed EDL return and
verified stock Android restoration. The ACM interface enumerated but its
serial shell did not work. Debian GNOME, native display/GPU, touch, Wi-Fi,
audio, charging, suspend and installed Android/Linux switching remain
unverified. The artifacts are development components, not a flashable installer.
The subsequent RAM desktop recipe `6b72e6d9cbd0a336df93ad12a936a121ab846d51`
passed both jobs in [CI run 43229000858](https://github.com/yeyebbc/tb522fu-debian/actions/runs/43229000858).
Its downloaded kernel/modules and local boot packaging passed verification;
it has not yet been booted on the tablet.
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
artifacts → Run workflow**. Download `kernel-usb-probe` and
`debian13-arm64-gnome` from that workflow run. Each contains SHA-256 checksums
and a source or package manifest. Artifacts expire after seven days.

The jobs use Debian 13 containers on `ubuntu-24.04-arm`. The kernel build uses
ccache. Root filesystem construction runs natively, avoiding QEMU overhead.
Workflow permissions are read-only; there is no deployment or flashing job.

To build the kernel locally on Debian 13 ARM64:

```sh
sudo apt-get install build-essential bc bison flex libssl-dev libelf-dev \
  ccache device-tree-compiler busybox-static cpio python3 git zstd kmod
python3 scripts/build-kernel.py
```

For an x86_64 Debian build host, also install `gcc-aarch64-linux-gnu` and
provide an ARM64 static BusyBox with `--busybox /path/to/arm64/busybox`.
Build the root filesystem on ARM64 as root with:

```sh
apt-get install mmdebstrap debian-archive-keyring ca-certificates zstd
python3 scripts/build-rootfs.py
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
logging is available. The new desktop candidate is **not hardware-tested**. Its
source is [yzddmr6/linux-sm8750-erhai](https://github.com/yzddmr6/linux-sm8750-erhai/tree/958a2b4654196bb52dfa0217a0f65ffeaa919f81/drivers/input/touchscreen/nt36536).
The TB522FU adaptation uses the stock driver's CRC-command lengths, report
length and pen pressure range. The changed objects and board DTB compiled locally; hardware validation is
pending. Native panel takeover must establish the panel-follower relationship
before display power management can be tested. Firmware is supplied privately
on the USB link and is never uploaded to this repository or CI.

## License

New integration scripts are GPL-2.0-only. Imported code retains its original
copyright and license notices, including the GPL-2.0-or-later Novatek driver
and BSD-3-Clause board device tree. [NOTICE.md](NOTICE.md) records provenance.
Debian packages retain their individual licenses. No firmware extracted from the tablet is included. The root filesystem uses
Debian’s redistributable firmware packages.
