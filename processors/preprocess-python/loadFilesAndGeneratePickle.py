import yaml
import sys
import pickle
import pandas as pd

# Local Imports
# setting path
sys.path.append('../../flow2text/src')
from Preprocess import preprocess
from Config import configFactory

# pandas disable chained assignment warning
pd.options.mode.chained_assignment = None

# ==============================================================================
# Config
# ==============================================================================
if len(sys.argv) < 5:
    print("Usage: python {} <config.yaml> <output_filename> <pcappath> <logpath>".format(
        sys.argv[0]))
    sys.exit(1)

config_file = sys.argv[1]
output_filename = sys.argv[2]
pcappath = sys.argv[3]
logpath = sys.argv[4]

with open(config_file, 'r') as file:
    config_raw = yaml.safe_load(file)
data_config, model_config = configFactory(config_raw,
                                          logpath=logpath,
                                          pcappath=pcappath)
# ==============================================================================
# END Config
# ==============================================================================

src, dst = preprocess(data_config)

with open(output_filename, 'wb') as file:
    pickle.dump(src, file)
    pickle.dump(dst, file)


# exit
sys.exit(0)
