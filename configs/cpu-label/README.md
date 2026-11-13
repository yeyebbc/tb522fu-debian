# ARM processor label candidate

GNOME Settings uses libgtop to obtain CPU model names. On ARM64, `/proc/cpuinfo`
provides implementer and part numbers without the x86 `model name` field.
This candidate rebuilds Debian's libgtop 2.41.3-1 with the unchanged Ubuntu
patch that obtains decoded model names from util-linux `lscpu`.

The patch is by Andreas Glinserer and Marco Trevisan, under libgtop's
GPL-2.0-or-later license. Its exact Ubuntu source archive, patch digest,
Debian source files and upstream merge request are pinned in `source.json`.
No CPU model is hardcoded and no kernel, clock or power setting changes.

Run the manual **Build Debian ARM CPU label fix** workflow. It produces Debian
packages and compares the installed candidate's libgtop results with `lscpu`
on a GitHub-hosted ARM64 runner. CI never installs on a tablet. Hardware
acceptance still requires the same comparison on the tablet and a visible
GNOME System Details check. Keep the original Debian packages for rollback.

Retire this backport when Debian ships the corresponding CPU-name fix.
Do not install it over a different base version without checking packaging
compatibility and preserving that version's fixes.
