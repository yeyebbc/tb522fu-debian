# EndeavourOS ARM comparison plan

**Superseded on 2026-11-17:** the user chose
[Fedora 45 ARM64](fedora45-trial.md) because EndeavourOS does not supply the
general-purpose ARM64 image they wanted. No EndeavourOS root or kernel was
installed. The remaining text preserves the earlier assessment.

The user requested EndeavourOS after the Ubuntu battery-wake reproduction and
is handling the image download. Preserve the
[Ubuntu checkpoint](checkpoints/2026-11-17-ubuntu-ci90.md) before changing the
comparison environment. No EndeavourOS image is installed or accepted yet.

## Image and kernel admission

The [standard EndeavourOS distribution](https://endeavouros.com/) targets
Intel/AMD systems. The separate [ARM project](https://endeavouros.com/endeavouros-arm/)
publishes board-specific images. Inspect the supplied image and verify its
publisher checksum/signature before extracting a root filesystem. Native
tablet binaries must be ARM64/aarch64; an x86_64 desktop ISO cannot provide
native userspace or a bootable kernel for this tablet.

The inspected `EndeavourOS_Titan-Nova-2026.08.15.iso` contains x86_64 boot files,
an x86_64 root filesystem and `linux 7.1.8.arch1-3` in its package list. It has
not been deployed. A rolling-system update may provide a different kernel;
record the actual ARM package and source rather than assuming the ISO version.

Our custom kernel already reports 7.3. A different distribution's 7.3 version
number does not establish equivalent SoC drivers, panel support, board DT,
boot-image format or recovery behavior. Audit those differences and matching
module ABI before selecting a kernel. A root-only trial retaining our kernel
tests userspace; a compatible alternative kernel is a separate comparison and
must be recorded as such. Do not silently substitute one for the other.

## Preparation and acceptance

1. Identify the ARM image/root source, license, checksum and package versions.
   Inspect board-specific boot scripts and package hooks offline; do not run
   their partitioning or bootloader installers on the tablet.
2. Prepare a separate root directory inside the existing Linux filesystem.
   Preserve Android, Debian, Ubuntu, partition geometry and selected CI78.
   Integrate required device firmware/configuration privately; preserve user
   language/time zone and the Wi-Fi-only US regulatory setting.
3. Resolve the kernel/DT/module set, GPU userspace and native dependencies.
   Retain opt-in key-only USB debugging, a persistent local logger, an
   independent timed return and the verified host recovery transaction.
4. Validate the staged root and immutable boot artifacts. First require clear
   physical GNOME output, real Adreno rendering and the supported-driver
   baseline, then one connected display off/on cycle with camera evidence.
5. Only after that baseline passes, repeat unplug → Lock → Space while still
   unplugged → reconnect. Use local input/power timestamps and camera frames
   entirely before reconnection. Keep actual system sleep masked so this
   comparison remains display wake.
6. Return to Android, collect native evidence, retire owned timers, verify the
   selected Debian image/graphics and filesystem, and restore host/camera state.

Do not promote a candidate on compilation, module loading, GNOME display-on
state, a compositor screenshot or connected-only wake success. Record the
physical battery result and which components actually changed. The retained
Ubuntu failure is sufficient; do not repeat it unchanged.
