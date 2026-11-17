#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Package the architecture-independent GNOME48 screen-only Suspend extension."""
import argparse
import hashlib
import json
from pathlib import Path
import stat
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'device/gnome-backlight-sleep'
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--output', type=Path, default=ROOT / 'artifacts/backlight-sleep')
a = p.parse_args()

def git(*args):
    return subprocess.check_output(['git', '-c', 'safe.directory=' + str(ROOT),
                                    '-C', str(ROOT), *args])

commit = git('rev-parse', 'HEAD').decode().strip()
inputs = [SOURCE / name for name in ['extension.js', 'metadata.json', 'README.md']]
inputs += [Path(__file__).resolve(), ROOT / 'tests/test_gnome_backlight_sleep.mjs']
source_hashes = {}
for path in inputs:
    relative = path.relative_to(ROOT).as_posix()
    data = path.read_bytes()
    if git('show', commit + ':' + relative) != data:
        raise SystemExit('Refusing uncommitted build input: ' + relative)
    source_hashes[relative] = hashlib.sha256(data).hexdigest()
metadata = json.loads((SOURCE / 'metadata.json').read_text())
assert metadata['uuid'] == 'backlight-sleep@tb522fu.local'
assert metadata['shell-version'] == ['48']
a.output.mkdir(parents=True, exist_ok=True)
archive = a.output / (metadata['uuid'] + '.shell-extension.zip')
with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as output:
    for name in ['metadata.json', 'extension.js', 'README.md']:
        item = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
        item.create_system = 3
        item.external_attr = (stat.S_IFREG | 0o644) << 16
        item.compress_type = zipfile.ZIP_DEFLATED
        output.writestr(item, (SOURCE / name).read_bytes())
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
manifest = dict(source_commit=commit, architecture='all', shell_versions=['48'],
                uuid=metadata['uuid'], version=metadata['version'],
                system_suspend_enabled=False, source_inputs=source_hashes,
                files={archive.name: dict(sha256=digest, bytes=archive.stat().st_size)})
(a.output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
(a.output / 'SHA256SUMS').write_text(digest + '  ' + archive.name + '\n')
print(archive)
