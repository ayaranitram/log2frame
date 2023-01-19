# -*- coding: utf-8 -*-
"""
Created on Thu Jan 19 20:07:16 2023

@author: Martín Carlos Araya <martinaraya@gmail.com>
"""

from dlisio import dlis
import os.path
import pandas as pd

try:
    import simpandas as spd
    simpandas = True
except ModuleNotFoundError:
    simpandas = False

__version__ = '0.0.0'
__release__ = 20230119


def dlis2frame(path: str, index: str = 'DEPTH'):
    if not os.path.isfile(path):
        raise FileNotFoundError("The provided path can't be found:\n" + str(path))
    if index is not None and type(index) not in [list, str]:
        raise TypeError("`index` must be a string representing a curve name")
    elif type(index) is list and len(index) != sum([type(i) is str for i in index]):
        raise TypeError("`index` must be a string representing a curve name")

    physical_file = dlis.load(path)
    frames = {}
    for logical_file in physical_file:
        for frame in logical_file.frames:
            frame_units = {channel.name: channel.units for channel in frame.channels}
            curves_df = pd.DataFrame(frame.curves())
            if index is not None and index in curves_df and len(curves_df[index].unique()) == len(curves_df):
                curves_df.set_index(index, inplace=True)
            frames[frame.name] = (curves_df, pd.Series(frame_units, name='frame_units'))
    if simpandas:
        frames = {name: spd.SimDataFrame(data=data[0], units=data[1]) for name, data in frames.items()}
        if len(frames) == 1:
            return frames[list(frames.keys())[0]]
        else:
            return frames
    else:
        if len(frames) == 1:
            return frames[list(frames.keys())[0]]
        else:
            return frames
