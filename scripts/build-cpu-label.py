#!/usr/bin/env python3
"""Build Debian libgtop with the unchanged Ubuntu ARM model-name backport."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import urllib.request

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--prepare-only', action='store_true')
args = parser.parse_args()
manifest_path = root / 'configs/cpu-label/source.json'
manifest = json.loads(manifest_path.read_text())
work = root / 'build/cpu-label'
work.mkdir(parents=True, exist_ok=True)
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
for item in manifest['files']:
    assert Path(item['name']).name == item['name']
    path = work / item['name']
    if not path.exists():
        with urllib.request.urlopen(item['url'], timeout=60) as response:
            path.write_bytes(response.read())
    assert digest(path) == item['sha256'], item['name']
patch = root / manifest['patch']['path']
assert digest(patch) == manifest['patch']['sha256']
source = work / 'source'
assert not source.exists(), 'Use a fresh build directory; do not reuse partially patched sources'
dsc = work / ('libgtop2_' + manifest['debian_source_version'] + '.dsc')
# Exact SHA256 for the .dsc and both payloads is checked above. Build hosts
# need no private signing keys or external keyserver access.
subprocess.run(['dpkg-source', '--no-check', '-x', str(dsc), str(source)], check=True)
patch_dir = source / 'debian/patches'
patch_dir.mkdir(exist_ok=True)
shutil.copy2(patch, patch_dir / patch.name)
series = patch_dir / 'series'
old_series = series.read_text() if series.exists() else ''
assert patch.name not in old_series
series.write_text(old_series + ('\n' if old_series and not old_series.endswith('\n') else '') + patch.name + '\n')
subprocess.run(['patch', '--batch', '--fuzz=0', '--dry-run', '-p1', '-i', str(patch)], cwd=source, check=True)
changelog = source / 'debian/changelog'
entry = ('libgtop2 (' + manifest['candidate_version'] + ') unstable; urgency=medium\n\n'
         '  * Backport the Ubuntu libgtop ARM model-name discovery patch.\n'
         '    No kernel or CPU operating parameters are changed.\n\n'
         ' -- Codex <codex@localhost>  Fri, 13 Nov 2026 18:00:00 +0000\n\n')
changelog.write_text(entry + changelog.read_text())
if args.prepare_only:
    print(source)
    raise SystemExit(0)
assert subprocess.check_output(['dpkg', '--print-architecture'], text=True).strip() == 'arm64'
env = dict(os.environ, DEB_BUILD_OPTIONS='parallel=' + str(min(os.cpu_count() or 2, 8)))
subprocess.run(['dpkg-buildpackage', '-us', '-uc', '-b'], cwd=source, env=env, check=True)
artifacts = root / 'artifacts/cpu-label'
artifacts.mkdir(parents=True, exist_ok=False)
files = {}
for path in sorted(work.glob('*')):
    if path.is_file() and path.suffix in ('.deb', '.changes', '.buildinfo'):
        shutil.copy2(path, artifacts / path.name)
        files[path.name] = {'sha256': digest(path), 'bytes': path.stat().st_size}
assert any(name.startswith('libgtop-2.0-11_') and name.endswith('_arm64.deb') for name in files)
shutil.copy2(manifest_path, artifacts / 'source.json')
shutil.copy2(patch, artifacts / patch.name)
subprocess.run(['tar', '-cJf', str(artifacts / 'patched-source.tar.xz'),
                '-C', str(work), 'source'], check=True)
files['patched-source.tar.xz'] = {'sha256': digest(artifacts / 'patched-source.tar.xz')}
report = {'recipe_commit': subprocess.check_output(['git', '-c', 'safe.directory='+str(root), 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
          'source': manifest, 'files': files, 'hardware_acceptance': False,
          'built_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
(artifacts / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
