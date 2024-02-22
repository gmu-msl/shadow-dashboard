import redis
import pickle
import os
import json
import multiprocessing as mp
from tqdm import tqdm
import yaml
import gzip
import uuid
from time import sleep

# TODO: Fix this dep. It should not be here. it does not need to know about
# this method to use it
from CastCol import cast_columns
from experiment_runner import evaluate_subset
from Config import configFactory


# system_hostname = os.environ.get('SYSTEM_HOSTNAME') or 'localhost'
system_hostname = os.environ.get('SYSTEM_HOSTNAME') or uuid.uuid1()
redis_host = os.environ.get('REDIS_HOST') or 'localhost'
redis_job_notify_channel = os.environ.get(
    'REDIS_JOB_NOTIFY_CHANNEL') or 'REDIS_JOB_NOTIFY_CHANNEL'
shared_folder = os.environ.get('SHARED_FOLDER') or './'


# evaluate_subset(src_df, dst_df, src_features, dst_feaures, config, ip_to_user, tda_config)
def process_tasks(tasks, tda_config, config):
    _, model_config = configFactory(config)
    # tasks is a list of tasks
    with mp.Pool(processes=num_cpus) as pool:
        results = []
        for task in tasks:
            results.append(pool.apply_async(evaluate_subset, args=(
                manager.src_df, manager.dst_df, task["src_feature"], task["dst_feature"],
                # tda_config, config
                model_config, model_config.ip_to_user, tda_config
                )))

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
