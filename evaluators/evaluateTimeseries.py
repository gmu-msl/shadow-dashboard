import redis
import pickle
import os
import json
import heapq
import math
import multiprocessing as mp
from tqdm import tqdm
import pandas as pd
import numpy as np
import yaml
import gzip
import uuid
from time import sleep

from TDA import TDA_Parameters, ts_to_tda
from CastCol import cast_columns
from CrossCorrelation import cross_cor
from Metrics import recall_at_k, get_value_position, heap_to_ordered_list


# system_hostname = os.environ.get('SYSTEM_HOSTNAME') or 'localhost'
system_hostname = os.environ.get('SYSTEM_HOSTNAME') or uuid.uuid1()
redis_host = os.environ.get('REDIS_HOST') or 'localhost'
redis_job_notify_channel = os.environ.get(
    'REDIS_JOB_NOTIFY_CHANNEL') or 'REDIS_JOB_NOTIFY_CHANNEL'
shared_folder = os.environ.get('SHARED_FOLDER') or './'

# TODO: FIX THIS


def ip_to_user_multi(ip, group_size=5, starting=5):
    isp = int(int(ip.split(".")[-2]))
    node_number = int(ip.split(".")[-1]) - starting - isp
    user = node_number % group_size
    group = math.floor(node_number / group_size)
    return '/tordata/config/group_' + str(group) + "_user_" + str(user)


def ip_to_user_single(ip, group_size=5, starting=10):
    local_net = int(ip.split(".")[-1]) - starting
    user = local_net % group_size
    group = math.floor(local_net/group_size)
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
    # buffer_room = 120  # in seconds
    range = min(ts2.index.values), max(ts2.index.values)
    ts1 = ts1.loc[(ts1.index >= range[0]) & (ts1.index <= range[1])]
    # ts1 = ts1[(ts1['frame.time'] >= int(range[0])) &
    #           (ts1['frame.time'] <= int(range[1]))]
    # print(ts1)
    # ts1 = ts1.loc[:, 'tda_pl']
    ts1 = ts1.values[:, 0]

    ts1_norm = np.array(ts1.copy())
    ts2_norm = np.array(ts2.copy())

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

    return score, lag


def evaluate(src_raw, dst_raw, src_features, dst_feaures, display=False, params=TDA_Parameters(0, 3, 1, 1, 1), config=None):
    src = {}
    dst = {}
    for ip in src_raw:
        try:
            data = src_raw[ip][src_features].copy(deep=True)
        except Exception:
            data = pd.DataFrame(
                0, index=src_raw[ip].index, columns=src_features)
        if config['tda']:
            src[ip] = ts_to_tda(data)
        else:
            src[ip] = data
    for user in dst_raw:
        try:
            data = dst_raw[user][dst_feaures].copy(deep=True)
        except Exception:
            data = pd.DataFrame(
                0, index=dst_raw[user].index, columns=dst_feaures)
        if config['tda']:
            dst[user] = ts_to_tda(data)
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
            score, _ = compare_ts_reshape(src[ip].copy(
                deep=True), dst[user].copy(deep=True))
            if not math.isnan(score) and not math.isinf(score):
                heapq.heappush(heap, (score, counter, ip_to_user(ip), ip))
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


def evaluate_subset(src_df, dst_df, src_features, dst_feaures, tda_config=None, config=None):
    score = evaluate(src_df, dst_df, list(src_features),
                     list(dst_feaures), params=tda_config, config=config)
    return score, src_features


def process_tasks(tasks, tda_config, config):
    # tasks is a list of tasks
    with mp.Pool(processes=num_cpus) as pool:
        results = []
        for task in tasks:
            results.append(pool.apply_async(evaluate_subset, args=(
                manager.src_df, manager.dst_df, task["src_feature"], task["dst_feature"], tda_config, config)))

        filename = f'{system_hostname}_{task["filename"]}'
        path = f'{shared_folder}/results/{experiment_name}/{filename}'
        with open(path, 'a+') as f:
            for result in tqdm(results, total=len(tasks)):
                score, subset = result.get()
                out = str(score) + "\t" + str(subset) + "\n"
                f.write(out)
            f.close()  # close the file after writing


def add_tasks_to_redis(tasks, redis_topic):
    # tasks is a list of tasks
    for task in tasks:
        r.rpush(redis_topic, json.dumps(task))


def acquire_redis_lock(redis_instance, key):
    return redis_instance.setnx(key, 1)


def release_redis_lock(redis_instance, key):
    return redis_instance.delete(key)


