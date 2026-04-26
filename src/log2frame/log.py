# -*- coding: utf-8 -*-
"""
Created on Tue Jan 24 21:53:17 2023

@author: Martín Carlos Araya <martinaraya@gmail.com>
"""
import logging
import pandas as pd
import unyts


__version__ = '0.2.2'
__release__ = 20260427
__all__ = ['Log']

logging.basicConfig(level=logging.INFO)


class Log2FrameType(type):
    def __repr__(self):
        return self.__name__


class Log(object, metaclass=Log2FrameType):
    """A single well-log file represented as a units-aware container.

    Public attributes
    -----------------
    name : str
        Well name (from the ``WELL`` mnemonic).
    uwi : str | None
        Unique Well Identifier (from ``UWI`` / ``API``); ``None`` if absent.
    path : str
        Path to the source file.
    source : str
        Format identifier — ``"LAS"`` / ``"DLIS"`` / ``"LIS"``.
    data : SimDataFrame | DataFrame
        Curves, indexed by depth.
    columns : list[str]
        Curve mnemonics.
    index_units : str
        Unit of the depth index (``"M"`` / ``"FT"`` / …).
    units : pandas.Series
        Per-mnemonic units. **Multi-element Series**; do not test for
        truthiness directly — see :meth:`units_dict`.
    well : object
        WELL-section attribute access (``log.well.STRT`` etc.).
    header, meta, curves : ...
        Free-form access to the LAS / DLIS sections.

    Methods
    -------
    index_to(unit) → Log
        Return a copy with the depth index converted to *unit*.
    to(unit) → Log
        Convert *all* curves to *unit* where the conversion is defined.
    set_index(curve), set_index_name(name), set_index_units(unit)
        Mutators on the depth index.
    rename, copy, sort, keys
        DataFrame-style helpers.
    """

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
        self._iter_index = 0
        return self

    def __len__(self):
        return len(self.data)

    def __next__(self):
        if self.data is None or not hasattr(self.data, 'columns'):
            raise StopIteration
        if self._iter_index >= len(self.data.columns):
            raise StopIteration
        curve = self.data.columns[self._iter_index]
        self._iter_index += 1
        return curve

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
        return Log(data=self.data.copy() if hasattr(self.data, 'copy') else self.data,
                   header=self.header.copy() if self.header is not None and hasattr(self.header, 'copy') else self.header,
                   units=self.units.copy() if self.units is not None and hasattr(self.units, 'copy') else self.units,
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
        units_str = None
        if hasattr(self.data, 'index_units'):
            units_str = self.data.index_units
        elif self.data.index.name in self.units:
            units_str = self.units[self.data.index.name]
        else:
            logging.warning("index units are not defined.")
            
        if isinstance(units_str, str):
            _DEPTH_UNIT_CANONICAL = {
                "m": "m", "metre": "m", "meter": "m", "meters": "m", "metres": "m",
                "ft": "ft", "foot": "ft", "feet": "ft",
            }
            return _DEPTH_UNIT_CANONICAL.get(units_str.strip().lower(), units_str)
        return units_str

    @index_units.setter
    def index_units(self, units: str):
        self.set_index_units(units)

    @property
    def units(self) -> pd.Series:
        """Per-mnemonic units as a pandas ``Series`` (not a dict).

        .. note::
            ``Log.units`` is a multi-element ``Series``, **not** a dict.
            The conventional ``dict(log.units or {})`` pattern silently
            evaluates to ``{}`` because of pandas' truthiness behaviour.
            Use :meth:`units_dict` or ``dict(log.units)`` explicitly.
        """
        return self._units

    @units.setter
    def units(self, value):
        self._units = value

    def units_dict(self) -> dict:
        """Return the curve→unit mapping as a plain ``dict``.

        Use this instead of ``dict(log.units)`` if you want to support both
        the (unusual) zero-curve case and the normal multi-curve case in a
        single line.

        >>> units = log.units_dict()
        >>> units.get('GR', 'unknown')
        'gAPI'
        """
        if self._units is None:
            return {}
        s = self._units
        if hasattr(s, "empty") and s.empty:
            return {}
        return dict(s)

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
        if units is None:
            return
        units = str(units)
        if hasattr(self.data, 'set_index_units'):
            try:
                self.data.set_index_units(units)
            except Exception:
                pass
        if self.units is not None and self.data.index.name in self.units:
            self.units[self.data.index.name] = units

    def index_to(self, index_units: str):
        if isinstance(index_units, Log):
            index_units = index_units.index_units
        if hasattr(self.data, 'index_to') and callable(self.data.index_to):
            current_units = getattr(self.data.index, 'units', None)
            if current_units == index_units:
                logging.info("index units are already '" + str(index_units) + "'.")
                return self
            data = self.data.index_to(index_units)
            new_units = getattr(data.index, 'units', None)
            if new_units == current_units:
                logging.warning("index units not converted!")
                units = self.units
            else:
                units = pd.Series(data.get_units()) if hasattr(data, 'get_units') else self.units
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
                logging.error(msg)
        else:
            from .__init__ import _params_
            msg = "index_to not implemented without SimPandas or Unyts."
            if _params_.raise_error_:
                raise NotImplementedError(msg)
            else:
                logging.error(msg)
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

    def rename(self, new_name: str, inplace=True):
        new_name = str(new_name).strip()
        if inplace:
            self.well = new_name
            if hasattr(self.data, "name"):
                self.data.name = new_name
        else:
            result = self.copy()
            result.well = new_name
            if hasattr(result.data, "name"):
                result.data.name = new_name

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
                logging.error(msg)

    def sort(self, inplace=False):
        if inplace:
            self.data.sort_index(inplace=True)
        else:
            result = self.copy()
            result.data.sort_index(inplace=True)
            return result

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
        if hasattr(self.data, 'to'):
            data = self.data.to(units)
            units = pd.Series(data.get_units()) if hasattr(data, 'get_units') else self.units
            return Log(data=data,
                       header=self.header,
                       units=units,
                       source=self.source,
                       well=self.well)
        else:
            logging.warning("Units conversion not implemented without SimPandas.")
            return self
