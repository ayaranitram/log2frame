from welly import Well
import os.path

try:
    import simpandas as spd
    simpandas = True
except ModuleNotFoundError:
    import pandas as pd

    simpandas = False

__version__ = '0.0.0'
__release__ = 20230119


def dlis2frame(path: str):
    if not os.path.isfile(path):
        raise FileNotFoundError("The provided path can't be found:\n" + str(path))
    physical_file = dlis.load(path)
    frames = {}
    for logical_file in physical_file:
        for frame in logical_file.frames:
            frame_units = {channel.name: channel.units for channel in frame.channels}
            frames[frame.name] = (pd.DataFrame(frame.curves()), pd.Series(frame_units, name='frame_units'))
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
