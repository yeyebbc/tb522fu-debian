# SPDX-License-Identifier: GPL-2.0-only
"""Exercise root selection without touching real block devices or mounts."""
from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest

SOURCE = (Path(__file__).resolve().parents[1] / 'configs/disk-root-prepare').read_text()
UUID = '00000000-1111-2222-3333-444444444444'


def exercise(profile='disk-test', fault=None, root_environment=None, swap_layout=False, fulltrace=False):
    with tempfile.TemporaryDirectory(prefix='root-guard-') as tmp:
        root = Path(tmp)
        bins = root / 'mockbin'
        bins.mkdir()
        trace = root / 'trace'
        def put(path, text=''):
            p = root / path.lstrip('/')
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)
            return p
        def link(path, target):
            p = root / path.lstrip('/')
            p.parent.mkdir(parents=True, exist_ok=True)
            p.symlink_to(target)
        release = subprocess.check_output(['uname', '-r'], text=True).strip()
        put('/lib/modules/' + release + '/modules.dep', 'fixture')
        put('/etc/boot-profile', profile)
        if root_environment is not None:
            put('/etc/root-environment', root_environment)
        put('/run/placeholder')
        put('/proc/1/exe')
        for n in range(6):
            name = 'sd' + chr(97 + n)
            scsi = root / f'sys/devices/1d84000.ufs/host0/target0:0:0/0:0:0:{n}'
            disk = scsi / 'block' / name
            disk.mkdir(parents=True)
            (disk / 'device').symlink_to(scsi)
            (disk / 'queue').mkdir()
            (disk / 'queue/logical_block_size').write_text('4096')
            link('/sys/class/block/' + name, disk)
            put('/dev/' + name)
            if n == 0:
                part = disk / 'sda17'
                part.mkdir()
                (part / 'partition').write_text('17')
                (part / 'uevent').write_text('PARTNAME=debian\nPARTUUID=' + UUID + '\n')
                (part / 'start').write_text('454096896')
                (part / 'size').write_text('536870912')
                if swap_layout:
                    (part / 'size').write_text('511705088')
                    swap = disk / 'sda18'
                    swap.mkdir()
                    (swap / 'partition').write_text('18')
                    (swap / 'uevent').write_text('PARTNAME=debian-swap\nPARTUUID=' + UUID + '\n')
                    (swap / 'start').write_text('965801984')
                    (swap / 'size').write_text('25165824')
                    link('/sys/class/block/sda18', swap)
                    put('/dev/sda18')
                    if fault == 'missing-swap':
                        (swap / 'uevent').write_text('PARTNAME=other\n')
                    elif fault == 'wrong-swap-size':
                        (swap / 'size').write_text('50331648')
                    elif fault == 'wrong-swap-start':
                        (swap / 'start').write_text('965801976')
                    elif fault == 'wrong-swap-index':
                        (swap / 'partition').write_text('19')
                link('/sys/class/block/sda17', part)
                put('/dev/sda17')
        # A failed mount leaves only the empty mountpoint created by the script.
        if fault != 'mount-failure':
            put('/newroot/etc/tb522fu/board', 'lenovo-tb522fu')
            put('/newroot/etc/tb522fu/root-partuuid', UUID)
            put('/newroot/usr/lib/modules/' + release + '/modules.dep', 'fixture')
            put('/newroot/sbin/init').chmod(0o755)
            if root_environment == 'ubuntu-test':
                trial = '/newroot/var/lib/tb522fu-dualboot/ubuntu-26.04.1-test/root'
                put(trial + '/etc/tb522fu/board', 'lenovo-tb522fu')
                put(trial + '/etc/tb522fu/root-partuuid', UUID)
                put(trial + '/etc/tb522fu/root-environment', 'ubuntu-test')
                put(trial + '/etc/tb522fu/ubuntu-trial-iso-sha256',
                    'c54d196489d3c867975fb3bbb72ca52ec2e137456e305481f81096304e4d2517')
                put(trial + '/etc/os-release', 'ID=ubuntu\nVERSION_ID="26.04"\n')
                put(trial + '/sbin/init').chmod(0o755)
                put(trial + '/usr/lib/modules/' + release + '/modules.dep', 'fixture')
                if fault == 'ubuntu-wrong-source':
                    put(trial + '/etc/tb522fu/ubuntu-trial-iso-sha256', 'wrong')
                elif fault == 'ubuntu-wrong-uuid':
                    put(trial + '/etc/tb522fu/root-partuuid', 'wrong')
                elif fault == 'ubuntu-wrong-distro':
                    put(trial + '/etc/os-release', 'ID=debian\nVERSION_ID="13"\n')
                elif fault == 'ubuntu-missing-modules':
                    shutil.rmtree(root / trial.lstrip('/') / 'usr/lib/modules')
                elif fault == 'ubuntu-symlink':
                    location = root / trial.lstrip('/')
                    location.rename(location.with_name('elsewhere'))
                    location.symlink_to('elsewhere', target_is_directory=True)
            if root_environment == 'fedora45-test':
                trial = '/newroot/var/lib/tb522fu-dualboot/fedora45-test/root'
                put(trial + '/etc/tb522fu/board', 'lenovo-tb522fu')
                put(trial + '/etc/tb522fu/root-partuuid', UUID)
                put(trial + '/etc/tb522fu/root-environment', 'fedora45-test')
                put(trial + '/etc/tb522fu/fedora45-trial-image-sha256',
                    '07ab3377cee9d4bbc15e7203214594f8cfdb58a9a57e195aa0ff183cf81ea0a8')
                put(trial + '/etc/os-release', 'ID=fedora\nVERSION_ID=45\n')
                put(trial + '/sbin/init').chmod(0o755)
                put(trial + '/usr/lib/modules/' + release + '/modules.dep', 'fixture')
                if fault == 'fedora-wrong-source':
                    put(trial + '/etc/tb522fu/fedora45-trial-image-sha256', 'wrong')
                elif fault == 'fedora-wrong-uuid':
                    put(trial + '/etc/tb522fu/root-partuuid', 'wrong')
                elif fault == 'fedora-wrong-environment':
                    put(trial + '/etc/tb522fu/root-environment', 'ubuntu-test')
                elif fault == 'fedora-wrong-version':
                    put(trial + '/etc/os-release', 'ID=fedora\nVERSION_ID=44\n')
                elif fault == 'fedora-wrong-distro':
                    put(trial + '/etc/os-release', 'ID=debian\nVERSION_ID="13"\n')
                elif fault == 'fedora-missing-modules':
                    shutil.rmtree(root / trial.lstrip('/') / 'usr/lib/modules')
                elif fault == 'fedora-symlink':
                    location = root / trial.lstrip('/')
                    location.rename(location.with_name('elsewhere'))
                    location.symlink_to('elsewhere', target_is_directory=True)
        if fault == 'wrong-board':
            put('/newroot/etc/tb522fu/board', 'another-board')
        elif fault == 'wrong-uuid':
            put('/newroot/etc/tb522fu/root-partuuid', 'other')
        elif fault == 'wrong-size':
            (root / 'sys/class/block/sda17/size').write_text('268435456')
        elif fault == 'wrong-start':
            (root / 'sys/class/block/sda17/start').write_text('454096888')
        elif fault == 'missing-modules':
            shutil.rmtree(root / 'newroot/usr/lib/modules')
        elif fault == 'missing-partition':
            (root / 'sys/class/block/sda17/uevent').write_text('PARTNAME=userdata\n')
        wrapper = '''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
name = Path(sys.argv[0]).name
with open(os.environ['TRACE'], 'a') as f:
    f.write(json.dumps([name, *sys.argv[1:]]) + '\\n')
if name == 'readlink':
    if sys.argv[-1].endswith('/proc/1/exe'):
        print(os.environ['FIXTURE'] + '/bin/busybox')
    else:
        os.execv('/usr/bin/readlink', ['readlink', *sys.argv[1:]])
if name == 'blockdev':
    state = Path(os.environ['FIXTURE']) / 'rw'
    if sys.argv[1] == '--setrw':
        state.touch()
    if sys.argv[1] == '--getro':
        print('0' if state.exists() else '1')
if name == 'mount' and os.environ.get('FAULT') == 'mount-failure':
    sys.exit(32)
if name == 'tb522fu-resume' and os.environ.get('FAULT') in ('snapshot-present', 'resume-returned'):
    sys.exit(3)
'''
        for name in ('modprobe', 'mdev', 'blockdev', 'mount', 'umount', 'readlink', 'e2fsck', 'tb522fu-resume'):
            path = bins / name
            path.write_text(wrapper)
            path.chmod(0o755)
        script = re.sub(r'(?<![\w])/(sys|dev|proc|newroot|lib|run|bin|sbin|etc)(?=/|[\n\": ])',
                        lambda m: str(root) + m[0], SOURCE)
        script = re.sub(r'^export PATH=.*$', 'export PATH=' + str(bins) + ':/usr/bin:/bin',
                        script, flags=re.M)
        script = script.replace('[ -b "$dev" ]', '[ -f "$dev" ]')
        script = script.replace(str(root) + '/sbin/e2fsck', str(bins / 'e2fsck'))
        script = script.replace(str(root) + '/sbin/tb522fu-resume', str(bins / 'tb522fu-resume'))
        path = root / 'script'
        path.write_text(script)
        result = subprocess.run(['/bin/sh', str(path)], capture_output=True, text=True,
                                env={**os.environ, 'TRACE': str(trace), 'FIXTURE': str(root),
                                     'FAULT': fault or ''}, timeout=15)
        calls = [json.loads(s) for s in trace.read_text().splitlines()] if trace.exists() else []
        writes = [s for s in calls if s[0] == 'e2fsck' or
                  (s[0] == 'blockdev' and s[1] == '--setrw') or
                  (s[0] == 'mount' and ('rw' in s or 'bind' in s))]
        return result, calls if fulltrace else writes, (root / 'newroot').exists()


