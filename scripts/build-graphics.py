#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Build an isolated Mesa prefix and matching sources, without device access."""
from pathlib import Path
import hashlib
import json
import os
import platform
import shutil
import subprocess
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def run(args, **kw):
    return subprocess.run([str(x) for x in args], check=True, **kw)


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    assert platform.machine() == 'aarch64', 'Native hosted ARM64 build required'
    recipe = subprocess.check_output(['git', '-c', f'safe.directory={ROOT}',
                                      '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    spec = json.loads((ROOT / 'configs/graphics/source.json').read_text())
    work = ROOT / 'work/graphics'
    target = ROOT / 'artifacts/graphics'
    work.mkdir(parents=True, exist_ok=True)
    target.mkdir(parents=True, exist_ok=True)
    assert not (target / 'manifest.json').exists()
    archive = work / 'mesa.tar.xz'
    if not archive.exists():
        with urllib.request.urlopen(spec['archive'], timeout=120) as src, archive.open('xb') as dst:
            shutil.copyfileobj(src, dst)
    assert sha(archive) == spec['sha256']
    source = work / ('mesa-' + spec['version'])
    assert not source.exists(), 'Use a fresh source tree to avoid reapplying the patch'
    with tarfile.open(archive) as tar:
        tar.extractall(work, filter='data')
    patch = ROOT / spec['patch']
    run(['patch', '--batch', '--fuzz=0', '-p1', '-i', patch], cwd=source)
    table = (source / 'src/freedreno/common/freedreno_devices.py').read_text()
    assert table.count('chip_id=0xffff44050001') == 1
    prefix = spec['prefix']
    build = work / 'build'
    options = [
        '--prefix=' + prefix, '--libdir=lib/aarch64-linux-gnu',
        '--buildtype=debugoptimized', '--wrap-mode=nofallback',
        '-Db_ndebug=false', '-Doptimization=2', '-Dplatforms=x11,wayland',
        '-Dgallium-drivers=freedreno,llvmpipe,softpipe', '-Dvulkan-drivers=freedreno',
        '-Dfreedreno-kmds=msm', '-Dglvnd=enabled', '-Dglx=dri',
        '-Dshared-glapi=enabled', '-Degl=enabled', '-Dgbm=enabled',
        '-Dgles1=enabled', '-Dgles2=enabled', '-Dllvm=enabled',
        '-Dgallium-va=disabled', '-Dvideo-codecs=[]', '-Dvalgrind=disabled',
        '-Dbuild-tests=false',
    ]
    run(['meson', 'setup', build, source, *options])
    run(['meson', 'compile', '-C', build, '-j', str(os.cpu_count() or 2)])
    stage = work / 'root'
    run(['meson', 'install', '-C', build, '--destdir', stage])
    binary = stage / prefix.lstrip('/') / 'bin/tb522fu-gpu-check'
    binary.parent.mkdir(parents=True, exist_ok=True)
    flags = subprocess.check_output(['pkg-config', '--cflags', '--libs', 'egl', 'glesv2'], text=True).split()
    run(['cc', '-O2', '-Wall', '-Wextra', '-Werror', ROOT / 'configs/graphics/gpu-check.c', '-o', binary, *flags])
    library = stage / prefix.lstrip('/') / 'lib/aarch64-linux-gnu'
    env = dict(os.environ, LD_LIBRARY_PATH=str(library),
               LIBGL_DRIVERS_PATH=str(library / 'dri'), LIBGL_ALWAYS_SOFTWARE='1',
               GALLIUM_DRIVER='llvmpipe')
    negative = subprocess.run([str(binary)], env=env, capture_output=True, text=True, timeout=30)
    (target / 'software-negative-control.txt').write_text(negative.stdout + negative.stderr)
    assert negative.returncode == 3 and 'llvmpipe' in negative.stdout, negative.stdout + negative.stderr
    files = {}
    for p in sorted(stage.rglob('*')):
        if p.is_file() and not p.is_symlink():
            files[str(p.relative_to(stage))] = {'sha256': sha(p), 'bytes': p.stat().st_size}
    run(['tar', '--zstd', '-cf', target / 'graphics-rootfs.tar.zst', '-C', stage, '.'])
    run(['tar', '--zstd', '-cf', target / 'mesa-source.tar.zst', '-C', source, '.'])
    shutil.copy2(ROOT / 'configs/graphics/source.json', target / 'source.json')
    shutil.copy2(patch, target / patch.name)
    shutil.copy2(build / 'meson-info/intro-buildoptions.json', target / 'buildoptions.json')
    shutil.copy2(build / 'meson-logs/meson-log.txt', target / 'meson-log.txt')
    manifest = dict(recipe_commit=recipe, source=spec, patch_sha256=sha(patch),
                    meson_options=options, runtime_files=files,
                    hardware_tested=False,
                    artifacts={p.name: dict(sha256=sha(p), bytes=p.stat().st_size)
                               for p in target.iterdir() if p.is_file()})
    (target / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (target / 'SHA256SUMS').write_text(''.join(sha(p) + '  ' + p.name + '\n'
        for p in sorted(target.iterdir()) if p.is_file() and p.name != 'SHA256SUMS'))


if __name__ == '__main__':
    main()
