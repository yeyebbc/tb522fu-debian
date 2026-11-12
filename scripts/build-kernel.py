#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Build the pinned USB-only kernel without accessing a device."""
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import os
import platform
import shutil
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def run(args, **kwargs):
    return subprocess.run([str(x) for x in args], check=True, **kwargs)


def capture(args):
    return subprocess.check_output([str(x) for x in args], text=True).strip()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--busybox', type=Path, default=Path('/usr/bin/busybox'))
    parser.add_argument('--jobs', type=int, default=os.cpu_count() or 2)
    args = parser.parse_args()
    spec = json.loads((ROOT / 'kernel/source.json').read_text())
    work = ROOT / 'work'
    source = work / 'kernel'
    out = work / 'kernel-out'
    target = ROOT / 'artifacts/kernel'
    work.mkdir(exist_ok=True)
    target.mkdir(parents=True, exist_ok=True)
    assert not (target / 'manifest.json').exists(), 'Preserve existing artifacts before rebuilding'
    if not source.exists():
        run(['git', 'init', source])
        run(['git', '-C', source, 'remote', 'add', 'origin', spec['repository']])
        run(['git', '-C', source, 'fetch', '--depth=1', 'origin', spec['commit']])
        run(['git', '-C', source, 'checkout', '--detach', 'FETCH_HEAD'])
    assert capture(['git', '-C', source, 'rev-parse', 'HEAD']) == spec['commit']
    assert not capture(['git', '-C', source, 'status', '--porcelain']), 'Source checkout must be clean'
    for patch in spec['applied_patches']:
        run(['git', '-C', source, 'apply', '--check', ROOT / patch])
        run(['git', '-C', source, 'apply', ROOT / patch])
    epoch = capture(['git', '-C', source, 'show', '-s', '--format=%ct', 'HEAD'])
    os.environ.update(SOURCE_DATE_EPOCH=epoch, KBUILD_BUILD_TIMESTAMP='@' + epoch,
                      KBUILD_BUILD_USER='builder', KBUILD_BUILD_HOST='tb522fu-ci',
                      KBUILD_BUILD_VERSION='1', CCACHE_DIR=str(ROOT / '.ccache'))
    cross = '' if platform.machine() in ['aarch64', 'arm64'] else 'aarch64-linux-gnu-'
    compiler = cross + 'gcc'
    run(['ccache', '--max-size=2G'])
    run(['ccache', '--zero-stats'])
    make = ['make', '-C', source, f'O={out}', 'ARCH=arm64', f'CROSS_COMPILE={cross}',
            f'CC=ccache {compiler}', f'-j{args.jobs}']
    run(make + ['defconfig'])
    # gen_init_cpio is a standalone host program, not a top-level make target.
    gen_cpio = work / 'gen_init_cpio'
    run(['cc', '-O2', '-Wall', source / 'usr/gen_init_cpio.c', '-o', gen_cpio])

    binary = args.busybox.read_bytes()
    assert binary[:4] == b'\x7fELF' and struct.unpack_from('<H', binary, 18)[0] == 183, 'BusyBox must be ARM64'
    launcher = []
    if cross:
        emulator = shutil.which('qemu-aarch64-static') or shutil.which('qemu-aarch64')
        assert emulator, 'qemu-user is needed to validate ARM64 BusyBox on x86_64'
        launcher = [emulator]
    applets = set(capture(launcher + [args.busybox, '--list']).split())
    required = {'sh', 'mount', 'mkdir', 'mdev', 'blockdev', 'ip', 'udhcpd', 'telnetd',
                'setsid', 'cttyhack', 'sleep', 'seq', 'cat', 'ln', 'reboot', 'dmesg', 'stty'}
    assert required <= applets, required - applets
    run(launcher + [args.busybox, 'sh', '-n', ROOT / 'configs/ram-probe-init'])
    init = (ROOT / 'configs/ram-probe-init').read_text()
    assert [s.strip() for s in init.splitlines() if s.strip().startswith('reboot ')] == ['reboot -f -n'] * 2
    identity = work / 'probe-id'
    identity.write_text('tb522fu-ci-ram-probe\n')
    cpio_spec = [f'dir /{d} 0755 0 0' for d in ['bin','sbin','dev','proc','sys','etc','run','tmp','root']]
    cpio_spec += ['nod /dev/console 0600 0 0 c 5 1', 'nod /dev/null 0666 0 0 c 1 3',
                 f'file /bin/busybox {args.busybox.resolve()} 0755 0 0',
                 f'file /init {ROOT / "configs/ram-probe-init"} 0755 0 0',
                 f'file /etc/udhcpd.conf {ROOT / "configs/udhcpd.conf"} 0644 0 0',
                 f'file /etc/port-device-id {identity} 0644 0 0']
    cpio_spec += [f'slink /bin/{a} busybox 0777 0 0' for a in sorted(applets) if a != 'busybox']
    (work / 'cpio.spec').write_text('\n'.join(cpio_spec) + '\n')
    cpio = work / 'initramfs.cpio'
    with cpio.open('wb') as stream:
        run([gen_cpio, '-t', epoch, work / 'cpio.spec'], stdout=stream)
    run([source / 'scripts/kconfig/merge_config.sh', '-m', '-O', out, out / '.config',
         source / 'arch/arm64/configs/y900-display.fragment', ROOT / 'configs/ram-probe.fragment'], cwd=source)
    run([source / 'scripts/config', '--file', out / '.config', '--set-str', 'INITRAMFS_SOURCE', cpio])
    number = os.environ.get('GITHUB_RUN_NUMBER', '0')
    assert number.isdigit()
    run([source / 'scripts/config', '--file', out / '.config', '--set-str', 'LOCALVERSION',
         '-tb522fu-probe-ci' + number])
    run(make + ['olddefconfig'])
    config = (out / '.config').read_text().splitlines()
    for setting in ['CONFIG_Y900_ACM_DIAG_DTB=y', 'CONFIG_INITRAMFS_FORCE=y',
                    'CONFIG_CMDLINE_FORCE=y', 'CONFIG_PANIC_TIMEOUT=5',
                    'CONFIG_DEBUG_INFO_NONE=y', 'CONFIG_USB_CONFIGFS=y',
                    'CONFIG_DETECT_HUNG_TASK=y', 'CONFIG_SOFTLOCKUP_DETECTOR=y',
                    'CONFIG_USB_CONFIGFS_NCM=y', 'CONFIG_USB_CONFIGFS_ACM=y',
                    'CONFIG_PHY_QCOM_M31_EUSB=y', 'CONFIG_PHY_QCOM_EUSB2_REPEATER=y']:
        assert setting in config, setting
    run(make + [spec['board_dtb']])
    run(make + ['Image'])
    image = out / 'arch/arm64/boot/Image'
    dtb = out / 'arch/arm64/boot/dts' / spec['board_dtb']
    data = image.read_bytes()
    assert data[0x38:0x3c] == b'ARMd' and dtb.read_bytes() in data
    for path, name in [(image, 'Image'), (dtb, 'mainline-board.dtb'),
                       (out / '.config', 'kernel.config'),
                       (out / 'include/config/kernel.release', 'kernel.release'),
                       (cpio, 'initramfs.cpio')]:
        shutil.copy2(path, target / name)
    (target / 'initramfs.cpio.gz').write_bytes(gzip.compress(cpio.read_bytes(), mtime=0))
    shutil.copy2(ROOT / 'kernel/source.json', target / 'source.json')
    manifest = {'source': spec, 'compiler': capture([compiler, '--version']).splitlines()[0],
                'recipe_commit': capture(['git', '-C', ROOT, 'rev-parse', 'HEAD']),
                'recipe_sha256': {p: sha(ROOT / p) for p in ['configs/ram-probe-init',
                    'configs/ram-probe.fragment', 'configs/udhcpd.conf', 'scripts/build-kernel.py']},
                'source_date_epoch': int(epoch), 'gadget_serial': identity.read_text().strip(),
                'busybox_sha256': sha(args.busybox),
                'patch_sha256': {p: sha(ROOT / p) for p in spec['applied_patches']},
                'hardware_tested': False,
                'files': {p.name: {'bytes': p.stat().st_size, 'sha256': sha(p)}
                          for p in target.iterdir() if p.is_file()}}
    (target / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (target / 'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in sorted(target.iterdir()) if p.is_file()))
    run(['tar', '--exclude=.git', '-I', 'zstd -3 -T0', '-cf', ROOT / 'artifacts/kernel-source.tar.zst', '-C', source, '.'])
    run(['ccache', '--show-stats'])
    print('Kernel and source artifacts:', target)


if __name__ == '__main__':
    main()
