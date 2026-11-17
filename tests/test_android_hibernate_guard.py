# SPDX-License-Identifier: GPL-2.0-only
"""Run the real Android Action in a mock sysfs, without mounts/block devices."""
from pathlib import Path
import json
import os
import re
import struct
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'android-module/action.sh').read_text()
UUID = '00000000-1111-2222-3333-444444444444'


def exercise(size='511705088', fault=None):
    with tempfile.TemporaryDirectory(prefix='android-hibernate-') as temporary:
        root = Path(temporary)
        bins = root / 'mockbin'; bins.mkdir()
        trace = root / 'trace'
        def put(name, content):
            p = root / name.lstrip('/'); p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(content.encode() if isinstance(content, str) else content)
            return p
        disk = root / 'sys/devices/1d84000.ufshc/host0/target0:0:0/0:0:0:0/block/sda'
        disk.mkdir(parents=True)
        (disk / 'device').symlink_to(disk.parent.parent)
        (disk / 'queue').mkdir(); (disk / 'queue/logical_block_size').write_text('4096')
        put('/sys/class/block/.keep', '')
        for number, name, start, length in [(17, 'debian', '454096896', size),
                (18, 'debian-swap', '965801984', '25165824')]:
            if number == 18 and size == '536870912':
                continue
            p = disk / ('sda' + str(number)); p.mkdir()
            for key, value in [('partition', str(number)), ('start', start), ('size', length),
                    ('uevent', 'PARTNAME=' + name + '\nPARTUUID=' + UUID + '\n')]:
                (p/key).write_text(value)
            (root / 'sys/class/block' / p.name).symlink_to(p)
        header = bytearray(4096); header[-10:] = b'SWAPSPACE2'
        if fault == 'pending-image':
            header[-20:-10] = b'SWAPSPACE2'; header[-10:] = b'S1SUSPEND\0'
        elif fault == 'invalid-header':
            header[-10:] = bytes(10)
        elif fault == 'wrong-swap-start':
            (disk / 'sda18/start').write_text('965801976')
        elif fault == 'wrong-swap-size':
            (disk / 'sda18/size').write_text('33554432')
        elif fault == 'duplicate-swap':
            p = disk / 'sda19'; p.mkdir()
            (p / 'partition').write_text('19')
            (p / 'uevent').write_text('PARTNAME=debian-swap\n')
            (root / 'sys/class/block/sda19').symlink_to(p)
        put('/dev/block/sda18', header)
        fs = bytearray(4096)
        struct.pack_into('<HH', fs, 1080, 0xef53, 1)
        put('/dev/block/sda17', fs)
        mount = '/data/adb/tb522fu-debian-mount'
        put(mount + '/etc/tb522fu/root-partuuid', UUID)
        rotate = put(mount + '/usr/libexec/tb522fu-rotate-boot',
            '#!/bin/sh\nprintf "rotate\\n" >>"$TRACE"\n')
        rotate.chmod(0o755)
        wrapper = '''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
n = Path(sys.argv[0]).name
if n == 'id': print('0')
elif n == 'getprop': print({'ro.boot.slot_suffix':'_b', 'ro.boot.flash.locked':'0'}[sys.argv[1]])
else:
 with open(os.environ['TRACE'], 'a') as f: f.write(json.dumps([n, *sys.argv[1:]])+'\\n')
'''
        for name in ('id', 'getprop', 'mount', 'umount', 'reboot', 'sync'):
            p = bins / name; p.write_text(wrapper); p.chmod(0o755)
        script = re.sub(r'(?<![\w])/(sys|dev|data)(?=/|[\n\": ])',
                        lambda m: str(root) + m[0], SOURCE)
        script = script.replace('[ -b "$dev" ]', '[ -f "$dev" ]')
        script = script.replace('/system/bin/sh', '/bin/sh')
        script = script.replace('/system/bin/reboot', str(bins / 'reboot'))
        path = root / 'action'; path.write_text(script)
        result = subprocess.run(['/bin/sh', str(path)], text=True, capture_output=True,
            env={**os.environ, 'PATH':str(bins)+':/usr/bin:/bin', 'TRACE':str(trace)}, timeout=15)
        events = trace.read_text().splitlines() if trace.exists() else []
        return result, events


class AndroidResumeGuardTests(unittest.TestCase):
    def test_original_and_new_empty_swap_layout_can_boot(self):
        for size in ('536870912', '511705088'):
            with self.subTest(size=size):
                result, events = exercise(size=size)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('rotate', events)

    def test_pending_or_invalid_snapshot_prevents_every_mount_and_rotation(self):
        for fault in ('pending-image', 'invalid-header', 'wrong-swap-start',
                      'wrong-swap-size', 'duplicate-swap'):
            with self.subTest(fault=fault):
                result, events = exercise(fault=fault)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(events, [])

    def test_unknown_root_geometry_is_rejected(self):
        result, events = exercise(size='503316480')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(events, [])


if __name__ == '__main__':
    unittest.main()
