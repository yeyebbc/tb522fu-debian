# Source provenance

| Component | Pinned source | License |
| --- | --- | --- |
| Mainline kernel and exact-device DTS | `arkylin/y900-linux` at `eccf7f8cde20924b8a22654f525f73f3cec0829e` | Linux file-level licenses; board DTS BSD-3-Clause |
| NT36536 driver, loadable test module | `yzddmr6/linux-sm8750-erhai` at `958a2b4654196bb52dfa0217a0f65ffeaa919f81` | Original Novatek/Xiaomi headers retained, GPL-2.0-or-later |
| TB522FU protocol adaptation | Local comparison with the owner's stock driver and Android input metadata | GPL-2.0-only additions |
| BusyBox probe userspace | Distribution `busybox-static` package | GPL-2.0-only; package version recorded in build manifest |
| Debian root filesystem | Signed Debian trixie, updates, security and backports archives | Individual package licenses and source information in Debian package metadata |

The kernel artifact's manifest records the source commit, applied patch hashes,
configuration hash and compiler version. Its source bundle contains the exact
patched tree used to build it. The touch import and board adaptation remain separate patches and preserve
their upstream notices. They are included in the RAM desktop build, with
identification, firmware loading and physical finger input verified on one unit.
Orientation correction and display-power ownership still need hardware validation.

The framebuffer power-domain declaration uses the existing mainline SM8750
MMCX/NOM_L1 definitions. Its 575 MHz/level 320 mapping was cross-checked
against the owner’s stock display driver; no proprietary code or binary is
included. Touch rotation comes from physical corner taps captured on the
owner’s device and uses standard touchscreen properties.
