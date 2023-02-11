# -*- coding: utf-8 -*-
"""
Created on Tue Jan 24 21:21:21 2023

@author: Martín Carlos Araya <martinaraya@gmail.com>
"""
import logging
import pandas as pd
from .log import Log, Log2FrameType


__version__ = '0.1.1'
__release__ = 20230210
__all__ = ['Pack', 'concat']


def concat(logs, use_simpandas=None):
    if use_simpandas is None:
        from .__init__ import _params_
        use_simpandas = _params_.simpandas_
    if use_simpandas:
        from simpandas import concat as _concat, SimDataFrame as _Frame
    else:
        from pandas import concat as _concat, DataFrame as _Frame
        logging.warning("Not able to guarantee units conversion, because not using SimDataFrame.")

    if type(logs) in (list, tuple):
        for each in logs:
            if not isinstance(each, Log):
                raise TypeError("Can only concatenate objects of type Log, not of type '" + str(type(each)) + "'.")
        return _concat([_concat([each.data, _Frame({'well': [each.name] * len(each.data),
                                                    'source': [each.source] * len(each.data)},
                                                   index=each.index,
                                                   dtype='category')], axis=1)
                        for each in logs], axis=0)
    elif isinstance(logs, Pack):
        return concat([logs.data[w][f] for w in logs.data.keys() for f in logs.data[w]])


class Pack(object, metaclass=Log2FrameType):
    valid_instances_ = (Log,)

    def __init__(self, data=None, **kwargs):
        if 'use_simpandas' in kwargs:
            self.simpandas_ = kwargs['use_simpandas']
        else:
            from .__init__ import _params_
            self.simpandas_ = _params_.simpandas_
        if self.simpandas_:
            from simpandas import SimDataFrame
            Pack.valid_instances_ = (SimDataFrame, Log)
        self.data = {}
        if 'data_from_dict' in kwargs:
            self.data = kwargs['data_from_dict']
        self.summary_ = None
        if type(data) is dict:
            self.from_dict(data)
        elif data is not None:
            self.append(data)

    def append(self, data, well=None, source_path=None):
        if isinstance(data, (list, Pack)):
            for each in data:
                self.append(data=each)
            return None
        elif data is None:
            return None
        else:
            if well is None and isinstance(data, Pack.valid_instances_):
                well = data.name
            if source_path is None and isinstance(data, Pack.valid_instances_):
                source_path = data.source

            if well not in self.data:
                self.data[well] = {source_path: data}
            else:
                if source_path is not None and source_path in self.data[well]:
                    logging.warning("The file '" + str(source_path) + "' is already loaded. It will be overwritten.")
                self.data[well][source_path] = data

    def copy(self):
        result = Pack(data_from_dict={well: {path: log.copy() for path, log in self.data[well].items()} for well in self.data},
                      use_simpandas=self.simpandas_)
        return result

    def __copy__(self):
        return self.copy()

    def __contains__(self, well):
        return well in self.summary()['well'].values

    def __add__(self, other):
        if isinstance(other, Pack.valid_instances_ + (Pack,)):
            result = self.copy()
            result.append(other)
            return result
        else:
            raise NotImplementedError("Addition of Pack and '" + str(type(other)) + "' is not implemented.")

    def update(self, data):
        if isinstance(data, Pack):
            self.append(data)
        if type(data) is dict:
            for key, value in data.data:
                self.append(data=value, source_path=key)

    def squeeze(self):
        if len(self.data) == 1 and len(self.data[list(self.data.keys())[0]]) == 1:
            return self.data[list(self.data.keys())[0]]
        else:
            return self

    def __iter__(self):
        self._iter_ = [0, len(self)]
        return self

    def __next__(self):
        if self._iter_[0] < self._iter_[1]:
            next_, self._iter_[0] = self._iter_[0], self._iter_[0] + 1
            return self.__getitem__(next_)
        else:
            raise StopIteration

    def summary(self, reload=False):
        if not reload and self.summary_ is not None and len(self.summary_) == len(self):
            pass
        else:
            wells = [w for w in self.data for f in self.data[w]]
            mnemonic = [', '.join(self.data[w][f].keys()) for w in self.data for f in self.data[w]]
            curves = [len(self.data[w][f].keys()) for w in self.data for f in self.data[w]]
            path = [f for w in self.data for f in self.data[w]]
            rows = [len(self.data[w][f]) for w in self.data for f in self.data[w]]
            index_names = [self.data[w][f].index_name for w in self.data for f in self.data[w]]
            index_units = [self.data[w][f].index_units for w in self.data for f in self.data[w]]
            min_index = [min(self.data[w][f].index) for w in self.data for f in self.data[w]]
            max_index = [max(self.data[w][f].index) for w in self.data for f in self.data[w]]
            self.summary_ = pd.DataFrame(data={'well': wells,
                                               'curves': curves,
                                               'steps': rows,
                                               'index mnemonic': index_names,
                                               'index units': index_units,
                                               'min index': min_index,
                                               'max index': max_index,
                                               'curves mnemonics': mnemonic,
                                               'path': path})
        return self.summary_

    def from_dict(self, dictionary):
        for key in dictionary:
            if isinstance(dictionary[key], Pack.valid_instances_):
                src = (dictionary[key].source, key)
            else:
                src = key
            self.append(data=dictionary[key], source_path=src)

    def __repr__(self):
        return self.summary().__repr__()

    def _repr_html_(self):
        return self.summary()._repr_html_()

    def __len__(self):
        return sum([1 for w in self.data for f in self.data[w]])

    def __getitem__(self, well):
        if well not in self.data and type(well) is int and well < len(self):
            well, source = [(w, f) for w in self.data for f in self.data[w]][well]
            return self.data[well][source]
        elif well in self.data:
            result = list(self.data[well].values())
            if len(result) == 1:
                return result[0]
        elif well in [f for w in self.data for f in self.data[w]]:
            well_name = [w for w in self.data for f in self.data[w] if f == well]
            result = [self.data[w] for w in well_name for f in self.data[w] if f == well]
            if len(result) == 1:
                return result[0]
        elif type(well) is tuple and len(well) == 2:
            well, source = well[0], well[1]
            if well in self.data and source in self.data[well]:
                return self.data[well][source]
            else:
                ValueError(str(well) + " is not an index in this Pack.")
        else:
            raise ValueError(str(well) + " is not an index in this Pack.")
        return Pack(result)

    def __setitem__(self, well, data):
        if type(data) is tuple and len(data) == 2:
            if isinstance(data[0], (Log, Pack)) and type(data[1]) is str:
                data, source_path = data[0], data[1]
            elif isinstance(data[1], (Log, Pack)) and type(data[0]) is str:
                data, source_path = data[1], data[0]
            else:
                raise TypeError("data must be a Log, Pack or path to log file.")
        elif type(data) is tuple and len(data) == 1:
            if isinstance(data[0], (Log, Pack)):
                data, source_path = data[0], None
            elif type(data[0]) is str:
                from .__init__ import read
                data, source_path = read(data[0]), data[0]
            else:
                raise TypeError("data must be a Log, Pack or path to log file.")
        elif isinstance(data, (Log, Pack)):
            source_path = None
        else:
            raise TypeError("data must be a Log, Pack or path to log file.")
        return self.append(data=data, well=well, source_path=source_path)

    def concat(self, list_of_Log: list = None):
        if list_of_Log is None:
            return concat(self, use_simpandas=self.simpandas_)
