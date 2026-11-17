# SPDX-License-Identifier: GPL-2.0-only
"""Compile and exercise the actual early-resume binary header parser."""
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ResumeHeaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='hibernate-header-')
        cls.directory = Path(cls.tmp.name)
        harness = cls.directory / 'harness.c'
        harness.write_text('#define RESUME_UNIT_TEST\n#include "' +
            str(ROOT / 'device/hibernate/resume.c') + '"\n' + '''
int main(int argc, char **argv) {
    unsigned char page[4096];
    if (argc != 3) return 9;
    FILE *f = fopen(argv[1], "rb");
    if (!f) return 9;
    size_t n = fread(page, 1, sizeof(page), f);
    fclose(f);
    return header_state(page, n, strtoull(argv[2], NULL, 10));
}
''')
        cls.binary = cls.directory / 'harness'
        cls.real = cls.directory / 'tb522fu-resume'
        compiler = shutil.which('cc')
        if not compiler:
            raise RuntimeError('A C compiler is required for resume parser checks')
        for source, binary in [(harness, cls.binary), (ROOT / 'device/hibernate/resume.c', cls.real)]:
            subprocess.run([compiler, '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror',
                            str(source), '-o', str(binary)], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def header(self):
        page = bytearray(4096)
        struct.pack_into('<III', page, 1024, 1, 3145727, 0)
        page[1036:1052] = bytes(range(1, 17))
        page[-10:] = b'SWAPSPACE2'
        return page

    def check(self, page, size=12 * 1024**3):
        path = self.directory / 'header'
        path.write_bytes(page)
        return subprocess.run([str(self.binary), str(path), str(size)], check=False).returncode

    def test_normal_swap_permits_ordinary_boot(self):
        self.assertEqual(self.check(self.header()), 0)

    def test_image_requires_early_restore(self):
        page = self.header()
        page[-20:-10] = b'SWAPSPACE2'
        page[-10:] = b'S1SUSPEND\0'
        self.assertEqual(self.check(page), 3)

    def test_corrupt_or_unexpected_headers_fail_closed(self):
        variants = []
        page = self.header(); page[-10:] = b'BAD_MAGIC!'; variants.append(page)
        page = self.header(); page[-10:] = b'S1SUSPEND\0'; variants.append(page)
        page = self.header(); page[1036:1052] = bytes(16); variants.append(page)
        for offset, value in [(1024, 2), (1028, 3145726), (1032, 1)]:
            page = self.header(); struct.pack_into('<I', page, offset, value); variants.append(page)
        variants += [self.header()[:4095], b'']
        for i, page in enumerate(variants):
            with self.subTest(case=i):
                self.assertEqual(self.check(page), 1)
        self.assertEqual(self.check(self.header(), 24 * 1024**3), 1)

    def test_real_binary_rejects_regular_files_instead_of_writing_sysfs(self):
        path = self.directory / 'fixture'
        path.write_bytes(self.header())
        for mode in ('inspect', 'resume'):
            result = subprocess.run([str(self.real), mode, str(path), str(path)],
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn('cannot read validated swap block device', result.stderr)


if __name__ == '__main__':
    unittest.main()
