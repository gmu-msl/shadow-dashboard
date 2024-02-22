UDP_PROTO = 17
DNS_PORT = 53
DOT_PORT = 853
DOH_PORT = 443
HTTP_PORT = 80
TCP_PROTO = 6


def getPossibleIPs(scopes):
    resolver = [scope for scope in scopes if "isp" in scope.name.lower()]
    assert len(resolver) >= 1
    resolver = resolver[0]
    resolv_df = resolver.as_df()
    r = resolv_df['ip.src'].unique()
    r = [x for x in r if str(x) != 'nan']
    return r


def dns_filter(df, evil_domain):
    if ('dns.qry.name' in df.columns and 'tcp.dstport' in df.columns):
        return df[(df['dns.qry.name'].isin(evil_domain))
                  | ((df['dns.qry.name'].isna())
                  & (df['tcp.dstport'].isin([DOT_PORT, DOH_PORT])))]
    else:
        return df[(df['dns.qry.name'].isin(evil_domain))
                  | (df['dns.qry.name'].isna())]


def none(df, evil_domain):
    return df


def dot_filter(df, evil_domain):
    evil_domain = [evil_domain] + evil_domain.split('.')
    # for dot, we check if tcp port is 853, we cannot check for dns.qry.name in
    # this case if it is upstream DNS, i.e for eg. from resolver to root, tld,
    # etc then we cannot check for tcp.dstport because it is udp (Plain DNS)
    # so, we check if either dns.qry.name is evil.dne or tcp.dstport is 853
    if ('dns.qry.name' not in df.columns and 'tcp.dstport' not in df.columns):
        raise Exception("No DNS or TCP port column found")

    # TODO: This is incorrect and should check for udp.dstport as well
    if ('dns.qry.name' in df.columns and 'tcp.dstport' not in df.columns):
        return df[(df['dns.qry.name'].isin(evil_domain))
                  | (df['dns.qry.name'].isna())]

    return df[(df['dns.qry.name'].isin(evil_domain))
              | (df['dns.qry.name'].isna())
              | (df['tcp.dstport'] == DOT_PORT)
              | (df['tcp.dstport'] == DOH_PORT)]


def isp_filter(df, evil_domain):
    # for isp traffic, we filter out DoT and HTTP traffic from the dataframe
    if ('tcp.dstport' not in df.columns):
        raise Exception("No TCP port column found")

    return df[(df['udp.dstport'] == DNS_PORT)
              | (df['tcp.dstport'] == HTTP_PORT)]
