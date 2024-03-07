import itertools
import importlib
import yaml
import sys
import pickle
import multiprocessing as mp
import heapq
from datetime import datetime
import pandas as pd
from tqdm import tqdm
import numpy as np
import math
from fastdtw import fastdtw

# Local Imports
from TDA import TDA_Parameters, ts_to_tda
from CrossCorrelation import cross_cor
from Metrics import recall_at_k, heap_to_ordered_list, get_value_position
from Preprocess import preprocess
from CastCol import cast_columns


# ==============================================================================
# Config
# ==============================================================================
if len(sys.argv) < 2:
    print("Usage: python {} <config.yaml>".format(sys.argv[0]))
    sys.exit(1)

config_file = sys.argv[1]
with open(config_file, 'r') as file:
    config = yaml.safe_load(file)
# ==============================================================================
# END Config
# ==============================================================================

window = pd.Timedelta(config['window'])
num_cpus = config['num_cpus']

module = importlib.import_module('ScopeFilters')
for scope in config['scope_config']:
    scope[2] = getattr(module, scope[2])

tda_config = TDA_Parameters(config['dim'],
                            config['tda_window'],
                            config['skip'],
                            config['k'],
                            float(config['thresh']))


src, dst = preprocess(config['pcappath'],
                      config['logpath'],
                      config['scope_config'],
                      config['server_logs'],
                      config['infra_ip'],
                      window,
                      config['evil_domain'],
                      config['bad_features'],
                      debug=config['DEBUG'])

p_filename = config['experiment_name'] + "_ts.pkl"
with open(p_filename, 'wb') as file:
    pickle.dump(src, file)
    pickle.dump(dst, file)

with open(p_filename, 'rb') as file:
    flows_ts_ip_total = pickle.load(file)
    client_chat_logs = pickle.load(file)

bad_features = ['ip', 'udp.dstport', 'frame', 'tcp.dstport', 'tcp.ack']
                # 'tcp.time_relative', 'tcp.reassembled.length']

for ip in flows_ts_ip_total:
    cast_columns(flows_ts_ip_total[ip])
    df = flows_ts_ip_total[ip]
    cols_to_remove = []
    for pattern in bad_features:
        cols_to_remove += [c for c in df.columns if pattern in c.lower()]
    df.drop(columns=cols_to_remove, inplace=True)

for user in client_chat_logs:
    cast_columns(client_chat_logs[user])


# def ip_to_group(ip):
#     if isinstance(ip, float) or ip.split(".")[0] != '102':
#         return -1
#     return math.floor((int(ip.split(".")[-1])-2) / 5)


# def get_real_label(dic):
#     data = dic.keys()
#     result = np.array([ip_to_group(xi) for xi in data])
#     return result


# answers = get_real_label(flows_ts_ip_total)


def my_dtw(ts1, ts2):
    distance, path = fastdtw(ts1, ts2)
    return distance


def my_pl_ts(ts1, ts2, ip1, ip2):
    return my_dtw(ts1, ts2)


def my_dist(ts1, ts2, ip1="", ip2=""):
    return my_pl_ts(ts1, ts2, ip1, ip2)


def ip_to_user(ip, group_size=5, starting=5):
    isp = int(int(ip.split(".")[-2]))
    node_number = int(ip.split(".")[-1]) - starting - isp
    user = node_number % group_size
    group = math.floor(node_number / group_size)
    return '/tordata/config/group_' + str(group) + "_user_" + str(user)


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
    adj_score = score + (((lag+1)^1.1)/1000.0)
    return adj_score, lag

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
    last_timestamp = ts.index[-1]#.timestamp()
    #print(ts.index[-1])
    
    # Create new rows with timestamps in seconds
    new_rows = pd.DataFrame(0, index=pd.date_range(start=last_timestamp, periods=n, freq='S'), columns=ts.columns)
    #print(new_rows)
    # Concatenate the original DataFrame with the new rows
    ts = pd.concat([new_rows, ts, new_rows])
    return ts


def new_tda_2(ts, buff=False):
    ts = ts.fillna(0)
    ts = norm(ts)
    
    dim = 0
    window = 50
    skip = 1
    k = 1
    thresh = float("inf")
    
    params=TDA_Parameters(dim, window, skip, k, thresh)
    if buff:
        ts = add_buff(ts, window+10)
    tda = ts_to_tda(ts, params=params)
    return diff_me(tda)
 
