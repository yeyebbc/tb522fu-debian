#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Build the pinned RAM, disk-test or installed kernel without device access."""
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import os
import platform
import re
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
    parser.add_argument('--profile', choices=['ram', 'disk-test', 'installed'], default='ram')
    parser.add_argument('--jobs', type=int, default=os.cpu_count() or 2)
    args = parser.parse_args()
    disk = args.profile != 'ram'
    # Actions containers can mount the checkout with a different owner. Trust
    # only this explicitly selected recipe checkout, and validate before build.
    recipe_commit = capture(['git', '-c', f'safe.directory={ROOT}', '-C', ROOT,
                             'rev-parse', 'HEAD'])
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
    required = {'grep', 'sed', 'dirname', 'umount', 'sync', 'sh', 'mount', 'mkdir', 'mdev', 'blockdev', 'ip', 'udhcpd', 'telnetd',
                'setsid', 'sleep', 'seq', 'cat', 'ls', 'ln', 'reboot', 'poweroff', 'dmesg', 'stty',
                'wget', 'sha256sum', 'tar', 'losetup', 'switch_root', 'cut', 'awk', 'mv', 'killall', 'touch', 'readlink', 'modprobe'}
    assert required <= applets, required - applets
    scripts = ['ram-probe-init', 'ram-desktop-prepare', 'ram-storage-probe']
    if disk:
        scripts += ['disk-init', 'disk-root-prepare']
    for script in scripts:
        run(launcher + [args.busybox, 'sh', '-n', ROOT / 'configs' / script])
    init = (ROOT / 'configs/ram-probe-init').read_text()
    assert [s.strip() for s in init.splitlines() if s.strip().startswith('reboot ')] == ['reboot -f -n']
    assert 'poweroff -f -n' in init and 'probe_edl_ready' in init
    init_script = 'disk-init' if disk else 'ram-probe-init'
    identity = work / 'probe-id'
    identity.write_text('tb522fu-ci-ram-probe\n')
    cpio_spec = [f'dir /{d} 0755 0 0' for d in ['bin','sbin','dev','proc','sys','etc','run','tmp','root']]
    cpio_spec += ['nod /dev/console 0600 0 0 c 5 1', 'nod /dev/null 0666 0 0 c 1 3',
                 f'file /bin/busybox {args.busybox.resolve()} 0755 0 0',
                 f'file /init {ROOT / "configs" / init_script} 0755 0 0',
                 f'file /bin/ram-desktop-prepare {ROOT / "configs/ram-desktop-prepare"} 0755 0 0',
                 f'file /bin/ram-storage-probe {ROOT / "configs/ram-storage-probe"} 0755 0 0',
                 f'file /etc/udhcpd.conf {ROOT / "configs/udhcpd.conf"} 0644 0 0',
                 f'file /etc/port-device-id {identity} 0644 0 0']
    cpio_spec += [f'slink /bin/{a} busybox 0777 0 0' for a in sorted(applets) if a != 'busybox']
    if disk:
        profile_file = work / 'boot-profile'
        profile_file.write_text(args.profile + '\n')
        cpio_spec += [f'dir /{d} 0755 0 0' for d in ['lib', 'usr', 'usr/lib']]
        cpio_spec += [f'file /etc/boot-profile {profile_file} 0644 0 0',
                      f'file /bin/disk-root-prepare {ROOT / "configs/disk-root-prepare"} 0755 0 0',
                      'slink /lib/modules /usr/lib/modules 0777 0 0']
        assert not cross, 'Disk profiles require native ARM64 CI for e2fsck libraries'
        checker = Path(capture(['sh', '-c', 'command -v e2fsck'])).resolve()
        libraries = re.findall(r'(/[^\s()]+)', capture(['ldd', checker]))
        copied_dirs = {'/lib', '/usr', '/usr/lib', '/sbin'}
        for library in sorted(set(libraries)):
            lib = Path(library)
            for parent in reversed(lib.parents):
                if str(parent) == '/' or str(parent) in copied_dirs:
                    continue
                cpio_spec.append(f'dir {parent} 0755 0 0')
                copied_dirs.add(str(parent))
            cpio_spec.append(f'file {lib} {lib.resolve()} 0755 0 0')
        cpio_spec.append(f'file /sbin/e2fsck {checker} 0755 0 0')
    (work / 'cpio.spec').write_text('\n'.join(cpio_spec) + '\n')
    cpio = work / 'initramfs.cpio'
    with cpio.open('wb') as stream:
        run([gen_cpio, '-t', epoch, work / 'cpio.spec'], stdout=stream)
    run([source / 'scripts/kconfig/merge_config.sh', '-m', '-O', out, out / '.config',
         source / 'arch/arm64/configs/y900-display.fragment', ROOT / 'configs/ram-probe.fragment'], cwd=source)
    run([source / 'scripts/config', '--file', out / '.config', '--set-str', 'INITRAMFS_SOURCE', cpio])
    number = os.environ.get('GITHUB_RUN_NUMBER', '0')
    assert number.isdigit()
    # A stable config avoids invalidating every ccache direct-mode key. The
    # command-line suffix keeps each build/profile ABI uniquely identifiable.
    run([source / 'scripts/config', '--file', out / '.config', '--set-str', 'LOCALVERSION',
         '-tb522fu'])
    make.append('LOCALVERSION=-' + args.profile + '-ci' + number)
    if disk:
        fragment = (ROOT / 'configs/ram-probe.fragment').read_text()
        cmdline = re.search(r'^CONFIG_CMDLINE="(.*)"$', fragment, re.M)[1]
        if args.profile == 'disk-test':
            cmdline = cmdline.replace('probe_seconds=600', 'probe_seconds=900')
        else:
            cmdline = cmdline.replace(' qcom_scm.probe_edl_return=1', '')
            cmdline = cmdline.replace(' qcom_scm.probe_seconds=600', '')
            # CI19 verified keyboard coldplug; bounded profiles retain its
            # explicit load. CI20 verified ADSP, which now coldplugs in all
            # profiles so the bounded profile can test its startup ordering.
            cmdline = cmdline.replace('modprobe.blacklist=lenovo_yoga_keyboard,',
                                      'modprobe.blacklist=')
        run([source / 'scripts/config', '--file', out / '.config', '--set-str', 'CMDLINE', cmdline])
    run(make + ['olddefconfig'])
    config = (out / '.config').read_text().splitlines()
    for setting in ['CONFIG_Y900_ACM_DIAG_DTB=y', 'CONFIG_INITRAMFS_FORCE=y',
                    'CONFIG_CMDLINE_FORCE=y', 'CONFIG_PANIC_TIMEOUT=5',
                    'CONFIG_DEBUG_INFO_NONE=y', 'CONFIG_USB_CONFIGFS=y',
                    'CONFIG_DRM_SIMPLEDRM=y', 'CONFIG_DRM=y', 'CONFIG_FONT_TER16x32=y', 'CONFIG_DEBUG_FS=y',
                    'CONFIG_OVERLAY_FS=y', 'CONFIG_SQUASHFS=y', 'CONFIG_SQUASHFS_ZLIB=y',
                    'CONFIG_SCSI_UFS_QCOM=m', 'CONFIG_PHY_QCOM_QMP_UFS=m',
                    'CONFIG_SPI_QCOM_GENI=m', 'CONFIG_QCOM_GPI_DMA=m', 'CONFIG_TOUCHSCREEN_NT36536_SPI=m',
                    'CONFIG_SERIAL_DEV_BUS=y', 'CONFIG_SERIAL_DEV_CTRL_TTYPORT=y',
                    'CONFIG_INPUT_LENOVO_YOGA_KEYBOARD=m',
                    'CONFIG_PCIE_QCOM=y', 'CONFIG_PHY_QCOM_QMP_PCIE=y',
                    'CONFIG_POWER_SEQUENCING=y', 'CONFIG_POWER_SEQUENCING_QCOM_WCN=m',
                    'CONFIG_PCI_PWRCTRL_PWRSEQ=m', 'CONFIG_ATH12K=m',
                    'CONFIG_ATH12K_DEBUG=y', 'CONFIG_ATH12K_DEBUGFS=y',
                    'CONFIG_QCOM_Q6V5_PAS=m', 'CONFIG_RPMSG_QCOM_GLINK_SMEM=m',
                    'CONFIG_QRTR_SMD=m', 'CONFIG_QCOM_PD_MAPPER=m', 'CONFIG_BATTERY_QCOM_BATTMGR=m',
                    'CONFIG_DETECT_HUNG_TASK=y', 'CONFIG_SOFTLOCKUP_DETECTOR=y',
                    'CONFIG_USB_CONFIGFS_NCM=y', 'CONFIG_USB_CONFIGFS_ACM=y',
                    'CONFIG_PHY_QCOM_M31_EUSB=y', 'CONFIG_PHY_QCOM_EUSB2_REPEATER=y',
                    'CONFIG_SM_TCSRCC_8750=y', 'CONFIG_SM_GCC_8750=y',
                    'CONFIG_QCOM_CLK_RPMH=y', 'CONFIG_QCOM_RPMHPD=y',
                    'CONFIG_QCOM_AOSS_QMP=y', 'CONFIG_QCOM_COMMAND_DB=y',
                    'CONFIG_REGULATOR_QCOM_RPMH=y', 'CONFIG_REGULATOR_FIXED_VOLTAGE=y',
                    'CONFIG_SPMI_MSM_PMIC_ARB=y', 'CONFIG_MFD_SPMI_PMIC=y',
                    'CONFIG_QCOM_PDC=y', 'CONFIG_ARM_SMMU=y', 'CONFIG_ARM_SMMU_QCOM=y',
                    'CONFIG_INTERCONNECT_QCOM_SM8750=y', 'CONFIG_USB_DWC3_QCOM=y']:
        assert setting in config, setting
    assert 'CONFIG_QCOM_SCM=y' in config
    # PMIC coldplug must not replace Debian's saved time with its raw counter.
    assert '# CONFIG_RTC_HCTOSYS is not set' in config
    assert '# CONFIG_RTC_SYSTOHC is not set' in config
    cmdline = next(s for s in config if s.startswith('CONFIG_CMDLINE='))
    assert ('qcom_scm.probe_edl_return=1' in cmdline) == (args.profile != 'installed')
    assert ('modprobe.blacklist=lenovo_yoga_keyboard' in cmdline) == (args.profile != 'installed')
    blocked = {name for value in re.findall(r'modprobe.blacklist=([^ \"]+)', cmdline)
               for name in value.split(',')}
    assert 'qcom_q6v5_pas' not in blocked
    assert {'pwrseq_qcom_wcn', 'pci_pwrctrl_pwrseq', 'ath12k', 'ath12k_wifi7'} <= blocked
    if disk:
        assert 'CONFIG_EXT4_FS=y' in config
    run(make + [spec['board_dtb']])
    dtb = out / 'arch/arm64/boot/dts' / spec['board_dtb']
    uart = '/soc@0/geniqup@8c0000/serial@89c000'
    assert capture(['fdtget', '-t', 's', dtb, '/aliases', 'serial0']) == uart
    assert capture(['fdtget', '-t', 's', dtb, uart, 'status']) == 'okay'
    assert capture(['fdtget', '-t', 's', dtb, uart + '/keyboard', 'compatible']) == 'lenovo,tb522fu-keyboard'
    # Check the encoded GPIO number/polarity rather than unstable phandles.
    for prop, gpio, active_low in [('vcc3-enable-gpios', 105, 0), ('vcc5-enable-gpios', 106, 0),
                                  ('ocp-enable-gpios', 110, 0), ('mode-gpios', 42, 0),
                                  ('tx-enable-gpios', 60, 0), ('detect-gpios', 43, 1),
                                  ('lid-gpios', 11, 1)]:
        cells = capture(['fdtget', '-t', 'i', dtb, uart + '/keyboard', prop]).split()
        assert len(cells) == 3 and list(map(int, cells[1:])) == [gpio, active_low], prop
    for node, prop, typ, expected in [
        ('/soc@0/remoteproc@6800000', 'status', 's', 'okay'),
        ('/soc@0/remoteproc@6800000', 'firmware-name', 's',
         'qcom/sm8750/lenovo/tb522fu/adsp.mdt qcom/sm8750/lenovo/tb522fu/adsp_dtb.mdt'),
        ('/reserved-memory/adspslpi@9ee00000', 'reg', 'x', '0 9ee00000 0 5600000'),
        ('/reserved-memory/q6-adsp-dtb@9ed80000', 'reg', 'x', '0 9ed80000 0 80000'),
        ('/soc@0/remoteproc@6800000/glink-edge/fastrpc', 'status', 's', 'disabled'),
        ('/soc@0/remoteproc@6800000/glink-edge/gpr', 'status', 's', 'disabled'),
    ]:
        assert capture(['fdtget', '-t', typ, dtb, node, prop]) == expected, (node, prop)
    # The radio remains blocked from coldplug until the first bounded test.
    wifi = '/soc@0/pcie@1c00000/pcie@0/wifi@0'
    assert capture(['fdtget', '-t', 's', dtb, wifi, 'compatible']) == 'pci17cb,110e'
    assert capture(['fdtget', '-t', 's', dtb, '/wcn7861-pmu', 'compatible']) == 'qcom,wcn7861-pmu'
    assert capture(['fdtget', '-t', 's', dtb, '/soc@0/phy@1c06000', 'status']) == 'okay'
    pmu = '/wcn7861-pmu'
    assert capture(['fdtget', '-t', 's', dtb, pmu, 'qcom,vreg-pdc-map']) == 's5f:rf s4d:bb s3g:rf s7i:rf'
    assert capture(['fdtget', '-t', 's', dtb, pmu, 'qcom,pmu-vreg-map']) == (
        'VDDD_AON_0P9:s5f VDDA_RFA_1P9:s3g VDDA_RFA_1P3:s7i VDDA_RFA_0P9:s5f '
        'VDDD_WLMX_0P9:s4d VDDD_WLCX_0P9:s5f VDDD_BTCX_0P9:s5f VDDD_BTCMX_0P9:s5f '
        'VDDA_PCIE_1P2:s7i VDDA_PCIE_0P9:s7i')
    assert capture(['fdtget', '-t', 'x', dtb, pmu, 'vdd-supply']) == capture(
        ['fdtget', '-t', 'x', dtb, pmu, 'vdddig-supply'])
    for node, prop, expected in [
        ('/wcn7861-pmu', 'wlan-enable-gpios', [16, 0]),
        ('/soc@0/pcie@1c00000/pcie@0', 'reset-gpios', [102, 1]),
        ('/soc@0/pcie@1c00000/pcie@0', 'wake-gpios', [104, 1]),
    ]:
        cells = list(map(int, capture(['fdtget', '-t', 'i', dtb, node, prop]).split()))
        assert len(cells) == 3 and cells[1:] == expected, (node, prop)
    iommu = capture(['fdtget', '-t', 'x', dtb, '/soc@0/pcie@1c00000', 'iommu-map']).split()
    assert len(iommu) == 10 and iommu[2:5] == ['1400', '0', '1'] and iommu[7:] == ['1401', '0', '1']
    run(make + ['Image', 'modules'])
    modules = work / 'modules'
    run(make + ['modules_install', f'INSTALL_MOD_PATH={modules}', 'INSTALL_MOD_STRIP=1'])
    release = (out / 'include/config/kernel.release').read_text().strip()
    assert release.endswith('-' + args.profile + '-ci' + number) and '+' not in release
    installed = modules / 'lib/modules' / release
    # Check names against the built modules; Kconfig symbols are not filenames.
    explicit = set(re.findall(r'^blacklist ([\w-]+)$',
                             (ROOT / 'configs/ram-desktop-prepare').read_text(), re.M))
    explicit.update(re.findall(r'^modprobe -v ([\w-]+)$',
                               (ROOT / 'configs/ram-storage-probe').read_text(), re.M))
    explicit.update(['lenovo_yoga_keyboard', 'qcom_q6v5_pas', 'qcom_glink_smem',
                     'qrtr_smd', 'qcom_pd_mapper', 'qcom_battmgr',
                     'pwrseq_qcom_wcn', 'pci_pwrctrl_pwrseq', 'ath12k', 'ath12k_wifi7'])
    for name in sorted(explicit):
        actual = capture(['modinfo', '-b', modules, '-k', release, '-F', 'name', name])
        assert actual.replace('-', '_') == name.replace('-', '_'), (name, actual)
    for name in ['build', 'source']:
        (installed / name).unlink(missing_ok=True)
    # Debian is usr-merged; keep the archive independent of its /lib symlink.
    (modules / 'usr/lib').mkdir(parents=True)
    (modules / 'lib/modules').rename(modules / 'usr/lib/modules')
    run(['tar', '-czf', target / 'modules.tar.gz', '-C', modules, 'usr/lib/modules'])
    if disk:
        cpio_spec.append(f'file /modules.tar.gz {target / "modules.tar.gz"} 0644 0 0')
        (work / 'cpio.spec').write_text('\n'.join(cpio_spec) + '\n')
        with cpio.open('wb') as stream:
            run([gen_cpio, '-t', epoch, work / 'cpio.spec'], stdout=stream)
        # Only initramfs and final link change; module ABI/config are unchanged.
        run(make + ['Image'])
    image = out / 'arch/arm64/boot/Image'
    dtb = out / 'arch/arm64/boot/dts' / spec['board_dtb']
    data = image.read_bytes()
    assert len(data) < 94 * 1024**2, 'Kernel/initramfs must leave room in boot_b'
    assert data[0x38:0x3c] == b'ARMd' and dtb.read_bytes() in data
    for path, name in [(image, 'Image'), (dtb, 'mainline-board.dtb'),
                       (out / '.config', 'kernel.config'),
                       (out / 'include/config/kernel.release', 'kernel.release'),
                       (cpio, 'initramfs.cpio')]:
        shutil.copy2(path, target / name)
    (target / 'initramfs.cpio.gz').write_bytes(gzip.compress(cpio.read_bytes(), mtime=0))
    shutil.copy2(ROOT / 'kernel/source.json', target / 'source.json')
    recipe_files = ['configs/' + s for s in scripts] + [
        'configs/ram-probe.fragment', 'configs/udhcpd.conf', 'scripts/build-kernel.py']
    seconds = 900 if args.profile == 'disk-test' else 600
    manifest = {'profile': args.profile, 'source': spec, 'compiler': capture([compiler, '--version']).splitlines()[0],
                'recipe_commit': recipe_commit,
                'recipe_sha256': {p: sha(ROOT / p) for p in recipe_files},
                'source_date_epoch': int(epoch), 'gadget_serial': identity.read_text().strip(),
                'busybox_sha256': sha(args.busybox),
                'patch_sha256': {p: sha(ROOT / p) for p in spec['applied_patches']},
                'hardware_tested': False,
                'return_mode': ('normal restart; no test timer' if args.profile == 'installed' else
                    f'EDL; kernel timer {seconds} seconds from SCM readiness; host stock restore required'),
                'test_stage': 'ram-desktop' if args.profile == 'ram' else args.profile,
                'files': {p.name: {'bytes': p.stat().st_size, 'sha256': sha(p)}
                          for p in target.iterdir() if p.is_file()}}
    (target / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (target / 'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in sorted(target.iterdir()) if p.is_file()))
    run(['tar', '--exclude=.git', '-I', 'zstd -3 -T0', '-cf', ROOT / 'artifacts/kernel-source.tar.zst', '-C', source, '.'])
    run(['ccache', '--show-stats'])
    print('Kernel and source artifacts:', target)


if __name__ == '__main__':
    main()
