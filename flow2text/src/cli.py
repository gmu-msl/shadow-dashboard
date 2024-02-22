import sys
import yaml

from experiment_runner import run_experiment

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python {} <config.yaml>".format(sys.argv[0]))
        sys.exit(1)

    with open(sys.argv[1], 'r') as file:
        config = yaml.safe_load(file)

    run_experiment(config)
