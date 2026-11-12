# TB522FU Debian build repository

This repository is public. Keep firmware, identifiers, credentials, backups,
stock partition images and local environment paths out of tracked files.

- Kernel source and imported drivers must retain pinned origins and licenses.
- Build artifacts do not establish hardware support. State only observed results.
- CI must never flash a device, deploy images, use a self-hosted runner, or need
  account secrets. Use GitHub-hosted ARM64 runners and read-only permissions.
- Preserve Android and verified stock recovery. RAM tests precede storage changes.
- ci11 verified physical GNOME with normal clock-provider coldplug, MMCX at320 after RPMh sync, and correctly aligned real finger input. Preserve these fixes and the independent600-second return. Native display/GPU, suspend and pen remain unverified.
- The next candidate permits UFS only through explicit host/PHY module loading in the BusyBox initramfs after USB and payload validation. Use ram-storage-probe, protect all six LUNs and partitions read-only, then capture and verify both GPTs. No automounter, filesystem mounts, disk writes or repartitioning in this probe. Stock node wiring is reviewed; reference-clock supply ownership remains a follow-up if runtime power management is enabled.
- A running GNOME process or a framebuffer capture does not prove physical output. Keep camera evidence and source/image hashes.
- Do not change the kernel version or source commit without updating its manifest.
- Validate Python/shell syntax, patch applicability, and the resulting workflow.

- Resolve every explicit modprobe/blacklist name against built modules with modinfo; Kconfig and driver names do not reliably match module filenames. ci12 artifact uses ufs_qcom; its original helper typo is corrected in RAM before the first storage test.
