import pandas as pd
import re
import numpy as np
from datetime import datetime
import json


def createScope(data, regex, name, debug=False):
    r = re.compile(regex)
    files = list(filter(r.match, data))
    if debug:
        print("Files for " + name + ": " + str(files))
    return PrivacyScope(files, name)


def createLogScope(data, logs, debug=False):
    chatlog = createScope(data, logs[0], logs[1], debug=debug)
    chatlog.time_col = "time"
    chatlog.time_cut_tail = 0
    chatlog.time_format = 'epoch'
    chatlog.as_df()
    return chatlog


class PrivacyScope:

    def __init__(self, filenames, name):
        self.name = name
        self.filenames = filenames
        self.time_format = '%b %d, %Y %X.%f'
        self.time_cut_tail = -7
        self.time_col = 'frame.time'
        self.filter_func = lambda df, args: df
        self.df = None
        self.ip_search_enabled = False
        self.cache_search_enabled = False
        self.cache_timing = pd.Timedelta("300 seconds")
        self.generated = False

    def __repr__(self):
        return str(self)

    def __str__(self):
        return self.name

    def start_time(self):
        return self.as_df().index.min()

    def set_offset(self, timeoffset):
        self.timeoffset = timeoffset
        self.as_df()
        self.df.index += timeoffset
        # print("after offset", self.df)

    def set_index(self, col_name):
        df = self.as_df()
        # print("after as_df", df, df.columns)
        df.set_index(col_name, inplace=True)
        self.df = df
        # print("after set_index", self.df, self.df.columns)
        return df

    def process_log(self, fn, sep='\t', cols=["time", "format", "data"]):
        # print("processing log: " + fn)
        df = pd.read_csv(fn, sep=sep, names=cols)
        # print("before format", df)
        m = pd.json_normalize(df["data"].apply(json.loads))
        df.drop(["data"], axis=1, inplace=True)
        df = pd.concat([df, m], axis=1, sort=False)
        # print("after format", df)
        return df

    def as_df(self, filenames=None):
        if self.df is not None:
            return self.df
        if filenames is None:
            filenames = self.filenames
        df = pd.DataFrame()
        for f in filenames:
            # print("processing file: " + f)
            if f.endswith(".csv"):
                ddf = pd.read_csv(f)
            elif f.endswith("stdout") or f.endswith("log"):
                ddf = self.process_log(f)
            df = pd.concat([df, ddf])
        self.df = df
        self.format_time_col()
        return self.df

    def get_ts(self):
        return None

    def format_time_col(self):
        if self.time_format == 'epoch':
            self.df[self.time_col] = \
                    self.df[self.time_col].apply(
                            lambda x: datetime.fromtimestamp(float(x)))
        else:
            self.df[self.time_col] = \
                    self.df[self.time_col].apply(
                            lambda x: datetime.strptime(
                                x[:self.time_cut_tail], self.time_format))
        self.set_time_to_idx()
        return self.df

    def pcap_only(self):
        r = re.compile(".*data/csv.*")
        return list(filter(r.match, self.filenames))

    def pcap_df(self):
        assert self.df is None
        return self.as_df(filenames=self.pcap_only())

    def set_filter(self, filter_func):
        self.filter_func = filter_func
        return self

    def set_search(self, search_options):
        self.ip_search_enabled = search_options[0]
        self.cache_search_enabled = search_options[1]
        return self

    def run_filter(self, args):
        return self.filter_func(self.as_df(), args)

    def filterByIP(self, ip, run_filter=True, args=None):
        df = self.as_df()
        if run_filter:
            df = self.run_filter(args)
        return df[((df['ip.dst'] == ip) |
                   (df['ip.src'] == ip))]

    def filterByCache(self, ip, cache_data, run_filter=True, args=None):
        df = self.as_df()
        if run_filter:
            df = self.run_filter(args)

        df_times = df.index.values.tolist()
        df_times = [pd.to_datetime(t) for t in df_times]

        input_times = cache_data.index.values.tolist()
        input_times = [pd.to_datetime(t) for t in input_times]

        keepers = [False] * len(df_times)
        idx = 0
        stop = len(input_times)
        for i in range(0, len(df_times)):
            if idx >= stop:
                break
            diff = input_times[idx] - df_times[i]
            if diff <= pd.Timedelta(0):
                idx += 1
            elif diff <= self.cache_timing:
                keepers[i] = True

        return df[keepers]

    def search(self, ip=None, cache_data=None, args=None):
        matches_ip = pd.DataFrame()
        matches_cache = pd.DataFrame()
        if self.ip_search_enabled and ip is not None:
            matches_ip = self.filterByIP(ip, args=args)
        if self.cache_search_enabled and cache_data is not None:
            matches_cache = self.filterByCache(ip, cache_data, args=args)
        return [matches_ip, matches_cache]

    def remove_zero_var(self, cutoff=0.01):
        df = self.as_df()

        numeric_cols = df.select_dtypes(include=np.number)
        cols_to_drop = numeric_cols.columns[(numeric_cols.std() <= cutoff) |
                                            (numeric_cols.std().isna())]\
                                                    .tolist()
        df_filtered = df.drop(cols_to_drop, axis=1)
        self.df = df_filtered

    def remove_features(self, bad_features):
        df = self.as_df()
        df.drop(bad_features, inplace=True, axis=1)
        self.df = df

    def set_time_to_idx(self):
        assert self.time_col is not None
        self.df = self.df.set_index(self.time_col)

    def adjust_time_scale(self, offset, scale):
        df = self.as_df()
        # print("before adjust", df, self.time_col in df.columns, df.columns)
        df[self.time_col] = df[self.time_col].apply(lambda x: int(x.timestamp()))
        df[self.time_col] = (df[self.time_col] - offset) * scale + offset
        col = df[self.time_col]
        self.df = df
        self.time_format = 'epoch'
        self.format_time_col()
        self.df = self.df.set_index(self.time_col)
        self.df[self.time_col] = col
        # print("after adjust", self.df)
