#!/usr/bin/env python3
"""Build the board-scoped ARM64 display-power adapter and support overlay."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'device/display-power'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--cc', default='aarch64-linux-gnu-gcc')
    a = p.parse_args()
    out = a.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    tree = out / 'tree'
    files = {}

    def copy(name, target, executable=False):
        dest = tree / target
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SOURCE / name, dest)
        dest.chmod(0o755 if executable else 0o644)
        files[target] = hashlib.sha256(dest.read_bytes()).hexdigest()

    library = tree / 'usr/lib/tb522fu/display-power/gsd-backlight-compat.so'
    library.parent.mkdir(parents=True)
    subprocess.run([a.cc, '-shared', '-fPIC', '-O2', '-Wall', '-Wextra', '-Werror',
                    '-Wl,-z,relro,-z,now,-z,noexecstack',
                    '-o', str(library), str(SOURCE / 'gsd-backlight-compat.c')], check=True)
    library.chmod(0o755)
    elf = subprocess.check_output(['readelf', '-h', str(library)], text=True)
    assert 'AArch64' in elf and 'DYN (Shared object file)' in elf
    symbols = subprocess.check_output(['readelf', '--dyn-syms', '--wide', str(library)], text=True)
    assert 'gsd_display_config_set_power_save_mode' in symbols
    files[str(library.relative_to(tree))] = hashlib.sha256(library.read_bytes()).hexdigest()
    for name in ['tb522fu-display-power', 'tb522fu-display-power-mode', 'tb522fu-display-powerctl']:
        compile((SOURCE / name).read_text(), str(SOURCE / name), 'exec')
        copy(name, 'usr/sbin/' + name, True)
    for name in ['tb522fu-display-power.service', 'tb522fu-display-power.socket']:
        copy(name, 'usr/lib/systemd/system/' + name)
    copy('80-tb522fu-backlight.conf', 'usr/lib/systemd/user/org.gnome.SettingsDaemon.Power.service.d/80-tb522fu-backlight.conf')
    copy('81-tb522fu-display-power.rules', 'usr/lib/udev/rules.d/81-tb522fu-display-power.rules')
    enabled = tree / 'etc/systemd/system/sockets.target.wants/tb522fu-display-power.socket'
    enabled.parent.mkdir(parents=True)
    enabled.symlink_to('/usr/lib/systemd/system/tb522fu-display-power.socket')
    inputs = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(SOURCE.iterdir()) if p.is_file()}
    git = ['git', '-c', 'safe.directory=' + str(ROOT), '-C', str(ROOT)]
    recipe = subprocess.check_output(git + ['rev-parse', 'HEAD'], text=True).strip()
    manifest = dict(architecture='aarch64', source_commit=recipe, source_inputs=inputs,
                    files=files, symlinks={str(enabled.relative_to(tree)): os.readlink(enabled)},
                    compiler=subprocess.check_output([a.cc, '--version'], text=True).splitlines()[0],
                    source_repository='https://github.com/yzddmr6/onepluspad-2pro-mainline',
                    source_pin='a82cd442c5e4c1e460bfc65483d4344698ced62a',
                    hardware_tested=False, system_suspend_enabled=False)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    epoch = int(subprocess.check_output(git + ['show', '-s', '--format=%ct', 'HEAD'], text=True))
    def normalize(info):
        info.uid = info.gid = 0
        info.uname = info.gname = ''
        info.mtime = epoch
        if info.isdir():
            info.mode = 0o755
        return info
    with tarfile.open(out / 'display-power.tar', 'w') as archive:
        for child in sorted(tree.iterdir()):
            archive.add(child, arcname=child.name, filter=normalize)
    (out / 'SHA256SUMS').write_text(''.join(
        hashlib.sha256((out / name).read_bytes()).hexdigest() + '  ' + name + '\n'
        for name in ['display-power.tar', 'manifest.json']))
    print(json.dumps(dict(output=str(out), files=len(files),
                          archive_sha256=hashlib.sha256((out / 'display-power.tar').read_bytes()).hexdigest())))


if __name__ == '__main__':
    main()
