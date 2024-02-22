from os import listdir
from os.path import isfile, join

from PrivacyScope import createScope, createLogScope
from ScopeFilters import getPossibleIPs
from Solo import Solo
from Packets2TS import Packets2TS
from DFutil import df_to_ts


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


def preprocess(pcappath, logpath, scope_config, server_logs, infra_ip, window,
               evil_domain, bad_features, debug=False):
    # Get data
    pcapCSVs = getFilenames(pcappath)
    logs = getFilenames(logpath)
    data = pcapCSVs + logs
    # Setup Input scopes
    scopes = [createScope(data, regex, name, debug=debug)
              .set_filter(filter)
              .set_search(search_options)
              for (regex, name, filter, search_options) in scope_config]
    # Set up chatlog scopes
    client_chat_logs = get_chat_logs(data, server_logs, debug=debug)

    ips_seen = getPossibleIPs(scopes)
    IPs = list(set(ips_seen) - set(infra_ip))
    print(IPs)
    assert len(IPs) == 100

    if debug:
        print("Scopes created")
        print(str(scopes))
        print(ips_seen)

    solo = Solo(window, debug=debug).run(scopes)

    # Add all scope data to IPs found in resolver address space
    # This should be a valid topo sorted list
    # of the scopes (it will be proccessed in order)
    for scope in scopes:
        scope.remove_features(bad_features)
        scope.remove_zero_var()

    flows_ts_ip_total = Packets2TS(evil_domain, ignored_ips=[infra_ip + solo])\
        .run(IPs, scopes)
    return flows_ts_ip_total, client_chat_logs
