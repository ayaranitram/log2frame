# -*- coding: utf-8 -*-
"""
Created on Thu Jan 19 20:07:16 2023

@author: Martín Carlos Araya <martinaraya@gmail.com>
"""

import logging
from dlisio import dlis
import os.path
import pandas as pd
import numpy as np
from .log import Log
from .pack import Pack
from .dictionaries.units import correct_units as correct_units_

try:
    import simpandas as spd
except ModuleNotFoundError:
    pass

__version__ = '0.1.7'
__release__ = 20230221


class DLISIOError(Exception):
    """
    Error raised while reading LAS file.
    """
    def __init__(self, message='raised by dlisio.'):
        self.message = 'ERROR: reading DLIS file ' + message


def dlis2frame(path: str, use_simpandas=False, raise_error=True, correct_units=True):
    if not os.path.isfile(path):
        raise FileNotFoundError("The provided path can't be found:\n" + str(path))
    if type(path) is str:
        path = path.replace('\\', '/')

    try:
        physical_file = dlis.load(path)
    except:  # any possible error raised at this point will be raised by dlisio
        if raise_error:
            raise DLISIOError("Error raised by dlisio while reading: " + str(path))
        else:
            logging.warning("Error raised by dlisio while reading: " + str(path))
            return None

    frames = {}
    l_count = -1
    for logical_file in physical_file:
        l_count += 1
        try:  # to skip RuntimeError raised by dlisio
            log_file_params = logical_file.parameters
        except:
            if raise_error:
                raise DLISIOError("Error raised by dlisio while reading: " + str(path))
            else:
                logging.error("Error raised by dlisio while reading: " + str(path))
                log_file_params = None
        if log_file_params is not None:
            meta = pd.DataFrame(index=range(len(log_file_params)))
            well_name = None
            for p in range(len(log_file_params)):
                meta.loc[p, 'name'] = logical_file.parameters[p].name
                meta.loc[p, 'long_name'] = logical_file.parameters[p].long_name
                try:
                    _len_values = len(logical_file.parameters[p].values)
                except:
                    if raise_error:
                        raise DLISIOError("Error raised by dlisio while reading: " + str(path))
                    else:
                        logging.error("Error raised by dlisio while reading: " + str(path))
                        _len_values = 0
                if _len_values > 0:
                    if isinstance(logical_file.parameters[p].values[0], np.ndarray):
                        meta.loc[p, 'values'] = 'numpy.ndarray not loaded.'
                    else:
                        meta.loc[p, 'values'] = logical_file.parameters[p].values[0]
                else:
                    meta.loc[p, 'values'] = ''
                if p in logical_file.parameters and hasattr(logical_file.parameters, 'name') and logical_file.parameters[p].name == 'WN':
                    well_name = logical_file.parameters[p].values[0] if len(logical_file.parameters[p].values) else ''
            if 'name' in meta:
                meta.set_index('name', inplace=True)
        else:
            well_name = None
            meta = pd.DataFrame()
        for frame in logical_file.frames:
            frame_units = {channel.name: channel.units for channel in frame.channels}
            if correct_units:
                frame_units = correct_units_(frame_units)
            try:
                curves_df = pd.DataFrame(frame.curves()).set_index(frame.index)
            except ValueError:
                if raise_error:
                    raise ValueError("The file " + str(path) + " contains data that is not 1-dimensional.")
                else:
                    logging.warning("The file " + str(path) + " contains data that is not 1-dimensional.")
                    continue

            frames[(l_count, frame.name)] = (curves_df, meta, pd.Series(frame_units, name='frame_units'), well_name)
    physical_file.close()

    if len(frames) == 1:
        frames = {name: Log(
            data=data[0] if not use_simpandas else spd.SimDataFrame(data=data[0], units=data[2], name=data[3],
                                                                    meta=data[1],
                                                                    source=str(path)),
            header=data[1],
            units=data[2],
            source=str(path),
            well=data[3]) for name, data in frames.items()}
        return frames[list(frames.keys())[0]]
    else:
        frames = {name: Log(
            data=data[0] if not use_simpandas else spd.SimDataFrame(data=data[0], units=data[2], name=data[3],
                                                                    meta=data[1],
                                                                    source='logical file ' + str(name[0]) +
                                                                           ', frame ' + str(name[1]) +
                                                                           ' in: ' + path),
            header=data[1],
            units=data[2],
            source='logical file ' + str(name[0]) +
                   ', frame ' + str(name[1]) +
                   ' in: ' + path,
            well=data[3]) for name, data in frames.items()}
        return Pack(frames)
