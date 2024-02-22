import redis
import json
import sys
import pickle
from datetime import datetime

# setting path
sys.path.append('../../flow2text/src')

from CastCol import cast_columns
from experiment_runner import findsubsets, get_features


if len(sys.argv) < 5:
    print("Usage: python {} <experiment-name> <output_filename> <redis_hostname> <REDIS_TASKS_LIST_NAME>".format(
        sys.argv[0]))

    sys.exit(1)

experiment_name = sys.argv[1]
output_filename = sys.argv[2]
redis_hostname = sys.argv[3]
REDIS_TASKS_LIST = sys.argv[4]

# load from the pickle file
with open(output_filename, 'rb') as file:
    flows_ts_ip_total = pickle.load(file)
    client_chat_logs = pickle.load(file)

    # close the pickle file
    file.close()

# cast columns
for ip in flows_ts_ip_total:
    cast_columns(flows_ts_ip_total[ip])

for user in client_chat_logs:
    cast_columns(client_chat_logs[user])

# get tasks
tasks = []

for n in range(1, 3):
    for output_size in range(1, len(client_chat_logs) + 1):
        for features in findsubsets(get_features(client_chat_logs), output_size):
            src_features_for_dst_features = findsubsets(get_features(flows_ts_ip_total), n)
            key = f"{output_size}_{n}_{features}"
            for src_feature in src_features_for_dst_features:
                task = {
                    "key": key,
                    "src_feature": src_feature,
                    "dst_feature": features
                }
                task["filename"] = experiment_name + "_" + str(
                    n) + "_outputFeatures_" + str(features) + "_" + str(datetime.now()) + ".output"
                tasks.append(task)

# write tasks to redis
r = redis.Redis(host=redis_hostname, port=6379, db=0)

tasks_json = [json.dumps(task) for task in tasks]
r.rpush(REDIS_TASKS_LIST, *tasks_json)

# check if tasks are written to redis, by checking the length of the list
print("Tasks written to redis: ", r.llen(REDIS_TASKS_LIST))

# exit
sys.exit(0)
