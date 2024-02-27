import multiprocessing as mp
import heapq
from datetime import datetime
import pandas as pd
from tqdm import tqdm
import math

# Local Imports
from TDA import TDA_Parameters, ts_to_tda
from Metrics import recall_at_k, heap_to_ordered_list, get_value_position
from sim import compare_ts_reshape
from Config import configFactory
from Preprocess import get_df
from Tasks import findsubsets, get_features


def run_experiment(config):
    data_config, model_config = configFactory(config)

    src_df, dst_df = get_df(data_config)
    run_model(src_df, dst_df, model_config)


def run_model(src_df, dst_df, model_config):

    for n in range(1, 5):
        for output_size in range(1, len(dst_df)+1):
            for features in findsubsets(get_features(dst_df), output_size):
                print("Evaluating " + str(n) +
                      " features from " + str(output_size) +
                      " output features")
                iterate_features(src_df, dst_df, n, features,
                                 model_config.name + str(n) +
                                 "_outputFeatures_" + str(features) +
                                 "_" + str(datetime.now()) +
                                 ".output", model_config)


def tda_transform(src_raw, src_features, dst_raw, dst_feaures, config, params):
    src = {}
    dst = {}

    for ip in src_raw:
        try:
            data = src_raw[ip][src_features].copy(deep=True)
        except Exception:
            data = pd.DataFrame(0, index=src_raw[ip].index, columns=src_features)
        if config.tda:
            src[ip] = ts_to_tda(data, params)
        else:
            src[ip] = data
    for user in dst_raw:
        try:
            data = dst_raw[user][dst_feaures].copy(deep=True)
        except Exception:
            data = pd.DataFrame(0, index=dst_raw[user].index, columns=dst_feaures)
        if config.tda:
            dst[user] = ts_to_tda(data, params)
        else:
            dst[user] = data
    return src, dst


def evaluate(src_raw, dst_raw, src_features, dst_feaures, config, ip_to_user,
             display=False, params=TDA_Parameters(0, 3, 1, 1, 1)):
    src, dst = tda_transform(src_raw, src_features, dst_raw, dst_feaures, config, params)

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
    return accuracy, recall_2, recall_4, recall_8, rank, rank_list, score_list


def evaluate_subset(src_df, dst_df, src_features, dst_feaures, config, ip_to_user, tda_config):
    score = evaluate(src_df, dst_df, list(src_features), list(dst_feaures), config, ip_to_user, params=tda_config)
    return score, src_features


def iterate_features(src_df, dst_df, n, dst_features, filename, config):
    features = get_features(src_df)
    subsets = findsubsets(features, n)
    results = []
    with mp.Pool(processes=config.num_cpus) as pool:
        results = []
        for subset in subsets:
            results.append(pool.apply_async(evaluate_subset, args=(src_df, dst_df, subset, dst_features, config, config.ip_to_user, config.tda_config)))
        with open(filename, 'a+') as f:
            for result in tqdm(results, total=len(subsets)):
                score, subset = result.get()
                out = str(score) + "\t" + str(subset) + "\n"
                f.write(out)
