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
from .rft import *

for name in ("lasio", "lasio.reader", "lasio.las", "unyts"):
    logging.getLogger(name).setLevel(logging.WARNING)

__version__ = '0.2.2'
__release__ = 20260427
__all__ = ['read', 'concat']


class _Log2FrameParams(object):
    def __init__(self):
        try:
            import simpandas as spd
            self.simpandas_ = True
        except ModuleNotFoundError:
            self.simpandas_ = False
        self.raise_error_ = True


_params_ = _Log2FrameParams()


def _read_one(path: str, raise_error=True, use_simpandas=None, correct_units=True):
    if use_simpandas is not None and use_simpandas is True and not _params_.simpandas_:
        raise ModuleNotFoundError("SimPandas is not installed, please install it or set parameter `use_simpandas` to False.")
    use_simpandas = _params_.simpandas_ if use_simpandas is None else bool(use_simpandas)
    if not os.path.isfile(path):
        if raise_error:
            raise FileNotFoundError("The provided path can't be found:\n" + str(path))
        else:
            logging.warning("The provided path can't be found:\n" + str(path))
    if path.split('.')[-1].lower() == 'las':
        return las2frame(path, use_simpandas=use_simpandas, raise_error=raise_error, correct_units=correct_units)
    elif path.split('.')[-1].lower() == 'dlis':
        return dlis2frame(path, use_simpandas=use_simpandas, raise_error=raise_error, correct_units=correct_units)
    elif path.split('.')[-1].lower() in ['lis', 'lti']:
        return lis2frame(path, use_simpandas=use_simpandas, raise_error=raise_error, correct_units=correct_units)
    elif not raise_error:
        # logging.warning("Not a valid log file: " + str(path))
        return None
    else:
        raise ValueError("`path` should be a '.las' or '.dlis' file")


def read(path: str, recursive=True, raise_error=False, squeeze=True, use_simpandas=None, correct_units=True):
    """Read a well-log file (LAS, DLIS, LIS) into a units-aware :class:`Log` container.

    Accepts individual file paths or a list of paths/globs. If multiple files are
    read, they are returned grouped in a :class:`Pack` container.

    Parameters
    ----------
    path : str | list[str]
        Path to the ``.las``, ``.dlis``, or ``.lis`` file(s). Glob expressions and directory paths are supported.
    recursive : bool, default True
        If reading a path pattern with globs, controls whether directories are searched recursively.
    squeeze : bool, default True
        If True and only one log is inside a resulting pack, return that single Log object instead of the Pack.
    use_simpandas : bool | None, default None
    raise_error : bool, default False
    correct_units : bool, default True
    """
    if use_simpandas is not None and use_simpandas is True and not _params_.simpandas_:
        raise ModuleNotFoundError("SimPandas is not installed, please install it or set parameter `use_simpandas` to False.")
    use_simpandas = _params_.simpandas_ if use_simpandas is None else bool(use_simpandas)
    raise_error = _params_.raise_error_ if raise_error is None else bool(raise_error)
    if os.path.isfile(path):
        return _read_one(path, raise_error=raise_error, use_simpandas=use_simpandas, correct_units=correct_units)
    if type(path) is str:
        path = [path]
    if type(path) is not str and hasattr(path, '__iter__'):
        result = Pack()
        for each in path:
            for file in glob.iglob(each, recursive=recursive):
                result.append(_read_one(file, raise_error=raise_error, use_simpandas=use_simpandas, correct_units=correct_units))
        if squeeze:
            return result.squeeze()
        else:
            return result
