# Fedora 45 ARM64 comparison plan

The user selected Fedora 45 after the
[Ubuntu battery-wake reproduction](checkpoints/2026-11-17-ubuntu-ci90.md),
replacing the EndeavourOS proposal. The user handles the image download;
integration, driver compatibility, test logging and recovery are agent work.
The supplied image is verified and host preparation is active. No Fedora
hardware boot or installed default is accepted yet.

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
