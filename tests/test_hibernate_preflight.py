# SPDX-License-Identifier: GPL-2.0-only
from pathlib import Path
import runpy
import struct
import unittest
import uuid

MODULE = runpy.run_path(str(Path(__file__).resolve().parents[1] /
                          'device/hibernate/tb522fu-hibernate-preflight'))


class HibernatePreflightTests(unittest.TestCase):
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
