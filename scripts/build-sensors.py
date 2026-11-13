#!/usr/bin/env python3
"""Build SSC userspace inside a disposable Debian ARM64 build container.

Installs build dependencies between projects in that container. The output is
an offline payload and matching sources; this script never accesses a tablet.
"""
import hashlib
import json
from pathlib import Path
import platform
import shutil
import socket
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def run(args, **kwargs):
    print('+', ' '.join(map(str, args)), flush=True)
    return subprocess.run(list(map(str, args)), check=True, **kwargs)


def capture(args, **kwargs):
    return run(args, stdout=subprocess.PIPE, text=True, **kwargs).stdout.strip()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if platform.machine() != 'aarch64' or not Path('/.dockerenv').exists():
        raise SystemExit('Use a disposable Debian ARM64 Docker build container')
    recipe = capture(['git', '-c', 'safe.directory=' + str(ROOT), '-C', ROOT,
                      'rev-parse', 'HEAD'])
    spec = json.loads((ROOT / 'configs/sensors/source.json').read_text())
    work = ROOT / 'work/sensors'
    artifacts = ROOT / 'artifacts/sensors'
    stage = work / 'stage'
    for path in (work, artifacts, stage):
        path.mkdir(parents=True, exist_ok=True)
    if any(stage.iterdir()):
        raise SystemExit('Use a fresh sensor staging directory')
    results = []
    for item in spec['components']:
        name = item['name']
        src = work / name
        build = work / (name + '-build')
        run(['git', 'init', src])
        run(['git', '-C', src, 'remote', 'add', 'origin', item['repository']])
        run(['git', '-C', src, 'fetch', '--depth=1', 'origin', item['commit']])
        run(['git', '-C', src, 'checkout', '--detach', 'FETCH_HEAD'])
        assert capture(['git', '-C', src, 'rev-parse', 'HEAD']) == item['commit']
        record = dict(item)
        record['upstream_tree'] = capture(['git', '-C', src, 'rev-parse', 'HEAD^{tree}'])
        if item.get('patch'):
            patch = ROOT / item['patch']
            record['patch_sha256'] = sha(patch)
            run(['git', '-C', src, 'apply', '--check', patch])
            run(['git', '-C', src, 'apply', patch])
        run(['git', '-C', src, 'add', '-A'])
        record['patched_tree'] = capture(['git', '-C', src, 'write-tree'])
        options = ['--prefix=/usr', '--libdir=lib/aarch64-linux-gnu', '--buildtype=release']
        if name == 'hexagonrpc':
            # This project's unit-file destination is relative to libdir.
            options[1] = '--libdir=lib'
        if name == 'iio-sensor-proxy':
            options += ['-Dssc-support=enabled', '-Dudevrulesdir=/usr/lib/udev/rules.d',
                        '-Dsystemdsystemunitdir=/usr/lib/systemd/system', '-Dtests=false']
        run(['meson', 'setup', build, src] + options)
        run(['meson', 'compile', '-C', build])
        if name == 'hexagonrpc':
            run(['meson', 'test', '-C', build, '--print-errorlogs'])
            record['tests'] = 'upstream tests and registry-write test passed'
        elif name == 'libssc':
            try:
                probe = socket.socket(socket.AF_QIPCRTR, socket.SOCK_DGRAM)
            except OSError as exc:
                record['tests'] = 'not run: build host has no QRTR socket: ' + str(exc)
            else:
                probe.close()
                run(['meson', 'test', '-C', build, '--print-errorlogs', 'tests-light'])
                record['tests'] = 'mocked light-sensor test passed'
        else:
            record['tests'] = 'compile only; hardware and D-Bus lifecycle pending'
        # Needed by the next project; these paths belong to the disposable container.
        run(['meson', 'install', '-C', build])
        run(['ldconfig'])
        run(['meson', 'install', '-C', build, '--destdir', stage])
        run(['tar', '--exclude=.git', '--zstd', '-cf', artifacts / (name + '-source.tar.zst'),
             '-C', work, name])
        record['source_archive_sha256'] = sha(artifacts / (name + '-source.tar.zst'))
        results.append(record)
    for binary in ['usr/bin/hexagonrpcd', 'usr/bin/ssccli', 'usr/libexec/iio-sensor-proxy']:
        description = capture(['file', stage / binary])
        assert 'ARM aarch64' in description, description
        linked = capture(['ldd', stage / binary])
        assert 'not found' not in linked, linked
    # Never silently ship a copy built without SSC support.
    linked = capture(['ldd', stage / 'usr/libexec/iio-sensor-proxy'])
    assert 'libssc.so' in linked, linked
    run(['tar', '--zstd', '-cf', artifacts / 'sensors-rootfs.tar.zst', '-C', stage, '.'])
    manifest = {
        'recipe_commit': recipe,
        'hardware_tested': False,
        'private_firmware_included': False,
        'components': results,
        'rootfs_sha256': sha(artifacts / 'sensors-rootfs.tar.zst'),
        'packages': capture(['dpkg-query', '-W', '-f=${Package} ${Version}\n']),
    }
    (artifacts / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    shutil.copy2(ROOT / 'configs/sensors/source.json', artifacts / 'source.json')
    (artifacts / 'SHA256SUMS').write_text(''.join(
        f'{sha(p)}  {p.name}\n' for p in sorted(artifacts.iterdir()) if p.is_file()
    ))


if __name__ == '__main__':
    main()
