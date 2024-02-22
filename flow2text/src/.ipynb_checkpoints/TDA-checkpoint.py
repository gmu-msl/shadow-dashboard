from ripser import ripser
import fast_pl_py
import pandas as pd


def my_dist(ts1, ts2, ip1="", ip2=""):
    return my_pl_ts(ts1, ts2, ip1, ip2)


def rip_ts(window, dim, skip, data, thresh=float("inf")):
    for_pl = {}
    for i in range(0, len(data)-window+1, skip):
        diagrams = ripser(data[i:i+window], maxdim=dim, thresh=thresh)['dgms']
        for_pl[i] = diagrams[dim]
    return for_pl


def tda_trans(pairs, k=2, debug=False):
    pairs = [(x[0], x[1]) for x in pairs]
    return fast_pl_py.pairs_to_l2_norm(pairs, k, debug)


class TDA_Parameters:
    def __init__(self, dim, window, skip, k, thresh):
        self.dim = dim
        self.window = window
        self.skip = skip
        self.k = k
        self.thresh = thresh


def ts_to_tda(data, header="", params=TDA_Parameters(0, 3, 1, 2, float("inf")), debug=False):
    data = data.astype(float)

    # compute birth death pairs
    rip_data = rip_ts(params.window, params.dim, params.skip, data, thresh=params.thresh)
    new_ts = [tda_trans(pairs, params.k, debug) for i, pairs in rip_data.items()]
    return pd.DataFrame({'tda_pl': new_ts}, index=data.index[:len(new_ts)])
