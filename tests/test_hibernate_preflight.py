# SPDX-License-Identifier: GPL-2.0-only
from pathlib import Path
import errno
import os
import runpy
import struct
import tempfile
import unittest
import uuid
from unittest.mock import patch

MODULE = runpy.run_path(str(Path(__file__).resolve().parents[1] /
                          'device/hibernate/tb522fu-hibernate-preflight'))


class HibernatePreflightTests(unittest.TestCase):
    def test_direct_header_read_uses_a_page_aligned_buffer(self):
        # Exercise real O_DIRECT I/O; an ordinary bytes buffer is not aligned.
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'header'
            page = bytes(range(256)) * 16
            target.write_bytes(page)
            fd = os.open(target, os.O_RDONLY | os.O_DIRECT)
            try:
                self.assertEqual(MODULE['read_page_direct'](fd), page)
            finally:
                os.close(fd)
            fd = os.open(target, os.O_RDONLY)
            try:
                with self.assertRaises(AssertionError):
                    MODULE['read_page_direct'](fd)
            finally:
                os.close(fd)

    def test_short_direct_read_cannot_accept_a_header(self):
        with patch('fcntl.fcntl', return_value=os.O_DIRECT), patch('os.preadv', return_value=2048):
            with self.assertRaises(RuntimeError):
                MODULE['read_page_direct'](44)

    def test_failed_resume_action_is_written_only_once(self):
        for result in (OSError(errno.EBUSY, 'busy'), 2):
            options = {'side_effect': result} if isinstance(result, OSError) else {'return_value': result}
            with self.subTest(result=result), patch('os.open', return_value=44), patch('os.write', **options) as written, patch('os.close') as closed:
                with self.assertRaises((OSError, RuntimeError)):
                    MODULE['write_once']('/sys/power/resume', b'259:2\n')
                written.assert_called_once_with(44, b'259:2\n')
                closed.assert_called_once_with(44)

    def test_only_the_configured_empty_swap_header_is_accepted(self):
        u = uuid.UUID('00000000-1111-2222-3333-444444444444')
        page = bytearray(4096)
        struct.pack_into('<III',page,1024,1,3145727,0)
        page[1036:1052] = u.bytes; page[-10:] = b'SWAPSPACE2'
        MODULE['check_header'](page,str(u))
        with self.assertRaises(RuntimeError):
            MODULE['check_header'](page,str(uuid.uuid4()))
        page[-10:] = b'S1SUSPEND\0'
        with self.assertRaises(RuntimeError):
            MODULE['check_header'](page,str(u))

    def test_space_guard_reserves_headroom_and_rejects_unknown_image_budgets(self):
        self.assertEqual(MODULE['required_space'](4*1024**3),5*1024**3+256*1024**2)
        for n in (0,-1,7*1024**3):
            with self.subTest(budget=n),self.assertRaises(RuntimeError):
                MODULE['required_space'](n)


if __name__ == '__main__':
    unittest.main()
