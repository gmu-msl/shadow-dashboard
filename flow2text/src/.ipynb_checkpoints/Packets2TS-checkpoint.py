from os import error
import pandas as pd
from tqdm import tqdm
from Pipeline import Pipeline
from DFutil import df_to_ts


class Packets2TS(Pipeline):

    def __init__(self, evil_domain, ignored_ips=[]):
        self.evil_domain = evil_domain
        self.ignored_ips = ignored_ips

    def combineScopes(self, dfs):
        if len(dfs) < 1:
            return dfs
        return pd.concat(dfs)

    def scopeToTS(self, df, time_col):
        return df_to_ts(df.copy(deep=True)).set_index(time_col)

    def scope_label(self, df, scope_name):
        for col in df.columns:
            df[col + "_" + scope_name] = df[col]
        df["scope_name"] = scope_name
        return df

    def run(self, IPs, scopes):
        flows_ip = {}
        flows_ts_ip_scoped = {}
        flows_ts_ip_total = {}

        for ip in tqdm(IPs):
            # Don't add known infra IPs or users that can are solo
            # communicaters
            if ip in self.ignored_ips:
                continue
            flows_ip[ip] = pd.DataFrame()
            flows_ts_ip_scoped[ip] = pd.DataFrame()
            flows_ts_ip_total[ip] = pd.DataFrame()
            for scope in scopes:
                # Find matches
                matches = scope.search(ip=ip, cache_data=flows_ip[ip],
                                       args=(self.evil_domain))
                if matches[0].empty and matches[1].empty:
                    print("No matches for {} at {}".format(ip, scope))
                    continue
                if not matches[0].empty:
                    matches[0]['count'] = 1
                if not matches[1].empty:
                    matches[1]['count_cache'] = 1

                # Update df for ip
                combined_scope = self.combineScopes(matches)
                combined_scope = self.scope_label(combined_scope, scope.name)
                combined_scope["scope_name"] = scope.name
                flows_ip[ip] = self.combineScopes([flows_ip[ip],
                                                   combined_scope])

                # update ts for ip
                new_ts_matches = self.scopeToTS(combined_scope, scope.time_col)
                if len(new_ts_matches) == 0:
                    continue
                new_ts_matches["scope_name"] = scope.name
                flows_ts_ip_scoped[ip] = \
                    self.combineScopes([flows_ts_ip_scoped[ip],
                                        new_ts_matches])
            if len(flows_ip[ip]) > 0:
                flows_ts_ip_total[ip] = self.scopeToTS(flows_ip[ip],
                                                       scope.time_col)

                # sort combined df by timestamp
                flows_ip[ip].sort_index(inplace=True)
                flows_ts_ip_scoped[ip].sort_index(inplace=True)
                flows_ts_ip_total[ip].sort_index(inplace=True)

                # Preserve time col to be used for feautre engineering
                flows_ip[ip]['frame.time'] = flows_ip[ip].index
                flows_ts_ip_total[ip]['frame.time'] = \
                    flows_ts_ip_total[ip].index

                # remove nans with 0
                flows_ip[ip].fillna(0, inplace=True)
                flows_ts_ip_scoped[ip].fillna(0, inplace=True)
                flows_ts_ip_total[ip].fillna(0, inplace=True)

                # label scope col as category
                flows_ip[ip]["scope_name"] = \
                    flows_ip[ip]["scope_name"].astype('category')
                flows_ts_ip_scoped[ip]["scope_name"] = \
                    flows_ts_ip_scoped[ip]["scope_name"].astype('category')
        return flows_ts_ip_total
