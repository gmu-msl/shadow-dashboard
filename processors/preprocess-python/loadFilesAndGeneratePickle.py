import importlib
import yaml
import sys
import pickle
import pandas as pd

# Local Imports
from Preprocess import preprocess

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


# exit
sys.exit(0)
