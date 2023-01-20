# -*- coding: utf-8 -*-
"""
Created on Thu Jan 19 19:01:21 2023

@author: Martín Carlos Araya <martinaraya@gmail.com>
"""
from .las import las2frame
from .dlis import dlis2frame

__version__ = '0.0.2'
__release__ = 20230119
__all__ = ['read', 'las2frame', 'dlis2frame']


def read(path: str):
    if path.split('.')[-1].lower() == 'las':
        return las2frame(path)
    elif path.split('.')[-1].lower() == 'dlis':
        return dlis2frame(path)
    else:
        raise ValueError("`path` should be a '.las' or '.dlis' file")
