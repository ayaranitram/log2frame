# log2frame — User Manual

`log2frame` reads well log data in **LAS**, **LIS**, and **DLIS** formats and returns the curves as a unit-aware DataFrame.  
Curve data is stored in a `Log` object. When multiple files are loaded at once the result is a `Pack` of `Log` objects.

---

## Table of Contents

1. [Installation](#installation)
2. [Quick start](#quick-start)
3. [Reading log files](#reading-log-files)
   - [Single file](#single-file)
   - [Multiple files / glob patterns](#multiple-files--glob-patterns)
   - [Recursive search](#recursive-search)
4. [The `Log` object](#the-log-object)
   - [Attributes](#attributes)
   - [Accessing curves](#accessing-curves)
   - [Index operations](#index-operations)
   - [Unit conversion](#unit-conversion)
   - [Other methods](#other-methods)
5. [The `Pack` object](#the-pack-object)
   - [Accessing logs](#accessing-a-log-from-a-pack)
   - [Concatenating data](#concatenating-data)
   - [Adding logs to a Pack](#adding-logs-to-a-pack)
   - [Renaming wells](#renaming-wells)
   - [Copying a Pack](#copying-a-pack)
6. [Unit-aware mode (SimPandas)](#unit-aware-mode-simpandas)
7. [RFT utilities](#rft-utilities)
8. [Supported formats](#supported-formats)
9. [Dependencies](#dependencies)

---

## Installation

```bash
pip install --upgrade log2frame
```

To enable unit-aware mode, also install `simpandas`:

```bash
pip install --upgrade simpandas
```

---

## Quick start

```python
import log2frame

# Read a single file
log = log2frame.read('path/to/well.las')

# Read many files at once (returns a Pack)
pack = log2frame.read('path/to/data/**/*.*')

# Access curve 'GR'
gr = log['GR']

# Convert the depth index from feet to metres
log_m = log.index_to('m')

# Convert curve values
log_psi = log.to({'BHP': 'psi'})
```

---

## Reading log files

### Single file

```python
log = log2frame.read('well.las')
log = log2frame.read('well.dlis')
log = log2frame.read('well.lis')
```

Returns a `Log` instance.  
If the file contains multiple frames (DLIS, LIS), a `Pack` is returned instead.

### Multiple files / glob patterns

```python
pack = log2frame.read('sampledata/*.*')
```

Returns a `Pack`. Invalid or unrecognised files are silently skipped by default (`raise_error=False`).  
Set `raise_error=True` to raise exceptions for unreadable files.

### Recursive search

```python
pack = log2frame.read('sampledata/**/*.*')
```

`recursive=True` is the default, which enables `**` glob patterns.

### Parameters of `read()`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `path` | `str` | required | Path, glob pattern, or list of paths |
| `use_simpandas` | `bool` or `None` | `None` | Use SimDataFrame for curve data. `None` = auto-detect |
| `recursive` | `bool` | `True` | Whether glob patterns recurse into subdirectories |
| `raise_error` | `bool` | `False` | Raise exceptions on unreadable files |
| `squeeze` | `bool` | `True` | Return `Log` directly when a `Pack` has only one entry |
| `correct_units` | `bool` | `True` | Normalise unit strings using the built-in dictionary |

---

## The `Log` object

### Attributes

| Attribute | Type | Description |
|---|---|---|
| `.data` | `DataFrame` or `SimDataFrame` | Curve values, indexed by depth (or time) |
| `.header` | `DataFrame` | Parsed log header (mnemonic, unit, value, description) |
| `.units` | `Series` | Curve and index units keyed by mnemonic. **Note:** Multi-element Series; see [truthiness warning](#warning-pandas-truthiness). |
| `.units_dict()` | `dict` | Returns the ``.units`` Series as a plain Python dictionary. |
| `.source` | `str` | Path (or identifier) of the source file |
| `.well` | `str` | Well name extracted from the header |
| `.name` | `str` | UWI if present, otherwise `.well` |
| `.uwi` | `str` or `None` | Unique Well Identifier from header |
| `.index` | pandas `Index` | The depth / time index |
| `.index_name` | `str` | Mnemonic of the index curve |
| `.index_units` | `str` | Units of the index (normalised to lowercase canonical forms like `"m"` or `"ft"`) |
| `.curves` / `.columns` | Index | Column mnemonics (does not include the index column) |

#### <a name="warning-pandas-truthiness"></a> ⚠️ Warning: pandas truthiness

`Log.units` is a multi-element pandas `Series`. Because of how pandas handles truthiness, common Python idioms like `dict(log.units or {})` will raise a `ValueError` or silently fail in some contexts.

**Recommended usage:**
```python
# Safe way to get a dictionary of units
units = log.units_dict()

# If you need to check for empty units
if not log.units.empty:
    ...
```

### Accessing curves

```python
# By mnemonic
gr = log['GR']

# Slice by index value
section = log.data.loc[1000:1500]

# Check if a curve exists
'RHOB' in log       # True / False
```

Iteration over a `Log` yields column names:

```python
for mnemonic in log:
    print(mnemonic)
```

`len(log)` returns the number of depth samples.

### Index operations

#### `.index_to(units)` — convert the depth / time axis

Returns a **new** `Log` with the index converted. Does not modify the original.

```python
log_m   = log.index_to('m')    # feet → metres
log_ft  = log.index_to('ft')   # metres → feet

# Copy the index units from another Log
log_matched = log_a.index_to(log_b)
```

#### `.set_index(curve)`

Change the column used as the DataFrame index.

```python
log2 = log.set_index('TVD')          # new Log, original unchanged
log.set_index('TVD', inplace=True)   # modify in place, returns None
```

#### `.set_index_units(units)` / `.index_units` setter

Correct the index unit string when the source file contains a non-standard abbreviation:

```python
log.set_index_units('ft')
# equivalent to:
log.index_units = 'ft'
```

#### `.set_index_name(name)`

Rename the index mnemonic:

```python
log.set_index_name('DEPTH')
```

#### `.sort()`

Sort curves by index value:

```python
sorted_log = log.sort()              # returns a new Log
log.sort(inplace=True)               # modifies in place
```

### Unit conversion

Unit conversion of curve values requires **SimPandas** to be installed.

#### `.to(units, curve=None)`

Convert one or more curves to the requested units. Returns a new `Log`.

```python
# Single curve — two equivalent forms:
log_bar = log.to('bar', curve='BHP')
log_bar = log.to({'BHP': 'bar'})

# Multiple curves at once:
log_si  = log.to({'BHP': 'MPa', 'TEMP': 'degC'})

# Same target units for several curves:
log_psi = log.to('psi', curve=['BHP', 'WHP'])
```

### Other methods

#### `.copy()`

Deep copy of the `Log` (data, header and units DataFrames are all copied):

```python
log2 = log.copy()
```

#### `.rename(new_name)`

Change the well name stored inside the `Log`:

```python
log.rename('NEW-WELL-NAME')
```

#### `.units_dict()`

Returns the curve units mapping as a plain dictionary. This is safer than converting `.units` directly if you need to handle potential empty sets.

```python
units = log.units_dict()
gr_unit = units.get('GR', 'unknown')
```

#### `log[mnemonic] = values`

Add or replace a curve:

```python
log['GR_SMOOTH'] = log['GR'].rolling(5).mean()
```

---

## The `Pack` object

A `Pack` is an ordered collection of `Log` objects grouped by well name and source path.

### Summary

Displaying a `Pack` (or calling `.summary()`) shows a table of all loaded logs:

```python
pack              # or pack.summary()
```

| Column | Description |
|---|---|
| `well` | Well name |
| `curves` | Number of curve columns |
| `steps` | Number of depth samples |
| `index mnemonic` | Name of the depth / time index |
| `index units` | Units of the depth / time axis |
| `min index` / `max index` | Depth range |
| `curves mnemonics` | Comma-separated list of all curve names |
| `path` | Source file path |

### Accessing a `Log` from a `Pack`

```python
# By integer position (row in the summary table)
log = pack[0]
log = pack[3]

# By well name — returns a Log if only one file, a Pack if several
log  = pack['ALK001']
sub  = pack['WELL-A']      # Pack if WELL-A has multiple files

# By (well_name, source_path) tuple
log  = pack[('WELL-A', './data/WELL-A_run1.las')]
```

### Concatenating data

`.concat()` merges all logs in a `Pack` into a single DataFrame, adding `well` and `source` columns:

```python
df = pack.concat()
```

With SimPandas installed the result is a `SimDataFrame`; otherwise it is a plain `DataFrame`.

### Adding logs to a `Pack`

#### `+` operator — returns a new `Pack`

```python
new_pack = pack_a + pack_b    # merge two Packs
new_pack = pack   + log       # add a single Log
```

#### `.append()` — modifies in place

```python
pack.append(log)              # add a single Log
pack.append(other_pack)       # add all logs from another Pack
pack.append([log1, log2])     # add from a list
```

#### `pack[well] = log` — assignment syntax

```python
pack['NEW-WELL'] = log
```

### Removing logs

```python
pack.drop('WELL-A')                               # drop all files for a well
pack.drop('./data/WELL-A_run2.las')               # drop by source path
pack.drop(('WELL-A', './data/WELL-A_run2.las'))   # drop by (well, path) tuple
```

### Renaming wells

Renames the well in the `Pack` index **and** inside each contained `Log`:

```python
pack.rename('OLD-NAME', 'NEW-NAME')
```

### Copying a `Pack`

Deep copy of the entire `Pack` including all `Log` objects:

```python
pack2 = pack.copy()
```

---

## Unit-aware mode (SimPandas)

When `simpandas` is installed, `log2frame` automatically uses `SimDataFrame` to store curve data so that unit labels travel with the data through every operation.

### Behaviour

| `simpandas` installed | `use_simpandas` kwarg | Curve data type |
|---|---|---|
| Yes | `None` (default) | `SimDataFrame` |
| Yes | `True` | `SimDataFrame` |
| Yes | `False` | `pandas.DataFrame` |
| No | `None` (default) | `pandas.DataFrame` |
| No | `True` | raises `ModuleNotFoundError` |
| No | `False` | `pandas.DataFrame` |

### Forcing plain pandas

```python
log = log2frame.read('well.las', use_simpandas=False)
```

### Checking which backend is active

```python
import log2frame
print(log2frame._params_.simpandas_)   # True / False
```

### With SimPandas — unit-propagating operations

```python
log = log2frame.read('well.las')

# Index conversion — units are correct in the returned Log
log_m = log.index_to('m')
print(log_m.index_units)    # 'm'

# Curve conversion
log_si = log.to({'GR': 'API', 'RHOB': 'g/cm3'})
print(log_si.units)
```

### Without SimPandas — manual unit tracking

When SimPandas is not installed, `.to()` logs a warning and returns the unchanged `Log`. Index conversion via `unyts` still works for the depth axis; only curve-value conversion is unavailable.

---

## RFT utilities

`log2frame` includes helper functions for reading RFT / MDT pressure data stored in `.ASC` files alongside a computed log in `.LAS` format.

### `rft_summary(folder_path)`

Reads all `.ASC` files in a folder and merges them with any `*COMPUTED*.LAS` file found in the same folder:

```python
import log2frame

df = log2frame.rft_summary('./well_rft/')
```

Returns a `DataFrame` with the raw RFT table columns plus `SUCCESS` (whether each sample depth existed in the computed log).

### `rft_summaries_from_folders(folder_path)`

Iterates over all subfolders of `folder_path`, calling `rft_summary` on each, and concatenates the results:

```python
df_all = log2frame.rft_summaries_from_folders('./all_wells/')
```

Each row is labelled with the subfolder name in the `FOLDER_NAME` column.

---

## Supported formats

| Extension | Library | Notes |
|---|---|---|
| `.las` | `lasio` | LAS 1.2, 2.0 |
| `.dlis` | `dlisio` | Single and multi-frame physical files |
| `.lis`, `.lti` | `dlisio` | Single and multi-run physical files |

---

## Dependencies

| Package | Purpose |
|---|---|
| `pandas` | Header and metadata storage; fallback curve data |
| `numpy` | Fast array operations |
| `lasio` | LAS file parsing |
| `dlisio` | DLIS and LIS file parsing |
| `unyts >= 1.0.1` | Unit string recognition and conversion (index axis) |
| `simpandas >= 0.90.7` | Unit-aware DataFrame backend for curve data (optional but recommended) |
