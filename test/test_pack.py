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
if 'lasio' not in sys.modules:
    sys.modules['lasio'] = types.ModuleType('lasio')
if 'lasio.exceptions' not in sys.modules:
    exc_mod = types.ModuleType('lasio.exceptions')
    exc_mod.LASDataError = Exception
    exc_mod.LASHeaderError = Exception
    exc_mod.LASUnknownUnitError = Exception
    sys.modules['lasio.exceptions'] = exc_mod
if 'dlisio' not in sys.modules:
    dlisio_mod = types.ModuleType('dlisio')
    dlisio_mod.dlis = types.SimpleNamespace()
    dlisio_mod.lis = types.SimpleNamespace()
    sys.modules['dlisio'] = dlisio_mod
    sys.modules['dlisio.dlis'] = dlisio_mod.dlis
    sys.modules['dlisio.lis'] = dlisio_mod.lis

pkg_name = 'src.log2frame'
pkg = types.ModuleType(pkg_name)
pkg.__path__ = [os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'log2frame'))]
sys.modules[pkg_name] = pkg
init_mod = types.ModuleType(pkg_name + '.__init__')
init_mod._params_ = types.SimpleNamespace(simpandas_=None, raise_error_=True)
sys.modules[pkg_name + '.__init__'] = init_mod

spec_log = importlib.util.spec_from_file_location(
    pkg_name + '.log',
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'log2frame', 'log.py'))
)
log_module = importlib.util.module_from_spec(spec_log)
log_module.__package__ = pkg_name
sys.modules[pkg_name + '.log'] = log_module
spec_log.loader.exec_module(log_module)
Log = log_module.Log

spec_pack = importlib.util.spec_from_file_location(
    pkg_name + '.pack',
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'log2frame', 'pack.py'))
)
pack_module = importlib.util.module_from_spec(spec_pack)
pack_module.__package__ = pkg_name
sys.modules[pkg_name + '.pack'] = pack_module
spec_pack.loader.exec_module(pack_module)
concat = pack_module.concat
Pack = pack_module.Pack

import pandas as pd


class TestPack(unittest.TestCase):
    def setUp(self):
        self.data1 = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
        self.data2 = pd.DataFrame({'A': [5, 6], 'B': [7, 8]})
        self.log1 = Log(data=self.data1, header={}, units=pd.Series({'A': 'm', 'B': 'kg'}), source='one', well='w1')
        self.log2 = Log(data=self.data2, header={}, units=pd.Series({'A': 'm', 'B': 'kg'}), source='two', well='w2')

    def test_concat_plain_pandas(self):
        result = concat([self.log1, self.log2], use_simpandas=False)
        self.assertEqual(len(result), len(self.log1) + len(self.log2))
        self.assertIn('well', result.columns)
        self.assertIn('source', result.columns)
        self.assertEqual(list(result['well']), ['w1', 'w1', 'w2', 'w2'])

    def test_pack_append_and_getitem(self):
        pack = Pack()
        pack.append(self.log1)
        pack.append(self.log2)
        self.assertEqual(pack['w1'], self.log1)
        self.assertEqual(pack['w2'], self.log2)
        with self.assertRaises(ValueError):
            _ = pack[('missing', 'path')]


if __name__ == '__main__':
    unittest.main()
