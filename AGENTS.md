# TB522FU Debian build repository

This repository is public. Keep firmware, identifiers, credentials, backups,
stock partition images and local environment paths out of tracked files.

- Kernel source and imported drivers must retain pinned origins and licenses.
- Build artifacts do not establish hardware support. State only observed results.
- CI must never flash a device, deploy images, use a self-hosted runner, or need
  account secrets. Use GitHub-hosted ARM64 runners and read-only permissions.
- Preserve Android and verified stock recovery. RAM tests precede storage changes.
- ci11 verified physical GNOME with normal clock-provider coldplug, MMCX at320 after RPMh sync, and correctly aligned real finger input. Preserve these fixes. Native display/GPU, suspend and pen remain unverified.
- ci12 verified six UFS LUNs, both GPTs, full partition hashes and a read after runtime suspend. Stock Android restoration passed. The requested persistent Debian allocation is256GiB. Disk-test has an independent900-second EDL return; installed has normal restart semantics and no test timer. Both embed their matching modules and e2fsck. Before root verification storage stays read-only. No automatic partition creation or formatting.
- A running GNOME process or a framebuffer capture does not prove physical output. Keep camera evidence and source/image hashes.
- Do not change the kernel version or source commit without updating its manifest.
- Validate Python/shell syntax, patch applicability, and the resulting workflow.

- Resolve every explicit modprobe/blacklist name against built modules with modinfo; Kconfig and driver names do not reliably match module filenames. ci12 artifact uses ufs_qcom; its original helper typo is corrected in RAM before the first storage test.
