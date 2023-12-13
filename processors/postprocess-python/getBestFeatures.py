import sys
import os
import glob
import ast
from pathlib import Path


if len(sys.argv) < 3:
    print(
        "Usage: python {} <experiment-name> <directory_path>".format(sys.argv[0]))

    sys.exit(1)

experiment_name = sys.argv[1]
directory_path = sys.argv[2]


def best_feature_ordered_csv(directory, files_to_check, key_size, evaluation_type):
    combined_output = []
    results_for_key_size_and_evaluation_type = []
    user_wise_result = {}
    for file in files_to_check:
        with open(file, 'r') as f:
            lines = f.readlines()
            for line in lines:
                combined_output.append(line)
                result_for_line = {}

                tuples = line.strip("()").strip("").split(" ")

                tuples = [x.strip(',') for x in tuples]

                accuracy, recall_2, recall_4, recall_8, avg_rank = tuples[
                    0], tuples[1], tuples[2], tuples[3], tuples[4]

                result_for_line["accuracy"] = accuracy
                result_for_line["recall_2"] = recall_2
                result_for_line["recall_4"] = recall_4
                result_for_line["recall_8"] = recall_8
                result_for_line["avg_rank"] = avg_rank

                # Remove leading and trailing whitespaces
                line = line.strip()

                # Split the string on commas
                data = line.split(',')

                feature = ''
                # if key size is 1, then there is only one feature
                if key_size == 1:
                    # Get the last value
                    feature = data[-1].split("\t")[-1][2:-1].strip("'")
                else:
                    # Get the last value
                    first_feature = data[-2].split("\t")[-1][2:-1]
                    second_feature = data[-1].strip("]").split("\t")[-1][2:-1]
                    feature = f'{first_feature}-{second_feature}'

                result_for_line["feature"] = feature

                results_for_key_size_and_evaluation_type.append(
                    result_for_line)

                # Split the string on \t
                data = line.split('\t')[-2]

                # literal_eval converts a string to a tuple
                tuple_data = ast.literal_eval(data)
                tuple_data = tuple_data[6]  # get the 6th element of the tuple
                for results, user in tuple_data:
                    user = user.split("/")[-1]
                    if user not in user_wise_result:
                        user_wise_result[user] = []

                    for result in results:
                        # negate the value
                        relative_coefficient = result[0] * -1
                        ip_guessed = result[-1]
                        guess = f"{relative_coefficient},{ip_guessed},{key_size}-{evaluation_type},{feature},{accuracy},{recall_2},{recall_4},{recall_8},{avg_rank}"
                        user_wise_result[user].append(guess)

            f.close()  # close the file

    # write the combined output to a file
    with open(f"{directory}/combined-output/{experiment_name}_{key_size}_{evaluation_type}_combined.output", 'w') as f:
        for line in combined_output:
            f.write(line)
        f.close()

    with open(f"{directory}/result-csv/{experiment_name}_{key_size}_{evaluation_type}_best_features.csv", 'w') as f:
        f.write("accuracy,recall_2,recall_4,recall_8,avg_rank,feature\n")
        results_for_key_size_and_evaluation_type.sort(
            key=lambda x: float(x["accuracy"]), reverse=True
        )
        for result in results_for_key_size_and_evaluation_type:
            f.write(
                f"{result['accuracy']},{result['recall_2']},{result['recall_4']},{result['recall_8']},{result['avg_rank']},{result['feature']}\n")

        f.close()

    # write user wise result to a file of their own
    for user in user_wise_result:
        with open(f"{directory}/user-wise-result/{user}.csv", 'w') as f:
            f.write(
                "relative_coefficient,ip_guessed,file,feature,accuracy,recall_2,recall_4,recall_8,avg_rank\n")
            for result in user_wise_result[user]:
                f.write(f"{result}\n")
            f.close()


print("finding best features")

# set the processing flag
processing_flag = open(f"{directory_path}/processing-in-progress", "w")
processing_flag.close()

# if result_csv doesn't exist, create it
Path(f"{directory_path}/result-csv").mkdir(parents=True, exist_ok=True)

# if combined output directory doesn't exist, create it
Path(f"{directory_path}/combined-output").mkdir(parents=True, exist_ok=True)

# if user wise result directory doesn't exist, create it
Path(f"{directory_path}/user-wise-result").mkdir(parents=True, exist_ok=True)

key_sizes = [1]
evaluation_types = ["count", "text_len"]

for key_size in key_sizes:
    for evaluation_type in evaluation_types:
        print("key_size: {}, evaluation_type: {}".format(
            key_size, evaluation_type))

        # get all files with the given key_size and evaluation_type
        files_with_key_size_and_evaluation_type = []
        for file in glob.glob(f"{directory_path}/*_{key_size}_*{evaluation_type}*.output"):
            files_with_key_size_and_evaluation_type.append(file)

        # get the best features and write to it's csv file
        best_feature_ordered_csv(directory_path,
                                 files_with_key_size_and_evaluation_type, key_size, evaluation_type)

        print(
            f"done with key_size: {key_size}, evaluation_type: {evaluation_type}")


# # get user wise result, from the combined output
# get_user_wise_result(directory_path)

# after processing, remove the procesing flag set
os.remove(f"{directory_path}/processing-in-progress")
