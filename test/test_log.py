import importlib.util
import os
import sys
import types
import unittest

if 'unyts' not in sys.modules:
    sys.modules['unyts'] = types.SimpleNamespace(
        convertible=lambda *args, **kwargs: False,
        convert=lambda *args, **kwargs: None,
    )

import pandas as pd

spec = importlib.util.spec_from_file_location(
    'log_module',
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'log2frame', 'log.py'))
)
log_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(log_module)
Log = log_module.Log


class TestLog(unittest.TestCase):
    def setUp(self):
        self.data = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
        self.header = {'UWI': '123'}
        self.units = pd.Series({'A': 'm', 'B': 'kg'})
        self.log = Log(data=self.data, header=self.header, units=self.units, source='test', well='w')

    def test_iter(self):
        self.assertEqual(list(iter(self.log)), ['A', 'B'])

    def test_copy(self):
        copy = self.log.copy()
        self.assertEqual(copy.well, 'w')
        self.assertEqual(copy.header, self.header)
        self.assertEqual(copy.units.to_dict(), self.units.to_dict())
        self.assertIsNot(copy.data, self.log.data)

    def test_set_index_units(self):
        self.log.data.index.name = 'DEPTH'
        self.log.units = pd.Series({'A': 'm', 'B': 'kg', 'DEPTH': 'ft'})
        self.log.set_index_units('m')
        self.assertEqual(self.log.units['DEPTH'], 'm')


if __name__ == '__main__':
    unittest.main()
