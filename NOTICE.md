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
Orientation correction and display-power ownership passed the ci11 RAM hardware test, including normal clock-provider synchronization and physical GUI interaction.

The framebuffer power-domain declaration uses the existing mainline SM8750
MMCX/NOM_L1 definitions. Its 575 MHz/level 320 mapping was cross-checked
against the owner’s stock display driver; no proprietary code or binary is
included. Touch rotation comes from physical corner taps captured on the
owner’s device and uses standard touchscreen properties.

The staged UFS probe reuses the pinned board wiring after comparison with the owner’s stock device tree. No stock binary or dump is distributed. Storage validation is pending.


The staged Lenovo UART keyboard driver uses the framing dictionary and HID
usage mapping from Lenovo's GPL driver, published at
https://github.com/AkarinServer/Y700-Gen3-Droidian/tree/124f2c154a6e34a66df56afc08336cadd193d9f0/kernel/lenovo/kirby/kernel/drivers/tty/serial/lenovo_keyboard .
Its serdev lifecycle, bounded parser and TB522FU adaptation are separate local
work. Exact wiring and packet layout were checked against stock evidence;
firmware, raw captures and hardware identifiers are not included.


Audio dependency patches preserve authors and licenses from yzddmr6/linux-sm8750-erhai
and the scoped AW88461 implementation from GEEKiDoS/linux. Exact origins and
context adaptations are listed in patches/sources.json. Local TB522FU changes
provide shared reset, a volume ceiling, stock TDM/clock settings and board wiring.
No stock amplifier tuning or ACDB binary is redistributed.

AudioReach templates retain the BSD-3-Clause Linaro notices. The pinned upstream
and integration reference commits are in configs/audio/source.json. The volume-free
stream template and graph-link checker derive from yzddmr6/xiaomipad-8pro-mainline
(BSD-3-Clause and MIT respectively); the MFC/TDM templates and validation helpers
derive from yzddmr6/onepluspad-2pro-mainline (BSD-3-Clause and GPL-2.0-only respectively).
The compiled graph uses this tablet's observed slot routing with kernel channel labels.
