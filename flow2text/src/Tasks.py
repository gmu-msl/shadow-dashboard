import itertools


def findsubsets(s, n):
    return list(itertools.combinations(s, n))


def get_features(df):
    features = []
    for src in df:
        features += df[src].columns.tolist()
    return list(set(features))
