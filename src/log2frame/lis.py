# -*- coding: utf-8 -*-
"""
Created on Thu Jan 19 20:07:16 2023

@author: Martín Carlos Araya <martinaraya@gmail.com>
"""

import logging
from dlisio import lis
import os.path
import pandas as pd
from .log import Log
from .pack import Pack
from .dictionaries.units import correct_units as correct_units_

try:
    import simpandas as spd
except ModuleNotFoundError:
    pass

__version__ = '0.1.6'
__release__ = 20230221


class DLISIOError(Exception):
    """
    Error raised while reading LAS file.
    """
    def __init__(self, message='raised by dlisio.'):
        self.message = 'ERROR: reading LIS file ' + message

def lis2frame(path: str, use_simpandas=False, raise_error=True, correct_units=True):
    if not os.path.isfile(path):
        raise FileNotFoundError("The provided path can't be found:\n" + str(path))
    if type(path) is str:
        path = path.replace('\\', '/')

    def _get_frame(data, l_count, i, sr):
        if frames[l_count][i]['index_name'] in data:
            index_name = frames[l_count][i]['index_name']
        elif len([c for c in data.columns if c.startswith(frames[l_count][i]['index_name'])]) > 0:
            index_name = [c for c in data.columns if c.startswith(frames[l_count][i]['index_name'])][0]
        else:
            index_name = list(data.columns)[0]
        if use_simpandas:
            return spd.SimDataFrame(data=data,
                                    units=frames[l_count][i]['curves_units'][sr],
                                    index=index_name,
                                    index_units=frames[l_count][i]['index_units'],
                                    name=(frames[l_count]['header']['service_name']
                                          if frames[l_count]['header']['service_name'] is not None
                                             and len(frames[l_count]['header']['service_name']) > 0 else
                                          frames[l_count]['header']['file_name']
                                          if frames[l_count]['header']['file_name'] is not None
                                             and len(frames[l_count]['header']['file_name']) > 0 else
                                          frames[l_count]['header']['name']
                                          if frames[l_count]['header']['name'] is not None
                                             and len(frames[l_count]['header']['name']) > 0 else None),
                                    meta=_make_header(l_count=l_count, i=i, sr=sr),
                                    source=path)
        else:
            return data.set_index(index_name)


    def _make_header(l_count, i, sr):
        to_concat = []
        if 'curves_units' in frames[l_count][i] and sr in frames[l_count][i]['curves_units']:
            to_concat.append(pd.DataFrame(frames[l_count][i]['curves_units'][sr],
                                          index=['units']).transpose())
        if 'wellsite_data' in frames[l_count][i]:
            to_concat.append(pd.DataFrame(frames[l_count][i]['wellsite_data']).set_index('MNEM'))
        if len(to_concat) == 2:
            to_concat = [pd.merge(to_concat[0], to_concat[1], right_index=True, left_index=True)]
        if 'header' in frames[l_count]:
            to_concat = [pd.DataFrame(frames[l_count]['header'], index=['values']).transpose()] + to_concat

        return pd.concat(to_concat, axis=0).fillna(value='')

    def _try_frame(data):
        try:
            return pd.DataFrame(data)
        except:
            return None

    try:
        physical_file = lis.load(path)
    except:  # any possible error raised at this point will be raised by dlisio
        if raise_error:
            raise DLISIOError("Error raised by dlisio while reading: " + str(path))
        else:
            logging.warning("Error raised by dlisio while reading: " + str(path))
            return None

    frames = {}
    l_count = -1
    for logical_file in physical_file:
        formatspecs = logical_file.data_format_specs()
        l_count += 1
        header = logical_file.header()
        reel_header = logical_file.reel.header()

        frames[l_count] = {'header': {'file_name': header.file_name if hasattr(header, 'file_name') else '',
                                      'date_of_generation': header.date_of_generation if hasattr(header,
                                                                                                 'date_of_generation') else '',
                                      'name': reel_header.name if hasattr(reel_header, 'name') else '',
                                      'service_name': reel_header.service_name if hasattr(reel_header,
                                                                                          'service_name') else '',
                                      'reel_date': reel_header.date if hasattr(reel_header, 'reel_date') else ''}}
        for i in range(len(formatspecs)):
            frames[l_count][i] = {'index_name': formatspecs[i].index_mnem,
                                  'index_units': correct_units_(formatspecs[i].index_units),
                                  'spacing': formatspecs[i].spacing,
                                  'spacing_units': formatspecs[i].spacing_units,
                                  'direction': formatspecs[i].direction,
                                  'curves': {},
                                  'curves_units': {}}
            for sample_rate in formatspecs[i].sample_rates():
                frames[l_count][i]['curves'][sample_rate] = lis.curves(logical_file, formatspecs[i],
                                                                       sample_rate=sample_rate, strict=False)
                meta = lis.curves_metadata(formatspecs[i], sample_rate=sample_rate, strict=False)
                frames[l_count][i]['curves_units'][sample_rate] = {meta[key].mnemonic: meta[key].units for key in meta
                                                                   if meta[key] is not None}
                if correct_units:
                    frames[l_count][i]['curves_units'][sample_rate] = correct_units_(frames[l_count][i]['curves_units'][sample_rate])

        wellsite_data = logical_file.wellsite_data()
        for i in range(len(wellsite_data)):
            if wellsite_data[i].isstructured():
                if i not in frames[l_count]:
                    frames[l_count][i] = {}
                frames[l_count][i]['wellsite_data'] = wellsite_data[i].table(simple=True)
    physical_file.close()

    frames = {(l_count, i, sr): Log(
        data=_get_frame(pd.concat([pd.DataFrame({'physical_file': [l_count] * len(frames[l_count][i]['curves'][sr]),
                                                 'logical_file': [i] * len(frames[l_count][i]['curves'][sr]),
                                                 'sample_rate': [sr] * len(frames[l_count][i]['curves'][sr])}),
                                   _try_frame(frames[l_count][i]['curves'][sr])], axis=1),
                        l_count=l_count, i=i, sr=sr),
        header=_make_header(l_count=l_count, i=i, sr=sr),
        units=pd.Series(frames[l_count][i]['curves_units'][sr]),
        source=path,
        well=(
            frames[l_count]['header']['service_name'] if frames[l_count]['header']['service_name'] is not None and len(
                frames[l_count]['header']['service_name']) > 0 else
            frames[l_count]['header']['file_name'] if frames[l_count]['header']['file_name'] is not None and len(
                frames[l_count]['header']['file_name']) > 0 else
            frames[l_count]['header']['name'] if frames[l_count]['header']['name'] is not None and len(
                frames[l_count]['header']['name']) > 0 else None)
    ) for l_count in frames
        for i in frames[l_count]
        if type(i) is int
           and 'curves' in frames[l_count][i]
        for sr in frames[l_count][i]['curves']
        if len(frames[l_count][i]['curves'][sr]) > 0}

    if len(frames) == 1:
        return frames[list(frames.keys())[0]]
    else:
        return Pack(frames)
