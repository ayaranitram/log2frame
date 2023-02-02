# -*- coding: utf-8 -*-
"""
Created on Thu Jan 19 19:02:12 2023

@author: Martín Carlos Araya <martinaraya@gmail.com>
"""

import lasio
import os.path
import pandas as pd
import ntpath
from .log import Log

try:
    import simpandas as spd
except ModuleNotFoundError:
    pass

__version__ = '0.1.1'
__release__ = 20230202


def las2frame(path: str, use_simpandas=False, raise_error=False):
    if not os.path.isfile(path):
        raise FileNotFoundError("The provided path can't be found:\n" + str(path))

    las = lasio.read(path)
    las_units = {}
    if 'Well' in las.header:
        las_units = {las.header['Well'][i]['mnemonic']: las.header['Well'][i]['unit'] for i in
                     range(len(las.header['Well']))}
    if 'Curves' in las.header:
        las_units.update({las.header['Curves'][i]['mnemonic']: las.header['Curves'][i]['unit'] for i in
                          range(len(las.header['Curves']))})
    las_header = pd.DataFrame({las.header[key][i]['mnemonic']: [las.header[key][i]['unit'], las.header[key][i]['value'],
                                                                las.header[key][i]['descr']]
                               for key in las.header.keys()
                               for i in range(len(las.header[key])) if hasattr(las.header[key], 'keys')},
                              index=['unit', 'value', 'descr']).transpose()
    well_name = None
    for well_name_ in ['UWI', 'WELL', 'WELL:1', 'WELL:2', 'WN', 'NAME', 'WNAME']:
        if well_name_ in las_header.index and type(las_header.loc[well_name_, 'value']) is str \
                and len(las_header.loc[well_name_, 'value']) > 0:
            well_name = las_header.loc[well_name_, 'value']
            break
    if well_name is None:
        well_name = ntpath.basename(path).split('.')[0]

    return Log(data=las.df() if not use_simpandas else spd.SimDataFrame(data=las.df(),
                                                                        index_units=las.index_unit,
                                                                        units=las_units,
                                                                        name=well_name,
                                                                        meta=las_header,
                                                                        source=path),
               header=las_header,
               units=pd.Series(las_units, name='curves_units'),
               source=path,
               well=well_name)
