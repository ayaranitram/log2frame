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
__release__ = 20230124


def lis2frame(path: str, index: str = 'DEPTH', use_simpandas=False):
    if not os.path.isfile(path):
        raise FileNotFoundError("The provided path can't be found:\n" + str(path))
    if index is not None and type(index) not in [list, str]:
        raise TypeError("`index` must be a string representing a curve name")
    elif type(index) is list and len(index) != sum([type(i) is str for i in index]):
        raise TypeError("`index` must be a string representing a curve name")

    physical_file = lis.load(path)
    frames = {}
    l_count = -1
    for logical_file in physical_file:
        l_count += 1
        meta = pd.DataFrame(index=range(len(logical_file.parameters)))
        well_name = None
        for p in range(len(logical_file.parameters)):
            meta.loc[p, 'name'] = logical_file.parameters[p].name
            meta.loc[p, 'long_name'] = logical_file.parameters[p].long_name
            meta.loc[p, 'values'] = logical_file.parameters[p].values[0]
            if logical_file.parameters[p].name == 'WN':
                well_name = logical_file.parameters[p].values[0]
        meta.set_index('name', inplace=True)
        for frame in logical_file.frames:
            frame_units = {channel.name: channel.units for channel in frame.channels}
            curves_df = pd.DataFrame(frame.curves())
            if index is not None and index in curves_df and len(curves_df[index].unique()) == len(curves_df):
                curves_df.set_index(index, inplace=True)
            frames[(l_count, frame.name)] = (curves_df, meta, pd.Series(frame_units, name='frame_units'), well_name)
    physical_file.close()
    if use_simpandas:
        frames = {name: spd.SimDataFrame(data=data[0],
                                         units=data[2],
                                         name=data[3],
                                         meta=data[1],
                                         source=path)
                  for name, data in frames.items()}
        if len(frames) == 1:
            return frames[list(frames.keys())[0]]
        else:
            return frames
    else:
        frames = {name: Log(data=data[0],
                            header=data[1],
                            units=data[2],
                            source=path,
                            well=data[3]) for name, data in frames.items()}
        if len(frames) == 1:
            return frames[list(frames.keys())[0]]
        else:
            return Pack(frames)
