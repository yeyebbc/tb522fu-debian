# Fedora 45 ARM64 comparison plan

The user selected Fedora 45 after the
[Ubuntu battery-wake reproduction](checkpoints/2026-11-17-ubuntu-ci90.md),
replacing the EndeavourOS proposal. The user handles the image download;
integration, driver compatibility, test logging and recovery are agent work.
The supplied image is verified and staged separately. First hardware boot
passed physical desktop and Adreno rendering, but failed the final display-log
gate. No battery-wake result or installed default is accepted yet.

## Verified image and initial route

| Input | Observed value |
| --- | --- |
| Image | `Fedora-Workstation-Disk-45-1.4.aarch64.raw.xz` |
| Compressed bytes | `3222363420` |
| SHA-256 | `07ab3377cee9d4bbc15e7203214594f8cfdb58a9a57e195aa0ff183cf81ea0a8` |
| Native image kernel | `7.2.11-300.fc45.aarch64` |
| GNOME / Mutter | `51.0-1.fc45` |
| Mesa | `26.2.3-1.fc45` |

The full image hash matches its Fedora-signed checksum; the signing fingerprint
matches [Fedora's published key](https://fedoraproject.org/security/).
XZ integrity and a read-only Btrfs-root/ext4-boot inspection passed. ARM64 ELF
identity and native package versions were checked in the supplied root.

The image has SM8750 reference-board DTs, but no DT for this Lenovo tablet.
Its module tree lacks our custom panel, touch and keyboard drivers. The initial
bounded Fedora boot therefore retains the CI90 tablet kernel source, DT and
effective config, while trying Fedora's native GNOME and Mesa. This is a
userspace/graphics comparison; it does not test Fedora's stock kernel or prove
a kernel-only cause. A Fedora-derived kernel needs separate board integration.

The supplied Mesa26.2.3 and upstream26.2.6 table both lack the mainline
wildcard-speed-bin entry for this A830 revision. A separate native Fedora45
Mesa26.2.6 build is therefore prepared with the existing one-line upstream ID
backport and unchanged GPU properties. It uses Fedora's own dependencies and
an isolated prefix; Debian/Ubuntu shared libraries are not imported. This is a
newer graphics-stack comparison, not unmodified Fedora Mesa acceptance.
Compilation and a software-renderer negative control precede hardware testing.

The explicit `fedora45-test` root is pinned to this image SHA and
`var/lib/tb522fu-dualboot/fedora45-test/root`. Source identity, board, partition,
OS/version, canonical path and matching modules must pass before writes.
Workflow `trial_root=fedora45-test` affects disk-test only; installed and RAM
cannot select it. The independent 900-second kernel return remains required.

## Image and root preparation

[Fedora Workstation 45](https://fedoraproject.org/workstation/download/) provides
an aarch64 Live ISO and a raw image. Inspect the supplied filename, architecture
and contents, verify the signed checksum with Fedora's published signing key,
and record the actual package versions. Extract a root filesystem offline;
do not run the generic installer or write the whole disk image to tablet UFS.

Keep Fedora in a separate directory on the existing Linux filesystem. Preserve
Android, selected Debian CI78, the retained Ubuntu root, partition geometry and
rollback images. Preserve numeric ownership, capabilities and relevant xattrs;
account for Fedora's SELinux labels and native library layout. Budget host
extraction/package space before unpacking large layers.

Use Fedora's GNOME, Mutter, Mesa and native dependencies where they support the
hardware. Check the exact Adreno revision before choosing graphics libraries;
record any required fallback to the shared A830-enabled Mesa separately. Adapt
device services with native dependencies and drop-ins. Do not copy Debian or
Ubuntu system libraries into Fedora or apply dpkg-specific integration there.
Retain user language/time zone, accepted audio/input settings and Wi-Fi-only US
regulatory configuration. Hardware presence alone is not functional acceptance.

## Kernel comparison

Our existing custom kernel already reports 7.3. Audit Fedora's actual ARM64
kernel package, configuration, source and DT/module support for the tablet,
including UFS, display/panel, touch, USB recovery and accepted peripherals.
A generic ARM64 release or matching version number does not establish this.
Fedora's UEFI boot artifacts also need the tablet's verified Android boot format.

Determine the supported route from that audit before staging a boot. A trial
using the existing tablet kernel is a userspace comparison; a Fedora-derived
kernel with required board adaptations is a different experiment. Record
exactly which components change and preserve the original Fedora kernel/config
for comparison. Do not claim kernel attribution from a root-only distro change.
Audit native SELinux expectations and custom-kernel configuration explicitly.

## Bounded test sequence

1. Verify the staged root identity, kernel/DT/module ABI, firmware/configuration
   manifests and immutable boot image before any device write.
2. Arm the independent timed return, USB key-only debug path, persistent native
   logger, camera recording and verified host restoration transaction before
   leaving Android. Do not reuse a finished Ubuntu transaction.
3. First require visible signed-in GNOME, real Adreno pixels and compositor GPU
   use, the supported-driver baseline and a connected display off/on cycle.
4. Then run one unplug → Lock → wait → Space while still unplugged → reconnect
   comparison. Use verified USB power readings, local input/monotonic timestamps
   and physical camera frames captured entirely before reconnection. Keep UDC
   state separate because `configured` can remain stale after unplugging.
5. Keep actual system sleep masked for this display-wake comparison. A later
   system-suspend test requires a separate passing baseline and recovery plan.
6. Return Android, retrieve native logs, retire owned timers, verify selected
   Debian/graphics and filesystem state, then restore host/camera settings.

Do not promote on compilation, GNOME display-on state, screenshots or connected
wake alone. Report the physical battery result, changed components and remaining
limits. The Ubuntu failure is already established; do not repeat it unchanged.

## Build preparation status

Kernel CI91 [run44064248541](https://github.com/yeyebbc/tb522fu-debian/actions/runs/44064248541)
passed both profiles. The downloaded disk-test artifact, embedded Fedora root
selector/modules and signed Android-format boot image pass admission. All114
patches, DT bytes and effective config equal CI90. Recipe
`a83b3187cdcf5e2cb25e79b94d34bff2f343b3fd`, boot SHA-256
`b6aaf10b944ca71532e35e220843389279ca4ca6456af27a3e499bd6cc6b0983`.
The first Fedora graphics run stopped before Mesa compilation because the
Fedora package is `spirv-headers-devel`. That dependency name is corrected;
[graphics-only run44066742541](https://github.com/yeyebbc/tb522fu-debian/actions/runs/44066742541)
passed dependency installation, native Mesa compilation and the llvmpipe
negative control. It uses the same pinned Mesa source and one-line GPU entry.
The downloaded GitHub artifact digest, inner hashes, native dependency versions
and exact one-line source-table delta pass audit; no kernel rebuild was needed.
Graphics recipe `f7d7f5c45bb9e0276cfe9f21f6dd3ff4374f6f98`.

The prepared root passes native ARM64 library loading, llvmpipe rejection,
key-only SSH configuration and six relevant systemd unit checks. All39 supported
module names resolve through modinfo to the matching CI91 ABI. Locale and
effective GNOME power defaults pass. The full frozen root manifest covers
162990 entries, ownership/modes and xattrs. Device staging/full verification and full filesystem checks passed for that
frozen preparation. A later source audit found its omitted separate `/var`
subvolume; the base archive is retained as failed preparation, with a separately
verified correction layer. Physical acceptance remains scenario-specific.


## Fedora compatibility limits

The existing tablet kernel has no SELinux LSM, PSI or zram. Preserve the source
SELinux xattrs in the root/archive and verify them after staging; Android's
SELinux policy is left unchanged. This bounded comparison does not provide
Fedora stock SELinux enforcement. Disable only the trial root's zram generator
and oomd units that need unavailable kernel features. Remove the raw image's
foreign UUID/growfs fstab entries and mask growfs in the test root; storage
geometry stays unchanged. These are explicit trial compatibility adjustments,
not kernel fixes or production Fedora acceptance.

Reuse the existing local account without copying its home, preserve user
locale/time zone, disable first-run GDM setup, and keep key-only SSH bound to
the USB address. The native Fedora firewall's existing SSH allowance is kept.
The isolated newer Mesa prefix uses Fedora dependencies; preserve the native
Vulkan ICD as a private backup before selecting the trial copy. Retire these
trial overrides when a native supported kernel/Mesa route is accepted.

Fedora's own offline setfiles restores labels replaced during account creation;
it runs inside the owned root with no host bind mounts. The raw image's native
wallpaper override emits an obsolete-key warning during normal schema
compilation and is retained. Validate the trial power override separately with
strict native XML compilation, then check its actual compiled GSettings values.
Do not change unrelated Fedora RPM settings to silence that existing warning.

## First hardware result and corrected preparation

The first CI91 Fedora boot displayed a clear greeter and signed-in GNOME
desktop. The native Mesa hardware pixel test rendered149 frames in2 seconds
on Adreno830v1; the llvmpipe negative control returned3. All39 listed support
modules loaded. This establishes those observations, not complete peripheral
or wake acceptance. Two vblank/commit-timeout pairs appeared just after desktop
login, so the final native probe returned1 despite the clear, responsive camera
footage. No DPMS, battery action or system sleep was requested in that session.

The raw Btrfs image contains separate `root`, `home` and `var` subvolumes. The
initial extraction missed `var`. A separate audited layer restores missing
stock files and packaged directory permissions without replacing newly created
account/runtime/log files. The failed base and first-session evidence are kept.
Future extraction must inspect fstab and every filesystem/subvolume, including
separate `/var`; copying just the apparent root is insufficient. The unused
source home is deliberately replaced by the existing local account's new home.

The trial now explicitly masks `systemd-repart.service` as well as growfs.
Both on-device GPT copies, all approved partition geometry/identities, selected
Debian image and graphics state pass post-return verification. The custom
kernel lacks NF_TABLES, so native Fedora firewall compatibility remains an
explicit limit; do not silently switch firewall backends or change the kernel
during this comparison. Detailed native service statuses are captured in the
next probe before any display cycle.

The corrected test retains the identical CI91 boot image, source, DT and
configuration. It requires a settled45-second signed-in whole-boot fault check
before connected DPMS, then physical camera review before any unplugged action.
Actual system sleep remains masked. The host coordinator runs in a persistent
user systemd unit; independent kernel return and exact Android restoration
remain armed. No first-boot failure is cleared or reclassified as a pass.
