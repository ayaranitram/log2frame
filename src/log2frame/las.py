# -*- coding: utf-8 -*-
"""
Created on Thu Jan 19 19:02:12 2023

@author: Martín Carlos Araya <martinaraya@gmail.com>
"""

import lasio
import os.path
import pandas as pd
from .log import Log

try:
    import simpandas as spd
except ModuleNotFoundError:
    pass

__version__ = '0.1.0'
__release__ = 20230201


def las2frame(path: str, use_simpandas=False):
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
    if 'UWI' in las_header.index and type(las_header.loc['UWI', 'value']) is str and len(las_header.loc['UWI', 'value']) > 0:
        well_name = las_header.loc['UWI', 'value']
    elif 'WELL' in las_header.index:
        well_name = las_header.loc['WELL', 'value']
    elif 'WN' in las_header.index:
        well_name = las_header.loc['WN', 'value']
    else:
        well_name = None

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
