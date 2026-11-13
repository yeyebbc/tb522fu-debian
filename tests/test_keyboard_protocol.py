"""Check the actual new kernel framing code, extracted from its source patch."""
from pathlib import Path
import subprocess
import json
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class KeyboardCodecTests(unittest.TestCase):
    def test_wire_reports_bounds_and_resynchronization(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(['git', 'apply', '--include=drivers/input/misc/lenovo-yoga-keyboard-protocol.h',
                            str(ROOT / 'patches/0110-tb522fu-uart-keyboard.patch')],
                           cwd=root, check=True, capture_output=True)
            (root / 'harness.c').write_text((ROOT / 'tests/keyboard_protocol_harness.c').read_text())
            subprocess.run(['cc', '-std=gnu11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                            '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                            '-I' + str(root / 'drivers/input/misc'), str(root / 'harness.c'),
                            '-o', str(root / 'harness')], check=True, capture_output=True)
            fixtures = json.loads((ROOT / 'tests/keyboard_protocol_fixtures.json').read_text())
            cases = [(wire, payload, encoded, valid, 0) for payload, wire, encoded, valid in fixtures]
            payload, good, encoded, valid = fixtures[0]
            for prefix in ['7eff7d007e', '7eff' + '00' * 100000]:
                cases.append((prefix + good, payload, encoded, valid, 1))
            result = subprocess.run([str(root / 'harness')],
                                    input=''.join(c[0] + '\n' for c in cases),
                                    text=True, capture_output=True, check=True, timeout=30)
            lines = iter(result.stdout.splitlines())
            for wire, payload, encoded, valid, errors in cases:
                self.assertEqual(next(lines), f'P {int(valid)} {payload} E {encoded}')
                end = next(lines).split()
                self.assertEqual(end[:3], ['END', '1', str(errors)])
                self.assertLessEqual(int(end[3]), 255)
            self.assertIsNone(next(lines, None))

if __name__ == '__main__':
    unittest.main()
