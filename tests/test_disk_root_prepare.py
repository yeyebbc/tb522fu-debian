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


def exercise(profile='disk-test', fault=None):
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
                link('/sys/class/block/sda17', part)
                put('/dev/sda17')
        # A failed mount leaves only the empty mountpoint created by the script.
        if fault != 'mount-failure':
            put('/newroot/etc/tb522fu/board', 'lenovo-tb522fu')
            put('/newroot/etc/tb522fu/root-partuuid', UUID)
            put('/newroot/usr/lib/modules/' + release + '/modules.dep', 'fixture')
            put('/newroot/sbin/init').chmod(0o755)
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
'''
        for name in ('modprobe', 'mdev', 'blockdev', 'mount', 'umount', 'readlink', 'e2fsck'):
            path = bins / name
            path.write_text(wrapper)
            path.chmod(0o755)
        script = re.sub(r'(?<![\w])/(sys|dev|proc|newroot|lib|run|bin|sbin|etc)(?=/|[\n\": ])',
                        lambda m: str(root) + m[0], SOURCE)
        script = re.sub(r'^export PATH=.*$', 'export PATH=' + str(bins) + ':/usr/bin:/bin',
                        script, flags=re.M)
        script = script.replace('[ -b "$dev" ]', '[ -f "$dev" ]')
        script = script.replace(str(root) + '/sbin/e2fsck', str(bins / 'e2fsck'))
        path = root / 'script'
        path.write_text(script)
        result = subprocess.run(['/bin/sh', str(path)], capture_output=True, text=True,
                                env={**os.environ, 'TRACE': str(trace), 'FIXTURE': str(root),
                                     'FAULT': fault or ''}, timeout=15)
        calls = [json.loads(s) for s in trace.read_text().splitlines()] if trace.exists() else []
        writes = [s for s in calls if s[0] == 'e2fsck' or
                  (s[0] == 'blockdev' and s[1] == '--setrw') or (s[0] == 'mount' and 'rw' in s)]
        return result, writes, (root / 'newroot').exists()


class RootGuardTests(unittest.TestCase):
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
