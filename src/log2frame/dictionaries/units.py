# -*- coding: utf-8 -*-
"""
Created on Tue Feb 21 17:50:05 2023

@author: Martín Carlos Araya <martinaraya@gmail.com>
"""

import json
from os.path import dirname
from pathlib import Path

this_path_ = Path(__file__).with_name('units_dictionary.json').absolute()
this_path_ = dirname(this_path_) + '/'

try:
    with open(this_path_ + 'units_dictionary.json', 'r') as f:
        units_correction_dict_ = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    import warnings
    warnings.warn(
        f"log2frame: units-correction dictionary not found "
        f"({type(e).__name__}: {e}); proceeding with unit-correction disabled.",
        UserWarning,
    )
    units_correction_dict_ = {}


def correct_units(units):
    if type(units) is dict:
        return {k: (units_correction_dict_[u]
                    if u in units_correction_dict_
                    else u)
                for k, u in units.items()}
    elif type(units) is str and units in units_correction_dict_:
        return units_correction_dict_[units]
    else:
        return units
