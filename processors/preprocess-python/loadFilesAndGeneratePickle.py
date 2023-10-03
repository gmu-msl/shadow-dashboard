import importlib
import yaml
import sys
import pickle
import pandas as pd
import datetime
import itertools
import redis
import json

# Local Imports
from Preprocess import preprocess
from CastCol import cast_columns


# ==============================================================================
# Config
# ==============================================================================
if len(sys.argv) < 7:
    print("Usage: python {} <config.yaml> <output_filename> <pcappath> <logpath> <redis_hostname> <REDIS_TASKS_LIST_NAME>".format(sys.argv[0]))
    sys.exit(1)

config_file = sys.argv[1]
output_filename = sys.argv[2]
pcappath = sys.argv[3]
logpath = sys.argv[4]
redis_hostname = sys.argv[5]
REDIS_TASKS_LIST = sys.argv[6]

with open(config_file, 'r') as file:
    config = yaml.safe_load(file)
# ==============================================================================
# END Config
# ==============================================================================

window = pd.Timedelta(config['window'])

module = importlib.import_module('ScopeFilters')
for scope in config['scope_config']:
    scope[2] = getattr(module, scope[2])

src, dst = preprocess(pcappath,
                      logpath,
                      config['scope_config'],
                      config['server_logs'],
                      config['infra_ip'],
                      window,
                      config['evil_domain'],
                      config['bad_features'],
                      debug=config['DEBUG'])

with open(output_filename, 'wb') as file:
    pickle.dump(src, file)
    pickle.dump(dst, file)

    # close the pickle file
    file.close()

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


# helper functions
def findsubsets(s, n):
    return list(itertools.combinations(s, n))

def get_features(df):
    features = []
    for src in df:
        features += df[src].columns.tolist()
    return list(set(features))

# get tasks
tasks = []

for output_size in range(1, len(client_chat_logs) + 1):
    for n in range(1, 3):
        for features in findsubsets(get_features(client_chat_logs), output_size):
            src_features_for_dst_features = findsubsets(get_features(flows_ts_ip_total), n)
            key = f"{output_size}_{n}_{features}"
            for src_feature in src_features_for_dst_features:
                task = {
                    "key": key,
                    "src_feature": src_feature,
                    "dst_feature": features
                }
                task["filename"] = config['experiment_name'] + str(n) + "_outputFeatures_" + str(features) + "_" + str(datetime.now()) + ".output"
                tasks.append(task)

# write tasks to redis
r = redis.Redis(host=redis_hostname, port=6379, db=0)

tasks_json = [json.dumps(task) for task in tasks]
r.rpush(REDIS_TASKS_LIST, *tasks_json)

# check if tasks are written to redis, by checking the length of the list
print("Tasks written to redis: ", r.llen(REDIS_TASKS_LIST))

# exit
sys.exit(0)