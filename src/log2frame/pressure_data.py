import pandas as pd
from .log import Log
from .__init__ import read as read_log_

def get_col_width(line):
    if len(line) == 0:
        return []
    cols_steps = []
    for i in range(len(line)):
        if line[i] != ' ' and i == 0:
            cols_steps.append(i)
        elif line[i] != ' ' and i == 1 and line[i-1] == ' ':
            cols_steps.append(i)
        elif line[i] != ' ' and line[i-2:i] == '  ':
            cols_steps.append(i)
    return cols_steps


def split_by_col_width(line, cols_width):
    output = [line[cols_width[i]: cols_width[i+1]] for i in range(len(cols_width)-1) if cols_width[i+1] < len(line)]
    if cols_width[-1] < len(line):
        output += [line[cols_width[-1]:]]
    else:
        last = max([w for w in cols_width if w < len(line)])
        output += [line[last:]]
    return output


def read_inf(path):
    header = {}
    data = []
    header_ = True
    data_header_flag = 0
    data_header = ''
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
            if key == 'PRESSURE DATA':
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
    if len(data_header) < len(data):
        data_header = data_header + [None] * (len(data) - len(data_header))
    elif len(data_header) > len(data):
        data = data + [[None] * len(data[0])] * (len(data_header) - len(data))

    return pd.DataFrame(data={data_header[i]: data[i] for i in range(len(data_header))})


def extract_inf(dataframe):
    for col in dataframe.select_dtypes(object):
        try:
            dataframe[col] = dataframe[col].astype(int)
        except:
            try:
                dataframe[col] = dataframe[col].astype(int)
            except:
                try:
                    dataframe[col] = pd.to_datetime(dataframe[col])
                except:
                    pass
    for col in dataframe.select_dtypes(object):
        if dataframe[col].str.contains('@').all():
            dataframe['KIND'] = [each.split('@')[0].strip() for each in dataframe[col]]
            dataframe['DEPTH'] = [each.split('@')[1].strip() for each in dataframe[col]]
            dataframe['KIND'] = dataframe['KIND'].astype('category')
            try:
                dataframe['DEPTH'] = dataframe['DEPTH'].astype(float)
                break
            except:
                pass


def read_log(path):
    return read_log_(path).data


def merge_and_label(dataframe, log):
    result = pd.merge(dataframe, log.reset_index(), right_on=log.index.name, left_on='DEPTH', how='outer')
    result['SUCESS'] = [(depth in log.index) for depth in dataframe['DEPTH']]
    return result