class RootGuardTests(unittest.TestCase):
    def test_swap_inspection_precedes_every_mount_and_filesystem_check(self):
        result, calls, _ = exercise(swap_layout=True, fulltrace=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        inspected = next(i for i, c in enumerate(calls) if c[0] == 'tb522fu-resume')
        self.assertEqual(calls[inspected][1], 'inspect')
        for i, call in enumerate(calls):
            if call[0] in ('mount', 'e2fsck') or call[:2] == ['blockdev', '--setrw']:
                self.assertGreater(i, inspected)

    def test_only_installed_profile_can_attempt_restore(self):
        result, calls, _ = exercise(profile='installed', swap_layout=True, fulltrace=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(next(c for c in calls if c[0] == 'tb522fu-resume')[1], 'resume')

    def test_snapshot_or_failed_restore_stops_before_mount_or_fsck(self):
        for profile, fault in [('disk-test', 'snapshot-present'), ('installed', 'resume-returned')]:
            with self.subTest(profile=profile):
                result, calls, _ = exercise(profile=profile, fault=fault,
                                             swap_layout=True, fulltrace=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(any(c[0] in ('mount', 'e2fsck') or
                    c[:2] == ['blockdev', '--setrw'] for c in calls))

    def test_incomplete_swap_layout_fails_before_mount_or_write(self):
        for fault in ('missing-swap', 'wrong-swap-size', 'wrong-swap-start', 'wrong-swap-index'):
            with self.subTest(fault=fault):
                result, calls, _ = exercise(swap_layout=True, fault=fault, fulltrace=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(any(c[0] in ('mount', 'e2fsck', 'tb522fu-resume') or
                    c[:2] == ['blockdev', '--setrw'] for c in calls))

    def test_explicit_maintenance_never_mounts_even_a_healthy_root(self):
        for swap_layout in (False, True):
            with self.subTest(swap=swap_layout):
                result, calls, _ = exercise(root_environment='maintenance',
                                             swap_layout=swap_layout, fulltrace=True)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertFalse(any(c[0] in ('mount', 'e2fsck') or
                    c[:2] == ['blockdev', '--setrw'] for c in calls))

    def test_installed_cannot_enter_explicit_maintenance(self):
        result, calls, _ = exercise(profile='installed', root_environment='maintenance', fulltrace=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(any(c[0] in ('mount', 'e2fsck') for c in calls))

    def test_explicit_fedora_mode_mounts_its_separate_directory(self):
        result, writes, _ = exercise(root_environment='fedora45-test')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(writes[-2][1:5], ['-t', 'ext4', '-o', 'rw'])
        self.assertEqual(writes[-1][1:3], ['-o', 'bind'])
        self.assertTrue(writes[-1][-2].endswith(
            '/run/tb522fu-fedora45-store/var/lib/tb522fu-dualboot/fedora45-test/root'))

    def test_fedora_must_match_source_root_distro_and_modules_before_writes(self):
        for fault in ('fedora-wrong-source', 'fedora-wrong-uuid',
                      'fedora-wrong-environment', 'fedora-wrong-version',
                      'fedora-wrong-distro', 'fedora-missing-modules', 'fedora-symlink',
                      'wrong-board', 'wrong-uuid', 'wrong-size', 'wrong-start'):
            with self.subTest(fault=fault):
                result, writes, _ = exercise(root_environment='fedora45-test', fault=fault)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(writes, [])

    def test_fedora_is_not_an_installed_or_ram_root(self):
        for profile in ('installed', 'ram'):
            with self.subTest(profile=profile):
                result, writes, _ = exercise(profile=profile, root_environment='fedora45-test')
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(writes, [])
                built = subprocess.run(['python3', str(Path(__file__).resolve().parents[1] /
                    'scripts/build-kernel.py'), '--profile', profile,
                    '--root-environment', 'fedora45-test'], text=True, capture_output=True)
                self.assertNotEqual(built.returncode, 0)
                self.assertIn('bounded test profile', built.stderr)

    def test_explicit_ubuntu_mode_mounts_separate_directory(self):
        result, writes, _ = exercise(root_environment='ubuntu-test')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(writes[-2][1:5], ['-t', 'ext4', '-o', 'rw'])
        self.assertEqual(writes[-1][1:3], ['-o', 'bind'])
        self.assertTrue(writes[-1][-2].endswith(
            '/run/tb522fu-ubuntu-store/var/lib/tb522fu-dualboot/ubuntu-26.04.1-test/root'))

    def test_ubuntu_requires_exact_staged_identity_before_writes(self):
        for fault in ('ubuntu-wrong-source', 'ubuntu-wrong-uuid',
                      'ubuntu-wrong-distro', 'ubuntu-missing-modules', 'ubuntu-symlink'):
            with self.subTest(fault=fault):
                result, writes, _ = exercise(root_environment='ubuntu-test', fault=fault)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(writes, [])

    def test_installed_or_unknown_mode_cannot_select_ubuntu(self):
        for profile, mode in (('installed', 'ubuntu-test'), ('disk-test', 'unknown')):
            with self.subTest(profile=profile, mode=mode):
                result, writes, _ = exercise(profile=profile, root_environment=mode)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(writes, [])

    def test_valid_root_can_be_checked_and_mounted(self):
        result, writes, _ = exercise()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(writes), 4)

    def test_blank_partition_enters_bounded_maintenance_without_writes(self):
        result, writes, mountpoint = exercise(fault='mount-failure')
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(writes, [])
        self.assertFalse(mountpoint)

    def test_installed_profile_rejects_unmountable_root(self):
        result, writes, _ = exercise(profile='installed', fault='mount-failure')
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(writes, [])

    def test_wrong_identity_geometry_or_modules_never_enable_writes(self):
        for fault in ('wrong-board', 'wrong-uuid', 'wrong-size', 'wrong-start', 'missing-modules'):
            with self.subTest(fault=fault):
                result, writes, _ = exercise(fault=fault)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotEqual(result.returncode, 2)
                self.assertEqual(writes, [])

    def test_missing_partition_maintenance(self):
        result, writes, _ = exercise(fault='missing-partition')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(writes, [])


if __name__ == '__main__':
    unittest.main()
