"""MGMT configuration boundaries: unrelated adapters must never be written."""
import importlib.machinery
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

helper = importlib.machinery.SourceFileLoader(
    'bluetooth_address', str(Path(__file__).resolve().parents[1] /
    'device/usr/libexec/tb522fu-bluetooth-address')).load_module()


class EventSocket:
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def settimeout(self, value): pass
    def recv(self, size): return b''


class ConfigurationTests(unittest.TestCase):
    address = bytes.fromhex('563412000002')

    def scenario(self, *, configured=False, address=None, missing=2, wrong_board=False):
        writes = []
        state = {'configured': configured, 'index': 3}
        def indexes(op):
            return (state['index'],) if ((op == 3) == state['configured']) else ()
        def identity(index):
            return None if wrong_board else Path('/board/bluetooth')
        def mgmt(op, index, payload=b'', **kwargs):
            if op == 0x37:
                return struct.pack('<HII', 29, 2, missing)
            if op == 0x39:
                writes.append((index, payload))
                state.update(configured=True, index=7)
                return bytes(4)
            if op == 4:
                return (address or self.address) + bytes(11)
            raise AssertionError(op)
        with patch.object(helper, 'indexes', indexes), patch.object(helper, 'board_controller', identity), \
             patch.object(helper, 'mgmt', mgmt), patch.object(helper, 'control_socket', EventSocket):
            try:
                result = helper.configure(3, self.address, timeout=1)
                return result, writes
            except RuntimeError:
                self.assertEqual(writes, [])
                raise

    def test_unconfigured_sets_once_and_accepts_reindexed_same_device(self):
        result, writes = self.scenario()
        self.assertEqual(writes, [(3, self.address)])
        self.assertEqual(result['index'], 7)
        self.assertTrue(result['configured_by_helper'])

    def test_configured_matching_address_is_read_only(self):
        result, writes = self.scenario(configured=True)
        self.assertEqual(writes, [])
        self.assertFalse(result['configured_by_helper'])

    def test_configured_wrong_address_is_never_overwritten(self):
        with self.assertRaisesRegex(RuntimeError, 'refusing to overwrite'):
            self.scenario(configured=True, address=bytes(6))

    def test_other_missing_configuration_is_never_modified(self):
        with self.assertRaisesRegex(RuntimeError, 'other than'):
            self.scenario(missing=3)

    def test_unrelated_adapter_is_never_modified(self):
        with self.assertRaisesRegex(RuntimeError, 'not the board'):
            self.scenario(wrong_board=True)


if __name__ == '__main__':
    unittest.main()
