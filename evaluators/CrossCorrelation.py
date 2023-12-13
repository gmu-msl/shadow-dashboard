import numpy as np
import statsmodels.api as sm


# https://www.datainsightonline.com/post/cross-correlation-with-two-time-series-in-python
# from scipy import signal
def ccf_values(series1, series2):
    p = series1
    q = series2
    p = (p - np.mean(p)) / (np.std(p) * len(p))
    q = (q - np.mean(q)) / (np.std(q))
    c = np.correlate(p, q, 'full')
    return c


def ccf_calc(sig1, sig2):
    corr = sm.tsa.stattools.ccf(sig2, sig1, adjusted=False)

    # Remove padding and reverse the order
    return corr[0:(len(sig2)+1)][::-1]


def cross_cor(ts1, ts2, debug=False, max_offset=300, only_positive=True):
    ccf = ccf_calc(ts1, ts2)
    best_cor = max(ccf)
    best_lag = np.argmax(ccf)

    if debug:
        print('best cross correlation: ' + str(best_cor) + " at time lag: " + str(best_lag))
        print(len(ccf))
        print(ccf)
        # ccf_plot(range(len(ccf)), ccf)
    return best_cor, best_lag