if __name__ == "__main__":
    print("Starting evaluator v0.0")

    # Connect to Redis
    r = redis.Redis(host=redis_host, port=6379, db=0)

    print("Connected to Redis")

    num_cpus = os.cpu_count() // 2  # Use half of the available CPUs

    pubsub = r.pubsub()
    # Listen for new jobs from Redis
    pubsub.subscribe(redis_job_notify_channel)

    manager = mp.Manager()
    manager.src_df = None
    manager.dst_df = None

    # Listen for new jobs from Redis
    while True:
        message = pubsub.get_message()
        if message and message['type'] == 'message':
            # Get the job data from Redis
            job_data = json.loads(message['data'])
            print("Received job: " + str(job_data))
            # Get the job parameters
            experiment_name = job_data['experimentName']
            pickle_filename = job_data['pickleFileName']
            redis_topic = job_data['redisTopicForJobs']
            redis_topic_lock = f"{redis_topic}:lock"
            config_for_job = job_data['config']
        else:
            continue

        # check if a experiment name folder exists in shared folder
        # if not, create it
        if not os.path.exists(f'{shared_folder}/results/{experiment_name}'):
            print("Creating folder for experiment: " + experiment_name +
                  " in path: " + f'{shared_folder}/results/{experiment_name}')
            try:
                os.makedirs(f'{shared_folder}/results/{experiment_name}')
            except FileExistsError as e:
                print("Folder already exists: " + str(e) + " continuing...")

        # once we get a job, we go on to process it
        # we'll come back to listen for more jobs only after we're done processing this one
        config_for_job = yaml.safe_load(config_for_job)

        with gzip.open(f"{shared_folder}/{pickle_filename}", 'rb') as f:
            src_df = pickle.load(f)
            dst_df = pickle.load(f)

        # cast columns
        for ip in src_df:
            cast_columns(src_df[ip])

        for user in dst_df:
            cast_columns(dst_df[user])

        # set variables for multiprocessing in manager
        manager.src_df = src_df
        manager.dst_df = dst_df

        ip_to_user = ip_to_user_single  # default to single user
        if config_for_job["multiISP"]:
            ip_to_user = ip_to_user_multi

        print("Loaded dataframes from pickle file")

        # get count of tasks in redis job
        task_count = r.llen(redis_topic)

        if task_count == 0:
            print("No tasks to process")
            continue

        # before we process tasks, check if we have any in progress
        in_progress_topic = f"{system_hostname}:{redis_topic}:in_progress"
        failed_topic = f"{system_hostname}:{redis_topic}:failed"
        in_progress_count = r.llen(in_progress_topic)

        if in_progress_count > 0:
            print("There are still tasks in progress processing them first")

            # get all the tasks in progress
            tasks_in_progress = r.lrange(in_progress_topic, 0, -1)

            # process the tasks in progress
            tasks_in_progress = [json.loads(task)
                                 for task in tasks_in_progress]

            try:
                process_tasks(tasks_in_progress,
                              config_for_job['tda'], config_for_job)
            except Exception as e:
                print("Error processing tasks in progress: " + str(e))
                # put the tasks back in the queue, so they can be processed again
                add_tasks_to_redis(tasks_in_progress, redis_topic)
                continue

            # remove the tasks in progress from redis
            # delete the in progress topic, everything is done
            r.delete(in_progress_topic)
        else:
            print("No tasks in progress, moving on to new tasks")

        # now we'll process the tasks
        print("Processing tasks....")

        failed_tasks = 0
        tasks_completed = 0
        # we'll process tasks in batches of num_cpus
        while True:
            # get a lock on the redis topic for jobs
            # this is to ensure that no other process is processing the same job
            # we'll release the lock once we're done getting tasks for ourselves
            print("Getting lock on redis topic: " + redis_topic)

            if acquire_redis_lock(r, redis_topic_lock):
                print("Acquired lock on redis topic: " + redis_topic)

                tasks = r.lrange(redis_topic, 0, num_cpus)

                print("Got " + str(len(tasks)) + " tasks")

                if len(tasks) == 0:
                    print("No more tasks to process")
                    break

                # move the tasks to in progress
                r.rpush(in_progress_topic, *tasks)

                # remove the tasks from the redis topic
                r.ltrim(redis_topic, len(tasks), -1)

                # release the lock
                release_redis_lock(r, redis_topic_lock)
            else:
                print("Failed to acquire lock on redis topic: " + redis_topic)
                sleep(1)
                continue

            # process the tasks
            tasks = [json.loads(task) for task in tasks]

            try:
                process_tasks(tasks, config_for_job['tda'], config_for_job)
                tasks_completed += len(tasks)

                # remove the tasks from in progress
                r.ltrim(in_progress_topic, len(tasks), -1)
            except Exception as e:
                print("Error processing tasks: " + str(e))
                failed_tasks += len(tasks)
                # put the tasks in the failed topic, so they can be processed again later
                add_tasks_to_redis(tasks, failed_topic)
                continue

        print("Finished processing " + str(tasks_completed) +
              " tasks for topic " + redis_topic + " with " + str(failed_tasks) + " failed tasks")

        # we'll move on to waiting for new jobs now
