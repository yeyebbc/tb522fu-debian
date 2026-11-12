# Source provenance

| Component | Pinned source | License |
| --- | --- | --- |
| Mainline kernel and exact-device DTS | `arkylin/y900-linux` at `eccf7f8cde20924b8a22654f525f73f3cec0829e` | Linux file-level licenses; board DTS BSD-3-Clause |
| NT36536 driver, staged only | `yzddmr6/linux-sm8750-erhai` at `958a2b4654196bb52dfa0217a0f65ffeaa919f81` | Original Novatek/Xiaomi headers retained, GPL-2.0-or-later |
| TB522FU protocol adaptation | Local comparison with the owner's stock driver and Android input metadata | GPL-2.0-only additions |
| BusyBox probe userspace | Distribution `busybox-static` package | GPL-2.0-only; package version recorded in build manifest |
| Debian root filesystem | Signed Debian trixie, updates, security and backports archives | Individual package licenses and source information in Debian package metadata |

The kernel artifact's manifest records the source commit, applied patch hashes,
configuration hash and compiler version. Its source bundle contains the exact
patched tree used to build it. Pending touch patches are separate from the
initial USB-only kernel and preserve their upstream notices.
