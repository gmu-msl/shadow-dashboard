from os import listdir
import gzip
import os
import pickle
from os.path import isfile, join
from tqdm import tqdm

from PrivacyScope import createScope, createLogScope
from ScopeFilters import getPossibleIPs
from CastCol import cast_columns
# from Solo import Solo
from Packets2TS import Packets2TS
from DFutil import df_to_ts


def get_df(data_config):
    if not os.path.isfile(data_config.p_filename):

        flows_ts_ip_total, client_chat_logs = preprocess(data_config)

        with gzip.GzipFile(data_config.p_filename, 'wb') as file:
            pickle.dump(flows_ts_ip_total, file)
            pickle.dump(client_chat_logs, file)

    else:
        with gzip.GzipFile(data_config.p_filename, 'rb') as file:
            flows_ts_ip_total = pickle.load(file)
            client_chat_logs = pickle.load(file)

    # bad_features = [
    #                 # 'ip',
    #                 'udp.dstport', 'frame', 'tcp.dstport', 'tcp.ack']
    #                 # 'tcp.time_relative', 'tcp.reassembled.length']

    for ip in flows_ts_ip_total:
        cast_columns(flows_ts_ip_total[ip])
        df = flows_ts_ip_total[ip]
        cols_to_remove = []
        # for pattern in bad_features:
        #     cols_to_remove += [c for c in df.columns if pattern in c.lower()]
        df.drop(columns=cols_to_remove, inplace=True)

    for user in client_chat_logs:
        cast_columns(client_chat_logs[user])

    return flows_ts_ip_total, client_chat_logs


def getFilenames(path):
    return [path+f for f in listdir(path) if isfile(join(path, f))]


def get_chat_logs(data, logs, debug=False):
    scope = createLogScope(data, logs, debug=debug)
    df = scope.as_df()
    df["text_len"] = df["text"].apply(len)
    users = df["username"].unique()
    client_log = {}
    for user in users:
        client_log[user] = \
                df_to_ts(df[df["username"] == user]).set_index('time')
    return client_log


def preprocess(data_config):
    # Get data
    pcapCSVs = getFilenames(data_config.pcappath)
    logs = getFilenames(data_config.logpath)
    data = pcapCSVs + logs
    # Setup Input scopes
    scopes = [createScope(data, regex, name, debug=data_config.debug)
              .set_filter(filter)
              .set_search(search_options)
              for (regex, name, filter, search_options) in data_config.scope_config]
    # Set up chatlog scopes
    client_chat_logs = get_chat_logs(data, data_config.server_logs, debug=data_config.debug)

    ips_seen = getPossibleIPs(scopes)
    IPs = list(set(ips_seen) - set(data_config.infra_ip))
    print(IPs)
    # assert len(IPs) == 100

    if data_config.debug:
        print("Scopes created")
        print(str(scopes))
        print(ips_seen)

    # Add all scope data to IPs found in resolver address space
    # This should be a valid topo sorted list
    # of the scopes (it will be proccessed in order)
    for scope in tqdm(scopes):
        scope.remove_features(data_config.bad_features)
        scope.remove_zero_var()

    # solo = Solo(window, debug=debug).run(scopes)

    # flows_ts_ip_total = Packets2TS(evil_domain, ignored_ips=[infra_ip + solo])\
    flows_ts_ip_total = Packets2TS(data_config.evil_domain, ignored_ips=[data_config.infra_ip])\
        .run(IPs, scopes)
    return flows_ts_ip_total, client_chat_logs
