# -*- coding: utf-8 -*-
"""
Created on Thu Jan 19 19:02:12 2023

@author: Martín Carlos Araya <martinaraya@gmail.com>
"""

from welly import Well
import os.path
import pandas as pd

try:
    import simpandas as spd
    simpandas = True
except ModuleNotFoundError:
    simpandas = False

__version__ = '0.0.3'
__release__ = 20230124


def las2frame(path: str):
    if not os.path.isfile(path):
        raise FileNotFoundError("The provided path can't be found:\n" + str(path))

    las = Well.from_las(path)
    las_units = {k: las.data[k].units for k in las.data.keys()}
    las_units.update({las.data[list(las.data.keys())[0]].index_name: las.data[list(las.data.keys())[0]].index_units})
    if simpandas:
        return spd.SimDataFrame(data=las.df(), units=las_units, name=las.name, meta=las.header)
    else:
        return pd.DataFrame(data=las.df()), las.header, pd.Series(las_units, name='curves_units')
