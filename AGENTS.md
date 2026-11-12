# TB522FU Debian build repository

This repository is public. Keep firmware, identifiers, credentials, backups,
stock partition images and local environment paths out of tracked files.

- Kernel source and imported drivers must retain pinned origins and licenses.
- Build artifacts do not establish hardware support. State only observed results.
- CI must never flash a device, deploy images, use a self-hosted runner, or need
  account secrets. Use GitHub-hosted ARM64 runners and read-only permissions.
- Preserve Android and verified stock recovery. RAM tests precede storage changes.
- The RAM desktop candidate includes GPI/SPI/touch modules for explicit loading only after USB logging works. ci10 clock-provider control showed physical GNOME and real finger input. The display blacks out when the final provider allows RPMh sync; the new MMCX consumer and touch rotation correction still require hardware validation. Do not add the temporary clock blacklist to the next test; verify normal coldplug with the explicit power vote. Start on the console, then load gpi, spi_geni_qcom and nt36536_ts explicitly; start GDM separately. A running GNOME process does not prove visible output.
- Do not change the kernel version or source commit without updating its manifest.
- Validate Python/shell syntax, patch applicability, and the resulting workflow.
