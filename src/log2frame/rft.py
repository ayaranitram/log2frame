"""
Created on Sun Feb  5 19:54:23 2023

@author: Martín Carlos Araya <martinaraya@gmail.com>
"""

import pandas as pd
import glob
import os
from .__init__ import read as read_log_

__version__ = '0.1.2'
__release__ = 20230221
__all__ = ['rft_summaries_from_folders', 'rft_summary']


def get_col_width(line: str) -> list:
    if len(line) == 0:
        return []
    cols_steps = []
    for i in range(len(line)):
        if line[i] != ' ' and i == 0:
            cols_steps.append(i)
        elif line[i] != ' ' and i == 1 and line[i - 1] == ' ':
            cols_steps.append(i)
        elif line[i] != ' ' and line[i - 2:i] == '  ':
            cols_steps.append(i)
    return cols_steps


def split_by_col_width(line: str, cols_width: list) -> list:
    output = [line[cols_width[i]: cols_width[i + 1]] for i in range(len(cols_width) - 1) if
              cols_width[i + 1] < len(line)]
    if cols_width[-1] < len(line):
        output += [line[cols_width[-1]:]]
    else:
        last = max([w for w in cols_width if w < len(line)])
        output += [line[last:]]
    return output


def read_asc_info(path: str) -> pd.DataFrame:
    header = {}
    data = []
    header_ = True
    data_header_flag = 0
    data_header = ''
    if not os.path.isfile(path):
        raise FileNotFoundError("The file '" + str(path) + "' does not exist.")
    if type(path) is str:
        path = path.replace('\\', '/')

    with open(path) as f:
        text = f.readlines()

    for line in text:
        line = line.strip()
        if len(line) == 0:
            continue
        if header_:
            split_line = line.split(':')
            if len(split_line) == 0:
                pass
            if len(split_line) == 1:
                key, value = split_line[0].strip(), None
            elif len(split_line) == 2:
                key, value = split_line[0].strip(), split_line[1].strip()
            else:
                key, value = split_line[0].strip(), ', '.join(split_line[1:])
            header[key] = value
            if key.upper() in ['PRESSURE RAW DATA', 'PRESSURE DATA']:
                header_ = False
        else:
            if line.count('-') == len(line):
                if data_header_flag == 0:
                    data_header_flag = 1
                elif data_header_flag >= 1:
                    data_header_flag = 3
                continue
            if data_header_flag == 1:
                cols_width = get_col_width(line)
                data_header = [split_by_col_width(line, cols_width)]
                data_header_flag = 2
            elif data_header_flag == 2:
                data_header.append(split_by_col_width(line, cols_width))
            elif data_header_flag == 3:
                data.append(split_by_col_width(line, cols_width))
            else:
                if ':' in line:
                    key, value = line.split(':')
                else:
                    key, value = line, None
                header[key] = value

    max_cols = -1
    if len(data_header) > 0:
        max_cols = max([len(each) for each in data_header])
        data_header = [(each + [''] * (max_cols - len(each))) for each in data_header]
        data_header = [[data_header[i][j].strip() for i in range(len(data_header))] for j in range(len(data_header[0]))]
        data_header = [(' '.join(each)).strip() for each in data_header]
    if len(data) > 0:
        max_cols = max_cols if max_cols > 0 else max([len(each) for each in data])
        data = [(each + [''] * (max_cols - len(each))) for each in data]
        data = [[data[i][j].strip() for i in range(len(data))] for j in range(len(data[0]))]
    elif len(data) == 0:
        return None
    if len(data_header) < len(data):
        data_header = data_header + [''] * (len(data) - len(data_header))
    elif len(data_header) > len(data):
        data = data + [[''] * len(data[0])] * (len(data_header) - len(data))
    result = pd.DataFrame(data={data_header[i]: data[i] for i in range(len(data_header))})
    for key, value in header.items():
        result[key] = value
    return result


