# -*- coding: utf-8 -*-
"""
Created on Thu Jan 19 20:07:16 2023

@author: Martín Carlos Araya <martinaraya@gmail.com>
"""

from dlisio import lis
import os.path
import pandas as pd
from .log import Log
from .pack import Pack

try:
    import simpandas as spd
except ModuleNotFoundError:
    pass

__version__ = '0.0.4'
__release__ = 20230130


def lis2frame(path: str, index: str = 'DEPTH', use_simpandas=False):
    if not os.path.isfile(path):
        raise FileNotFoundError("The provided path can't be found:\n" + str(path))
    if index is not None and type(index) not in [list, str]:
        raise TypeError("`index` must be a string representing a curve name")
    elif type(index) is list and len(index) != sum([type(i) is str for i in index]):
        raise TypeError("`index` must be a string representing a curve name")

    logs = {}
    physical_file = lis.load(path)
    frames = {}
    l_count = -1
    for logical_file in physical_file:
        formatspecs = logical_file.data_format_specs()
        l_count += 1
        header = logical_file.header()
        reel_header = logical_file.reel.header()

        frames[l_count] = {'header': {'file_name': header.file_name,
                                      'date_of_generation': header.date_of_generation,
                                      'name': reel_header.name,
                                      'service_name': reel_header.service_name,
                                      'reel_date': reel_header.date}}
        for i in range(len(logical_file.data_format_specs())):
            format_spec = logical_file.data_format_specs()[i]
            frames[l_count][i] = {'index_name': format_spec[i].index_mnem,
                                  'index_units': format_spec[i].index_units,
                                  'spacing': format_spec[i].spacing,
                                  'spacing_units': format_spec[i].spacing_units,
                                  'direction': format_spec[i].direction,
                                  'curves': {},
                                  'curves_units': {}}
            for sample_rate in format_spec.sample_rates():
                frames[l_count][i]['curves'][sample_rate] = lis.curves(logical_file, format_spec, sample_rate=sample_rate, strict=False)
                meta = lis.curves_metadata(format_spec, sample_rate=sample_rate, strict=False)
                frames[l_count][i]['curves_units'][sample_rate] = {meta[i][key].mnemonic: meta[i][key].units for key in meta[i]}

        for i in range(len(logical_file.wellsite_data())):
            if logical_file.wellsite_data()[i].isstructured():
                if i not in frames[l_count]:
                    frames[l_count][i] = {}
                frames[l_count][i]['wellsite_data'] = logical_file.wellsite_data()[i].table(simple=True)

    physical_file.close()

    if use_simpandas:
        frames = {i: spd.concat([spd.SimDataFrame(data=frames[l_count][i]['curves'][sr].update({'sample_rate': [sr] * len(frames[l_count][i]['curves'][sr])}),
                                                  units=frames[l_count][i]['curves'],
                                                  index=frames[l_count][i]['index_name'],
                                                  index_units=frames[l_count][i]['index_units'],
                                                  name=(frames[l_count]['header']['service_name'] if frames[l_count]['header']['service_name'] is not None and len(frames[l_count]['header']['service_name']) > 0 else
                                                        frames[l_count]['header']['file_name'] if frames[l_count]['header']['file_name'] is not None and len(frames[l_count]['header']['file_name']) > 0 else
                                                        frames[l_count]['header']['name'] if frames[l_count]['header']['name'] is not None and len(frames[l_count]['header']['name']) > 0 else None),
                                                  meta=frames[l_count]['header'],
                                                  source=path)
                                 for sr in frames[l_count][i]['curves']
                                 for i in frames[l_count]
                                 if len(frames[l_count][i]['curves'][sr]) > 0],
                                axis=0)
                  for i in frames}

    else:
        frames = {i: Log(
            data=pd.concat([pd.DataFrame(data=frames[l_count][i]['curves'][sr].update({'sample_rate': [sr] * len(frames[l_count][i]['curves'][sr])}))
                            for sr in frames[l_count][i]['curves']
                            for i in frames[l_count]
                            if len(frames[l_count][i]['curves'][sr]) > 0],
                           axis=0),
            header=frames[l_count]['header'],
            units=frames[l_count][i]['curves'],
            source=path,
            well=(frames[l_count]['header']['service_name'] if frames[l_count]['header']['service_name'] is not None and len(frames[l_count]['header']['service_name']) > 0 else
                  frames[l_count]['header']['file_name'] if frames[l_count]['header']['file_name'] is not None and len(frames[l_count]['header']['file_name']) > 0 else
                  frames[l_count]['header']['name'] if frames[l_count]['header']['name'] is not None and len(frames[l_count]['header']['name']) > 0 else None)
        ) for i in frames}

    if len(subframe) == 1:
        return subframe[list(subframe.keys())[0]]
    else:
        return Pack(subframe)
