import importlib
import pandas as pd
from ip_convert import ip_to_user_multi, ip_to_user_single


class TDA_Parameters:
    def __init__(self, dim, window, skip, k, thresh):
        self.dim = dim
        self.window = window
        self.skip = skip
        self.k = k
        self.thresh = thresh


class DataConfig:
    def __init__(self, config, pcappath=None, logpath=None):
        self.p_filename = config['experiment_name'] + "_ts.pkl.gz"

        module = importlib.import_module('ScopeFilters')
        for scope in config['scope_config']:
            scope[2] = getattr(module, scope[2])
        if pcappath is not None:
            self.pcappath = pcappath
        else:
            self.pcappath = config['pcappath']

        if logpath is not None:
            self.logpath = logpath
        else:
            self.logpath = config['logpath']
        self.scope_config = config['scope_config']
        self.server_logs = config['server_logs']
        self.infra_ip = config['infra_ip']
        self.window = pd.Timedelta(config['window'])
        self.evil_domain = config['evil_domain']
        self.bad_features = config['bad_features']
        self.DEBUG = config['DEBUG']
        self.debug = config['DEBUG']


class ModelConfig:
    def __init__(self, config):
        self.DEBUG = config['DEBUG']
        self.debug = config['DEBUG']
        self.ip_to_user = ip_to_user_single
        self.num_cpus = config["num_cpus"]
        self.tda = config["tda"]
        self.name = config["experiment_name"]
        if config['multiISP']:
            self.ip_to_user = ip_to_user_multi
        self.tda_config = TDA_Parameters(config['dim'],
                                         config['tda_window'],
                                         config['skip'],
                                         config['k'],
                                         float(config['thresh']))


def configFactory(config, pcappath=None, logpath=None):
    return DataConfig(config, pcappath=pcappath, logpath=logpath), ModelConfig(config)