def extract_info(info_df: pd.DataFrame) -> None:
    for col in info_df.select_dtypes(object):
        if col.upper() in ['WELL', 'WELL_NAME', 'WELL NAME', 'WELLBORE', 'HOLE SECTION', 'WN']:
            continue
        try:
            info_df[col] = info_df[col].astype(int)
        except:
            try:
                info_df[col] = info_df[col].astype(int)
            except:
                try:
                    info_df[col] = pd.to_datetime(info_df[col])
                except:
                    pass
    might_be = {}
    for col in info_df.select_dtypes(object):
        if info_df[col].str.contains('@').all():
            info_df['KIND'] = [each.split('@')[0].strip().lower() for each in info_df[col]]
            info_df['DEPTH'] = [each.split('@')[1].strip() for each in info_df[col]]
            info_df['KIND'] = info_df['KIND'].astype('category')
            try:
                info_df['DEPTH'] = info_df['DEPTH'].astype(float)
                might_be = {}
                break
            except:
                pass
        elif info_df[col].str.contains('@').any():
            might_be[col] = info_df[col].str.contains('@').sum()
    if len(might_be) > 0:
        col = [col for col, count in might_be.items() if count == max(might_be.values())][0]
        info_df['KIND'] = [each.split('@')[0].strip().lower() for each in info_df[col]]
        info_df['DEPTH'] = [None if '@' not in each else each.split('@')[1].strip() for each in info_df[col]]
        info_df['KIND'] = info_df['KIND'].astype('category')
        try:
            info_df['DEPTH'] = info_df['DEPTH'].astype(float)
        except:
            pass


def read_mdt_log(path: str) -> pd.DataFrame:
    return read_log_(path).data


def merge_and_label(info_df, log_df):
    result = pd.merge(info_df, log_df.reset_index(), right_on=log_df.index.name, left_on='DEPTH', how='left')
    result['SUCCESS'] = [(depth in log_df.index) for depth in info_df['DEPTH']]
    return result


def rft_summary(folder_path: str) -> pd.DataFrame:
    if len(folder_path) == 0:
        raise ValueError("`folder_path` must not be empty.")
    if os.path.isfile(folder_path):
        folder_path =  '/'.join(folder_path.replace('\\', '/').split('/')[:-1])
    if not os.path.isdir(folder_path):
        raise FileNotFoundError("The folder '" + str(folder_path) + "' does not exist.")
    folder_path = folder_path.replace('\\', '/')
    if folder_path[-1] != '/':
        folder_path = folder_path + '/'

    rft_sum = [read_asc_info(file) for file in glob.glob(folder_path + '*.ASC')]
    rft_sum = [each for each in rft_sum if each is not None]
    if len(rft_sum) == 0:
        return None
    elif len(rft_sum) == 1:
        rft_sum = rft_sum[0]
    else:
        rft_sum = pd.concat(rft_sum, axis=0)
    extract_info(rft_sum)

    rft_log = [read_mdt_log(file) for file in glob.glob(folder_path + '*COMPUTED*.LAS')]
    if len(rft_log) == 0:
        rft_sum['SUCCESS'] = None
        return rft_sum
    elif len(rft_log) == 1:
        rft_log = rft_log[0]
    else:
        rft_log = pd.concat(rft_log, axis=0)

    return merge_and_label(rft_sum, rft_log)


def rft_summaries_from_folders(folder_path: str) -> pd.DataFrame:
    wells_folders = [f.path for f in os.scandir(folder_path) if f.is_dir()]
    if len(wells_folders) == 0:
        raise FileNotFoundError("`folder_path` must be a folder containing one subfolder for each well.")
    wells_data = {}
    for folder in wells_folders:
        print("reading:", folder)
        df = rft_summary(folder)
        if df is None:
            continue
        folder = folder.replace('\\', '/').split('/')[-1]
        df['FOLDER_NAME'] = folder
        wells_data[folder] = df
    if len(wells_data) == 1:
        wells_data = wells_data[0]
    else:
        wells_data = pd.concat(wells_data, axis=0)
    return wells_data
