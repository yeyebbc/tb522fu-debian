# TB522FU Debian build repository

This repository is public. Keep firmware, identifiers, credentials, backups,
stock partition images and local environment paths out of tracked files.

- Kernel source and imported drivers must retain pinned origins and licenses.
- Build artifacts do not establish hardware support. State only observed results.
- CI must never flash a device, deploy images, use a self-hosted runner, or need
  account secrets. Use GitHub-hosted ARM64 runners and read-only permissions.
- Preserve Android and verified stock recovery. RAM tests precede storage changes.
- The RAM desktop candidate includes GPI/SPI/touch modules for explicit loading only after USB logging works. ci9 booted Debian but showed a black screen and SPI timeouts. Start on the console, then load qcom_gpi, spi_geni_qcom and nt36536_ts explicitly; start GDM separately. A running GNOME process does not prove visible output.
- Do not change the kernel version or source commit without updating its manifest.
- Validate Python/shell syntax, patch applicability, and the resulting workflow.
