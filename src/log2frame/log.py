# -*- coding: utf-8 -*-
"""
Created on Tue Jan 24 21:53:17 2023

@author: Martín Carlos Araya <martinaraya@gmail.com>
"""
import logging

import pandas as pd
import unyts


__version__ = '0.1.3'
__release__ = 20230219
__all__ = ['Log']


class Log2FrameType(type):
    def __repr__(self):
        return self.__name__


class Log(object, metaclass=Log2FrameType):

    def __init__(self, data=None, header=None, units=None, source=None, well=None):
        self.data = data
        self.header = header
        self.units = units
        self.source = source
        self.uwi = self.header['UWI'] if 'UWI' in self.header else None
        if well is None:
            self.well = self.header['WN'] if 'WN' in self.header else self.header['WELL'] if 'WELL' in self.header else self.uwi
        else:
            self.well = well

    def __add__(self, other):
        from .pack import Pack
        if isinstance(other, Pack):
            return other.__add__(self)
        elif isinstance(other, Pack.valid_instances_):
            new_pack = Pack()
            new_pack.append(self)
            new_pack.append(other)
            return new_pack
        else:
            raise NotImplementedError("Addition of Log and '" + str(type(other)) + "' is not implemented.")

    def __contains__(self, curve):
        return curve in self.data or curve == self.index_name

    def __copy__(self):
        return self.copy()

    def __getitem__(self, mnemonics):
        try:
            return self.data[mnemonics]
        except:
            try:
                return self.data.loc[mnemonics]
            except:
                try:
                    return self.data.iloc[mnemonics]
                except:
                    raise KeyError("'" + str(mnemonics) + "' is not a curve name and is not a value in the index.")

    def __iter__(self):
        return self

    def __len__(self):
        return len(self.data)

    def __next__(self):
        for curve in self.data.columns:
            yield curve

    def __repr__(self):
        return self.data.__repr__()

    def _repr_html_(self):
        return self.data._repr_html_()

    def __setitem__(self, mnemonics, curve):
        self.data[mnemonics] = curve

    @property
    def columns(self):
        return self.keys()

    def copy(self):
        return Log(data=self.data.copy(),
                   header=self.header.copy(),
                   units=self.units.copy(),
                   source=self.source,
                   well=self.well)

    @property
    def curves(self):
        return self.keys()

    @property
    def index(self):
        return self.data.index

    @index.setter
    def index(self, index):
        self.data.index = index

    @property
    def index_name(self):
        return self.data.index.name

    @index_name.setter
    def index_name(self, name):
        self.data.index.name = name

    @property
    def index_units(self):
        if hasattr(self.data, 'index_units'):
            return self.data.index_units
        elif self.data.index.name in self.units:
            return self.units[self.data.index.name]
        else:
            logging.warning("index units are not defined.")

    @index_units.setter
    def index_units(self, units: str):
        self.set_index_units(units)

    def keys(self):
        return self.data.columns

    @property
    def meta(self):
        return self.header

    @property
    def path(self):
        return self.source

    def set_index_name(self, name):
        self.data.index.name = name

    def set_index_units(self, units: str):
        if hasattr(self.data, 'set_index_units'):
            self.data.set_index_units(units)
        if self.data.index.name in self.units:
            self.units[self.data.index.name] = units.split()

    def index_to(self, index_units: str):
        if isinstance(index_units, Log):
            index_units = index_units.index_units
        if hasattr(self.data, 'index_to'):
            data = self.data.index_to(index_units)
            if data.index.units == self.data.index.units:
                logging.warning("index units not converted!")
                units = self.units
            else:
                units = pd.Series(data.get_units())
            return Log(data=data,
                       header=self.header,
                       units=units,
                       source=self.source,
                       well=self.well)
        elif unyts.convertible(self.index_units, index_units):
            new_index = pd.Index(unyts.convert(self.index, self.index_units, index_units), name=self.index_name)
            new_data = self.data.copy()
            new_data.index = new_index
            new_units = self.units.copy()
            new_units[self.index_name] = index_units
            return Log(data=new_data,
                       header=self.header,
                       units=new_units,
                       source=self.source,
                       well=self.well)
        elif unyts.convertible(self.index_units.lower(), index_units):
            new_index = pd.Index(unyts.convert(self.index, self.index_units.lower(), index_units), name=self.index_name)
            new_data = self.data.copy()
            new_data.index = new_index
            new_units = self.units.copy()
            new_units[self.index_name] = index_units
            return Log(data=new_data,
                       header=self.header,
                       units=new_units,
                       source=self.source,
                       well=self.well)
        elif not unyts.convertible(self.index_units, index_units):
            from .__init__ import _params_
            msg = "Not possible to convert '" + str(self.index_name) + "' from '" + str(self.index_units) + "' to '" + str(index_units) + "'."
            if _params_.raise_error_:
                raise ValueError(msg)
            else:
                logging.warning(msg)
        else:
            from .__init__ import _params_
            msg = "index_to not implemented without SimPandas or Unyts."
            if _params_.raise_error_:
                raise NotImplementedError(msg)
            else:
                logging.warning(msg)
            return self

    @property
    def name(self):
        if self.uwi is not None:
            return self.uwi
        elif self.well is not None:
            return self.well

    @name.setter
    def name(self, new_name: str):
        self.rename(new_name)

    def rename(self, new_name: str):
        new_name = str(new_name).strip()
        self.well = new_name
        if hasattr(self.data, "name"):
            self.data.name = new_name

    def set_index(self, curve, inplace=False):
        inplace = bool(inplace)
        if curve == self.index_name:
            logging.warning(str(curve) + " is already the index of this Log.")
            return None if inplace else self
        elif curve in self.data.columns:
            if inplace:
                self.data.set_index(curve, inplace=True)
                return None
            else:
                return Log(data=self.data.set_index(curve),
                           header=self.header,
                           units=self.units,
                           source=self.source,
                           well=self.well)
        else:
            from .__init__ import _params_
            msg = str(curve) + " is not present in this Log."
            if _params_.raise_error_:
                raise ValueError(msg)
            else:
                logging.warning(msg)

    def to(self, units, curve=None):
        if curve is not None:
            if type(curve) is str and type(units) is str:
                if curve in self:
                    units = {curve: units}
                elif units in self:
                    units = {units: curve}
                else:
                    logging.warning("The curve '" + str(curve) + "' is not present in this Log.")
                    return self
            elif type(units) is dict:
                logging.warning("`units` is a dictionary, curve will be ignored.")
            elif type(curve) is not str and hasattr(curve, '__iter__') and type(units) is str:
                units = {curv: units for curv in curve}
            elif type(curve) is not str and hasattr(curve, '__iter__') \
                    and type(units) is not str and hasattr(units, '__iter__') \
                and len(curve) == len(units):
                units = dict(zip(curve, units))
            else:
                logging.warning("`curve` must be str or iterable. If `units` is iterable, curves and units must have the same length.")
        if hasattr(self.data, 'index_to'):
            data = self.data.to(units)
            units = pd.Series(data.get_units())
            return Log(data=data,
                       header=self.header,
                       units=units,
                       source=self.source,
                       well=self.well)
        else:
            logging.warning("Units conversion not implemented without SimPandas.")
            return self
