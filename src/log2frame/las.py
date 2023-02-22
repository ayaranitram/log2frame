# -*- coding: utf-8 -*-
"""
Created on Thu Jan 19 19:02:12 2023

@author: Martín Carlos Araya <martinaraya@gmail.com>
"""
import logging
import lasio
from lasio.exceptions import LASDataError, LASHeaderError, LASUnknownUnitError
import os.path
import pandas as pd
import ntpath
from .log import Log
from .dictionaries.units import correct_units as correct_units_

try:
    import simpandas as spd
except ModuleNotFoundError:
    pass

__version__ = '0.1.6'
__release__ = 20230221

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)


class LASIOError(Exception):
    """
    Error raised while reading LAS file.
    """
    def __init__(self, message='raised by lasio.'):
        self.message = 'ERROR: reading LAS file ' + message


def las2frame(path: str, use_simpandas=False, raise_error=True, correct_units=True):
    if not os.path.isfile(path):
        raise FileNotFoundError("The provided path can't be found:\n" + str(path))
    if type(path) is str:
        path = path.replace('\\', '/')

    try:
        las = lasio.read(path)
    except:  # any possible error raised at this point will be raised by lasio
        if raise_error:
            raise LASIOError("Error raised by lasio while reading: " + str(path))
        else:
            logging.error("Error raised by lasio while reading: " + str(path))
            return None

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
    for well_name_ in ['UWI', 'WELLBORE', 'WELL', 'WELL:1', 'WELL:2', 'WN', 'NAME', 'WNAME']:
        if well_name_ in las_header.index and type(las_header.loc[well_name_, 'value']) is str \
                and len(las_header.loc[well_name_, 'value']) > 0:
            well_name = las_header.loc[well_name_, 'value']
            break
    if well_name is None:
        well_name = ntpath.basename(path).split('.')[0]

    if correct_units:
        las_units = correct_units_(las_units)

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
