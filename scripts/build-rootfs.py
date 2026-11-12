#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Build Debian 13 ARM64 natively from authenticated distribution archives."""
from pathlib import Path
import hashlib
import json
import os
import platform
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    assert os.geteuid() == 0, 'Run in the privileged build container or as root'
    assert platform.machine() in ['aarch64', 'arm64'], 'Use a native ARM64 runner'
    dest = ROOT / 'artifacts/rootfs'
    dest.mkdir(parents=True, exist_ok=False)
    temp = ROOT / 'work/rootfs-tmp'
    temp.mkdir(parents=True, exist_ok=True)
    packages = [x.strip() for x in (ROOT / 'configs/rootfs-packages.txt').read_text().splitlines()
                if x.strip() and not x.startswith('#')]
    archive = dest / 'debian13-arm64-gnome.tar.zst'
    env = dict(os.environ, TMPDIR=str(temp), TB522FU_ARTIFACT_DIR=str(dest),
               DEBIAN_FRONTEND='noninteractive', LC_ALL='C.UTF-8')
    subprocess.run(['mmdebstrap', '--mode=root', '--architectures=arm64',
                    '--variant=important', '--components=main,contrib,non-free-firmware',
                    '--aptopt=APT::Update::Error-Mode "any"',
                    '--include=' + ','.join(packages),
                    '--hook-dir=' + str(ROOT / 'hooks'), 'trixie', str(archive),
                    str(ROOT / 'configs/debian.sources.list')], env=env, check=True)
    installed = (dest / 'packages.tsv').read_text().splitlines()
    assert installed and all(x.endswith('\tinstalled') for x in installed)
    assert not any(x.startswith('linux-image-') for x in installed)
    assert any(x.startswith('mesa-libgallium\tarm64\t26.') for x in installed)
    assert archive.stat().st_size > 100 * 1024 * 1024
    subprocess.run(['zstd', '--test', str(archive)], check=True)
    (dest / 'manifest.json').write_text(json.dumps({
        'distribution': 'Debian 13 trixie', 'architecture': 'arm64',
        'desktop': 'GNOME', 'hardware_tested': False,
        'device_firmware_dumps_included': False, 'kernel_included': False,
        'sources_sha256': sha(ROOT / 'configs/debian.sources.list'),
        'packages_sha256': sha(dest / 'packages.tsv'),
        'archive_sha256': sha(archive), 'archive_bytes': archive.stat().st_size,
    }, indent=2) + '\n')
    (dest / 'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in sorted(dest.iterdir()) if p.is_file()))
    print('Debian root filesystem artifact:', archive)


if __name__ == '__main__':
    main()
