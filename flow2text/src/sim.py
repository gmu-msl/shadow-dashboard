import numpy as np
from fastdtw import fastdtw
import pandas as pd
from CrossCorrelation import cross_cor
from TDA import TDA_Parameters, ts_to_tda


def my_dtw(ts1, ts2):
    distance, path = fastdtw(ts1, ts2)
    return distance


def my_pl_ts(ts1, ts2, ip1, ip2):
    return my_dtw(ts1, ts2)


def my_dist(ts1, ts2, ip1="", ip2=""):
    return my_pl_ts(ts1, ts2, ip1, ip2)


def compare_ts(ts1, ts2, debug=False):
    # dtw_classic, path_classic = dtw(ts1, ts2, dist='square',
    #                             method='classic', return_path=True)
    # return dtw_classic
    # print(ts1)
    # print(ts2)
    # dist, lag = cross_cor(pd.Series(ts1), pd.Series(ts2))
    dist, lag = cross_cor(ts1, ts2, debug=debug)
    # assert dist >= -1 and dist <= 1
    dist = dist * -1  # flip for use as distance metric
    # assert dist >= -1 and dist <= 1
    return dist, lag


def compare_ts_reshape(ts1, ts2, debug=False):
    ts1 = ts1.fillna(0)
    ts2 = ts2.fillna(0)

    range = min(ts2.index.values), max(ts2.index.values)
    ts1 = ts1.loc[(ts1.index >= range[0]) & (ts1.index <= range[1])]

    # ts1 = ts1.loc[:, 'tda_pl']
    ts1 = ts1.values[:, 0]

    ts1_norm = np.array(ts1)
    ts2_norm = np.array(ts2)

    # delay = 0

    # ts1_norm.index = ts1_norm.index + pd.DateOffset(seconds=delay)

    # lock to same range with buffer room
    # on each side to account for network (or PPT) delay

    # detect if no overlap
    if len(ts1_norm) < 2 or len(ts2_norm) < 2:
        return float("inf"), 0

    # Normalize peaks?
    # ts1_norm = normalize_ts(ts1_norm)
    # ts2_norm = normalize_ts(ts2_norm)

    # plot_ts(ts1_norm, ts2_norm)
    # exit(1)

    # else:
    #     ts1_norm = ts1_norm.tolist()
    #     ts2_norm = ts2_norm.tolist()

    score, lag = compare_ts(ts1_norm, ts2_norm, debug=debug)
    # adj_score = score + (((lag+1)**1.1)/1000.0)
    return score, lag


def norm(df):
    # Initialize a new DataFrame to store the normalized values
    normalized_df = pd.DataFrame()

    # Loop through each column and normalize it using min-max scaling
    for column in df.columns:
        min_val = df[column].min()
        max_val = df[column].max()
        normalized_values = (df[column] - min_val) / (max_val - min_val)
        normalized_df[column] = normalized_values

    return normalized_df


def diff_me(ts):
    return ts.diff().abs()


def add_buff(ts, n):
    # Calculate the new timestamp for the last row
    last_timestamp = ts.index[-1]  # .timestamp()
    # print(ts.index[-1])

    # Create new rows with timestamps in seconds
    new_rows = pd.DataFrame(0, index=pd.date_range(start=last_timestamp,
                                                   periods=n, freq='S'),
                            columns=ts.columns)
    # print(new_rows)
    # Concatenate the original DataFrame with the new rows
    ts = pd.concat([new_rows, ts, new_rows])
    return ts


def new_tda_2(ts, buff=False):
    ts = norm(ts)

    dim = 0
    window = 50
    skip = 1
    k = 1
    thresh = float("inf")

    params = TDA_Parameters(dim, window, skip, k, thresh)
    if buff:
        ts = add_buff(ts, window+10)
    ts = ts.fillna(0)
    tda = ts_to_tda(ts, params=params)
    return diff_me(tda)
