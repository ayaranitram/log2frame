import os
import sys
import tempfile
import types
import unittest

import pandas as pd

# Ensure the package root is importable.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Stub external dependencies that are not installed in this environment.
if 'unyts' not in sys.modules:
    sys.modules['unyts'] = types.SimpleNamespace(
        convertible=lambda *args, **kwargs: False,
        convert=lambda *args, **kwargs: None,
    )
if 'lasio' not in sys.modules:
    lasio_mod = types.ModuleType('lasio')
    sys.modules['lasio'] = lasio_mod
if 'lasio.exceptions' not in sys.modules:
    exc_mod = types.ModuleType('lasio.exceptions')
    exc_mod.LASDataError = Exception
    exc_mod.LASHeaderError = Exception
    exc_mod.LASUnknownUnitError = Exception
    sys.modules['lasio.exceptions'] = exc_mod
if 'dlisio' not in sys.modules:
    dlisio_mod = types.ModuleType('dlisio')
    sys.modules['dlisio'] = dlisio_mod
if 'dlisio.lis' not in sys.modules:
    dlisio_lis = types.ModuleType('dlisio.lis')
    sys.modules['dlisio.lis'] = dlisio_lis
if 'dlisio.dlis' not in sys.modules:
    dlisio_dlis = types.ModuleType('dlisio.dlis')
    sys.modules['dlisio.dlis'] = dlisio_dlis
if 'simpandas' not in sys.modules:
    simpandas_mod = types.ModuleType('simpandas')
    simpandas_mod.SimDataFrame = type('SimDataFrame', (pd.DataFrame,), {})
    simpandas_mod.concat = lambda frames, axis=0: pd.concat(frames, axis=axis)
    sys.modules['simpandas'] = simpandas_mod

# Dummy LAS backend.
class DummyLasEntry:
    def __init__(self, mnemonic, unit, value, descr):
        self.mnemonic = mnemonic
        self.unit = unit
        self.value = value
        self.descr = descr
    def __getitem__(self, key):
        return getattr(self, key)

class DummyLas:
    def __init__(self):
        self.header = {
            'Well': [DummyLasEntry('UWI', 'unitless', 'WELL-1', 'Well UWI')],
            'Curves': [DummyLasEntry('GR', 'gAPI', None, 'Gamma Ray')]
        }
        self.index_unit = 'ft'

    def df(self):
        return pd.DataFrame({'GR': [10, 20, 30], 'RHOB': [2.3, 2.4, 2.5]})

sys.modules['lasio'].read = lambda path: DummyLas()

# Generic wrapper for dummy library file objects that exposes close().
class DummyFileWrapper:
    def __init__(self, logical_files):
        self._logical_files = logical_files
    def __iter__(self):
        return iter(self._logical_files)
    def close(self):
        return None

# Dummy LIS backend.
class DummyFormatSpec:
    def __init__(self):
        self.index_mnem = 'DEPTH'
        self.index_units = 'ft'
        self.spacing = None
        self.spacing_units = None
        self.direction = None
    def sample_rates(self):
        return [1]

class DummyLogicalFile:
    def __init__(self):
        self._header = types.SimpleNamespace(file_name='test.lis', date_of_generation='2026-04-26')
        self.reel = types.SimpleNamespace(header=lambda: types.SimpleNamespace(name='LIS-WELL', service_name='SERVICE', date='2026-04-26'))
        self.frames = []
    def header(self):
        return self._header
    def wellsite_data(self):
        return []
    def data_format_specs(self):
        return [DummyFormatSpec()]

class DummyLisFrame:
    def __init__(self):
        self.channels = [types.SimpleNamespace(name='GR', units='gAPI'), types.SimpleNamespace(name='RHOB', units='g/cm3')]
        self.index = pd.Index([1000.0, 1001.0], name='DEPTH')
        self.name = 'FRAME1'
    def curves(self):
        return {'DEPTH': [1000.0, 1001.0], 'GR': [10, 20], 'RHOB': [2.45, 2.50]}

class DummyLisMetaEntry:
    def __init__(self, mnemonic, units):
        self.mnemonic = mnemonic
        self.units = units

mock_logical_file = DummyLogicalFile()
mock_logical_file.frames = [DummyLisFrame()]

sys.modules['dlisio.lis'].load = lambda path: DummyFileWrapper([mock_logical_file])
sys.modules['dlisio.lis'].curves = lambda logical_file, formatspec, sample_rate, strict=False: logical_file.frames[0].curves()
sys.modules['dlisio.lis'].curves_metadata = lambda formatspec, sample_rate=1, strict=False: {
    'GR': DummyLisMetaEntry('GR', 'gAPI'),
    'RHOB': DummyLisMetaEntry('RHOB', 'g/cm3')
}

# Dummy DLIS backend.
class DummyIndex(list):
    def __init__(self, values, name, units):
        super().__init__(values)
        self.name = name
        self.units = units
    def __array__(self, dtype=None):
        return np.asarray(list(self), dtype=dtype)

class DummyDlisFrame:
    def __init__(self):
        self.channels = [types.SimpleNamespace(name='GR', units='gAPI'), types.SimpleNamespace(name='RHOB', units='g/cm3')]
        self.index = 'DEPTH'
        self.index_units = 'ft'
        self.name = 'DLIS_FRAME'
    def curves(self):
        return {'DEPTH': [2000.0, 2001.0], 'GR': [15, 25], 'RHOB': [2.55, 2.60]}

class DummyDlisLogicalFile:
    def __init__(self):
        self.parameters = []
        self.frames = [DummyDlisFrame()]

sys.modules['dlisio.dlis'].load = lambda path: DummyFileWrapper([DummyDlisLogicalFile()])

import log2frame


class TestReaders(unittest.TestCase):
    def test_las2frame_plain_pandas_units_preserved(self):
        with tempfile.NamedTemporaryFile(suffix='.las', delete=False) as tmp:
            tmp_path = tmp.name
        try:
            log = log2frame.read(tmp_path, use_simpandas=False)
            self.assertEqual(log.data.index.name, 'INDEX')
            self.assertEqual(log.units['INDEX'], 'ft')
            self.assertEqual(log.units['GR'], 'gAPI')
        finally:
            os.remove(tmp_path)

    def test_lis2frame_plain_pandas_index_units_preserved(self):
        with tempfile.NamedTemporaryFile(suffix='.lis', delete=False) as tmp:
            tmp_path = tmp.name
        try:
            log = log2frame.lis2frame(tmp_path, use_simpandas=False)
            self.assertEqual(log.data.index.name, 'DEPTH')
            self.assertEqual(log.units['DEPTH'], 'ft')
            self.assertEqual(log.units['GR'], 'gAPI')
        finally:
            os.remove(tmp_path)

    def test_dlis2frame_plain_pandas_index_units_preserved(self):
        with tempfile.NamedTemporaryFile(suffix='.dlis', delete=False) as tmp:
            tmp_path = tmp.name
        try:
            log = log2frame.dlis2frame(tmp_path, use_simpandas=False)
            self.assertEqual(log.data.index.name, 'DEPTH')
            self.assertEqual(log.units['DEPTH'], 'ft')
            self.assertEqual(log.units['GR'], 'gAPI')
        finally:
            os.remove(tmp_path)


if __name__ == '__main__':
    unittest.main()
