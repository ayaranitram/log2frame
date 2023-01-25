# -*- coding: utf-8 -*-
"""
Created on Thu Jan 19 19:01:21 2023

@author: Martín Carlos Araya <martinaraya@gmail.com>
"""
from .las import las2frame
from .dlis import dlis2frame
from .lis import lis2frame
from .pack import Pack, concat
from .log import Log
import glob
import os.path
import logging

__version__ = '0.0.4'
__release__ = 20230125
__all__ = ['read', 'concat']


class _Log2FrameParams(object):
    def __init__(self):
        try:
            import simpandas as spd
            self.simpandas_ = True
        except ModuleNotFoundError:
            self.simpandas_ = None
        self.raise_error_ = True


_params_ = _Log2FrameParams()


def _read_one(path: str, index: str = 'DEPTH', raise_error=True, use_simpandas=None):
    use_simpandas = _params_.simpandas_ if use_simpandas is None else bool(use_simpandas)
    if not os.path.isfile(path):
        if raise_error:
            raise FileNotFoundError("The provided path can't be found:\n" + str(path))
        else:
            logging.warning("The provided path can't be found:\n" + str(path))
    if path.split('.')[-1].lower() == 'las':
        return las2frame(path, index=index, use_simpandas=use_simpandas)
    elif path.split('.')[-1].lower() == 'dlis':
        return dlis2frame(path, index=index, use_simpandas=use_simpandas)
    elif path.split('.')[-1].lower() == 'lis':
        raise NotImplementedError  # return lis2frame(path, index=index, use_simpandas=use_simpandas)
    elif not raise_error:
        logging.warning("Not a valid log file: " + str(path))
        return None
    else:
        raise ValueError("`path` should be a '.las' or '.dlis' file")


def read(path: str, index: str = 'DEPTH', recursive=True, raise_error=None, squeeze=True, use_simpandas=False):
    use_simpandas = _params_.simpandas_ if use_simpandas is None else bool(use_simpandas)
    raise_error = _params_.raise_error_ if raise_error is None else bool(raise_error)
    if os.path.isfile(path):
        return _read_one(path, index=index, raise_error=raise_error, use_simpandas=use_simpandas)
    if type(path) is str:
        path = [path]
    if type(path) is not str and hasattr(path, '__iter__'):
        result = Pack()
        for each in path:
            for file in glob.iglob(each, recursive=recursive):
                result.append(_read_one(file, index=index, raise_error=raise_error, use_simpandas=use_simpandas))
    if squeeze:
        return result.squeeze()
    else:
        return result