#compare_ts_reshape(new_tda_2(src_ip[features]), new_tda_2(dst_ip, buff=True))


def evaluate(src_raw, dst_raw, src_features, dst_feaures, display=False, params=TDA_Parameters(0, 3, 1, 1, 1)):
    src = {}
    dst = {}
    for ip in src_raw:
        try:
            data = src_raw[ip][src_features].copy(deep=True)
        except Exception:
            data = pd.DataFrame(0, index=src_raw[ip].index, columns=src_features)
        if config['tda']:
            src[ip] = new_tda_2(data)
        else:
            src[ip] = data
    for user in dst_raw:
        try:
            data = dst_raw[user][dst_feaures].copy(deep=True)
        except Exception:
            data = pd.DataFrame(0, index=dst_raw[user].index, columns=dst_feaures)
        if config['tda']:
            dst[user] = new_tda_2(data, buff=True)
        else:
            dst[user] = data

    correct = 0.0
    rank_list = []
    score_list = []
    recall_2 = 0
    recall_4 = 0
    recall_8 = 0
    rank = 0
    for user in dst:
        best_score = 0
        best_user = 0
        heap = []
        counter = 0
        r2 = False
        r4 = False
        r8 = False
        for ip in src:
            counter += 1
            score, _ = compare_ts_reshape(src[ip], dst[user])
            if not math.isnan(score) and not math.isinf(score):
                heapq.heappush(heap, (score, counter, ip_to_user(ip)))
            if score < best_score:
                best_score = score
                best_user = ip_to_user(ip)
        if user == best_user:
            correct += 1
        # print(user)
        if recall_at_k(heap.copy(), 2, user):
            recall_2 += 1
            r2 = True
        if recall_at_k(heap.copy(), 4, user):
            recall_4 += 1
            r4 = True
        if recall_at_k(heap.copy(), 8, user):
            recall_8 += 1
            r8 = True
        if (r2 and (not r4 or not r8)) or (r4 and not r8):
            print("r2: " + str(r2))
            print("r4: " + str(r4))
            print("r8: " + str(r8))
            raise Exception("Bad recall")
        rank += get_value_position(heap, user)
        rank_list += [(get_value_position(heap, user), user)]
        score_list += [(heap_to_ordered_list(heap), user)]
    accuracy = correct / len(src)
    recall_2 = recall_2 / len(src)
    recall_4 = recall_4 / len(src)
    recall_8 = recall_8 / len(src)
    rank = rank / len(src)
    return accuracy, recall_2, recall_4, recall_8, rank #  , rank_list, score_list


def findsubsets(s, n):
    return list(itertools.combinations(s, n))


def evaluate_subset(src_df, dst_df, src_features, dst_feaures, tda_config=None):
    score = evaluate(src_df, dst_df, list(src_features), list(dst_feaures), params=tda_config)
    return score, src_features


def get_features(df):
    features = []
    for src in df:
        features += df[src].columns.tolist()
    return list(set(features))


def iterate_features(src_df, dst_df, n, dst_features, tda_config, filename):
    features = get_features(src_df)
    subsets = findsubsets(features, n)
    results = []
    print("Using " + str(num_cpus) + " cpus for " + str(len(subsets)) + " subsets")
    with mp.Pool(processes=num_cpus) as pool:
        results = []
        for subset in subsets:
            results.append(pool.apply_async(evaluate_subset, args=(src_df, dst_df, subset, dst_features, tda_config)))
        with open(filename, 'a+') as f:
            for result in tqdm(results, total=len(subsets)):
                score, subset = result.get()
                out = str(score) + "\t" + str(subset) + "\n"
                f.write(out)


src_df = flows_ts_ip_total
dst_df = client_chat_logs

# dst_features = ['count']
# src_features = ['count']
# n = 1
# data = evaluate_subset(src_df, dst_df, src_features, dst_features)[-2][-1]
# with open(output_file, 'w') as f:
#     for i in data:
#         out = str(i[-1]) + ", " + str(i[0]) + "\n"
#         f.write(out)

for output_size in range(1, len(dst_df)+1):
    for n in range(2, 4):
        for features in findsubsets(get_features(dst_df), output_size):
            print("Evaluating " + str(n) + " features from " + str(output_size) + " output features")
            best_features = iterate_features(src_df, dst_df, n, features, tda_config,
                                             config['experiment_name'] + str(n) +
                                             "_outputFeatures_" + str(features) +
                                             "_" + str(datetime.now()) +
                                             ".output")
